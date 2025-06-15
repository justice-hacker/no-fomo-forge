"""
Network Configuration Module

This module contains network configurations for various blockchain networks
including RPC endpoints, chain IDs, and block explorer information.
"""

from typing import Dict, Any
from .exceptions import ConfigurationError


# Network configurations
NETWORKS = {
    "ARBITRUM_ONE": {
        "name": "Arbitrum One",
        "chain_id": 42161,
        "rpc": "https://arb1.arbitrum.io/rpc",
        "alternative_rpcs": [
            "https://arbitrum-mainnet.infura.io/v3/YOUR-PROJECT-ID",
            "https://arb-mainnet.g.alchemy.com/v2/YOUR-API-KEY",
            "https://endpoints.omniatech.io/v1/arbitrum/one/public"
        ],
        "explorer": {
            "name": "Arbiscan",
            "base_url": "https://arbiscan.io",
            "api_url": "https://api.arbiscan.io/api"
        },
        "native_token": "ETH",
        "is_testnet": False
    },
    
    "ARBITRUM_NOVA": {
        "name": "Arbitrum Nova",
        "chain_id": 42170,
        "rpc": "https://nova.arbitrum.io/rpc",
        "alternative_rpcs": [
            "https://arbitrum-nova.publicnode.com",
            "https://arbitrum-nova.drpc.org"
        ],
        "explorer": {
            "name": "NovaArbiscan",
            "base_url": "https://nova.arbiscan.io",
            "api_url": "https://api-nova.arbiscan.io/api"
        },
        "native_token": "ETH",
        "is_testnet": False
    },
    
    "ARBITRUM_SEPOLIA": {
        "name": "Arbitrum Sepolia",
        "chain_id": 421614,
        "rpc": "https://sepolia-rollup.arbitrum.io/rpc",
        "alternative_rpcs": [
            "https://arbitrum-sepolia.infura.io/v3/YOUR-PROJECT-ID",
            "https://arb-sepolia.g.alchemy.com/v2/YOUR-API-KEY"
        ],
        "explorer": {
            "name": "Sepolia Arbiscan",
            "base_url": "https://sepolia.arbiscan.io",
            "api_url": "https://api-sepolia.arbiscan.io/api"
        },
        "native_token": "ETH",
        "is_testnet": True
    },
    
    "BERACHAIN": {
        "name": "Berachain Bartio (Testnet)",
        "chain_id": 80085,  # Bartio testnet chain ID
        "rpc": "https://bartio.rpc.berachain.com",
        "alternative_rpcs": [
            "https://bartio.drpc.org",
            "https://bera-testnet.nodeinfra.com"
        ],
        "explorer": {
            "name": "Beratrail",
            "base_url": "https://bartio.beratrail.io",
            "api_url": "https://api.routescan.io/v2/network/testnet/evm/80085/etherscan/api"
        },
        "native_token": "BERA",
        "is_testnet": True
    }
}


def get_network_config(network_name: str) -> Dict[str, Any]:
    """
    Get the configuration for a specific network.
    
    Args:
        network_name: Name of the network (e.g., 'ARBITRUM_ONE')
        
    Returns:
        dict: Network configuration
        
    Raises:
        ConfigurationError: If network is not supported
    """
    if network_name not in NETWORKS:
        available = ", ".join(NETWORKS.keys())
        raise ConfigurationError(
            f"Unsupported network: {network_name}. "
            f"Available networks: {available}"
        )
    
    return NETWORKS[network_name].copy()


def get_block_explorer_url(network_name: str, tx_hash: str = None, address: str = None) -> str:
    """
    Get a block explorer URL for a transaction or address.
    
    Args:
        network_name: Name of the network
        tx_hash: Transaction hash (optional)
        address: Address (optional)
        
    Returns:
        str: Block explorer URL
    """
    config = get_network_config(network_name)
    base_url = config['explorer']['base_url']
    
    if tx_hash:
        return f"{base_url}/tx/{tx_hash}"
    elif address:
        return f"{base_url}/address/{address}"
    else:
        return base_url


def is_testnet(network_name: str) -> bool:
    """
    Check if a network is a testnet.
    
    Args:
        network_name: Name of the network
        
    Returns:
        bool: True if testnet, False if mainnet
    """
    config = get_network_config(network_name)
    return config.get('is_testnet', False)


def get_native_token(network_name: str) -> str:
    """
    Get the native token symbol for a network.
    
    Args:
        network_name: Name of the network
        
    Returns:
        str: Native token symbol (e.g., 'ETH', 'BERA')
    """
    config = get_network_config(network_name)
    return config.get('native_token', 'ETH')


def get_all_networks() -> Dict[str, str]:
    """
    Get a dictionary of all available networks.
    
    Returns:
        dict: Network names mapped to their display names
    """
    return {
        key: config['name'] 
        for key, config in NETWORKS.items()
    }


def get_rpc_endpoints(network_name: str) -> list:
    """
    Get all available RPC endpoints for a network.
    
    Args:
        network_name: Name of the network
        
    Returns:
        list: List of RPC endpoints
    """
    config = get_network_config(network_name)
    endpoints = [config['rpc']]
    
    if 'alternative_rpcs' in config:
        endpoints.extend(config['alternative_rpcs'])
    
    return endpoints


def validate_chain_id(network_name: str, chain_id: int) -> bool:
    """
    Validate that a chain ID matches the expected network.
    
    Args:
        network_name: Name of the network
        chain_id: Chain ID to validate
        
    Returns:
        bool: True if chain ID matches
    """
    config = get_network_config(network_name)
    return config['chain_id'] == chain_id