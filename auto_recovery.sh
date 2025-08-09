#!/bin/bash
# Auto-recovery for continuous balance checker - for use with crontab

LOG_FILE="/home/admin/Desktop/wallet_tool/auto_recovery.log"
cd /home/admin/Desktop/wallet_tool

# Check if continuous checker is running
if ! pgrep -f "continuous_checker.py" > /dev/null; then
    echo "$(date): Continuous checker not running. Starting it..." >> "$LOG_FILE"
    
    # Clean up any zombies
    pkill -f "continuous_checker.py"
    sleep 2
    
    # Start the continuous checker with unbuffered output
    nohup python -u continuous_checker.py > balance_checker.log 2>&1 &
    
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
