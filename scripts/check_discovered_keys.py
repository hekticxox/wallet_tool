#!/usr/bin/env python3
"""
Check balances for the newly discovered private keys from the Chrome Profile 2 directory
"""

import json
import os
from enhanced_balance_checker import EnhancedBalanceChecker
from eth_keys import keys as eth_keys
from bit import PrivateKeyTestnet, PrivateKey

def private_key_to_bitcoin_address(private_key_hex: str) -> str:
    """Convert private key to Bitcoin address"""
    try:
        # Try mainnet first
        key = PrivateKey(private_key_hex)
        return key.address
    except:
        try:
            # Try testnet
            key = PrivateKeyTestnet(private_key_hex)
            return key.address
        except:
            return None

def private_key_to_ethereum_address(private_key_hex: str) -> str:
    """Convert private key to Ethereum address"""
    try:
        private_key = eth_keys.PrivateKey(bytes.fromhex(private_key_hex.replace('0x', '')))
        return private_key.public_key.to_checksum_address()
    except:
        return None

def main():
    """Check balances for discovered private keys"""
    
    print("🔍 CHECKING DISCOVERED PRIVATE KEYS")
    print("=" * 60)
    
    # Load the scan results to get discovered keys
    try:
        with open('comprehensive_scan_results.json', 'r') as f:
            scan_results = json.load(f)
    except FileNotFoundError:
        print("❌ comprehensive_scan_results.json not found. Please run comprehensive_wallet_scanner.py first.")
        return
    
    # Initialize balance checker
    checker = EnhancedBalanceChecker()
    
    # Extract unique private keys (remove duplicates)
    private_keys = []
    seen_keys = set()
    
    for key_info in scan_results.get('private_keys', []):
        full_key = key_info.get('full_key')
        if full_key and full_key not in seen_keys:
            private_keys.append(full_key)
            seen_keys.add(full_key)
    
    print(f"🔑 Found {len(private_keys)} unique private keys to check")
    print()
    
    # Check each key
    funded_wallets = []
    for i, private_key in enumerate(private_keys, 1):
        print(f"Checking key {i}/{len(private_keys)}: {private_key[:8]}...{private_key[-8:]}")
        
        # Convert private key to Bitcoin address
        btc_address = private_key_to_bitcoin_address(private_key)
        if btc_address:
            btc_result = checker.check_bitcoin_balance_multiple_apis(btc_address)
            if btc_result.get('success') and btc_result.get('balance_btc', 0) > 0:
                funded_wallets.append({
                    'private_key': private_key,
                    'currency': 'BTC',
                    'address': btc_address,
                    'balance': btc_result['balance_btc']
                })
                print(f"💰 FUNDED BTC WALLET: {btc_address}")
                print(f"    Balance: {btc_result['balance_btc']} BTC")
        
        # Convert private key to Ethereum address
        eth_address = private_key_to_ethereum_address(private_key)
        if eth_address:
            eth_result = checker.check_ethereum_balance_multiple_apis(eth_address)
            if eth_result.get('success') and eth_result.get('balance_eth', 0) > 0:
                funded_wallets.append({
                    'private_key': private_key,
                    'currency': 'ETH',
                    'address': eth_address,
                    'balance': eth_result['balance_eth']
                })
                print(f"💰 FUNDED ETH WALLET: {eth_address}")
                print(f"    Balance: {eth_result['balance_eth']} ETH")
        
        if not (btc_address or eth_address):
            print(f"    ❌ Unable to derive addresses from private key")
        elif not any([
            btc_result.get('success') and btc_result.get('balance_btc', 0) > 0 if btc_address else False,
            eth_result.get('success') and eth_result.get('balance_eth', 0) > 0 if eth_address else False
        ]):
            print(f"    ❌ No balance found")
        
        print()
    
    # Summary
    print("=" * 60)
    print("📊 SUMMARY")
    print(f"🔑 Keys checked: {len(private_keys)}")
    print(f"💰 Funded wallets: {len(funded_wallets)}")
    
    if funded_wallets:
        print("\n🎉 FUNDED WALLETS FOUND:")
        for wallet in funded_wallets:
            print(f"   {wallet['currency']}: {wallet['address']}")
            print(f"   Balance: {wallet['balance']} {wallet['currency']}")
            print(f"   Private Key: {wallet['private_key'][:8]}...{wallet['private_key'][-8:]}")
            print()
        
        # Save results
        with open('discovered_funded_wallets.json', 'w') as f:
            json.dump(funded_wallets, f, indent=2)
        print("💾 Results saved to discovered_funded_wallets.json")
    else:
        print("❌ No funded wallets found")
    
    # Also check the discovered Bitcoin address
    discovered_addresses = scan_results.get('addresses', [])
    if discovered_addresses:
        print(f"\n🔍 Checking {len(discovered_addresses)} discovered addresses...")
        for addr_info in discovered_addresses:
            address = addr_info.get('address')
            if address:
                print(f"Checking {address}...")
                # This is a Bitcoin address, check Bitcoin balance
                btc_result = checker.check_bitcoin_balance_multiple_apis(address)
                if btc_result.get('success') and btc_result.get('balance_btc', 0) > 0:
                    print(f"💰 FUNDED ADDRESS: {address}")
                    print(f"    Balance: {btc_result['balance_btc']} BTC")
                    print("    ⚠️  WARNING: This is an address without a private key!")
                else:
                    print(f"    ❌ No balance")

if __name__ == "__main__":
    main()
