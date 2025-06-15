"""
Utility Functions Module

This module contains various utility functions used throughout the NFT minter
application, including validation, file operations, and API interactions.
"""

import json
import logging
import requests
import re
from pathlib import Path
from datetime import datetime
from typing import Any, Optional, Union
from web3 import Web3


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """
    Setup logging configuration for the application.
    
    Args:
        level: Logging level (e.g., logging.INFO, logging.DEBUG)
        
    Returns:
        Logger instance
    """
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Generate log filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"nft_minter_{timestamp}.log"
    
    # Configure logging
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    # Set specific loggers to WARNING to reduce noise
    logging.getLogger("web3").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    
    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized. Log file: {log_file}")
    
    return logger


def validate_ethereum_address(address: str) -> bool:
    """
    Validate an Ethereum address.
    
    Args:
        address: Address to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not address:
        return False
    
    # Check if it's a valid hex address
    if not re.match(r'^0x[a-fA-F0-9]{40}$', address):
        return False
    
    try:
        # Use Web3 to validate checksum
        Web3.to_checksum_address(address)
        return True
    except:
        # If checksum validation fails, check if it's at least a valid format
        return re.match(r'^0x[a-fA-F0-9]{40}$', address) is not None


def validate_private_key(private_key: str) -> bool:
    """
    Validate an Ethereum private key format.
    
    Args:
        private_key: Private key to validate
        
    Returns:
        bool: True if valid format, False otherwise
    """
    if not private_key:
        return False
    
    # Remove 0x prefix if present
    if private_key.startswith('0x'):
        private_key = private_key[2:]
    
    # Check if it's 64 hex characters
    return bool(re.match(r'^[a-fA-F0-9]{64}$', private_key))


def load_json_file(file_path: Union[str, Path]) -> dict:
    """
    Load JSON data from a file.
    
    Args:
        file_path: Path to JSON file
        
    Returns:
        dict: Parsed JSON data
        
    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If file is not valid JSON
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    with open(file_path, 'r') as f:
        return json.load(f)


def save_json_file(data: dict, file_path: Union[str, Path], indent: int = 2):
    """
    Save data to a JSON file.
    
    Args:
        data: Data to save
        file_path: Path to save file
        indent: JSON indentation (default: 2)
    """
    file_path = Path(file_path)
    
    # Create parent directory if it doesn't exist
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=indent)


def load_abi_from_file(abi_path: Union[str, Path]) -> list:
    """
    Load contract ABI from a JSON file.
    
    Args:
        abi_path: Path to ABI file
        
    Returns:
        list: Contract ABI
        
    Raises:
        Exception: If file cannot be loaded or parsed
    """
    abi_path = Path(abi_path)
    
    if not abi_path.exists():
        raise FileNotFoundError(f"ABI file not found: {abi_path}")
    
    data = load_json_file(abi_path)
    
    # Handle different ABI file formats
    if isinstance(data, list):
        # Direct ABI array
        return data
    elif isinstance(data, dict):
        # Truffle/Hardhat artifact format
        if 'abi' in data:
            return data['abi']
        # Foundry format
        elif 'abi' in data.get('metadata', {}).get('output', {}):
            return data['metadata']['output']['abi']
        else:
            raise ValueError("Could not find ABI in JSON file")
    else:
        raise ValueError("Invalid ABI file format")


def get_contract_abi_from_explorer(
    contract_address: str,
    api_key: str,
    api_url: str
) -> list:
    """
    Fetch contract ABI from a block explorer API.
    
    Args:
        contract_address: Contract address
        api_key: Block explorer API key
        api_url: Block explorer API URL
        
    Returns:
        list: Contract ABI
        
    Raises:
        Exception: If ABI cannot be fetched
    """
    params = {
        "module": "contract",
        "action": "getabi",
        "address": contract_address,
        "apikey": api_key
    }
    
    try:
        response = requests.get(api_url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get("status") == "1" and data.get("result"):
            # Parse the ABI JSON string
            abi = json.loads(data["result"])
            return abi
        else:
            error_msg = data.get("result", "Unknown error")
            raise Exception(f"API error: {error_msg}")
            
    except requests.RequestException as e:
        raise Exception(f"Network error fetching ABI: {str(e)}")
    except json.JSONDecodeError as e:
        raise Exception(f"Invalid ABI JSON from explorer: {str(e)}")


def format_wei_to_ether(wei_amount: int, decimals: int = 4) -> str:
    """
    Format wei amount to ether with specified decimal places.
    
    Args:
        wei_amount: Amount in wei
        decimals: Number of decimal places
        
    Returns:
        str: Formatted ether amount
    """
    ether = Web3.from_wei(wei_amount, 'ether')
    return f"{ether:.{decimals}f}"


def format_gas_price(gas_price_wei: int) -> str:
    """
    Format gas price from wei to gwei.
    
    Args:
        gas_price_wei: Gas price in wei
        
    Returns:
        str: Formatted gas price in gwei
    """
    gwei = Web3.from_wei(gas_price_wei, 'gwei')
    return f"{gwei:.2f} gwei"


def estimate_transaction_cost(gas_limit: int, gas_price_wei: int) -> dict:
    """
    Estimate transaction cost in ETH and USD.
    
    Args:
        gas_limit: Gas limit for transaction
        gas_price_wei: Gas price in wei
        
    Returns:
        dict: Cost estimates
    """
    total_wei = gas_limit * gas_price_wei
    eth_cost = Web3.from_wei(total_wei, 'ether')
    
    return {
        'gas_limit': gas_limit,
        'gas_price_gwei': float(Web3.from_wei(gas_price_wei, 'gwei')),
        'total_eth': float(eth_cost),
        'total_wei': total_wei
    }


def parse_revert_reason(error: Exception) -> Optional[str]:
    """
    Extract revert reason from a transaction error.
    
    Args:
        error: Exception from failed transaction
        
    Returns:
        str: Revert reason if found, None otherwise
    """
    error_str = str(error)
    
    # Common patterns for revert reasons
    patterns = [
        r"execution reverted: (.+?)(?:\n|$)",
        r"VM Exception while processing transaction: revert (.+?)(?:\n|$)",
        r"revert: (.+?)(?:\n|$)",
        r"reason string '(.+?)'",
    ]
    
    for pattern in patterns:
        match = re.search(pattern, error_str, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    
    return None


def create_example_abi():
    """
    Create an example ABI file for common NFT contracts.
    
    This creates a basic ERC721 ABI with common minting functions.
    """
    example_abi = [
        {
            "inputs": [],
            "name": "totalSupply",
            "outputs": [{"name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function"
        },
        {
            "inputs": [],
            "name": "maxSupply",
            "outputs": [{"name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function"
        },
        {
            "inputs": [],
            "name": "mintLive",
            "outputs": [{"name": "", "type": "bool"}],
            "stateMutability": "view",
            "type": "function"
        },
        {
            "inputs": [
                {"name": "_amount", "type": "uint256"},
                {"name": "_groupId", "type": "uint256"},
                {"name": "_to", "type": "address"}
            ],
            "name": "batchMint",
            "outputs": [],
            "stateMutability": "payable",
            "type": "function"
        },
        {
            "inputs": [
                {"name": "_groupId", "type": "uint256"},
                {"name": "_amount", "type": "uint256"}
            ],
            "name": "quoteBatchMint",
            "outputs": [
                {"name": "totalCost", "type": "uint256"},
                {"name": "fee", "type": "uint256"}
            ],
            "stateMutability": "view",
            "type": "function"
        },
        {
            "inputs": [
                {"name": "_groupId", "type": "uint256"}
            ],
            "name": "maxMintPerWallet",
            "outputs": [{"name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function"
        }
    ]
    
    # Save to abi directory
    abi_dir = Path("abi")
    abi_dir.mkdir(exist_ok=True)
    
    save_json_file(example_abi, abi_dir / "example_nft_abi.json")
    
    logging.getLogger(__name__).info(
        "Created example ABI file at abi/example_nft_abi.json"
    )


def check_dependencies():
    """
    Check if all required dependencies are installed.
    
    Returns:
        tuple: (all_installed: bool, missing: list)
    """
    required = [
        'web3',
        'eth-account',
        'requests',
        'tqdm'
    ]
    
    missing = []
    
    for package in required:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing.append(package)
    
    return len(missing) == 0, missing


def format_time_remaining(seconds: int) -> str:
    """
    Format seconds into human-readable time.
    
    Args:
        seconds: Number of seconds
        
    Returns:
        str: Formatted time string
    """
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes}m {secs}s"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m"