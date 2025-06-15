"""
Utility Functions Tests

This module contains comprehensive tests for all utility functions used
throughout the NFT minter application. We test validation functions,
file operations, API interactions, and various helper utilities.

The tests are organized into logical groups to make them easy to understand
and maintain. Each test class focuses on a specific area of functionality.
"""

import unittest
import json
import tempfile
import os
import logging
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, mock_open
import requests
from datetime import datetime

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
    """
    Test cases for validation functions.
    
    These tests ensure that our address and private key validation
    functions correctly identify valid and invalid inputs. This is
    crucial for preventing errors when interacting with the blockchain.
    """
    
    def test_validate_ethereum_address_valid(self):
        """Test validation of valid Ethereum addresses."""
        # Valid addresses come in different formats - let's test them all
        valid_addresses = [
            '0x' + '1' * 40,  # All lowercase hex
            '0x' + 'A' * 40,  # All uppercase hex
            '0x' + 'aB' * 20,  # Mixed case pattern
            '0x742d35Cc6634C0532925a3b844Bc9e7595f0F0fa',  # Real checksum address
            '0x5aAeb6053f3E94C9b9A09f33669435E7Ef1BeAed',  # Another real address
        ]
        
        for address in valid_addresses:
            with self.subTest(address=address):
                # Each address should validate as True
                self.assertTrue(
                    validate_ethereum_address(address),
                    f"Address {address} should be valid"
                )
    
    def test_validate_ethereum_address_invalid(self):
        """Test validation of invalid Ethereum addresses."""
        # These are all the ways an address can be wrong
        invalid_addresses = [
            '',  # Empty string
            None,  # None value
            '0x',  # Just the prefix
            '0x' + '1' * 39,  # Too short by one character
            '0x' + '1' * 41,  # Too long by one character
            '1' * 40,  # Missing 0x prefix
            '0x' + 'G' * 40,  # Invalid hex characters (G is not hex)
            'not_an_address',  # Completely wrong format
            '0X' + '1' * 40,  # Wrong case for prefix (should be 0x not 0X)
        ]
        
        for address in invalid_addresses:
            with self.subTest(address=address):
                # Each should validate as False
                self.assertFalse(
                    validate_ethereum_address(address),
                    f"Address {address} should be invalid"
                )
    
    def test_validate_private_key_valid(self):
        """Test validation of valid private keys."""
        # Private keys can come with or without 0x prefix
        valid_keys = [
            '1' * 64,  # Without 0x prefix
            '0x' + '1' * 64,  # With 0x prefix
            'a' * 64,  # Lowercase hex
            'A' * 64,  # Uppercase hex
            'aAbBcCdDeEfF' * 5 + 'aAbB',  # Mixed case (64 chars total)
            '0x' + 'deadbeef' * 8,  # Common test pattern
        ]
        
        for key in valid_keys:
            with self.subTest(key=key[:10] + '...'):
                # Show only first 10 chars in test name for security
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
            '0x',  # Just prefix
            '0x' + 'zzzz' + '1' * 60,  # Contains non-hex chars
        ]
        
        for key in invalid_keys:
            with self.subTest(key=str(key)[:10] + '...' if key else 'None'):
                self.assertFalse(
                    validate_private_key(key),
                    f"Private key should be invalid"
                )


class TestFileOperations(unittest.TestCase):
    """
    Test cases for file operation functions.
    
    These tests ensure our file I/O operations work correctly,
    including error handling for missing or malformed files.
    """
    
    def setUp(self):
        """Create a temporary directory for file tests."""
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up temporary directory after tests."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_load_json_file_success(self):
        """Test successful loading of JSON file."""
        # Create a test JSON file with some data
        test_data = {
            "key": "value", 
            "number": 42,
            "nested": {"inner": "data"},
            "array": [1, 2, 3]
        }
        test_file = Path(self.temp_dir) / "test.json"
        
        # Write the test data to file
        with open(test_file, 'w') as f:
            json.dump(test_data, f)
        
        # Load it back and verify
        loaded_data = load_json_file(test_file)
        self.assertEqual(loaded_data, test_data)
        
        # Test with string path as well as Path object
        loaded_data_str = load_json_file(str(test_file))
        self.assertEqual(loaded_data_str, test_data)
    
    def test_load_json_file_not_found(self):
        """Test loading non-existent file raises appropriate error."""
        non_existent = Path(self.temp_dir) / "does_not_exist.json"
        
        # Should raise FileNotFoundError
        with self.assertRaises(FileNotFoundError):
            load_json_file(non_existent)
    
    def test_load_json_file_invalid_json(self):
        """Test loading invalid JSON raises appropriate error."""
        invalid_file = Path(self.temp_dir) / "invalid.json"
        
        # Write invalid JSON (missing closing brace)
        with open(invalid_file, 'w') as f:
            f.write("{ invalid json }")
        
        # Should raise JSONDecodeError
        with self.assertRaises(json.JSONDecodeError):
            load_json_file(invalid_file)
    
    def test_save_json_file(self):
        """Test saving data to JSON file."""
        test_data = {
            "test": "data", 
            "nested": {"value": 123},
            "list": ["a", "b", "c"]
        }
        output_file = Path(self.temp_dir) / "output.json"
        
        # Save data
        save_json_file(test_data, output_file)
        
        # Verify file exists
        self.assertTrue(output_file.exists())
        
        # Verify content is correct
        with open(output_file, 'r') as f:
            loaded_data = json.load(f)
        
        self.assertEqual(loaded_data, test_data)
        
        # Verify it's nicely formatted (has indentation)
        with open(output_file, 'r') as f:
            content = f.read()
        self.assertIn('  ', content)  # Should have indentation
    
    def test_save_json_file_creates_directory(self):
        """Test that save_json_file creates parent directories if needed."""
        # Create a nested path that doesn't exist
        nested_path = Path(self.temp_dir) / "nested" / "dir" / "file.json"
        test_data = {"test": "data"}
        
        # Parent directories don't exist yet
        self.assertFalse(nested_path.parent.exists())
        
        # Save to nested path
        save_json_file(test_data, nested_path)
        
        # Verify file and directories were created
        self.assertTrue(nested_path.exists())
        self.assertTrue(nested_path.parent.exists())
        
        # Verify content
        with open(nested_path, 'r') as f:
            loaded = json.load(f)
        self.assertEqual(loaded, test_data)


class TestABIOperations(unittest.TestCase):
    """
    Test cases for ABI-related functions.
    
    ABIs (Application Binary Interfaces) define how to interact with
    smart contracts. These tests ensure we can load ABIs from various
    file formats and fetch them from block explorers.
    """
    
    def setUp(self):
        """Set up temporary directory for ABI tests."""
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_load_abi_from_file_direct_array(self):
        """Test loading ABI that's a direct JSON array."""
        # This is the simplest ABI format - just an array
        abi_data = [
            {"type": "function", "name": "mint", "inputs": [], "outputs": []},
            {"type": "function", "name": "transfer", "inputs": [{"name": "to", "type": "address"}]}
        ]
        
        abi_file = Path(self.temp_dir) / "abi.json"
        with open(abi_file, 'w') as f:
            json.dump(abi_data, f)
        
        loaded_abi = load_abi_from_file(abi_file)
        self.assertEqual(loaded_abi, abi_data)
    
    def test_load_abi_from_file_truffle_format(self):
        """Test loading ABI from Truffle/Hardhat artifact format."""
        # Truffle and Hardhat wrap the ABI in a larger object
        abi_data = [{"type": "function", "name": "mint"}]
        artifact_data = {
            "contractName": "TestNFT",
            "abi": abi_data,  # ABI is nested here
            "bytecode": "0x608060405234801561001057600080fd5b50",
            "networks": {}
        }
        
        abi_file = Path(self.temp_dir) / "artifact.json"
        with open(abi_file, 'w') as f:
            json.dump(artifact_data, f)
        
        loaded_abi = load_abi_from_file(abi_file)
        self.assertEqual(loaded_abi, abi_data)
    
    def test_load_abi_from_file_foundry_format(self):
        """Test loading ABI from Foundry format."""
        # Foundry has a different nesting structure
        abi_data = [{"type": "function", "name": "mint"}]
        foundry_data = {
            "metadata": {
                "output": {
                    "abi": abi_data  # Deeply nested
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
        # This JSON doesn't contain an ABI in any recognized format
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
        # When the explorer returns a successful response, we should get the ABI
        abi_data = [{"type": "function", "name": "mint"}]
        
        # Mock the response object
        mock_response = Mock()
        mock_response.json.return_value = {
            "status": "1",  # Status 1 means success
            "result": json.dumps(abi_data)  # ABI is JSON-encoded in result
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Call the function - it should succeed and return the parsed ABI
        result = get_contract_abi_from_explorer(
            "0x123...", "test_key", "https://api.test.com"
        )
        
        # Verify we got the correct ABI back
        self.assertEqual(result, abi_data)
        
        # Verify the API was called correctly
        mock_get.assert_called_once_with(
            "https://api.test.com",
            params={
                "module": "contract",
                "action": "getabi",
                "address": "0x123...",
                "apikey": "test_key"
            },
            timeout=30
        )
    
    @patch('requests.get')
    def test_get_contract_abi_from_explorer_api_error(self, mock_get):
        """Test handling of API error response."""
        # When the explorer returns an error, we should get an exception
        mock_response = Mock()
        mock_response.json.return_value = {
            "status": "0",  # Status 0 means error
            "result": "Contract source code not verified"
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # This should raise an exception with the error message
        with self.assertRaises(Exception) as cm:
            get_contract_abi_from_explorer(
                "0x123...", "test_key", "https://api.test.com"
            )
        
        self.assertIn("API error", str(cm.exception))
        self.assertIn("Contract source code not verified", str(cm.exception))
    
    @patch('requests.get')
    def test_get_contract_abi_from_explorer_network_error(self, mock_get):
        """Test handling of network errors."""
        # Simulate a network failure
        mock_get.side_effect = requests.RequestException("Network error")
        
        # Should wrap the network error in our exception
        with self.assertRaises(Exception) as cm:
            get_contract_abi_from_explorer(
                "0x123...", "test_key", "https://api.test.com"
            )
        
        self.assertIn("Network error", str(cm.exception))


class TestFormattingFunctions(unittest.TestCase):
    """
    Test cases for formatting utility functions.
    
    These functions help display blockchain data in human-readable formats,
    which is crucial for user interfaces and logging.
    """
    
    def test_format_wei_to_ether(self):
        """Test Wei to Ether formatting with various amounts."""
        # Test cases: (wei_amount, decimal_places, expected_output)
        test_cases = [
            (1000000000000000000, 4, "1.0000"),  # Exactly 1 ETH
            (1500000000000000000, 2, "1.50"),    # 1.5 ETH
            (123456789012345678, 6, "0.123457"), # Small amount with rounding
            (0, 2, "0.00"),                       # Zero
            (1, 18, "0.000000000000000001"),     # Smallest unit
        ]
        
        for wei, decimals, expected in test_cases:
            with self.subTest(wei=wei, decimals=decimals):
                result = format_wei_to_ether(wei, decimals)
                self.assertEqual(result, expected)
    
    def test_format_gas_price(self):
        """Test gas price formatting from Wei to Gwei."""
        # Gas prices are typically shown in Gwei (1 Gwei = 10^9 Wei)
        test_cases = [
            (20000000000, "20.00 gwei"),   # 20 Gwei (typical)
            (1500000000, "1.50 gwei"),      # 1.5 Gwei (very low)
            (100000000000, "100.00 gwei"),  # 100 Gwei (high)
            (1000000000, "1.00 gwei"),      # Exactly 1 Gwei
            (123456789, "0.12 gwei"),       # Sub-gwei amount
        ]
        
        for wei_price, expected in test_cases:
            with self.subTest(wei_price=wei_price):
                result = format_gas_price(wei_price)
                self.assertEqual(result, expected)
    
    def test_estimate_transaction_cost(self):
        """Test transaction cost estimation calculations."""
        # Test with typical values
        gas_limit = 150000  # Typical for NFT mint
        gas_price_wei = 20000000000  # 20 Gwei
        
        result = estimate_transaction_cost(gas_limit, gas_price_wei)
        
        # Verify all fields are calculated correctly
        self.assertEqual(result['gas_limit'], 150000)
        self.assertEqual(result['gas_price_gwei'], 20.0)
        self.assertEqual(result['total_eth'], 0.003)  # 150000 * 20 Gwei = 0.003 ETH
        self.assertEqual(result['total_wei'], 3000000000000000)  # In Wei
    
    def test_parse_revert_reason(self):
        """Test parsing various revert reason formats from errors."""
        # Different blockchains and tools format revert reasons differently
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
                None  # No revert reason found
            )
        ]
        
        for error_msg, expected_reason in test_cases:
            with self.subTest(error_msg=error_msg[:30] + '...'):
                error = Exception(error_msg)
                reason = parse_revert_reason(error)
                self.assertEqual(reason, expected_reason)
    
    def test_format_time_remaining(self):
        """Test time formatting for human-readable display."""
        test_cases = [
            (30, "30s"),              # Less than a minute
            (90, "1m 30s"),           # 1.5 minutes
            (3600, "1h 0m"),          # Exactly 1 hour
            (3665, "1h 1m"),          # 1 hour and 1 minute
            (7320, "2h 2m"),          # 2 hours and 2 minutes
            (0, "0s"),                # Zero seconds
            (59, "59s"),              # Just under a minute
            (3599, "59m 59s"),        # Just under an hour
        ]
        
        for seconds, expected in test_cases:
            with self.subTest(seconds=seconds):
                result = format_time_remaining(seconds)
                self.assertEqual(result, expected)


class TestMiscellaneousFunctions(unittest.TestCase):
    """
    Test cases for miscellaneous utility functions.
    
    These include dependency checking, logging setup, and other
    helper functions that don't fit into the other categories.
    """
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    @patch('src.utils.Path')
    @patch('src.utils.save_json_file')
    def test_create_example_abi(self, mock_save):
        """Test example ABI creation"""

        with patch("pathlib.Path.mkdir") as mock_mkdir:

            # Create example ABI
            create_example_abi()
        
            # Verify mkdir was called to create the abi directory
            mock_mkdir.assert_any_call(parents=True, exist_ok=True)
        
            # Verify save was called
            mock_save.assert_called_once()
        
            # Check that the saved data is a list (ABI format)
            saved_data, saved_path = mock_save.call_args[0]
            self.assertIsInstance(saved_data, list)
            self.assertIn("example_nft_abi.json", str(saved_path))

            # Check for expected function names in the ABI
            function_names = [item.get('name') for item in saved_data if item.get('name')]
            expected_functions = ['totalSupply', 'maxSupply', 'mintLive', 'batchMint']

            for func_name in expected_functions:
                self.assertIn(func_name, function_names)
    
    @patch('builtins.__import__')
    def test_check_dependencies_all_installed(self, mock_import):
        """Test dependency check when all packages are installed."""
        # Mock successful imports - everything is installed
        mock_import.return_value = Mock()
        
        all_installed, missing = check_dependencies()
        
        self.assertTrue(all_installed)
        self.assertEqual(missing, [])
        
        # Verify we tried to import the expected packages
        expected_imports = ['web3', 'eth_account', 'requests', 'tqdm']
        actual_imports = [call[0][0] for call in mock_import.call_args_list]
        for pkg in expected_imports:
            self.assertIn(pkg, actual_imports)
    
    @patch('builtins.__import__')
    def test_check_dependencies_some_missing(self, mock_import):
        """Test dependency check when some packages are missing."""
        # Mock import to fail for specific packages
        def import_side_effect(name, *args, **kwargs):
            # Simulate that eth_account and tqdm are not installed
            if name in ['eth_account', 'tqdm']:
                raise ImportError(f"No module named '{name}'")
            return Mock()
        
        mock_import.side_effect = import_side_effect
        
        all_installed, missing = check_dependencies()
        
        # Should report that not all are installed
        self.assertFalse(all_installed)
        
        # Should list the missing packages with their pip names
        self.assertIn('eth-account', missing)  # Note: pip name, not import name
        self.assertIn('tqdm', missing)
        self.assertEqual(len(missing), 2)
    
    @patch('logging.getLogger')
    @patch('logging.basicConfig')
    @patch('src.utils.datetime')
    @patch('src.utils.Path')
    def test_setup_logging(self, mock_path_class, mock_datetime, mock_basic_config, mock_get_logger):
        """Test logging setup with comprehensive mocking."""
        # Mock the datetime to return a fixed timestamp
        mock_now = Mock()
        mock_now.strftime.return_value = "20240115_120000"
        mock_datetime.now.return_value = mock_now
        
        # Mock Path to handle directory creation and file path operations
        mock_log_dir = Mock()
        mock_log_dir.mkdir = Mock()
        mock_log_file = Mock()
        mock_log_dir.__truediv__ = Mock(return_value=mock_log_file)
        mock_path_class.return_value = mock_log_dir
        
        # Mock the logger that will be returned
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        # Mock the handlers that will be created
        with patch('logging.FileHandler') as mock_file_handler, \
             patch('logging.StreamHandler') as mock_stream_handler:
            
            # Setup logging with DEBUG level
            logger = setup_logging(logging.DEBUG)
        
        # Verify log directory was created
        mock_log_dir.mkdir.assert_called_once_with(exist_ok=True)
        
        # Verify the log file path was constructed correctly
        mock_log_dir.__truediv__.assert_called_once_with("nft_minter_20240115_120000.log")
        
        # Verify logging was configured with correct parameters
        mock_basic_config.assert_called_once()
        config_kwargs = mock_basic_config.call_args[1]
        self.assertEqual(config_kwargs['level'], logging.DEBUG)
        self.assertEqual(config_kwargs['format'], '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # Verify we got the logger back
        self.assertEqual(logger, mock_logger)


class TestEdgeCases(unittest.TestCase):
    """
    Test edge cases and error conditions.
    
    These tests ensure our functions handle unusual inputs gracefully
    and don't crash with unexpected data.
    """
    
    def test_validate_ethereum_address_with_mixed_case(self):
        """Test validation of checksum addresses with specific mixed case."""
        # These are real Ethereum checksum addresses with specific capitalization
        checksum_addresses = [
            '0x5aAeb6053f3E94C9b9A09f33669435E7Ef1BeAed',
            '0xfB6916095ca1df60bB79Ce92cE3Ea74c37c5d359',
            '0xdbF03B407c01E7cD3CBea99509d93f8DDDC8C6FB',
            '0xD1220A0cf47c7B9Be7A2E6BA89F429762e7b9aDb'
        ]
        
        for address in checksum_addresses:
            # These should all validate successfully
            self.assertTrue(validate_ethereum_address(address))
    
    def test_format_wei_to_ether_edge_cases(self):
        """Test Wei to Ether formatting with extreme values."""
        # Very large number (more ETH than exists)
        large_wei = 123456789012345678901234567890
        result = format_wei_to_ether(large_wei, 2)
        self.assertIsInstance(result, str)
        # Should handle the large number without error
        self.assertTrue(len(result) > 10)  # It's a big number
        
        # Very small number (1 Wei)
        small_wei = 1
        result = format_wei_to_ether(small_wei, 18)
        self.assertEqual(result, "0.000000000000000001")
        
        # Maximum decimals
        result_max = format_wei_to_ether(123456789012345678, 18)
        self.assertEqual(result_max, "0.123456789012345678")
    
    def test_parse_revert_reason_multiline(self):
        """Test parsing revert reasons from multiline error messages."""
        # Multiline error messages are common in stack traces
        error_msg = """Error: Transaction reverted
        execution reverted: This is a
        multiline error message
        with additional context"""
        
        error = Exception(error_msg)
        reason = parse_revert_reason(error)
        
        # Should capture up to the newline in the revert message
        self.assertEqual(reason, "This is a")
        
        # Test another format
        error_msg2 = "Error: VM Exception\nrevert: Out of tokens\nStack trace follows"
        error2 = Exception(error_msg2)
        reason2 = parse_revert_reason(error2)
        self.assertEqual(reason2, "Out of tokens")


class TestIntegrationScenarios(unittest.TestCase):
    """
    Integration tests for utility functions working together.
    
    These tests verify that our utility functions work correctly
    when used in combination, simulating real-world usage patterns.
    """
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_abi_workflow(self):
        """Test complete ABI workflow: create, save, and load."""
        # This simulates the full lifecycle of working with an ABI
        abi_dir = Path(self.temp_dir) / "abi"
        abi_dir.mkdir()
        
        # Create a sample ABI
        example_abi = [
            {
                "inputs": [],
                "name": "testFunction",
                "outputs": [{"name": "", "type": "uint256"}],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [{"name": "amount", "type": "uint256"}],
                "name": "mint",
                "outputs": [],
                "stateMutability": "payable",
                "type": "function"
            }
        ]
        
        # Save it
        abi_file = abi_dir / "test_abi.json"
        save_json_file(example_abi, abi_file)
        
        # Load it back
        loaded_abi = load_abi_from_file(abi_file)
        
        # Verify it matches
        self.assertEqual(loaded_abi, example_abi)
        
        # Verify we can also load it as a Truffle artifact
        truffle_artifact = {
            "contractName": "TestContract",
            "abi": example_abi,
            "networks": {}
        }
        
        truffle_file = abi_dir / "truffle_artifact.json"
        save_json_file(truffle_artifact, truffle_file)
        
        loaded_from_truffle = load_abi_from_file(truffle_file)
        self.assertEqual(loaded_from_truffle, example_abi)
    
    def test_transaction_cost_calculation_workflow(self):
        """Test complete transaction cost calculation and formatting workflow."""
        # This simulates calculating and displaying transaction costs
        
        # Typical values for an NFT mint
        gas_limit = 200000
        gas_price_wei = 50000000000  # 50 Gwei
        
        # Calculate the cost
        cost_info = estimate_transaction_cost(gas_limit, gas_price_wei)
        
        # Format individual components for display
        formatted_price = format_gas_price(gas_price_wei)
        formatted_cost = format_wei_to_ether(cost_info['total_wei'], 4)
        
        # Verify the formatted outputs
        self.assertEqual(formatted_price, "50.00 gwei")
        self.assertEqual(formatted_cost, "0.0100")  # 200000 * 50 gwei = 0.01 ETH
        
        # Verify the cost calculation
        self.assertEqual(cost_info['gas_limit'], 200000)
        self.assertEqual(cost_info['gas_price_gwei'], 50.0)
        self.assertEqual(cost_info['total_eth'], 0.01)
        
        # Test with a different scenario - low gas price
        low_gas_price = 1000000000  # 1 Gwei
        low_cost_info = estimate_transaction_cost(gas_limit, low_gas_price)
        
        self.assertEqual(low_cost_info['total_eth'], 0.0002)  # Much cheaper!
    
    def test_validation_and_error_handling_workflow(self):
        """Test validation functions with error handling."""
        # Test a complete validation workflow
        
        # Valid inputs should pass
        valid_address = "0x742d35Cc6634C0532925a3b844Bc9e7595f0F0fa"
        valid_key = "0x" + "a" * 64
        
        self.assertTrue(validate_ethereum_address(valid_address))
        self.assertTrue(validate_private_key(valid_key))
        
        # Invalid inputs should fail gracefully
        invalid_inputs = [
            "",           # Empty
            None,         # None
            "invalid",    # Wrong format
            123,          # Wrong type
        ]
        
        for invalid_input in invalid_inputs:
            # Should return False, not crash
            self.assertFalse(validate_ethereum_address(invalid_input))
            self.assertFalse(validate_private_key(invalid_input))
    
    def test_time_formatting_for_user_display(self):
        """Test time formatting for various durations."""
        # Simulate displaying estimated wait times to users
        
        test_scenarios = [
            (10, "Confirming in 10s"),
            (90, "Estimated wait: 1m 30s"),
            (3660, "Time remaining: 1h 1m"),
            (0, "Complete!"),
        ]
        
        for seconds, message_template in test_scenarios:
            if seconds == 0:
                expected = "Complete!"
            else:
                time_str = format_time_remaining(seconds)
                expected = message_template.replace(
                    f"{seconds}s", time_str
                ).replace(
                    "1m 30s", time_str
                ).replace(
                    "1h 1m", time_str
                )
            
            # Just verify the time formatting works
            formatted = format_time_remaining(seconds)
            self.assertIsInstance(formatted, str)
            self.assertNotEqual(formatted, "")


class TestRealWorldScenarios(unittest.TestCase):
    """
    Test real-world scenarios that combine multiple utilities.
    
    These tests simulate actual use cases from the NFT minter application.
    """
    
    def test_user_input_validation_flow(self):
        """Test the complete flow of validating user configuration."""
        # Simulate validating a user's configuration file
        
        config = {
            "wallet": {
                "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0F0fa",
                "private_key": "0x" + "1" * 64
            },
            "contract": {
                "address": "0x1234567890123456789012345678901234567890"
            }
        }
        
        # Validate all addresses
        self.assertTrue(validate_ethereum_address(config["wallet"]["address"]))
        self.assertTrue(validate_ethereum_address(config["contract"]["address"]))
        self.assertTrue(validate_private_key(config["wallet"]["private_key"]))
        
        # Test with invalid configuration
        invalid_config = {
            "wallet": {
                "address": "not_an_address",
                "private_key": "not_a_key"
            }
        }
        
        self.assertFalse(validate_ethereum_address(invalid_config["wallet"]["address"]))
        self.assertFalse(validate_private_key(invalid_config["wallet"]["private_key"]))
    
    def test_gas_estimation_display(self):
        """Test displaying gas estimates to users."""
        # Simulate showing users the cost of their transaction
        
        # Current gas price from network
        current_gas_price = 35000000000  # 35 Gwei
        
        # Different transaction types have different gas requirements
        transactions = [
            ("Simple Transfer", 21000),
            ("NFT Mint", 150000),
            ("Batch Mint (5 NFTs)", 500000),
        ]
        
        for tx_type, gas_limit in transactions:
            cost = estimate_transaction_cost(gas_limit, current_gas_price)
            
            # Verify cost calculation
            self.assertEqual(cost['gas_limit'], gas_limit)
            self.assertGreater(cost['total_eth'], 0)
            
            # Format for display
            formatted_cost = format_wei_to_ether(cost['total_wei'], 4)
            formatted_gas = format_gas_price(current_gas_price)
            
            # These should be strings ready for display
            self.assertIsInstance(formatted_cost, str)
            self.assertIsInstance(formatted_gas, str)
            self.assertIn("gwei", formatted_gas)
    
    @patch('requests.get')
    def test_contract_deployment_verification(self, mock_get):
        """Test verifying a newly deployed contract."""
        # Simulate checking if a contract's ABI is verified on explorer
        
        contract_address = "0x1234567890123456789012345678901234567890"
        
        # First attempt - not verified yet
        mock_response_unverified = Mock()
        mock_response_unverified.json.return_value = {
            "status": "0",
            "result": "Contract source code not verified"
        }
        mock_response_unverified.raise_for_status.return_value = None
        mock_get.return_value = mock_response_unverified
        
        # Should fail to get ABI
        with self.assertRaises(Exception) as cm:
            get_contract_abi_from_explorer(contract_address, "api_key", "https://api.etherscan.io/api")
        
        self.assertIn("not verified", str(cm.exception))
        
        # Later attempt - now verified
        abi_data = [
            {"type": "function", "name": "mint"},
            {"type": "function", "name": "totalSupply"}
        ]
        mock_response_verified = Mock()
        mock_response_verified.json.return_value = {
            "status": "1",
            "result": json.dumps(abi_data)
        }
        mock_get.return_value = mock_response_verified
        
        # Should successfully get ABI
        result = get_contract_abi_from_explorer(contract_address, "api_key", "https://api.etherscan.io/api")
        self.assertEqual(result, abi_data)


class TestErrorMessages(unittest.TestCase):
    """
    Test that error messages are helpful and informative.
    
    Good error messages are crucial for debugging issues in production.
    """
    
    def test_parse_revert_reason_various_formats(self):
        """Test parsing revert reasons from various error formats."""
        # Different tools and chains format errors differently
        error_formats = [
            # Hardhat style
            ("Error: VM Exception while processing transaction: reverted with reason string 'Mint not live'", "Mint not live"),
            # Ganache style
            ("Transaction: 0x123... exited with an error (status 0). Reason given: Max supply reached.", "Max supply reached"),
            # Generic revert
            ("execution reverted: Insufficient funds", "Insufficient funds"),
            # Custom error
            ("error: MintNotActive()", None),  # Custom errors need special handling
            # Panic code
            ("Panic: 0x11", None),  # Arithmetic overflow
        ]
        
        for error_msg, expected in error_formats:
            error = Exception(error_msg)
            result = parse_revert_reason(error)
            self.assertEqual(result, expected)
    
    def test_helpful_validation_errors(self):
        """Test that validation functions provide clear feedback."""
        # These tests ensure users understand what went wrong
        
        # Address too short
        short_address = "0x123"
        self.assertFalse(validate_ethereum_address(short_address))
        
        # Missing 0x prefix
        no_prefix = "1234567890123456789012345678901234567890"
        self.assertFalse(validate_ethereum_address(no_prefix))
        
        # Private key with spaces (common copy-paste error)
        key_with_spaces = "0x " + "1" * 64
        self.assertFalse(validate_private_key(key_with_spaces))


# Run tests if this file is executed directly
if __name__ == '__main__':
    unittest.main(verbosity=2)