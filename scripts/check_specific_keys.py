#!/usr/bin/env python3
"""
Check the specific private keys extracted from the Chrome Profile 2 Cookies.txt
"""

from enhanced_balance_checker import EnhancedBalanceChecker
from eth_keys import keys as eth_keys
from bit import PrivateKey

def main():
    """Check the specific discovered private keys"""
    
    # The actual full private keys found in the Chrome Profile 2 Cookies.txt
    private_keys = [
        "31d73869b1ea6773862bb7a95397fbbbb0a793fb3f72379c147e73c30328298c",
        "d330ae8912dde5252ca0fc0d1e08aba8f87544157e262d135630d7098a65dbea", 
        "05ab467b14617b2a75d2c0b54fcf52b1b8e1080df8afd1801c0b352feeb05ee7"
    ]
    
    print("🔍 CHECKING DISCOVERED PRIVATE KEYS")
    print("=" * 70)
    
    # Initialize balance checker
    checker = EnhancedBalanceChecker()
    funded_wallets = []
    
    for i, private_key in enumerate(private_keys, 1):
        print(f"\n🔑 Checking Key {i}/3: {private_key[:8]}...{private_key[-8:]}")
        print(f"   Full key: {private_key}")
        
        # Check if valid Ethereum private key
        try:
            eth_private_key = eth_keys.PrivateKey(bytes.fromhex(private_key))
            eth_address = eth_private_key.public_key.to_checksum_address()
            print(f"   📍 ETH Address: {eth_address}")
            
            # Check Ethereum balance
            eth_result = checker.check_ethereum_balance_multiple_apis(eth_address)
            if eth_result.get('success'):
                balance = eth_result.get('balance_eth', 0)
                print(f"   💰 ETH Balance: {balance} ETH")
                if balance > 0:
                    funded_wallets.append({
                        'private_key': private_key,
                        'currency': 'ETH',
                        'address': eth_address,
                        'balance': balance
                    })
                    print(f"   🎉 FUNDED ETH WALLET FOUND!")
            else:
                print(f"   ❌ ETH balance check failed")
        except Exception as e:
            print(f"   ❌ Invalid Ethereum private key: {e}")
        
        # Try Bitcoin
        try:
            btc_private_key = PrivateKey(private_key)
            btc_address = btc_private_key.address
            print(f"   📍 BTC Address: {btc_address}")
            
            # Check Bitcoin balance
            btc_result = checker.check_bitcoin_balance_multiple_apis(btc_address)
            if btc_result.get('success'):
                balance = btc_result.get('balance_btc', 0)
                print(f"   💰 BTC Balance: {balance} BTC")
                if balance > 0:
                    funded_wallets.append({
                        'private_key': private_key,
                        'currency': 'BTC', 
                        'address': btc_address,
                        'balance': balance
                    })
                    print(f"   🎉 FUNDED BTC WALLET FOUND!")
            else:
                print(f"   ❌ BTC balance check failed")
        except Exception as e:
            print(f"   ❌ Invalid Bitcoin private key: {e}")
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 FINAL RESULTS")
    print(f"🔑 Private keys checked: {len(private_keys)}")
    print(f"💰 Funded wallets found: {len(funded_wallets)}")
    
    if funded_wallets:
        print("\n🎉🎉🎉 FUNDED WALLETS DISCOVERED! 🎉🎉🎉")
        for wallet in funded_wallets:
            print(f"\n💰 {wallet['currency']} WALLET:")
            print(f"   Address: {wallet['address']}")
            print(f"   Balance: {wallet['balance']} {wallet['currency']}")
            print(f"   Private Key: {wallet['private_key']}")
        
        # Save critical results
        import json
        with open('CRITICAL_FUNDED_WALLETS.json', 'w') as f:
            json.dump(funded_wallets, f, indent=2)
        print(f"\n🚨 CRITICAL: Results saved to CRITICAL_FUNDED_WALLETS.json")
        print("🔐 SECURE THESE PRIVATE KEYS IMMEDIATELY!")
        
    else:
        print("\n❌ No funded wallets found")

if __name__ == "__main__":
    main()
