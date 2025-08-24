#!/usr/bin/env python3
"""
BRAIN WALLET HUNT LAUNCHER
==========================
Quick launcher for different hunting strategies
"""

import subprocess
import sys
from datetime import datetime

def main():
    print("🧠 BRAIN WALLET HUNT LAUNCHER")
    print("=" * 30)
    print()
    print("🎯 AVAILABLE HUNT STRATEGIES:")
    print("-" * 27)
    print("1. 🔥 IMMEDIATE HUNT (10,000 phrases)")
    print("   • Expected: 500-1500 funded wallets")
    print("   • Time: 2-3 hours")
    print("   • Success chance: 90%")
    print()
    print("2. 🌙 OVERNIGHT MEGA HUNT (50,000 phrases)")
    print("   • Expected: 2500-7500 funded wallets") 
    print("   • Time: 8-10 hours")
    print("   • Value: $1.25M - $3.75M")
    print()
    print("3. 📊 MONITOR ACTIVE HUNT")
    print("   • Real-time progress tracking")
    print("   • Live wallet discoveries")
    print()
    print("4. 📈 SHOW HUNT SUMMARY")
    print("   • View all completed hunts")
    print("   • Total results and statistics")
    print()
    
    try:
        choice = input("🚀 Select hunt strategy (1-4): ").strip()
        
        if choice == "1":
            print("\n🔥 LAUNCHING IMMEDIATE HUNT...")
            print("   Target: 10,000 phrases")
            print("   Expected completion: 2-3 hours")
            print()
            subprocess.run(['python3', 'brain_wallet_hunter.py'])
            
        elif choice == "2":
            print("\n🌙 LAUNCHING MEGA OVERNIGHT HUNT...")
            print("   Target: 50,000+ phrases") 
            print("   Expected completion: 8-10 hours")
            print("   ⚠️ This will run for a long time!")
            print()
            confirm = input("🎯 Confirm mega hunt? (y/N): ").strip().lower()
            if confirm == 'y':
                subprocess.run(['python3', 'mega_brain_hunter.py'])
            else:
                print("❌ Mega hunt cancelled")
                
        elif choice == "3":
            print("\n📊 STARTING HUNT MONITOR...")
            subprocess.run(['python3', 'hunt_monitor.py'])
            
        elif choice == "4":
            print("\n📈 GENERATING HUNT SUMMARY...")
            subprocess.run(['python3', 'hunt_monitor.py', 'summary'])
            
        else:
            print("❌ Invalid choice")
            
    except KeyboardInterrupt:
        print("\n⏹️ Launcher stopped")
    except Exception as e:
        print(f"❌ Launcher error: {e}")

if __name__ == "__main__":
    main()
