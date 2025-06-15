"""
Custom Exceptions Module

This module defines custom exception classes used throughout the NFT minter
application for better error handling and debugging.
"""


class MinterError(Exception):
    """Base exception class for all minter-related errors."""
    pass


class ConfigurationError(MinterError):
    """Raised when there are issues with configuration."""
    pass


class ConnectionError(MinterError):
    """Raised when there are network connection issues."""
    pass


class ContractError(MinterError):
    """Raised when there are issues with smart contract interactions."""
    pass


class TransactionError(MinterError):
    """Raised when a blockchain transaction fails."""
    pass


class ValidationError(MinterError):
    """Raised when input validation fails."""
    pass


class InsufficientFundsError(TransactionError):
    """Raised when wallet has insufficient funds for transaction."""
    pass


class GasEstimationError(TransactionError):
    """Raised when gas estimation fails."""
    pass


class ABIError(ContractError):
    """Raised when there are issues with contract ABI."""
    pass


class MintNotLiveError(ContractError):
    """Raised when attempting to mint while minting is not live."""
    pass


class MintLimitExceededError(ContractError):
    """Raised when mint amount exceeds allowed limit."""
    pass