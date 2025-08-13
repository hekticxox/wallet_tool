#!/usr/bin/env python3
"""
Batch Balance Checker for [US]172.58.122.84 Dataset
Checks all 165 unique private keys found in the extracted archive
"""

import json
import time
import sys
from datetime import datetime
import requests
from eth_keys import keys
from bit import Key, PrivateKeyTestnet

# Import the enhanced balance checker functions
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from enhanced_balance_checker import EnhancedBalanceChecker

def load_private_keys():
    """Load the extracted private keys"""
    with open("/home/admin/wallet_tool/extracted_keys_172_58_122_84.txt", "r") as f:
        keys_list = [line.strip() for line in f if line.strip() and len(line.strip()) == 64]
    return keys_list

def derive_ethereum_address(private_key_hex):
    """Derive Ethereum address from private key"""
    try:
        private_key_bytes = bytes.fromhex(private_key_hex)
        private_key = keys.PrivateKey(private_key_bytes)
        return private_key.public_key.to_checksum_address()
    except Exception as e:
        return None

def derive_bitcoin_address(private_key_hex):
    """Derive Bitcoin address from private key"""
    try:
        bitcoin_key = Key.from_hex(private_key_hex)
        return bitcoin_key.address
    except Exception as e:
        return None

def check_balances_batch(balance_checker, addresses_data):
    """Check balances for all addresses with rate limiting"""
    funded_wallets = []
    total_checked = 0
    
    print(f"Starting batch balance check for {len(addresses_data)} wallets...")
    
    for i, wallet_data in enumerate(addresses_data):
        private_key = wallet_data["private_key"]
        eth_address = wallet_data["ethereum_address"]
        btc_address = wallet_data["bitcoin_address"]
        
        print(f"\nChecking wallet {i+1}/{len(addresses_data)}")
        print(f"Private Key: {private_key[:10]}...{private_key[-10:]}")
        print(f"ETH Address: {eth_address}")
        print(f"BTC Address: {btc_address}")
        
        # Check Ethereum balance
        if eth_address:
            try:
                balance_result = balance_checker.check_ethereum_balance_multiple_apis(eth_address)
                balance_eth = float(balance_result.get('balance_eth', 0))
                
                if balance_eth > 0:
                    print(f"🎉 FUNDED ETHEREUM WALLET FOUND!")
                    print(f"   Address: {eth_address}")
                    print(f"   Balance: {balance_eth:.8f} ETH")
                    print(f"   Private Key: {private_key}")
                    
                    funded_wallets.append({
                        "type": "ethereum",
                        "address": eth_address,
                        "private_key": private_key,
                        "balance_wei": int(balance_eth * 10**18),
                        "balance_eth": balance_eth,
                        "timestamp": datetime.now().isoformat()
                    })
                else:
                    print(f"   ETH Balance: 0 ETH")
                    
            except Exception as e:
                print(f"   ETH Balance check failed: {str(e)}")
                
        # Check Bitcoin balance
        if btc_address:
            try:
                balance_result = balance_checker.check_bitcoin_balance_multiple_apis(btc_address)
                balance_btc = float(balance_result.get('balance_btc', 0))
                
                if balance_btc > 0:
                    print(f"🎉 FUNDED BITCOIN WALLET FOUND!")
                    print(f"   Address: {btc_address}")
                    print(f"   Balance: {balance_btc:.8f} BTC")
                    print(f"   Private Key: {private_key}")
                    
                    funded_wallets.append({
                        "type": "bitcoin",
                        "address": btc_address,
                        "private_key": private_key,
                        "balance_satoshis": int(balance_btc * 100000000),
                        "balance_btc": balance_btc,
                        "timestamp": datetime.now().isoformat()
                    })
                else:
                    print(f"   BTC Balance: 0 BTC")
                    
            except Exception as e:
                print(f"   BTC Balance check failed: {str(e)}")
        
        total_checked += 1
        
        # Rate limiting - pause every 10 requests
        if i % 10 == 9:
            print(f"   [Rate limiting: pausing for 2 seconds...]")
            time.sleep(2)
    
    return funded_wallets, total_checked

def main():
    """Main execution"""
    print("="*60)
    print("BATCH BALANCE CHECKER - [US]172.58.122.84 Dataset")
    print("="*60)
    
    # Load private keys
    private_keys = load_private_keys()
    print(f"\nLoaded {len(private_keys)} unique private keys")
    
    # Initialize balance checker
    balance_checker = EnhancedBalanceChecker()
    
    # Prepare wallet data
    addresses_data = []
    for private_key in private_keys:
        eth_address = derive_ethereum_address(private_key)
        btc_address = derive_bitcoin_address(private_key)
        
        addresses_data.append({
            "private_key": private_key,
            "ethereum_address": eth_address,
            "bitcoin_address": btc_address
        })
    
    print(f"Successfully derived addresses for {len(addresses_data)} wallets")
    
    # Check balances
    funded_wallets, total_checked = check_balances_batch(balance_checker, addresses_data)
    
    # Save results
    if funded_wallets:
        filename = f"FUNDED_WALLETS_172_58_122_84_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(funded_wallets, f, indent=2)
        
        print(f"\n🎉 SUCCESS! Found {len(funded_wallets)} funded wallets!")
        print(f"Results saved to: {filename}")
        
        for wallet in funded_wallets:
            if wallet['type'] == 'ethereum':
                print(f"\nETH Wallet: {wallet['address']}")
                print(f"Balance: {wallet['balance_eth']:.8f} ETH")
                print(f"Private Key: {wallet['private_key']}")
            elif wallet['type'] == 'bitcoin':
                print(f"\nBTC Wallet: {wallet['address']}")
                print(f"Balance: {wallet['balance_btc']:.8f} BTC")
                print(f"Private Key: {wallet['private_key']}")
    else:
        print(f"\nNo funded wallets found in {total_checked} checked addresses")
    
    # Create summary report
    report = {
        "dataset": "[US]172.58.122.84",
        "total_private_keys": len(private_keys),
        "total_checked": total_checked,
        "funded_wallets_found": len(funded_wallets),
        "funded_wallets": funded_wallets,
        "scan_timestamp": datetime.now().isoformat()
    }
    
    with open(f"scan_report_172_58_122_84_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n✅ Scan complete! Checked {total_checked} wallets from [US]172.58.122.84 dataset")

if __name__ == "__main__":
    main()
