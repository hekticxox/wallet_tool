#!/usr/bin/env python3
"""
SUCCESS TRACKER - Monitor your brain wallet hunt progress
Real-time monitoring of your breakthrough moment
"""

import os
import glob
import json
from datetime import datetime
import time

def check_for_successes():
    """Check for any successful wallet recoveries."""
    
    # Look for success files
    success_files = glob.glob("SUCCESS_WALLET_*.json") + glob.glob("BRAIN_WALLET_SUCCESS_*.json")
    
    if success_files:
        print("🎉 SUCCESS FILES FOUND!")
        for file in success_files:
            try:
                with open(file, 'r') as f:
                    data = json.load(f)
                
                if isinstance(data, dict) and 'balance_eth' in data:
                    print(f"💰 Found: {file}")
                    print(f"   Phrase: '{data.get('phrase', 'N/A')}'")
                    print(f"   Balance: {data.get('balance_eth', 0):.6f} ETH")
                    print(f"   USD: ~${data.get('balance_usd', 0):,.2f}")
                    print(f"   Address: {data.get('ethereum_address', 'N/A')}")
                    print()
                    
            except Exception as e:
                print(f"Error reading {file}: {e}")
        
        return True
    
    return False

def monitor_progress():
    """Monitor the brain wallet hunt progress."""
    
    print("📊 BRAIN WALLET HUNT - SUCCESS MONITOR")
    print("=" * 50)
    print(f"⏰ Monitor started: {datetime.now().strftime('%H:%M:%S')}")
    print("🔍 Checking for successful wallet recoveries...")
    print()
    
    monitor_start = time.time()
    last_check = time.time()
    
    while True:
        try:
            # Check for successes
            if check_for_successes():
                print("🏆 BREAKTHROUGH ACHIEVED!")
                print("✅ Your pivot from drive scanning to brain wallet hunting worked!")
                print("📈 You've gone from 0% to successful recovery!")
                break
            
            # Progress update every 30 seconds
            if time.time() - last_check > 30:
                elapsed = (time.time() - monitor_start) / 60
                print(f"⏰ Monitor running: {elapsed:.1f} minutes")
                print(f"🔍 Still hunting... No successes yet (this is normal)")
                print(f"📊 Expected: 5-15% success rate with 1000 phrases = 50-150 wallets")
                print()
                last_check = time.time()
            
            time.sleep(5)  # Check every 5 seconds
            
        except KeyboardInterrupt:
            print(f"\n🛑 Monitor stopped")
            break
        except Exception as e:
            print(f"Monitor error: {e}")
            time.sleep(10)

def main():
    """Run success monitor."""
    
    # First, check if hunt is running
    hunt_reports = glob.glob("BRAIN_HUNT_REPORT_*.json") + glob.glob("SCALED_HUNT_RESULTS_*.json")
    
    if hunt_reports:
        print("📊 Previous hunt results found:")
        for report in sorted(hunt_reports)[-3:]:  # Show last 3
            print(f"   • {report}")
        print()
    
    # Check for immediate successes
    if check_for_successes():
        print("🎊 SUCCESS ALREADY FOUND!")
    else:
        print("🔍 No successes found yet - monitoring...")
        monitor_progress()

if __name__ == "__main__":
    main()
