#!/usr/bin/env python3

import json
import time
import requests
from datetime import datetime
from eth_keys import keys
from bit import PrivateKey
from api_manager import api_manager

def hex_to_ethereum_address(private_key_hex):
    """Convert hex private key to Ethereum address using eth-keys"""
    try:
        # Remove 0x prefix if present
        if private_key_hex.startswith('0x'):
            private_key_hex = private_key_hex[2:]
        
        # Create private key object
        private_key_bytes = bytes.fromhex(private_key_hex)
        private_key = keys.PrivateKey(private_key_bytes)
        
        # Get Ethereum address
        address = private_key.public_key.to_checksum_address()
        return address
        
    except Exception as e:
        return None

def hex_to_bitcoin_address(private_key_hex):
    """Convert hex private key to Bitcoin address using bit"""
    try:
        # Remove 0x prefix if present
        if private_key_hex.startswith('0x'):
            private_key_hex = private_key_hex[2:]
        
        # Create Bitcoin private key
        private_key_bytes = bytes.fromhex(private_key_hex)
        key = PrivateKey.from_bytes(private_key_bytes)
        
        # Get Bitcoin address
        return key.address
        
    except Exception as e:
        return None

def check_ethereum_balance_real(address):
    """Check real Ethereum balance using our APIs"""
    try:
        eth_apis = api_manager.get_ethereum_apis()
        
        if eth_apis.get('etherscan'):
            api_key = eth_apis['etherscan']
            url = f"https://api.etherscan.io/api"
            
            params = {
                'module': 'account',
                'action': 'balance',
                'address': address,
                'tag': 'latest',
                'apikey': api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == '1':
                    balance_wei = int(data.get('result', 0))
                    balance_eth = balance_wei / 10**18
                    return balance_eth
        
        return 0
        
    except Exception as e:
        return 0

def check_bitcoin_balance_real(address):
    """Check real Bitcoin balance using our APIs"""
    try:
        btc_apis = api_manager.get_bitcoin_apis()
        
        # Try BlockStream API (no key required)
        try:
            url = f"https://blockstream.info/api/address/{address}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                balance_sat = data.get('chain_stats', {}).get('funded_txo_sum', 0) - \
                            data.get('chain_stats', {}).get('spent_txo_sum', 0)
                balance_btc = balance_sat / 100000000  # Convert satoshis to BTC
                return balance_btc
                
        except:
            pass
        
        return 0
        
    except Exception as e:
        return 0

def check_metamask_priority_keys():
    """Check the priority MetaMask keys for balances"""
    
    print("🔥 METAMASK PRIORITY KEY CHECKER")
    print("="*60)
    
    # Load priority keys
    try:
        with open('PRIORITY_CHECKING_LIST.json', 'r') as f:
            data = json.load(f)
        
        priority_keys = data['keys']
        print(f"🎯 Loaded {len(priority_keys)} priority keys from MetaMask logs")
        
    except FileNotFoundError:
        print("❌ PRIORITY_CHECKING_LIST.json not found!")
        print("   Run extract_richest_sources.py first")
        return
    
    funded_wallets = []
    checked_count = 0
    start_time = time.time()
    
    # Check first 100 keys thoroughly
    test_keys = priority_keys[:100]
    
    print(f"🔍 Checking first {len(test_keys)} priority keys...")
    print(f"⏱️  Estimated time: {len(test_keys) * 3 / 60:.1f} minutes")
    
    for i, key_data in enumerate(test_keys, 1):
        private_key = key_data['private_key']
        source_file = key_data['source_file']
        
        print(f"\n🔍 [{i}/{len(test_keys)}] {source_file}: {private_key[:12]}...")
        
        try:
            # Convert to Ethereum address
            eth_address = hex_to_ethereum_address(private_key)
            if eth_address:
                print(f"    📍 ETH: {eth_address}")
                
                # Check Ethereum balance
                eth_balance = check_ethereum_balance_real(eth_address)
                if eth_balance > 0:
                    print(f"    💰 ETH BALANCE: {eth_balance:.8f} ETH")
                    
                    funded_wallets.append({
                        'index': i,
                        'private_key': private_key,
                        'source_file': source_file,
                        'eth_address': eth_address,
                        'eth_balance': eth_balance,
                        'btc_address': None,
                        'btc_balance': 0,
                        'total_usd': eth_balance * 2600,  # Rough ETH price
                        'discovery_time': datetime.now().isoformat()
                    })
                    
                    print(f"    🚨 FUNDED WALLET FOUND! ${eth_balance * 2600:.2f}")
                    continue
            
            # Convert to Bitcoin address
            btc_address = hex_to_bitcoin_address(private_key)
            if btc_address:
                print(f"    📍 BTC: {btc_address}")
                
                # Check Bitcoin balance
                btc_balance = check_bitcoin_balance_real(btc_address)
                if btc_balance > 0:
                    print(f"    💰 BTC BALANCE: {btc_balance:.8f} BTC")
                    
                    funded_wallets.append({
                        'index': i,
                        'private_key': private_key,
                        'source_file': source_file,
                        'eth_address': eth_address,
                        'eth_balance': 0,
                        'btc_address': btc_address,
                        'btc_balance': btc_balance,
                        'total_usd': btc_balance * 35000,  # Rough BTC price
                        'discovery_time': datetime.now().isoformat()
                    })
                    
                    print(f"    🚨 FUNDED WALLET FOUND! ${btc_balance * 35000:.2f}")
                    continue
            
            print(f"    ✓ Empty")
            
        except Exception as e:
            print(f"    ❌ Error: {str(e)}")
        
        checked_count += 1
        
        # Progress update
        if i % 10 == 0:
            elapsed = time.time() - start_time
            rate = i / elapsed if elapsed > 0 else 0
            print(f"\n📊 Progress: {i}/{len(test_keys)} ({i/len(test_keys)*100:.1f}%)")
            print(f"    Rate: {rate:.1f} keys/sec")
            print(f"    Funded: {len(funded_wallets)} wallets")
        
        # Rate limiting
        time.sleep(3)  # 3 seconds between checks
    
    elapsed = time.time() - start_time
    
    print(f"\n" + "="*60)
    print(f"🏁 PRIORITY METAMASK CHECK COMPLETE")
    print(f"   ⏱️  Time: {elapsed/60:.1f} minutes")
    print(f"   🔍 Checked: {checked_count} priority keys")
    print(f"   💰 Funded: {len(funded_wallets)} wallets")
    
    if funded_wallets:
        # Save results
        results = {
            'check_date': datetime.now().isoformat(),
            'source': 'MetaMask_Priority_Logs',
            'keys_checked': checked_count,
            'funded_count': len(funded_wallets),
            'funded_wallets': funded_wallets
        }
        
        with open('METAMASK_FUNDED_WALLETS.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n🎉 FUNDED METAMASK WALLETS:")
        total_value = 0
        for wallet in funded_wallets:
            crypto = "ETH" if wallet['eth_balance'] > 0 else "BTC"
            balance = wallet['eth_balance'] if wallet['eth_balance'] > 0 else wallet['btc_balance']
            print(f"   #{wallet['index']} ({wallet['source_file']}): {balance:.8f} {crypto} (${wallet['total_usd']:.2f})")
            total_value += wallet['total_usd']
        
        print(f"\n💎 TOTAL VALUE: ${total_value:.2f}")
        print(f"💾 Results: METAMASK_FUNDED_WALLETS.json")
        print(f"🚨 SECURE THESE PRIVATE KEYS IMMEDIATELY!")
        
        # Show recovery instructions
        print(f"\n🛡️  RECOVERY INSTRUCTIONS:")
        for wallet in funded_wallets:
            print(f"   Key: {wallet['private_key']}")
            if wallet['eth_balance'] > 0:
                print(f"   Import to MetaMask/MyEtherWallet for ETH access")
            if wallet['btc_balance'] > 0:
                print(f"   Import to Electrum/Bitcoin Core for BTC access")
        
    else:
        print(f"\n💡 No funded wallets in first 100 MetaMask keys")
        print(f"   📊 {len(priority_keys) - 100} priority keys remaining")
        print(f"   🎯 Continue with next batch or expand search")

if __name__ == "__main__":
    check_metamask_priority_keys()
