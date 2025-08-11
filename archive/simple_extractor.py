#!/usr/bin/env python3
"""
Simple Private Key & Address Extractor
Extracts all private keys and addresses from LevelDB directories without any complexity
"""

import os
import json
import time
import re
import plyvel
from bip_utils import WifEncoder, WifDecoder, Bip44, Bip44Coins, Bip44Changes
from eth_keys import keys as eth_keys
from eth_utils import to_checksum_address

def find_leveldb_directories(root_path):
    """Find all LevelDB directories"""
    print(f"🔍 Searching for LevelDB directories in: {root_path}")
    leveldb_dirs = []
    
    for root, dirs, files in os.walk(root_path):
        # Check if this looks like a LevelDB directory
        if any(f.endswith('.ldb') for f in files) or 'CURRENT' in files:
            leveldb_dirs.append(root)
            print(f"  📁 Found: {root}")
    
    print(f"📊 Total LevelDB directories found: {len(leveldb_dirs)}")
    return leveldb_dirs

def extract_private_keys(data_string):
    """Extract potential private keys from string data"""
    private_keys = []
    
    # Look for 64-character hex strings (32 bytes = 64 hex chars)
    hex_pattern = re.compile(r'[0-9a-fA-F]{64}')
    hex_matches = hex_pattern.findall(data_string)
    
    for match in hex_matches:
        try:
            # Validate as private key (must be < secp256k1 curve order)
            key_int = int(match, 16)
            if 1 <= key_int <= 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364140:
                private_keys.append(match.lower())
        except:
            continue
    
    return list(set(private_keys))  # Remove duplicates

def generate_addresses_from_private_key(private_key_hex):
    """Generate Bitcoin and Ethereum addresses from private key"""
    addresses = {}
    
    try:
        # Bitcoin addresses
        key_bytes = bytes.fromhex(private_key_hex)
        
        # Bitcoin compressed
        try:
            bip44_mst_ctx = Bip44.FromSeed(key_bytes, Bip44Coins.BITCOIN)
            bip44_acc_ctx = bip44_mst_ctx.Purpose().Coin().Account(0)
            bip44_chg_ctx = bip44_acc_ctx.Change(Bip44Changes.CHAIN_EXT)
            bip44_addr_ctx = bip44_chg_ctx.AddressIndex(0)
            addresses['bitcoin'] = bip44_addr_ctx.PublicKey().ToAddress()
        except:
            pass
        
        # Ethereum address
        try:
            private_key_obj = eth_keys.PrivateKey(key_bytes)
            eth_address = private_key_obj.public_key.to_checksum_address()
            addresses['ethereum'] = eth_address
        except:
            pass
            
    except Exception as e:
        print(f"  ⚠️ Error generating addresses: {e}")
    
    return addresses

def extract_from_database(db_path, limit=None):
    """Extract from a single LevelDB database"""
    print(f"\n📖 Opening database: {db_path}")
    
    extracted = []
    keys_processed = 0
    
    try:
        db = plyvel.DB(db_path, create_if_missing=False)
        print(f"  ✅ Database opened successfully")
        
        # Count total keys first
        total_keys = sum(1 for _ in db)
        print(f"  📊 Total keys in database: {total_keys:,}")
        
        if limit:
            print(f"  🔄 Processing limit: {limit:,} keys")
        
        # Reset and process
        db.close()
        db = plyvel.DB(db_path, create_if_missing=False)
        
        for key, value in db:
            keys_processed += 1
            
            # Progress every 100 keys
            if keys_processed % 100 == 0:
                pct = (keys_processed / total_keys) * 100 if total_keys > 0 else 0
                print(f"    🔍 Processed {keys_processed:,}/{total_keys:,} keys ({pct:.1f}%) - Found {len(extracted)} addresses")
            
            # Apply limit if set
            if limit and keys_processed > limit:
                print(f"    🔄 Reached processing limit of {limit:,} keys")
                break
            
            try:
                # Decode key and value
                key_str = key.decode('utf-8', errors='ignore')
                value_str = value.decode('utf-8', errors='ignore')
                combined = key_str + value_str
                
                # Extract private keys
                private_keys = extract_private_keys(combined)
                
                # Generate addresses for each private key
                for pk in private_keys:
                    addresses = generate_addresses_from_private_key(pk)
                    
                    for chain, address in addresses.items():
                        extracted.append({
                            'private_key': pk,
                            'address': address,
                            'chain': chain,
                            'source': db_path,
                            'extracted_at': time.time()
                        })
            except Exception as e:
                continue  # Skip problematic entries
        
        db.close()
        print(f"  ✅ Extracted {len(extracted)} addresses from {keys_processed:,} keys")
        
    except Exception as e:
        print(f"  ❌ Database error: {e}")
        
    return extracted

def main():
    """Main extraction function"""
    import sys
    
    print("🚀 SIMPLE PRIVATE KEY & ADDRESS EXTRACTOR")
    print("=" * 50)
    
    # Get directory
    if len(sys.argv) > 1:
        scan_dir = sys.argv[1]
    else:
        scan_dir = input("Enter directory to scan: ").strip()
        if not scan_dir:
            scan_dir = "."
    
    # Get limit
    limit_input = input("Enter key processing limit per database (or press Enter for no limit): ").strip()
    limit = int(limit_input) if limit_input.isdigit() else None
    
    if not os.path.exists(scan_dir):
        print(f"❌ Directory not found: {scan_dir}")
        return
    
    print(f"📂 Scanning directory: {os.path.abspath(scan_dir)}")
    if limit:
        print(f"🔢 Processing limit: {limit:,} keys per database")
    
    # Find databases
    leveldb_dirs = find_leveldb_directories(scan_dir)
    
    if not leveldb_dirs:
        print("❌ No LevelDB directories found!")
        return
    
    all_extracted = []
    
    # Process each database
    for i, db_dir in enumerate(leveldb_dirs, 1):
        print(f"\n📊 Processing database {i}/{len(leveldb_dirs)}")
        
        db_extracted = extract_from_database(db_dir, limit)
        all_extracted.extend(db_extracted)
        
        print(f"  📈 Total extracted so far: {len(all_extracted):,} addresses")
    
    # Remove duplicates
    print(f"\n🔄 Removing duplicates...")
    unique_addresses = {}
    for item in all_extracted:
        key = (item['address'], item['chain'])
        if key not in unique_addresses:
            unique_addresses[key] = item
    
    final_data = list(unique_addresses.values())
    
    # Save results
    output_file = "simple_extraction_results.json"
    with open(output_file, 'w') as f:
        json.dump(final_data, f, indent=2)
    
    # Summary
    print(f"\n🎉 EXTRACTION COMPLETE!")
    print(f"📊 Databases processed: {len(leveldb_dirs)}")
    print(f"🔑 Total addresses extracted: {len(final_data):,}")
    print(f"💾 Results saved to: {output_file}")
    
    # Show breakdown
    chains = {}
    for item in final_data:
        chain = item['chain']
        chains[chain] = chains.get(chain, 0) + 1
    
    print(f"\n📈 Breakdown by chain:")
    for chain, count in sorted(chains.items()):
        print(f"  {chain.upper()}: {count:,} addresses")

if __name__ == "__main__":
    main()
