#!/usr/bin/env python3
"""
Test Runner Script

This script runs all tests for the NFT Batch Minter application.
It discovers and executes all test files in the tests directory.
"""

import sys
import unittest
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def run_tests(verbosity=2, pattern='test*.py'):
    """
    Run all tests in the tests directory.
    
    Args:
        verbosity: Test output verbosity (0-2)
        pattern: File pattern for test discovery
        
    Returns:
        bool: True if all tests passed, False otherwise
    """
    # Discover tests
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover(
        start_dir='tests',
        pattern=pattern,
        top_level_dir=str(project_root)
    )
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(test_suite)
    
    # Return success status
    return result.wasSuccessful()


def run_specific_test(test_path):
    """
    Run a specific test module or test case.
    
    Args:
        test_path: Path to test module (e.g., 'tests.test_config')
        
    Returns:
        bool: True if tests passed, False otherwise
    """
    try:
        # Load the specific test
        test_loader = unittest.TestLoader()
        test_suite = test_loader.loadTestsFromName(test_path)
        
        # Run tests
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(test_suite)
        
        return result.wasSuccessful()
    except Exception as e:
        print(f"Error loading test: {e}")
        return False


def main():
    """Main test runner entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Run tests for NFT Batch Minter'
    )
    
    parser.add_argument(
        'test',
        nargs='?',
        help='Specific test to run (e.g., tests.test_config)'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Increase test output verbosity'
    )
    
    parser.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='Decrease test output verbosity'
    )
    
    parser.add_argument(
        '-p', '--pattern',
        default='test*.py',
        help='File pattern for test discovery (default: test*.py)'
    )
    
    args = parser.parse_args()
    
    # Determine verbosity
    if args.quiet:
        verbosity = 0
    elif args.verbose:
        verbosity = 2
    else:
        verbosity = 1
    
    # Print header
    print("=" * 70)
    print("NFT Batch Minter - Test Suite")
    print("=" * 70)
    print()
    
    # Run tests
    if args.test:
        # Run specific test
        print(f"Running specific test: {args.test}")
        print()
        success = run_specific_test(args.test)
    else:
        # Run all tests
        print("Running all tests...")
        print()
        success = run_tests(verbosity=verbosity, pattern=args.pattern)
    
    # Print summary
    print()
    print("=" * 70)
    if success:
        print("✅ All tests passed!")
        sys.exit(0)
    else:
        print("❌ Some tests failed!")
        sys.exit(1)


if __name__ == '__main__':
    main()