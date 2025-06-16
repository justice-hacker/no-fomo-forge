"""
NFT Batch Minter Package

A Python-based automated NFT minting tool that supports multiple blockchain
networks and provides batch minting capabilities with real-time monitoring.
"""

__version__ = "1.0.0"
__author__ = "Justice"
__license__ = "AGPL-3.0 license"

from .minter import NFTMinter
from .config import ConfigManager
from .exceptions import (
    MinterError,
    ConfigurationError,
    ConnectionError,
    ContractError,
    TransactionError,
    ValidationError
)

__all__ = [
    'NFTMinter',
    'ConfigManager',
    'MinterError',
    'ConfigurationError', 
    'ConnectionError',
    'ContractError',
    'TransactionError',
    'ValidationError'
]