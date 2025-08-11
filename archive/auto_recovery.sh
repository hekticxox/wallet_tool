#!/bin/bash
# Auto-recovery for continuous balance checker - for use with crontab

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_FILE="$SCRIPT_DIR/auto_recovery.log"
cd "$SCRIPT_DIR"

# Check if continuous checker is running
if ! pgrep -f "continuous_checker.py" > /dev/null; then
    echo "$(date): Continuous checker not running. Starting it..." >> "$LOG_FILE"
    
    # Clean up any zombies
    pkill -f "continuous_checker.py"
    sleep 2
    
    # Start the continuous checker with unbuffered output
    nohup python3 -u continuous_checker.py > balance_checker.log 2>&1 &
    
    # Verify it started
    sleep 3
    if pgrep -f "continuous_checker.py" > /dev/null; then
        echo "$(date): Successfully restarted continuous checker (PID: $(pgrep -f 'continuous_checker.py'))" >> "$LOG_FILE"
    else
        echo "$(date): FAILED to start continuous checker" >> "$LOG_FILE"
    fi
else
    # Optional: log that it's running (comment out if too verbose)
    # echo "$(date): Continuous checker is running normally" >> "$LOG_FILE"
    :
fi
