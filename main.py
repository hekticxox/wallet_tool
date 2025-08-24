#!/usr/bin/env python3
"""
Wallet Recovery Tool - Production Entry Point
============================================
Production-ready cryptocurrency wallet recovery and balance scanner.

Commands:
    python main.py brain-scan <mode>         - Brain wallet scanning (fast/massive/research/realistic)
    python main.py balance-check <file>      - Check balances for keys/addresses from file
    python main.py extract <dataset_path>    - Extract crypto keys from dataset
    python main.py config                    - Show configuration summary
    python main.py setup                     - Setup production environment
    python main.py status                    - Show system status

Examples:
    python main.py brain-scan fast           - Fast brain wallet scan
    python main.py balance-check keys.txt    - Check balances for keys in file
    python main.py config --summary          - Show configuration
"""

import sys
import os
import argparse
import logging
from pathlib import Path

# Add src directories to Python path
project_root = Path(__file__).parent
src_path = project_root / 'src'
sys.path.insert(0, str(src_path))
sys.path.insert(0, str(src_path / 'core'))
sys.path.insert(0, str(src_path / 'scanners'))
sys.path.insert(0, str(src_path / 'extractors'))
sys.path.insert(0, str(src_path / 'utils'))
sys.path.insert(0, str(src_path / 'reports'))

# Import modules
from core.config import get_config
from scanners.brain_wallet_scanner import BrainWalletScanner
from scanners.balance_checker import BalanceChecker

def setup_environment():
    """Setup production environment and dependencies."""
    print("🚀 Setting up production environment...")
    
    config = get_config()
    
    # Check dependencies
    try:
        import bitcoin
        print("✅ Bitcoin library available")
    except ImportError:
        print("❌ Bitcoin library missing. Install with: pip install bitcoin")
        return False
    
    try:
        import requests
        print("✅ Requests library available")
    except ImportError:
        print("❌ Requests library missing. Install with: pip install requests")
        return False
    
    # Create directories
    for directory in [config.data_dir, config.results_dir, config.logs_dir, config.backup_dir]:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"📁 Directory ready: {directory}")
    
    print("✅ Environment setup complete!")
    return True

def brain_scan_command(args):
    """Execute brain wallet scanning."""
    if not args.mode:
        print("Error: Brain scan mode required (fast/massive/research/realistic)")
        return
    
    if args.mode not in ['fast', 'massive', 'research', 'realistic']:
        print(f"Error: Invalid mode '{args.mode}'. Use: fast, massive, research, or realistic")
        return
    
    print(f"🧠 Starting {args.mode} brain wallet scan...")
    
    config = get_config()
    scanner = BrainWalletScanner(
        api_timeout=config.scanner.api_timeout,
        num_threads=config.scanner.max_threads
    )
    
    results = scanner.scan(args.mode)
    
    if results['found_wallets']:
        print(f"\n🎉 SUCCESS: Found {len(results['found_wallets'])} funded wallets!")
        for wallet in results['found_wallets']:
            print(f"  💰 {wallet['address']}: {wallet['balance_btc']:.8f} BTC")
    else:
        print("\n📊 Scan complete - no funded wallets found in this batch")

def balance_check_command(args):
    """Execute balance checking for file of keys/addresses."""
    if not args.file:
        print("Error: File path required")
        return
    
    if not os.path.exists(args.file):
        print(f"Error: File not found: {args.file}")
        return
    
    print(f"🔍 Checking balances for keys/addresses in {args.file}...")
    
    config = get_config()
    checker = BalanceChecker()
    
    # Read file
    with open(args.file, 'r') as f:
        lines = [line.strip() for line in f if line.strip()]
    
    print(f"📋 Loaded {len(lines):,} entries from file")
    
    # Determine if these are private keys or addresses
    first_line = lines[0] if lines else ""
    
    if len(first_line) == 64 and all(c in '0123456789abcdefABCDEF' for c in first_line):
        # Looks like private keys
        print("🔑 Detected private keys format")
        found_wallets = checker.check_multiple_keys(lines)
    elif len(first_line) >= 26 and first_line.startswith(('1', '3', 'bc1')):
        # Looks like Bitcoin addresses
        print("📬 Detected Bitcoin addresses format")
        found_wallets = checker.batch_check_addresses(lines)
    else:
        print("❓ Auto-detecting format...")
        # Try as private keys first
        found_wallets = checker.check_multiple_keys(lines[:10])  # Test first 10
        if not found_wallets:
            # Try as addresses
            found_wallets = checker.batch_check_addresses(lines[:10])
    
    if found_wallets:
        print(f"\n🎉 Found {len(found_wallets)} funded wallets:")
        total_balance = sum(w.balance_btc for w in found_wallets)
        for wallet in found_wallets:
            print(f"  💰 {wallet.address}: {wallet.balance_btc:.8f} BTC")
        print(f"\n💎 Total Balance: {total_balance:.8f} BTC")
        
        # Save results
        filename = checker.save_results(found_wallets)
        print(f"💾 Results saved to: {filename}")
    else:
        print("\n📊 No funded wallets found")
    
    # Show statistics
    stats = checker.get_stats()
    print(f"\n📈 Statistics:")
    print(f"  Checked: {stats['total_checked']:,}")
    print(f"  Success Rate: {stats['success_rate']:.1%}")

def config_command(args):
    """Show configuration information."""
    config = get_config()
    
    if args.summary:
        config.print_summary()
    elif args.validate:
        print("🔐 Validating API keys...")
        results = config.validate_api_keys()
        for api_name, valid in results.items():
            status = "✅ Valid" if valid else "❌ Invalid/Missing"
            print(f"  {api_name}: {status}")
    else:
        config.print_summary()

def status_command(args):
    """Show system status."""
    print("🔋 Wallet Recovery Tool - System Status")
    print("=" * 50)
    
    # Check Python version
    print(f"🐍 Python Version: {sys.version.split()[0]}")
    
    # Check dependencies
    dependencies = ['bitcoin', 'requests', 'pathlib']
    for dep in dependencies:
        try:
            __import__(dep)
            print(f"✅ {dep}: Available")
        except ImportError:
            print(f"❌ {dep}: Missing")
    
    # Check configuration
    try:
        config = get_config()
        print(f"⚙️  Configuration: Loaded")
        print(f"📁 Data Directory: {config.data_dir}")
        print(f"📊 Results Directory: {config.results_dir}")
        
        # Check API availability
        enabled_apis = config.get_enabled_btc_apis()
        print(f"📡 Enabled APIs: {len(enabled_apis)} Bitcoin APIs")
        
    except Exception as e:
        print(f"❌ Configuration Error: {e}")
    
    print("\n✅ System status check complete")

def main():
    """Main entry point with command parsing."""
    parser = argparse.ArgumentParser(
        description="Production Wallet Recovery Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py brain-scan fast           # Quick brain wallet scan
  python main.py brain-scan massive        # Comprehensive scan
  python main.py balance-check keys.txt    # Check balances from file
  python main.py config --summary          # Show configuration
  python main.py setup                     # Setup environment
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Brain scan command
    brain_parser = subparsers.add_parser('brain-scan', help='Brain wallet scanning')
    brain_parser.add_argument('mode', nargs='?', choices=['fast', 'massive', 'research', 'realistic'],
                             help='Scanning mode')
    brain_parser.add_argument('--threads', type=int, help='Number of threads')
    brain_parser.add_argument('--timeout', type=int, help='API timeout seconds')
    
    # Balance check command
    balance_parser = subparsers.add_parser('balance-check', help='Check balances for keys/addresses')
    balance_parser.add_argument('file', nargs='?', help='File containing keys or addresses')
    balance_parser.add_argument('--output', help='Output filename')
    
    # Config command
    config_parser = subparsers.add_parser('config', help='Configuration management')
    config_parser.add_argument('--summary', action='store_true', help='Show config summary')
    config_parser.add_argument('--validate', action='store_true', help='Validate API keys')
    
    # Setup command
    setup_parser = subparsers.add_parser('setup', help='Setup production environment')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Show system status')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == 'brain-scan':
            brain_scan_command(args)
        elif args.command == 'balance-check':
            balance_check_command(args)
        elif args.command == 'config':
            config_command(args)
        elif args.command == 'setup':
            if setup_environment():
                print("\n🎯 Ready for production use!")
        elif args.command == 'status':
            status_command(args)
        else:
            print(f"Unknown command: {args.command}")
            parser.print_help()
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        if os.getenv('DEBUG', '').lower() == 'true':
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()
