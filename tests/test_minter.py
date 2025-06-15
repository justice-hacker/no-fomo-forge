"""
Minter Module Tests

This module contains comprehensive tests for the NFTMinter class, testing
all aspects of blockchain interaction, contract loading, and minting operations.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import json
from pathlib import Path

# Add parent directory to path for imports
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.minter import NFTMinter
from src.config import ConfigManager
from src.exceptions import (
    ConnectionError, ContractError, TransactionError,
    MinterError
)


class TestNFTMinter(unittest.TestCase):
    """Test cases for the NFTMinter class."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create a mock configuration
        self.mock_config = Mock(spec=ConfigManager)
        
        # Set up default configuration values
        self.config_values = {
            'wallet.private_key': '0x' + '1' * 64,
            'wallet.address': '0x' + '2' * 40,
            'network.name': 'BERACHAIN',
            'network.custom_rpc': None,
            'contract.address': '0x' + '3' * 40,
            'contract.abi_path': 'test_abi.json',
            'contract.explorer_api_key': 'test_api_key',
            'minting.group_id': 0,
            'minting.amount': 1,
            'minting.to_address': 'DEFAULT',
            'minting.auto_max': False
        }
        
        # Configure the mock to return values based on the key
        self.mock_config.get.side_effect = lambda key, default=None: \
            self.config_values.get(key, default)
        
        # Create minter instance with mock config
        self.minter = NFTMinter(self.mock_config, dry_run=False)
        
    def test_initialization(self):
        """Test that NFTMinter initializes correctly."""
        self.assertIsNotNone(self.minter)
        self.assertEqual(self.minter.config, self.mock_config)
        self.assertFalse(self.minter.dry_run)
        self.assertIsNone(self.minter.web3)
        self.assertIsNone(self.minter.contract)
        self.assertIsNone(self.minter.account)
        
    @patch('src.minter.Web3')
    def test_connect_success(self, mock_web3_class):
        """Test successful connection to blockchain network."""
        # Set up mock Web3 instance
        mock_web3 = Mock()
        mock_web3.is_connected.return_value = True
        mock_web3.eth.chain_id = 80085  # Berachain testnet
        mock_web3.eth.get_transaction_count.return_value = 5
        mock_web3_class.return_value = mock_web3
        mock_web3_class.HTTPProvider.return_value = Mock()
        
        # Test connection
        self.minter.connect()
        
        # Verify Web3 was initialized correctly
        mock_web3_class.HTTPProvider.assert_called_once()
        self.assertTrue(mock_web3.is_connected.called)
        self.assertEqual(self.minter.web3, mock_web3)
        self.assertEqual(self.minter.chain_id, 80085)
        self.assertEqual(self.minter.nonce, 5)
        
    @patch('src.minter.Web3')
    def test_connect_failure(self, mock_web3_class):
        """Test connection failure handling."""
        # Set up mock to simulate connection failure
        mock_web3 = Mock()
        mock_web3.is_connected.return_value = False
        mock_web3_class.return_value = mock_web3
        mock_web3_class.HTTPProvider.return_value = Mock()
        
        # Test that connection failure raises appropriate error
        with self.assertRaises(ConnectionError) as cm:
            self.minter.connect()
        
        self.assertIn("Failed to connect", str(cm.exception))
        
    @patch('src.minter.Web3')
    @patch('src.minter.Account')
    def test_initialize_account_success(self, mock_account, mock_web3_class):
        """Test successful account initialization."""
        # Set up mocks
        mock_web3 = Mock()
        mock_web3.is_connected.return_value = True
        mock_web3.eth.chain_id = 80085
        mock_web3.eth.get_transaction_count.return_value = 10
        mock_web3_class.return_value = mock_web3
        mock_web3_class.HTTPProvider.return_value = Mock()
        
        mock_account_instance = Mock()
        mock_account_instance.address = '0x' + '2' * 40
        mock_account_instance.key = b'test_key'
        mock_account.from_key.return_value = mock_account_instance
        
        # Connect (which initializes account)
        self.minter.connect()
        
        # Verify account was initialized
        mock_account.from_key.assert_called_once()
        self.assertEqual(self.minter.account, mock_account_instance)
        self.assertEqual(self.minter.nonce, 10)
        
    def test_load_contract_no_address(self):
        """Test contract loading fails without address."""
        self.config_values['contract.address'] = None
        
        with self.assertRaises(ContractError) as cm:
            self.minter.load_contract()
        
        self.assertIn("Contract address not provided", str(cm.exception))
        
    @patch('src.minter.load_abi_from_file')
    def test_load_contract_from_file(self, mock_load_abi):
        """Test loading contract with ABI from file."""
        # Set up mocks
        mock_abi = [{"type": "function", "name": "mint"}]
        mock_load_abi.return_value = mock_abi
        
        self.minter.web3 = Mock()
        mock_contract = Mock()
        self.minter.web3.eth.contract.return_value = mock_contract
        
        # Load contract
        self.minter.load_contract()
        
        # Verify ABI was loaded from file
        mock_load_abi.assert_called_once_with('test_abi.json')
        self.minter.web3.eth.contract.assert_called_once()
        self.assertEqual(self.minter.contract, mock_contract)
        
    @patch('src.minter.get_contract_abi_from_explorer')
    def test_load_contract_from_explorer(self, mock_get_abi):
        """Test loading contract with ABI from block explorer."""
        # Remove file path to force explorer fetch
        self.config_values['contract.abi_path'] = None
        
        # Set up mocks
        mock_abi = [{"type": "function", "name": "mint"}]
        mock_get_abi.return_value = mock_abi
        
        self.minter.web3 = Mock()
        mock_contract = Mock()
        self.minter.web3.eth.contract.return_value = mock_contract
        
        # Mock network config
        self.minter.network_config = {
            'explorer': {
                'api_url': 'https://api.test.com'
            }
        }
        
        # Load contract
        self.minter.load_contract()
        
        # Verify ABI was fetched from explorer
        mock_get_abi.assert_called_once()
        self.assertEqual(self.minter.contract, mock_contract)
        
    def test_get_contract_info(self):
        """Test retrieving contract information."""
        # Set up mock contract
        mock_contract = Mock()
        mock_contract.functions.totalSupply.return_value.call.return_value = 100
        mock_contract.functions.maxSupply.return_value.call.return_value = 1000
        mock_contract.functions.mintLive.return_value.call.return_value = True
        
        self.minter.contract = mock_contract
        
        # Get contract info
        info = self.minter.get_contract_info()
        
        # Verify info
        self.assertEqual(info['total_supply'], 100)
        self.assertEqual(info['max_supply'], 1000)
        self.assertTrue(info['mint_live'])
        
    def test_get_wallet_balance(self):
        """Test getting wallet balance."""
        # Set up mocks
        self.minter.web3 = Mock()
        self.minter.web3.eth.get_balance.return_value = 1000000000000000000  # 1 ETH in wei
        self.minter.web3.from_wei.return_value = 1.0
        
        self.minter.account = Mock()
        self.minter.account.address = '0x' + '2' * 40
        
        # Get balance
        balance = self.minter.get_wallet_balance()
        
        # Verify
        self.assertEqual(balance, 1.0)
        self.minter.web3.eth.get_balance.assert_called_once_with('0x' + '2' * 40)
        
    def test_mint_dry_run(self):
        """Test minting in dry run mode."""
        # Set up dry run mode
        self.minter.dry_run = True
        self.minter.contract = Mock()
        self.minter.account = Mock()
        self.minter.account.address = '0x' + '2' * 40
        
        # Perform mint
        result = self.minter.mint()
        
        # Verify no transaction was sent
        self.assertIsNone(result)
        
    @patch('src.minter.Web3')
    def test_build_mint_transaction(self, mock_web3_class):
        """Test building a mint transaction."""
        # Set up mocks
        mock_web3_class.to_checksum_address.side_effect = lambda x: x
        
        self.minter.web3 = Mock()
        self.minter.web3.eth.gas_price = 20000000000  # 20 gwei
        self.minter.web3.eth.estimate_gas.return_value = 150000
        
        self.minter.chain_id = 80085
        self.minter.nonce = 5
        self.minter.account = Mock()
        self.minter.account.address = '0x' + '2' * 40
        
        # Set up contract with batchMint function
        mock_contract = Mock()
        mock_batch_mint = Mock()
        mock_batch_mint.build_transaction.return_value = {
            'chainId': 80085,
            'from': '0x' + '2' * 40,
            'value': 0,
            'gas': 150000,
            'gasPrice': 20000000000,
            'nonce': 5
        }
        mock_contract.functions.batchMint.return_value = mock_batch_mint
        # Add quoteBatchMint for cost calculation
        mock_contract.functions.quoteBatchMint.return_value.call.return_value = (0, 0)
        
        self.minter.contract = mock_contract
        
        # Build transaction
        tx = self.minter._build_mint_transaction('0x' + '4' * 40, 0, 1)
        
        # Verify transaction structure
        self.assertIn('chainId', tx)
        self.assertIn('gas', tx)
        self.assertIn('nonce', tx)
        self.assertEqual(tx['nonce'], 5)
        
    def test_wait_for_mint_live(self):
        """Test waiting for mint to go live."""
        # Set up mock contract
        mock_contract = Mock()
        
        # Simulate mint going live after 3 checks
        call_count = 0
        def mint_live_side_effect():
            nonlocal call_count
            call_count += 1
            return call_count >= 3
        
        mock_contract.functions.mintLive.return_value.call.side_effect = mint_live_side_effect
        self.minter.contract = mock_contract
        
        # Test wait with very short interval
        with patch('time.sleep'):  # Mock sleep to speed up test
            self.minter.wait_for_mint_live(check_interval=0.1)
        
        # Verify mint was checked multiple times
        self.assertEqual(mock_contract.functions.mintLive.return_value.call.call_count, 3)
        
    def test_parse_revert_reason(self):
        """Test parsing revert reasons from transaction errors."""
        from src.utils import parse_revert_reason
        
        # Test various error formats
        test_cases = [
            ("execution reverted: Mint not live", "Mint not live"),
            ("VM Exception while processing transaction: revert Insufficient funds", "Insufficient funds"),
            ("Error: revert: Max supply reached", "Max supply reached"),
            ("Transaction failed with reason string 'Over mint limit'", "Over mint limit"),
            ("Unknown error format", None)
        ]
        
        for error_msg, expected_reason in test_cases:
            error = Exception(error_msg)
            reason = parse_revert_reason(error)
            self.assertEqual(reason, expected_reason)


class TestMinterIntegration(unittest.TestCase):
    """Integration tests for the NFTMinter class."""
    
    @patch('src.minter.Web3')
    @patch('src.minter.Account')
    @patch('src.minter.load_abi_from_file')
    def test_full_minting_flow(self, mock_load_abi, mock_account, mock_web3_class):
        """Test the complete minting flow from connection to transaction."""
        # Create real config
        config = ConfigManager()
        config.data = {
            'wallet': {
                'private_key': '0x' + '1' * 64,
                'address': '0x' + '2' * 40
            },
            'network': {
                'name': 'BERACHAIN',
                'custom_rpc': None
            },
            'contract': {
                'address': '0x' + '3' * 40,
                'abi_path': 'test.json',
                'explorer_api_key': None
            },
            'minting': {
                'group_id': 0,
                'amount': 1,
                'to_address': 'DEFAULT',
                'auto_max': False
            }
        }
        
        # Set up all mocks for full flow
        mock_web3 = Mock()
        mock_web3.is_connected.return_value = True
        mock_web3.eth.chain_id = 80085
        mock_web3.eth.get_transaction_count.return_value = 0
        mock_web3.eth.gas_price = 20000000000
        mock_web3.eth.estimate_gas.return_value = 150000
        mock_web3.eth.account.sign_transaction.return_value = Mock(raw_transaction=b'signed_tx')
        mock_web3.eth.send_raw_transaction.return_value = b'tx_hash'
        mock_web3.eth.wait_for_transaction_receipt.return_value = {'status': 1, 'gasUsed': 140000}
        mock_web3.from_wei.return_value = 1.0
        
        mock_web3_class.return_value = mock_web3
        mock_web3_class.HTTPProvider.return_value = Mock()
        mock_web3_class.to_checksum_address.side_effect = lambda x: x
        
        # Set up account mock
        mock_account_instance = Mock()
        mock_account_instance.address = '0x' + '2' * 40
        mock_account_instance.key = b'test_key'
        mock_account.from_key.return_value = mock_account_instance
        
        # Set up ABI mock
        mock_load_abi.return_value = [{"type": "function", "name": "batchMint"}]
        
        # Set up contract mock
        mock_contract = Mock()
        mock_contract.functions.totalSupply.return_value.call.return_value = 100
        mock_contract.functions.maxSupply.return_value.call.return_value = 1000
        mock_contract.functions.mintLive.return_value.call.return_value = True
        mock_contract.functions.quoteBatchMint.return_value.call.return_value = (0, 0)
        
        mock_batch_mint = Mock()
        mock_batch_mint.build_transaction.return_value = {
            'chainId': 80085,
            'from': '0x' + '2' * 40,
            'value': 0,
            'gas': 150000,
            'gasPrice': 20000000000,
            'nonce': 0
        }
        mock_contract.functions.batchMint.return_value = mock_batch_mint
        
        mock_web3.eth.contract.return_value = mock_contract
        
        # Create minter and execute full flow
        minter = NFTMinter(config, dry_run=False)
        
        # Connect
        minter.connect()
        
        # Load contract
        minter.load_contract()
        
        # Get contract info
        info = minter.get_contract_info()
        self.assertTrue(info['mint_live'])
        
        # Mint
        tx_hash = minter.mint()
        
        # Verify transaction was sent
        self.assertEqual(tx_hash, b'tx_hash'.hex())
        mock_web3.eth.send_raw_transaction.assert_called_once()
        mock_web3.eth.wait_for_transaction_receipt.assert_called_once()


if __name__ == '__main__':
    unittest.main()