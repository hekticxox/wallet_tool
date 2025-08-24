#!/bin/bash

echo "🧹 Final cleanup - removing all non-essential scripts..."

cd /home/admin/wallet_tool

# Keep only these essential files
KEEP_FILES=(
    "main.py"
    "database.py"
    "setup.sh"
)

# Get list of all Python files
ALL_PY_FILES=($(ls *.py 2>/dev/null))

# Delete everything except keep files
for file in "${ALL_PY_FILES[@]}"; do
    if [[ ! " ${KEEP_FILES[@]} " =~ " ${file} " ]]; then
        echo "  Deleting $file"
        rm -f "$file"
    fi
done

# Clean up shell scripts except setup.sh
rm -f *.sh 2>/dev/null
rm -f setup.sh 2>/dev/null || echo "setup.sh not found"

# Remove remaining clutter
rm -f *.json 2>/dev/null
rm -f cleanup_repo.sh 2>/dev/null

echo "✅ Final cleanup complete!"
echo "📊 Remaining Python files:"
ls -la *.py 2>/dev/null
