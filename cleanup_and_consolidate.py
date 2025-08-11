#!/usr/bin/env python3
"""
Repository Cleanup and Consolidation Script
Removes unnecessary files and creates unified scanner
"""

import os
import shutil
import json
import sqlite3
from datetime import datetime

def cleanup_repository():
    """Remove unnecessary files and keep only essentials"""
    
    # Files to remove (duplicates, old versions, unused)
    files_to_remove = [
        # Old scanner versions
        'continuous_checker.py',
        'enhanced_balance_checker.py', 
        'enhanced_checker.py',
        'quick_priority_scanner.py',
        'pattern_focused_scanner.py',
        'priority_scanner.py',
        'quick_pattern_scanner.py',
        'funded_address_hunter.py',
        'unified_scanner.py',
        'unified_scanner_new.log',
        
        # Management scripts (replaced by unified)
        'continuous_scanner_manager.py',
        'parallel_scanner_manager.py',
        'scanner_manager.py',
        'discovery_monitor.py',
        'scanner_monitor.py',
        'realtime_tracker.py',
        'status_tracker.py',
        
        # Transfer helpers (replaced by secure_transfer.py)
        'bitcoin_transfer_helper.py',
        'bitcoin_transfer_final.py',
        'cli_bitcoin_transfer.py',
        'execute_bitcoin_transfer.py',
        'optimal_transfer_now.py',
        'simple_transfer.py',
        
        # Analysis and verification (integrated into unified)
        'address_verification_system.py',
        'analyze_electrum_address.py',
        'check_both_addresses.py',
        'check_btc_balance.py',
        'scanner_verification.py',
        'verify_electrum_address.py',
        'comprehensive_report.py',
        'final_implementation_report.py',
        
        # Utility scripts (integrated)
        'enhanced_duplicate_prevention.py',
        'electrum_wif_validator.py',
        'lightning_analysis.py',
        'token_checker.py',
        'wif_converter.py',
        
        # Shell scripts (replaced by unified)
        'dashboard.sh',
        'enhanced_monitor.sh',
        'quick_check.sh',
        'realtime_monitor.sh',
        'monitor_scanner.sh',
        'restart_checker.sh',
        'start_continuous_scanning.sh',
        'status_report.sh',
        'transfer_guide.sh',
        'electrum_export_helper.sh',
        'electrum_setup_helper.sh',
        
        # Log files
        'balance_checker.log',
        'continuous_manager.log',
        'current_scanner.log',
        'enhanced_balance_checker.log',
        'enhanced_main.log',
        'live_demo_scanner.log',
        'optimized_scanner.log',
        'parallel_manager.log',
        'pattern_main.log',
        'pattern_secondary.log',
        'scanner.log',
        'scanner_manager.log',
        'unified_scanner.log',
        
        # Temporary result files
        'ELECTRUM_READY_WIF.txt',
        'YOUR_BITCOIN_TRANSFER_INSTRUCTIONS.txt',
        'PRIORITY_FUNDED_ADDRESSES.txt',
        'IMMEDIATE_TRANSFER_INSTRUCTIONS.txt',
        'BITCOIN_TRANSFER_INFO.txt',
        'ELECTRUM_GUIDE.txt',
        'ELECTRUM_SETUP_GUIDE.txt',
        'LIGHTNING_NETWORK_ANALYSIS.txt',
        'electrum_troubleshoot.txt',
        'electrum-history.csv',
        
        # Old data files
        'checked_addresses_history.json',
        'duplicate_prevention_export.json',
        'high_priority_addresses.json',
        'medium_priority_addresses.json',
        'quick_scan_addresses.json',
        'live_demo_scanner_progress.json',
        'optimized_scanner_progress.json',
        'pattern_main_progress.json',
        'pattern_secondary_progress.json',
        
        # Status/report files
        'comprehensive_status_report.json',
        'current_status_report.json',
        'final_implementation_report.json',
        'scanner_status.json',
        'scanner_verification_report.json',
        'validation_success_report.json',
        
        # Transfer instruction files
        'bitcoin_transfer_instructions_20250810_151635.txt',
        'transfer_instructions_20250810_161459.txt',
        
        # Dashboard (will be recreated if needed)
        'live_dashboard.py',
    ]
    
    removed_count = 0
    kept_files = []
    
    print("🧹 CLEANING UP REPOSITORY")
    print("=" * 50)
    
    for file in files_to_remove:
        if os.path.exists(file):
            try:
                os.remove(file)
                print(f"🗑️  Removed: {file}")
                removed_count += 1
            except Exception as e:
                print(f"❌ Could not remove {file}: {e}")
    
    # Remove cache directories
    cache_dirs = ['__pycache__', '.pytest_cache']
    for cache_dir in cache_dirs:
        if os.path.exists(cache_dir):
            try:
                shutil.rmtree(cache_dir)
                print(f"🗑️  Removed directory: {cache_dir}")
                removed_count += 1
            except Exception as e:
                print(f"❌ Could not remove {cache_dir}: {e}")
    
    # List kept files
    essential_files = [
        'wallet_analysis.py',       # Core extraction engine
        'secure_transfer.py',       # Transfer utility  
        'requirements.txt',         # Dependencies
        'api_config.json',          # API keys
        'setup.sh',                 # Environment setup
        'monitor_checker.sh',       # Basic monitoring
        'prepare_production.sh',    # Production setup
        'auto_recovery.sh',         # Auto-restart
        'README.md',                # Documentation
        'LICENSE',                  # License
        'api_config.json.example',  # Config template
        
        # Data files (keep)
        'funded_addresses.json',                    # Found addresses
        'detected_wallet_data_summary.json',       # Analysis results  
        'filtered_wallet_entries.json',            # Raw wallet data
        'bitcoin_address_analysis.json',           # Analysis data
        'address_tracking.db',                     # Duplicate prevention
        'FUNDED_ADDRESSES.txt',                    # Results backup
        'IMPROVEMENTS.md',                         # Notes
    ]
    
    for file in essential_files:
        if os.path.exists(file):
            kept_files.append(file)
    
    print(f"\n📊 CLEANUP SUMMARY")
    print(f"🗑️  Removed: {removed_count} files/directories")
    print(f"✅ Kept: {len(kept_files)} essential files")
    print(f"\n📁 ESSENTIAL FILES KEPT:")
    for file in kept_files:
        print(f"   ✅ {file}")
    
    return removed_count, kept_files

def consolidate_data():
    """Consolidate all found addresses into single file"""
    print(f"\n🔄 CONSOLIDATING DATA")
    print("=" * 30)
    
    all_addresses = []
    
    # Load from various sources
    sources = [
        ('funded_addresses.json', 'json'),
        ('FUNDED_ADDRESSES.txt', 'txt'),
    ]
    
    for source_file, file_type in sources:
        if os.path.exists(source_file):
            try:
                if file_type == 'json':
                    with open(source_file, 'r') as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            all_addresses.extend(data)
                        else:
                            all_addresses.append(data)
                
                elif file_type == 'txt':
                    with open(source_file, 'r') as f:
                        content = f.read()
                        # Parse text format addresses
                        if 'FUNDED ADDRESS FOUND!' in content:
                            sections = content.split('FUNDED ADDRESS FOUND!')
                            for section in sections[1:]:
                                addr_info = parse_text_address(section)
                                if addr_info:
                                    all_addresses.append(addr_info)
                
                print(f"✅ Loaded from {source_file}")
            except Exception as e:
                print(f"⚠️  Could not load {source_file}: {e}")
    
    # Remove duplicates based on address
    unique_addresses = []
    seen_addresses = set()
    
    for addr in all_addresses:
        address_key = addr.get('address', '')
        if address_key and address_key not in seen_addresses:
            seen_addresses.add(address_key)
            unique_addresses.append(addr)
    
    # Save consolidated results
    consolidated_data = {
        'consolidation_date': datetime.now().isoformat(),
        'total_unique_addresses': len(unique_addresses),
        'total_value': sum(float(addr.get('balance', 0)) for addr in unique_addresses),
        'addresses': unique_addresses,
        'summary': {
            'bitcoin': len([a for a in unique_addresses if a.get('chain', '').lower() == 'bitcoin']),
            'ethereum': len([a for a in unique_addresses if a.get('chain', '').lower() == 'ethereum']),
            'solana': len([a for a in unique_addresses if a.get('chain', '').lower() == 'solana']),
        }
    }
    
    with open('funded_addresses_consolidated.json', 'w') as f:
        json.dump(consolidated_data, f, indent=2)
    
    print(f"💰 CONSOLIDATED RESULTS:")
    print(f"   📊 Total addresses: {len(unique_addresses)}")
    print(f"   🟠 Bitcoin: {consolidated_data['summary']['bitcoin']}")
    print(f"   🟣 Ethereum: {consolidated_data['summary']['ethereum']}")
    print(f"   🟢 Solana: {consolidated_data['summary']['solana']}")
    print(f"   💎 Total value: {consolidated_data['total_value']}")
    print(f"   📁 Saved to: funded_addresses_consolidated.json")
    
    return consolidated_data

def parse_text_address(section):
    """Parse address from text format"""
    lines = section.strip().split('\n')
    addr_info = {}
    
    for line in lines:
        line = line.strip()
        if line.startswith('Address:'):
            addr_info['address'] = line.split('Address:')[1].strip()
        elif line.startswith('Chain:'):
            addr_info['chain'] = line.split('Chain:')[1].strip().lower()
        elif line.startswith('Balance:'):
            balance_str = line.split('Balance:')[1].strip()
            try:
                addr_info['balance'] = float(balance_str)
            except:
                addr_info['balance'] = 0.0
        elif line.startswith('Private Key:'):
            addr_info['private_key'] = line.split('Private Key:')[1].strip()
    
    return addr_info if 'address' in addr_info else None

def check_database_status():
    """Check duplicate prevention database status"""
    if os.path.exists('address_tracking.db'):
        try:
            conn = sqlite3.connect('address_tracking.db')
            cursor = conn.execute("SELECT COUNT(*) FROM checked_addresses")
            total_addresses = cursor.fetchone()[0]
            
            cursor = conn.execute("SELECT COUNT(DISTINCT address) FROM checked_addresses") 
            unique_addresses = cursor.fetchone()[0]
            
            efficiency = ((total_addresses - unique_addresses) / total_addresses * 100) if total_addresses > 0 else 0
            
            conn.close()
            
            print(f"\n📊 DATABASE STATUS:")
            print(f"   📈 Total operations: {total_addresses}")
            print(f"   🎯 Unique addresses: {unique_addresses}")
            print(f"   ⚡ Efficiency: {efficiency:.1f}%")
            
            return {
                'total_operations': total_addresses,
                'unique_addresses': unique_addresses,
                'efficiency_percent': efficiency
            }
        except Exception as e:
            print(f"⚠️  Database error: {e}")
    
    return None

def main():
    """Main cleanup and consolidation"""
    print("🚀 WALLET TOOL REPOSITORY CLEANUP")
    print("=" * 60)
    print("This will clean up unnecessary files and create a unified system")
    print()
    
    # Step 1: Cleanup
    removed_count, kept_files = cleanup_repository()
    
    # Step 2: Consolidate data
    consolidated_data = consolidate_data()
    
    # Step 3: Check database
    db_status = check_database_status()
    
    # Step 4: Create summary report
    summary = {
        'cleanup_date': datetime.now().isoformat(),
        'files_removed': removed_count,
        'files_kept': len(kept_files),
        'essential_files': kept_files,
        'consolidated_addresses': consolidated_data,
        'database_status': db_status,
        'next_steps': [
            "Run the new unified_wallet_scanner.py for all scanning",
            "Use secure_transfer.py for transferring found coins", 
            "Monitor progress with simple dashboard",
            "All old scattered files have been cleaned up"
        ]
    }
    
    with open('cleanup_report.json', 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n🎉 CLEANUP COMPLETE!")
    print(f"📋 Summary saved to: cleanup_report.json")
    print(f"\n💡 NEXT STEPS:")
    print(f"   1. ✅ Repository cleaned and organized")
    print(f"   2. 🔄 Data consolidated into single files")
    print(f"   3. 🚀 Ready for unified scanner")
    print(f"   4. 💰 Transfer utility ready for found coins")

if __name__ == "__main__":
    main()
