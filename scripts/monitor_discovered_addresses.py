#!/usr/bin/env python3
"""
Monitor discovered addresses for incoming transactions
"""

import json
import time
from datetime import datetime
from enhanced_balance_checker import EnhancedBalanceChecker

def main():
    """Monitor discovered addresses for activity"""
    
    print("📡 MONITORING DISCOVERED ADDRESSES")
    print("=" * 50)
    
    # Load discovered addresses
    addresses_to_monitor = [
        {
            "address": "0xA6A3c8d80AD9FEBe877B2A95aa298FE8A4635776",
            "currency": "ETH",
            "has_private_key": True
        },
        {
            "address": "0xc1489967c6ee7e64dAd17607532caBeF8f5bcfE7", 
            "currency": "ETH",
            "has_private_key": True
        },
        {
            "address": "0xEA609424930d0D48d613d4fe501F3f4B0B0Dd72E",
            "currency": "ETH", 
            "has_private_key": True
        },
        {
            "address": "3AXwj1tZqoRA2xpxHNAkShbNwZtxtwYbwY",
            "currency": "BTC",
            "has_private_key": False
        }
    ]
    
    checker = EnhancedBalanceChecker()
    
    print(f"👀 Monitoring {len(addresses_to_monitor)} addresses...")
    print(f"🕐 Check time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    funded_found = False
    
    for addr_info in addresses_to_monitor:
        address = addr_info["address"]
        currency = addr_info["currency"]
        has_key = addr_info["has_private_key"]
        
        print(f"📍 {currency}: {address}")
        print(f"   🔑 Private Key: {'✅ Available' if has_key else '❌ Not Available'}")
        
        if currency == "ETH":
            result = checker.check_ethereum_balance_multiple_apis(address)
            if result.get('success'):
                balance = result.get('balance_eth', 0)
                print(f"   💰 Balance: {balance} ETH")
                if balance > 0:
                    funded_found = True
                    print(f"   🚨 FUNDED WALLET DETECTED!")
                    if has_key:
                        print(f"   ✅ RECOVERABLE - Private key available!")
                    else:
                        print(f"   ⚠️  Watch-only - Private key not available")
        
        elif currency == "BTC":
            result = checker.check_bitcoin_balance_multiple_apis(address)
            if result.get('success'):
                balance = result.get('balance_btc', 0)
                print(f"   💰 Balance: {balance} BTC")
                if balance > 0:
                    funded_found = True
                    print(f"   🚨 FUNDED WALLET DETECTED!")
                    if has_key:
                        print(f"   ✅ RECOVERABLE - Private key available!")
                    else:
                        print(f"   ⚠️  Watch-only - Private key not available")
        
        print()
    
    if funded_found:
        print("🎉 FUNDED WALLETS DETECTED! Check output above for details.")
        # Log to file
        with open('wallet_monitor_alert.txt', 'a') as f:
            f.write(f"{datetime.now()}: FUNDED WALLET DETECTED!\n")
    else:
        print("✅ All monitored addresses are still empty")
    
    print("\n💡 Run this script periodically to monitor for incoming funds")

if __name__ == "__main__":
    main()
