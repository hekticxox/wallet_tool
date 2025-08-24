#!/usr/bin/env python3
"""
Comprehensive Private Key Balance Report Generator
================================================
Analyzes all available private keys and balance scan results
"""

import json
import glob
import os
from datetime import datetime
from pathlib import Path

def generate_comprehensive_balance_report():
    """Generate comprehensive report of all private keys and balance results"""
    print("🔍 COMPREHENSIVE PRIVATE KEY BALANCE ANALYSIS")
    print("=" * 55)
    print()
    
    # 1. Count all available private keys
    print("📊 AVAILABLE PRIVATE KEYS INVENTORY:")
    print("-" * 35)
    
    total_keys = 0
    key_types = {}
    source_files = 0
    
    # Check extraction result files
    for pattern in ['*extraction_results_*.json', 'data/keys/*.json', 'data/keys/*.txt']:
        for file_path in glob.glob(pattern):
            if os.path.getsize(file_path) == 0:
                continue
                
            try:
                source_files += 1
                if file_path.endswith('.json'):
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                        if 'findings' in data:
                            findings = data['findings']
                            file_keys = len(findings)
                            total_keys += file_keys
                            
                            # Count by type
                            for finding in findings:
                                finding_type = finding.get('type', 'unknown')
                                key_types[finding_type] = key_types.get(finding_type, 0) + 1
                            
                            print(f"  • {os.path.basename(file_path)}: {file_keys:,} keys")
                        elif isinstance(data, list):
                            file_keys = len(data)
                            total_keys += file_keys
                            print(f"  • {os.path.basename(file_path)}: {file_keys:,} keys")
                else:
                    # Text file - count lines
                    with open(file_path, 'r') as f:
                        lines = [line.strip() for line in f if line.strip()]
                        file_keys = len(lines)
                        total_keys += file_keys
                        key_types['hex_keys'] = key_types.get('hex_keys', 0) + file_keys
                        print(f"  • {os.path.basename(file_path)}: {file_keys:,} keys")
                        
            except Exception as e:
                print(f"  ⚠️ Could not read {file_path}: {e}")
    
    print(f"\n📈 SUMMARY:")
    print(f"   Total keys available: {total_keys:,}")
    print(f"   Source files: {source_files}")
    print(f"   Key types breakdown:")
    for key_type, count in sorted(key_types.items(), key=lambda x: x[1], reverse=True):
        print(f"     - {key_type}: {count:,}")
    
    # 2. Analyze balance scan results
    print(f"\n💰 BALANCE SCAN RESULTS ANALYSIS:")
    print("-" * 34)
    
    total_scanned = 0
    total_funded = 0
    total_value = 0.0
    scan_sessions = 0
    latest_scan = None
    
    # Check balance scan results
    for file_path in glob.glob('results/balance_scan_results_*.json'):
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                scan_sessions += 1
                keys_scanned = data.get('keys_scanned', 0)
                funded_wallets = data.get('funded_wallets', 0)
                
                total_scanned += keys_scanned
                total_funded += funded_wallets
                
                # Track latest scan
                timestamp = data.get('timestamp', '')
                if not latest_scan or timestamp > latest_scan:
                    latest_scan = timestamp
                
                if funded_wallets > 0:
                    print(f"  🎉 FUNDED WALLET FOUND in {os.path.basename(file_path)}")
                    print(f"     Keys scanned: {keys_scanned}")
                    print(f"     Funded wallets: {funded_wallets}")
                    
        except Exception as e:
            print(f"  ⚠️ Could not read scan result: {e}")
    
    # Check hex scan results
    for file_path in glob.glob('results/hex_scan_results_*.json'):
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                scan_sessions += 1
                keys_scanned = data.get('keys_scanned', 0)
                funded_wallets = data.get('funded_wallets', 0)
                
                total_scanned += keys_scanned
                total_funded += funded_wallets
                
                if funded_wallets > 0:
                    print(f"  🎉 FUNDED WALLET FOUND in {os.path.basename(file_path)}")
                    
        except Exception as e:
            print(f"  ⚠️ Could not read hex scan result: {e}")
    
    print(f"\n📊 SCANNING SUMMARY:")
    print(f"   Total scan sessions: {scan_sessions}")
    print(f"   Total keys scanned: {total_scanned:,}")
    print(f"   Funded wallets found: {total_funded}")
    print(f"   Success rate: {(total_funded/max(total_scanned,1)*100):.4f}%")
    print(f"   Latest scan: {latest_scan}")
    
    # 3. Calculate scanning progress
    print(f"\n📈 SCANNING PROGRESS:")
    print("-" * 20)
    scanned_percentage = (total_scanned / max(total_keys, 1)) * 100
    print(f"   Keys scanned: {total_scanned:,} / {total_keys:,}")
    print(f"   Progress: {scanned_percentage:.2f}%")
    print(f"   Remaining: {total_keys - total_scanned:,} keys")
    
    # 4. Recommendations
    print(f"\n💡 RECOMMENDATIONS:")
    print("-" * 15)
    if total_funded == 0:
        print("   🔍 No funded wallets found yet")
        print("   📈 Consider scanning more keys from different sources")
        print("   🌐 Try multi-chain scanning (Ethereum, BSC, Polygon)")
        print("   🎯 Focus on high-priority/promising key sets")
    else:
        print(f"   🎉 Found {total_funded} funded wallets!")
        print("   💰 Continue scanning to find more")
    
    if scanned_percentage < 1:
        print(f"   ⚡ Only {scanned_percentage:.2f}% of keys scanned - huge potential remaining")
    
    # 5. Next steps
    print(f"\n🚀 SUGGESTED NEXT ACTIONS:")
    print("-" * 25)
    print("   1. python3 main.py scan --max-keys 1000")
    print("   2. python3 src/scanners/simple_hex_scanner.py --input-file data/keys/net599_FUNDED_keys.txt --max-keys 500")
    print("   3. Scan other key files in data/keys/ directory")
    print("   4. Set up API keys for multi-chain scanning")
    
    print(f"\n" + "=" * 55)
    print(f"🔍 Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎯 Status: {total_keys:,} keys available, {total_scanned:,} scanned, {total_funded} funded found")

if __name__ == "__main__":
    generate_comprehensive_balance_report()
