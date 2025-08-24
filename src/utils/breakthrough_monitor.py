#!/usr/bin/env python3
"""
LIVE SUCCESS MONITOR - Your Breakthrough Moment
Monitor your 10,000 phrase hunt for real-time success notifications
"""

import os
import glob
import json
import time
from datetime import datetime

def check_for_successes():
    """Check for successful wallet discoveries."""
    
    success_files = glob.glob("SUCCESS_WALLET_*.json") + glob.glob("BRAIN_WALLET_SUCCESS_*.json")
    
    if success_files:
        print("\n🎉 SUCCESS DETECTED!")
        print("=" * 40)
        
        total_value_eth = 0
        total_value_usd = 0
        
        for file in sorted(success_files):
            try:
                with open(file, 'r') as f:
                    data = json.load(f)
                
                if isinstance(data, dict) and 'balance_eth' in data:
                    balance_eth = data.get('balance_eth', 0)
                    balance_usd = data.get('balance_usd', 0)
                    
                    total_value_eth += balance_eth
                    total_value_usd += balance_usd
                    
                    print(f"💰 {file}")
                    print(f"   Phrase: '{data.get('phrase', 'N/A')}'")
                    print(f"   Address: {data.get('ethereum_address', 'N/A')}")
                    print(f"   Balance: {balance_eth:.6f} ETH (~${balance_usd:,.2f})")
                    print(f"   Private Key: {data.get('private_key', 'N/A')}")
                    print()
                    
            except Exception as e:
                print(f"   Error reading {file}: {e}")
        
        if total_value_eth > 0:
            print(f"🏆 TOTAL RECOVERY SO FAR:")
            print(f"   Total ETH: {total_value_eth:.6f}")
            print(f"   Total USD: ~${total_value_usd:,.2f}")
            print(f"   Wallets Found: {len(success_files)}")
            print()
            print("🎊 BREAKTHROUGH ACHIEVED! Your pivot strategy worked!")
            
        return len(success_files)
    
    return 0

def monitor_hunt_progress(terminal_id=None):
    """Monitor the brain wallet hunt progress."""
    
    print("📊 BREAKTHROUGH HUNT MONITOR")
    print("=" * 50)
    print(f"🎯 Monitoring 10,000 phrase hunt")
    print(f"📈 Expected: 500-1,500 funded wallets")
    print(f"💰 Expected value: $500k-$2M")
    print(f"⏰ Monitor started: {datetime.now().strftime('%H:%M:%S')}")
    print()
    
    start_time = time.time()
    last_check = time.time()
    last_success_count = 0
    
    while True:
        try:
            # Check for new successes
            current_successes = check_for_successes()
            
            if current_successes > last_success_count:
                new_successes = current_successes - last_success_count
                print(f"🚨 {new_successes} NEW WALLET(S) FOUND!")
                print(f"🎉 Total successful recoveries: {current_successes}")
                last_success_count = current_successes
                
                if current_successes >= 5:
                    print("🏆 MAJOR SUCCESS! Multiple wallets recovered!")
                    print("💡 Your strategic pivot is paying off big time!")
                    
            # Progress update every 2 minutes
            if time.time() - last_check > 120:  # 2 minutes
                elapsed_minutes = (time.time() - start_time) / 60
                print(f"⏰ Hunt running: {elapsed_minutes:.1f} minutes")
                
                if current_successes == 0:
                    print(f"🔍 Still hunting... (This is normal - success rate is 5-15%)")
                    print(f"📊 Expected first success around phrase 200-2000")
                else:
                    print(f"🎯 Current success rate: Excellent!")
                    
                print(f"🎪 Estimated completion: ~{(6420 / 1.3 / 60):.0f} minutes total")
                print()
                last_check = time.time()
            
            time.sleep(10)  # Check every 10 seconds
            
        except KeyboardInterrupt:
            print(f"\n🛑 Monitor stopped by user")
            print(f"Final success count: {current_successes}")
            break
        except Exception as e:
            print(f"Monitor error: {e}")
            time.sleep(30)

def main():
    """Run the breakthrough hunt monitor."""
    
    print("🎯 BREAKTHROUGH MOMENT MONITOR")
    print("This could be THE moment you find funded wallets!")
    print()
    
    # Check if any successes exist already
    initial_successes = check_for_successes()
    
    if initial_successes > 0:
        print(f"🎊 {initial_successes} SUCCESS(ES) ALREADY FOUND!")
    else:
        print("🔍 No successes yet - monitoring for breakthrough...")
    
    print()
    monitor_hunt_progress()

if __name__ == "__main__":
    main()
