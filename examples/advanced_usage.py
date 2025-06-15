#!/usr/bin/env python3
"""
Advanced Usage Examples

This file demonstrates advanced usage patterns including custom mint strategies,
error recovery, monitoring, and integration with external systems.
"""

import sys
import os
import time
import asyncio
from typing import List, Dict, Any
from datetime import datetime
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.config import ConfigManager
from src.minter import NFTMinter
from src.exceptions import (
    MinterError, TransactionError, ContractError,
    InsufficientFundsError
)
from src.utils import format_wei_to_ether, parse_revert_reason
import logging


class AdvancedMinter:
    """Advanced minting strategies and patterns."""
    
    def __init__(self, config_path: str = "config.json"):
        self.config = ConfigManager(config_path)
        self.config.load()
        self.logger = logging.getLogger(__name__)
        self.mint_history = []
        
    def mint_with_retry(self, max_retries: int = 3, delay: int = 5) -> bool:
        """
        Mint with automatic retry on failure.
        
        Args:
            max_retries: Maximum number of retry attempts
            delay: Delay between retries in seconds
            
        Returns:
            bool: True if successful, False otherwise
        """
        for attempt in range(max_retries):
            try:
                self.logger.info(f"Mint attempt {attempt + 1}/{max_retries}")
                
                minter = NFTMinter(self.config)
                minter.connect()
                minter.load_contract()
                
                # Check if we have enough balance
                balance = minter.get_wallet_balance()
                if balance < 0.01:  # Minimum balance threshold
                    raise InsufficientFundsError(
                        f"Insufficient balance: {balance} ETH"
                    )
                
                tx_hash = minter.mint()
                
                if tx_hash:
                    self.logger.info(f"Success! TX: {tx_hash}")
                    self.mint_history.append({
                        'timestamp': datetime.now().isoformat(),
                        'tx_hash': tx_hash,
                        'attempt': attempt + 1,
                        'status': 'success'
                    })
                    return True
                    
            except TransactionError as e:
                # Parse revert reason
                reason = parse_revert_reason(e)
                self.logger.warning(f"Transaction failed: {reason or str(e)}")
                
                # Don't retry if it's a permanent error
                if reason and any(msg in reason.lower() for msg in [
                    'max supply', 'mint not live', 'invalid proof'
                ]):
                    self.logger.error("Permanent error detected, not retrying")
                    break
                    
                if attempt < max_retries - 1:
                    self.logger.info(f"Retrying in {delay} seconds...")
                    time.sleep(delay)
                    
            except Exception as e:
                self.logger.error(f"Unexpected error: {e}")
                if attempt < max_retries - 1:
                    time.sleep(delay)
        
        return False
    
    def mint_in_batches(
        self, 
        total_amount: int, 
        batch_size: int = 10,
        delay_between_batches: int = 2
    ) -> List[str]:
        """
        Mint NFTs in batches to avoid gas limits.
        
        Args:
            total_amount: Total number of NFTs to mint
            batch_size: Number of NFTs per batch
            delay_between_batches: Delay between batches in seconds
            
        Returns:
            list: Transaction hashes
        """
        tx_hashes = []
        remaining = total_amount
        
        while remaining > 0:
            current_batch = min(batch_size, remaining)
            
            self.logger.info(
                f"Minting batch: {current_batch} NFTs "
                f"({total_amount - remaining + current_batch}/{total_amount})"
            )
            
            # Update configuration for this batch
            self.config.set('minting.amount', current_batch)
            
            # Mint this batch
            if self.mint_with_retry():
                tx_hashes.extend(self.mint_history[-1:])
                remaining -= current_batch
                
                if remaining > 0:
                    self.logger.info(
                        f"Waiting {delay_between_batches}s before next batch..."
                    )
                    time.sleep(delay_between_batches)
            else:
                self.logger.error("Batch failed, stopping")
                break
        
        return tx_hashes
    
    def monitor_and_mint(
        self,
        check_interval: int = 30,
        max_wait_time: int = 3600
    ) -> bool:
        """
        Monitor contract and mint when conditions are met.
        
        Args:
            check_interval: Seconds between checks
            max_wait_time: Maximum time to wait in seconds
            
        Returns:
            bool: True if minted successfully
        """
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            try:
                minter = NFTMinter(self.config)
                minter.connect()
                minter.load_contract()
                
                info = minter.get_contract_info()
                
                # Check various conditions
                if not info.get('mint_live', False):
                    self.logger.info("Mint not live yet, waiting...")
                elif info['total_supply'] >= info['max_supply']:
                    self.logger.error("Max supply reached!")
                    return False
                else:
                    # All conditions met, attempt to mint
                    self.logger.info("Conditions met, attempting to mint...")
                    return self.mint_with_retry()
                
            except Exception as e:
                self.logger.error(f"Error during monitoring: {e}")
            
            time.sleep(check_interval)
        
        self.logger.error("Timeout reached while monitoring")
        return False
    
    def estimate_total_cost(self, amount: int) -> Dict[str, Any]:
        """
        Estimate total cost for minting including gas.
        
        Args:
            amount: Number of NFTs to mint
            
        Returns:
            dict: Cost breakdown
        """
        try:
            minter = NFTMinter(self.config)
            minter.connect()
            minter.load_contract()
            
            # Get current gas price
            gas_price = minter.web3.eth.gas_price
            
            # Estimate gas for transaction
            # This is a rough estimate, actual may vary
            estimated_gas = 150000 + (50000 * amount)  # Base + per NFT
            
            # Get mint price (if any)
            mint_cost = minter._get_mint_cost(
                self.config.get('minting.group_id'),
                amount
            )
            
            # Calculate totals
            gas_cost_wei = estimated_gas * gas_price
            total_cost_wei = gas_cost_wei + mint_cost
            
            return {
                'amount': amount,
                'mint_cost_eth': format_wei_to_ether(mint_cost),
                'gas_cost_eth': format_wei_to_ether(gas_cost_wei),
                'total_cost_eth': format_wei_to_ether(total_cost_wei),
                'gas_price_gwei': minter.web3.from_wei(gas_price, 'gwei'),
                'estimated_gas': estimated_gas
            }
            
        except Exception as e:
            self.logger.error(f"Error estimating cost: {e}")
            return {}


class MintingScheduler:
    """Schedule minting operations at specific times."""
    
    def __init__(self, config_path: str = "config.json"):
        self.minter = AdvancedMinter(config_path)
        self.logger = logging.getLogger(__name__)
        
    async def schedule_mint_at(self, target_time: datetime) -> bool:
        """
        Schedule a mint operation at a specific time.
        
        Args:
            target_time: DateTime when to execute the mint
            
        Returns:
            bool: True if successful
        """
        now = datetime.now()
        if target_time <= now:
            self.logger.error("Target time is in the past")
            return False
        
        wait_seconds = (target_time - now).total_seconds()
        self.logger.info(
            f"Scheduled mint for {target_time}. "
            f"Waiting {wait_seconds:.0f} seconds..."
        )
        
        await asyncio.sleep(wait_seconds)
        
        self.logger.info("Executing scheduled mint...")
        return self.minter.mint_with_retry()
    
    async def recurring_mint(
        self,
        interval_minutes: int,
        max_iterations: int = None
    ):
        """
        Execute minting at regular intervals.
        
        Args:
            interval_minutes: Minutes between mint attempts
            max_iterations: Maximum number of iterations (None for infinite)
        """
        iteration = 0
        
        while max_iterations is None or iteration < max_iterations:
            self.logger.info(f"Recurring mint iteration {iteration + 1}")
            
            success = self.minter.mint_with_retry()
            
            if success:
                self.logger.info(
                    f"Mint successful. Next attempt in {interval_minutes} minutes"
                )
            else:
                self.logger.warning("Mint failed")
            
            iteration += 1
            
            if max_iterations is None or iteration < max_iterations:
                await asyncio.sleep(interval_minutes * 60)


def example_cost_estimation():
    """Example: Estimate costs before minting."""
    print("\n=== Cost Estimation Example ===")
    
    minter = AdvancedMinter()
    
    for amount in [1, 5, 10, 20]:
        cost = minter.estimate_total_cost(amount)
        if cost:
            print(f"\nMinting {amount} NFTs:")
            print(f"  Mint cost: {cost['mint_cost_eth']} ETH")
            print(f"  Gas cost: {cost['gas_cost_eth']} ETH")
            print(f"  Total: {cost['total_cost_eth']} ETH")


def example_batch_minting():
    """Example: Mint large quantities in batches."""
    print("\n=== Batch Minting Example ===")
    
    minter = AdvancedMinter()
    
    # Mint 50 NFTs in batches of 10
    tx_hashes = minter.mint_in_batches(
        total_amount=50,
        batch_size=10,
        delay_between_batches=5
    )
    
    print(f"\nCompleted {len(tx_hashes)} transactions")
    
    # Save mint history
    with open('mint_history.json', 'w') as f:
        json.dump(minter.mint_history, f, indent=2)


async def example_scheduled_minting():
    """Example: Schedule minting operations."""
    print("\n=== Scheduled Minting Example ===")
    
    scheduler = MintingScheduler()
    
    # Schedule a mint 30 seconds from now
    target_time = datetime.now().replace(second=0, microsecond=0)
    target_time = target_time.replace(minute=target_time.minute + 1)
    
    print(f"Scheduling mint for {target_time}")
    
    await scheduler.schedule_mint_at(target_time)


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("NFT Batch Minter - Advanced Usage Examples")
    print("=" * 50)
    
    # Run examples
    example_cost_estimation()
    
    # Uncomment to run other examples:
    # example_batch_minting()
    # asyncio.run(example_scheduled_minting())
    
    print("\nAdvanced examples completed!")