#!/usr/bin/env python3
"""
Basic Usage Example

This example demonstrates basic usage of the NFT Batch Minter library
for programmatic minting without using the CLI.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.config import ConfigManager
from src.minter import NFTMinter
from src.exceptions import MinterError
import logging


def basic_minting_example():
    """Example of basic NFT minting workflow."""
    
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    try:
        # Create configuration programmatically
        config = ConfigManager()
        config.data = {
            "wallet": {
                "private_key": os.environ.get("WALLET_PRIVATE_KEY", ""),
                "address": os.environ.get("WALLET_ADDRESS", "")
            },
            "network": {
                "name": "BERACHAIN",
                "custom_rpc": None
            },
            "contract": {
                "address": os.environ.get("CONTRACT_ADDRESS", ""),
                "abi_path": "abi/example_nft_abi.json",
                "explorer_api_key": None
            },
            "minting": {
                "group_id": 0,
                "amount": 1,
                "to_address": "DEFAULT",
                "auto_max": False
            }
        }
        
        # Validate configuration
        config.validate()
        
        # Create minter instance
        logger.info("Initializing NFT Minter...")
        minter = NFTMinter(config, dry_run=True)  # Set to False for real minting
        
        # Connect to network
        logger.info("Connecting to blockchain network...")
        minter.connect()
        
        # Load contract
        logger.info("Loading smart contract...")
        minter.load_contract()
        
        # Get contract information
        info = minter.get_contract_info()
        logger.info(f"Contract Info: {info}")
        
        # Check wallet balance
        balance = minter.get_wallet_balance()
        logger.info(f"Wallet Balance: {balance} ETH")
        
        # Wait for mint to go live (if needed)
        if not info.get('mint_live', True):
            logger.info("Waiting for mint to go live...")
            minter.wait_for_mint_live(check_interval=5)
        
        # Perform minting
        logger.info("Executing mint transaction...")
        tx_hash = minter.mint()
        
        if tx_hash:
            logger.info(f"Success! Transaction hash: {tx_hash}")
            logger.info(f"View on explorer: {minter.get_transaction_url(tx_hash)}")
        else:
            logger.info("Dry run completed successfully")
            
    except MinterError as e:
        logger.error(f"Minting error: {e}")
        return False
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return False
    
    return True


def custom_configuration_example():
    """Example of using custom configuration."""
    
    # Create custom configuration
    config = ConfigManager("custom_config.json")
    
    # Override specific values
    config.set("network.name", "ARBITRUM_ONE")
    config.set("minting.amount", 5)
    
    # Save configuration for reuse
    config.save_example("my_custom_config.json")
    
    print("Custom configuration created")


def multi_wallet_example():
    """Example of minting from multiple wallets."""
    
    wallets = [
        {
            "private_key": os.environ.get("WALLET1_PRIVATE_KEY", ""),
            "address": os.environ.get("WALLET1_ADDRESS", "")
        },
        {
            "private_key": os.environ.get("WALLET2_PRIVATE_KEY", ""),
            "address": os.environ.get("WALLET2_ADDRESS", "")
        }
    ]
    
    base_config = ConfigManager()
    base_config.load()
    
    for i, wallet in enumerate(wallets):
        print(f"\nMinting from wallet {i + 1}...")
        
        # Update wallet configuration
        base_config.set("wallet.private_key", wallet["private_key"])
        base_config.set("wallet.address", wallet["address"])
        
        # Create minter and execute
        minter = NFTMinter(base_config, dry_run=True)
        # ... continue with minting process


if __name__ == "__main__":
    print("NFT Batch Minter - Basic Usage Examples")
    print("=" * 50)
    
    # Run basic example
    print("\n1. Running basic minting example...")
    basic_minting_example()
    
    # Show custom configuration example
    print("\n2. Custom configuration example...")
    custom_configuration_example()
    
    print("\nExamples completed!")