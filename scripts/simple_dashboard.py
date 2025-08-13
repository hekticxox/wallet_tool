#!/usr/bin/env python3
"""
Simple Dashboard for Unified Wallet Scanner
Real-time monitoring of scanner progress and results
"""

import os
import json
import time
import sqlite3
import subprocess
from datetime import datetime, timedelta

class SimpleDashboard:
    def __init__(self):
        self.clear_screen()
        
    def clear_screen(self):
        """Clear terminal screen"""
        os.system('clear' if os.name == 'posix' else 'cls')
    
    def get_scanner_processes(self):
        """Get running scanner processes"""
        try:
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
            processes = []
            
            for line in result.stdout.split('\n'):
                if 'unified_wallet_scanner.py' in line and 'python' in line:
                    parts = line.split()
                    if len(parts) >= 11:
                        processes.append({
                            'pid': parts[1],
                            'cpu': parts[2],
                            'memory': parts[3],
                            'command': ' '.join(parts[10:])
                        })
            
            return processes
        except:
            return []
    
    def get_database_stats(self):
        """Get statistics from address tracking database"""
        if not os.path.exists('address_tracking.db'):
            return None
        
        try:
            conn = sqlite3.connect('address_tracking.db')
            
            # Total addresses
            cursor = conn.execute("SELECT COUNT(*) FROM checked_addresses")
            total_addresses = cursor.fetchone()[0]
            
            # Unique addresses
            cursor = conn.execute("SELECT COUNT(DISTINCT address) FROM checked_addresses")
            unique_addresses = cursor.fetchone()[0]
            
            # Funded addresses
            cursor = conn.execute("SELECT COUNT(*) FROM checked_addresses WHERE balance > 0")
            funded_count = cursor.fetchone()[0]
            
            # Total balance
            cursor = conn.execute("SELECT SUM(balance) FROM checked_addresses WHERE balance > 0")
            total_balance = cursor.fetchone()[0] or 0
            
            # Chain distribution
            cursor = conn.execute("SELECT chain, COUNT(*) FROM checked_addresses GROUP BY chain")
            chain_stats = dict(cursor.fetchall())
            
            # Recent activity (last hour)
            one_hour_ago = int(time.time()) - 3600
            cursor = conn.execute("SELECT COUNT(*) FROM checked_addresses WHERE checked_timestamp > ?", (one_hour_ago,))
            recent_addresses = cursor.fetchone()[0]
            
            conn.close()
            
            efficiency = ((total_addresses - unique_addresses) / total_addresses * 100) if total_addresses > 0 else 0
            
            return {
                'total_operations': total_addresses,
                'unique_addresses': unique_addresses,
                'duplicates_prevented': total_addresses - unique_addresses,
                'efficiency_percent': efficiency,
                'funded_addresses': funded_count,
                'total_balance': total_balance,
                'chain_distribution': chain_stats,
                'recent_activity': recent_addresses
            }
        except Exception as e:
            return {'error': str(e)}
    
    def get_progress_data(self):
        """Get progress from progress file"""
        if os.path.exists('unified_scanner_progress.json'):
            try:
                with open('unified_scanner_progress.json', 'r') as f:
                    return json.load(f)
            except:
                return None
        return None
    
    def get_consolidated_results(self):
        """Get consolidated funded addresses"""
        if os.path.exists('funded_addresses_consolidated.json'):
            try:
                with open('funded_addresses_consolidated.json', 'r') as f:
                    return json.load(f)
            except:
                return None
        return None
    
    def format_time(self, seconds):
        """Format seconds into readable time"""
        return str(timedelta(seconds=int(seconds)))
    
    def format_number(self, num):
        """Format number with commas"""
        return f"{num:,}" if isinstance(num, (int, float)) else str(num)
    
    def create_progress_bar(self, percentage, width=30):
        """Create ASCII progress bar"""
        filled = int(width * percentage / 100)
        bar = "█" * filled + "░" * (width - filled)
        return f"[{bar}] {percentage:.1f}%"
    
    def display_dashboard(self):
        """Display the main dashboard"""
        
        # Header
        print("="*80)
        print("🔍 UNIFIED WALLET SCANNER - LIVE DASHBOARD".center(80))
        print(f"📊 Real-time System Status - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}".center(80))
        print("="*80)
        
        # Scanner Processes
        processes = self.get_scanner_processes()
        print(f"\n🔄 ACTIVE SCANNERS")
        print("-" * 40)
        if processes:
            for proc in processes:
                runtime_info = proc['command'].split()[-1] if len(proc['command'].split()) > 1 else "scanning..."
                print(f"🟢 PID {proc['pid']}: {runtime_info}")
                print(f"   💻 CPU: {proc['cpu']}% | 🧠 Memory: {proc['memory']}%")
        else:
            print("❌ No active scanners detected")
            print("💡 Start with: python3 unified_wallet_scanner.py [directory]")
        
        # Database Statistics
        print(f"\n🗄️  DATABASE STATISTICS")
        print("-" * 40)
        db_stats = self.get_database_stats()
        if db_stats and 'error' not in db_stats:
            print(f"📊 Total operations: {self.format_number(db_stats['total_operations'])}")
            print(f"🎯 Unique addresses: {self.format_number(db_stats['unique_addresses'])}")
            print(f"🔄 Duplicates prevented: {self.format_number(db_stats['duplicates_prevented'])}")
            print(f"⚡ Efficiency: {db_stats['efficiency_percent']:.1f}%")
            print(f"📈 {self.create_progress_bar(db_stats['efficiency_percent'])}")
            print(f"⏰ Recent activity (1h): {self.format_number(db_stats['recent_activity'])} addresses")
            
            if db_stats.get('chain_distribution') and isinstance(db_stats['chain_distribution'], dict):
                print(f"\n📊 Chain Distribution:")
                for chain, count in db_stats['chain_distribution'].items():
                    print(f"   {chain.upper()}: {self.format_number(count)} addresses")
        else:
            print("❌ Database not accessible or no data")
        
        # Funded Addresses
        print(f"\n💰 FUNDED ADDRESSES")
        print("-" * 40)
        consolidated = self.get_consolidated_results()
        if consolidated:
            print(f"🎉 Total found: {consolidated['total_unique_addresses']}")
            print(f"💎 Total value: {consolidated['total_value']}")
            
            summary = consolidated['summary']
            print(f"🟠 Bitcoin: {summary['bitcoin']} addresses")
            print(f"🟣 Ethereum: {summary['ethereum']} addresses")
            print(f"🟢 Solana: {summary['solana']} addresses")
            
            if consolidated.get('addresses'):
                print(f"\n📋 Latest Findings:")
                for addr in consolidated['addresses'][-3:]:  # Show last 3
                    chain = addr.get('chain', 'unknown').upper()
                    balance = addr.get('balance', 0)
                    address_short = addr.get('address', '')[:20] + '...' if len(addr.get('address', '')) > 20 else addr.get('address', '')
                    print(f"   {chain}: {address_short} (Balance: {balance})")
        else:
            funded_count = db_stats.get('funded_addresses', 0) if db_stats else 0
            total_balance = db_stats.get('total_balance', 0) if db_stats else 0
            
            if (isinstance(funded_count, (int, float)) and funded_count > 0):
                print(f"🎉 Found: {funded_count} addresses")
                if isinstance(total_balance, (int, float)):
                    print(f"💎 Total value: {total_balance}")
            else:
                print("📭 No funded addresses found yet")
        
        # Current Progress
        print(f"\n📊 SCANNING PROGRESS")
        print("-" * 40)
        progress = self.get_progress_data()
        if progress:
            runtime = progress.get('runtime_seconds', 0)
            stats = progress.get('statistics', {})
            
            print(f"⏱️  Runtime: {self.format_time(runtime)}")
            print(f"✅ Addresses checked: {self.format_number(stats.get('addresses_checked', 0))}")
            
            rate = stats.get('addresses_checked', 0) / max(runtime, 1) * 60
            print(f"⚡ Scan rate: {rate:.1f} addresses/minute")
            
            if stats.get('patterns_found'):
                print(f"🎯 Pattern matches: {dict(stats['patterns_found'])}")
        else:
            print("📊 No progress data available")
        
        # System Health
        print(f"\n🏥 SYSTEM HEALTH")
        print("-" * 40)
        
        health_score = 0
        health_issues = []
        
        # Check if scanner is running
        if processes:
            health_score += 30
            print("✅ Scanner processes: Active")
        else:
            health_issues.append("No active scanner processes")
            print("⚠️  Scanner processes: Inactive")
        
        # Check database
        if db_stats and 'error' not in db_stats:
            health_score += 25
            print("✅ Database: Connected")
        else:
            health_issues.append("Database connection issues")
            print("❌ Database: Error")
        
        # Check recent activity
        recent_activity = db_stats.get('recent_activity', 0) if db_stats else 0
        if (db_stats and 
            isinstance(recent_activity, (int, float)) and 
            recent_activity > 0):
            health_score += 25
            print("✅ Recent activity: Detected")
        else:
            health_issues.append("No recent scanning activity")
            print("⚠️  Recent activity: None")
        
        # Check configuration
        if os.path.exists('api_config.json'):
            health_score += 20
            print("✅ Configuration: Loaded")
        else:
            health_issues.append("Missing API configuration")
            print("⚠️  Configuration: Missing")
        
        # Overall health status
        if health_score >= 80:
            status = "🟢 EXCELLENT"
        elif health_score >= 60:
            status = "🟡 GOOD"
        elif health_score >= 40:
            status = "🟠 FAIR"
        else:
            status = "🔴 POOR"
        
        print(f"\n📋 Overall Status: {status} ({health_score}/100)")
        
        if health_issues:
            print(f"⚠️  Issues detected:")
            for issue in health_issues:
                print(f"   • {issue}")
        
        # Footer
        print("\n" + "="*80)
        print("💡 Press Ctrl+C to exit | 🔄 Auto-refresh every 10 seconds")
        print("="*80)
    
    def run(self):
        """Run the dashboard with auto-refresh"""
        try:
            while True:
                self.clear_screen()
                self.display_dashboard()
                time.sleep(10)  # Refresh every 10 seconds
        except KeyboardInterrupt:
            print(f"\n👋 Dashboard shutting down...")

def main():
    dashboard = SimpleDashboard()
    dashboard.run()

if __name__ == "__main__":
    main()
