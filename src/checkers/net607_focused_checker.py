#!/usr/bin/env python3
"""
NET607 Focused Balance Checker
Check the extracted high-priority keys for balances
"""

import json
import time
import asyncio
import aiohttp
from datetime import datetime
from pathlib import Path
import random
from web3 import Web3
from eth_keys import keys as eth_keys
from eth_utils import to_checksum_address

class NET607FocusedChecker:
    def __init__(self):
        self.session = None
        self.api_keys = []
        self.results_file = f"NET607_BALANCE_RESULTS_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        self.funded_wallets = []
        self.checked_count = 0
        self.start_time = time.time()
        self.keys_to_check = []
        
        # Load API configuration
        self.load_api_config()
        
        # Load extracted keys
        self.load_extracted_keys()
        
    def load_api_config(self):
        """Load API keys from configuration"""
        try:
            with open('api_config.json', 'r') as f:
                config = json.load(f)
                self.api_keys = [
                    key for provider in config.values() 
                    for key in (provider.get('keys', []) if isinstance(provider.get('keys'), list) else [])
                    if key and key.strip()
                ]
            print(f"✅ Loaded {len(self.api_keys)} API keys")
        except Exception as e:
            print(f"⚠️  API config error: {e}")
            # Add backup API keys (replace with real ones)
            self.api_keys = ['REPLACE_WITH_YOUR_BACKUP_KEY', 'REPLACE_WITH_YOUR_BACKUP_KEY']
    
    def load_extracted_keys(self):
        """Load the extracted keys from JSON"""
        try:
            # Find the latest extraction file
            extraction_files = list(Path('.').glob('NET607_COMPREHENSIVE_KEYS_*.json'))
            if not extraction_files:
                raise FileNotFoundError("No NET607 extraction results found")
            
            latest_file = max(extraction_files, key=lambda x: x.stat().st_mtime)
            print(f"📂 Loading keys from: {latest_file}")
            
            with open(latest_file, 'r') as f:
                data = json.load(f)
            
            # Get prioritized keys
            prioritized_keys = data.get('prioritized_keys', {})
            
            # Load high priority first, then medium, then low
            for priority_level in ['high_priority', 'medium_priority', 'low_priority']:
                keys_list = prioritized_keys.get(priority_level, [])
                for key_data in keys_list:
                    key_data['priority_level'] = priority_level
                    self.keys_to_check.append(key_data)
            
            print(f"🎯 Loaded {len(self.keys_to_check)} prioritized keys")
            
            # Priority breakdown
            priority_counts = {}
            for key_data in self.keys_to_check:
                level = key_data.get('priority_level', 'unknown')
                priority_counts[level] = priority_counts.get(level, 0) + 1
            
            for priority, count in priority_counts.items():
                print(f"    {priority}: {count} keys")
                
        except Exception as e:
            print(f"❌ Failed to load extraction results: {e}")
            self.keys_to_check = []
    
    def get_api_key(self) -> str:
        """Get a random API key"""
        if not self.api_keys:
            return ""
        return random.choice(self.api_keys)
    
    def is_valid_ethereum_key(self, key: str) -> bool:
        """Check if this looks like a valid Ethereum private key"""
        try:
            # Remove 0x prefix if present
            if key.startswith('0x'):
                key = key[2:]
            
            # Must be exactly 64 hex characters
            if len(key) != 64:
                return False
            
            # Must be valid hex
            int(key, 16)
            
            # Should not be all zeros or all Fs
            if key == '0' * 64 or key.lower() == 'f' * 64:
                return False
            
            return True
            
        except ValueError:
            return False
    
    async def check_single_balance(self, session: aiohttp.ClientSession, key_data: dict) -> dict | None:
        """Check balance for a single key"""
        try:
            key = key_data.get('key', '').strip()
            
            # Skip if not a valid Ethereum key
            if not self.is_valid_ethereum_key(key):
                return None
            
            # Convert to Ethereum address
            try:
                if key.startswith('0x'):
                    pk_bytes = bytes.fromhex(key[2:])
                else:
                    pk_bytes = bytes.fromhex(key)
                
                if len(pk_bytes) != 32:
                    return None
                
                private_key_obj = eth_keys.PrivateKey(pk_bytes)
                address = to_checksum_address(private_key_obj.public_key.to_address())
                
            except Exception:
                return None
            
            # Check balance using Etherscan API
            api_key = self.get_api_key()
            url = "https://api.etherscan.io/api"
            params = {
                'module': 'account',
                'action': 'balance',
                'address': address,
                'tag': 'latest'
            }
            
            if api_key and api_key not in ['backup_key_1', 'backup_key_2']:
                params['apikey'] = api_key
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('status') == '1' and 'result' in data:
                        balance_wei = int(data['result'])
                        if balance_wei > 0:
                            balance_eth = balance_wei / 10**18
                            
                            result = {
                                'private_key': key,
                                'address': address,
                                'balance_wei': balance_wei,
                                'balance_eth': balance_eth,
                                'source_file': key_data.get('source_file', 'unknown'),
                                'country': key_data.get('country', 'unknown'),
                                'priority_score': key_data.get('priority_score', 0),
                                'priority_level': key_data.get('priority_level', 'unknown'),
                                'pattern_type': key_data.get('pattern_type', 'unknown'),
                                'checked_at': datetime.now().isoformat()
                            }
                            
                            print(f"\n💰 FUNDED WALLET FOUND!")
                            print(f"    Address: {address}")
                            print(f"    Balance: {balance_eth:.6f} ETH ({balance_wei} wei)")
                            print(f"    Priority: {key_data.get('priority_level', 'unknown')} (score: {key_data.get('priority_score', 0):.3f})")
                            print(f"    Pattern: {key_data.get('pattern_type', 'unknown')}")
                            print(f"    Source: {key_data.get('source_file', 'unknown')}")
                            print(f"    Country: {key_data.get('country', 'unknown')}")
                            
                            return result
                elif response.status == 429:  # Rate limited
                    await asyncio.sleep(1)  # Wait longer on rate limit
                    
            # Rate limiting
            await asyncio.sleep(0.15)  # Slightly slower to avoid rate limits
            return None
            
        except Exception as e:
            return None
    
    async def batch_check_balances(self, max_keys: int = 10000, batch_size: int = 30):
        """Check balances in batches"""
        if not self.keys_to_check:
            print("❌ No keys to check")
            return
        
        # Limit keys to check
        keys_to_process = self.keys_to_check[:max_keys]
        
        print(f"🚀 Starting balance checking for {len(keys_to_process)} keys")
        print(f"📊 Batch size: {batch_size}")
        
        connector = aiohttp.TCPConnector(limit=50, limit_per_host=25)
        timeout = aiohttp.ClientTimeout(total=60)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            for i in range(0, len(keys_to_process), batch_size):
                batch = keys_to_process[i:i + batch_size]
                batch_num = i // batch_size + 1
                total_batches = (len(keys_to_process) + batch_size - 1) // batch_size
                
                print(f"\n🔍 Checking batch {batch_num}/{total_batches} ({len(batch)} keys)...")
                
                # Create tasks for this batch
                tasks = []
                for key_data in batch:
                    task = self.check_single_balance(session, key_data)
                    tasks.append(task)
                
                # Execute batch
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Process results
                for result in results:
                    if isinstance(result, dict) and result:
                        self.funded_wallets.append(result)
                        self.save_results()  # Save immediately when found
                
                self.checked_count += len(batch)
                
                # Progress update
                elapsed = time.time() - self.start_time
                rate = self.checked_count / elapsed if elapsed > 0 else 0
                
                print(f"📊 Progress: {self.checked_count}/{len(keys_to_process)} keys checked")
                print(f"⚡ Rate: {rate:.1f} keys/sec")
                print(f"💰 Funded wallets found: {len(self.funded_wallets)}")
                
                # Pause between batches to be respectful to API
                await asyncio.sleep(2)
    
    def save_results(self):
        """Save current results to file"""
        results = {
            'scan_info': {
                'scan_type': 'NET607_focused_balance_check',
                'started_at': datetime.fromtimestamp(self.start_time).isoformat(),
                'completed_at': datetime.now().isoformat(),
                'keys_checked': self.checked_count,
                'funded_wallets_found': len(self.funded_wallets),
                'total_balance_wei': sum(w.get('balance_wei', 0) for w in self.funded_wallets),
                'total_balance_eth': sum(w.get('balance_eth', 0) for w in self.funded_wallets)
            },
            'funded_wallets': self.funded_wallets
        }
        
        with open(self.results_file, 'w') as f:
            json.dump(results, f, indent=2)
    
    def print_summary(self):
        """Print final summary"""
        elapsed = time.time() - self.start_time
        
        print(f"\n🎉 NET607 FOCUSED BALANCE CHECK COMPLETE!")
        print(f"==================================================")
        print(f"⏱️  Total Time: {elapsed:.1f} seconds")
        print(f"🔍 Keys Checked: {self.checked_count:,}")
        print(f"⚡ Average Rate: {self.checked_count/elapsed:.1f} keys/sec")
        print(f"💰 Funded Wallets Found: {len(self.funded_wallets)}")
        
        if self.funded_wallets:
            total_eth = sum(w.get('balance_eth', 0) for w in self.funded_wallets)
            total_wei = sum(w.get('balance_wei', 0) for w in self.funded_wallets)
            print(f"💎 Total Balance Found: {total_eth:.6f} ETH ({total_wei:,} wei)")
            print(f"\n🏆 FUNDED WALLETS:")
            for i, wallet in enumerate(self.funded_wallets, 1):
                print(f"  [{i}] {wallet['address']}")
                print(f"      Balance: {wallet['balance_eth']:.6f} ETH")
                print(f"      Priority: {wallet['priority_level']} (score: {wallet['priority_score']:.3f})")
                print(f"      Pattern: {wallet['pattern_type']}")
                print(f"      Source: {wallet['source_file']}")
                print(f"      Country: {wallet['country']}")
        else:
            print("💡 No funded wallets found in this batch")
        
        print(f"\n💾 Results saved to: {self.results_file}")

async def main():
    """Main execution function"""
    checker = NET607FocusedChecker()
    
    if not checker.keys_to_check:
        print("❌ No keys loaded for checking")
        return
    
    try:
        # Check top 10,000 keys in batches of 30
        await checker.batch_check_balances(max_keys=10000, batch_size=30)
        
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"❌ Error during balance checking: {e}")
    finally:
        checker.save_results()
        checker.print_summary()

if __name__ == "__main__":
    print("🎯 NET607 FOCUSED BALANCE CHECKER")
    print("=" * 50)
    asyncio.run(main())
