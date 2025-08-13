#!/usr/bin/env python3
"""
ZelCore Balances Analysis Script
Attempts to decode and analyze the ZelCore balances file
"""

import os
import sys
import binascii
from cryptography.fernet import Fernet
import base64
import hashlib
import json

def analyze_zelcore_file(file_path):
    """Analyze the ZelCore balances file"""
    print(f"Analyzing ZelCore file: {file_path}")
    
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return False
    
    # Read the file content
    with open(file_path, 'r') as f:
        content = f.read().strip()
    
    print(f"File size: {len(content)} characters")
    
    # Check if it's valid hex
    try:
        hex_data = bytes.fromhex(content)
        print(f"Valid hex data, decoded size: {len(hex_data)} bytes")
        
        # Try to find patterns that might indicate wallet data
        # Look for common cryptocurrency address patterns
        hex_str = content.lower()
        
        # Look for potential Bitcoin addresses (starts with 1, 3, or bc1)
        btc_patterns = []
        
        # Look for potential Ethereum addresses (40 hex chars)
        eth_patterns = []
        
        # Search for 64-char hex strings (potential private keys)
        private_key_patterns = []
        
        # Search in 64-character chunks
        for i in range(0, len(hex_str), 64):
            chunk = hex_str[i:i+64]
            if len(chunk) == 64:
                private_key_patterns.append(chunk)
        
        print(f"Found {len(private_key_patterns)} potential 64-char hex strings")
        
        # Try to decode as different formats
        try:
            # Try UTF-8 decode
            decoded_text = hex_data.decode('utf-8', errors='ignore')
            print("UTF-8 decode preview:", decoded_text[:100] + "..." if len(decoded_text) > 100 else decoded_text)
        except:
            print("Could not decode as UTF-8")
        
        # Try to find JSON structure
        if '{' in str(hex_data) or '[' in str(hex_data):
            print("Possible JSON structure detected")
        
        # Check for common wallet file headers
        magic_bytes = hex_data[:16]
        print(f"First 16 bytes (hex): {magic_bytes.hex()}")
        
        # Look for seed phrase patterns (12/24 word patterns)
        words = str(hex_data).split()
        if len(words) >= 12:
            print(f"Found {len(words)} space-separated words - possible seed phrase")
            if 12 <= len(words) <= 24:
                print("POTENTIAL SEED PHRASE FOUND!")
                print("Words:", ' '.join(words[:12]))
        
        # Save first few potential private keys for analysis
        if private_key_patterns:
            print("\nFirst 10 potential private key patterns:")
            for i, pattern in enumerate(private_key_patterns[:10]):
                print(f"{i+1}: {pattern}")
        
        return True
        
    except ValueError:
        print("Not valid hex data")
        
        # Try other interpretations
        if content.startswith('U2FsdGVkX1'):
            print("Looks like base64 encrypted data (OpenSSL format)")
        elif content.startswith('{'):
            print("Looks like JSON data")
        
        return False

def main():
    file_path = "/home/admin/Downloads/net599/[AR]39.4.38.112/Important Files/Profile/ZelCore/balances_SeedPhrase-1747047018275"
    
    success = analyze_zelcore_file(file_path)
    
    if success:
        print("\n" + "="*50)
        print("Analysis complete. Check output above for potential wallet data.")
    else:
        print("Could not analyze file as hex data")

if __name__ == "__main__":
    main()
