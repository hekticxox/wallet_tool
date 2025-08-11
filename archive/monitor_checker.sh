#!/bin/bash
# Continuous Balance Checker Monitor Script

echo "🔍 CONTINUOUS BALANCE CHECKER STATUS MONITOR"
echo "============================================="
echo ""

# Check if process is running
if pgrep -f "continuous_checker.py" > /dev/null; then
    PID=$(pgrep -f "continuous_checker.py")
    echo "✅ Continuous checker is RUNNING (PID: $PID)"
    
    # Show process details
    echo ""
    echo "📊 Process Info:"
    ps aux | grep $PID | grep -v grep | head -1
    
    # Show recent log activity
    echo ""
    echo "📝 Recent Activity (last 10 lines):"
    if [ -f "balance_checker.log" ]; then
        tail -10 balance_checker.log
    else
        echo "   No log file found"
    fi
    
    # Show progress from history file
    echo ""
    echo "📈 Checking Progress:"
    if [ -f "checked_addresses_history.json" ]; then
        CHECKED=$(wc -l < checked_addresses_history.json)
        echo "   Addresses checked: $((CHECKED - 1))"  # Subtract 1 for JSON formatting
        echo "   Estimated remaining: ~366,000"
        
        # Show funded addresses found
        if [ -f "FUNDED_ADDRESSES.txt" ]; then
            FUNDED=$(wc -l < FUNDED_ADDRESSES.txt)
            echo "   💰 FUNDED ADDRESSES FOUND: $FUNDED"
        fi
        
        # Calculate rate
        if [ -f "balance_checker.log" ]; then
            START_TIME=$(stat -c %Y balance_checker.log 2>/dev/null || echo "0")
            CURRENT_TIME=$(date +%s)
            if [ "$START_TIME" != "0" ]; then
                ELAPSED=$((CURRENT_TIME - START_TIME))
                if [ "$ELAPSED" -gt 0 ]; then
                    RATE=$((CHECKED / ELAPSED * 3600))  # addresses per hour
                    echo "   Estimated rate: $RATE addresses/hour"
                fi
            fi
        fi
    else
        echo "   No history file found"
    fi
    
else
    echo "❌ Balance checker is NOT RUNNING"
    echo ""
    echo "🔧 To start it:"
    echo "   nohup python continuous_checker.py > balance_checker.log 2>&1 &"
fi

echo ""
echo "🎯 Commands:"
echo "============"
echo "📊 Monitor:     ./monitor_checker.sh"
echo "📝 View logs:   tail -f balance_checker.log"
echo "⏹️  Stop:       pkill -f continuous_checker.py"
echo "🔄 Restart:     ./restart_checker.sh"
