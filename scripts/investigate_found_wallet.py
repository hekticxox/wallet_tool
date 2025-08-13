#!/usr/bin/env python3
"""
Check the exact balance of the found NET501 wallet
"""

from enhanced_balance_checker import EnhancedBalanceChecker
import json

def check_found_wallet():
    """Check the exact balance of the discovered wallet"""
    
    address = "0x00299Cb32bfa1C11226dEE1cbC4eDd17901c9F7F"
    private_key = "aa102235a5ccb18bd3668c0e14aa3ea7e2503cfac2a7a9bf3d6549899e125af4"
    
    print("="*60)
    print("DETAILED WALLET INVESTIGATION")
    print("="*60)
    print(f"Address: {address}")
    print(f"Private Key: {private_key}")
    
    balance_checker = EnhancedBalanceChecker()
    
    # Check with multiple APIs for precise balance
    try:
        result = balance_checker.check_ethereum_balance_multiple_apis(address)
        print(f"\nBalance Result: {json.dumps(result, indent=2)}")
        
        balance_wei = result.get('balance_wei', 0)
        balance_eth = result.get('balance_eth', 0)
        
        print(f"\nDetailed Balance:")
        print(f"  Wei: {balance_wei}")
        print(f"  ETH: {balance_eth:.18f}")
        
        if balance_wei > 0:
            print(f"\n🎉 CONFIRMED FUNDED WALLET!")
            print(f"  This wallet contains {balance_wei} wei ({balance_eth:.18f} ETH)")
        else:
            print(f"\n❌ Wallet is actually empty (0 wei)")
            
    except Exception as e:
        print(f"Error checking balance: {e}")
    
    # Also check transaction history if possible
    print(f"\n📊 Checking transaction history...")
    # You can add transaction history checking here if needed

if __name__ == "__main__":
    check_found_wallet()
