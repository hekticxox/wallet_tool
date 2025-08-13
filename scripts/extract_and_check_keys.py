#!/usr/bin/env python3
"""
Extract and check the full private keys from the discovered Chrome Profile 2 files
"""

import json
import re
import os
from enhanced_balance_checker import EnhancedBalanceChecker
from eth_keys import keys as eth_keys
from bit import PrivateKeyTestnet, PrivateKey

def extract_private_keys_from_file(file_path):
    """Extract private keys from a file"""
    private_keys = []
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Enhanced pattern for hex private keys (64 hex characters)
        hex_patterns = [
            r'\b[0-9a-fA-F]{64}\b',  # Exactly 64 hex characters
            r'0x[0-9a-fA-F]{64}',    # With 0x prefix
        ]
        
        for pattern in hex_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                # Remove 0x prefix if present
                clean_key = match.replace('0x', '').lower()
                if len(clean_key) == 64:
                    private_keys.append(clean_key)
        
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
    
    return private_keys

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
    """Extract and check private keys from discovered files"""
    
    print("🔍 EXTRACTING AND CHECKING PRIVATE KEYS")
    print("=" * 60)
    
    # Files that were found to contain private keys
    target_files = [
        "/home/admin/Downloads/[CA]50.92.164.97/[CA]50.92.164.97/Chrome/Profile 2/Cookies.txt",
        "/home/admin/Downloads/[CA]50.92.164.97/[CA]50.92.164.97/Cookies/Cookies_Chrome_Profile 2.txt"
    ]
    
    # Initialize balance checker
    checker = EnhancedBalanceChecker()
    
    # Extract all private keys
    all_private_keys = []
    for file_path in target_files:
        if os.path.exists(file_path):
            print(f"📄 Extracting from: {os.path.basename(file_path)}")
            keys = extract_private_keys_from_file(file_path)
            all_private_keys.extend(keys)
            print(f"   Found {len(keys)} potential private keys")
        else:
            print(f"❌ File not found: {file_path}")
    
    # Remove duplicates
    unique_keys = list(set(all_private_keys))
    print(f"\n🔑 Total unique private keys found: {len(unique_keys)}")
    
    if not unique_keys:
        print("❌ No private keys found")
        return
    
    # Check each key
    funded_wallets = []
    for i, private_key in enumerate(unique_keys, 1):
        print(f"\nChecking key {i}/{len(unique_keys)}: {private_key[:8]}...{private_key[-8:]}")
        
        # Convert private key to Bitcoin address
        btc_address = private_key_to_bitcoin_address(private_key)
        if btc_address:
            print(f"   📍 BTC Address: {btc_address}")
            btc_result = checker.check_bitcoin_balance_multiple_apis(btc_address)
            if btc_result.get('success') and btc_result.get('balance_btc', 0) > 0:
                funded_wallets.append({
                    'private_key': private_key,
                    'currency': 'BTC',
                    'address': btc_address,
                    'balance': btc_result['balance_btc']
                })
                print(f"   💰 FUNDED BTC WALLET!")
                print(f"       Balance: {btc_result['balance_btc']} BTC")
            else:
                print(f"   ❌ BTC: No balance")
        else:
            print(f"   ❌ Could not derive BTC address")
        
        # Convert private key to Ethereum address
        eth_address = private_key_to_ethereum_address(private_key)
        if eth_address:
            print(f"   📍 ETH Address: {eth_address}")
            eth_result = checker.check_ethereum_balance_multiple_apis(eth_address)
            if eth_result.get('success') and eth_result.get('balance_eth', 0) > 0:
                funded_wallets.append({
                    'private_key': private_key,
                    'currency': 'ETH',
                    'address': eth_address,
                    'balance': eth_result['balance_eth']
                })
                print(f"   💰 FUNDED ETH WALLET!")
                print(f"       Balance: {eth_result['balance_eth']} ETH")
            else:
                print(f"   ❌ ETH: No balance")
        else:
            print(f"   ❌ Could not derive ETH address")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 FINAL SUMMARY")
    print(f"🔑 Private keys checked: {len(unique_keys)}")
    print(f"💰 Funded wallets found: {len(funded_wallets)}")
    
    if funded_wallets:
        print("\n🎉 FUNDED WALLETS DISCOVERED:")
        for wallet in funded_wallets:
            print(f"\n   💰 {wallet['currency']} WALLET:")
            print(f"      Address: {wallet['address']}")
            print(f"      Balance: {wallet['balance']} {wallet['currency']}")
            print(f"      Private Key: {wallet['private_key']}")
        
        # Save results
        with open('discovered_funded_wallets.json', 'w') as f:
            json.dump(funded_wallets, f, indent=2)
        print(f"\n💾 Full results saved to discovered_funded_wallets.json")
        
        # Also create a secure backup with just the essential info
        secure_backup = []
        for wallet in funded_wallets:
            secure_backup.append({
                'currency': wallet['currency'],
                'address': wallet['address'],
                'balance': wallet['balance'],
                'private_key_preview': wallet['private_key'][:8] + '...' + wallet['private_key'][-8:]
            })
        
        with open('funded_wallets_summary.json', 'w') as f:
            json.dump(secure_backup, f, indent=2)
        print("🔐 Secure summary saved to funded_wallets_summary.json")
        
    else:
        print("\n❌ No funded wallets found")
    
    # Also check the standalone Bitcoin address
    print(f"\n🔍 Checking standalone Bitcoin address...")
    btc_address = "3AXwj1tZqoRA2xpxHNAkShbNwZtxtwYbwY"
    print(f"   📍 Address: {btc_address}")
    btc_result = checker.check_bitcoin_balance_multiple_apis(btc_address)
    if btc_result.get('success') and btc_result.get('balance_btc', 0) > 0:
        print(f"   💰 FUNDED ADDRESS FOUND!")
        print(f"       Balance: {btc_result['balance_btc']} BTC")
        print("   ⚠️  WARNING: This address was found standalone (no private key)")
    else:
        print(f"   ❌ No balance")

if __name__ == "__main__":
    main()
