"""
NFT Minter Core Module

This module contains the main NFTMinter class that handles all blockchain
interactions for minting NFTs. It provides methods for connecting to networks,
loading contracts, monitoring mint status, and executing batch mints.
"""

import time
import logging
from typing import Dict, Any, Optional, Union
from web3 import Web3
from web3.exceptions import ContractLogicError
from eth_account import Account

from .networks import get_network_config, get_block_explorer_url
from .exceptions import (
    ConnectionError, ContractError, TransactionError, 
    MinterError, ConfigurationError
)
from .utils import load_abi_from_file, get_contract_abi_from_explorer


class NFTMinter:
    """
    Main class for interacting with NFT smart contracts and performing mints.
    
    This class handles all blockchain operations including connecting to networks,
    loading contracts, monitoring mint status, and executing batch mint transactions.
    """
    
    def __init__(self, config, dry_run: bool = False):
        """
        Initialize the NFT Minter with configuration.
        
        Args:
            config: ConfigManager instance with loaded configuration
            dry_run: If True, simulate transactions without executing
        """
        self.config = config
        self.dry_run = dry_run
        self.logger = logging.getLogger(__name__)
        
        # Web3 instance and contract will be initialized later
        self.web3 = None
        self.contract = None
        self.account = None
        
        # Transaction tracking
        self.nonce = None
        self.last_tx_hash = None
        
        # Network and contract details
        self.network_config = None
        self.chain_id = None
        
    def connect(self):
        """
        Connect to the blockchain network.
        
        Raises:
            ConnectionError: If connection to network fails
        """
        # Get network configuration
        network_name = self.config.get('network.name')
        custom_rpc = self.config.get('network.custom_rpc')
        
        self.network_config = get_network_config(network_name)
        
        # Use custom RPC if provided, otherwise use default
        rpc_url = custom_rpc or self.network_config['rpc']
        
        self.logger.debug(f"Connecting to {network_name} at {rpc_url}")
        
        # Initialize Web3
        self.web3 = Web3(Web3.HTTPProvider(rpc_url))
        
        # Check connection
        if not self.web3.is_connected():
            raise ConnectionError(f"Failed to connect to {network_name} at {rpc_url}")
        
        # Get chain ID
        self.chain_id = self.web3.eth.chain_id
        self.logger.info(f"Connected to {network_name} (Chain ID: {self.chain_id})")
        
        # Initialize account
        self._initialize_account()
        
    def _initialize_account(self):
        """
        Initialize the wallet account from private key.
        
        Raises:
            ConfigurationError: If private key is invalid
        """
        private_key = self.config.get('wallet.private_key')
        
        if not private_key:
            raise ConfigurationError("Private key not provided in configuration")
        
        # Ensure private key has 0x prefix
        if not private_key.startswith('0x'):
            private_key = '0x' + private_key
        
        try:
            self.account = Account.from_key(private_key)
            self.logger.info(f"Initialized wallet: {self.account.address}")
            
            # Verify address matches configuration
            config_address = self.config.get('wallet.address')
            if config_address and config_address.lower() != self.account.address.lower():
                self.logger.warning(
                    f"Configured address {config_address} doesn't match "
                    f"derived address {self.account.address}"
                )
        except Exception as e:
            raise ConfigurationError(f"Invalid private key: {str(e)}")
        
        # Get initial nonce
        self.nonce = self.web3.eth.get_transaction_count(self.account.address)
        self.logger.debug(f"Current nonce: {self.nonce}")
        
    def load_contract(self):
        """
        Load the smart contract using ABI.
        
        This method will attempt to load the ABI from a file first,
        then fall back to fetching from block explorer if needed.
        
        Raises:
            ContractError: If contract cannot be loaded
        """
        contract_address = self.config.get('contract.address')
        
        if not contract_address:
            raise ContractError("Contract address not provided in configuration")
        
        # Ensure contract address is checksummed
        contract_address = Web3.to_checksum_address(contract_address)
        
        # Load ABI
        abi = self._load_contract_abi()
        
        # Initialize contract
        try:
            self.contract = self.web3.eth.contract(
                address=contract_address,
                abi=abi
            )
            self.logger.info(f"Loaded contract at {contract_address}")
        except Exception as e:
            raise ContractError(f"Failed to load contract: {str(e)}")
        
    def _load_contract_abi(self) -> list:
        """
        Load contract ABI from file or block explorer.
        
        Returns:
            list: Contract ABI
            
        Raises:
            ContractError: If ABI cannot be loaded
        """
        # Try loading from file first
        abi_path = self.config.get('contract.abi_path')
        if abi_path:
            try:
                abi = load_abi_from_file(abi_path)
                self.logger.info(f"Loaded ABI from file: {abi_path}")
                return abi
            except Exception as e:
                self.logger.warning(f"Failed to load ABI from file: {e}")
        
        # Try fetching from block explorer
        api_key = self.config.get('contract.explorer_api_key')
        if api_key:
            try:
                contract_address = self.config.get('contract.address')
                explorer_config = self.network_config.get('explorer', {})
                
                if not explorer_config:
                    raise ContractError("No block explorer configured for this network")
                
                abi = get_contract_abi_from_explorer(
                    contract_address,
                    api_key,
                    explorer_config['api_url']
                )
                self.logger.info("Loaded ABI from block explorer")
                return abi
            except Exception as e:
                self.logger.warning(f"Failed to fetch ABI from explorer: {e}")
        
        raise ContractError(
            "Could not load contract ABI. Please provide either 'abi_path' "
            "or 'explorer_api_key' in configuration."
        )
        
    def get_contract_info(self) -> Dict[str, Any]:
        """
        Get information about the NFT contract.
        
        Returns:
            dict: Contract information including supply and mint status
            
        Raises:
            ContractError: If contract calls fail
        """
        if not self.contract:
            raise ContractError("Contract not loaded")
        
        try:
            info = {}
            
            # Get total supply
            if hasattr(self.contract.functions, 'totalSupply'):
                info['total_supply'] = self.contract.functions.totalSupply().call()
            else:
                info['total_supply'] = 'N/A'
            
            # Get max supply
            if hasattr(self.contract.functions, 'maxSupply'):
                info['max_supply'] = self.contract.functions.maxSupply().call()
            else:
                info['max_supply'] = 'N/A'
            
            # Check if mint is live
            if hasattr(self.contract.functions, 'mintLive'):
                info['mint_live'] = self.contract.functions.mintLive().call()
            else:
                info['mint_live'] = True  # Assume live if no check function
            
            return info
            
        except Exception as e:
            raise ContractError(f"Failed to get contract info: {str(e)}")
    
    def get_wallet_balance(self) -> float:
        """
        Get the wallet's native token balance.
        
        Returns:
            float: Balance in ETH (or native token)
        """
        if not self.web3 or not self.account:
            raise MinterError("Not connected to network")
        
        balance_wei = self.web3.eth.get_balance(self.account.address)
        balance_eth = self.web3.from_wei(balance_wei, 'ether')
        
        return float(balance_eth)
    
    def wait_for_mint_live(self, check_interval: int = 10, timeout: int = 3600):
        """
        Wait for minting to go live.
        
        Args:
            check_interval: Seconds between checks
            timeout: Maximum seconds to wait
            
        Raises:
            ContractError: If mint doesn't go live within timeout
        """
        if not self.contract:
            raise ContractError("Contract not loaded")
        
        # Check if contract has mintLive function
        if not hasattr(self.contract.functions, 'mintLive'):
            self.logger.warning("Contract doesn't have mintLive function, proceeding anyway")
            return
        
        start_time = time.time()
        
        while True:
            try:
                is_live = self.contract.functions.mintLive().call()
                
                if is_live:
                    self.logger.info("Minting is now LIVE!")
                    return
                
                elapsed = time.time() - start_time
                if elapsed > timeout:
                    raise ContractError(f"Timeout waiting for mint to go live ({timeout}s)")
                
                self.logger.debug(f"Mint not live yet, checking again in {check_interval}s...")
                time.sleep(check_interval)
                
            except Exception as e:
                if "mintLive" in str(e):
                    self.logger.warning("Error checking mint status, proceeding anyway")
                    return
                raise ContractError(f"Error checking mint status: {str(e)}")
    
    def mint(self) -> Optional[str]:
        """
        Execute the minting transaction.
        
        Returns:
            str: Transaction hash if successful, None if dry run
            
        Raises:
            TransactionError: If transaction fails
        """
        if not self.contract or not self.account:
            raise MinterError("Not initialized properly")
        
        # Get minting parameters
        group_id = self.config.get('minting.group_id')
        amount = self.config.get('minting.amount')
        to_address = self.config.get('minting.to_address')
        
        # Handle special address values
        if to_address == 'DEFAULT' or not to_address:
            to_address = self.account.address
        
        # Convert to checksum address
        to_address = Web3.to_checksum_address(to_address)
        
        # Check if we should mint max amount
        if amount == -1:
            amount = self._get_max_mint_amount(group_id)
            self.logger.info(f"Auto-detected max mint amount: {amount}")
        
        self.logger.info(
            f"Minting {amount} NFT(s) from group {group_id} to {to_address}"
        )
        
        if self.dry_run:
            self.logger.info("DRY RUN - Transaction not executed")
            return None
        
        # Build and send transaction
        tx_hash = self._execute_mint_transaction(
            to_address, group_id, amount
        )
        
        return tx_hash
    
    def _get_max_mint_amount(self, group_id: int) -> int:
        """
        Get the maximum mint amount for a group.
        
        Args:
            group_id: The group/collection ID
            
        Returns:
            int: Maximum mint amount
            
        Raises:
            ContractError: If unable to determine max amount
        """
        # Try different function names
        function_names = ['maxMintPerWallet', 'maxMint', 'maxMintAmount']
        
        for func_name in function_names:
            if hasattr(self.contract.functions, func_name):
                try:
                    func = getattr(self.contract.functions, func_name)
                    # Try with group_id parameter
                    try:
                        return func(group_id).call()
                    except:
                        # Try without parameters
                        return func().call()
                except Exception as e:
                    self.logger.debug(f"Failed to call {func_name}: {e}")
        
        # Default to 1 if we can't determine
        self.logger.warning("Could not determine max mint amount, defaulting to 1")
        return 1
    
    def _execute_mint_transaction(
        self, 
        to_address: str, 
        group_id: int, 
        amount: int
    ) -> str:
        """
        Build and execute the mint transaction.
        
        Args:
            to_address: Recipient address
            group_id: Token group/collection ID  
            amount: Number of tokens to mint
            
        Returns:
            str: Transaction hash
            
        Raises:
            TransactionError: If transaction fails
        """
        try:
            # Build transaction
            tx = self._build_mint_transaction(to_address, group_id, amount)
            
            # Sign transaction
            signed_tx = self.web3.eth.account.sign_transaction(
                tx, 
                private_key=self.account.key
            )
            
            # Send transaction
            self.logger.info("Sending transaction...")
            tx_hash = self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)
            tx_hash_hex = tx_hash.hex()
            
            self.logger.info(f"Transaction sent! Hash: {tx_hash_hex}")
            
            # Wait for receipt
            self.logger.info("Waiting for transaction confirmation...")
            receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
            
            # Check transaction status
            if receipt['status'] == 0:
                raise TransactionError("Transaction failed (status = 0)")
            
            self.logger.info(f"Transaction confirmed! Gas used: {receipt['gasUsed']}")
            
            # Update nonce for next transaction
            self.nonce += 1
            self.last_tx_hash = tx_hash_hex
            
            return tx_hash_hex
            
        except ContractLogicError as e:
            # Extract revert reason if available
            revert_reason = str(e)
            if "execution reverted" in revert_reason:
                raise TransactionError(f"Contract execution reverted: {revert_reason}")
            raise TransactionError(f"Contract error: {str(e)}")
            
        except Exception as e:
            raise TransactionError(f"Transaction failed: {str(e)}")
    
    def _build_mint_transaction(
        self, 
        to_address: str, 
        group_id: int, 
        amount: int
    ) -> Dict[str, Any]:
        """
        Build the mint transaction.
        
        Args:
            to_address: Recipient address
            group_id: Token group/collection ID
            amount: Number of tokens to mint
            
        Returns:
            dict: Transaction dictionary
            
        Raises:
            ContractError: If unable to build transaction
        """
        # Try to find the correct mint function
        mint_functions = [
            ('batchMint', [amount, group_id, to_address]),
            ('mint', [to_address, amount, group_id]),
            ('mintBatch', [to_address, group_id, amount]),
            ('publicMint', [amount, group_id])
        ]
        
        mint_function = None
        mint_params = None
        
        for func_name, params in mint_functions:
            if hasattr(self.contract.functions, func_name):
                mint_function = getattr(self.contract.functions, func_name)
                mint_params = params
                self.logger.debug(f"Using mint function: {func_name}")
                break
        
        if not mint_function:
            raise ContractError(
                "Could not find a suitable mint function in the contract"
            )
        
        # Get mint cost
        mint_cost = self._get_mint_cost(group_id, amount)
        
        # Build transaction
        try:
            tx = mint_function(*mint_params).build_transaction({
                'chainId': self.chain_id,
                'from': self.account.address,
                'value': mint_cost,
                'gas': 500000,  # Initial gas estimate
                'gasPrice': self.web3.eth.gas_price,
                'nonce': self.nonce
            })
            
            # Estimate gas
            try:
                gas_estimate = self.web3.eth.estimate_gas(tx)
                tx['gas'] = int(gas_estimate * 1.2)  # Add 20% buffer
                self.logger.debug(f"Gas estimate: {gas_estimate} (using {tx['gas']})")
            except Exception as e:
                self.logger.warning(f"Gas estimation failed, using default: {e}")
                tx['gas'] = 2000000  # Fallback gas limit
            
            return tx
            
        except Exception as e:
            raise ContractError(f"Failed to build transaction: {str(e)}")
    
    def _get_mint_cost(self, group_id: int, amount: int) -> int:
        """
        Get the cost for minting.
        
        Args:
            group_id: Token group/collection ID
            amount: Number of tokens to mint
            
        Returns:
            int: Cost in wei
        """
        # Try different cost calculation functions
        cost_functions = [
            ('quoteBatchMint', [group_id, amount]),
            ('mintPrice', [group_id, amount]),
            ('price', [amount]),
            ('cost', [amount])
        ]
        
        for func_name, params in cost_functions:
            if hasattr(self.contract.functions, func_name):
                try:
                    func = getattr(self.contract.functions, func_name)
                    result = func(*params).call()
                    
                    # Handle different return types
                    if isinstance(result, tuple):
                        # Some contracts return (cost, fee)
                        return result[0]
                    else:
                        return result
                        
                except Exception as e:
                    self.logger.debug(f"Failed to call {func_name}: {e}")
        
        # If no cost function found, assume free mint
        self.logger.warning("Could not determine mint cost, assuming free mint")
        return 0
    
    def get_transaction_url(self, tx_hash: str) -> str:
        """
        Get the block explorer URL for a transaction.
        
        Args:
            tx_hash: Transaction hash
            
        Returns:
            str: Block explorer URL
        """
        explorer_config = self.network_config.get('explorer', {})
        base_url = explorer_config.get('base_url', '')
        
        if base_url:
            return f"{base_url}/tx/{tx_hash}"
        else:
            return f"Transaction hash: {tx_hash}"