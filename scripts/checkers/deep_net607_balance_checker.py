#!/usr/bin/env python3
"""
Deep Net607 Balance Checker
Check balances for all 2,044 unique keys extracted from IP directories
"""

import json
import asyncio
import aiohttp
from datetime import datetime
from bitcoin import privkey_to_address

class DeepNet607BalanceChecker:
    def __init__(self):
        self.results_file = "DEEP_NET607_HUNT_RESULTS_20250813_185936.json"
        self.batch_size = 20
        self.delay_between_batches = 1.0
        
    def load_extracted_keys(self):
        """Load the 2,044 unique keys from the hunt results"""
        try:
            with open(self.results_file, 'r') as f:
                data = json.load(f)
            
            unique_keys = data.get('unique_keys', [])
            print(f"✅ Loaded {len(unique_keys)} unique keys from deep hunt")
            return unique_keys
            
        except Exception as e:
            print(f"❌ Error loading keys: {e}")
            return []
    
    async def check_bitcoin_balance(self, session, address):
        """Check Bitcoin balance for an address"""
        try:
            url = f"https://api.blockcypher.com/v1/btc/main/addrs/{address}/balance"
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    balance = data.get('balance', 0)
                    total_received = data.get('total_received', 0)
                    
                    return {
                        'address': address,
                        'balance': balance,
                        'balance_btc': balance / 100000000,
                        'total_received': total_received,
                        'status': 'funded' if balance > 0 else ('swept' if total_received > 0 else 'empty')
                    }
                    
        except Exception as e:
            return None
    
    async def check_balance_batch(self, keys_batch, batch_num, total_batches):
        """Check balances for a batch of keys"""
        print(f"🔄 Processing batch {batch_num}/{total_batches} ({len(keys_batch)} keys)...")
        
        connector = aiohttp.TCPConnector(limit=25)
        timeout = aiohttp.ClientTimeout(total=30)
        
        funded_wallets = []
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            tasks = []
            
            for key_data in keys_batch:
                try:
                    private_key = key_data['key']
                    
                    # Only check hex private keys for now
                    if key_data['type'] == 'private_key_hex' and len(private_key) == 64:
                        # Generate Bitcoin address
                        address = privkey_to_address(private_key)
                        
                        # Create balance check task
                        task = self.check_bitcoin_balance(session, address)
                        tasks.append((task, private_key, key_data))
                        
                except Exception as e:
                    continue
            
            if tasks:
                # Execute all balance checks concurrently
                results = await asyncio.gather(*[task[0] for task in tasks], return_exceptions=True)
                
                for i, result in enumerate(results):
                    if isinstance(result, dict) and result:
                        private_key = tasks[i][1]
                        source_data = tasks[i][2]
                        
                        if result['status'] != 'empty':
                            funded_wallets.append({
                                **result,
                                'private_key': private_key,
                                'source_file': source_data.get('file', 'unknown'),
                                'found_in_ip': source_data.get('file', '').split('/')[4] if '/' in source_data.get('file', '') else 'unknown'
                            })
                            
                            status_icon = "💰" if result['status'] == 'funded' else "🔄"
                            print(f"   {status_icon} {result['address']}: {result['balance_btc']:.8f} BTC ({result['status']})")
        
        return funded_wallets
    
    async def check_all_balances(self):
        """Check balances for all 2,044 keys"""
        print("🚀 DEEP NET607 BALANCE CHECKING")
        print("=" * 60)
        print(f"📅 Check Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Load extracted keys
        all_keys = self.load_extracted_keys()
        
        if not all_keys:
            print("❌ No keys to check!")
            return
        
        # Filter to hex private keys only
        hex_keys = [k for k in all_keys if k['type'] == 'private_key_hex' and len(k['key']) == 64]
        print(f"🔍 Checking {len(hex_keys)} hex private keys out of {len(all_keys)} total")
        
        # Process in batches
        total_batches = (len(hex_keys) + self.batch_size - 1) // self.batch_size
        all_funded = []
        
        for i in range(0, len(hex_keys), self.batch_size):
            batch = hex_keys[i:i + self.batch_size]
            batch_num = i // self.batch_size + 1
            
            funded = await self.check_balance_batch(batch, batch_num, total_batches)
            
            if funded:
                all_funded.extend(funded)
                print(f"   ✅ Found {len(funded)} funded/swept wallets in batch {batch_num}")
            else:
                print(f"   📭 No funded wallets in batch {batch_num}")
            
            # Rate limiting
            if batch_num < total_batches:
                await asyncio.sleep(self.delay_between_batches)
        
        # Final results
        print(f"\n🎉 DEEP BALANCE CHECK COMPLETE")
        print("=" * 60)
        print(f"   Keys Checked: {len(hex_keys)}")
        print(f"   Funded/Swept Found: {len(all_funded)}")
        
        if all_funded:
            funded_only = [w for w in all_funded if w['status'] == 'funded']
            swept_only = [w for w in all_funded if w['status'] == 'swept']
            
            print(f"   Currently Funded: {len(funded_only)}")
            print(f"   Previously Swept: {len(swept_only)}")
            
            if funded_only:
                total_btc = sum(w['balance_btc'] for w in funded_only)
                print(f"   Total Recoverable: {total_btc:.8f} BTC")
                print(f"   Estimated USD: ${total_btc * 65000:.2f}")
                
                print(f"\n💰 FUNDED WALLETS READY FOR RECOVERY:")
                for wallet in funded_only:
                    print(f"   🎯 {wallet['address']}: {wallet['balance_btc']:.8f} BTC")
                    print(f"      Private Key: {wallet['private_key']}")
                    print(f"      Source: {wallet['found_in_ip']}")
            
            # Save results
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            results_file = f"DEEP_NET607_BALANCE_RESULTS_{timestamp}.json"
            
            balance_results = {
                'check_info': {
                    'type': 'deep_net607_balance_check',
                    'started_at': datetime.now().isoformat(),
                    'keys_checked': len(hex_keys),
                    'wallets_found': len(all_funded),
                    'funded_wallets': len(funded_only),
                    'swept_wallets': len(swept_only)
                },
                'funded_wallets': funded_only,
                'swept_wallets': swept_only,
                'all_results': all_funded,
                'summary': {
                    'total_btc_found': sum(w['balance_btc'] for w in funded_only),
                    'recovery_opportunities': len(funded_only)
                }
            }
            
            with open(results_file, 'w') as f:
                json.dump(balance_results, f, indent=2)
            
            print(f"\n💾 Results saved to: {results_file}")
            
            if len(funded_only) > 0:
                print(f"\n🚀 RECOVERY READY!")
                print(f"   Use the private keys above for immediate recovery")
                print(f"   Estimated total value: ${sum(w['balance_btc'] for w in funded_only) * 65000:.2f}")
        
        else:
            print(f"   📭 No funded or swept wallets found")
            print(f"   All checked addresses are empty")
        
        return len(all_funded)

async def main():
    checker = DeepNet607BalanceChecker()
    results = await checker.check_all_balances()

if __name__ == "__main__":
    asyncio.run(main())
