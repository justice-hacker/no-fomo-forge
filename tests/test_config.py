"""
Configuration Manager Tests

This module contains tests for the configuration management functionality.
"""

import unittest
import json
import tempfile
import os
from pathlib import Path

# Add parent directory to path
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.config import ConfigManager
from src.exceptions import ConfigurationError


class TestConfigManager(unittest.TestCase):
    """Test cases for ConfigManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = Path(self.temp_dir) / "test_config.json"
        
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)
        
    def test_default_config(self):
        """Test loading default configuration."""
        config = ConfigManager(str(self.config_file))
        config.load()
        
        # Check default values
        self.assertEqual(config.get('network.name'), 'BERACHAIN')
        self.assertEqual(config.get('minting.amount'), 1)
        self.assertEqual(config.get('minting.group_id'), 0)
        
    def test_file_config_override(self):
        """Test that file configuration overrides defaults."""
        # Create test config file
        test_config = {
            "network": {
                "name": "ARBITRUM_ONE"
            },
            "minting": {
                "amount": 5
            }
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(test_config, f)
        
        config = ConfigManager(str(self.config_file))
        config.load()
        
        # Check overridden values
        self.assertEqual(config.get('network.name'), 'ARBITRUM_ONE')
        self.assertEqual(config.get('minting.amount'), 5)
        # Check default still works
        self.assertEqual(config.get('minting.group_id'), 0)
        
    def test_env_override(self):
        """Test that environment variables override file config."""
        # Set environment variable
        os.environ['NETWORK_NAME'] = 'ARBITRUM_NOVA'
        
        try:
            config = ConfigManager(str(self.config_file))
            config.load()
            
            self.assertEqual(config.get('network.name'), 'ARBITRUM_NOVA')
        finally:
            # Clean up
            del os.environ['NETWORK_NAME']
            
    def test_nested_key_access(self):
        """Test accessing nested configuration keys."""
        config = ConfigManager(str(self.config_file))
        config.load()
        
        # Test nested access
        self.assertIsNotNone(config.get('wallet.private_key'))
        self.assertIsNone(config.get('nonexistent.key'))
        self.assertEqual(config.get('nonexistent.key', 'default'), 'default')
        
    def test_validation_missing_private_key(self):
        """Test validation fails when private key is missing."""
        config = ConfigManager(str(self.config_file))
        config.load()
        
        # Remove private key
        config.set('wallet.private_key', '')
        
        with self.assertRaises(ConfigurationError) as cm:
            config.validate()
        
        self.assertIn('wallet.private_key is required', str(cm.exception))
        
    def test_validation_invalid_network(self):
        """Test validation fails with invalid network."""
        config = ConfigManager(str(self.config_file))
        config.load()
        
        # Set invalid network
        config.set('network.name', 'INVALID_NETWORK')
        config.set('wallet.private_key', '0x' + '1' * 64)
        config.set('contract.address', '0x' + '2' * 40)
        config.set('contract.abi_path', 'test.json')
        
        with self.assertRaises(ConfigurationError) as cm:
            config.validate()
        
        self.assertIn('Invalid network', str(cm.exception))
        
    def test_validation_invalid_amount(self):
        """Test validation fails with invalid mint amount."""
        config = ConfigManager(str(self.config_file))
        config.load()
        
        # Set required fields
        config.set('wallet.private_key', '0x' + '1' * 64)
        config.set('contract.address', '0x' + '2' * 40)
        config.set('contract.abi_path', 'test.json')
        
        # Set invalid amount
        config.set('minting.amount', -5)
        
        with self.assertRaises(ConfigurationError) as cm:
            config.validate()
        
        self.assertIn('minting.amount must be -1', str(cm.exception))
        
    def test_save_example(self):
        """Test saving example configuration."""
        config = ConfigManager(str(self.config_file))
        example_file = Path(self.temp_dir) / "example.json"
        
        config.save_example(str(example_file))
        
        self.assertTrue(example_file.exists())
        
        # Load and check example
        with open(example_file, 'r') as f:
            example_data = json.load(f)
        
        self.assertIn('wallet', example_data)
        self.assertIn('network', example_data)
        self.assertIn('contract', example_data)
        self.assertIn('minting', example_data)


if __name__ == '__main__':
    unittest.main()