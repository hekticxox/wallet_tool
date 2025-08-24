#!/usr/bin/env python3
"""
📊 SYSTEM STATUS DASHBOARD
=========================

Real-time operational status of the wallet recovery system.
"""

import json
import os
from datetime import datetime, timedelta
import time

def get_system_status():
    """Get comprehensive system status"""
    
    print("""
╔═══════════════════════════════════════════════════════════╗
║              📊 WALLET RECOVERY SYSTEM STATUS              ║
║                    Live Dashboard                         ║
╚═══════════════════════════════════════════════════════════╝
    """)
    
    # Current timestamp
    now = datetime.now()
    print(f"🕐 Status as of: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 🎯 DISCOVERY STATUS
    print("🎯 DISCOVERY STATUS")
    print("=" * 40)
    
    # Count jackpots
    jackpot_files = []
    total_jackpots = 0
    total_eth_wei = 0
    total_btc_sat = 0
    
    for file in os.listdir('.'):
        if 'JACKPOT' in file.upper() and file.endswith('.json'):
            try:
                with open(file, 'r') as f:
                    data = json.load(f)
                
                if isinstance(data, dict):
                    if 'jackpots' in data:
                        for jackpot in data['jackpots']:
                            total_jackpots += 1
                            total_eth_wei += jackpot.get('eth_balance', 0)
                            total_btc_sat += jackpot.get('btc_balance', 0)
                    elif 'private_key' in data:
                        total_jackpots += 1
                        total_eth_wei += data.get('eth_balance', 0)
                        total_btc_sat += data.get('btc_balance', 0)
                
                jackpot_files.append(file)
            except:
                continue
    
    print(f"💎 Total Jackpots: {total_jackpots}")
    print(f"💰 ETH Balance: {total_eth_wei} wei ({total_eth_wei / 10**18:.10f} ETH)")
    print(f"₿  BTC Balance: {total_btc_sat} sat ({total_btc_sat / 10**8:.8f} BTC)")
    print(f"📄 Jackpot Files: {len(jackpot_files)}")
    
    # 🔑 KEY INVENTORY
    print("\n🔑 KEY INVENTORY")
    print("=" * 40)
    
    total_keys = 0
    key_files = 0
    
    for file in os.listdir('.'):
        if 'key' in file.lower() and file.endswith('.json'):
            try:
                with open(file, 'r') as f:
                    data = json.load(f)
                
                count = 0
                if isinstance(data, list):
                    count = len(data)
                elif isinstance(data, dict):
                    if 'private_keys' in data:
                        count = len(data['private_keys'])
                    elif 'keys' in data:
                        count = len(data['keys'])
                
                if count > 0:
                    total_keys += count
                    key_files += 1
            except:
                continue
    
    print(f"📦 Total Keys Available: {total_keys:,}")
    print(f"📁 Key Files: {key_files}")
    
    # 🚀 OPERATIONAL STATUS
    print("\n🚀 OPERATIONAL STATUS")
    print("=" * 40)
    
    # Check core scripts
    core_scripts = [
        'laser_focus_hunter.py',
        'ultimate_jackpot_hunter.py',
        'comprehensive_wallet_scanner.py',
        'enhanced_balance_checker.py',
        'api_manager.py'
    ]
    
    functional_scripts = 0
    for script in core_scripts:
        if os.path.exists(script):
            size = os.path.getsize(script)
            if size > 1000:  # Functional size check
                functional_scripts += 1
    
    print(f"🐍 Core Scripts: {functional_scripts}/{len(core_scripts)} operational")
    
    # Check API config
    api_configured = False
    if os.path.exists('api_config.json'):
        try:
            with open('api_config.json', 'r') as f:
                api_data = json.load(f)
            api_configured = len(api_data) > 0
        except:
            pass
    
    print(f"🔗 API Configuration: {'✅ Ready' if api_configured else '❌ Needs Setup'}")
    
    # Check environment
    venv_ready = os.path.exists('venv')
    requirements_ready = os.path.exists('requirements.txt')
    
    print(f"🔧 Python Environment: {'✅ Ready' if venv_ready and requirements_ready else '❌ Setup Required'}")
    
    # 📈 RECENT ACTIVITY
    print("\n📈 RECENT ACTIVITY (Last 24h)")
    print("=" * 40)
    
    cutoff_time = time.time() - (24 * 60 * 60)
    recent_files = []
    
    for root, dirs, files in os.walk('.'):
        for file in files:
            if not file.startswith('.') and 'venv' not in root:
                filepath = os.path.join(root, file)
                try:
                    mtime = os.path.getmtime(filepath)
                    if mtime > cutoff_time:
                        recent_files.append({
                            'file': filepath,
                            'modified': datetime.fromtimestamp(mtime)
                        })
                except:
                    continue
    
    recent_files.sort(key=lambda x: x['modified'], reverse=True)
    
    print(f"📝 Files Modified: {len(recent_files)}")
    
    if recent_files:
        print("📋 Most Recent:")
        for i, rf in enumerate(recent_files[:5], 1):
            time_ago = now - rf['modified']
            hours = int(time_ago.total_seconds() / 3600)
            minutes = int((time_ago.total_seconds() % 3600) / 60)
            print(f"   {i}. {os.path.basename(rf['file'])} ({hours}h {minutes}m ago)")
    
    # 🎯 SYSTEM HEALTH
    print("\n🎯 SYSTEM HEALTH")
    print("=" * 40)
    
    # Calculate health score
    health_score = 0
    max_score = 100
    
    # Functional scripts (30 points)
    health_score += (functional_scripts / len(core_scripts)) * 30
    
    # API configuration (20 points)
    if api_configured:
        health_score += 20
    
    # Environment ready (20 points)
    if venv_ready and requirements_ready:
        health_score += 20
    
    # Has discoveries (15 points)
    if total_jackpots > 0:
        health_score += 15
    
    # Recent activity (15 points)
    if len(recent_files) > 10:
        health_score += 15
    elif len(recent_files) > 5:
        health_score += 10
    elif len(recent_files) > 0:
        health_score += 5
    
    print(f"❤️  System Health: {health_score:.1f}/{max_score}")
    
    if health_score >= 90:
        status = "🟢 EXCELLENT"
        message = "System operating at peak performance"
    elif health_score >= 80:
        status = "🟡 GOOD"
        message = "System ready with minor optimizations possible"
    elif health_score >= 60:
        status = "🟠 FAIR"
        message = "System functional but improvements recommended"
    else:
        status = "🔴 NEEDS ATTENTION"
        message = "System requires maintenance"
    
    print(f"📊 Status: {status}")
    print(f"💬 Assessment: {message}")
    
    # 🎯 QUICK ACTIONS
    print("\n🎯 QUICK ACTIONS AVAILABLE")
    print("=" * 40)
    
    actions = []
    
    if total_keys > 0 and functional_scripts >= 3:
        actions.append("🚀 python laser_focus_hunter.py - Run precision hunt")
        
    if api_configured:
        actions.append("⚡ python enhanced_balance_checker.py - Check specific addresses")
        
    if len(recent_files) < 5:
        actions.append("🔍 python comprehensive_wallet_scanner.py - Scan new data")
        
    actions.append("📊 python system_auditor.py - Full system audit")
    actions.append("📋 python final_precision_campaign_report.py - Generate report")
    
    for i, action in enumerate(actions, 1):
        print(f"   {i}. {action}")
    
    print("\n" + "=" * 60)
    print("🏁 Dashboard complete - System ready for operations")
    print("=" * 60)

if __name__ == "__main__":
    get_system_status()
