# NFT Batch Minter

A professional Python-based automated NFT minting tool that provides enterprise-grade batch minting capabilities with real-time monitoring, multi-chain support, and advanced error recovery mechanisms.

## Overview

The NFT Batch Minter is designed to streamline the process of minting NFTs on various blockchain networks. Whether you're launching a new collection, participating in a mint, or managing large-scale NFT operations, this tool provides the automation and reliability you need.

Think of this tool as your automated assistant that handles all the complex blockchain interactions, monitors gas prices, waits for optimal minting conditions, and executes transactions with built-in safety mechanisms. It's like having a dedicated team member who never sleeps and always follows best practices for blockchain interactions.

## Key Features

### Core Functionality

The heart of this tool lies in its ability to interact with smart contracts across multiple blockchain networks. It automatically detects contract interfaces, adapts to different minting functions, and handles the entire transaction lifecycle from gas estimation to confirmation.

- **Intelligent Contract Detection**: The minter automatically identifies available minting functions (batchMint, mint, publicMint, etc.) and adapts its approach accordingly
- **Multi-Network Support**: Seamlessly switch between Arbitrum One, Arbitrum Nova, Arbitrum Sepolia, and Berachain networks
- **Batch Operations**: Mint multiple NFTs in a single transaction or split large quantities into manageable batches
- **Live Monitoring**: Continuously monitor contract state and automatically begin minting when conditions are met

### Advanced Features

Beyond basic minting, the tool provides sophisticated features for professional users who need more control and reliability.

- **Retry Mechanisms**: Automatically retry failed transactions with intelligent backoff strategies
- **Cost Estimation**: Calculate total costs including gas fees before executing transactions
- **Scheduled Minting**: Set up mints to execute at specific times or intervals
- **Multi-Wallet Support**: Manage minting operations across multiple wallets
- **Dry Run Mode**: Test your configuration without executing actual transactions

### Security & Configuration

Security is paramount when dealing with blockchain transactions. The tool provides multiple layers of protection for your sensitive data.

- **Environment Variable Support**: Keep private keys secure using environment variables
- **Configuration Validation**: Comprehensive checks before any transaction execution
- **Sanitized Logging**: Sensitive data is automatically redacted from log files
- **Transaction Simulation**: Preview transactions before committing to the blockchain

## Prerequisites

Before you begin, ensure you have the following:

- **Python 3.8 or higher**: The tool is built with modern Python features
- **pip**: Python's package installer (usually comes with Python)
- **A funded wallet**: You'll need ETH or the native token for gas fees
- **Contract details**: The address and ABI of the NFT contract you want to interact with

## Installation

Let's walk through the installation process step by step. The tool provides multiple installation methods to suit different preferences and environments.

### Method 1: Using the Setup Script (Recommended)

The easiest way to get started is using our automated setup script:

```bash
# Clone the repository
git clone https://github.com/justice-hacker/no-fomo-forge.git
cd no-fomo-forge

# Run the setup script
python setup.py
```

The setup script will:

1. Create a Python virtual environment to isolate dependencies
2. Install all required packages
3. Create necessary directories (logs, abi, output)
4. Generate example configuration files

### Method 2: Manual Installation

If you prefer more control over the installation process:

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create necessary directories
mkdir -p logs abi output
```

### Method 3: Using Make (Unix-like systems)

If you have `make` installed:

```bash
make setup  # Complete setup
make install  # Just install dependencies
```

### Method 4: Docker Installation

For containerized deployment:

```bash
# Build the Docker image
docker build -t nft-minter .

# Or use docker-compose
docker-compose up -d
```

## Configuration

Configuration is the foundation of successful minting operations. The tool supports multiple configuration methods, allowing you to choose the approach that best fits your security requirements and workflow.

### Configuration Methods

#### 1. JSON Configuration File

The primary configuration method uses a JSON file. Copy the example and customize it:

```bash
cp config.example.json config.json
```

Edit `config.json` with your settings:

```json
{
  "wallet": {
    "private_key": "YOUR_PRIVATE_KEY_HERE",
    "address": "YOUR_WALLET_ADDRESS_HERE"
  },
  "network": {
    "name": "BERACHAIN",
    "custom_rpc": null
  },
  "contract": {
    "address": "CONTRACT_ADDRESS_HERE",
    "abi_path": "abi/contract_abi.json",
    "explorer_api_key": "YOUR_API_KEY_HERE"
  },
  "minting": {
    "group_id": 0,
    "amount": 1,
    "to_address": "DEFAULT",
    "auto_max": false
  }
}
```

#### 2. Environment Variables (Recommended for Production)

For enhanced security, especially in production environments, use environment variables:

```bash
export WALLET_PRIVATE_KEY="your_private_key"
export WALLET_ADDRESS="your_wallet_address"
export NETWORK_NAME="BERACHAIN"
export CONTRACT_ADDRESS="contract_address"
export EXPLORER_API_KEY="your_api_key"
export MINTING_AMOUNT="1"
export MINTING_GROUP_ID="0"
```

Environment variables take precedence over JSON configuration, allowing you to override specific values without modifying files.

### Configuration Options Explained

Let me explain each configuration option to help you understand their purpose:

**Wallet Configuration**:

- `private_key`: Your wallet's private key (keep this extremely secure!)
- `address`: Your wallet's public address (must match the private key)

**Network Configuration**:

- `name`: The blockchain network to use (ARBITRUM_ONE, ARBITRUM_NOVA, ARBITRUM_SEPOLIA, or BERACHAIN)
- `custom_rpc`: Optional custom RPC endpoint (useful for private nodes or specific providers)

**Contract Configuration**:

- `address`: The NFT contract address you want to mint from
- `abi_path`: Path to the contract's ABI JSON file (describes the contract interface)
- `explorer_api_key`: API key for automatically fetching ABI from block explorers

**Minting Configuration**:

- `group_id`: The token group or collection ID (often 0 for single collections)
- `amount`: Number of NFTs to mint (-1 automatically uses maximum allowed)
- `to_address`: Recipient address (DEFAULT uses your wallet, or specify another address)
- `auto_max`: Automatically mint the maximum allowed amount when true

## Usage Guide

### Basic Usage

The simplest way to run the minter:

```bash
python main.py
```

This will:

1. Load your configuration
2. Connect to the blockchain network
3. Load the smart contract
4. Wait for minting to be enabled (if necessary)
5. Execute the mint transaction
6. Report the results

### Command Line Options

The tool provides various command-line options for flexibility:

```bash
python main.py [options]

Options:
  -c, --config PATH      Configuration file path (default: config.json)
  -n, --network NAME     Override network from config
  -a, --amount NUM       Override mint amount
  -g, --group ID         Override group ID
  --to-address ADDR      Override recipient address
  --dry-run             Simulate without executing
  -v, --verbose         Enable detailed logging
  -h, --help           Show help message
```

### Common Usage Scenarios

#### 1. Testing Your Configuration

Always test your configuration before real minting:

```bash
python main.py --dry-run -v
```

This simulates the entire process without sending transactions, showing you exactly what would happen.

#### 2. Minting a Specific Amount

Override the configured amount for a one-time mint:

```bash
python main.py -a 5
```

#### 3. Using a Different Network

Switch networks without modifying your config file:

```bash
python main.py -n ARBITRUM_ONE
```

#### 4. Minting to a Different Address

Send NFTs to another wallet:

```bash
python main.py --to-address 0x742d35Cc6634C0532925a3b844Bc9e7595f0F0fa
```

### Advanced Usage Examples

For more complex scenarios, use the provided example scripts:

```bash
# Run basic examples
python examples/basic_usage.py

# Run advanced examples (batch minting, scheduling, etc.)
python examples/advanced_usage.py
```

## Project Structure

Understanding the project structure helps you navigate the codebase and make modifications:

```
no-fomo-forge/
├── .github/
│   └── workflows/
│       └── ci.yml         # Actions workflow for CI/CD
├── src/                    # Source code modules
│   ├── __init__.py        # Package initialization
│   ├── minter.py          # Core minting logic
│   ├── config.py          # Configuration management
│   ├── networks.py        # Network definitions
│   ├── utils.py           # Utility functions
│   └── exceptions.py      # Custom exceptions
├── tests/                  # Test suite
│   ├── __init__.py
│   ├── test_minter.py     # Minter tests
│   ├── test_config.py     # Configuration tests
│   └── test_utils.py      # Utility tests
├── examples/               # Usage examples
│   ├── basic_usage.py     # Basic examples
│   └── advanced_usage.py  # Advanced patterns
├── logs/                   # Log files (auto-created)
├── abi/                    # Contract ABI files
├── main.py                # Entry point
├── setup.py               # Setup script
├── run_tests.py           # Test runner
├── requirements.txt       # Python dependencies
├── Makefile              # Development tasks
├── Dockerfile            # Container definition
├── docker-compose.yml    # Container orchestration
├── config.example.json   # Example configuration
├── .env.example         # Example environment variables
├── .gitignore           # Git ignore rules
├── LICENSE              # AGPL-3.0 license
└── CONTRIBUTING.md      # Contribution guidelines
```

## Development

### Running Tests

Testing is crucial for maintaining code quality. Run the test suite:

```bash
# Run all tests
make test
# or
python run_tests.py

# Run specific test module
python run_tests.py tests.test_minter

# Run with coverage report
make coverage
```

### Code Quality

Maintain code quality with built-in tools:

```bash
# Format code with black
make format

# Run linting checks
make lint

# Type checking (if mypy installed)
make typecheck
```

### Development Workflow

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Make your changes
3. Run tests: `make test`
4. Format code: `make format`
5. Commit with clear messages
6. Submit a pull request

## Docker Deployment

For production deployments, Docker provides isolation and consistency:

### Basic Docker Usage

```bash
# Build image
docker build -t nft-minter .

# Run container
docker run -v $(pwd)/config:/app/config nft-minter
```

### Docker Compose

For more complex deployments:

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Environment Configuration

Create a `.env` file for Docker:

```env
WALLET_PRIVATE_KEY=your_key_here
WALLET_ADDRESS=your_address_here
NETWORK_NAME=BERACHAIN
CONTRACT_ADDRESS=contract_here
```

## Troubleshooting

### Common Issues and Solutions

#### "Failed to connect to network"

This typically indicates RPC endpoint issues:

- Check your internet connection
- Verify the RPC endpoint is accessible
- Try alternative RPC endpoints listed in `src/networks.py`
- Consider using a private RPC provider for better reliability

#### "Insufficient funds for gas"

Your wallet needs native tokens for gas fees:

- Check your wallet balance
- Ensure you have enough ETH/BERA for gas
- Consider current network congestion
- Use cost estimation to plan ahead

#### "Transaction failed"

Transaction failures can have various causes:

- Verify minting is actually enabled on the contract
- Check if you've exceeded mint limits
- Ensure the contract address is correct
- Review the revert reason in logs
- Try with a smaller amount first

#### "Invalid private key"

Private key format issues:

- Ensure your key starts with '0x'
- Verify it's exactly 64 characters (after 0x)
- Check for extra spaces or hidden characters
- Never share your private key in support requests!

### Debug Mode

Enable detailed logging for troubleshooting:

```bash
python main.py -v
```

Check the `logs/` directory for detailed information about errors.

## Security Best Practices

Security is paramount when dealing with blockchain transactions. Follow these guidelines:

1. **Private Key Management**:

   - Never commit private keys to version control
   - Use environment variables in production
   - Consider using hardware wallets for large operations
   - Rotate keys regularly

2. **Configuration Security**:

   - Keep `config.json` in `.gitignore`
   - Use read-only permissions on configuration files
   - Audit configuration before each use

3. **Network Security**:

   - Use HTTPS RPC endpoints only
   - Consider running your own node for sensitive operations
   - Monitor for suspicious activity

4. **Testing**:
   - Always test on testnets first
   - Use dry-run mode before real transactions
   - Start with small amounts

## Performance Optimization

For large-scale minting operations:

1. **Batch Processing**: Use batch minting to reduce transaction costs
2. **Gas Optimization**: Monitor gas prices and mint during low-congestion periods
3. **RPC Selection**: Use high-performance RPC providers
4. **Parallel Operations**: Run multiple instances with different wallets

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the AGPL-3.0 license - see [LICENSE](LICENSE) for details.

## Support

- **Documentation**: This README and code comments
- **Issues**: GitHub Issues for bug reports and feature requests
- **Examples**: Check the `examples/` directory
- **Tests**: Review test files for usage patterns

## Disclaimer

This software is provided as-is. Always understand the smart contracts you're interacting with and the associated risks. The authors are not responsible for any losses incurred through the use of this software. Never share your private keys and always test thoroughly before mainnet usage.

---

Built with ❤️ for the NFT community. Happy minting!
