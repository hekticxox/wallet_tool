#!/usr/bin/env python3
"""
AGGRESSIVE REPOSITORY CLEANUP
Moves ALL files from root directory into organized structure
"""

import os
import shutil
import glob
from datetime import datetime

def aggressive_cleanup():
    """Aggressively move ALL files from root to organized directories"""
    
    print("🧹 AGGRESSIVE REPOSITORY CLEANUP")
    print("=" * 60)
    
    workspace = "/home/admin/wallet_tool"
    moved_count = 0
    
    # Create organized directories if they don't exist
    dirs_to_create = [
        "src/core", "src/scanners", "src/extractors", "src/checkers", 
        "src/hunters", "src/analyzers", "src/recovery", "src/security", "src/utils",
        "data/results", "data/keys", "data/reports", "data/configs", "data/cache",
        "data/json_files", "data/verification", "data/analysis",
        "docs/reports", "tests", "scripts", "archive/old_data"
    ]
    
    for dir_path in dirs_to_create:
        full_path = os.path.join(workspace, dir_path)
        os.makedirs(full_path, exist_ok=True)
    
    # Define file categorization rules
    file_moves = {
        # Core scanning tools
        "src/core": [
            "unified_wallet_scanner.py", "ultimate_wallet_hunter.py", 
            "comprehensive_wallet_scanner.py", "comprehensive_wallet_recheck.py"
        ],
        
        # Scanners and discovery
        "src/scanners": [
            "*scanner*.py", "*scan*.py", "downloads_scanner.py", "scan_directory.py"
        ],
        
        # Key extraction and finders
        "src/extractors": [
            "*finder*.py", "*extractor*.py", "private_key_*.py", "correct_key_finder.py",
            "targeted_key_*.py", "key_*.py"
        ],
        
        # Balance checkers and validators
        "src/checkers": [
            "*checker*.py", "*check*.py", "balance_*.py", "*balance*.py", 
            "validate_*.py", "*verifier*.py", "*validator*.py"
        ],
        
        # Hunting and searching tools
        "src/hunters": [
            "*hunter*.py", "*hunt*.py", "top_wallet_finder.py", "wallet_pattern_search.py",
            "enhanced_key_hunter.py", "vegaspix_credential_hunter.py"
        ],
        
        # Analysis and investigation
        "src/analyzers": [
            "*analyzer*.py", "*analysis*.py", "context_analyzer.py", "address_origin_tracer.py",
            "investigate_*.py", "pattern_*.py", "smart_*.py", "target_*_analyzer.py",
            "high_value_*_analyzer.py"
        ],
        
        # Recovery tools
        "src/recovery": [
            "*recovery*.py", "recover_*.py", "brain_wallet_*.py", "metamask_*.py",
            "bitcoin_*.py", "mnemonic_*.py"
        ],
        
        # Security and audit
        "src/security": [
            "*security*.py", "*audit*.py", "system_*.py"
        ],
        
        # Utilities and helpers  
        "src/utils": [
            "api_*.py", "*manager*.py", "*monitor*.py", "*cleaner*.py", 
            "quick_*.py", "simple_*.py", "status_*.py", "success_monitor.py",
            "breakthrough_monitor.py", "error_cleaner.py", "fix_*.py"
        ],
        
        # Data files - Results and findings
        "data/results": [
            "*RESULTS*.json", "*results*.json", "*DISCOVERY*.json", "*JACKPOT*.json",
            "FOUND_WALLETS_*.json", "*HUNTING*.json", "*VERIFICATION*.json"
        ],
        
        # Data files - Keys and addresses  
        "data/keys": [
            "*KEYS*.json", "*keys*.json", "*PRIORITY*.json", "*addresses*.json",
            "extracted_*.json", "top_candidates.txt", "validated_candidates.txt"
        ],
        
        # Data files - Reports and analysis
        "data/reports": [
            "*REPORT*.json", "*report*.json", "*ANALYSIS*.json", "*SUMMARY*.json", 
            "*STATUS*.json", "*analysis*.json", "*summary*.json"
        ],
        
        # Data files - Configuration
        "data/configs": [
            "api_config*.json", "*config*.json", "PROJECT_*.json", "requirements.txt"
        ],
        
        # Data files - All other JSON
        "data/json_files": [
            "*.json"
        ],
        
        # Test files
        "tests": [
            "test_*.py", "*test*.py", "quick_test_*.py"
        ],
        
        # Scripts and utilities
        "scripts": [
            "*_summary*.py", "*_report*.py", "final_*.py", "project_*.py", 
            "workspace_*.py", "cleanup_*.py", "prepare_*.py", "setup.sh", "*.sh"
        ],
        
        # Archive old data
        "archive/old_data": [
            "*.db", "*backup*", "*BACKUP*", "address_tracking.db", "wallet_items_*.json",
            "*.txt", "browser_recovery_guide.json", "email_patterns.json"
        ]
    }
    
    print("📦 MOVING FILES TO ORGANIZED STRUCTURE")
    print("-" * 60)
    
    # Get all files in root directory (excluding directories and special files)
    all_files = []
    for item in os.listdir(workspace):
        item_path = os.path.join(workspace, item)
        if os.path.isfile(item_path) and not item.startswith('.') and item not in ['README.md']:
            all_files.append(item)
    
    print(f"Found {len(all_files)} files to organize")
    
    # Track moved files
    moved_files = {}
    remaining_files = all_files.copy()
    
    # Move files according to patterns
    for dest_dir, patterns in file_moves.items():
        dest_path = os.path.join(workspace, dest_dir)
        moved_files[dest_dir] = []
        
        for pattern in patterns:
            matches = []
            
            if '*' in pattern or '?' in pattern:
                # Use glob pattern matching
                matches = [f for f in remaining_files if matches_pattern(f, pattern)]
            else:
                # Exact match
                if pattern in remaining_files:
                    matches = [pattern]
            
            for filename in matches:
                if filename in remaining_files:
                    source_path = os.path.join(workspace, filename)
                    dest_file_path = os.path.join(dest_path, filename)
                    
                    try:
                        shutil.move(source_path, dest_file_path)
                        moved_files[dest_dir].append(filename)
                        remaining_files.remove(filename)
                        moved_count += 1
                        print(f"✓ Moved {filename} to {dest_dir}")
                    except Exception as e:
                        print(f"✗ Error moving {filename}: {e}")
    
    # Move any remaining files to src/utils
    if remaining_files:
        print(f"\n📁 Moving {len(remaining_files)} remaining files to src/utils")
        for filename in remaining_files:
            if filename not in ['README.md', 'check_organization.py']:  # Keep these
                source_path = os.path.join(workspace, filename)
                dest_file_path = os.path.join(workspace, "src/utils", filename)
                
                try:
                    shutil.move(source_path, dest_file_path)
                    moved_count += 1
                    print(f"✓ Moved {filename} to src/utils")
                except Exception as e:
                    print(f"✗ Error moving {filename}: {e}")
    
    print("\n" + "=" * 60)
    print(f"🎉 CLEANUP COMPLETE!")
    print(f"✅ Moved {moved_count} files")
    print(f"✅ Repository is now organized and clean!")
    print("=" * 60)
    
    return moved_count

def matches_pattern(filename, pattern):
    """Simple pattern matching"""
    import fnmatch
    return fnmatch.fnmatch(filename, pattern)

if __name__ == "__main__":
    aggressive_cleanup()
