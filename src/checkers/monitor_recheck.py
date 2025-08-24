#!/usr/bin/env python3
"""
Monitor the comprehensive recheck progress and show any funded wallets found
"""

import os
import time
import glob
import json
from datetime import datetime

def monitor_recheck_progress():
    print("🔍 MONITORING COMPREHENSIVE WALLET RECHECK")
    print("=" * 60)
    print("Scanning 106,770 unique wallet addresses...")
    print("This will take approximately 30-45 minutes to complete.")
    print("Any funded wallets found will be displayed immediately!")
    print("=" * 60)
    
    last_check = 0
    
    while True:
        # Check for new result files
        result_files = glob.glob('/home/admin/wallet_tool/comprehensive_recheck_results_*.json')
        funded_files = glob.glob('/home/admin/wallet_tool/newly_found_funded_wallets_*.json')
        
        # Check for any newly found funded wallets
        if funded_files:
            for funded_file in funded_files:
                try:
                    with open(funded_file, 'r') as f:
                        funded_wallets = json.load(f)
                    
                    if funded_wallets:
                        print(f"\n🎉 FUNDED WALLETS FOUND! ({len(funded_wallets)} wallets)")
                        print("-" * 40)
                        total_value = 0
                        for wallet in funded_wallets:
                            balance = float(wallet.get('balance_eth', 0))
                            total_value += balance
                            print(f"💰 {wallet['address']}: {balance:.6f} ETH")
                        print(f"💎 Total Value: {total_value:.6f} ETH")
                        print("-" * 40)
                except:
                    pass
        
        # Check if process is complete
        if result_files:
            latest_result = max(result_files, key=os.path.getctime)
            try:
                with open(latest_result, 'r') as f:
                    results = json.load(f)
                
                total_checked = results.get('total_addresses_checked', 0)
                funded_found = results.get('funded_addresses_found', 0)
                total_value = float(results.get('total_value_found_eth', 0))
                
                if total_checked >= 106770:
                    print(f"\n✅ COMPREHENSIVE RECHECK COMPLETE!")
                    print(f"📊 Total addresses checked: {total_checked:,}")
                    print(f"💰 Funded addresses found: {funded_found}")
                    print(f"💎 Total value found: {total_value:.6f} ETH")
                    
                    if funded_found > 0:
                        print(f"\n🎉 SUCCESS! Found {funded_found} funded wallets!")
                        print(f"📄 Results saved in: {latest_result}")
                    else:
                        print(f"\n📄 No new funded wallets found.")
                        print(f"📄 Complete results in: {latest_result}")
                    
                    break
                    
                # Show progress every 30 seconds
                current_time = time.time()
                if current_time - last_check > 30:
                    progress = (total_checked / 106770) * 100
                    print(f"⏳ Progress: {total_checked:,}/106,770 ({progress:.1f}%) - {funded_found} funded found")
                    last_check = current_time
                    
            except:
                pass
        
        time.sleep(5)  # Check every 5 seconds

if __name__ == "__main__":
    monitor_recheck_progress()
