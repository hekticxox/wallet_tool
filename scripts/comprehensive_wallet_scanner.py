#!/usr/bin/env python3
"""
Comprehensive Wallet Scanner - Scans files for private keys, addresses, and wallet data
Shows detailed verbose output about what's being processed
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
        
        # Patterns for private keys and addresses
        self.private_key_patterns = [
            # Bitcoin WIF format (51-52 chars starting with K, L, or 5)
            (r'\b[KL5][1-9A-HJ-NP-Za-km-z]{50,51}\b', 'Bitcoin WIF'),
            # Ethereum private key (64 hex chars, often with 0x prefix)
            (r'\b(?:0x)?[0-9a-fA-F]{64}\b', 'Hex Private Key')
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
            'private_keys_found': [],
            'addresses_found': [],
            'interesting_files': []
        }
        
    def is_valid_private_key(self, key_string, key_type):
        """Validate if a string is a valid private key"""
        if not CRYPTO_LIBS_AVAILABLE:
            return True  # Assume valid if we can't validate
            
        try:
            clean_key = key_string.replace('0x', '')
            
            if key_type == 'Bitcoin WIF' and len(clean_key) in [51, 52]:
                try:
                    WifDecoder.Decode(clean_key)
                    return True
                except:
                    return False
                    
            elif key_type == 'Hex Private Key' and len(clean_key) == 64:
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
                    decoded_key = WifDecoder.Decode(clean_key)
                    # decoded_key is a tuple (key_bytes, pub_key_mode)
                    key_bytes = decoded_key[0] if isinstance(decoded_key, tuple) else decoded_key
                    wif_key = WifEncoder.Encode(key_bytes)
                    # Create address using the key bytes
                    bip44_mst_ctx = Bip44.FromSeed(key_bytes, Bip44Coins.BITCOIN)
                    bip44_acc_ctx = bip44_mst_ctx.Purpose().Coin().Account(0)
                    bip44_chg_ctx = bip44_acc_ctx.Change(Bip44Changes.CHAIN_EXT)
                    bip44_addr_ctx = bip44_chg_ctx.AddressIndex(0)
                    addresses.append(('Bitcoin', bip44_addr_ctx.PublicKey().ToAddress()))
                except Exception as e:
                    print(f"        ⚠️  Error generating Bitcoin address: {e}")
                    
            elif key_type == 'Hex Private Key' and len(clean_key) == 64:
                # Try as Ethereum private key
                try:
                    eth_key = eth_keys.PrivateKey(bytes.fromhex(clean_key))
                    eth_address = to_checksum_address(eth_key.public_key.to_address())
                    addresses.append(('Ethereum', eth_address))
                except Exception as e:
                    print(f"        ⚠️  Error generating Ethereum address: {e}")
                    
        except Exception as e:
            print(f"        ⚠️  Error processing private key: {e}")
            
        return addresses
        
    def scan_file_content(self, file_path, file_size):
        """Scan a file's content for private keys and addresses"""
        max_file_size = 5 * 1024 * 1024  # 5MB limit
        
        if file_size > max_file_size:
            print(f"          ⚠️  File too large ({self._format_size(file_size)}) - skipping")
            return
            
        try:
            content = ""
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read(max_file_size)
            except:
                with open(file_path, 'rb') as f:
                    raw_content = f.read(max_file_size)
                    content = raw_content.decode('utf-8', errors='ignore')
                    
            if len(content) < 10:
                return
                
            print(f"          🔍 Content scan ({len(content):,} chars)")
            
            # Look for private keys
            keys_found = 0
            for pattern, key_type in self.private_key_patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    if self.is_valid_private_key(match, key_type):
                        keys_found += 1
                        print(f"          🔑 PRIVATE KEY: {match[:8]}...{match[-8:]} ({key_type})")
                        
                        key_info = {
                            'key_preview': match[:8] + '...' + match[-8:],
                            'key_type': key_type,
                            'file_path': file_path,
                            'full_key': match
                        }
                        self.results['private_keys_found'].append(key_info)
                        
                        # Generate addresses
                        addresses = self.extract_addresses_from_private_key(match, key_type)
                        for chain, address in addresses:
                            print(f"            → {chain}: {address}")
                            addr_info = {
                                'address': address,
                                'chain': chain,
                                'source': 'from_private_key',
                                'file_path': file_path
                            }
                            self.results['addresses_found'].append(addr_info)
                            
            # Look for standalone addresses
            addr_found = 0
            for pattern, addr_type in self.address_patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    addr_found += 1
                    print(f"          📍 ADDRESS: {match} ({addr_type})")
                    
                    addr_info = {
                        'address': match,
                        'chain': addr_type,
                        'source': 'standalone',
                        'file_path': file_path
                    }
                    self.results['addresses_found'].append(addr_info)
                    
            if keys_found == 0 and addr_found == 0:
                print(f"          ℹ️  No wallet data found")
                
        except Exception as e:
            print(f"          ⚠️  Scan error: {e}")
    
    def scan_directory(self, root_path, max_depth=4):
        """Scan directory with comprehensive analysis"""
        print(f"🔍 COMPREHENSIVE WALLET SCAN")
        print(f"📂 Target: {root_path}")
        print(f"📊 Max depth: {max_depth} levels")
        print("=" * 80)
        
        total_files = 0
        scanned_files = 0
        
        try:
            for root, dirs, files in os.walk(root_path):
                # Calculate depth
                depth = root.replace(root_path, '').count(os.sep)
                if depth > max_depth:
                    dirs[:] = []
                    continue
                    
                indent = "  " * depth
                rel_path = os.path.relpath(root, root_path) if root != root_path else "."
                print(f"\n{indent}📁 {rel_path}/")
                print(f"{indent}   📊 {len(files)} files, {len(dirs)} subdirs")
                
                for file in files:
                    total_files += 1
                    file_path = os.path.join(root, file)
                    
                    try:
                        file_size = os.path.getsize(file_path)
                    except:
                        file_size = 0
                    
                    file_ext = Path(file).suffix.lower()
                    size_str = self._format_size(file_size)
                    
                    # Check if interesting
                    is_interesting = (
                        file_ext in self.wallet_extensions or
                        any(keyword in file.lower() for keyword in ['wallet', 'key', 'seed', 'mnemonic', 'bitcoin', 'ethereum', 'crypto']) or
                        file_size > 1024  # Files larger than 1KB
                    )
                    
                    if is_interesting:
                        scanned_files += 1
                        print(f"{indent}   🎯 {file} ({size_str})")
                        
                        # Store file info
                        file_info = {
                            'path': file_path,
                            'filename': file,
                            'size': file_size,
                            'extension': file_ext
                        }
                        self.results['interesting_files'].append(file_info)
                        
                        # Scan content if it's a text-based file
                        if file_ext in ['.txt', '.json', '.dat', '.key', '.log', '.conf', '.cfg'] or not file_ext:
                            self.scan_file_content(file_path, file_size)
                    else:
                        print(f"{indent}   📄 {file} ({size_str})")
                
        except KeyboardInterrupt:
            print("\n⏹️  Scan interrupted")
        except Exception as e:
            print(f"\n❌ Scan error: {e}")
        
        # Summary
        self.results['scan_summary'] = {
            'total_files': total_files,
            'scanned_files': scanned_files,
            'private_keys_found': len(self.results['private_keys_found']),
            'addresses_found': len(self.results['addresses_found']),
            'interesting_files': len(self.results['interesting_files'])
        }
        
        self.print_summary()
        self.save_results()
        
    def print_summary(self):
        """Print comprehensive summary"""
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE SCAN RESULTS")
        print("=" * 80)
        
        s = self.results['scan_summary']
        print(f"📁 Total files: {s['total_files']:,}")
        print(f"🎯 Scanned files: {s['scanned_files']:,}")
        print(f"🔑 Private keys found: {s['private_keys_found']}")
        print(f"📍 Addresses found: {s['addresses_found']}")
        print()
        
        if self.results['private_keys_found']:
            print("🔑 PRIVATE KEYS:")
            for i, key in enumerate(self.results['private_keys_found'], 1):
                print(f"  {i}. {key['key_preview']} ({key['key_type']})")
                print(f"     File: {key['file_path']}")
        
        if self.results['addresses_found']:
            print(f"\n📍 ADDRESSES:")
            for i, addr in enumerate(self.results['addresses_found'], 1):
                print(f"  {i}. {addr['address']} ({addr['chain']})")
                print(f"     Source: {addr['source']}")
                print(f"     File: {addr['file_path']}")
    
    def save_results(self):
        """Save results to JSON"""
        # Remove full keys for security
        safe_results = self.results.copy()
        for key_info in safe_results['private_keys_found']:
            key_info.pop('full_key', None)
        
        output_file = "comprehensive_scan_results.json"
        try:
            with open(output_file, 'w') as f:
                json.dump(safe_results, f, indent=2)
            print(f"\n💾 Results saved: {output_file}")
        except Exception as e:
            print(f"⚠️  Save error: {e}")
    
    def _format_size(self, size_bytes):
        """Format file size"""
        if size_bytes == 0:
            return "0 B"
        
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"

def main():
    if len(sys.argv) != 2:
        print("Usage: python comprehensive_wallet_scanner.py <directory>")
        print("Example: python comprehensive_wallet_scanner.py /mnt/windows_drive")
        sys.exit(1)
    
    scan_path = sys.argv[1]
    if not os.path.exists(scan_path):
        print(f"❌ Directory not found: {scan_path}")
        sys.exit(1)
    
    scanner = ComprehensiveWalletScanner()
    scanner.scan_directory(scan_path)
    
    results = scanner.results
    if results['private_keys_found'] or results['addresses_found']:
        print("\n🔥 WALLET DATA FOUND!")
        print("💡 Next steps:")
        print("1. Check balances with enhanced_balance_checker.py")
        print("2. Secure any valuable keys immediately")
    else:
        print("\n✅ Scan complete - no wallet data found")

if __name__ == "__main__":
    main()
