#!/usr/bin/env python3
"""
⚡ Electrum-Compatible WIF Key Formatter
======================================
Format discovered WIF key for Electrum wallet import
"""

import os
import json
import hashlib
import base58
import binascii

class ElectrumWIFFormatter:
    def __init__(self):
        self.discovered_wif = "KXFTFgvnAfFqKfU8B6pe6NEfHCeaXVtVgXFT7irPHzhwyqV57LwF"
    
    def validate_wif_key(self, wif_key):
        """Validate WIF key format for Electrum compatibility"""
        print(f"🔍 VALIDATING WIF KEY: {wif_key}")
        print("-" * 50)
        
        try:
            # Check length
            print(f"📏 Length: {len(wif_key)} characters")
            
            if len(wif_key) < 51 or len(wif_key) > 52:
                print("❌ Invalid length (should be 51-52 characters)")
                return False, "Invalid length"
            
            # Check first character (version byte indicator)
            first_char = wif_key[0]
            print(f"🔤 First character: '{first_char}'")
            
            if first_char in ['5', 'K', 'L']:
                if first_char == '5':
                    key_type = "Uncompressed WIF (Mainnet)"
                elif first_char == 'K':
                    key_type = "Compressed WIF (Mainnet)"
                elif first_char == 'L':
                    key_type = "Compressed WIF (Mainnet)"
                
                print(f"✅ Valid WIF prefix: {key_type}")
            else:
                print(f"❌ Invalid WIF prefix: {first_char}")
                return False, f"Invalid prefix: {first_char}"
            
            # Attempt Base58 decode
            try:
                decoded = base58.b58decode(wif_key)
                print(f"✅ Base58 decode successful: {len(decoded)} bytes")
                
                if len(decoded) == 37:  # 1 version + 32 private key + 4 checksum
                    print("✅ Uncompressed WIF format (37 bytes)")
                    is_compressed = False
                elif len(decoded) == 38:  # 1 version + 32 private key + 1 compression + 4 checksum
                    print("✅ Compressed WIF format (38 bytes)")
                    is_compressed = True
                else:
                    print(f"❌ Invalid decoded length: {len(decoded)} bytes")
                    return False, f"Invalid decoded length: {len(decoded)}"
                
                # Verify checksum
                payload = decoded[:-4]
                checksum = decoded[-4:]
                hash_check = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
                
                if checksum == hash_check:
                    print("✅ Checksum valid")
                    return True, {
                        'valid': True,
                        'type': key_type,
                        'compressed': is_compressed,
                        'electrum_ready': True
                    }
                else:
                    print("❌ Invalid checksum")
                    return False, "Invalid checksum"
                    
            except Exception as e:
                print(f"❌ Base58 decode failed: {str(e)}")
                return False, f"Base58 decode error: {str(e)}"
                
        except Exception as e:
            print(f"❌ Validation error: {str(e)}")
            return False, str(e)
    
    def create_electrum_import_formats(self, wif_key):
        """Create various formats for Electrum import"""
        print(f"\n⚡ ELECTRUM IMPORT FORMATS")
        print("=" * 50)
        
        formats = {
            'wif_key_raw': wif_key,
            'electrum_import_methods': [
                {
                    'method': 'Private Key Import',
                    'format': wif_key,
                    'instructions': [
                        "1. Open Electrum wallet",
                        "2. File → New/Restore",
                        "3. Choose 'Import Bitcoin addresses or private keys'",
                        "4. Paste the WIF key below:",
                        f"   {wif_key}",
                        "5. Click Next to import"
                    ]
                },
                {
                    'method': 'Sweep to New Wallet',
                    'format': wif_key,
                    'instructions': [
                        "1. Open existing Electrum wallet",
                        "2. Tools → Sweep Private Key",
                        "3. Paste the WIF key:",
                        f"   {wif_key}",
                        "4. Choose destination address",
                        "5. Sweep funds to your wallet"
                    ]
                },
                {
                    'method': 'Text File Import',
                    'format': wif_key,
                    'instructions': [
                        "1. Create text file 'private_keys.txt'",
                        "2. Add the WIF key on a single line:",
                        f"   {wif_key}",
                        "3. Import via Electrum's import function"
                    ]
                }
            ]
        }
        
        return formats
    
    def create_electrum_import_file(self, wif_key):
        """Create ready-to-import file for Electrum"""
        
        # Create electrum-ready import file
        import_content = {
            'electrum_wif_import': {
                'wif_key': wif_key,
                'format': 'WIF_PRIVATE_KEY',
                'ready_for_electrum': True,
                'import_instructions': [
                    "ELECTRUM IMPORT STEPS:",
                    "1. Open Electrum",
                    "2. File → New/Restore", 
                    "3. Select 'Import Bitcoin addresses or private keys'",
                    "4. Copy-paste the WIF key below into Electrum:",
                    "",
                    f"WIF_KEY_TO_IMPORT: {wif_key}",
                    "",
                    "5. Electrum will automatically detect the format",
                    "6. Click Next to complete import"
                ]
            }
        }
        
        # Save Electrum import file
        with open('electrum_import_ready.json', 'w') as f:
            json.dump(import_content, f, indent=2)
        
        # Also create simple text file for direct import
        with open('electrum_wif_key.txt', 'w') as f:
            f.write(wif_key + '\n')
        
        print(f"📄 Created Electrum import files:")
        print(f"   • electrum_import_ready.json (detailed instructions)")
        print(f"   • electrum_wif_key.txt (simple WIF key for import)")
        
        return True
    
    def process_for_electrum(self):
        """Main function to process WIF key for Electrum"""
        print("⚡ ELECTRUM WIF KEY FORMATTER")
        print("=" * 60)
        
        wif_key = self.discovered_wif
        
        # Validate the WIF key
        is_valid, validation_result = self.validate_wif_key(wif_key)
        
        if not is_valid:
            print(f"\n❌ WIF key validation failed: {validation_result}")
            return False
        
        print(f"\n✅ WIF KEY VALIDATION SUCCESSFUL")
        print(f"   Type: {validation_result['type']}")
        print(f"   Compressed: {validation_result['compressed']}")
        print(f"   Electrum Ready: {validation_result['electrum_ready']}")
        
        # Create Electrum import formats
        formats = self.create_electrum_import_formats(wif_key)
        
        # Display import methods
        for method in formats['electrum_import_methods']:
            print(f"\n📋 {method['method'].upper()}")
            print("-" * 30)
            for instruction in method['instructions']:
                print(f"   {instruction}")
        
        # Create import files
        self.create_electrum_import_file(wif_key)
        
        print(f"\n🎯 READY FOR ELECTRUM IMPORT")
        print("=" * 40)
        print(f"✅ WIF key validated and formatted")
        print(f"✅ Import files created")
        print(f"✅ Multiple import methods available")
        
        print(f"\n🚀 IMMEDIATE NEXT STEPS:")
        print(f"1. Open Electrum wallet software")
        print(f"2. Use 'Import Bitcoin addresses or private keys' option")
        print(f"3. Paste this exact WIF key:")
        print(f"   {wif_key}")
        print(f"4. Let Electrum derive the address and check balance")
        print(f"5. If funds found, transfer immediately to secure wallet")
        
        return True

def main():
    formatter = ElectrumWIFFormatter()
    success = formatter.process_for_electrum()
    
    if success:
        print(f"\n💡 ADDITIONAL TIPS:")
        print(f"• Electrum automatically handles WIF format validation")
        print(f"• Both compressed and uncompressed addresses will be checked")
        print(f"• Use 'Sweep Private Key' if you want to move funds immediately")
        print(f"• Always verify addresses match before sending funds")

if __name__ == "__main__":
    main()
