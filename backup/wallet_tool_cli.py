import os
import sys
import json
import csv
import re
import base64
from datetime import datetime

try:
    import plyvel
except ImportError:
    plyvel = None

# Wallet type detection regex patterns - enhanced and more flexible
WALLET_TYPES = {
    "Ethereum": re.compile(r'0x[a-fA-F0-9]{40}'),
    "Bitcoin (Base58)": re.compile(r'[13][a-km-zA-HJ-NP-Z1-9]{25,34}'),
    "Bitcoin (Bech32)": re.compile(r'bc1[a-z0-9]{25,39}'),
    "Bitcoin WIF": re.compile(r'[5KL][1-9A-HJ-NP-Za-km-z]{50,51}'),
    "Mnemonic": re.compile(r'([a-z]{2,10}\s){11,24}[a-z]{2,10}'),  # 12-25 words approx
}

KEYWORDS = ['mnemonic', 'private', 'key', 'addr', 'address', '0x', 'seed', 'wallet', 'pk']

# Expanded regex for encoded strings
BASE64_REGEX = re.compile(r'([A-Za-z0-9+/=]{24,}|[A-Za-z0-9_\-]{24,})')  # standard + URL safe base64
HEX_REGEX = re.compile(r'\b[a-fA-F0-9]{40,128}\b')
BASE58_REGEX = re.compile(r'\b[123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz]{25,52}\b')

def detect_wallet_type(s):
    s = s.strip()
    for wtype, pattern in WALLET_TYPES.items():
        if pattern.fullmatch(s):
            return wtype
    return "Unknown"

def clean_string(s):
    s = s.strip('"\'')
    s = s.replace('\\"', '"').replace('\\n', ' ').replace('\\r', ' ').replace('\\t', ' ')
    return s.strip()

def extract_strings(obj):
    found = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            found.extend(extract_strings(k))
            found.extend(extract_strings(v))
    elif isinstance(obj, list):
        for i in obj:
            found.extend(extract_strings(i))
    elif isinstance(obj, str):
        s = clean_string(obj)
        s_lower = s.lower()
        if any(kw in s_lower for kw in KEYWORDS) and len(s) >= 20:
            # Try direct wallet patterns
            for pat in WALLET_TYPES.values():
                matches = pat.findall(s)
                for m in matches:
                    if len(m) > 20:
                        found.append(m)
            # Also add the whole string if looks like mnemonic phrase
            if WALLET_TYPES['Mnemonic'].search(s):
                found.append(s)
    return found

def extract_encoded_strings(text):
    found = []

    # Base64 decode attempts
    for match in BASE64_REGEX.findall(text):
        try:
            b64 = match.replace('-', '+').replace('_', '/')
            decoded = base64.b64decode(b64 + '===').decode('utf-8', errors='ignore')
            if any(kw in decoded.lower() for kw in KEYWORDS):
                found.extend(extract_strings(decoded))
        except Exception:
            pass

    # Hex matches (40+ length)
    for match in HEX_REGEX.findall(text):
        if any(kw in match.lower() for kw in KEYWORDS):
            found.append(match)

    # Base58 matches
    for match in BASE58_REGEX.findall(text):
        if len(match) >= 25:
            found.append(match)

    return found

def extract_fuzzy(text):
    """
    Try to extract wallet-like strings around keywords, allowing for noise
    Example: find keywords + 50 chars around it and extract possible keys
    """
    found = []
    text_lower = text.lower()
    for kw in KEYWORDS:
        for m in re.finditer(kw, text_lower):
            start = max(m.start() - 50, 0)
            end = min(m.end() + 50, len(text))
            snippet = text[start:end]
            # extract wallet strings from snippet
            found.extend(extract_strings(snippet))
            found.extend(extract_encoded_strings(snippet))
    return list(set(found))

def scan_leveldb_wallets(scan_dir):
    """
    Find all LevelDB folders recursively (by presence of CURRENT file and .ldb files)
    """
    leveldb_dirs = []
    for root, dirs, files in os.walk(scan_dir):
        if 'CURRENT' in files:
            # heuristic: presence of CURRENT file indicates LevelDB dir
            # check if at least one .ldb file inside
            ldb_files = [f for f in files if f.endswith('.ldb') or f.endswith('.log')]
            if ldb_files:
                leveldb_dirs.append(root)
    return leveldb_dirs

def parse_leveldb_folder(folderpath):
    """
    Use plyvel to open LevelDB and extract keys/values as strings for scanning
    """
    if not plyvel:
        print("[!] plyvel not installed; skipping LevelDB parsing for", folderpath)
        return []

    found = []
    try:
        db = plyvel.DB(folderpath, create_if_missing=False)
        for key, value in db:
            try:
                # Try decode key and value as utf-8
                k = key.decode('utf-8', errors='ignore')
                v = value.decode('utf-8', errors='ignore')
                found.extend(extract_strings(k))
                found.extend(extract_strings(v))
                found.extend(extract_encoded_strings(k))
                found.extend(extract_encoded_strings(v))
            except Exception:
                continue
        db.close()
    except Exception as e:
        print(f"[!] Error opening LevelDB at {folderpath}: {e}")
    return list(set(found))

def parse_file_fallback(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except Exception as e:
        print(f"[!] Error reading {filepath}: {e}")
        return []

    # Try JSON parse first
    try:
        data = json.loads(content)
        return extract_strings(data)
    except Exception:
        pass

    results = extract_strings(content)
    results += extract_encoded_strings(content)
    results += extract_fuzzy(content)

    # Print suspicious strings for manual review
    if results:
        print(f"[!] Suspicious strings found in {filepath}:")
        for s in results:
            snippet = s if len(s) < 100 else s[:100] + "..."
            print(f"    {snippet}")

    return list(set(results))

def main():
    scan_dir = input("Enter the path to the directory to scan (leave empty for current directory): ").strip()
    if not scan_dir:
        scan_dir = os.getcwd()

    if not os.path.isdir(scan_dir):
        print(f"Error: Directory '{scan_dir}' does not exist.")
        sys.exit(1)

    output_dir = f"wallet_scan_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(output_dir, exist_ok=True)

    print(f"Scanning directory: {scan_dir}")

    # 1. Scan for LevelDB folders recursively
    leveldb_dirs = scan_leveldb_wallets(scan_dir)
    print(f"[*] Found {len(leveldb_dirs)} LevelDB directories.")

    extracted_rows = []

    # 2. Extract from LevelDB folders via plyvel
    for i, ldb_dir in enumerate(leveldb_dirs, 1):
        print(f"[LevelDB {i}/{len(leveldb_dirs)}] Parsing LevelDB folder: {ldb_dir}")
        strings = parse_leveldb_folder(ldb_dir)
        candidate_name = os.path.basename(ldb_dir.rstrip('/\\'))
        for s in strings:
            wtype = detect_wallet_type(s)
            extracted_rows.append([candidate_name, 'LevelDB', s, wtype])

    # 3. Fallback: scan all .log and .ldb files individually
    wallet_files = []
    for root, dirs, files in os.walk(scan_dir):
        for file in files:
            if file.endswith('.log') or file.endswith('.ldb'):
                wallet_files.append(os.path.join(root, file))
    print(f"[*] Found {len(wallet_files)} individual .log/.ldb files to scan.")

    for i, wf in enumerate(wallet_files, 1):
        print(f"[{i}/{len(wallet_files)}] Processing file: {wf}")
        strings = parse_file_fallback(wf)
        if not strings:
            print(f"Skipping {wf}, no data parsed.")
            continue
        candidate_name = os.path.basename(os.path.dirname(wf))
        for s in strings:
            wtype = detect_wallet_type(s)
            extracted_rows.append([candidate_name, os.path.basename(wf), s, wtype])

    if not extracted_rows:
        print("[*] No wallet data found.")
        return

    csv_file = os.path.join(output_dir, "wallet_extracted_summary.csv")
    with open(csv_file, 'w', newline='', encoding='utf-8') as csvf:
        writer = csv.writer(csvf)
        writer.writerow(['Candidate', 'File', 'ExtractedString', 'WalletType'])
        for row in extracted_rows:
            writer.writerow(row)

    print(f"[*] Extraction CSV saved: {csv_file}")

    md_file = os.path.join(output_dir, "wallet_report.md")
    with open(md_file, 'w', encoding='utf-8') as mdf:
        mdf.write("| Candidate | File | Extracted String | Wallet Type |\n")
        mdf.write("|-----------|------|------------------|-------------|\n")
        for row in extracted_rows:
            esc_string = row[2].replace('|', '\\|')
            mdf.write(f"| {row[0]} | {row[1]} | {esc_string} | {row[3]} |\n")

    print(f"[*] Markdown report saved: {md_file}")

if __name__ == "__main__":
    main()

