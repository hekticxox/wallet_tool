#!/usr/bin/env python3
"""
Net501 Sample Balance Checker
Checks the 42 extracted private keys for balances
"""

import json
import time
from datetime import datetime
from enhanced_balance_checker import EnhancedBalanceChecker
from eth_keys import keys
from bit import Key

def derive_ethereum_address(private_key_hex):
    """Derive Ethereum address from private key"""
    try:
        private_key_bytes = bytes.fromhex(private_key_hex)
        private_key = keys.PrivateKey(private_key_bytes)
        return private_key.public_key.to_checksum_address()
    except Exception:
        return None

def derive_bitcoin_address(private_key_hex):
    """Derive Bitcoin address from private key"""
    try:
        bitcoin_key = Key.from_hex(private_key_hex)
        return bitcoin_key.address
    except Exception:
        return None

def main():
    print("="*60)
    print("NET501 SAMPLE BALANCE CHECKER")
    print("="*60)
    
    # Load sample keys
    with open("/home/admin/wallet_tool/net501_sample_keys.txt", "r") as f:
        private_keys = [line.strip() for line in f if line.strip()]
    
    print(f"Loaded {len(private_keys)} private keys from net501 sample")
    
    balance_checker = EnhancedBalanceChecker()
    funded_wallets = []
    total_checked = 0
    start_time = datetime.now()
    
    for i, private_key in enumerate(private_keys):
        print(f"\n[{i+1}/{len(private_keys)}] Checking: {private_key[:10]}...{private_key[-10:]}")
        
        eth_address = derive_ethereum_address(private_key)
        btc_address = derive_bitcoin_address(private_key)
        
        print(f"ETH: {eth_address}")
        print(f"BTC: {btc_address}")
        
        # Check Ethereum
        if eth_address:
            try:
                eth_result = balance_checker.check_ethereum_balance_multiple_apis(eth_address)
                eth_balance = float(eth_result.get('balance_eth', 0))
                if eth_balance > 0:
                    print(f"🎉🎉🎉 FUNDED ETHEREUM WALLET! 🎉🎉🎉")
                    print(f"Address: {eth_address}")
                    print(f"Balance: {eth_balance:.8f} ETH")
                    print(f"Private Key: {private_key}")
                    
                    funded_wallets.append({
                        "type": "ethereum",
                        "address": eth_address,
                        "private_key": private_key,
                        "balance_eth": eth_balance,
                        "timestamp": datetime.now().isoformat(),
                        "source": "net501"
                    })
                else:
                    print(f"ETH Balance: 0")
            except Exception as e:
                print(f"ETH Error: {e}")
        
        # Check Bitcoin
        if btc_address:
            try:
                btc_result = balance_checker.check_bitcoin_balance_multiple_apis(btc_address)
                btc_balance = float(btc_result.get('balance_btc', 0))
                if btc_balance > 0:
                    print(f"🎉🎉🎉 FUNDED BITCOIN WALLET! 🎉🎉🎉")
                    print(f"Address: {btc_address}")
                    print(f"Balance: {btc_balance:.8f} BTC")
                    print(f"Private Key: {private_key}")
                    
                    funded_wallets.append({
                        "type": "bitcoin",
                        "address": btc_address,
                        "private_key": private_key,
                        "balance_btc": btc_balance,
                        "timestamp": datetime.now().isoformat(),
                        "source": "net501"
                    })
                else:
                    print(f"BTC Balance: 0")
            except Exception as e:
                print(f"BTC Error: {e}")
        
        total_checked += 1
        
        # Rate limiting
        if i < len(private_keys) - 1:
            time.sleep(1)
    
    # Final results
    print("\n" + "="*60)
    print("NET501 SAMPLE SCAN COMPLETE!")
    print("="*60)
    
    if funded_wallets:
        print(f"🎉 SUCCESS! Found {len(funded_wallets)} funded wallets!")
        
        filename = f"FUNDED_NET501_SAMPLE_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(funded_wallets, f, indent=2)
        print(f"Results saved to: {filename}")
        
        for wallet in funded_wallets:
            print(f"\n🎯 {wallet['type'].upper()} WALLET:")
            print(f"   Address: {wallet['address']}")
            if wallet['type'] == 'ethereum':
                print(f"   Balance: {wallet['balance_eth']:.8f} ETH")
            else:
                print(f"   Balance: {wallet['balance_btc']:.8f} BTC")
            print(f"   Private Key: {wallet['private_key']}")
    else:
        print(f"No funded wallets found in {total_checked} net501 sample keys")
    
    # Save summary
    summary = {
        "dataset": "net501_sample",
        "total_keys_checked": total_checked,
        "funded_wallets_found": len(funded_wallets),
        "funded_wallets": funded_wallets,
        "scan_duration_minutes": (datetime.now() - start_time).total_seconds() / 60,
        "scan_timestamp": datetime.now().isoformat()
    }
    
    with open(f"net501_sample_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n✅ Net501 sample scan finished! Checked {total_checked} wallets")

if __name__ == "__main__":
    main()
