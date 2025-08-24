#!/bin/bash

# Remove empty files final cleanup script
echo "🧹 FINAL EMPTY FILES CLEANUP"
echo "=================================="

# Count files before cleanup
total_files=$(find . -maxdepth 1 -type f | wc -l)
empty_files=$(find . -maxdepth 1 -type f -size 0 | wc -l)

echo "📊 BEFORE CLEANUP:"
echo "Total files in root: $total_files"
echo "Empty files in root: $empty_files"
echo ""

# Remove empty files (but keep important ones)
echo "🗑️ Removing empty files..."

# Remove empty Python files
find . -maxdepth 1 -name "*.py" -size 0 -not -name "__init__.py" -delete

# Remove empty shell scripts  
find . -maxdepth 1 -name "*.sh" -size 0 -delete

# Remove empty text files
find . -maxdepth 1 -name "*.txt" -size 0 -delete

# Remove empty JSON files
find . -maxdepth 1 -name "*.json" -size 0 -delete

# Remove empty config files
find . -maxdepth 1 -name "*.conf" -size 0 -delete
find . -maxdepth 1 -name "*.cfg" -size 0 -delete
find . -maxdepth 1 -name "*.ini" -size 0 -delete

# Remove empty log files
find . -maxdepth 1 -name "*.log" -size 0 -delete

# Count files after cleanup
total_files_after=$(find . -maxdepth 1 -type f | wc -l)
empty_files_after=$(find . -maxdepth 1 -type f -size 0 | wc -l)

echo ""
echo "📊 AFTER CLEANUP:"
echo "Total files in root: $total_files_after"  
echo "Empty files remaining: $empty_files_after"
echo "Files removed: $((total_files - total_files_after))"

if [ $empty_files_after -eq 0 ]; then
    echo "✅ All empty files successfully removed!"
else
    echo "⚠️ Some empty files remain (might be important system files)"
    echo "Remaining empty files:"
    find . -maxdepth 1 -type f -size 0 -ls
fi

echo ""
echo "🎉 Empty files cleanup completed!"
