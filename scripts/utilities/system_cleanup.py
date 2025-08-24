import time
#!/usr/bin/env python3
"""
🧹 COMPREHENSIVE SYSTEM CLEANUP
================================

Advanced cleanup and optimization of the wallet recovery system.
Removes duplicates, organizes files, optimizes storage, and maintains security.
"""

import os
import json
import shutil
from datetime import datetime, timedelta
from pathlib import Path
import hashlib

class SystemCleanup:
    def __init__(self):
        self.removed_files = []
        self.organized_files = []
        self.space_saved = 0
        self.duplicates_found = []
        
    def analyze_and_cleanup(self):
        """Perform comprehensive system cleanup"""
        
        print("""
╔══════════════════════════════════════════════════════════════════╗
║                  🧹 COMPREHENSIVE SYSTEM CLEANUP                 ║
║                    Optimization & Organization                   ║
╚══════════════════════════════════════════════════════════════════╝
        """)
        
        print("🔍 ANALYZING CURRENT SYSTEM STATE")
        print("=" * 70)
        
        # Analyze current state
        total_files = len([f for f in os.listdir('.') if os.path.isfile(f)])
        py_files = len([f for f in os.listdir('.') if f.endswith('.py')])
        json_files = len([f for f in os.listdir('.') if f.endswith('.json')])
        log_files = len([f for f in os.listdir('.') if f.endswith('.log')])
        
        print(f"📊 Current State:")
        print(f"   📁 Total Files: {total_files}")
        print(f"   🐍 Python Scripts: {py_files}")
        print(f"   📋 JSON Files: {json_files}")
        print(f"   📝 Log Files: {log_files}")
        
        # Calculate total size
        total_size = sum(os.path.getsize(f) for f in os.listdir('.') if os.path.isfile(f))
        print(f"   💾 Total Size: {total_size / 1024 / 1024:.2f} MB")
        
        print("\n🧹 CLEANUP OPERATIONS")
        print("=" * 70)
        
        # 1. Remove duplicate files
        self.remove_duplicates()
        
        # 2. Clean old temporary/test files
        self.clean_temp_files()
        
        # 3. Organize files into directories
        self.organize_files()
        
        # 4. Clean old logs and reports
        self.clean_old_logs()
        
        # 5. Optimize JSON files
        self.optimize_json_files()
        
        # 6. Remove empty files
        self.remove_empty_files()
        
        # Generate cleanup report
        self.generate_cleanup_report()
        
    def remove_duplicates(self):
        """Find and remove duplicate files"""
        print("🔍 Scanning for duplicate files...")
        
        file_hashes = {}
        duplicates = []
        
        for file in os.listdir('.'):
            if os.path.isfile(file):
                # Calculate file hash
                with open(file, 'rb') as f:
                    file_hash = hashlib.md5(f.read()).hexdigest()
                
                if file_hash in file_hashes:
                    duplicates.append((file, file_hashes[file_hash]))
                    print(f"   🔄 Duplicate found: {file} = {file_hashes[file_hash]}")
                else:
                    file_hashes[file_hash] = file
        
        # Remove duplicates (keep the one with better name)
        for duplicate, original in duplicates:
            # Keep the file with more descriptive name
            if len(duplicate) < len(original) or 'temp' in original.lower():
                to_remove = original
                to_keep = duplicate
            else:
                to_remove = duplicate
                to_keep = original
            
            try:
                size = os.path.getsize(to_remove)
                os.remove(to_remove)
                self.removed_files.append(to_remove)
                self.space_saved += size
                print(f"   ✅ Removed duplicate: {to_remove}")
            except Exception as e:
                print(f"   ❌ Could not remove {to_remove}: {e}")
        
        if not duplicates:
            print("   ✅ No duplicates found")
    
    def clean_temp_files(self):
        """Remove temporary and test files"""
        print("🗑️ Cleaning temporary files...")
        
        temp_patterns = [
            'temp_', 'tmp_', 'test_', 'debug_', 'backup_',
            '.tmp', '.bak', '.old', '~', '.swp'
        ]
        
        removed_count = 0
        
        for file in os.listdir('.'):
            if os.path.isfile(file):
                should_remove = False
                
                # Check for temp patterns
                for pattern in temp_patterns:
                    if pattern in file.lower():
                        should_remove = True
                        break
                
                # Check for old test files
                if file.startswith('test') and file.endswith('.py'):
                    # Keep if it's a legitimate test file
                    continue
                
                if should_remove:
                    try:
                        size = os.path.getsize(file)
                        os.remove(file)
                        self.removed_files.append(file)
                        self.space_saved += size
                        removed_count += 1
                        print(f"   ✅ Removed temp file: {file}")
                    except Exception as e:
                        print(f"   ❌ Could not remove {file}: {e}")
        
        if removed_count == 0:
            print("   ✅ No temporary files found")
    
    def organize_files(self):
        """Organize files into appropriate directories"""
        print("📁 Organizing files into directories...")
        
        # Create organization structure
        directories = {
            'reports': ['*REPORT*.json', '*_report_*.json', '*AUDIT*.json'],
            'logs': ['*.log', '*_log_*.txt'],
            'backups': ['*_backup_*.json', '*BACKUP*.json'],
            'results': ['*RESULT*.json', '*_results_*.json', '*DISCOVERY*.json'],
            'jackpots': ['*JACKPOT*.json', '*_jackpot_*.json'],
            'configs': ['*config*.json', '*_config_*.json'],
            'archives': ['*.zip', '*.tar.gz', '*.rar']
        }
        
        # Create directories if they don't exist
        for dir_name in directories:
            if not os.path.exists(dir_name):
                os.makedirs(dir_name)
                print(f"   📁 Created directory: {dir_name}/")
        
        # Move files to appropriate directories
        moved_count = 0
        for file in os.listdir('.'):
            if os.path.isfile(file):
                moved = False
                
                for dir_name, patterns in directories.items():
                    for pattern in patterns:
                        # Simple pattern matching
                        pattern_clean = pattern.replace('*', '')
                        if pattern_clean.upper() in file.upper():
                            try:
                                dest_path = os.path.join(dir_name, file)
                                if not os.path.exists(dest_path):
                                    shutil.move(file, dest_path)
                                    self.organized_files.append(f"{file} -> {dir_name}/")
                                    moved_count += 1
                                    print(f"   📂 Moved: {file} -> {dir_name}/")
                                    moved = True
                                    break
                            except Exception as e:
                                print(f"   ❌ Could not move {file}: {e}")
                    
                    if moved:
                        break
        
        if moved_count == 0:
            print("   ✅ Files already organized")
    
    def clean_old_logs(self):
        """Remove old log files and reports"""
        print("🗂️ Cleaning old logs and reports...")
        
        cutoff_date = datetime.now() - timedelta(days=7)  # Keep last 7 days
        removed_count = 0
        
        for file in os.listdir('.'):
            if os.path.isfile(file):
                # Check if it's a log or old report
                if any(keyword in file.lower() for keyword in ['log', 'debug', 'trace']):
                    try:
                        mtime = datetime.fromtimestamp(os.path.getmtime(file))
                        if mtime < cutoff_date:
                            size = os.path.getsize(file)
                            os.remove(file)
                            self.removed_files.append(file)
                            self.space_saved += size
                            removed_count += 1
                            print(f"   ✅ Removed old log: {file}")
                    except Exception as e:
                        print(f"   ❌ Could not process {file}: {e}")
        
        if removed_count == 0:
            print("   ✅ No old logs to remove")
    
    def optimize_json_files(self):
        """Optimize JSON files by removing duplicates and compacting"""
        print("⚡ Optimizing JSON files...")
        
        optimized_count = 0
        space_saved_json = 0
        
        for file in os.listdir('.'):
            if file.endswith('.json') and os.path.isfile(file):
                try:
                    # Read original
                    with open(file, 'r') as f:
                        data = json.load(f)
                    
                    original_size = os.path.getsize(file)
                    
                    # Write optimized (compact)
                    with open(file, 'w') as f:
                        json.dump(data, f, separators=(',', ':'))
                    
                    new_size = os.path.getsize(file)
                    saved = original_size - new_size
                    
                    if saved > 0:
                        space_saved_json += saved
                        optimized_count += 1
                        print(f"   ✅ Optimized: {file} (saved {saved} bytes)")
                
                except Exception as e:
                    print(f"   ❌ Could not optimize {file}: {e}")
        
        self.space_saved += space_saved_json
        
        if optimized_count == 0:
            print("   ✅ JSON files already optimized")
    
    def remove_empty_files(self):
        """Remove empty files"""
        print("🗑️ Removing empty files...")
        
        removed_count = 0
        
        for file in os.listdir('.'):
            if os.path.isfile(file):
                try:
                    if os.path.getsize(file) == 0:
                        os.remove(file)
                        self.removed_files.append(file)
                        removed_count += 1
                        print(f"   ✅ Removed empty file: {file}")
                except Exception as e:
                    print(f"   ❌ Could not check {file}: {e}")
        
        if removed_count == 0:
            print("   ✅ No empty files found")
    
    def generate_cleanup_report(self):
        """Generate final cleanup report"""
        print("\n📊 CLEANUP SUMMARY")
        print("=" * 70)
        
        # Final state analysis
        final_files = len([f for f in os.listdir('.') if os.path.isfile(f)])
        final_py = len([f for f in os.listdir('.') if f.endswith('.py')])
        final_json = len([f for f in os.listdir('.') if f.endswith('.json')])
        final_size = sum(os.path.getsize(f) for f in os.listdir('.') if os.path.isfile(f))
        
        print(f"✅ Files Removed: {len(self.removed_files)}")
        print(f"📂 Files Organized: {len(self.organized_files)}")
        print(f"💾 Space Saved: {self.space_saved / 1024:.2f} KB")
        print(f"📁 Final File Count: {final_files}")
        print(f"📊 Final Size: {final_size / 1024 / 1024:.2f} MB")
        
        # Detailed report
        cleanup_report = {
            'timestamp': datetime.now().isoformat(),
            'operation': 'System Cleanup',
            'files_removed': self.removed_files,
            'files_organized': self.organized_files,
            'space_saved_bytes': self.space_saved,
            'final_stats': {
                'total_files': final_files,
                'python_files': final_py,
                'json_files': final_json,
                'total_size_mb': final_size / 1024 / 1024
            },
            'directories_created': list(set([f.split(' -> ')[1] for f in self.organized_files if ' -> ' in f])),
            'optimization_level': 'COMPREHENSIVE'
        }
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"SYSTEM_CLEANUP_REPORT_{timestamp}.json"
        
        with open(report_file, 'w') as f:
            json.dump(cleanup_report, f, indent=2)
        
        print(f"\n📋 Detailed report saved: {report_file}")
        
        print("\n" + "=" * 80)
        print("🎉 CLEANUP COMPLETED SUCCESSFULLY")
        print("=" * 80)
        print("✅ System optimized and organized")
        print("✅ Duplicate files removed") 
        print("✅ Storage space optimized")
        print("✅ File structure organized")
        print("✅ System ready for optimal performance")
        print("=" * 80)

def main():
    """Main cleanup execution"""
    cleanup = SystemCleanup()
    cleanup.analyze_and_cleanup()

if __name__ == "__main__":
    main()
