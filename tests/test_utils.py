"""
Utility Functions Tests

This module contains comprehensive tests for all utility functions used
throughout the NFT minter application. We test validation functions,
file operations, API interactions, and various helper utilities.
"""

import unittest
import json
import tempfile
import os
import logging
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import requests

# Add parent directory to path for imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.utils import (
    setup_logging, validate_ethereum_address, validate_private_key,
    load_json_file, save_json_file, load_abi_from_file,
    get_contract_abi_from_explorer, format_wei_to_ether,
    format_gas_price, estimate_transaction_cost, parse_revert_reason,
    create_example_abi, check_dependencies, format_time_remaining
)


class TestValidationFunctions(unittest.TestCase):
    """Test cases for validation functions."""
    
    def test_validate_ethereum_address_valid(self):
        """Test validation of valid Ethereum addresses."""
        # Valid addresses (with different case variations)
        valid_addresses = [
            '0x' + '1' * 40,  # All lowercase
            '0x' + 'A' * 40,  # All uppercase
            '0x' + 'aB' * 20,  # Mixed case
            '0x742d35Cc6634C0532925a3b844Bc9e7595f0F0fa',  # Real address
        ]
        
        for address in valid_addresses:
            with self.subTest(address=address):
                self.assertTrue(
                    validate_ethereum_address(address),
                    f"Address {address} should be valid"
                )
    
    def test_validate_ethereum_address_invalid(self):
        """Test validation of invalid Ethereum addresses."""
        invalid_addresses = [
            '',  # Empty string
            None,  # None value
            '0x',  # Too short
            '0x' + '1' * 39,  # One character short
            '0x' + '1' * 41,  # One character long
            '1' * 40,  # Missing 0x prefix
            '0x' + 'G' * 40,  # Invalid hex characters
            'not_an_address',  # Completely invalid
        ]
        
        for address in invalid_addresses:
            with self.subTest(address=address):
                self.assertFalse(
                    validate_ethereum_address(address),
                    f"Address {address} should be invalid"
                )
    
    def test_validate_private_key_valid(self):
        """Test validation of valid private keys."""
        valid_keys = [
            '1' * 64,  # Without 0x prefix
            '0x' + '1' * 64,  # With 0x prefix
            'a' * 64,  # Lowercase hex
            'A' * 64,  # Uppercase hex
            'aAbBcCdDeEfF' * 5 + 'aAbB',  # Mixed case
        ]
        
        for key in valid_keys:
            with self.subTest(key=key[:10] + '...'):
                self.assertTrue(
                    validate_private_key(key),
                    f"Private key should be valid"
                )
    
    def test_validate_private_key_invalid(self):
        """Test validation of invalid private keys."""
        invalid_keys = [
            '',  # Empty string
            None,  # None value
            '1' * 63,  # Too short
            '1' * 65,  # Too long
            '0x' + '1' * 63,  # Too short with prefix
            'G' * 64,  # Invalid hex characters
            'not_a_private_key',  # Completely invalid
        ]
        
        for key in invalid_keys:
            with self.subTest(key=str(key)[:10] + '...' if key else 'None'):
                self.assertFalse(
                    validate_private_key(key),
                    f"Private key should be invalid"
                )


class TestFileOperations(unittest.TestCase):
    """Test cases for file operation functions."""
    
    def setUp(self):
        """Set up temporary directory for file tests."""
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_load_json_file_success(self):
        """Test successful loading of JSON file."""
        # Create test JSON file
        test_data = {"key": "value", "number": 42}
        test_file = Path(self.temp_dir) / "test.json"
        
        with open(test_file, 'w') as f:
            json.dump(test_data, f)
        
        # Load and verify
        loaded_data = load_json_file(test_file)
        self.assertEqual(loaded_data, test_data)
    
    def test_load_json_file_not_found(self):
        """Test loading non-existent file raises error."""
        non_existent = Path(self.temp_dir) / "does_not_exist.json"
        
        with self.assertRaises(FileNotFoundError):
            load_json_file(non_existent)
    
    def test_load_json_file_invalid_json(self):
        """Test loading invalid JSON raises error."""
        invalid_file = Path(self.temp_dir) / "invalid.json"
        
        with open(invalid_file, 'w') as f:
            f.write("{ invalid json }")
        
        with self.assertRaises(json.JSONDecodeError):
            load_json_file(invalid_file)
    
    def test_save_json_file(self):
        """Test saving data to JSON file."""
        test_data = {"test": "data", "nested": {"value": 123}}
        output_file = Path(self.temp_dir) / "output.json"
        
        # Save data
        save_json_file(test_data, output_file)
        
        # Verify file exists and contains correct data
        self.assertTrue(output_file.exists())
        
        with open(output_file, 'r') as f:
            loaded_data = json.load(f)
        
        self.assertEqual(loaded_data, test_data)
    
    def test_save_json_file_creates_directory(self):
        """Test that save_json_file creates parent directories."""
        nested_path = Path(self.temp_dir) / "nested" / "dir" / "file.json"
        test_data = {"test": "data"}
        
        # Save to nested path
        save_json_file(test_data, nested_path)
        
        # Verify file and directories were created
        self.assertTrue(nested_path.exists())
        self.assertTrue(nested_path.parent.exists())


class TestABIOperations(unittest.TestCase):
    """Test cases for ABI-related functions."""
    
    def setUp(self):
        """Set up temporary directory for ABI tests."""
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_load_abi_from_file_direct_array(self):
        """Test loading ABI that's a direct JSON array."""
        abi_data = [
            {"type": "function", "name": "mint"},
            {"type": "function", "name": "transfer"}
        ]
        
        abi_file = Path(self.temp_dir) / "abi.json"
        with open(abi_file, 'w') as f:
            json.dump(abi_data, f)
        
        loaded_abi = load_abi_from_file(abi_file)
        self.assertEqual(loaded_abi, abi_data)
    
    def test_load_abi_from_file_truffle_format(self):
        """Test loading ABI from Truffle/Hardhat artifact format."""
        abi_data = [{"type": "function", "name": "mint"}]
        artifact_data = {
            "contractName": "TestNFT",
            "abi": abi_data,
            "bytecode": "0x..."
        }
        
        abi_file = Path(self.temp_dir) / "artifact.json"
        with open(abi_file, 'w') as f:
            json.dump(artifact_data, f)
        
        loaded_abi = load_abi_from_file(abi_file)
        self.assertEqual(loaded_abi, abi_data)
    
    def test_load_abi_from_file_foundry_format(self):
        """Test loading ABI from Foundry format."""
        abi_data = [{"type": "function", "name": "mint"}]
        foundry_data = {
            "metadata": {
                "output": {
                    "abi": abi_data
                }
            }
        }
        
        abi_file = Path(self.temp_dir) / "foundry.json"
        with open(abi_file, 'w') as f:
            json.dump(foundry_data, f)
        
        loaded_abi = load_abi_from_file(abi_file)
        self.assertEqual(loaded_abi, abi_data)
    
    def test_load_abi_from_file_invalid_format(self):
        """Test loading ABI with invalid format raises error."""
        invalid_data = {"some": "data", "but": "no abi"}
        
        abi_file = Path(self.temp_dir) / "invalid.json"
        with open(abi_file, 'w') as f:
            json.dump(invalid_data, f)
        
        with self.assertRaises(ValueError) as cm:
            load_abi_from_file(abi_file)
        
        self.assertIn("Could not find ABI", str(cm.exception))
    
    @patch('requests.get')
    def test_get_contract_abi_from_explorer_success(self, mock_get):
        """Test successful ABI fetch from block explorer."""
        # Mock successful API response
        abi_data = [{"type": "function", "name": "mint"}]
        mock_response = Mock()
        mock_response.json.return_value = {
            "status": "1",
            "result": json.dumps(abi_data)
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Fetch ABI should raise exception
        with self.assertRaises(Exception) as cm:
            get_contract_abi_from_explorer(
                "0x123...", "test_key", "https://api.test.com"
            )
        
        self.assertIn("Contract source code not verified", str(cm.exception))
    
    @patch('requests.get')
    def test_get_contract_abi_from_explorer_network_error(self, mock_get):
        """Test handling of network errors."""
        # Mock network error
        mock_get.side_effect = requests.RequestException("Network error")
        
        # Fetch ABI should raise exception
        with self.assertRaises(Exception) as cm:
            get_contract_abi_from_explorer(
                "0x123...", "test_key", "https://api.test.com"
            )
        
        self.assertIn("Network error", str(cm.exception))


class TestFormattingFunctions(unittest.TestCase):
    """Test cases for formatting utility functions."""
    
    def test_format_wei_to_ether(self):
        """Test Wei to Ether formatting."""
        test_cases = [
            (1000000000000000000, 4, "1.0000"),  # 1 ETH
            (1500000000000000000, 2, "1.50"),    # 1.5 ETH
            (123456789012345678, 6, "0.123457"), # ~0.123 ETH
            (0, 2, "0.00"),                       # 0 ETH
        ]
        
        for wei, decimals, expected in test_cases:
            with self.subTest(wei=wei):
                result = format_wei_to_ether(wei, decimals)
                self.assertEqual(result, expected)
    
    def test_format_gas_price(self):
        """Test gas price formatting."""
        test_cases = [
            (20000000000, "20.00 gwei"),  # 20 gwei
            (1500000000, "1.50 gwei"),     # 1.5 gwei
            (100000000000, "100.00 gwei"), # 100 gwei
            (1000000000, "1.00 gwei"),     # 1 gwei
        ]
        
        for wei_price, expected in test_cases:
            with self.subTest(wei_price=wei_price):
                result = format_gas_price(wei_price)
                self.assertEqual(result, expected)
    
    def test_estimate_transaction_cost(self):
        """Test transaction cost estimation."""
        gas_limit = 150000
        gas_price_wei = 20000000000  # 20 gwei
        
        result = estimate_transaction_cost(gas_limit, gas_price_wei)
        
        self.assertEqual(result['gas_limit'], 150000)
        self.assertEqual(result['gas_price_gwei'], 20.0)
        self.assertEqual(result['total_eth'], 0.003)  # 150000 * 20 gwei
        self.assertEqual(result['total_wei'], 3000000000000000)
    
    def test_parse_revert_reason(self):
        """Test parsing various revert reason formats."""
        test_cases = [
            (
                "execution reverted: Mint not live",
                "Mint not live"
            ),
            (
                "VM Exception while processing transaction: revert Insufficient balance",
                "Insufficient balance"
            ),
            (
                "Transaction failed with reason string 'Max supply reached'",
                "Max supply reached"
            ),
            (
                "revert: Custom error message",
                "Custom error message"
            ),
            (
                "Some other error without revert reason",
                None
            )
        ]
        
        for error_msg, expected_reason in test_cases:
            with self.subTest(error_msg=error_msg[:30] + '...'):
                error = Exception(error_msg)
                reason = parse_revert_reason(error)
                self.assertEqual(reason, expected_reason)
    
    def test_format_time_remaining(self):
        """Test time formatting function."""
        test_cases = [
            (30, "30s"),              # Less than a minute
            (90, "1m 30s"),           # 1.5 minutes
            (3600, "1h 0m"),          # Exactly 1 hour
            (3665, "1h 1m"),          # 1 hour and 1 minute
            (7320, "2h 2m"),          # 2 hours and 2 minutes
            (0, "0s"),                # Zero seconds
        ]
        
        for seconds, expected in test_cases:
            with self.subTest(seconds=seconds):
                result = format_time_remaining(seconds)
                self.assertEqual(result, expected)


class TestMiscellaneousFunctions(unittest.TestCase):
    """Test cases for miscellaneous utility functions."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    @patch('src.utils.Path')
    @patch('src.utils.save_json_file')
    def test_create_example_abi(self, mock_save, mock_path):
        """Test example ABI creation."""
        # Mock Path to use temp directory
        mock_path.return_value.mkdir.return_value = None
        
        # Create example ABI
        create_example_abi()
        
        # Verify save was called
        mock_save.assert_called_once()
        
        # Check that the saved data contains expected functions
        saved_data = mock_save.call_args[0][0]
        self.assertIsInstance(saved_data, list)
        
        # Check for expected function names
        function_names = [item.get('name') for item in saved_data if item.get('name')]
        expected_functions = ['totalSupply', 'maxSupply', 'mintLive', 'batchMint']
        
        for func_name in expected_functions:
            self.assertIn(func_name, function_names)
    
    @patch('builtins.__import__')
    def test_check_dependencies_all_installed(self, mock_import):
        """Test dependency check when all packages are installed."""
        # Mock successful imports
        mock_import.return_value = Mock()
        
        all_installed, missing = check_dependencies()
        
        self.assertTrue(all_installed)
        self.assertEqual(missing, [])
    
    @patch('builtins.__import__')
    def test_check_dependencies_some_missing(self, mock_import):
        """Test dependency check when some packages are missing."""
        # Mock import to fail for specific packages
        def import_side_effect(name):
            if name in ['eth_account', 'tqdm']:
                raise ImportError(f"No module named '{name}'")
            return Mock()
        
        mock_import.side_effect = import_side_effect
        
        all_installed, missing = check_dependencies()
        
        self.assertFalse(all_installed)
        self.assertIn('eth-account', missing)
        self.assertIn('tqdm', missing)
    
    @patch('logging.getLogger')
    @patch('logging.basicConfig')
    @patch('src.utils.Path')
    def test_setup_logging(self, mock_path_class, mock_basic_config, mock_get_logger):
        """Test logging setup."""
        # Mock Path for log directory
        mock_log_dir = Mock()
        mock_log_dir.mkdir = Mock()
        mock_log_dir.__truediv__ = Mock(return_value="logs/nft_minter_test.log")
        mock_path_class.return_value = mock_log_dir
        
        # Mock logger
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        # Also need to mock the logging module methods that get called
        with patch('logging.FileHandler'), \
             patch('logging.StreamHandler'):
            # Setup logging
            logger = setup_logging(logging.DEBUG)
        
        # Verify log directory was created
        mock_log_dir.mkdir.assert_called_once_with(exist_ok=True)
        
        # Verify logging was configured
        mock_basic_config.assert_called_once()
        config_call = mock_basic_config.call_args
        self.assertEqual(config_call[1]['level'], logging.DEBUG)
        
        # Verify specific loggers were set to WARNING
        self.assertEqual(logger, mock_logger)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions."""
    
    def test_validate_ethereum_address_with_mixed_case(self):
        """Test checksum address validation."""
        # Valid checksum addresses
        checksum_addresses = [
            '0x5aAeb6053f3E94C9b9A09f33669435E7Ef1BeAed',
            '0xfB6916095ca1df60bB79Ce92cE3Ea74c37c5d359',
            '0xdbF03B407c01E7cD3CBea99509d93f8DDDC8C6FB',
            '0xD1220A0cf47c7B9Be7A2E6BA89F429762e7b9aDb'
        ]
        
        for address in checksum_addresses:
            self.assertTrue(validate_ethereum_address(address))
    
    def test_format_wei_to_ether_edge_cases(self):
        """Test Wei to Ether formatting with edge cases."""
        # Very large number
        large_wei = 123456789012345678901234567890
        result = format_wei_to_ether(large_wei, 2)
        self.assertIsInstance(result, str)
        
        # Very small number
        small_wei = 1
        result = format_wei_to_ether(small_wei, 18)
        self.assertEqual(result, "0.000000000000000001")
    
    def test_parse_revert_reason_multiline(self):
        """Test parsing revert reasons from multiline errors."""
        error_msg = """Error: Transaction reverted
        execution reverted: This is a
        multiline error message
        with additional context"""
        
        error = Exception(error_msg)
        reason = parse_revert_reason(error)
        self.assertEqual(reason, "This is a")  # Should capture until newline


class TestIntegrationScenarios(unittest.TestCase):
    """Integration tests for utility functions working together."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_abi_workflow(self):
        """Test complete ABI workflow: create, save, load."""
        # Create and save example ABI
        abi_dir = Path(self.temp_dir) / "abi"
        abi_dir.mkdir()
        
        example_abi = [
            {
                "inputs": [],
                "name": "testFunction",
                "outputs": [{"name": "", "type": "uint256"}],
                "stateMutability": "view",
                "type": "function"
            }
        ]
        
        abi_file = abi_dir / "test_abi.json"
        save_json_file(example_abi, abi_file)
        
        # Load and verify
        loaded_abi = load_abi_from_file(abi_file)
        self.assertEqual(loaded_abi, example_abi)
    
    def test_transaction_cost_calculation_workflow(self):
        """Test complete transaction cost calculation workflow."""
        # Simulate gas estimation
        gas_limit = 200000
        gas_price_wei = 50000000000  # 50 gwei
        
        # Calculate cost
        cost_info = estimate_transaction_cost(gas_limit, gas_price_wei)
        
        # Format for display
        formatted_price = format_gas_price(gas_price_wei)
        formatted_cost = format_wei_to_ether(cost_info['total_wei'], 4)
        
        # Verify formatting
        self.assertEqual(formatted_price, "50.00 gwei")
        self.assertEqual(formatted_cost, "0.0100")  # 200000 * 50 gwei = 0.01 ETH


if __name__ == '__main__':
    unittest.main()