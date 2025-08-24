#!/usr/bin/env python3
"""
Complete Autofill Context Analyzer - Extract all context around our target items
"""

import re
import json
from datetime import datetime

def extract_complete_context():
    file_path = "/home/admin/Downloads/net605/[BR]170.247.37.63/Chrome/Profile 1/Autofills.txt"
    target_address = "0x6e59e2a98d12f45ab5872942fe45a1036b1ea9c9"
    recovery_key = "8AKP9G3UJYWK4OYGFLRWEUBHZTA="
    
    print("🎯 COMPLETE AUTOFILL CONTEXT ANALYSIS")
    print("=" * 70)
    print(f"Target Address: {target_address}")
    print(f"Recovery Key: {recovery_key}")
    print(f"File: {file_path}")
    print("-" * 70)
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        print(f"📊 File size: {len(content)} characters")
        
        # Split into lines for analysis
        lines = content.split('\n')
        print(f"📄 Total lines: {len(lines)}")
        
        # Find all relevant lines
        target_lines = []
        recovery_lines = []
        
        for i, line in enumerate(lines):
            if target_address.lower() in line.lower():
                target_lines.append((i+1, line.strip()))
            elif recovery_key in line:
                recovery_lines.append((i+1, line.strip()))
        
        print(f"\n🎯 TARGET ADDRESS OCCURRENCES: {len(target_lines)}")
        for line_num, line in target_lines:
            print(f"   Line {line_num}: {line}")
        
        print(f"\n🔑 RECOVERY KEY OCCURRENCES: {len(recovery_lines)}")
        for line_num, line in recovery_lines:
            print(f"   Line {line_num}: {line}")
        
        # Extract extended context around each occurrence
        print(f"\n📍 EXTENDED CONTEXT ANALYSIS:")
        print("=" * 50)
        
        # Target address context
        for line_num, line in target_lines:
            print(f"\n🏷️  TARGET ADDRESS CONTEXT (Line {line_num}):")
            start_line = max(0, line_num - 20)
            end_line = min(len(lines), line_num + 20)
            
            for i in range(start_line, end_line):
                prefix = ">>> " if i+1 == line_num else "    "
                print(f"{prefix}Line {i+1:5d}: {lines[i].strip()}")
        
        # Recovery key context
        for line_num, line in recovery_lines:
            print(f"\n🔑 RECOVERY KEY CONTEXT (Line {line_num}):")
            start_line = max(0, line_num - 20)
            end_line = min(len(lines), line_num + 20)
            
            for i in range(start_line, end_line):
                prefix = ">>> " if i+1 == line_num else "    "
                print(f"{prefix}Line {i+1:5d}: {lines[i].strip()}")
        
        # Look for patterns and relationships
        print(f"\n🔍 PATTERN ANALYSIS:")
        print("-" * 30)
        
        # Extract form structures
        form_patterns = []
        wallet_related_terms = []
        
        for i, line in enumerate(lines):
            if "FORM:" in line and i < len(lines) - 1:
                form_name = line.strip()
                form_value = lines[i+1].strip() if i+1 < len(lines) else ""
                
                # Check if related to our targets or wallet terms
                if (target_address.lower() in form_value.lower() or 
                    recovery_key in form_value or
                    any(term in form_name.lower() + form_value.lower() 
                        for term in ['wallet', 'purse', 'recover', 'key', 'private', 'seed', 
                                   'mnemonic', 'bitcoin', 'ethereum', 'crypto', 'vegaspix'])):
                    
                    form_patterns.append({
                        'line': i+1,
                        'form': form_name,
                        'value': form_value
                    })
        
        print(f"📋 WALLET-RELATED FORM ENTRIES: {len(form_patterns)}")
        for entry in form_patterns:
            print(f"   Line {entry['line']:5d}: {entry['form']}")
            print(f"   Line {entry['line']+1:5d}: {entry['value']}")
            print()
        
        # Look for email patterns near our targets
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        
        print(f"📧 NEARBY EMAIL PATTERNS:")
        for line_num, line in target_lines + recovery_lines:
            # Check surrounding lines for emails
            start_check = max(0, line_num - 10)
            end_check = min(len(lines), line_num + 10)
            
            for i in range(start_check, end_check):
                emails = re.findall(email_pattern, lines[i])
                if emails:
                    print(f"   Line {i+1:5d}: {emails} (distance: {abs(i+1-line_num)} lines)")
        
        # Look for URLs near our targets
        url_pattern = r'https?://[^\s]+'
        
        print(f"\n🌐 NEARBY URL PATTERNS:")
        for line_num, line in target_lines + recovery_lines:
            start_check = max(0, line_num - 5)
            end_check = min(len(lines), line_num + 5)
            
            for i in range(start_check, end_check):
                urls = re.findall(url_pattern, lines[i])
                if urls:
                    print(f"   Line {i+1:5d}: {urls} (distance: {abs(i+1-line_num)} lines)")
        
        # Look for potential passwords or keys in nearby fields
        print(f"\n🔐 NEARBY POTENTIAL CREDENTIALS:")
        for line_num, line in target_lines + recovery_lines:
            start_check = max(0, line_num - 15)
            end_check = min(len(lines), line_num + 15)
            
            for i in range(start_check, end_check):
                line_content = lines[i].strip()
                if "VALUE:" in line_content:
                    value = line_content.replace("VALUE:", "").strip()
                    # Look for potential credentials
                    if (len(value) > 10 and 
                        any(char.isalnum() for char in value) and
                        any(term in lines[i-1].lower() if i > 0 else "" 
                            for term in ['pass', 'key', 'token', 'secret', 'auth', 'login', 'account'])):
                        
                        form_name = lines[i-1].strip() if i > 0 else "Unknown"
                        print(f"   Line {i:5d}: {form_name}")
                        print(f"   Line {i+1:5d}: {value} (distance: {abs(i+1-line_num)} lines)")
        
        # Save results
        results = {
            'timestamp': datetime.now().isoformat(),
            'file_path': file_path,
            'target_address': target_address,
            'recovery_key': recovery_key,
            'file_size': len(content),
            'total_lines': len(lines),
            'target_occurrences': len(target_lines),
            'recovery_occurrences': len(recovery_lines),
            'wallet_related_forms': len(form_patterns),
            'form_patterns': form_patterns[:20]  # First 20 for brevity
        }
        
        with open('/home/admin/wallet_tool/complete_autofill_analysis.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n💾 Results saved to: complete_autofill_analysis.json")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == "__main__":
    extract_complete_context()
