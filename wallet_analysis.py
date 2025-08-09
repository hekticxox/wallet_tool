#!/usr/bin/env python3
"""
Crypto Wallet Recovery Tool - Main Analysis Module

This tool extracts cryptocurrency private keys, seed phrases, and wallet addresses
from LevelDB database files. It supports Bitcoin, Ethereum, and Solana networks.

Author: Crypto Recovery Tools
License: MIT
"""

import json
import re
import requests
import os
import time
from glob import glob
from bip_utils import (
    Bip39MnemonicValidator, Bip39MnemonicDecoder, Bip44, Bip44Coins,
    WifDecoder, Bip32Slip10Secp256k1
)
from eth_keys import keys as eth_keys
from eth_utils import to_checksum_address
from solders.keypair import Keypair as SolanaKeypair
from solana.rpc.api import Client as SolanaClient
import plyvel

def get_ldb_directory():
    """Get LevelDB directory from user input with validation."""
    print("🔍 Crypto Wallet Recovery Tool")
    print("=============================")
    print("This tool will analyze LevelDB databases for wallet data.")
    print()
    
    while True:
        ldb_dir = input("Enter the path to directory containing .ldb files: ").strip()
        if os.path.isdir(ldb_dir):
            return ldb_dir
        print(f"❌ Directory '{ldb_dir}' not found. Please try again.")

def is_leveldb_dir(path):
    """Check if directory contains LevelDB files."""
    if not os.path.isdir(path):
        return False
    files = os.listdir(path)
    has_current = 'CURRENT' in files
    has_ldb = any(f.endswith('.ldb') for f in files)
    return has_current and has_ldb

def find_leveldb_directories(root_dir):
    """Recursively find all LevelDB database directories."""
    print(f"🔍 Scanning {root_dir} for LevelDB databases...")
    leveldb_dirs = []
    
    for root, dirs, files in os.walk(root_dir):
        for d in dirs:
            full_path = os.path.join(root, d)
            if is_leveldb_dir(full_path):
                leveldb_dirs.append(full_path)
                
    if not leveldb_dirs:
        print(f"❌ No LevelDB databases found in {root_dir}")
        return None
        
    print(f"✅ Found {len(leveldb_dirs)} LevelDB database(s)")
    return leveldb_dirs

def extract_data_from_databases(leveldb_dirs):
    """Extract readable data from LevelDB databases."""
    data = []
    MAX_ENTRIES_PER_DB = 10000
    
    for i, db_dir in enumerate(leveldb_dirs, 1):
        print(f"📂 Processing database {i}/{len(leveldb_dirs)}: {os.path.basename(db_dir)}")
        
        try:
            db = plyvel.DB(db_dir, create_if_missing=False)
        except Exception as e:
            if 'idb_cmp1' in str(e):
                print(f"⏭️  Skipping IndexedDB: {os.path.basename(db_dir)}")
                continue
            print(f"❌ Error opening {db_dir}: {e}")
            continue
            
        count = 0
        start_time = time.time()
        
        try:
            for k, v in db:
                try:
                    val_decoded = v.decode('utf-8', errors='replace')
                except Exception:
                    val_decoded = repr(v)
                    
                data.append({
                    'key': k.hex(),
                    'value': v.hex(),
                    'value_decoded': val_decoded,
                    'ldb_dir': db_dir
                })
                
                count += 1
                if count >= MAX_ENTRIES_PER_DB:
                    print(f"⚠️  Reached {MAX_ENTRIES_PER_DB} entries limit")
                    break
                    
                if time.time() - start_time > 30:
                    print(f"⚠️  Timeout after 30 seconds")
                    break
                    
            db.close()
            print(f"✅ Extracted {count} entries")
            
        except Exception as e:
            print(f"❌ Error reading {db_dir}: {e}")
            db.close()
            continue
            
    return data

# === Cryptographic Helper Functions ===

mnemonic_validator = Bip39MnemonicValidator()

def extract_mnemonics(text, max_candidates=1000):
    """Extract BIP39 mnemonic phrases from text."""
    words = re.split(r'[\s\n\r]+', text.strip())
    found_mnemonics = []
    checked = 0
    
    for length in range(12, 25):
        for i in range(len(words) - length + 1):
            if checked >= max_candidates:
                return found_mnemonics
            
            candidate = words[i:i+length]
            phrase = ' '.join(candidate)
            
            if mnemonic_validator.IsValid(phrase):
                found_mnemonics.append(phrase)
                
            checked += 1
            
    return found_mnemonics

def looks_like_private_key(s):
    """Check if string looks like a hex private key."""
    return bool(re.fullmatch(r'[0-9a-fA-F]{64}', s))

def eth_privkey_to_address(privkey_hex):
    """Convert Ethereum private key to address."""
    priv_bytes = bytes.fromhex(privkey_hex)
    pk = eth_keys.PrivateKey(priv_bytes)
    return to_checksum_address(pk.public_key.to_address())

def solana_privkey_to_pubkey(privkey_hex):
    """Convert Solana private key to public key."""
    priv_bytes = bytes.fromhex(privkey_hex)
    
    if len(priv_bytes) == 64:
        kp = SolanaKeypair.from_bytes(priv_bytes)
    elif len(priv_bytes) == 32:
        from nacl.signing import SigningKey
        signing_key = SigningKey(priv_bytes)
        kp = SolanaKeypair.from_bytes(signing_key._seed + signing_key.verify_key.encode())
    else:
        return None
        
    return str(kp.pubkey())

def bitcoin_wif_to_address(wif):
    """Convert Bitcoin WIF private key to address."""
    try:
        priv_key_bytes, _ = WifDecoder.Decode(wif)
        bip44_ctx = Bip44.FromPrivateKey(priv_key_bytes, Bip44Coins.BITCOIN)
        return bip44_ctx.PublicKey().ToAddress()
    except Exception:
        return None

def privkey_hex_to_btc_address(privkey_hex):
    """Convert hex private key to Bitcoin address."""
    try:
        bip44_mst = Bip44.FromPrivateKey(bytes.fromhex(privkey_hex), Bip44Coins.BITCOIN)
        return bip44_mst.PublicKey().ToAddress()
    except Exception:
        return None

def is_ethereum_address(addr):
    """Validate Ethereum address format."""
    return bool(re.fullmatch(r'0x[a-fA-F0-9]{40}', addr))

# === Balance Checking Functions ===

def get_eth_balance(address):
    """Get Ethereum balance via Etherscan API."""
    retries = 3
    for attempt in range(retries):
        try:
            url = f"https://api.etherscan.io/api?module=account&action=balance&address={address}&tag=latest&apikey=YourApiKeyToken"
            r = requests.get(url, timeout=15)
            result = r.json()
            
            if result.get('status') == '1':
                wei = int(result['result'])
                return wei / 1e18
                
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
            else:
                print(f"⚠️  ETH balance error for {address[:10]}...: {e}")
                
    return None

def get_btc_balance(address):
    """Get Bitcoin balance via Blockstream API."""
    retries = 3
    for attempt in range(retries):
        try:
            url = f"https://blockstream.info/api/address/{address}"
            r = requests.get(url, timeout=15)
            
            if r.status_code == 200:
                data = r.json()
                balance_sat = (data.get('chain_stats', {}).get('funded_txo_sum', 0) - 
                              data.get('chain_stats', {}).get('spent_txo_sum', 0))
                return balance_sat / 1e8
            else:
                raise Exception(f"HTTP {r.status_code}")
                
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
            else:
                print(f"⚠️  BTC balance error for {address[:10]}...: {e}")
                
    return None

# === Address Validation Functions ===

def is_valid_eth_address(addr):
    """Strict Ethereum address validation."""
    if not isinstance(addr, str):
        return False
    if not re.fullmatch(r"0x[a-fA-F0-9]{40}", addr):
        return False
    try:
        return addr == to_checksum_address(addr)
    except Exception:
        return False

def is_valid_btc_address(addr):
    """Strict Bitcoin address validation."""
    if not isinstance(addr, str):
        return False
        
    # Legacy P2PKH
    if re.fullmatch(r"1[1-9A-HJ-NP-Za-km-z]{25,34}", addr):
        return True
    # Script P2SH  
    if re.fullmatch(r"3[1-9A-HJ-NP-Za-km-z]{25,34}", addr):
        return True
    # Bech32 P2WPKH/P2WSH
    if re.fullmatch(r"bc1[0-9a-z]{39,59}", addr):
        return True
        
    return False

def analyze_wallet_data(data):
    """Main analysis function to extract wallet information."""
    print("🔍 Analyzing extracted data for wallet information...")
    
    # Data containers
    mnemonics = set()
    private_keys = set()
    detected_addresses = {
        "ethereum": set(),
        "bitcoin": set(), 
        "solana": set(),
        "unknown": set(),
    }
    privkey_to_addresses = {}
    
    # Progress tracking
    progress_interval = max(1, len(data) // 50)
    
    for idx, entry in enumerate(data):
        if idx % progress_interval == 0:
            print(f"📊 Progress: {idx+1}/{len(data)} entries...")
            
        val = entry.get('value_decoded') or entry.get('value') or ''
        if not val:
            continue
            
        # Extract mnemonics
        found_mnemonics = extract_mnemonics(val, max_candidates=1000)
        mnemonics.update(found_mnemonics)
        
        # Find hex private keys (64 hex chars)
        privkey_hex_matches = re.findall(r'\b[0-9a-fA-F]{64}\b', val)
        # Find WIF private keys (Bitcoin)
        wif_matches = re.findall(r'\b[5KL][1-9A-HJ-NP-Za-km-z]{50,51}\b', val)
        
        # Process hex private keys
        for privkey_hex in privkey_hex_matches:
            try:
                priv_bytes = bytes.fromhex(privkey_hex)
                if len(priv_bytes) not in [32, 64]:
                    continue
            except Exception:
                continue
                
            private_keys.add(privkey_hex)
            
            # Generate addresses for each chain
            addresses = {}
            
            try:
                eth_addr = eth_privkey_to_address(privkey_hex)
                detected_addresses["ethereum"].add(eth_addr)
                addresses["ethereum"] = eth_addr
            except Exception:
                pass
                
            try:
                sol_addr = solana_privkey_to_pubkey(privkey_hex)
                if sol_addr:
                    detected_addresses["solana"].add(sol_addr)
                    addresses["solana"] = sol_addr
            except Exception:
                pass
                
            try:
                btc_addr = privkey_hex_to_btc_address(privkey_hex)
                if btc_addr:
                    detected_addresses["bitcoin"].add(btc_addr)
                    addresses["bitcoin"] = btc_addr
            except Exception:
                pass
                
            privkey_to_addresses[privkey_hex] = addresses
            
        # Process WIF private keys
        for wif in wif_matches:
            private_keys.add(wif)
            btc_addr = bitcoin_wif_to_address(wif)
            if btc_addr:
                detected_addresses["bitcoin"].add(btc_addr)
                privkey_to_addresses[wif] = {"bitcoin": btc_addr}
                
        # Extract addresses directly from text
        eth_addrs = re.findall(r'0x[a-fA-F0-9]{40}', val)
        for addr in eth_addrs:
            detected_addresses["ethereum"].add(to_checksum_address(addr))
            
        btc_addrs = re.findall(r'\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b', val)
        for addr in btc_addrs:
            detected_addresses["bitcoin"].add(addr)
    
    return mnemonics, private_keys, detected_addresses, privkey_to_addresses

def sample_balance_check(detected_addresses, limit=10):
    """Check balances for a small sample of addresses."""
    print("💰 Checking sample balances...")
    
    balances = {"ethereum": {}, "bitcoin": {}}
    
    # Filter valid addresses
    eth_addrs = [a for a in detected_addresses["ethereum"] if is_valid_eth_address(a)]
    btc_addrs = [a for a in detected_addresses["bitcoin"] if is_valid_btc_address(a)]
    
    # Update detected addresses with only valid ones
    detected_addresses["ethereum"] = set(eth_addrs)
    detected_addresses["bitcoin"] = set(btc_addrs)
    
    # Check sample Ethereum balances
    print(f"🔸 Checking {min(limit, len(eth_addrs))} Ethereum addresses...")
    for addr in eth_addrs[:limit]:
        bal = get_eth_balance(addr)
        if bal is not None:
            balances["ethereum"][addr] = bal
            if bal > 0:
                print(f"💰 Found ETH balance: {addr} = {bal} ETH")
        time.sleep(1)  # Rate limiting
    
    # Check sample Bitcoin balances  
    print(f"🔸 Checking {min(limit, len(btc_addrs))} Bitcoin addresses...")
    for addr in btc_addrs[:limit]:
        bal = get_btc_balance(addr)
        if bal is not None:
            balances["bitcoin"][addr] = bal
            if bal > 0:
                print(f"💰 Found BTC balance: {addr} = {bal} BTC")
        time.sleep(1)  # Rate limiting
        
    return balances

def save_results(mnemonics, private_keys, detected_addresses, privkey_to_addresses, balances, data):
    """Save all results to JSON files."""
    print("💾 Saving results...")
    
    # Create comprehensive summary
    summary = {
        "analysis_timestamp": time.time(),
        "mnemonics": list(mnemonics),
        "private_keys": list(private_keys),
        "detected_addresses": {k: list(v) for k, v in detected_addresses.items()},
        "cross_check_results": [
            {
                "private_key": priv,
                "chain": chain, 
                "address": addr,
                "matched": addr in detected_addresses.get(chain, [])
            }
            for priv, addrs in privkey_to_addresses.items() 
            for chain, addr in addrs.items() if addr
        ],
        "balances": balances,
        "statistics": {
            "total_mnemonics": len(mnemonics),
            "total_private_keys": len(private_keys),
            "total_ethereum_addresses": len(detected_addresses["ethereum"]),
            "total_bitcoin_addresses": len(detected_addresses["bitcoin"]),
            "total_solana_addresses": len(detected_addresses["solana"])
        }
    }
    
    # Save summary
    with open('detected_wallet_data_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    print("✅ Summary saved to: detected_wallet_data_summary.json")
    
    # Save raw data  
    with open('filtered_wallet_entries.json', 'w') as f:
        json.dump(data, f, indent=2)
    print("✅ Raw data saved to: filtered_wallet_entries.json")
    
    return summary

def display_summary(summary):
    """Display analysis summary."""
    print("\n" + "="*50)
    print("📊 WALLET RECOVERY ANALYSIS SUMMARY")
    print("="*50)
    
    stats = summary["statistics"]
    
    print(f"🔑 Mnemonic phrases found: {stats['total_mnemonics']}")
    if summary["mnemonics"]:
        for i, mnemonic in enumerate(summary["mnemonics"][:3], 1):
            print(f"    {i}. {mnemonic}")
        if len(summary["mnemonics"]) > 3:
            print(f"    ... and {len(summary['mnemonics']) - 3} more")
    
    print(f"\n🔐 Private keys found: {stats['total_private_keys']}")
    
    print(f"\n📍 Addresses discovered:")
    print(f"    • Ethereum: {stats['total_ethereum_addresses']:,}")
    print(f"    • Bitcoin: {stats['total_bitcoin_addresses']:,}")  
    print(f"    • Solana: {stats['total_solana_addresses']:,}")
    
    # Show controlled addresses
    controlled_count = len(summary["cross_check_results"])
    print(f"\n🎯 Controlled addresses (with private keys): {controlled_count:,}")
    
    # Show sample balances
    total_balances = sum(len(bal) for bal in summary["balances"].values())
    if total_balances > 0:
        print(f"\n💰 Sample balance check results:")
        for chain, balances in summary["balances"].items():
            if balances:
                print(f"    {chain.capitalize()}:")
                for addr, bal in list(balances.items())[:3]:
                    print(f"        {addr[:20]}... = {bal}")
    
    print(f"\n📁 Next steps:")
    print(f"    1. Review results in 'detected_wallet_data_summary.json'")
    print(f"    2. Run 'python continuous_checker.py' to check all balances")
    print(f"    3. Check 'FUNDED_ADDRESSES.txt' for any found funds")

def main():
    """Main execution function."""
    try:
        # Get LevelDB directory from user
        ldb_dir = get_ldb_directory()
        
        # Find all LevelDB databases
        leveldb_dirs = find_leveldb_directories(ldb_dir)
        if not leveldb_dirs:
            return
            
        # Extract data from databases
        data = extract_data_from_databases(leveldb_dirs)
        if not data:
            print("❌ No data extracted from databases")
            return
            
        print(f"✅ Total entries extracted: {len(data)}")
        
        # Analyze wallet data
        mnemonics, private_keys, detected_addresses, privkey_to_addresses = analyze_wallet_data(data)
        
        # Sample balance checking
        balances = sample_balance_check(detected_addresses, limit=10)
        
        # Save results
        summary = save_results(mnemonics, private_keys, detected_addresses, 
                             privkey_to_addresses, balances, data)
        
        # Display summary
        display_summary(summary)
        
        print(f"\n🎉 Analysis complete! Use './monitor_checker.sh' to track balance checking progress.")
        
    except KeyboardInterrupt:
        print("\n⚠️  Analysis interrupted by user")
    except Exception as e:
        print(f"❌ Error during analysis: {e}")

if __name__ == "__main__":
    main()
