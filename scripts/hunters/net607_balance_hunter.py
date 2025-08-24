#!/usr/bin/env python3
"""
NET607 Balance Hunter - High-Priority Balance Checking
Advanced batch checking for NET607 extracted keys
"""

import json
import time
import asyncio
import aiohttp
from datetime import datetime
from pathlib import Path
import concurrent.futures
from typing import Dict, List, Any, Optional
import hashlib
import random
from web3 import Web3
from eth_keys import keys as eth_keys
from eth_utils import to_checksum_address
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class NET607BalanceHunter:
    def __init__(self):
        self.session = None
        self.api_keys = []
        self.rate_limits = {}
        self.results_file = f"NET607_BALANCE_RESULTS_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        self.funded_wallets = []
        self.checked_count = 0
        self.start_time = time.time()
        
        # Load API configuration
        self.load_api_config()
        
        # Load NET607 extraction results
        self.load_extraction_results()
        
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
            self.api_keys = []
    
    def load_extraction_results(self):
        """Load NET607 extraction results"""
        try:
            # Find the latest NET607 extraction file
            extraction_files = list(Path('.').glob('NET607_EXTRACTION_*.json'))
            if not extraction_files:
                raise FileNotFoundError("No NET607 extraction results found")
            
            latest_file = max(extraction_files, key=lambda x: x.stat().st_mtime)
            
            with open(latest_file, 'r') as f:
                data = json.load(f)
                
            # Get prioritized keys (high priority first)
            all_keys = data.get('prioritized_keys', {})
            
            # Sort by priority score (highest first)
            self.priority_keys = []
            for priority, keys_list in all_keys.items():
                for key_data in keys_list:
                    key_data['priority_level'] = priority
                    self.priority_keys.append(key_data)
            
            # Sort by score descending
            self.priority_keys.sort(key=lambda x: x.get('score', 0), reverse=True)
            
            print(f"🎯 Loaded {len(self.priority_keys)} prioritized keys from {latest_file}")
            print(f"📊 Priority breakdown:")
            priority_counts = {}
            for key_data in self.priority_keys:
                level = key_data.get('priority_level', 'unknown')
                priority_counts[level] = priority_counts.get(level, 0) + 1
            
            for priority, count in sorted(priority_counts.items()):
                print(f"    {priority}: {count} keys")
                
        except Exception as e:
            print(f"❌ Failed to load extraction results: {e}")
            self.priority_keys = []
    
    def get_api_key(self) -> str:
        """Get a random API key"""
        if not self.api_keys:
            return ""
        return random.choice(self.api_keys)
    
    async def check_single_balance(self, session: aiohttp.ClientSession, key_data: Dict) -> Optional[Dict]:
        """Check balance for a single key"""
        try:
            private_key = key_data.get('private_key', '')
            if not private_key:
                return None
            
            # Generate address from private key
            try:
                # Handle different private key formats
                if private_key.startswith('0x'):
                    pk_bytes = bytes.fromhex(private_key[2:])
                else:
                    pk_bytes = bytes.fromhex(private_key)
                
                if len(pk_bytes) != 32:
                    return None
                
                private_key_obj = eth_keys.PrivateKey(pk_bytes)
                address = to_checksum_address(private_key_obj.public_key.to_address())
                
            except Exception as e:
                return None
            
            # Check balance using Etherscan API
            api_key = self.get_api_key()
            url = "https://api.etherscan.io/api"
            params = {
                'module': 'account',
                'action': 'balance',
                'address': address,
                'tag': 'latest',
                'apikey': api_key
            }
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('status') == '1' and 'result' in data:
                        balance_wei = int(data['result'])
                        if balance_wei > 0:
                            balance_eth = balance_wei / 10**18
                            
                            result = {
                                'private_key': private_key,
                                'address': address,
                                'balance_wei': balance_wei,
                                'balance_eth': balance_eth,
                                'source': key_data.get('source', 'unknown'),
                                'priority_score': key_data.get('score', 0),
                                'priority_level': key_data.get('priority_level', 'unknown'),
                                'checked_at': datetime.now().isoformat()
                            }
                            
                            print(f"💰 FUNDED WALLET FOUND!")
                            print(f"    Address: {address}")
                            print(f"    Balance: {balance_eth:.6f} ETH ({balance_wei} wei)")
                            print(f"    Priority: {key_data.get('priority_level', 'unknown')} (score: {key_data.get('score', 0):.3f})")
                            print(f"    Source: {key_data.get('source', 'unknown')}")
                            
                            return result
            
            # Small delay to respect rate limits
            await asyncio.sleep(0.1)
            return None
            
        except Exception as e:
            return None
    
    async def batch_check_balances(self, batch_size: int = 50, max_keys: int = 10000):
        """Check balances in batches"""
        if not self.priority_keys:
            print("❌ No keys to check")
            return
        
        print(f"🚀 Starting balance checking for up to {max_keys} high-priority keys")
        print(f"📊 Batch size: {batch_size}")
        
        # Limit to max_keys
        keys_to_check = self.priority_keys[:max_keys]
        
        connector = aiohttp.TCPConnector(limit=100, limit_per_host=50)
        timeout = aiohttp.ClientTimeout(total=30)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            for i in range(0, len(keys_to_check), batch_size):
                batch = keys_to_check[i:i + batch_size]
                batch_num = i // batch_size + 1
                total_batches = (len(keys_to_check) + batch_size - 1) // batch_size
                
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
                    if isinstance(result, dict) and result.get('balance_wei', 0) > 0:
                        self.funded_wallets.append(result)
                        
                        # Save immediately when found
                        self.save_results()
                
                self.checked_count += len(batch)
                
                # Progress update
                elapsed = time.time() - self.start_time
                rate = self.checked_count / elapsed if elapsed > 0 else 0
                
                print(f"📊 Progress: {self.checked_count}/{len(keys_to_check)} keys checked")
                print(f"⚡ Rate: {rate:.1f} keys/sec")
                print(f"💰 Funded wallets found: {len(self.funded_wallets)}")
                
                # Brief pause between batches
                await asyncio.sleep(1)
    
    def save_results(self):
        """Save current results to file"""
        results = {
            'scan_info': {
                'scan_type': 'NET607_balance_check',
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
        
        print(f"\n🎉 NET607 BALANCE CHECK COMPLETE!")
        print(f"==================================================")
        print(f"⏱️  Total Time: {elapsed:.1f} seconds")
        print(f"🔍 Keys Checked: {self.checked_count:,}")
        print(f"⚡ Average Rate: {self.checked_count/elapsed:.1f} keys/sec")
        print(f"💰 Funded Wallets Found: {len(self.funded_wallets)}")
        
        if self.funded_wallets:
            total_eth = sum(w.get('balance_eth', 0) for w in self.funded_wallets)
            print(f"💎 Total Balance Found: {total_eth:.6f} ETH")
            print(f"\n🏆 FUNDED WALLETS:")
            for i, wallet in enumerate(self.funded_wallets, 1):
                print(f"  [{i}] {wallet['address']}")
                print(f"      Balance: {wallet['balance_eth']:.6f} ETH")
                print(f"      Priority: {wallet['priority_level']} (score: {wallet['priority_score']:.3f})")
                print(f"      Source: {wallet['source']}")
        
        print(f"\n💾 Results saved to: {self.results_file}")

async def main():
    """Main execution function"""
    hunter = NET607BalanceHunter()
    
    if not hunter.priority_keys:
        print("❌ No keys loaded for checking")
        return
    
    try:
        # Check top 10,000 priority keys in batches of 50
        await hunter.batch_check_balances(batch_size=50, max_keys=10000)
        
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"❌ Error during balance checking: {e}")
    finally:
        hunter.save_results()
        hunter.print_summary()

if __name__ == "__main__":
    print("🎯 NET607 BALANCE HUNTER")
    print("=" * 50)
    asyncio.run(main())
