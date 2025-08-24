#!/usr/bin/env python3
"""
REPOSITORY CLEANUP AND AUDIT TOOL
==================================
Clean up duplicate, outdated, and low-quality scripts while preserving working tools.
"""

import os
import shutil
from pathlib import Path
import json
from datetime import datetime

class RepositoryAuditor:
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.cleanup_report = {
            'files_removed': [],
            'files_kept': [],
            'directories_removed': [],
            'cleanup_date': datetime.now().isoformat(),
            'summary': {}
        }
        
    def audit_and_cleanup(self):
        """Perform comprehensive repository audit and cleanup"""
        print("🔍 REPOSITORY AUDIT AND CLEANUP")
        print("=" * 40)
        
        # 1. Remove obvious duplicates and low-quality scripts
        self._remove_duplicate_scripts()
        
        # 2. Clean up root directory clutter
        self._clean_root_directory()
        
        # 3. Organize archive directories
        self._organize_archives()
        
        # 4. Ensure core tools are in place
        self._verify_core_tools()
        
        # 5. Generate cleanup report
        self._generate_cleanup_report()
    
    def _remove_duplicate_scripts(self):
        """Remove obvious duplicate and low-quality scripts"""
        print("🗑️  Removing duplicate and outdated scripts...")
        
        # Scripts to remove (obvious duplicates or poor quality)
        remove_patterns = [
            # Duplicate balance checkers
            'check_*_keys.py',
            'check_*_batch*.py',
            'check_*_parallel.py',
            'check_*_priority.py',
            'check_*_sample.py',
            'check_*_extended.py',
            
            # Duplicate extractors
            'extract_*_keys.py',
            'extract_*_sample.py',
            'extract_*_cache*.py',
            'extract_*_private_keys.py',
            
            # Analysis duplicates
            '*_analyzer.py',
            '*_investigator.py',
            '*_tracer.py',
            '*_locator.py',
            '*_finder.py',
            '*_verifier.py',
            '*_validator.py',
            '*_checker.py',
            '*_monitor.py',
            
            # Strategy and planning scripts (outdated)
            '*_strategy.py',
            '*_plan.py',
            'phase*_*.py',
            'week*_*.py',
            'next_*.py',
            'final_*.py',
            'ultimate_*.py',
            'advanced_*.py',
            'enhanced_*.py',
            'comprehensive_*.py',
            
            # Network-specific duplicates
            'net*_*.py',
            '*_net*.py',
            
            # Misc cleanup files
            '*_cleanup*.py',
            '*_organizer*.py',
            'aggressive_*.py',
            'system_*.py',
            'workspace_*.py',
            
            # Temporary and test files
            '*_test*.py',
            'temp_*.py',
            'debug_*.py',
            'sample_*.py',
            'preview_*.py',
        ]
        
        removed_count = 0
        for pattern in remove_patterns:
            for file_path in self.repo_path.glob(pattern):
                if file_path.is_file() and file_path.suffix == '.py':
                    try:
                        file_path.unlink()
                        self.cleanup_report['files_removed'].append(str(file_path))
                        removed_count += 1
                    except Exception as e:
                        print(f"⚠️  Could not remove {file_path}: {e}")
        
        print(f"   Removed {removed_count} duplicate/outdated scripts")
    
    def _clean_root_directory(self):
        """Clean up the root directory of clutter"""
        print("🧹 Cleaning root directory...")
        
        # Files to definitely keep
        keep_files = {
            'README.md',
            'requirements.txt', 
            'setup.sh',
            '.gitignore',
            '.env',
            'api_config.json.example',
            'api_config.json'
        }
        
        # Directories to keep
        keep_dirs = {
            '.git',
            '.vscode', 
            'src',
            'docs',
            'archive',
            'data',
            'logs',
            'venv',
            'tests'
        }
        
        # Remove clutter from root
        removed_count = 0
        for item in self.repo_path.iterdir():
            if item.name.startswith('.'):
                continue
                
            if item.is_file():
                if (item.name not in keep_files and 
                    item.suffix == '.py' and
                    'wallet_recovery_results_' not in item.name):
                    try:
                        item.unlink()
                        self.cleanup_report['files_removed'].append(str(item))
                        removed_count += 1
                    except Exception:
                        pass
            
            elif item.is_dir() and item.name not in keep_dirs:
                # Remove temporary/cache directories
                if any(temp in item.name.lower() for temp in 
                       ['temp', 'cache', 'backup', 'security_', 'final_', 'archive_']):
                    try:
                        shutil.rmtree(item)
                        self.cleanup_report['directories_removed'].append(str(item))
                        removed_count += 1
                    except Exception:
                        pass
        
        print(f"   Cleaned {removed_count} items from root directory")
    
    def _organize_archives(self):
        """Organize archive directories"""
        print("📁 Organizing archives...")
        
        # Ensure archive directory structure
        archive_dir = self.repo_path / 'archive'
        if not archive_dir.exists():
            archive_dir.mkdir()
        
        # Move old archive directories into main archive
        archive_patterns = ['Archive', 'ARCHIVE_*', 'FINAL_BACKUP_*', 'security_backup_*']
        
        moved_count = 0
        for pattern in archive_patterns:
            for old_archive in self.repo_path.glob(pattern):
                if old_archive.is_dir() and old_archive.name != 'archive':
                    try:
                        new_location = archive_dir / old_archive.name
                        if not new_location.exists():
                            shutil.move(str(old_archive), str(new_location))
                            moved_count += 1
                    except Exception:
                        pass
        
        print(f"   Organized {moved_count} archive directories")
    
    def _verify_core_tools(self):
        """Verify that core tools are present and working"""
        print("✅ Verifying core tools...")
        
        core_tools = {
            'src/core/professional_wallet_recovery.py': 'Main recovery tool',
            'src/security/security_hardening.py': 'Security utilities',
            'src/utils/status_dashboard.py': 'Status monitoring',
            'setup.sh': 'Environment setup',
            'requirements.txt': 'Dependencies',
            'README.md': 'Documentation'
        }
        
        missing_tools = []
        for tool_path, description in core_tools.items():
            full_path = self.repo_path / tool_path
            if not full_path.exists():
                missing_tools.append(f"{tool_path} ({description})")
            else:
                self.cleanup_report['files_kept'].append(str(full_path))
        
        if missing_tools:
            print("⚠️  Missing core tools:")
            for tool in missing_tools:
                print(f"   - {tool}")
        else:
            print("   All core tools verified ✓")
    
    def _generate_cleanup_report(self):
        """Generate comprehensive cleanup report"""
        print("\n" + "="*50)
        print("📊 CLEANUP REPORT")
        print("="*50)
        
        removed_files = len(self.cleanup_report['files_removed'])
        removed_dirs = len(self.cleanup_report['directories_removed'])
        kept_files = len(self.cleanup_report['files_kept'])
        
        self.cleanup_report['summary'] = {
            'files_removed': removed_files,
            'directories_removed': removed_dirs,
            'files_kept': kept_files,
            'total_cleaned': removed_files + removed_dirs
        }
        
        print(f"Files removed: {removed_files}")
        print(f"Directories removed: {removed_dirs}")
        print(f"Core files kept: {kept_files}")
        print(f"Total items cleaned: {removed_files + removed_dirs}")
        
        # Save detailed report
        report_file = self.repo_path / 'repository_cleanup_report.json'
        with open(report_file, 'w') as f:
            json.dump(self.cleanup_report, f, indent=2)
        
        print(f"\n📁 Detailed report saved to: {report_file}")
        print("\n🎯 REPOSITORY CLEANUP COMPLETE!")
        print("Your repository is now clean and organized.")

def main():
    """Main entry point"""
    current_dir = os.getcwd()
    
    auditor = RepositoryAuditor(current_dir)
    auditor.audit_and_cleanup()

if __name__ == "__main__":
    main()
