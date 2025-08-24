#!/usr/bin/env python3
"""
Unified Crypto Key Extractor
============================
Production-grade key extraction tool that combines:
- Fast pattern-based key scanning
- MetaMask vault decryption
- LevelDB extraction
- Multi-format key detection
"""

import os
import re
import json
import time
import hashlib
import base58
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import logging

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - EXTRACTOR - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('extraction.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class UnifiedCryptoExtractor:
    """Unified key extraction with multiple methods"""
    
    def __init__(self, dataset_path: str):
        self.dataset_path = Path(dataset_path)
        self.found_keys = []
        
        # Comprehensive key patterns
        self.key_patterns = {
            # Bitcoin WIF formats
            'bitcoin_wif': r'\b[5KL][1-9A-HJ-NP-Za-km-z]{50,51}\b',
            'bitcoin_wif_compressed': r'\b[KL][1-9A-HJ-NP-Za-km-z]{51}\b',
            
            # Ethereum/Bitcoin hex keys
            'ethereum_hex': r'\b(?:0x)?[0-9a-fA-F]{64}\b',
            'bitcoin_hex': r'\b[0-9a-fA-F]{64}\b',
            
            # Solana private keys
            'solana_base58': r'\b[1-9A-HJ-NP-Za-km-z]{87,88}\b',
            
            # Seed phrases
            'seed_12': r'\b([a-z]+\s+){11}[a-z]+\b',
            'seed_24': r'\b([a-z]+\s+){23}[a-z]+\b',
            
            # MetaMask vault patterns
            'metamask_vault': r'"vault":"[^"]{100,}"',
            'metamask_keyring': r'"keyring[^"]*":\s*"[^"]{50,}"',
            
            # Electrum wallet patterns
            'electrum_seed': r'"seed":\s*"[^"]{50,}"',
            'electrum_master_key': r'"master_private_key":\s*"[^"]{50,}"',
        }
    
    def is_valid_hex_key(self, key: str) -> bool:
        """Validate hex private key"""
        key = key.replace('0x', '').strip()
        if len(key) != 64:
            return False
        try:
            # Check if it's valid hex
            int(key, 16)
            # Avoid obviously invalid keys
            if key in ['0' * 64, 'f' * 64, 'F' * 64]:
                return False
            # Check if it's in valid range for secp256k1
            key_int = int(key, 16)
            return 1 <= key_int <= 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364140
        except ValueError:
            return False
    
    def is_valid_wif_key(self, key: str) -> bool:
        """Validate WIF private key"""
        try:
            # Basic length check
            if len(key) not in [51, 52]:
                return False
            # Check prefix
            if not key.startswith(('5', 'K', 'L')):
                return False
            # Try base58 decode
            decoded = base58.b58decode(key)
            return len(decoded) in [37, 38]  # 32 bytes + prefix + optional suffix + checksum
        except:
            return False
    
    def extract_from_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Extract keys from a single file"""
        findings = []
        
        try:
            # Handle different file types
            if file_path.suffix.lower() in ['.json', '.txt', '.log']:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
            elif file_path.suffix.lower() in ['.db', '.sqlite', '.leveldb']:
                # Binary file handling for databases
                with open(file_path, 'rb') as f:
                    raw_content = f.read()
                content = raw_content.decode('utf-8', errors='ignore')
            else:
                # Try reading as text
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
            
            # Search for patterns
            for pattern_name, pattern in self.key_patterns.items():
                matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
                
                for match in matches:
                    key_candidate = match.group().strip()
                    
                    # Validate based on type
                    is_valid = False
                    if 'hex' in pattern_name and self.is_valid_hex_key(key_candidate):
                        is_valid = True
                    elif 'wif' in pattern_name and self.is_valid_wif_key(key_candidate):
                        is_valid = True
                    elif pattern_name in ['seed_12', 'seed_24']:
                        is_valid = len(key_candidate.split()) in [12, 24]
                    elif 'metamask' in pattern_name or 'vault' in pattern_name:
                        is_valid = len(key_candidate) > 50
                    
                    if is_valid:
                        finding = {
                            'type': pattern_name,
                            'key': key_candidate,
                            'file': str(file_path),
                            'position': match.start(),
                            'timestamp': datetime.now().isoformat()
                        }
                        findings.append(finding)
                        logger.info(f"✅ Found {pattern_name} in {file_path.name}")
        
        except Exception as e:
            logger.error(f"❌ Error processing {file_path}: {e}")
        
        return findings
    
    def extract_metamask_vaults(self, file_path: Path) -> List[Dict[str, Any]]:
        """Specialized MetaMask vault extraction"""
        vaults = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Look for MetaMask vault data
            vault_pattern = r'"vault":"([^"]+)"'
            vault_matches = re.finditer(vault_pattern, content)
            
            for match in vault_matches:
                vault_data = match.group(1)
                if len(vault_data) > 100:  # Valid vaults are quite long
                    vault_info = {
                        'type': 'metamask_vault',
                        'vault_data': vault_data,
                        'file': str(file_path),
                        'length': len(vault_data),
                        'timestamp': datetime.now().isoformat()
                    }
                    vaults.append(vault_info)
                    logger.info(f"🔒 Found MetaMask vault in {file_path.name} (length: {len(vault_data)})")
        
        except Exception as e:
            logger.error(f"❌ Error extracting MetaMask vaults from {file_path}: {e}")
        
        return vaults
    
    def scan_directory(self, target_extensions=None) -> Dict[str, Any]:
        """Scan entire directory for crypto keys"""
        if target_extensions is None:
            target_extensions = ['.txt', '.json', '.log', '.db', '.sqlite', '.ldb', '.dat']
        
        start_time = time.time()
        all_findings = []
        files_processed = 0
        files_with_findings = 0
        
        logger.info(f"🚀 Starting unified extraction scan on {self.dataset_path}")
        
        for file_path in self.dataset_path.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in target_extensions:
                files_processed += 1
                
                # Regular pattern extraction
                findings = self.extract_from_file(file_path)
                
                # Specialized MetaMask extraction for relevant files
                if any(term in file_path.name.lower() for term in ['metamask', 'vault', 'storage', 'extension']):
                    vault_findings = self.extract_metamask_vaults(file_path)
                    findings.extend(vault_findings)
                
                if findings:
                    files_with_findings += 1
                    all_findings.extend(findings)
                
                # Progress update
                if files_processed % 100 == 0:
                    logger.info(f"📊 Progress: {files_processed} files processed, {len(all_findings)} findings")
        
        # Compile results
        results = {
            'scan_timestamp': datetime.now().isoformat(),
            'dataset_path': str(self.dataset_path),
            'files_processed': files_processed,
            'files_with_findings': files_with_findings,
            'total_findings': len(all_findings),
            'findings': all_findings,
            'findings_by_type': {},
            'scan_duration': time.time() - start_time
        }
        
        # Count findings by type
        for finding in all_findings:
            finding_type = finding['type']
            results['findings_by_type'][finding_type] = results['findings_by_type'].get(finding_type, 0) + 1
        
        # Save results
        output_file = f"unified_extraction_results_{int(time.time())}.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"✅ Scan complete! Results saved to {output_file}")
        logger.info(f"📊 Summary: {files_processed} files, {len(all_findings)} findings in {results['scan_duration']:.1f}s")
        
        return results
    
    def quick_priority_scan(self, max_files=1000) -> Dict[str, Any]:
        """Quick scan focusing on high-priority file types"""
        priority_extensions = ['.json', '.txt', '.log']
        priority_keywords = ['metamask', 'vault', 'wallet', 'private', 'key', 'seed']
        
        start_time = time.time()
        all_findings = []
        files_processed = 0
        
        logger.info(f"⚡ Starting priority scan (max {max_files} files)")
        
        for file_path in self.dataset_path.rglob('*'):
            if files_processed >= max_files:
                break
                
            if file_path.is_file():
                # Priority files first
                is_priority = (file_path.suffix.lower() in priority_extensions or
                             any(keyword in file_path.name.lower() for keyword in priority_keywords))
                
                if is_priority:
                    files_processed += 1
                    findings = self.extract_from_file(file_path)
                    
                    if findings:
                        all_findings.extend(findings)
                        logger.info(f"🎯 Priority file: {file_path.name} - {len(findings)} findings")
        
        results = {
            'scan_type': 'priority_scan',
            'scan_timestamp': datetime.now().isoformat(),
            'files_processed': files_processed,
            'total_findings': len(all_findings),
            'findings': all_findings,
            'scan_duration': time.time() - start_time
        }
        
        output_file = f"priority_extraction_results_{int(time.time())}.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"⚡ Priority scan complete: {len(all_findings)} findings in {results['scan_duration']:.1f}s")
        return results

def main():
    """Main extraction function"""
    import argparse
    parser = argparse.ArgumentParser(description="Unified Crypto Key Extractor")
    parser.add_argument("dataset_path", help="Path to dataset directory")
    parser.add_argument("--quick", action="store_true", help="Run quick priority scan")
    parser.add_argument("--max-files", type=int, default=1000, help="Max files for quick scan")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.dataset_path):
        logger.error(f"❌ Dataset path not found: {args.dataset_path}")
        return
    
    extractor = UnifiedCryptoExtractor(args.dataset_path)
    
    if args.quick:
        results = extractor.quick_priority_scan(args.max_files)
    else:
        results = extractor.scan_directory()
    
    print(f"\n🏆 EXTRACTION COMPLETE")
    print(f"Files processed: {results['files_processed']}")
    print(f"Total findings: {results['total_findings']}")
    print(f"Scan duration: {results['scan_duration']:.1f} seconds")

if __name__ == "__main__":
    main()
