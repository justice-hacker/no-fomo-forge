# Contributing to NFT Batch Minter

First off, thank you for considering contributing to NFT Batch Minter! It's people like you that make this tool better for everyone.

## Code of Conduct

By participating in this project, you are expected to uphold our Code of Conduct:

- Use welcoming and inclusive language
- Be respectful of differing viewpoints and experiences
- Gracefully accept constructive criticism
- Focus on what is best for the community
- Show empathy towards other community members

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check existing issues to avoid duplicates. When you create a bug report, include as many details as possible:

- **Use a clear and descriptive title**
- **Describe the exact steps to reproduce the problem**
- **Provide specific examples**
- **Describe the behavior you observed and expected**
- **Include logs and error messages**
- **Include your configuration (without sensitive data)**

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion:

- **Use a clear and descriptive title**
- **Provide a detailed description of the suggested enhancement**
- **Explain why this enhancement would be useful**
- **List any alternative solutions you've considered**
- **Include mockups or examples if applicable**

### Pull Requests

1. Fork the repository and create your branch from `main`
2. If you've added code that should be tested, add tests
3. Ensure the test suite passes (`make test`)
4. Make sure your code follows the style guidelines (`make lint`)
5. Issue the pull request

## Development Setup

1. **Fork and clone the repository**

   ```bash
   git clone https://github.com/justice-hacker/no-fomo-forge.git
   cd no-fomo-forge
   ```

2. **Set up development environment**

   ```bash
   make dev-setup
   ```

3. **Create a branch for your feature**

   ```bash
   git checkout -b feature/amazing-feature
   ```

4. **Make your changes and test**
   ```bash
   make test
   make lint
   make format
   ```

## Style Guidelines

### Python Style Guide

We follow PEP 8 with some modifications:

- Line length: 100 characters maximum
- Use type hints where appropriate
- Document all public functions with docstrings
- Use descriptive variable names

Example:

```python
def calculate_mint_cost(
    gas_limit: int,
    gas_price_wei: int,
    mint_price: int = 0
) -> Dict[str, Any]:
    """
    Calculate the total cost for minting NFTs.

    Args:
        gas_limit: Estimated gas limit for transaction
        gas_price_wei: Current gas price in wei
        mint_price: Price per NFT in wei (default: 0 for free mint)

    Returns:
        dict: Cost breakdown including gas and mint fees
    """
    # Implementation here
    pass
```

### Commit Messages

- Use the present tense ("Add feature" not "Added feature")
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit the first line to 72 characters or less
- Reference issues and pull requests liberally after the first line

Example:

```
Add support for Polygon network

- Add Polygon mainnet and Mumbai testnet configurations
- Update network validation to include new networks
- Add tests for Polygon-specific functionality

Fixes #123
```

### Documentation

- Update README.md if you change functionality
- Add docstrings to all new functions and classes
- Update configuration examples if adding new options
- Include examples in docstrings where helpful

## Testing

### Running Tests

```bash
# Run all tests
make test

# Run specific test file
python run_tests.py tests.test_config

# Run with coverage
make coverage

# Run specific test class
python -m unittest tests.test_minter.TestNFTMinter

# Run specific test method
python -m unittest tests.test_minter.TestNFTMinter.test_connect_success
```

### Writing Tests

- Write tests for all new functionality
- Aim for >80% code coverage
- Use mocks for external dependencies
- Test both success and failure cases
- Use descriptive test names

Example:

```python
def test_validate_ethereum_address_with_invalid_checksum(self):
    """Test that invalid checksum addresses are rejected."""
    invalid_address = "0x5aaeb6053f3e94c9b9a09f33669435e7ef1beaed"
    self.assertFalse(validate_ethereum_address(invalid_address))
```

## Project Structure

When adding new features, maintain the existing structure:

```
src/
├── __init__.py          # Package initialization
├── minter.py            # Core minting logic
├── config.py            # Configuration management
├── networks.py          # Network configurations
├── utils.py             # Utility functions
└── exceptions.py        # Custom exceptions

tests/
├── __init__.py          # Test package initialization
├── test_minter.py       # Minter tests
├── test_config.py       # Configuration tests
└── test_utils.py        # Utility tests
```

## Adding New Networks

To add support for a new network:

1. Add network configuration to `src/networks.py`:

   ```python
   "NETWORK_NAME": {
       "name": "Human Readable Name",
       "chain_id": 12345,
       "rpc": "https://rpc.example.com",
       "explorer": {
           "name": "ExplorerName",
           "base_url": "https://explorer.example.com",
           "api_url": "https://api.explorer.example.com"
       },
       "native_token": "TOKEN",
       "is_testnet": False
   }
   ```

2. Update validation in `src/config.py`
3. Add tests for the new network
4. Update documentation

## Security Considerations

- Never commit private keys or sensitive data
- Always validate user input
- Use secure random generation for any cryptographic operations
- Be careful with gas estimation to prevent overspending
- Review dependencies for known vulnerabilities

## Release Process

1. Update version in `src/__init__.py`
2. Update CHANGELOG.md
3. Create a pull request to `main`
4. After merge, create a release tag
5. GitHub Actions will handle the rest

## Questions?

Feel free to open an issue for any questions about contributing. We're here to help!

## Recognition

Contributors will be recognized in:

- The project README
- Release notes
- Special thanks in documentation

Thank you for helping make NFT Batch Minter better! 🚀
