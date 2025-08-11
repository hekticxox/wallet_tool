#!/usr/bin/env python3
"""
Interactive Directory Wallet Scanner
Allows you to specify any directory to scan for wallet files
"""

import os
import sys
from pathlib import Path
from enhanced_wallet_scanner import MultiFormatWalletScanner

def get_directory_input():
    """Get directory path from user input"""
    print("🔍 INTERACTIVE WALLET DIRECTORY SCANNER")
    print("="*50)
    print()
    
    # Show some common directories as options
    home_dir = Path.home()
    common_dirs = [
        home_dir / "Downloads",
        home_dir / "Desktop", 
        home_dir / "Documents",
        Path("/tmp"),
        Path("/home/admin"),
        Path.cwd()
    ]
    
    print("📁 Common directories:")
    for i, dir_path in enumerate(common_dirs, 1):
        exists_marker = "✅" if dir_path.exists() else "❌"
        print(f"   {i}. {exists_marker} {dir_path}")
    
    print(f"   {len(common_dirs) + 1}. Custom path")
    print()
    
    while True:
        try:
            choice = input("Select directory (number) or press Enter for Downloads: ").strip()
            
            # Default to Downloads if empty
            if not choice:
                target_dir = home_dir / "Downloads"
                break
            
            # Handle numeric choice
            if choice.isdigit():
                choice_num = int(choice)
                if 1 <= choice_num <= len(common_dirs):
                    target_dir = common_dirs[choice_num - 1]
                    break
                elif choice_num == len(common_dirs) + 1:
                    # Custom path
                    custom_path = input("Enter custom directory path: ").strip()
                    target_dir = Path(custom_path)
                    break
                else:
                    print(f"❌ Invalid choice. Please select 1-{len(common_dirs) + 1}")
                    continue
            else:
                # Treat as direct path
                target_dir = Path(choice)
                break
        
        except KeyboardInterrupt:
            print("\n\n👋 Cancelled by user")
            sys.exit(0)
        except Exception as e:
            print(f"❌ Error: {e}")
            continue
    
    return target_dir

def confirm_scan(directory_path):
    """Confirm scan with user"""
    print(f"\n🎯 Target directory: {directory_path}")
    
    if not directory_path.exists():
        print(f"❌ Directory does not exist: {directory_path}")
        return False
    
    if not directory_path.is_dir():
        print(f"❌ Path is not a directory: {directory_path}")
        return False
    
    # Count files roughly
    try:
        file_count = len(list(directory_path.rglob("*")))
        print(f"📊 Estimated files to scan: {file_count:,}")
        
        if file_count > 10000:
            print(f"⚠️  Large directory detected! Scan will be limited to first 10,000 files.")
    
    except Exception as e:
        print(f"⚠️  Could not estimate file count: {e}")
    
    print()
    confirm = input("🚀 Start scan? (y/N): ").strip().lower()
    return confirm in ['y', 'yes', '1']

def main():
    """Main interactive function"""
    try:
        # Get directory from user
        target_directory = get_directory_input()
        
        # Confirm scan
        if not confirm_scan(target_directory):
            print("👋 Scan cancelled")
            return
        
        # Initialize scanner
        print("\n" + "="*70)
        scanner = MultiFormatWalletScanner()
        
        # Run scan
        results = scanner.scan_directory(str(target_directory))
        
        print(f"\n✅ Scan completed successfully!")
        print(f"📄 Results saved to: enhanced_wallet_extraction_results.json")
        
        # Show quick summary
        stats = results.get('statistics', {})
        extracted_count = stats.get('total_extracted_items', 0)
        
        if extracted_count > 0:
            print(f"\n🎉 Found {extracted_count} wallet-related items!")
            
            # Show breakdown by type
            items_by_type = stats.get('items_by_type', {})
            if items_by_type:
                print("\n📊 Breakdown by type:")
                for item_type, count in items_by_type.items():
                    print(f"   {item_type.upper()}: {count}")
            
            # Show breakdown by chain
            items_by_chain = stats.get('items_by_chain', {})
            if items_by_chain:
                print("\n⛓️  Breakdown by blockchain:")
                for chain, count in items_by_chain.items():
                    print(f"   {chain.upper()}: {count}")
        else:
            print(f"\n💡 No wallet data found in {target_directory}")
            print("   This could mean:")
            print("   - No wallet files in this directory")
            print("   - Files are encrypted or in unsupported formats")
            print("   - Permission issues accessing some files")
    
    except KeyboardInterrupt:
        print("\n\n👋 Scan cancelled by user")
    except Exception as e:
        print(f"\n❌ Error during scan: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
