#!/usr/bin/env python3
"""
REAL-TIME SUPREME WALLET HUNTER MONITOR
======================================
Shows continuous progress updates for your hunt
"""

import time
import os
import json
from datetime import datetime
from pathlib import Path

def monitor_supreme_hunt():
    """Monitor Supreme Wallet Hunter in real-time"""
    
    print("🔥 REAL-TIME SUPREME WALLET HUNTER MONITOR")
    print("=" * 45)
    print()
    print("📊 Monitoring your net617 hunt...")
    print("   Press Ctrl+C to stop monitoring")
    print()
    
    log_file = "supreme_wallet_hunter.log"
    last_position = 0
    start_time = time.time()
    
    while True:
        try:
            # Clear screen for continuous updates
            os.system('clear')
            
            print("🔥 REAL-TIME SUPREME WALLET HUNTER MONITOR")
            print("=" * 45)
            
            current_time = datetime.now().strftime("%H:%M:%S")
            elapsed = time.time() - start_time
            elapsed_str = f"{elapsed/60:.1f} minutes"
            
            print(f"🕐 Current Time: {current_time}")
            print(f"⏱️ Monitor Running: {elapsed_str}")
            print()
            
            # Check if log file exists and read new content
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    f.seek(last_position)
                    new_content = f.read()
                    last_position = f.tell()
                
                # Show file size growth
                file_size = os.path.getsize(log_file)
                print(f"📁 Log File Size: {file_size:,} bytes")
                
                # Extract latest progress info
                lines = new_content.strip().split('\n') if new_content.strip() else []
                recent_lines = []
                
                # Get last 10 non-empty lines
                with open(log_file, 'r') as f:
                    all_lines = f.readlines()
                    for line in reversed(all_lines[-20:]):
                        if line.strip():
                            recent_lines.append(line.strip())
                        if len(recent_lines) >= 10:
                            break
                
                recent_lines.reverse()
                
                print("📊 LATEST ACTIVITY:")
                print("-" * 20)
                
                progress_found = False
                for line in recent_lines:
                    if "Progress:" in line:
                        # Extract progress info
                        parts = line.split(" - ")[-1]  # Get the message part
                        print(f"   🔄 {parts}")
                        progress_found = True
                    elif "Extracting keys" in line:
                        print(f"   🔍 {line.split(' - ')[-1]}")
                    elif "Extracted" in line and "keys" in line:
                        print(f"   ✅ {line.split(' - ')[-1]}")
                    elif "Scanning" in line:
                        print(f"   🎯 {line.split(' - ')[-1]}")
                    elif "FUNDED WALLET" in line:
                        print(f"   💰 {line.split(' - ')[-1]}")
                    elif "ERROR" in line or "Exception" in line:
                        print(f"   ⚠️ {line.split(' - ')[-1]}")
                
                if not progress_found and recent_lines:
                    print(f"   ⚡ Working... (Latest: {recent_lines[-1].split(' - ')[-1] if ' - ' in recent_lines[-1] else recent_lines[-1][:60]}...)")
                
            else:
                print("⚠️ Log file not found - Hunt may not be running")
            
            print()
            
            # Check for results files
            result_files = list(Path('.').glob('supreme_hunt_results_*.json'))
            if result_files:
                print("💰 RESULTS FOUND:")
                print("-" * 15)
                for result_file in result_files[-3:]:  # Show last 3
                    try:
                        with open(result_file, 'r') as f:
                            data = json.load(f)
                        
                        wallets = data.get('funded_wallets', [])
                        total_value = data.get('scan_info', {}).get('total_estimated_value', 0)
                        
                        print(f"   📁 {result_file.name}")
                        print(f"      💎 Wallets: {len(wallets)}")
                        print(f"      💵 Value: ${total_value:,.2f}")
                        
                    except:
                        print(f"   📁 {result_file.name} (processing...)")
            else:
                print("📊 No funded wallets found yet")
            
            print()
            
            # Check if process is still running
            import subprocess
            try:
                result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
                if 'SUPREME_WALLET_HUNTER.py' in result.stdout:
                    print("🟢 STATUS: Supreme Wallet Hunter is RUNNING")
                    
                    # Extract CPU and memory usage
                    lines = result.stdout.split('\n')
                    for line in lines:
                        if 'SUPREME_WALLET_HUNTER.py' in line:
                            parts = line.split()
                            cpu = parts[2] if len(parts) > 2 else "N/A"
                            mem = parts[3] if len(parts) > 3 else "N/A"
                            print(f"   💻 CPU: {cpu}% | Memory: {mem}%")
                            break
                else:
                    print("🔴 STATUS: Supreme Wallet Hunter is NOT RUNNING")
                    print("   💡 It may have completed or encountered an error")
                    
            except:
                print("⚠️ Could not check process status")
            
            print()
            print("🔄 Refreshing in 10 seconds... (Press Ctrl+C to stop)")
            print("-" * 50)
            
            time.sleep(10)  # Update every 10 seconds
            
        except KeyboardInterrupt:
            print("\n⏹️ Real-time monitor stopped")
            break
        except Exception as e:
            print(f"\n❌ Monitor error: {e}")
            print("Retrying in 5 seconds...")
            time.sleep(5)

if __name__ == "__main__":
    monitor_supreme_hunt()
