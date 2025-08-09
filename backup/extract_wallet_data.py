import json
import os
import csv
import re

input_dir = "/home/admin/Downloads/net599/wallet_leveldb_parsed_20250808_184631"
output_csv = "wallet_extracted_summary_clean.csv"

# Keywords to look for in strings (lowercase)
keywords = ['mnemonic', 'private', 'key', 'addr', 'address', '0x', 'seed']

# Regex patterns for typical wallet-related strings
patterns = [
    re.compile(r'0x[a-fA-F0-9]{40,}', re.IGNORECASE),    # Ethereum addresses/private keys
    re.compile(r'[13][a-km-zA-HJ-NP-Z1-9]{25,34}'),     # Bitcoin addresses (Base58)
    re.compile(r'bc1[a-z0-9]{25,39}'),                   # Bech32 Bitcoin addresses
    re.compile(r'[5KL][1-9A-HJ-NP-Za-km-z]{50,51}'),    # Bitcoin WIF keys
    re.compile(r'([a-z]+ ){11,24}[a-z]+'),               # 12-24 word mnemonic phrase (approximate)
]

def clean_string(s):
    # Remove leading/trailing quotes and unescape common JSON escapes
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
        if any(kw in s_lower for kw in keywords) and len(s) >= 20:
            all_matches = []
            for pat in patterns:
                all_matches.extend(pat.findall(s))
            # Filter duplicates & substrings
            unique_matches = set(all_matches)
            filtered = []
            for m in unique_matches:
                # minimal length check, skip very short fragments (under 30 chars)
                if len(m) < 30:
                    continue
                # Skip if this match is substring of another longer match
                if any(m != other and m in other for other in unique_matches):
                    continue
                filtered.append(m)
            found.extend(filtered)
    return found

def main():
    with open(output_csv, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Candidate', 'File', 'ExtractedString'])

        for root, dirs, files in os.walk(input_dir):
            for file in files:
                if file.endswith('.json'):
                    full_path = os.path.join(root, file)
                    try:
                        with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                            data = json.load(f)
                    except Exception as e:
                        print(f"Skipping {full_path}: {e}")
                        continue

                    strings = extract_strings(data)
                    for s in strings:
                        candidate_name = os.path.basename(root)
                        writer.writerow([candidate_name, file, s])

    print(f"Extraction complete. Clean results saved in {output_csv}")

if __name__ == "__main__":
    main()

