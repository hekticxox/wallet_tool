#!/bin/bash
"""
Repository Cleanup Script
=========================
Delete redundant, duplicate, and empty scripts after consolidation
"""

cd /home/admin/wallet_tool

echo "🧹 Starting repository cleanup..."

# Define scripts to keep (core functionality)
KEEP_SCRIPTS=(
    "main.py"
)

# Define scripts to delete (duplicates/redundant)
DELETE_SCRIPTS=(
    "ultimate_scanner.py"
    "production_enhanced_scanner.py" 
    "working_production_scanner.py"
    "comprehensive_checker.py"
    "final_comprehensive_checker.py"
    "periodic_balance_checker.py"
    "robust_balance_checker.py"
    "priority_balance_checker.py"
    "enhanced_balance_checker.py"
    "multi_chain_balance_checker.py"
    "mega_dataset_scanner.py"
    "production_monitor.py"
    "breakthrough_monitor.py"
    "success_monitor.py"
    "monitor_discovered_addresses.py"
    "monitor_key_testing.py"
    "monitor_recheck.py"
    "fast_crypto_hunter.py"
    "additional_extractor.py"
    "metamask_vault_decryptor.py"
    "leveldb_crypto_extractor.py"
    "advanced_crypto_key_extractor.py"
    "direct_key_extractor.py"
    "final_key_extractor.py"
    "high_value_extractor.py"
    "analyze_all_results.py"
    "massive_discovery_analysis.py"
    "analyze_scan_results.py"
    "analyze_zelcore_balances.py"
    "wallet_database_integration.py"
    "database_setup.py"
    "setup_production_db.py"
    "api_manager.py"
    "balance_checker_with_apis.py"
    "batch_balance_checker.py"
    "cleanup_completion.py"
    "aggressive_cleanup.py"
    "project_cleanup_organizer.py"
    "workspace_cleanup.py"
    "system_cleanup.py"
)

# Delete redundant scripts
echo "Deleting redundant scripts..."
for script in "${DELETE_SCRIPTS[@]}"; do
    if [ -f "$script" ]; then
        echo "  Deleting $script"
        rm "$script"
    fi
done

# Delete empty files
echo "Deleting empty files..."
find . -type f -name "*.py" -size 0 -delete
find . -type f -name "*.txt" -size 0 -delete
find . -type f -name "*.json" -size 0 -delete

# Delete specific redundant pattern files
echo "Deleting pattern-specific redundant files..."
rm -f check_*.py 2>/dev/null
rm -f extract_*.py 2>/dev/null
rm -f test_*.py 2>/dev/null
rm -f final_*.py 2>/dev/null
rm -f advanced_*.py 2>/dev/null
rm -f quick_*.py 2>/dev/null
rm -f simple_*.py 2>/dev/null
rm -f batch_*.py 2>/dev/null
rm -f enhanced_*.py 2>/dev/null

# Delete decryption result files
rm -f decrypted_*.txt 2>/dev/null
rm -f auto_decrypted_*.txt 2>/dev/null
rm -f electrum_decrypted_*.txt 2>/dev/null

# Delete WIF and key files  
rm -f electrum_wif_*.txt 2>/dev/null
rm -f bitcoin_*.txt 2>/dev/null
rm -f private_key_*.txt 2>/dev/null

echo "✅ Cleanup complete!"

# Show what remains
echo "📊 Remaining files:"
ls -la *.py 2>/dev/null | wc -l
echo "files remaining in root"
