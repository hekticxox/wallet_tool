#!/usr/bin/env python3
"""
PROJECT CLEANUP & ORGANIZATION - AUGUST 2025
Comprehensive cleanup, archiving, and optimization of wallet recovery system
"""

import os
import json
import shutil
from datetime import datetime
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ProjectCleanup:
    def __init__(self):
        self.workspace_path = Path(".")
        self.cleanup_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.cleanup_report = {
            'timestamp': datetime.now().isoformat(),
            'cleanup_actions': [],
            'files_archived': [],
            'files_removed': [],
            'directories_created': [],
            'optimization_results': {},
            'final_structure': {}
        }
        
    def analyze_project_structure(self):
        """Analyze current project structure."""
        logger.info("🔍 Analyzing project structure...")
        
        structure = {
            'python_files': list(self.workspace_path.glob("*.py")),
            'json_files': list(self.workspace_path.glob("*.json")),
            'log_files': list(self.workspace_path.glob("*.log")),
            'md_files': list(self.workspace_path.glob("*.md")),
            'result_files': list(self.workspace_path.glob("*_RESULTS_*.json")),
            'hunt_files': list(self.workspace_path.glob("*_HUNT_*.json")),
            'balance_files': list(self.workspace_path.glob("*_BALANCE_*.json")),
            'summary_files': list(self.workspace_path.glob("*_SUMMARY_*")),
            'audit_files': list(self.workspace_path.glob("*AUDIT*.json")),
            'config_files': list(self.workspace_path.glob("*.example")) + [Path(".env"), Path("api_config.json")],
            'encrypted_files': list(self.workspace_path.glob("*.enc")),
            'directories': [p for p in self.workspace_path.iterdir() if p.is_dir() and not p.name.startswith('.')]
        }
        
        # Count files by category
        for category, files in structure.items():
            print(f"   📊 {category.replace('_', ' ').title()}: {len([f for f in files if f.exists()])}")
        
        return structure
    
    def create_organized_structure(self):
        """Create organized directory structure."""
        logger.info("📁 Creating organized directory structure...")
        
        directories = {
            'scripts/core': 'Core system scripts',
            'scripts/hunters': 'Drive-specific hunters',
            'scripts/checkers': 'Balance checkers and verifiers',
            'scripts/utilities': 'Utility and helper scripts',
            'scripts/archived': 'Archived/legacy scripts',
            'data/campaigns': 'Campaign results and hunt data',
            'data/balances': 'Balance check results',
            'data/summaries': 'Campaign summaries and reports',
            'data/configs': 'Configuration files and templates',
            'data/logs': 'Log files and debug output',
            'data/secure': 'Encrypted and sensitive data',
            'docs/reports': 'Audit reports and documentation',
            'docs/guides': 'Setup and usage guides',
            'temp/backups': 'Temporary and backup files'
        }
        
        for dir_path, description in directories.items():
            full_path = self.workspace_path / dir_path
            if not full_path.exists():
                full_path.mkdir(parents=True, exist_ok=True)
                self.cleanup_report['directories_created'].append(f"{dir_path}: {description}")
                print(f"   ✅ Created: {dir_path}")
    
    def categorize_and_move_files(self):
        """Categorize and move files to appropriate directories."""
        logger.info("🗂️  Categorizing and organizing files...")
        
        # File categorization rules
        file_categories = {
            'scripts/core': [
                'unified_wallet_scanner.py',
                'multi_blockchain_hunter.py', 
                'bitcoin_recovery_system.py',
                'status_dashboard.py'
            ],
            'scripts/hunters': [
                '*_hunter.py',
                '*_extractor.py', 
                '*_scanner.py'
            ],
            'scripts/checkers': [
                '*_checker.py',
                '*_verifier.py',
                '*_validator.py',
                '*_balance*.py'
            ],
            'scripts/utilities': [
                '*_cleanup*.py',
                '*_audit*.py',
                '*_summary*.py',
                '*_report*.py',
                'api_*.py',
                'test_*.py'
            ],
            'data/campaigns': [
                '*_HUNT_RESULTS_*.json',
                '*_HUNT_*.json'
            ],
            'data/balances': [
                '*_BALANCE_*.json',
                '*_RESULTS_*.json'
            ],
            'data/summaries': [
                '*_SUMMARY_*',
                '*_CAMPAIGN_*'
            ],
            'data/logs': [
                '*.log'
            ],
            'data/secure': [
                '*.enc',
                'SECURE_*'
            ],
            'docs/reports': [
                '*AUDIT*.json',
                '*REPORT*.json',
                '*FINDINGS*'
            ],
            'docs/guides': [
                '*.md',
                'README*'
            ],
            'data/configs': [
                '*.json.example',
                'PROCESSED_*.json',
                'requirements.txt'
            ]
        }
        
        moved_files = 0
        
        for target_dir, patterns in file_categories.items():
            target_path = self.workspace_path / target_dir
            
            for pattern in patterns:
                if pattern.startswith('*') or pattern.endswith('*'):
                    # Handle glob patterns
                    matching_files = list(self.workspace_path.glob(pattern))
                else:
                    # Handle exact filenames
                    file_path = self.workspace_path / pattern
                    matching_files = [file_path] if file_path.exists() else []
                
                for file_path in matching_files:
                    if file_path.is_file() and file_path.parent == self.workspace_path:
                        try:
                            new_path = target_path / file_path.name
                            if not new_path.exists():  # Avoid overwriting
                                shutil.move(str(file_path), str(new_path))
                                moved_files += 1
                                print(f"   📁 Moved: {file_path.name} → {target_dir}")
                        except Exception as e:
                            logger.warning(f"Could not move {file_path}: {e}")
        
        print(f"   ✅ Moved {moved_files} files to organized structure")
        self.cleanup_report['optimization_results']['files_moved'] = moved_files
    
    def identify_redundant_files(self):
        """Identify files that can be removed or archived."""
        logger.info("🔍 Identifying redundant and obsolete files...")
        
        # Files to remove (duplicates, test files, etc.)
        remove_patterns = [
            '*_test.py',
            'test_*.py', 
            'quick_*.py',
            'simple_*.py',
            'temp_*.py',
            '*_backup.py',
            '*_old.py',
            '*_copy.py'
        ]
        
        # Files to archive (old but potentially useful)
        archive_patterns = [
            'check_*.py',
            'extract_*.py',
            '*_original.py',
            'batch_*.py',
            'enhanced_*.py'
        ]
        
        files_to_remove = []
        files_to_archive = []
        
        # Find files to remove
        for pattern in remove_patterns:
            matching_files = list(self.workspace_path.rglob(pattern))
            for file_path in matching_files:
                if file_path.is_file():
                    files_to_remove.append(file_path)
        
        # Find files to archive
        for pattern in archive_patterns:
            matching_files = list(self.workspace_path.rglob(pattern))
            for file_path in matching_files:
                if file_path.is_file() and file_path not in files_to_remove:
                    files_to_archive.append(file_path)
        
        return files_to_remove, files_to_archive
    
    def archive_old_files(self, files_to_archive):
        """Archive old but potentially useful files."""
        logger.info("📦 Archiving old files...")
        
        archive_dir = self.workspace_path / 'scripts' / 'archived'
        archive_dir.mkdir(parents=True, exist_ok=True)
        
        archived_count = 0
        for file_path in files_to_archive:
            try:
                if file_path.exists():
                    new_path = archive_dir / file_path.name
                    if not new_path.exists():
                        shutil.move(str(file_path), str(new_path))
                        archived_count += 1
                        self.cleanup_report['files_archived'].append(str(file_path))
                        print(f"   📦 Archived: {file_path.name}")
            except Exception as e:
                logger.warning(f"Could not archive {file_path}: {e}")
        
        print(f"   ✅ Archived {archived_count} files")
        return archived_count
    
    def remove_redundant_files(self, files_to_remove):
        """Remove redundant and unnecessary files."""
        logger.info("🗑️  Removing redundant files...")
        
        # Be conservative - only remove obvious test/temp files
        safe_remove_patterns = [
            'temp_', 'test_', 'quick_', '_test.', '_temp.'
        ]
        
        removed_count = 0
        for file_path in files_to_remove:
            # Only remove if filename contains safe patterns
            if any(pattern in file_path.name.lower() for pattern in safe_remove_patterns):
                try:
                    if file_path.exists() and file_path.is_file():
                        file_path.unlink()
                        removed_count += 1
                        self.cleanup_report['files_removed'].append(str(file_path))
                        print(f"   🗑️  Removed: {file_path.name}")
                except Exception as e:
                    logger.warning(f"Could not remove {file_path}: {e}")
        
        print(f"   ✅ Removed {removed_count} redundant files")
        return removed_count
    
    def clean_empty_directories(self):
        """Remove empty directories."""
        logger.info("📁 Cleaning empty directories...")
        
        removed_dirs = 0
        for dir_path in self.workspace_path.rglob("*"):
            if dir_path.is_dir() and not dir_path.name.startswith('.'):
                try:
                    # Check if directory is empty
                    if not any(dir_path.iterdir()):
                        dir_path.rmdir()
                        removed_dirs += 1
                        print(f"   🗑️  Removed empty directory: {dir_path}")
                except Exception as e:
                    pass  # Directory not empty or permission issue
        
        return removed_dirs
    
    def optimize_file_structure(self):
        """Optimize file structure and naming."""
        logger.info("⚡ Optimizing file structure...")
        
        optimizations = {
            'duplicate_jsons_merged': 0,
            'log_files_compressed': 0,
            'config_files_organized': 0
        }
        
        # Move .env and api_config.json to configs if they exist
        config_files = ['.env', 'api_config.json']
        for config_file in config_files:
            source = self.workspace_path / config_file
            if source.exists():
                target = self.workspace_path / 'data' / 'configs' / config_file
                try:
                    if not target.exists():
                        shutil.copy2(str(source), str(target))
                        optimizations['config_files_organized'] += 1
                        print(f"   ⚡ Copied config: {config_file}")
                except Exception as e:
                    logger.warning(f"Could not copy {config_file}: {e}")
        
        self.cleanup_report['optimization_results'].update(optimizations)
        return optimizations
    
    def create_project_index(self):
        """Create an index of the organized project structure."""
        logger.info("📋 Creating project index...")
        
        index = {
            'project_info': {
                'name': 'Wallet Recovery System',
                'version': '2025.08.14',
                'cleanup_date': datetime.now().isoformat(),
                'status': 'Production Ready'
            },
            'directory_structure': {},
            'file_counts': {},
            'key_files': {
                'core_scripts': [],
                'hunters': [],
                'checkers': [],
                'configs': [],
                'documentation': []
            }
        }
        
        # Analyze organized structure
        for root, dirs, files in os.walk(self.workspace_path):
            root_path = Path(root)
            relative_path = root_path.relative_to(self.workspace_path)
            
            if str(relative_path) != '.':
                index['directory_structure'][str(relative_path)] = {
                    'file_count': len(files),
                    'subdirectories': dirs,
                    'files': files[:10]  # First 10 files as sample
                }
        
        # Count files by type
        for category in ['scripts', 'data', 'docs']:
            category_path = self.workspace_path / category
            if category_path.exists():
                file_count = len(list(category_path.rglob("*.*")))
                index['file_counts'][category] = file_count
        
        # Save index
        index_file = self.workspace_path / 'PROJECT_INDEX.json'
        with open(index_file, 'w') as f:
            json.dump(index, f, indent=2)
        
        print(f"   ✅ Created project index: PROJECT_INDEX.json")
        return index
    
    def generate_cleanup_report(self):
        """Generate final cleanup report."""
        logger.info("📊 Generating cleanup report...")
        
        # Final statistics
        final_stats = {
            'total_python_files': len(list(self.workspace_path.rglob("*.py"))),
            'total_json_files': len(list(self.workspace_path.rglob("*.json"))),
            'total_directories': len([p for p in self.workspace_path.rglob("*") if p.is_dir()]),
            'organized_structure': True,
            'cleanup_complete': True
        }
        
        self.cleanup_report['final_statistics'] = final_stats
        
        # Save report
        report_file = self.workspace_path / f'CLEANUP_REPORT_{self.cleanup_timestamp}.json'
        with open(report_file, 'w') as f:
            json.dump(self.cleanup_report, f, indent=2)
        
        return report_file
    
    def run_comprehensive_cleanup(self):
        """Execute complete cleanup process."""
        print("🧹 COMPREHENSIVE PROJECT CLEANUP")
        print("=" * 50)
        print(f"📅 Date: {datetime.now().strftime('%B %d, %Y at %H:%M')}")
        print(f"🎯 Goal: Organize, optimize, and maintain project structure")
        print()
        
        # Step 1: Analyze current structure
        structure = self.analyze_project_structure()
        self.cleanup_report['cleanup_actions'].append("Analyzed project structure")
        
        # Step 2: Create organized directory structure
        self.create_organized_structure()
        self.cleanup_report['cleanup_actions'].append("Created organized directory structure")
        
        # Step 3: Categorize and move files
        self.categorize_and_move_files()
        self.cleanup_report['cleanup_actions'].append("Organized files into categories")
        
        # Step 4: Identify redundant files
        files_to_remove, files_to_archive = self.identify_redundant_files()
        
        # Step 5: Archive old files
        archived_count = self.archive_old_files(files_to_archive)
        
        # Step 6: Remove redundant files
        removed_count = self.remove_redundant_files(files_to_remove)
        
        # Step 7: Clean empty directories
        empty_dirs_removed = self.clean_empty_directories()
        
        # Step 8: Optimize structure
        optimizations = self.optimize_file_structure()
        
        # Step 9: Create project index
        project_index = self.create_project_index()
        
        # Step 10: Generate final report
        report_file = self.generate_cleanup_report()
        
        # Summary
        print(f"\n🎯 CLEANUP SUMMARY")
        print("=" * 25)
        print(f"📁 Directories created: {len(self.cleanup_report['directories_created'])}")
        print(f"📦 Files archived: {archived_count}")
        print(f"🗑️  Files removed: {removed_count}")
        print(f"📂 Empty directories cleaned: {empty_dirs_removed}")
        print(f"⚡ Optimizations applied: {sum(optimizations.values())}")
        print(f"📋 Project index created: ✅")
        
        print(f"\n📊 FINAL STATISTICS")
        print("=" * 20)
        final_stats = self.cleanup_report['final_statistics']
        print(f"🐍 Python files: {final_stats['total_python_files']}")
        print(f"📄 JSON files: {final_stats['total_json_files']}")
        print(f"📁 Directories: {final_stats['total_directories']}")
        
        print(f"\n📁 Report saved: {report_file.name}")
        print(f"\n" + "=" * 50)
        print("✅ PROJECT CLEANUP COMPLETE")
        print("🎉 Organized structure ready for long-term maintenance")
        print("=" * 50)
        
        return self.cleanup_report

def main():
    cleanup = ProjectCleanup()
    cleanup.run_comprehensive_cleanup()

if __name__ == "__main__":
    main()
