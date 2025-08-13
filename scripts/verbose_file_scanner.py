#!/usr/bin/env python3
"""
Comprehensive Verbose File Scanner - Scans for private keys, addresses, and wallet data
Shows detailed information about what files are being processed
"""
import os
import sys
import re
import json
from pathlib import Path

try:
    from bip_utils import WifEncoder, WifDecoder, Bip44, Bip44Coins, Bip44Changes
    from eth_keys import keys as eth_keys
    from eth_utils import to_checksum_address
    CRYPTO_LIBS_AVAILABLE = True
except ImportError:
    print("⚠️  Crypto libraries not available - will only find patterns, not validate keys")
    CRYPTO_LIBS_AVAILABLE = False

class ComprehensiveWalletScanner:
    def __init__(self):
        self.wallet_extensions = ['.dat', '.wallet', '.key', '.json', '.txt', '.log', '.conf', '.cfg', '.ini', '.bak']
        self.wallet_patterns = [
            r'wallet', r'bitcoin', r'ethereum', r'crypto', r'seed', r'mnemonic',
            r'private.*key', r'keystore', r'metamask', r'exodus', r'electrum',
            r'atomic', r'trust.*wallet', r'coinbase'
        ]
        self.leveldb_indicators = ['CURRENT', 'MANIFEST', '.ldb', '.log']
        
        # Patterns for private keys and addresses
        self.private_key_patterns = [
            # Bitcoin WIF format (51-52 chars starting with K, L, or 5)
            (r'\b[KL5][1-9A-HJ-NP-Za-km-z]{50,51}\b', 'Bitcoin WIF'),
            # Ethereum private key (64 hex chars, often with 0x prefix)
            (r'\b(?:0x)?[0-9a-fA-F]{64}\b', 'Hex Private Key'),
            # Bitcoin private key (64 hex chars)
            (r'\b[0-9a-fA-F]{64}\b', 'Hex Private Key')
        ]
        
        self.address_patterns = [
            # Bitcoin legacy addresses (starts with 1)
            (r'\b1[1-9A-HJ-NP-Za-km-z]{25,34}\b', 'Bitcoin Legacy'),
            # Bitcoin segwit addresses (starts with 3)
            (r'\b3[1-9A-HJ-NP-Za-km-z]{25,34}\b', 'Bitcoin SegWit'),
            # Bitcoin bech32 addresses (starts with bc1)
            (r'\bbc1[a-zA-HJ-NP-Z0-9]{25,39}\b', 'Bitcoin Bech32'),
            # Ethereum addresses (0x followed by 40 hex chars)
            (r'\b0x[a-fA-F0-9]{40}\b', 'Ethereum')
        ]
        
        # Results storage
        self.results = {
            'scan_summary': {},
            'interesting_files': [],
            'private_keys_found': [],
            'addresses_found': [],
            'potential_wallet_files': []
        }
        
    def is_valid_private_key(self, key_string, key_type):
        """Validate if a string is a valid private key"""
        if not CRYPTO_LIBS_AVAILABLE:
            return True  # Assume valid if we can't validate
            
        try:
            # Clean the key (remove 0x prefix if present)
            clean_key = key_string.replace('0x', '')
            
            if key_type == 'Bitcoin WIF' and len(clean_key) in [51, 52]:
                try:
                    WifDecoder.Decode(clean_key)
                    return True
                except:
                    return False
                    
            elif key_type == 'Hex Private Key' and len(clean_key) == 64:
                # Check if it's valid hex and in valid range for private key
                try:
                    key_int = int(clean_key, 16)
                    # Must be > 0 and < secp256k1 curve order
                    if 0 < key_int < 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141:
                        return True
                except:
                    pass
                    
            return False
        except:
            return False
            
    def extract_addresses_from_private_key(self, private_key, key_type):
        """Extract corresponding addresses from a private key"""
        addresses = []
        
        if not CRYPTO_LIBS_AVAILABLE:
            return addresses
            
        try:
            clean_key = private_key.replace('0x', '')
            
            if key_type == 'Bitcoin WIF':
                # Generate Bitcoin address from WIF
                try:
                    decoded = WifDecoder.Decode(clean_key)
                    bip44_mst_ctx = Bip44.FromSeed(decoded, Bip44Coins.BITCOIN)
                    bip44_acc_ctx = bip44_mst_ctx.Purpose().Coin().Account(0)
                    bip44_chg_ctx = bip44_acc_ctx.Change(Bip44Changes.CHAIN_EXT)
                    bip44_addr_ctx = bip44_chg_ctx.AddressIndex(0)
                    addresses.append(('Bitcoin', bip44_addr_ctx.PublicKey().ToAddress()))
                except Exception as e:
                    print(f"      ⚠️  Error generating Bitcoin address: {e}")
                    
            elif key_type == 'Hex Private Key' and len(clean_key) == 64:
                # Try as Ethereum private key
                try:
                    eth_key = eth_keys.PrivateKey(bytes.fromhex(clean_key))
                    eth_address = to_checksum_address(eth_key.public_key.to_address())
                    addresses.append(('Ethereum', eth_address))
                except Exception as e:
                    print(f"      ⚠️  Error generating Ethereum address: {e}")
                    
                # Try as Bitcoin private key (convert to WIF first)
                try:
                    key_bytes = bytes.fromhex(clean_key)
                    wif_key = WifEncoder.Encode(key_bytes)
                    decoded = WifDecoder.Decode(wif_key)
                    bip44_mst_ctx = Bip44.FromSeed(decoded, Bip44Coins.BITCOIN)
                    bip44_acc_ctx = bip44_mst_ctx.Purpose().Coin().Account(0)
                    bip44_chg_ctx = bip44_acc_ctx.Change(Bip44Changes.CHAIN_EXT)
                    bip44_addr_ctx = bip44_chg_ctx.AddressIndex(0)
                    addresses.append(('Bitcoin', bip44_addr_ctx.PublicKey().ToAddress()))
                except Exception as e:
                    print(f"      ⚠️  Error generating Bitcoin address from hex: {e}")
                    
        except Exception as e:
            print(f"      ⚠️  Error processing private key: {e}")
            
        return addresses
        
    def scan_file_for_keys_and_addresses(self, file_path, file_size):
        """Scan a file's content for private keys and addresses"""
        max_file_size = 10 * 1024 * 1024  # 10MB limit
        
        if file_size > max_file_size:
            print(f"        ⚠️  File too large ({self._format_size(file_size)}) - skipping content scan")
            return
            
        try:
            # Try to read the file content
            content = ""
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read(max_file_size)  # Limit read size
            except:
                # Try binary mode if text mode fails
                with open(file_path, 'rb') as f:
                    raw_content = f.read(max_file_size)
                    content = raw_content.decode('utf-8', errors='ignore')
                    
            if len(content) < 10:  # Skip very small files
                return
                
            print(f"        🔍 Scanning content ({len(content):,} chars)...")
            
            # Look for private keys
            keys_found = 0
            for pattern, key_type in self.private_key_patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    if self.is_valid_private_key(match, key_type):
                        keys_found += 1
                        print(f"        🔑 PRIVATE KEY FOUND: {match[:10]}...{match[-10:]} ({key_type})")
                        
                        key_info = {
                            'key_preview': match[:10] + '...' + match[-10:],
                            'key_type': key_type,
                            'file_path': file_path,
                            'full_key': match  # Store full key for address generation
                        }
                        self.results['private_keys_found'].append(key_info)
                        
                        # Generate addresses from this private key
                        addresses = self.extract_addresses_from_private_key(match, key_type)
                        for chain, address in addresses:
                            print(f"          → {chain} Address: {address}")
                            addr_info = {
                                'address': address,
                                'chain': chain,
                                'source': 'generated_from_private_key',
                                'private_key_preview': match[:10] + '...' + match[-10:],
                                'file_path': file_path
                            }
                            self.results['addresses_found'].append(addr_info)
                            
            # Look for standalone addresses
            addresses_found = 0
            for pattern, addr_type in self.address_patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    addresses_found += 1
                    print(f"        📍 ADDRESS FOUND: {match} ({addr_type})")
                    
                    addr_info = {
                        'address': match,
                        'chain': addr_type,
                        'source': 'standalone_in_file',
                        'private_key_preview': None,
                        'file_path': file_path
                    }
                    self.results['addresses_found'].append(addr_info)
                    
            if keys_found == 0 and addresses_found == 0:
                print(f"        ℹ️  No keys or addresses found in content")
                
        except Exception as e:
            print(f"        ⚠️  Error scanning file content: {e}")
    
    def scan_directory(self, root_path, max_depth=5):
        """Scan directory with comprehensive analysis"""
        print(f"🔍 Starting comprehensive wallet scan of: {root_path}")
        print(f"📊 Max depth: {max_depth} levels")
        print("=" * 80)
        
        total_files = 0
        wallet_files = 0
        leveldb_dirs = 0
        
        try:
            for root, dirs, files in os.walk(root_path):
                # Calculate current depth
                depth = root.replace(root_path, '').count(os.sep)
                if depth > max_depth:
                    dirs[:] = []  # Don't go deeper
                    continue
                    
                indent = "  " * depth
                print(f"\n{indent}📁 {os.path.basename(root) or root}")
                print(f"{indent}   📊 {len(dirs)} directories, {len(files)} files")
                
                # Check if this is a LevelDB directory
                leveldb_files = [f for f in files if any(indicator in f for indicator in self.leveldb_indicators)]
                if leveldb_files:
                    leveldb_dirs += 1
                    print(f"{indent}   🗄️  LevelDB detected! Files: {leveldb_files}")
                
                # Process each file
                for file in files:
                    total_files += 1
                    file_path = os.path.join(root, file)
                    file_size = 0
                    
                    try:
                        file_size = os.path.getsize(file_path)
                    except:
                        pass
                    
                    # Check if file is interesting
                    is_interesting = False
                    reasons = []
                    
                    # Check extension
                    if any(file.lower().endswith(ext) for ext in self.wallet_extensions):
                        is_interesting = True
                        reasons.append("wallet extension")
                    
                    # Check filename patterns
                    for pattern in self.wallet_patterns:
                        if re.search(pattern, file.lower()):
                            is_interesting = True
                            reasons.append(f"matches '{pattern}'")
                            break
                    
                    # Check if it's a LevelDB file
                    if any(indicator in file for indicator in self.leveldb_indicators):
                        is_interesting = True
                        reasons.append("LevelDB file")
                    
                    if is_interesting:
                        wallet_files += 1
                        size_str = self._format_size(file_size)
                        print(f"{indent}   🎯 {file} ({size_str}) - {', '.join(reasons)}")
                        
                        # Store interesting file info
                        file_info = {
                            'path': file_path,
                            'filename': file,
                            'size': file_size,
                            'reasons': reasons
                        }
                        self.results['interesting_files'].append(file_info)
                        
                        # Scan content for keys/addresses if it's a text-based file
                        if any(file.lower().endswith(ext) for ext in ['.txt', '.json', '.dat', '.key', '.log', '.conf']):
                            self.scan_file_for_keys_and_addresses(file_path, file_size)
                            
                    elif file_size > 1024 * 1024:  # Show large files (>1MB)
                        size_str = self._format_size(file_size)
                        print(f"{indent}   📄 {file} ({size_str})")
                    elif len(files) < 20:  # Show all files if not too many
                        size_str = self._format_size(file_size)
                        print(f"{indent}   📄 {file} ({size_str})")
                
                # Limit output for very large directories
                if len(files) > 100:
                    print(f"{indent}   ⚠️  Large directory - showing only interesting files")
                    
        except KeyboardInterrupt:
            print("\n⏹️  Scan interrupted by user")
        except Exception as e:
            print(f"\n❌ Error during scan: {e}")
        
        # Store summary
        self.results['scan_summary'] = {
            'total_files': total_files,
            'interesting_files': wallet_files,
            'leveldb_directories': leveldb_dirs,
            'private_keys_found': len(self.results['private_keys_found']),
            'addresses_found': len(self.results['addresses_found'])
        }
        
        self.print_comprehensive_summary()
        self.save_results()
        
        return self.results
    
    def print_comprehensive_summary(self):
        """Print detailed summary of all findings"""
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE SCAN SUMMARY")
        print("=" * 80)
        
        summary = self.results['scan_summary']
        print(f"📁 Total files scanned: {summary['total_files']:,}")
        print(f"🎯 Interesting files found: {summary['interesting_files']}")
        print(f"🗄️  LevelDB directories: {summary['leveldb_directories']}")
        print(f"🔑 Private keys found: {summary['private_keys_found']}")
        print(f"📍 Addresses found: {summary['addresses_found']}")
        print()
        
        if self.results['private_keys_found']:
            print("🔑 PRIVATE KEYS DISCOVERED:")
            print("-" * 40)
            for i, key_info in enumerate(self.results['private_keys_found'], 1):
                print(f"{i:3d}. {key_info['key_preview']} ({key_info['key_type']})")
                print(f"     File: {key_info['file_path']}")
                print()
        
        if self.results['addresses_found']:
            print("📍 ADDRESSES DISCOVERED:")
            print("-" * 40)
            for i, addr_info in enumerate(self.results['addresses_found'], 1):
                print(f"{i:3d}. {addr_info['address']} ({addr_info['chain']})")
                print(f"     Source: {addr_info['source']}")
                if addr_info['private_key_preview']:
                    print(f"     Private Key: {addr_info['private_key_preview']}")
                print(f"     File: {addr_info['file_path']}")
                print()
        
        if self.results['interesting_files']:
            print("🎯 ALL INTERESTING FILES:")
            print("-" * 40)
            for i, file_info in enumerate(self.results['interesting_files'], 1):
                print(f"{i:3d}. {file_info['filename']}")
                print(f"     Path: {file_info['path']}")
                print(f"     Size: {self._format_size(file_info['size'])}")
                print(f"     Reasons: {', '.join(file_info['reasons'])}")
                print()
    
    def save_results(self):
        """Save all results to JSON file"""
        # Remove full private keys from saved results for security
        safe_results = self.results.copy()
        for key_info in safe_results['private_keys_found']:
            if 'full_key' in key_info:
                del key_info['full_key']
        
        output_file = "comprehensive_wallet_scan_results.json"
        try:
            with open(output_file, 'w') as f:
                json.dump(safe_results, f, indent=2)
            print(f"💾 Results saved to: {output_file}")
        except Exception as e:
            print(f"⚠️  Error saving results: {e}")
    
    def _format_size(self, size_bytes):
        """Format file size in human readable format"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.1f} {size_names[i]}"

def main():
    if len(sys.argv) != 2:
        print("Usage: python verbose_file_scanner.py <directory_path>")
        print("Example: python verbose_file_scanner.py /mnt/windows_drive")
        sys.exit(1)
    
    scan_path = sys.argv[1]
    
    if not os.path.exists(scan_path):
        print(f"❌ Directory not found: {scan_path}")
        sys.exit(1)
    
    scanner = ComprehensiveWalletScanner()
    results = scanner.scan_directory(scan_path)
    
    print(f"\n🎉 Comprehensive scan complete!")
    print(f"   Found {results['scan_summary']['private_keys_found']} private keys")
    print(f"   Found {results['scan_summary']['addresses_found']} addresses")
    print(f"   Found {results['scan_summary']['interesting_files']} interesting files")
    
    if results['private_keys_found'] or results['addresses_found']:
        print("\n🔥 WALLET DATA DISCOVERED! Check the summary above for details.")
        print("💡 Next steps:")
        print("1. Review private keys and addresses found")
        print("2. Check balances using enhanced_balance_checker.py")
        print("3. Secure any valuable keys immediately")

if __name__ == "__main__":
    main()
                for file in files:
                    total_files += 1
                    file_path = os.path.join(root, file)
                    file_size = 0
                    
                    try:
                        file_size = os.path.getsize(file_path)
                    except:
                        pass
                    
                    # Check if file is interesting
                    is_interesting = False
                    reasons = []
                    
                    # Check extension
                    if any(file.lower().endswith(ext) for ext in self.wallet_extensions):
                        is_interesting = True
                        reasons.append("wallet extension")
                    
                    # Check filename patterns
                    for pattern in self.wallet_patterns:
                        if re.search(pattern, file.lower()):
                            is_interesting = True
                            reasons.append(f"matches '{pattern}'")
                            break
                    
                    # Check if it's a LevelDB file
                    if any(indicator in file for indicator in self.leveldb_indicators):
                        is_interesting = True
                        reasons.append("LevelDB file")
                    
                    if is_interesting:
                        wallet_files += 1
                        interesting_files.append({
                            'path': file_path,
                            'size': file_size,
                            'reasons': reasons
                        })
                        size_str = self._format_size(file_size)
                        print(f"{indent}   🎯 {file} ({size_str}) - {', '.join(reasons)}")
                    elif file_size > 1024 * 1024:  # Show large files (>1MB)
                        size_str = self._format_size(file_size)
                        print(f"{indent}   📄 {file} ({size_str})")
                    elif len(files) < 20:  # Show all files if not too many
                        size_str = self._format_size(file_size)
                        print(f"{indent}   📄 {file} ({size_str})")
                
                # Limit output for very large directories
                if len(files) > 100:
                    print(f"{indent}   ⚠️  Large directory - showing only interesting files")
                    
        except KeyboardInterrupt:
            print("\n⏹️  Scan interrupted by user")
        except Exception as e:
            print(f"\n❌ Error during scan: {e}")
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 SCAN SUMMARY")
        print("=" * 80)
        print(f"📁 Total files scanned: {total_files:,}")
        print(f"🎯 Interesting files found: {wallet_files}")
        print(f"🗄️  LevelDB directories: {leveldb_dirs}")
        print()
        
        if interesting_files:
            print("🎯 DETAILED INTERESTING FILES:")
            print("-" * 40)
            for i, file_info in enumerate(interesting_files, 1):
                print(f"{i:3d}. {file_info['path']}")
                print(f"     Size: {self._format_size(file_info['size'])}")
                print(f"     Reasons: {', '.join(file_info['reasons'])}")
                print()
        
        return interesting_files
    
    def _format_size(self, size_bytes):
        """Format file size in human readable format"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.1f} {size_names[i]}"

def main():
    if len(sys.argv) != 2:
        print("Usage: python verbose_file_scanner.py <directory_path>")
        print("Example: python verbose_file_scanner.py /mnt/windows_drive")
        sys.exit(1)
    
    scan_path = sys.argv[1]
    
    if not os.path.exists(scan_path):
        print(f"❌ Directory not found: {scan_path}")
        sys.exit(1)
    
    scanner = VerboseFileScanner()
    interesting_files = scanner.scan_directory(scan_path)
    
    print(f"\n🎉 Scan complete! Found {len(interesting_files)} interesting files.")
    
    if interesting_files:
        print("\n💡 Next steps:")
        print("1. Review the interesting files listed above")
        print("2. Use unified_wallet_scanner.py for LevelDB directories")
        print("3. Manually examine any .txt, .dat, or .json files for wallet data")

if __name__ == "__main__":
    main()
