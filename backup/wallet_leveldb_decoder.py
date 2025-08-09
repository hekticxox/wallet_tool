#!/usr/bin/env python3
"""
wallet_leveldb_decoder.py
Attempt to parse LevelDB (and similar) files/directories and produce readable dumps for forensics.

Usage:
    python3 wallet_leveldb_decoder.py [directory]

If a directory path is provided, scans that directory. Otherwise scans current directory.

Outputs:
    ./wallet_leveldb_parsed_YYYYMMDD_HHMMSS/  - JSON/text dumps per candidate DB

Notes:
 - If `plyvel` is installed the script will try to open LevelDB directories directly (best results).
 - If `snappy` (python-snappy) is installed the script will attempt Snappy decompression on candidate blobs.
 - Otherwise the script falls back to extracting printable strings and hex-dumps from candidate files.

This is a best-effort forensic tool — LevelDB internals (SST format, compression) vary by implementation.
"""

from __future__ import annotations
import os, sys, re, json, time, hashlib, binascii, datetime, traceback, subprocess
from pathlib import Path

# Optional libraries (used if available)
try:
    import plyvel
except Exception:
    plyvel = None

try:
    import snappy
except Exception:
    snappy = None

def main():
    # === START ADDED PART ===
    if len(sys.argv) > 1:
        root = Path(sys.argv[1])
        if not root.exists() or not root.is_dir():
            print(f"[!] Directory does not exist or not a directory: {root}")
            return
    else:
        root = Path.cwd()
    print(f"Scanning {root} for LevelDB-like candidates...")
    # === END ADDED PART ===

    OUT_ROOT = Path.cwd() / f"wallet_leveldb_parsed_{time.strftime('%Y%m%d_%H%M%S')}"
    OUT_ROOT.mkdir(parents=True, exist_ok=True)

    LEVELDB_EXTS = {'.ldb', '.sst', '.log', '.btdb', '.db', '.dat', '.key'}
    CANDIDATE_KEYWORDS = ['leveldb', 'ldb', 'sst', 'btdb', 'ledger', 'wallet', 'bt.co', 'btdb']

    PRINTABLE_RE = re.compile(rb'[\x20-\x7E]{4,}')  # printable ASCII sequences length>=4

    def is_candidate_file(p: Path) -> bool:
        if any(k in p.name.lower() for k in CANDIDATE_KEYWORDS):
            return True
        if p.suffix.lower() in LEVELDB_EXTS:
            return True
        return False

    def find_candidates(root: Path) -> list[Path]:
        candidates = []
        for p in root.rglob('*'):
            try:
                if p.is_dir():
                    if 'leveldb' in p.name.lower():
                        candidates.append(p)
                        continue
                    child_exts = {c.suffix.lower() for c in p.iterdir() if c.is_file()}
                    if '.ldb' in child_exts or '.sst' in child_exts:
                        candidates.append(p)
                        continue
                else:
                    if is_candidate_file(p):
                        candidates.append(p)
            except Exception:
                pass
        uniq = []
        seen = set()
        for c in candidates:
            try:
                real = c.resolve()
            except Exception:
                real = c
            if real not in seen:
                seen.add(real)
                uniq.append(c)
        return uniq

    def try_plyvel_open(dirpath: Path):
        if plyvel is None:
            return None, "plyvel not installed"
        try:
            db = plyvel.DB(str(dirpath), create_if_missing=False)
            return db, None
        except Exception as e:
            return None, str(e)

    def iter_plyvel_db(db):
        try:
            for k, v in db:
                yield k, v
        except Exception:
            it = db.iterator()
            for item in it:
                yield item

    def extract_printable_strings_from_bytes(b: bytes, min_len: int = 4):
        return [m.group(0).decode('ascii', errors='ignore') for m in PRINTABLE_RE.finditer(b)]

    def run_strings_subprocess(path: Path, min_len: int = 4) -> list[str]:
        try:
            proc = subprocess.run(['strings', '-a', str(path)], capture_output=True, check=False)
            out = proc.stdout.decode('utf-8', errors='ignore').splitlines()
            out = [line for line in out if len(line) >= min_len]
            return out
        except Exception:
            try:
                data = path.read_bytes()
                return extract_printable_strings_from_bytes(data, min_len)
            except Exception:
                return []

    def attempt_snappy_decompress(blob: bytes):
        if snappy is None:
            return None, "snappy not installed"
        try:
            return snappy.decompress(blob), None
        except Exception as e:
            return None, str(e)

    def hex_preview(b: bytes, length: int = 256) -> str:
        return binascii.hexlify(b[:length]).decode('ascii', errors='ignore')

    def analyze_candidate(path: Path, outdir: Path):
        report = {
            "candidate": str(path),
            "is_dir": path.is_dir(),
            "files": [],
            "plyvel_ok": False,
            "plyvel_error": None,
            "entries_sample": [],
            "strings_sample": [],
            "snappy_attempts": [],
        }
        try:
            if path.is_dir():
                db, err = try_plyvel_open(path)
                if db:
                    report['plyvel_ok'] = True
                    try:
                        for i, (k, v) in enumerate(iter_plyvel_db(db)):
                            try:
                                entry = {
                                    "key_hex": binascii.hexlify(k).decode('ascii', errors='ignore'),
                                    "val_hex": binascii.hexlify(v).decode('ascii', errors='ignore'),
                                    "key_preview": (k.decode('utf-8', errors='ignore') if len(k)<200 else k[:200].decode('utf-8', errors='ignore')),
                                    "val_preview": (v.decode('utf-8', errors='ignore') if len(v)<200 else v[:200].decode('utf-8', errors='ignore')),
                                    "val_len": len(v)
                                }
                            except Exception:
                                entry = {
                                    "key_hex": hex_preview(k),
                                    "val_hex": hex_preview(v),
                                    "val_len": len(v)
                                }
                            report['entries_sample'].append(entry)
                            if i >= 200:
                                break
                    finally:
                        try:
                            db.close()
                        except Exception:
                            pass
                else:
                    report['plyvel_error'] = err
                for child in sorted(path.rglob('*')):
                    if child.is_file():
                        try:
                            s = run_strings_subprocess(child)[:200]
                            if s:
                                report['files'].append({
                                    "path": str(child),
                                    "strings_count": len(s),
                                    "strings_sample": s[:50]
                                })
                                data = None
                                try:
                                    data = child.read_bytes()
                                except Exception:
                                    data = None
                                if data and len(data) > 64:
                                    dec, derr = attempt_snappy_decompress(data)
                                    if dec is not None:
                                        report['snappy_attempts'].append({
                                            "path": str(child),
                                            "decompressed_preview": dec[:500].decode('utf-8', errors='ignore'),
                                            "decompressed_len": len(dec)
                                        })
                        except Exception:
                            pass
            else:
                report['files'].append({"path": str(path), "strings_count": None, "strings_sample": []})
                s = run_strings_subprocess(path)[:500]
                report['strings_sample'] = s[:200]
                data = None
                try:
                    data = path.read_bytes()
                except Exception:
                    data = None
                if data and len(data) > 64:
                    dec, derr = attempt_snappy_decompress(data)
                    if dec is not None:
                        report['snappy_attempts'].append({
                            "path": str(path),
                            "decompressed_preview": dec[:500].decode('utf-8', errors='ignore'),
                            "decompressed_len": len(dec)
                        })
        except Exception as e:
            report['error'] = traceback.format_exc()

        outpath = outdir / (hashlib.sha1(str(path).encode()).hexdigest() + '.json')
        try:
            outpath.write_text(json.dumps(report, indent=2, ensure_ascii=False))
        except Exception:
            try:
                with outpath.open('w', encoding='utf-8', errors='ignore') as f:
                    json.dump(report, f, indent=2)
            except Exception:
                pass
        return report

    candidates = find_candidates(root)
    if not candidates:
        print("No obvious candidates found by name/extension heuristics. Expanding to any large binary files...")
        for p in root.rglob('*'):
            try:
                if p.is_file() and p.stat().st_size > 64_000:
                    candidates.append(p)
            except Exception:
                pass

    print(f"Found {len(candidates)} candidate(s).")
    for idx, c in enumerate(candidates, 1):
        print(f"[{idx}/{len(candidates)}] Analyzing: {c}")
        cand_out = OUT_ROOT / f"candidate_{idx}"
        cand_out.mkdir(parents=True, exist_ok=True)
        r = analyze_candidate(c, cand_out)
        summary = {
            "candidate": r.get("candidate"),
            "plyvel_ok": r.get("plyvel_ok"),
            "plyvel_error": r.get("plyvel_error"),
            "files_found": len(r.get("files", [])),
            "strings_sample_count": len(r.get("strings_sample", [])),
            "snappy_attempts": len(r.get("snappy_attempts", [])),
            "entries_sample_count": len(r.get("entries_sample", []))
        }
        (cand_out / "summary.json").write_text(json.dumps(summary, indent=2))
        print(f"  -> summary saved to {cand_out}/summary.json")

    print("All done. Output directory:", OUT_ROOT)
    print("If you want more aggressive parsing (iterate full DBs), install 'plyvel' and re-run: pip3 install plyvel")
    print("To enable snappy decompression attempts install python-snappy: pip3 install python-snappy")
    print("Tip: Inspect the JSONs, grep for 'mnemonic', 'private', 'key', 'addr', 'address', '0x' in the outputs.")

if __name__ == '__main__':
    main()

