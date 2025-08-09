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

# Prompt user for .ldb directory
ldb_dir = input("Enter the path to the directory containing .ldb files: ").strip()
while not os.path.isdir(ldb_dir):
    print(f"Directory '{ldb_dir}' not found. Please try again.")
    ldb_dir = input("Enter the path to the directory containing .ldb files: ").strip()

# Recursively find all LevelDB database directories in the directory and subdirectories
def is_leveldb_dir(path):
    if not os.path.isdir(path):
        return False
    files = os.listdir(path)
    has_current = 'CURRENT' in files
    has_ldb = any(f.endswith('.ldb') for f in files)
    return has_current and has_ldb

leveldb_dirs = []
for root, dirs, files in os.walk(ldb_dir):
    for d in dirs:
        full_path = os.path.join(root, d)
        if is_leveldb_dir(full_path):
            leveldb_dirs.append(full_path)

if not leveldb_dirs:
    print(f"No LevelDB database directories found in {ldb_dir} or its subdirectories. Exiting.")
    exit(1)

# Extract readable values from LevelDB database directories
data = []
MAX_ENTRIES_PER_DB = 10000
for db_dir in leveldb_dirs:
    try:
        db = plyvel.DB(db_dir, create_if_missing=False)
    except Exception as e:
        if 'idb_cmp1' in str(e):
            print(f"Skipping IndexedDB or unsupported comparator in {db_dir}.")
            continue
        print(f"Error opening {db_dir}: {e}")
        continue
    count = 0
    start_time = time.time()
    try:
        for k, v in db:
            try:
                val_decoded = v.decode('utf-8', errors='replace')
            except Exception:
                val_decoded = repr(v)
            data.append({'key': k.hex(), 'value': v.hex(), 'value_decoded': val_decoded, 'ldb_dir': db_dir})
            count += 1
            if count >= MAX_ENTRIES_PER_DB:
                print(f"Reached {MAX_ENTRIES_PER_DB} entries in {db_dir}, skipping the rest.")
                break
            if time.time() - start_time > 10:
                print(f"Timeout reading {db_dir}, skipping the rest.")
                break
        db.close()
    except Exception as e:
        print(f"Error reading {db_dir}: {e}")
        db.close()
        continue

# --- Helper functions ---
mnemonic_validator = Bip39MnemonicValidator()
def extract_mnemonics(text, max_candidates=1000):
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
    return bool(re.fullmatch(r'[0-9a-fA-F]{64}', s))

def eth_privkey_to_address(privkey_hex):
    priv_bytes = bytes.fromhex(privkey_hex)
    pk = eth_keys.PrivateKey(priv_bytes)
    return to_checksum_address(pk.public_key.to_address())

def solana_privkey_to_pubkey(privkey_hex):
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
    try:
        priv_key_bytes = WifDecoder.Decode(wif)
        bip32_ctx = Bip32Slip10Secp256k1.FromPrivateKey(priv_key_bytes)
        bip44_ctx = Bip44.FromBip32(bip32_ctx, Bip44Coins.BITCOIN)
        address = bip44_ctx.PublicKey().ToAddress()
        return address
    except Exception:
        return None

def privkey_hex_to_btc_address(privkey_hex):
    try:
        bip44_mst = Bip44.FromPrivateKey(bytes.fromhex(privkey_hex), Bip44Coins.BITCOIN)
        addr = bip44_mst.PublicKey().ToAddress()
        return addr
    except Exception:
        return None

def is_ethereum_address(addr):
    return bool(re.fullmatch(r'0x[a-fA-F0-9]{40}', addr))

# --- Containers ---
mnemonics = set()
private_keys = set()
detected_addresses = {
    "ethereum": set(),
    "bitcoin": set(),
    "solana": set(),
    "unknown": set(),
}
privkey_to_addresses = {}

# --- Main entry-processing loop ---
progress_interval = max(1, len(data)//50)
for idx, entry in enumerate(data):
    if idx % progress_interval == 0:
        print(f"Scanning entry {idx+1}/{len(data)}...")
    val = entry.get('value_decoded') or entry.get('value') or ''
    if not val:
        continue

    # Extract mnemonics
    found = extract_mnemonics(val, max_candidates=1000)
    mnemonics.update(found)

    # Find private keys hex (64 hex chars) or WIF private keys (start with 5, K or L for BTC)
    privkey_hex_matches = re.findall(r'\b[0-9a-fA-F]{64}\b', val)
    wif_matches = re.findall(r'\b[5KL][1-9A-HJ-NP-Za-km-z]{50,51}\b', val)

    for privkey_hex in privkey_hex_matches:
        try:
            priv_bytes = bytes.fromhex(privkey_hex)
            if len(priv_bytes) != 32 and len(priv_bytes) != 64:
                continue
        except Exception:
            continue
        private_keys.add(privkey_hex)
        eth_addr = None
        sol_addr = None
        btc_addr = None
        try:
            eth_addr = eth_privkey_to_address(privkey_hex)
            detected_addresses["ethereum"].add(eth_addr)
        except Exception:
            pass
        try:
            sol_addr = solana_privkey_to_pubkey(privkey_hex)
            if sol_addr:
                detected_addresses["solana"].add(sol_addr)
        except Exception:
            pass
        try:
            btc_addr = privkey_hex_to_btc_address(privkey_hex)
            if btc_addr:
                detected_addresses["bitcoin"].add(btc_addr)
        except Exception:
            pass
        privkey_to_addresses[privkey_hex] = {
            "ethereum": eth_addr,
            "solana": sol_addr,
            "bitcoin": btc_addr,
        }

    for wif in wif_matches:
        private_keys.add(wif)
        btc_addr = bitcoin_wif_to_address(wif)
        if btc_addr:
            detected_addresses["bitcoin"].add(btc_addr)
            privkey_to_addresses[wif] = {"bitcoin": btc_addr}

    # Also extract addresses directly in text (Ethereum & Bitcoin)
    eth_addrs = re.findall(r'0x[a-fA-F0-9]{40}', val)
    for a in eth_addrs:
        detected_addresses["ethereum"].add(to_checksum_address(a))
    btc_addrs = re.findall(r'\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b', val)
    for a in btc_addrs:
        detected_addresses["bitcoin"].add(a)

# Wallet balance queries (simple examples)
def get_eth_balance(address):
    import time
    retries = 3
    for attempt in range(retries):
        try:
            url = f"https://api.etherscan.io/api?module=account&action=balance&address={address}&tag=latest&apikey=YourApiKeyToken"
            r = requests.get(url, timeout=10)
            result = r.json()
            if result.get('status') == '1':
                wei = int(result['result'])
                eth = wei / 1e18
                return eth
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
            else:
                print(f"[warn] ETH balance error for {address}: {e}")
    return None

def get_btc_balance(address):
    import time
    retries = 3
    for attempt in range(retries):
        try:
            url = f"https://blockchain.info/q/addressbalance/{address}"
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                satoshi = int(r.text)
                btc = satoshi / 1e8
                return btc
            else:
                raise Exception(f"HTTP {r.status_code}")
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
            else:
                print(f"[warn] BTC balance error for {address}: {e}")
    return None

# --- Filter and limit addresses for balance checking ---
def is_valid_eth_address(addr):
    # Stricter: must be 0x-prefixed, 40 hex chars, and pass EIP-55 checksum
    if not isinstance(addr, str):
        return False
    if not re.fullmatch(r"0x[a-fA-F0-9]{40}", addr):
        return False
    try:
        # to_checksum_address will raise if not valid
        return addr == to_checksum_address(addr)
    except Exception:
        return False

def is_valid_btc_address(addr):
    # Stricter: use regex for legacy, segwit, and bech32 formats
    if not isinstance(addr, str):
        return False
    # Legacy (P2PKH): starts with 1, 26-35 chars
    if re.fullmatch(r"1[1-9A-HJ-NP-Za-km-z]{25,34}", addr):
        return True
    # Script (P2SH): starts with 3, 26-35 chars
    if re.fullmatch(r"3[1-9A-HJ-NP-Za-km-z]{25,34}", addr):
        return True
    # Bech32 (P2WPKH/P2WSH): starts with bc1, 42-62 chars, lowercase only
    if re.fullmatch(r"bc1[0-9a-z]{39,59}", addr):
        return True
    return False

balances = {"ethereum": {}, "bitcoin": {}}
eth_addrs = [a for a in detected_addresses["ethereum"] if is_valid_eth_address(a)]
btc_addrs = [a for a in detected_addresses["bitcoin"] if is_valid_btc_address(a)]

# Remove invalid addresses from detected_addresses (for reporting accuracy)
detected_addresses["ethereum"] = set(eth_addrs)
detected_addresses["bitcoin"] = set(btc_addrs)

for addr in eth_addrs[:10]:
    bal = get_eth_balance(addr)
    if bal is not None:
        balances["ethereum"][addr] = bal

for addr in btc_addrs[:10]:
    bal = get_btc_balance(addr)
    if bal is not None:
        balances["bitcoin"][addr] = bal

# --- Save results ---
summary = {
    "mnemonics": list(mnemonics),
    "private_keys": list(private_keys),
    "detected_addresses": {k: list(v) for k, v in detected_addresses.items()},
    "cross_check_results": [
        {"private_key": priv, "chain": chain, "address": addr, "matched": addr in detected_addresses.get(chain, [])}
        for priv, addrs in privkey_to_addresses.items() for chain, addr in addrs.items() if addr
    ],
    "balances": balances,
}

with open('detected_wallet_data_summary.json', 'w') as f:
    json.dump(summary, f, indent=2)
print("Detailed results saved to detected_wallet_data_summary.json")

with open('filtered_wallet_entries.json', 'w') as f:
    json.dump(data, f, indent=2)
print("Raw extracted entries saved to filtered_wallet_entries.json (for cli.py)")

# Output summary
print(f"Detected mnemonic phrases: {len(mnemonics)}")
for i, m in enumerate(list(mnemonics)[:5], 1):
    print(f"  Mnemonic #{i}: {m}")

print(f"Detected private keys: {len(private_keys)}")

for chain in ["ethereum", "bitcoin", "solana"]:
    print(f"Detected {chain.capitalize()} addresses: {len(detected_addresses[chain])}")
    for i, a in enumerate(list(detected_addresses[chain])[:5], 1):
        print(f"  {chain.capitalize()} Address #{i}: {a}")

print("Cross-check of private keys to addresses (sample 5):")
for item in summary["cross_check_results"][:5]:
    print(f"  PrivKey: {item['private_key'][:8]}... Chain: {item['chain']} Address: {item['address']} Matched: {item['matched']}")

print("Sample balances (first 5):")
for chain in balances:
    print(f"{chain.capitalize()} balances:")
    for addr, bal in list(balances[chain].items())[:5]:
        print(f"  {addr}: {bal}")
