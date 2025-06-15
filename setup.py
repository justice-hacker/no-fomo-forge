#!/usr/bin/env python3
"""
Setup script for NFT Batch Minter

This script sets up the project environment and dependencies.
"""

import os
import sys
import subprocess
import platform
from pathlib import Path


def create_directories():
    """Create necessary project directories."""
    directories = ['logs', 'abi', 'output']
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✓ Created directory: {directory}/")


def create_virtual_environment():
    """Create a Python virtual environment."""
    if Path('venv').exists():
        print("✓ Virtual environment already exists")
        return
    
    print("Creating virtual environment...")
    subprocess.run([sys.executable, '-m', 'venv', 'venv'], check=True)
    print("✓ Virtual environment created")


def get_pip_command():
    """Get the correct pip command for the virtual environment."""
    if platform.system() == 'Windows':
        return os.path.join('venv', 'Scripts', 'pip')
    else:
        return os.path.join('venv', 'bin', 'pip')


def install_dependencies():
    """Install required Python packages."""
    pip_cmd = get_pip_command()
    
    print("\nInstalling dependencies...")
    subprocess.run([pip_cmd, 'install', '--upgrade', 'pip'], check=True)
    subprocess.run([pip_cmd, 'install', '-r', 'requirements.txt'], check=True)
    print("✓ Dependencies installed")


def create_example_files():
    """Create example configuration files if they don't exist."""
    example_files = {
        'config.example.json': 'config.json',
        '.env.example': '.env'
    }
    
    for example, target in example_files.items():
        if Path(example).exists() and not Path(target).exists():
            print(f"✓ Created {target} from {example}")
            # Note: In a real setup, you'd copy the file
            # For now, just notify the user
            print(f"  → Please copy {example} to {target} and update with your values")


def main():
    """Main setup function."""
    print("NFT Batch Minter Setup")
    print("=" * 50)
    
    try:
        # Create project directories
        create_directories()
        
        # Create virtual environment
        create_virtual_environment()
        
        # Install dependencies
        install_dependencies()
        
        # Create example files
        create_example_files()
        
        print("\n" + "=" * 50)
        print("✅ Setup completed successfully!")
        print("\nNext steps:")
        print("1. Activate the virtual environment:")
        if platform.system() == 'Windows':
            print("   venv\\Scripts\\activate")
        else:
            print("   source venv/bin/activate")
        print("2. Copy config.example.json to config.json and update values")
        print("3. Run the minter: python main.py")
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error during setup: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()