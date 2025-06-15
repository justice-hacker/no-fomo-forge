#!/usr/bin/env python3
"""
NFT Batch Minter - Main Entry Point

This script serves as the main entry point for the NFT batch minting application.
It handles command-line arguments, initializes the configuration, and orchestrates
the minting process.
"""

import argparse
import logging
import sys
import os
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.config import ConfigManager
from src.minter import NFTMinter
from src.exceptions import MinterError, ConfigurationError
from src.utils import setup_logging, validate_ethereum_address


def parse_arguments():
    """
    Parse command line arguments for the NFT minter.
    
    Returns:
        argparse.Namespace: Parsed command line arguments
    """
    parser = argparse.ArgumentParser(
        description='NFT Batch Minter - Automated NFT minting tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                    # Run with default config.json
  python main.py -n ARBITRUM_ONE    # Override network
  python main.py -a 5 -g 1          # Mint 5 NFTs from group 1
  python main.py --dry-run -v       # Test run with verbose output
        """
    )
    
    parser.add_argument(
        '-c', '--config',
        type=str,
        default='config.json',
        help='Path to configuration file (default: config.json)'
    )
    
    parser.add_argument(
        '-n', '--network',
        type=str,
        help='Override network from config (e.g., ARBITRUM_ONE, BERACHAIN)'
    )
    
    parser.add_argument(
        '-a', '--amount',
        type=int,
        help='Override mint amount from config'
    )
    
    parser.add_argument(
        '-g', '--group',
        type=int,
        help='Override group ID from config'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Simulate minting without executing transactions'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--to-address',
        type=str,
        help='Override recipient address (default: your wallet)'
    )
    
    return parser.parse_args()


def validate_overrides(args, config):
    """
    Validate command line overrides against configuration.
    
    Args:
        args: Command line arguments
        config: Configuration manager instance
        
    Raises:
        ConfigurationError: If validation fails
    """
    # Validate network override
    if args.network:
        valid_networks = ['ARBITRUM_ONE', 'ARBITRUM_NOVA', 'ARBITRUM_SEPOLIA', 'BERACHAIN']
        if args.network not in valid_networks:
            raise ConfigurationError(
                f"Invalid network: {args.network}. "
                f"Valid options: {', '.join(valid_networks)}"
            )
    
    # Validate amount override
    if args.amount is not None and args.amount < -1:
        raise ConfigurationError("Amount must be -1 (for max) or greater than 0")
    
    # Validate group override
    if args.group is not None and args.group < 0:
        raise ConfigurationError("Group ID must be non-negative")
    
    # Validate to_address override
    if args.to_address:
        if not validate_ethereum_address(args.to_address):
            raise ConfigurationError(f"Invalid Ethereum address: {args.to_address}")


def apply_overrides(config, args):
    """
    Apply command line overrides to configuration.
    
    Args:
        config: Configuration manager instance
        args: Command line arguments
    """
    if args.network:
        config.data['network']['name'] = args.network
        logging.info(f"Network overridden to: {args.network}")
    
    if args.amount is not None:
        config.data['minting']['amount'] = args.amount
        logging.info(f"Mint amount overridden to: {args.amount}")
    
    if args.group is not None:
        config.data['minting']['group_id'] = args.group
        logging.info(f"Group ID overridden to: {args.group}")
    
    if args.to_address:
        config.data['minting']['to_address'] = args.to_address
        logging.info(f"Recipient address overridden to: {args.to_address}")


def main():
    """
    Main entry point for the NFT minter application.
    """
    # Parse command line arguments
    args = parse_arguments()
    
    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logger = setup_logging(log_level)
    
    logger.info("NFT Batch Minter starting...")
    
    try:
        # Load configuration
        config = ConfigManager(args.config)
        config.load()
        
        # Validate configuration
        config.validate()
        
        # Validate and apply command line overrides
        validate_overrides(args, config)
        apply_overrides(config, args)
        
        # Log configuration summary
        logger.info(f"Network: {config.get('network.name')}")
        logger.info(f"Contract: {config.get('contract.address')}")
        logger.info(f"Group ID: {config.get('minting.group_id')}")
        logger.info(f"Amount: {config.get('minting.amount')}")
        
        if args.dry_run:
            logger.info("DRY RUN MODE - No transactions will be executed")
        
        # Initialize minter
        minter = NFTMinter(config, dry_run=args.dry_run)
        
        # Connect to network
        logger.info("Connecting to blockchain network...")
        minter.connect()
        
        # Load contract
        logger.info("Loading smart contract...")
        minter.load_contract()
        
        # Display contract information
        contract_info = minter.get_contract_info()
        logger.info(f"Contract total supply: {contract_info['total_supply']}")
        logger.info(f"Contract max supply: {contract_info['max_supply']}")
        logger.info(f"Minting status: {'LIVE' if contract_info['mint_live'] else 'NOT LIVE'}")
        
        # Check wallet balance
        balance = minter.get_wallet_balance()
        logger.info(f"Wallet balance: {balance} ETH")
        
        if not args.dry_run and balance == 0:
            raise MinterError("Insufficient balance for gas fees")
        
        # Wait for minting to go live
        if not contract_info['mint_live']:
            logger.info("Waiting for minting to go live...")
            minter.wait_for_mint_live()
        
        # Perform minting
        logger.info("Starting minting process...")
        result = minter.mint()
        
        if result:
            logger.info(f"Minting successful! Transaction hash: {result}")
            logger.info("View transaction on block explorer:")
            logger.info(minter.get_transaction_url(result))
        else:
            logger.warning("Minting completed but no transaction hash returned")
        
        logger.info("NFT Batch Minter completed successfully!")
        
    except ConfigurationError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    except MinterError as e:
        logger.error(f"Minting error: {e}")
        sys.exit(2)
    except KeyboardInterrupt:
        logger.warning("Process interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        sys.exit(3)


if __name__ == "__main__":
    main()