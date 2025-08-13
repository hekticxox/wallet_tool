#!/usr/bin/env python3
"""
📂 FINAL ORGANIZATION
====================

Complete file organization with advanced categorization.
"""

import os
import shutil
import json
from datetime import datetime

def final_organization():
    """Perform final file organization"""
    
    print("""
╔══════════════════════════════════════════════════════════════════╗
║                   📂 FINAL SYSTEM ORGANIZATION                   ║
║                     Professional Structure                      ║
╚══════════════════════════════════════════════════════════════════╝
    """)
    
    # Enhanced directory structure
    directories = {
        'scripts': {
            'patterns': ['*.py'],
            'exclude': ['system_', 'project_', 'quick_', 'final_']
        },
        'scripts/core': {
            'patterns': ['unified_wallet_scanner.py', 'comprehensive_wallet_scanner.py', 
                        'enhanced_balance_checker.py', 'batch_balance_checker.py', 
                        'api_manager.py', 'verbose_file_scanner.py']
        },
        'scripts/hunters': {
            'patterns': ['*hunter*.py', '*precision*.py', '*jackpot*.py', 'laser_*.py']
        },
        'scripts/extractors': {
            'patterns': ['extract_*.py', 'check_*.py']  
        },
        'scripts/utilities': {
            'patterns': ['*util*.py', '*helper*.py', 'analyze_*.py', 'monitor_*.py',
                        'generate_*.py', 'validate_*.py', 'investigate_*.py']
        },
        'data/keys': {
            'patterns': ['*keys*.json', '*keys*.txt', 'PRIORITY_*.json']
        },
        'data/addresses': {
            'patterns': ['*addresses*.json', '*addresses*.txt', 'top_*.json',
                        'extracted_addresses*.json', 'validated_candidates.json']
        },
        'data/scans': {
            'patterns': ['*scan_results*.txt', '*scan*.json', 'net*_scan*.txt']
        },
        'data/balances': {
            'patterns': ['*balance*.json', '*FUNDED*.json', 'zelcore_*.json']
        },
        'reports/jackpots': {
            'patterns': ['*JACKPOT*.json', '*jackpot*.json']
        },
        'reports/campaigns': {
            'patterns': ['*CAMPAIGN*.json', '*PRECISION*.json', '*DISCOVERY*.json']
        },
        'reports/audits': {
            'patterns': ['*AUDIT*.json', '*SYSTEM*.json', '*CLEANUP*.json']
        },
        'docs': {
            'patterns': ['*.md', '*GUIDE*.md', '*REPORT*.md']
        }
    }
    
    # Create all directories
    for dir_path in directories:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            print(f"📁 Created: {dir_path}/")
    
    moved_files = []
    
    # Organize files
    for file in os.listdir('.'):
        if os.path.isfile(file):
            moved = False
            
            for dir_path, config in directories.items():
                if moved:
                    break
                    
                patterns = config.get('patterns', [])
                exclude = config.get('exclude', [])
                
                # Check exclusions first
                should_exclude = False
                for ex_pattern in exclude:
                    if ex_pattern.replace('*', '') in file:
                        should_exclude = True
                        break
                
                if should_exclude:
                    continue
                
                # Check patterns
                for pattern in patterns:
                    pattern_clean = pattern.replace('*', '')
                    
                    if pattern.startswith('*') and pattern.endswith('*'):
                        # Contains pattern
                        if pattern_clean in file:
                            match = True
                        else:
                            match = False
                    elif pattern.startswith('*'):
                        # Ends with pattern
                        match = file.endswith(pattern_clean)
                    elif pattern.endswith('*'):
                        # Starts with pattern  
                        match = file.startswith(pattern_clean)
                    else:
                        # Exact match
                        match = file == pattern
                    
                    if match:
                        try:
                            dest_path = os.path.join(dir_path, file)
                            if not os.path.exists(dest_path):
                                shutil.move(file, dest_path)
                                moved_files.append(f"{file} -> {dir_path}/")
                                print(f"📂 Moved: {file} -> {dir_path}/")
                                moved = True
                                break
                        except Exception as e:
                            print(f"❌ Could not move {file}: {e}")
    
    # Create index files for each category
    create_directory_indexes(directories)
    
    print(f"\n✅ Organization complete: {len(moved_files)} files moved")
    print("📋 Directory indexes created")
    
    # Final cleanup report
    cleanup_summary = {
        'timestamp': datetime.now().isoformat(),
        'operation': 'Final Organization',
        'files_moved': moved_files,
        'directories_created': list(directories.keys()),
        'total_files_organized': len(moved_files)
    }
    
    with open('FINAL_ORGANIZATION_REPORT.json', 'w') as f:
        json.dump(cleanup_summary, f, indent=2)
    
    print(f"📋 Organization report: FINAL_ORGANIZATION_REPORT.json")

def create_directory_indexes(directories):
    """Create index files for organized directories"""
    
    for dir_path in directories:
        if os.path.exists(dir_path):
            files = [f for f in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, f))]
            
            if files:
                index_content = f"# {dir_path.upper()} INDEX\n\n"
                index_content += f"Directory: `{dir_path}/`\n"
                index_content += f"Files: {len(files)}\n"
                index_content += f"Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                index_content += "## Files:\n\n"
                
                for file in sorted(files):
                    file_path = os.path.join(dir_path, file)
                    try:
                        size = os.path.getsize(file_path) / 1024
                        index_content += f"- `{file}` ({size:.1f} KB)\n"
                    except:
                        index_content += f"- `{file}`\n"
                
                index_file = os.path.join(dir_path, 'INDEX.md')
                with open(index_file, 'w') as f:
                    f.write(index_content)

if __name__ == "__main__":
    final_organization()
