#!/usr/bin/env python3
"""
Targeted Balance Checker - Only checks addresses with known private keys
- Focuses on addresses you can actually control
- Rate-limit safe with smart delays and multiple API fallbacks
- Shows private key for each funded address found
- Tracks checking history to avoid duplicate work
- Multiple API sources with automatic failover
"""

import json
import time
import random
import requests
import sys
import os
from typing import Dict, List, Optional, Set

def load_checking_history() -> Dict[str, Set[str]]:
    """Load history of already checked addresses to avoid duplicates"""
    history_file = "checked_addresses_history.json"
    if not os.path.exists(history_file):
        return {'ethereum': set(), 'bitcoin': set(), 'solana': set()}
    
    try:
        with open(history_file, 'r') as f:
            data = json.load(f)
        
        # Convert lists back to sets for fast lookup
        return {
            'ethereum': set(data.get('ethereum', [])),
            'bitcoin': set(data.get('bitcoin', [])),  
            'solana': set(data.get('solana', []))
        }
    except Exception as e:
        print(f"⚠️  Warning: Could not load checking history: {e}")
        return {'ethereum': set(), 'bitcoin': set(), 'solana': set()}

def save_checking_history(history: Dict[str, Set[str]]):
    """Save history of checked addresses"""
    history_file = "checked_addresses_history.json"
    try:
        # Convert sets to lists for JSON serialization
        data = {
            'ethereum': list(history['ethereum']),
            'bitcoin': list(history['bitcoin']),
            'solana': list(history['solana'])
        }
        
        with open(history_file, 'w') as f:
            json.dump(data, f, indent=2)
            
    except Exception as e:
        print(f"⚠️  Warning: Could not save checking history: {e}")

def load_key_address_mappings(wallet_file: str) -> Dict:
    """Load and organize private key to address mappings"""
    try:
        with open(wallet_file, 'r') as f:
            data = json.load(f)
        
        # Organize by blockchain for easy access
        mappings = {
            'ethereum': [],
            'bitcoin': [],
            'solana': []
        }
        
        # Process cross-check results to get private key -> address mappings
        if 'cross_check_results' in data:
            for result in data['cross_check_results']:
                if result.get('matched', False):  # Only include matched keys
                    chain = result.get('chain')
                    if chain in mappings:
                        mappings[chain].append({
                            'private_key': result['private_key'],
                            'address': result['address']
                        })
        
        # Remove duplicates while preserving order
        for chain in mappings:
            seen = set()
            unique_mappings = []
            for item in mappings[chain]:
                key = (item['private_key'], item['address'])
                if key not in seen:
                    seen.add(key)
                    unique_mappings.append(item)
            mappings[chain] = unique_mappings
        
        return mappings
    
    except Exception as e:
        print(f"❌ Error loading wallet data: {e}")
        return {}

def check_ethereum_balance(session: requests.Session, address: str, private_key: str) -> Optional[Dict]:
    """Check ETH balance using multiple API providers with fallback"""
    
    # Multiple free API sources for ETH
    apis = [
        {
            'name': 'Etherscan',
            'url': f"https://api.etherscan.io/api?module=account&action=balance&address={address}&tag=latest&apikey=YourApiKeyToken",
            'delay': random.uniform(2, 4),
            'parse_func': lambda r: {
                'balance_wei': r.get('result', '0') if r.get('status') == '1' and r.get('result', '').isdigit() else '0', 
                'source': 'etherscan'
            }
        },
        {
            'name': 'Alchemy',  
            'url': f"https://eth-mainnet.g.alchemy.com/v2/demo",
            'delay': random.uniform(3, 5),
            'is_json_rpc': True,
            'payload': {
                "jsonrpc": "2.0",
                "method": "eth_getBalance", 
                "params": [address, "latest"],
                "id": 1
            },
            'parse_func': lambda r: {'balance_wei': str(int(r.get('result', '0x0'), 16)), 'source': 'alchemy'}
        },
        {
            'name': 'Blockchair',
            'url': f"https://api.blockchair.com/ethereum/dashboards/address/{address}",
            'delay': random.uniform(8, 12),
            'parse_func': lambda r: {'balance_wei': r.get('data', {}).get(address, {}).get('address', {}).get('balance', '0'), 'source': 'blockchair'}
        },
        {
            'name': 'CloudFlare',
            'url': "https://cloudflare-eth.com",
            'delay': random.uniform(2, 3),
            'is_json_rpc': True,
            'payload': {
                "jsonrpc": "2.0",
                "method": "eth_getBalance",
                "params": [address, "latest"], 
                "id": 1
            },
            'parse_func': lambda r: {'balance_wei': str(int(r.get('result', '0x0'), 16)), 'source': 'cloudflare'}
        }
    ]
    
    for api in apis:
        try:
            print(f"⏳ {api['name']} waiting {api['delay']:.1f}s...", end=' ')
            time.sleep(api['delay'])
            
            if api.get('is_json_rpc'):
                response = session.post(api['url'], json=api['payload'], timeout=30)
            else:
                response = session.get(api['url'], timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                # Handle error responses
                if 'error' in data:
                    print(f"❌ API Error")
                    continue
                    
                parsed = api['parse_func'](data)
                balance_wei = parsed['balance_wei']
                
                if balance_wei and balance_wei != '0':
                    balance_eth = float(balance_wei) / 1e18
                    print(f"💰 {balance_eth:.6f} ETH ({parsed['source']})")
                    
                    return {
                        'address': address,
                        'private_key': private_key,
                        'balance_wei': balance_wei,
                        'balance_eth': balance_eth,
                        'has_balance': balance_eth > 0,
                        'blockchain': 'ethereum',
                        'api_source': parsed['source']
                    }
                else:
                    print(f"💸 0 ETH ({parsed['source']})")
                    return {
                        'address': address,
                        'private_key': private_key,
                        'balance_wei': '0',
                        'balance_eth': 0.0,
                        'has_balance': False,
                        'blockchain': 'ethereum',
                        'api_source': parsed['source']
                    }
                    
            elif response.status_code == 429 or response.status_code == 430:
                print(f"⚠️  Rate limited, trying next API...")
                continue
            else:
                print(f"❌ HTTP {response.status_code}")
                continue
                
        except Exception as e:
            print(f"❌ {str(e)[:20]}")
            continue
    
    print("❌ All ETH APIs failed")
    return None

def check_bitcoin_balance(session: requests.Session, address: str, private_key: str) -> Optional[Dict]:
    """Check BTC balance using multiple API providers with fallback"""
    
    # Multiple free API sources for BTC
    apis = [
        {
            'name': 'Blockstream',
            'url': f"https://blockstream.info/api/address/{address}",
            'delay': random.uniform(2, 4),
            'parse_func': lambda r: {
                'balance_sat': r.get('chain_stats', {}).get('funded_txo_sum', 0) - r.get('chain_stats', {}).get('spent_txo_sum', 0),
                'source': 'blockstream'
            }
        },
        {
            'name': 'BlockCypher',
            'url': f"https://api.blockcypher.com/v1/btc/main/addrs/{address}/balance",
            'delay': random.uniform(3, 5),
            'parse_func': lambda r: {'balance_sat': r.get('balance', 0), 'source': 'blockcypher'}
        },
        {
            'name': 'Blockchain.info',
            'url': f"https://blockchain.info/rawaddr/{address}",
            'delay': random.uniform(4, 6),
            'parse_func': lambda r: {'balance_sat': r.get('final_balance', 0), 'source': 'blockchain_info'}
        },
        {
            'name': 'Blockchair',
            'url': f"https://api.blockchair.com/bitcoin/dashboards/address/{address}",
            'delay': random.uniform(6, 8),
            'parse_func': lambda r: {
                'balance_sat': r.get('data', {}).get(address, {}).get('address', {}).get('balance', 0),
                'source': 'blockchair'
            }
        }
    ]
    
    for api in apis:
        try:
            print(f"⏳ {api['name']} waiting {api['delay']:.1f}s...", end=' ')
            time.sleep(api['delay'])
            
            response = session.get(api['url'], timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                parsed = api['parse_func'](data)
                balance_sat = parsed['balance_sat']
                balance_btc = balance_sat / 1e8
                
                if balance_btc > 0:
                    print(f"💰 {balance_btc:.8f} BTC ({parsed['source']})")
                else:
                    print(f"💸 0 BTC ({parsed['source']})")
                
                return {
                    'address': address,
                    'private_key': private_key,
                    'balance_sat': balance_sat,
                    'balance_btc': balance_btc,
                    'has_balance': balance_btc > 0,
                    'blockchain': 'bitcoin',
                    'api_source': parsed['source']
                }
                    
            elif response.status_code == 429 or response.status_code == 430:
                print(f"⚠️  Rate limited, trying next API...")
                continue
            else:
                print(f"❌ HTTP {response.status_code}")
                continue
                
        except Exception as e:
            print(f"❌ {str(e)[:20]}")
            continue
    
    print("❌ All BTC APIs failed")
    return None

def check_solana_balance(session: requests.Session, address: str, private_key: str) -> Optional[Dict]:
    """Check SOL balance using multiple RPC providers with fallback"""
    
    # Multiple free Solana RPC endpoints
    rpcs = [
        {
            'name': 'Solana Official',
            'url': "https://api.mainnet-beta.solana.com",
            'delay': random.uniform(1, 2)
        },
        {
            'name': 'Ankr',
            'url': "https://rpc.ankr.com/solana",
            'delay': random.uniform(1.5, 2.5)
        },
        {
            'name': 'GetBlock',
            'url': "https://go.getblock.io/solana",
            'delay': random.uniform(2, 3)
        },
        {
            'name': 'Quicknode',
            'url': "https://solana-mainnet.g.quicknode.com/free",
            'delay': random.uniform(2, 4)
        }
    ]
    
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getBalance",
        "params": [address]
    }
    
    for rpc in rpcs:
        try:
            print(f"⏳ {rpc['name']} waiting {rpc['delay']:.1f}s...", end=' ')
            time.sleep(rpc['delay'])
            
            response = session.post(rpc['url'], json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'error' in data:
                    print(f"❌ RPC Error")
                    continue
                    
                if 'result' in data and 'value' in data['result']:
                    balance_lamports = data['result']['value']
                    balance_sol = balance_lamports / 1e9
                    
                    if balance_sol > 0:
                        print(f"💰 {balance_sol:.6f} SOL ({rpc['name']})")
                    else:
                        print(f"💸 0 SOL ({rpc['name']})")
                    
                    return {
                        'address': address,
                        'private_key': private_key,
                        'balance_lamports': balance_lamports,
                        'balance_sol': balance_sol,
                        'has_balance': balance_sol > 0,
                        'blockchain': 'solana',
                        'api_source': rpc['name'].lower().replace(' ', '_')
                    }
                else:
                    print(f"❌ Invalid response")
                    continue
                    
            elif response.status_code == 429:
                print(f"⚠️  Rate limited, trying next RPC...")
                continue
            else:
                print(f"❌ HTTP {response.status_code}")
                continue
                
        except Exception as e:
            print(f"❌ {str(e)[:20]}")
            continue
    
    print("❌ All SOL RPCs failed")
    return None

def check_controlled_addresses(wallet_file: str, max_per_blockchain: int = 25):
    """Check balances only for addresses with known private keys"""
    
    print("🔑 Targeted Balance Checker - Only Controlled Addresses")
    print("=" * 60)
    
    # Load checking history to avoid duplicates
    print("📚 Loading checking history...")
    checking_history = load_checking_history()
    
    # Load mappings
    mappings = load_key_address_mappings(wallet_file)
    if not mappings:
        return
    
    # Filter out already checked addresses
    print("🔍 Filtering out previously checked addresses...")
    original_counts = {}
    for chain in mappings:
        original_counts[chain] = len(mappings[chain])
        mappings[chain] = [
            item for item in mappings[chain] 
            if item['address'] not in checking_history[chain]
        ]
    
    # Show what we found
    total_controlled = sum(len(mappings[chain]) for chain in mappings)
    total_original = sum(original_counts.values())
    total_already_checked = total_original - total_controlled
    
    print(f"🎯 Address Status Summary:")
    print(f"   • Total controlled addresses: {total_original}")
    print(f"   • Already checked previously: {total_already_checked}")
    print(f"   • New addresses to check: {total_controlled}")
    
    for chain in mappings:
        original = original_counts[chain]
        remaining = len(mappings[chain])
        already_checked = original - remaining
        if original > 0:
            print(f"   • {chain.upper()}: {remaining} new ({already_checked} already checked)")
    
    if total_controlled == 0:
        print("✅ All controlled addresses have already been checked!")
        print("🔍 Check previous results in FUNDED_CONTROLLED_ADDRESSES_*.json files")
        return
    
    # Set up session
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
    })
    
    results = {'checked': 0, 'funded': [], 'errors': 0}
    
    # Check each blockchain
    for blockchain in ['ethereum', 'bitcoin', 'solana']:
        addresses_with_keys = mappings[blockchain]
        if not addresses_with_keys:
            continue
        
        # Limit sample size
        sample = addresses_with_keys[:max_per_blockchain]
        print(f"\n🔸 Checking {len(sample)} NEW {blockchain.upper()} addresses...")
        
        for i, addr_data in enumerate(sample, 1):
            address = addr_data['address']
            private_key = addr_data['private_key']
            
            print(f"   {i:2d}/{len(sample)} {blockchain[:3].upper()} {address[:12]}... ", end='')
            
            if blockchain == 'ethereum':
                result = check_ethereum_balance(session, address, private_key)
            elif blockchain == 'bitcoin':
                result = check_bitcoin_balance(session, address, private_key)
            elif blockchain == 'solana':
                result = check_solana_balance(session, address, private_key)
            else:
                continue
            
            # Add to checking history regardless of result
            checking_history[blockchain].add(address)
            
            if result:
                results['checked'] += 1
                if result['has_balance']:
                    results['funded'].append(result)
                # Balance is already printed by the API checking functions
            else:
                results['errors'] += 1
    
    # Save updated checking history
    print(f"\n💾 Saving checking history...")
    save_checking_history(checking_history)
    
    # Final summary
    print("\n" + "=" * 60)
    print("📊 CONTROLLED ADDRESS BALANCE SUMMARY")
    print("=" * 60)
    print(f"🔑 Total Controlled Addresses Checked: {results['checked']}")
    print(f"❌ Errors Encountered: {results['errors']}")
    print(f"💰 Funded Addresses Found: {len(results['funded'])}")
    
    if results['funded']:
        print(f"\n🎉 SUCCESS: Found {len(results['funded'])} funded addresses you control!")
        print("-" * 60)
        
        for i, fund in enumerate(results['funded'], 1):
            print(f"\n💎 FUNDED ADDRESS #{i}:")
            print(f"   Blockchain: {fund['blockchain'].upper()}")
            print(f"   Address: {fund['address']}")
            
            if fund['blockchain'] == 'ethereum':
                print(f"   Balance: {fund['balance_eth']:.6f} ETH")
                print(f"   Value (Wei): {fund['balance_wei']}")
            elif fund['blockchain'] == 'bitcoin':
                print(f"   Balance: {fund['balance_btc']:.8f} BTC")
                print(f"   Value (Satoshis): {fund['balance_sat']}")
            elif fund['blockchain'] == 'solana':
                print(f"   Balance: {fund['balance_sol']:.6f} SOL")
                print(f"   Value (Lamports): {fund['balance_lamports']}")
            
            print(f"   🔑 Private Key: {fund['private_key']}")
            print("   " + "-" * 50)
        
        # Save results
        output_file = f"FUNDED_CONTROLLED_ADDRESSES_{int(time.time())}.json"
        with open(output_file, 'w') as f:
            json.dump({
                'summary': {
                    'total_checked': results['checked'],
                    'total_funded': len(results['funded']),
                    'errors': results['errors']
                },
                'funded_addresses': results['funded']
            }, f, indent=2)
        
        print(f"\n💾 Complete results saved to: {output_file}")
        print(f"🚨 KEEP THIS FILE SECURE - IT CONTAINS PRIVATE KEYS!")
        
    else:
        print(f"\n💸 No funded addresses found among the {results['checked']} controlled addresses checked.")
        print("🔄 Try checking more addresses or run again later.")

if __name__ == "__main__":
    wallet_file = "detected_wallet_data_summary.json"
    max_addresses = 25  # Per blockchain
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--reset-history":
            print("🗑️  Resetting checking history...")
            history_file = "checked_addresses_history.json"
            if os.path.exists(history_file):
                os.remove(history_file)
                print("✅ Checking history cleared!")
            else:
                print("✅ No history file found, nothing to clear.")
            sys.exit(0)
        else:
            wallet_file = sys.argv[1]
            
    if len(sys.argv) > 2:
        max_addresses = int(sys.argv[2])
    
    print("💡 Tip: Use '--reset-history' to clear checking history and start fresh")
    print("📁 History is saved in: checked_addresses_history.json")
    print()
    
    check_controlled_addresses(wallet_file, max_addresses)
