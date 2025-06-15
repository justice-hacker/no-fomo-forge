"""
Configuration Management Module

This module handles loading, validating, and managing configuration for the
NFT minter application. It supports both JSON files and environment variables.
"""

import json
import os
import logging
from typing import Any, Dict, Optional
from pathlib import Path

from .exceptions import ConfigurationError
from .utils import validate_ethereum_address


class ConfigManager:
    """
    Manages application configuration from files and environment variables.
    
    This class provides a unified interface for accessing configuration values
    with support for nested keys, validation, and environment variable overrides.
    """
    
    # Default configuration structure
    DEFAULT_CONFIG = {
        "wallet": {
            "private_key": "",
            "address": ""
        },
        "network": {
            "name": "BERACHAIN",
            "custom_rpc": None
        },
        "contract": {
            "address": "",
            "abi_path": None,
            "explorer_api_key": None
        },
        "minting": {
            "group_id": 0,
            "amount": 1,
            "to_address": "DEFAULT",
            "auto_max": False
        }
    }
    
    # Environment variable mappings
    ENV_MAPPINGS = {
        "WALLET_PRIVATE_KEY": "wallet.private_key",
        "WALLET_ADDRESS": "wallet.address",
        "NETWORK_NAME": "network.name",
        "NETWORK_RPC": "network.custom_rpc",
        "CONTRACT_ADDRESS": "contract.address",
        "CONTRACT_ABI_PATH": "contract.abi_path",
        "EXPLORER_API_KEY": "contract.explorer_api_key",
        "MINTING_GROUP_ID": "minting.group_id",
        "MINTING_AMOUNT": "minting.amount",
        "MINTING_TO_ADDRESS": "minting.to_address",
        "MINTING_AUTO_MAX": "minting.auto_max"
    }
    
    def __init__(self, config_path: str = "config.json"):
        """
        Initialize the configuration manager.
        
        Args:
            config_path: Path to the configuration file
        """
        self.config_path = Path(config_path)
        self.data = {}
        self.logger = logging.getLogger(__name__)
        
    def load(self):
        """
        Load configuration from file and environment variables.
        
        The loading order is:
        1. Default configuration
        2. Configuration file (if exists)
        3. Environment variables (override previous values)
        
        Raises:
            ConfigurationError: If configuration file is invalid
        """
        # Start with default configuration
        self.data = self._deep_copy(self.DEFAULT_CONFIG)
        
        # Load from file if it exists
        if self.config_path.exists():
            self._load_from_file()
        else:
            self.logger.warning(
                f"Configuration file not found: {self.config_path}. "
                "Using defaults and environment variables."
            )
        
        # Override with environment variables
        self._load_from_env()
        
        self.logger.debug(f"Configuration loaded: {self._sanitized_config()}")
        
    def _load_from_file(self):
        """
        Load configuration from JSON file.
        
        Raises:
            ConfigurationError: If file cannot be read or parsed
        """
        try:
            with open(self.config_path, 'r') as f:
                file_config = json.load(f)
            
            # Merge with existing config
            self._merge_config(self.data, file_config)
            
            self.logger.info(f"Loaded configuration from {self.config_path}")
            
        except json.JSONDecodeError as e:
            raise ConfigurationError(
                f"Invalid JSON in configuration file {self.config_path}: {e}"
            )
        except Exception as e:
            raise ConfigurationError(
                f"Failed to read configuration file {self.config_path}: {e}"
            )
    
    def _load_from_env(self):
        """Load configuration from environment variables."""
        env_loaded = False
        
        for env_var, config_key in self.ENV_MAPPINGS.items():
            value = os.environ.get(env_var)
            if value is not None:
                # Convert value type based on the target
                converted_value = self._convert_env_value(value, config_key)
                self._set_nested(self.data, config_key, converted_value)
                env_loaded = True
                self.logger.debug(f"Loaded {config_key} from ${env_var}")
        
        if env_loaded:
            self.logger.info("Loaded configuration from environment variables")
    
    def _convert_env_value(self, value: str, config_key: str) -> Any:
        """
        Convert environment variable string to appropriate type.
        
        Args:
            value: String value from environment
            config_key: Configuration key to determine type
            
        Returns:
            Converted value
        """
        # Get the current value to determine type
        current = self.get(config_key)
        
        if isinstance(current, bool):
            return value.lower() in ('true', '1', 'yes', 'on')
        elif isinstance(current, int):
            try:
                return int(value)
            except ValueError:
                return value
        elif isinstance(current, float):
            try:
                return float(value)
            except ValueError:
                return value
        else:
            # String or None
            return None if value.lower() == 'none' else value
    
    def validate(self):
        """
        Validate the loaded configuration.
        
        Raises:
            ConfigurationError: If configuration is invalid
        """
        errors = []
        
        # Validate wallet configuration
        if not self.get('wallet.private_key'):
            errors.append("wallet.private_key is required")
        
        wallet_address = self.get('wallet.address')
        if wallet_address and not validate_ethereum_address(wallet_address):
            errors.append(f"Invalid wallet address: {wallet_address}")
        
        # Validate network configuration
        valid_networks = ['ARBITRUM_ONE', 'ARBITRUM_NOVA', 'ARBITRUM_SEPOLIA', 'BERACHAIN']
        network = self.get('network.name')
        if network not in valid_networks:
            errors.append(
                f"Invalid network: {network}. "
                f"Valid options: {', '.join(valid_networks)}"
            )
        
        # Validate contract configuration
        contract_address = self.get('contract.address')
        if not contract_address:
            errors.append("contract.address is required")
        elif not validate_ethereum_address(contract_address):
            errors.append(f"Invalid contract address: {contract_address}")
        
        # Check that we have either ABI path or API key
        if not self.get('contract.abi_path') and not self.get('contract.explorer_api_key'):
            errors.append(
                "Either contract.abi_path or contract.explorer_api_key must be provided"
            )
        
        # Validate minting configuration
        amount = self.get('minting.amount')
        if amount < -1 or amount == 0:
            errors.append("minting.amount must be -1 (for max) or greater than 0")
        
        group_id = self.get('minting.group_id')
        if group_id < 0:
            errors.append("minting.group_id must be non-negative")
        
        to_address = self.get('minting.to_address')
        if to_address and to_address != 'DEFAULT':
            if not validate_ethereum_address(to_address):
                errors.append(f"Invalid minting.to_address: {to_address}")
        
        # Raise all errors if any
        if errors:
            raise ConfigurationError(
                "Configuration validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
            )
        
        self.logger.info("Configuration validation passed")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value by key.
        
        Supports nested keys using dot notation (e.g., 'wallet.address').
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        try:
            value = self.data
            for part in key.split('.'):
                value = value[part]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any):
        """
        Set a configuration value by key.
        
        Args:
            key: Configuration key (supports dot notation)
            value: Value to set
        """
        self._set_nested(self.data, key, value)
    
    def _set_nested(self, data: dict, key: str, value: Any):
        """
        Set a nested dictionary value using dot notation.
        
        Args:
            data: Dictionary to modify
            key: Dot-separated key
            value: Value to set
        """
        parts = key.split('.')
        current = data
        
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        
        current[parts[-1]] = value
    
    def _merge_config(self, base: dict, override: dict):
        """
        Recursively merge override config into base config.
        
        Args:
            base: Base configuration dictionary
            override: Override configuration dictionary
        """
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value
    
    def _deep_copy(self, obj: Any) -> Any:
        """
        Create a deep copy of an object.
        
        Args:
            obj: Object to copy
            
        Returns:
            Deep copy of the object
        """
        if isinstance(obj, dict):
            return {k: self._deep_copy(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._deep_copy(item) for item in obj]
        else:
            return obj
    
    def _sanitized_config(self) -> dict:
        """
        Get a sanitized version of config for logging (hides sensitive data).
        
        Returns:
            dict: Sanitized configuration
        """
        config = self._deep_copy(self.data)
        
        # Hide sensitive values
        if 'wallet' in config and 'private_key' in config['wallet']:
            key = config['wallet']['private_key']
            if key:
                config['wallet']['private_key'] = f"{key[:6]}...{key[-4:]}"
        
        if 'contract' in config and 'explorer_api_key' in config['contract']:
            key = config['contract']['explorer_api_key']
            if key:
                config['contract']['explorer_api_key'] = f"{key[:4]}...{key[-4:]}"
        
        return config
    
    def save_example(self, path: Optional[str] = None):
        """
        Save an example configuration file.
        
        Args:
            path: Path to save the example (default: config.example.json)
        """
        example_path = Path(path) if path else Path("config.example.json")
        
        example_config = self._deep_copy(self.DEFAULT_CONFIG)
        example_config['wallet']['private_key'] = "YOUR_PRIVATE_KEY_HERE"
        example_config['wallet']['address'] = "YOUR_WALLET_ADDRESS_HERE"
        example_config['contract']['address'] = "CONTRACT_ADDRESS_HERE"
        example_config['contract']['abi_path'] = "path/to/contract_abi.json"
        example_config['contract']['explorer_api_key'] = "YOUR_API_KEY_HERE"
        
        with open(example_path, 'w') as f:
            json.dump(example_config, f, indent=2)
        
        self.logger.info(f"Saved example configuration to {example_path}")