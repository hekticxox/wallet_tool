#!/usr/bin/env python3
"""
LIVE SUPREME HUNTER MONITOR
===========================
Real-time monitoring with detailed progress
"""

import time
import os
import subprocess
import glob
import json
from datetime import datetime


def get_live_progress():
    """Get live progress from the Supreme Wallet Hunter"""
    
    print("� SUPREME WALLET HUNTER - LIVE MONITOR")
    print("=" * 45)
    print()
    
    last_log_size = 0
    
    while True:
        try:
            # Check if process is running
            result = subprocess.run(['pgrep', '-f', 'SUPREME_WALLET_HUNTER'], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                pids = result.stdout.strip().split('\n')
                print(f"🟢 STATUS: ACTIVE (PID: {pids[0]})")
                
                # Get CPU and memory usage
                cpu_cmd = ['ps', '-p', pids[0], '-o', '%cpu,%mem', '--no-headers']
                cpu_result = subprocess.run(cpu_cmd, capture_output=True, text=True)
                if cpu_result.returncode == 0:
                    cpu_mem = cpu_result.stdout.strip().split()
                    if len(cpu_mem) >= 2:
                        print(f"   💻 CPU: {cpu_mem[0]}% | Memory: {cpu_mem[1]}%")
            else:
                print("🔴 STATUS: NOT RUNNING")
                print("   ⚠️ Supreme Wallet Hunter is not active")
            
            print(f"🕐 Last Update: {datetime.now().strftime('%H:%M:%S')}")
            print()
            
            # Check log file
            log_file = "supreme_wallet_hunter.log"
            if os.path.exists(log_file):
                current_size = os.path.getsize(log_file)
                print(f"📋 Log File Size: {current_size:,} bytes")
                
                if current_size > last_log_size:
                    print("🆕 NEW ACTIVITY DETECTED!")
                    last_log_size = current_size
                else:
                    print("⏸️ No new activity in last 15 seconds")
                
                # Show last 15 lines from log
                try:
                    with open(log_file, 'r') as f:
                        lines = f.readlines()
                        recent_lines = lines[-15:]
                        
                        print("\n� LATEST ACTIVITY:")
                        print("-" * 20)
                        for line in recent_lines:
                            if 'INFO' in line and any(x in line for x in ['Progress:', 'Found:', 'Processing:', 'Extraction:', 'MILESTONE:']):
                                # Extract just the important part
                                if ' - ' in line:
                                    message = line.split(' - ')[-1].strip()
                                    print(f"   🔄 {message}")
                        
                except Exception as e:
                    print(f"❌ Error reading log: {e}")
            else:
                print("📋 No log file found")
            
            # Check for results files
            result_files = []
            try:
                import glob
                result_files = glob.glob("supreme_hunt_results_*.json")
            except:
                pass
            
            if result_files:
                print(f"\n💰 {len(result_files)} result file(s) found")
                try:
                    import json
                    latest_file = max(result_files, key=os.path.getmtime)
                    with open(latest_file, 'r') as f:
                        data = json.load(f)
                    
                    funded_count = data.get('scan_info', {}).get('total_funded_wallets', 0)
                    if funded_count > 0:
                        total_value = data.get('scan_info', {}).get('total_estimated_value', 0)
                        print(f"🎉 FUNDED WALLETS FOUND: {funded_count}")
                        print(f"� TOTAL VALUE: ${total_value:,.2f}")
                    else:
                        print("📊 No funded wallets found yet")
                        
                except Exception as e:
                    print(f"⚠️ Error reading results: {e}")
            else:
                print("\n📊 No result files yet")
            
            print("\n" + "="*50)
            print("🔄 Refreshing in 15 seconds... (Ctrl+C to stop)")
            print("="*50)
            
            time.sleep(15)
            
            # Clear screen for next update
            os.system('clear')
            
        except KeyboardInterrupt:
            print("\n⏹️ Monitor stopped by user")
            break
        except Exception as e:
            print(f"❌ Monitor error: {e}")
            time.sleep(10)

if __name__ == "__main__":
    get_live_progress()
