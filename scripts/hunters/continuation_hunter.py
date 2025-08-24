#!/usr/bin/env python3
"""
Comprehensive Continuation Hunter
Process all remaining data sources for wallet recovery opportunities
"""

import json
import os
import re
import hashlib
import asyncio
import aiohttp
from datetime import datetime
from collections import defaultdict
import sqlite3

class ContinuationHunter:
    def __init__(self):
        self.base_dir = "/home/admin/wallet_tool"
        self.networks = {
            'bitcoin': {'min_balance': 1000, 'priority': 1},  # 1000 sats minimum
            'ethereum': {'min_balance': 0.001, 'priority': 2},  # 0.001 ETH minimum
            'litecoin': {'min_balance': 0.01, 'priority': 3},
            'dogecoin': {'min_balance': 100, 'priority': 4},
            'bitcoin_cash': {'min_balance': 0.001, 'priority': 5}
        }
        
        # Track what we've already checked
        self.checked_addresses = set()
        self.load_previous_results()
        
        # Data sources to process
        self.data_sources = [
            "SMART_HUNTING_TARGETS_20250813_124818.json",
            "PRIORITY_RICHEST_KEYS.json", 
            "PRIORITY_CHECKING_LIST.json",
            "NET602_EXTRACTED_KEYS_20250813_130504.json",
            "NET607_COMPREHENSIVE_KEYS_20250813_162221.json",
            "METAMASK_BATCH2_RESULTS.json",
            "enhanced_wallet_extraction_results.json",
            "extracted_addresses_sorted.json",
            "funded_addresses_consolidated.json",
            "wallet_items_sorted_by_likelihood.json",
            "FOCUSED_JACKPOT_1_20250813_103810.json",
            "MULTI_DATASET_JACKPOT_20250813_100243.json"
        ]
    
    def load_previous_results(self):
        """Load previously checked addresses to avoid duplicates"""
        previous_files = [
            "MULTI_BLOCKCHAIN_RESULTS_20250813_170136.json",
            "NET607_BALANCE_RESULTS_20250813_162940.json",
            "ADDRESS_VERIFICATION_20250813_171615.json"
        ]
        
        for file in previous_files:
            path = os.path.join(self.base_dir, file)
            if os.path.exists(path):
                try:
                    with open(path, 'r') as f:
                        data = json.load(f)
                        
                    # Extract addresses from various formats
                    if isinstance(data, dict):
                        if 'results_by_network' in data:
                            for network, results in data['results_by_network'].items():
                                for result in results:
                                    if 'address' in result:
                                        self.checked_addresses.add(result['address'])
                        
                        if 'addresses_checked' in data:
                            self.checked_addresses.update(data['addresses_checked'])
                            
                except Exception as e:
                    print(f"⚠️ Error loading {file}: {e}")
        
        print(f"📋 Loaded {len(self.checked_addresses)} previously checked addresses")
    
    def extract_keys_from_source(self, source_file):
        """Extract private keys and addresses from various data source formats"""
        path = os.path.join(self.base_dir, source_file)
        
        if not os.path.exists(path):
            return []
        
        try:
            with open(path, 'r') as f:
                data = json.load(f)
            
            keys = []
            
            # Handle various JSON structures
            if isinstance(data, list):
                for item in data:
                    keys.extend(self.extract_keys_from_item(item))
            elif isinstance(data, dict):
                # Check for common key structures
                for key in ['keys', 'wallets', 'targets', 'addresses', 'results', 'candidates']:
                    if key in data:
                        if isinstance(data[key], list):
                            for item in data[key]:
                                keys.extend(self.extract_keys_from_item(item))
                        else:
                            keys.extend(self.extract_keys_from_item(data[key]))
                
                # Also check the root level
                keys.extend(self.extract_keys_from_item(data))
            
            return keys
            
        except Exception as e:
            print(f"⚠️ Error processing {source_file}: {e}")
            return []
    
    def extract_keys_from_item(self, item):
        """Extract keys from individual items"""
        keys = []
        
        if isinstance(item, dict):
            # Look for private key patterns
            for key in ['private_key', 'privkey', 'key', 'privateKey', 'pk']:
                if key in item and item[key]:
                    private_key = str(item[key]).replace('0x', '').strip()
                    if len(private_key) in [64, 66] and all(c in '0123456789abcdefABCDEF' for c in private_key):
                        keys.append({
                            'private_key': private_key.lower(),
                            'source_data': item
                        })
            
            # Also extract any hex strings that look like private keys
            for key, value in item.items():
                if isinstance(value, str):
                    # Remove 0x prefix if present
                    clean_value = value.replace('0x', '').strip()
                    # Check if it's a valid private key format
                    if len(clean_value) == 64 and all(c in '0123456789abcdefABCDEF' for c in clean_value):
                        keys.append({
                            'private_key': clean_value.lower(),
                            'source_data': item
                        })
        
        elif isinstance(item, str):
            # Direct string that might be a private key
            clean_item = item.replace('0x', '').strip()
            if len(clean_item) == 64 and all(c in '0123456789abcdefABCDEF' for c in clean_item):
                keys.append({
                    'private_key': clean_item.lower(),
                    'source_data': {'raw_key': item}
                })
        
        return keys
    
    async def check_bitcoin_balance(self, session, address):
        """Check Bitcoin balance using BlockCypher API"""
        try:
            url = f"https://api.blockcypher.com/v1/btc/main/addrs/{address}/balance"
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    balance = data.get('balance', 0)
                    total_received = data.get('total_received', 0)
                    
                    if balance > 0 or total_received > 0:
                        return {
                            'network': 'bitcoin',
                            'address': address,
                            'balance': balance,
                            'balance_btc': balance / 100000000,
                            'total_received': total_received,
                            'status': 'funded' if balance > 0 else 'swept'
                        }
                        
        except Exception as e:
            pass
        
        return None
    
    async def check_ethereum_balance(self, session, address):
        """Check Ethereum balance"""
        try:
            # Convert private key to Ethereum address if needed
            from eth_keys import keys
            from eth_utils import to_checksum_address
            
            # This is a placeholder - would need proper ETH address derivation
            # For now, skip ETH to focus on Bitcoin
            return None
                        
        except Exception as e:
            pass
        
        return None
    
    async def process_key_batch(self, keys_batch):
        """Process a batch of keys for balance checking"""
        connector = aiohttp.TCPConnector(limit=20)
        timeout = aiohttp.ClientTimeout(total=30)
        
        funded_wallets = []
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            tasks = []
            
            for key_data in keys_batch:
                private_key = key_data['private_key']
                
                # Generate Bitcoin address
                try:
                    from bitcoin import privkey_to_address
                    btc_address = privkey_to_address(private_key)
                    
                    # Skip if we've already checked this address
                    if btc_address not in self.checked_addresses:
                        tasks.append(self.check_bitcoin_balance(session, btc_address))
                        key_data['btc_address'] = btc_address
                        self.checked_addresses.add(btc_address)
                
                except Exception as e:
                    continue
            
            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for i, result in enumerate(results):
                    if isinstance(result, dict) and result:
                        funded_wallets.append({
                            **result,
                            'private_key': keys_batch[i]['private_key'],
                            'source_data': keys_batch[i].get('source_data', {})
                        })
        
        return funded_wallets
    
    async def hunt_continuation(self):
        """Main hunting continuation function"""
        print("🚀 COMPREHENSIVE CONTINUATION HUNT")
        print("=" * 60)
        print(f"📅 Hunt Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        all_keys = []
        source_stats = {}
        
        # Extract keys from all data sources
        print(f"\n📥 EXTRACTING KEYS FROM DATA SOURCES")
        print("-" * 40)
        
        for source in self.data_sources:
            print(f"🔍 Processing {source}...")
            keys = self.extract_keys_from_source(source)
            
            if keys:
                all_keys.extend(keys)
                source_stats[source] = len(keys)
                print(f"   ✅ Extracted {len(keys)} keys")
            else:
                print(f"   📭 No keys found")
        
        # Deduplicate keys
        unique_keys = {}
        for key_data in all_keys:
            private_key = key_data['private_key']
            if private_key not in unique_keys:
                unique_keys[private_key] = key_data
        
        print(f"\n📊 EXTRACTION SUMMARY")
        print("-" * 40)
        print(f"   Total Keys Extracted: {len(all_keys)}")
        print(f"   Unique Keys: {len(unique_keys)}")
        print(f"   Data Sources Processed: {len([s for s in source_stats.values() if s > 0])}")
        print(f"   Previously Checked Addresses: {len(self.checked_addresses)}")
        
        if not unique_keys:
            print(f"\n⚠️ No new keys to process!")
            return
        
        # Process keys in batches
        print(f"\n⚡ BATCH PROCESSING KEYS")
        print("-" * 40)
        
        keys_list = list(unique_keys.values())
        batch_size = 50
        total_batches = (len(keys_list) + batch_size - 1) // batch_size
        
        all_funded = []
        
        for i in range(0, len(keys_list), batch_size):
            batch = keys_list[i:i + batch_size]
            batch_num = i // batch_size + 1
            
            print(f"🔄 Processing batch {batch_num}/{total_batches} ({len(batch)} keys)...")
            
            funded = await self.process_key_batch(batch)
            
            if funded:
                all_funded.extend(funded)
                print(f"   💰 Found {len(funded)} funded wallets!")
                
                # Show immediate results
                for wallet in funded:
                    balance_btc = wallet['balance_btc']
                    status = wallet['status']
                    print(f"      🎯 {wallet['address']}: {balance_btc:.8f} BTC ({status})")
            else:
                print(f"   📭 No funded wallets in this batch")
            
            # Rate limiting
            await asyncio.sleep(2)
        
        # Final results
        print(f"\n🎉 CONTINUATION HUNT COMPLETE")
        print("=" * 60)
        print(f"   Keys Processed: {len(keys_list)}")
        print(f"   Funded Wallets Found: {len(all_funded)}")
        
        if all_funded:
            total_btc = sum(w['balance_btc'] for w in all_funded)
            print(f"   Total Recoverable: {total_btc:.8f} BTC")
            print(f"   Estimated USD: ${total_btc * 65000:.2f}")
            
            # Save results
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            results_file = f"CONTINUATION_HUNT_RESULTS_{timestamp}.json"
            
            hunt_results = {
                'hunt_info': {
                    'type': 'continuation_hunt',
                    'started_at': datetime.now().isoformat(),
                    'keys_processed': len(keys_list),
                    'sources_processed': list(source_stats.keys()),
                    'funded_wallets_found': len(all_funded)
                },
                'source_statistics': source_stats,
                'funded_wallets': all_funded,
                'summary': {
                    'total_btc_found': total_btc,
                    'estimated_usd': total_btc * 65000,
                    'recovery_opportunities': len([w for w in all_funded if w['status'] == 'funded'])
                }
            }
            
            with open(results_file, 'w') as f:
                json.dump(hunt_results, f, indent=2)
            
            print(f"\n💾 Results saved to: {results_file}")
            
            # Show actionable results
            funded_only = [w for w in all_funded if w['status'] == 'funded']
            if funded_only:
                print(f"\n🚀 READY FOR RECOVERY ({len(funded_only)} wallets):")
                for wallet in funded_only:
                    print(f"   💰 {wallet['address']}: {wallet['balance_btc']:.8f} BTC")
                    print(f"      Private Key: {wallet['private_key']}")
        
        else:
            print(f"   📭 No new funded wallets discovered")
            print(f"   🔄 All available sources have been processed")
        
        return all_funded

async def main():
    hunter = ContinuationHunter()
    results = await hunter.hunt_continuation()

if __name__ == "__main__":
    asyncio.run(main())
