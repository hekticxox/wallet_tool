#!/usr/bin/env python3
"""
Extract and Check Private Keys from net599 Dataset
This massive 143GB dataset contains 62,600+ addresses including real wallet data
"""

import json
import time
import os
from datetime import datetime
from enhanced_balance_checker import EnhancedBalanceChecker
from eth_keys import keys
from bit import Key

def extract_private_keys_from_scan():
    """Extract all unique private keys from the comprehensive scan results"""
    print("Loading comprehensive scan results...")
    
    with open('/home/admin/wallet_tool/comprehensive_scan_results.json', 'r') as f:
        scan_data = json.load(f)
    
    print(f"Found {scan_data['scan_summary']['private_keys_found']} private keys in scan")
    
    all_keys = set()
    
    # Extract from private_keys_found section
    if 'private_keys_found' in scan_data:
        for key_entry in scan_data['private_keys_found']:
            file_path = key_entry.get('file_path', '')
            
            # Skip if it's from a cache file (might be already checked addresses)
            if 'cache' in file_path.lower():
                continue
                
            # Try to extract the full key from preview
            key_preview = key_entry.get('key_preview', '')
            if '...' in key_preview:
                # This is a preview, need to get the full key from the file
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    # Find 64-character hex strings
                    import re
                    hex_keys = re.findall(r'[0-9a-fA-F]{64}', content)
                    for key in hex_keys:
                        if len(key) == 64:
                            all_keys.add(key.lower())
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")
                    continue
            else:
                # Full key in preview
                if len(key_preview) == 64:
                    all_keys.add(key_preview.lower())
    
    unique_keys = list(all_keys)
    print(f"Extracted {len(unique_keys)} unique private keys")
    
    return unique_keys

def main():
    print("="*70)
    print("NET599 MASSIVE DATASET PRIVATE KEY CHECKER")
    print("143GB of wallet data - 62,600+ addresses found")
    print("="*70)
    
    # Extract private keys
    private_keys = extract_private_keys_from_scan()
    
    if not private_keys:
        print("❌ No private keys extracted. Let me try a different approach...")
        return
    
    print(f"\n🚀 Starting balance check for {len(private_keys)} private keys...")
    print(f"   This could take a while - checking for REAL funded wallets!")
    
    balance_checker = EnhancedBalanceChecker()
    funded_wallets = []
    total_checked = 0
    start_time = datetime.now()
    
    for i, private_key in enumerate(private_keys):
        print(f"\n[{i+1}/{len(private_keys)}] {private_key[:10]}...{private_key[-10:]}")
        
        # Derive addresses
        try:
            # Ethereum
            private_key_bytes = bytes.fromhex(private_key)
            eth_private_key = keys.PrivateKey(private_key_bytes)
            eth_address = eth_private_key.public_key.to_checksum_address()
            
            # Bitcoin
            btc_key = Key.from_hex(private_key)
            btc_address = btc_key.address
            
            print(f"ETH: {eth_address}")
            print(f"BTC: {btc_address}")
            
        except Exception as e:
            print(f"Address derivation failed: {e}")
            continue
        
        # Check Ethereum balance
        try:
            eth_result = balance_checker.check_ethereum_balance_multiple_apis(eth_address)
            eth_balance = float(eth_result.get('balance_eth', 0))
            
            if eth_balance > 0:
                print(f"🎉🎉🎉 FUNDED ETHEREUM WALLET! 🎉🎉🎉")
                print(f"💰 Balance: {eth_balance:.8f} ETH")
                print(f"🔑 Private Key: {private_key}")
                
                funded_wallets.append({
                    "type": "ethereum",
                    "address": eth_address,
                    "private_key": private_key,
                    "balance_eth": eth_balance,
                    "dataset": "net599",
                    "timestamp": datetime.now().isoformat()
                })
                
                # IMMEDIATE SAVE for funded wallets
                with open(f"URGENT_FUNDED_WALLET_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", 'w') as f:
                    json.dump(funded_wallets, f, indent=2)
            else:
                print(f"ETH: 0")
                
        except Exception as e:
            print(f"ETH check failed: {e}")
        
        # Check Bitcoin balance
        try:
            btc_result = balance_checker.check_bitcoin_balance_multiple_apis(btc_address)
            btc_balance = float(btc_result.get('balance_btc', 0))
            
            if btc_balance > 0:
                print(f"🎉🎉🎉 FUNDED BITCOIN WALLET! 🎉🎉🎉")
                print(f"💰 Balance: {btc_balance:.8f} BTC")
                print(f"🔑 Private Key: {private_key}")
                
                funded_wallets.append({
                    "type": "bitcoin",
                    "address": btc_address,
                    "private_key": private_key,
                    "balance_btc": btc_balance,
                    "dataset": "net599",
                    "timestamp": datetime.now().isoformat()
                })
                
                # IMMEDIATE SAVE for funded wallets
                with open(f"URGENT_FUNDED_WALLET_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", 'w') as f:
                    json.dump(funded_wallets, f, indent=2)
            else:
                print(f"BTC: 0")
                
        except Exception as e:
            print(f"BTC check failed: {e}")
        
        total_checked += 1
        
        # Progress reporting every 10 wallets
        if (i + 1) % 10 == 0:
            elapsed = datetime.now() - start_time
            rate = total_checked / elapsed.total_seconds() if elapsed.total_seconds() > 0 else 0
            remaining = len(private_keys) - total_checked
            eta_minutes = (remaining / rate / 60) if rate > 0 else 0
            
            print(f"\n📊 Progress: {total_checked}/{len(private_keys)} ({(total_checked/len(private_keys)*100):.1f}%)")
            print(f"   Funded found: {len(funded_wallets)}")
            print(f"   Rate: {rate:.1f}/sec | ETA: {eta_minutes:.1f} minutes")
        
        # Rate limiting
        time.sleep(1)  # Be nice to APIs
    
    # Final results
    print(f"\n{'='*70}")
    print(f"NET599 SCAN COMPLETE!")
    print(f"{'='*70}")
    
    if funded_wallets:
        print(f"🎉🎉🎉 JACKPOT! Found {len(funded_wallets)} funded wallets! 🎉🎉🎉")
        
        final_filename = f"NET599_FUNDED_WALLETS_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(final_filename, 'w') as f:
            json.dump(funded_wallets, f, indent=2)
        
        total_value = 0
        for wallet in funded_wallets:
            if wallet['type'] == 'ethereum':
                print(f"\n💎 ETH WALLET: {wallet['address']}")
                print(f"   💰 {wallet['balance_eth']:.8f} ETH")
                print(f"   🔑 {wallet['private_key']}")
            elif wallet['type'] == 'bitcoin':
                print(f"\n💎 BTC WALLET: {wallet['address']}")
                print(f"   💰 {wallet['balance_btc']:.8f} BTC")
                print(f"   🔑 {wallet['private_key']}")
        
        print(f"\n🎯 Results saved to: {final_filename}")
    else:
        print(f"No funded wallets found in {total_checked} checked keys from net599")
    
    print(f"\n✅ net599 dataset check complete!")

if __name__ == "__main__":
    main()
