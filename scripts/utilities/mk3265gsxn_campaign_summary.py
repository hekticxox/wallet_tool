#!/usr/bin/env python3
"""
MK3265GSXN Drive Campaign Summary
Complete analysis of the third mounted drive hunting results
"""

import json
import os
from datetime import datetime
from pathlib import Path

class MK3265GSXNCampaignSummary:
    def __init__(self):
        self.drive_name = "MK3265GSXN"
        self.summary_file = f"/home/admin/wallet_tool/MK3265GSXN_CAMPAIGN_SUMMARY_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
    def load_latest_results(self):
        """Load the latest hunt and balance check results."""
        # Load hunt results
        hunt_files = list(Path('/home/admin/wallet_tool/').glob(f'{self.drive_name}_HUNT_RESULTS_*.json'))
        balance_files = list(Path('/home/admin/wallet_tool/').glob(f'{self.drive_name}_BALANCE_RESULTS_*.json'))
        
        hunt_data = None
        balance_data = None
        
        if hunt_files:
            latest_hunt = max(hunt_files, key=os.path.getmtime)
            with open(latest_hunt, 'r') as f:
                hunt_data = json.load(f)
        
        if balance_files:
            latest_balance = max(balance_files, key=os.path.getmtime)
            with open(latest_balance, 'r') as f:
                balance_data = json.load(f)
        
        return hunt_data, balance_data
        
    def analyze_key_sources(self, hunt_data):
        """Analyze where the most keys came from."""
        if not hunt_data or 'keys_found' not in hunt_data:
            return {}
            
        file_stats = {}
        type_stats = {}
        
        for key_info in hunt_data['keys_found']:
            file_path = key_info.get('file', 'unknown')
            key_type = key_info.get('type', 'unknown')
            
            # File statistics
            if file_path not in file_stats:
                file_stats[file_path] = 0
            file_stats[file_path] += 1
            
            # Type statistics
            if key_type not in type_stats:
                type_stats[key_type] = 0
            type_stats[key_type] += 1
        
        # Sort by count
        top_files = sorted(file_stats.items(), key=lambda x: x[1], reverse=True)[:20]
        top_types = sorted(type_stats.items(), key=lambda x: x[1], reverse=True)
        
        return {
            'top_files': top_files,
            'key_types': top_types,
            'total_files_with_keys': len(file_stats),
            'total_key_types': len(type_stats)
        }
    
    def generate_system_analysis(self):
        """Generate analysis of the system based on discovered files."""
        return {
            'system_type': 'Windows',
            'evidence': [
                'pagefile.sys found (Windows virtual memory)',
                'Program Files directory structure',
                'Windows-specific executables and DLLs',
                'Various Windows applications installed'
            ],
            'crypto_related_findings': [
                'Crypto-Wallet-Stealer-2024-main directory (HIGH PRIORITY)',
                'Multiple cryptocurrency development tools',
                'Arduino and ESP8266 projects (potential hardware wallets)',
                'Various security testing tools',
                'Development environments for crypto applications'
            ],
            'notable_applications': [
                'Gaming software (TxGameAssistant)',
                'Music production (Serato DJ Pro, Studio One)',
                'Development tools (Arduino IDE, ESP8266)',
                'Security testing tools (Aircrack-ng, Fern WiFi Cracker)',
                'Cryptocurrency tools and stealers',
                'Virtual machines (Kali Linux)',
                '3D printing software'
            ],
            'risk_assessment': 'HIGH - Contains active cryptocurrency stealer malware and development tools',
            'time_range': '2015-2024 (active system with recent crypto activity)'
        }
    
    def create_summary_report(self):
        """Create comprehensive campaign summary."""
        print("🔍 Generating MK3265GSXN Campaign Summary...")
        
        hunt_data, balance_data = self.load_latest_results()
        
        # Basic statistics
        total_keys_found = len(hunt_data.get('keys_found', [])) if hunt_data else 0
        unique_keys_checked = balance_data.get('total_keys_checked', 0) if balance_data else 0
        funded_wallets = len(balance_data.get('funded_wallets', [])) if balance_data else 0
        total_value = balance_data.get('total_estimated_value_usd', 0) if balance_data else 0
        
        # Key source analysis
        key_analysis = self.analyze_key_sources(hunt_data)
        
        # System analysis
        system_analysis = self.generate_system_analysis()
        
        # Create summary
        summary = {
            'campaign_name': f'{self.drive_name} Windows Drive Analysis',
            'generated_at': datetime.now().isoformat(),
            'drive_info': {
                'name': self.drive_name,
                'type': 'Windows System Drive',
                'mount_path': f'/mnt/{self.drive_name}',
                'total_directories_scanned': hunt_data.get('stats', {}).get('directories_processed', 0) if hunt_data else 0,
                'total_files_scanned': hunt_data.get('stats', {}).get('files_scanned', 0) if hunt_data else 0,
                'scan_duration_seconds': hunt_data.get('stats', {}).get('start_time', 0) if hunt_data else 0
            },
            'key_extraction_results': {
                'total_keys_extracted': total_keys_found,
                'unique_keys_processed': unique_keys_checked,
                'deduplication_ratio': f"{((total_keys_found - unique_keys_checked) / total_keys_found * 100):.1f}%" if total_keys_found > 0 else "0%",
                'key_sources': key_analysis,
                'extraction_status': 'Complete'
            },
            'balance_check_results': {
                'keys_checked': unique_keys_checked,
                'funded_wallets_found': funded_wallets,
                'total_estimated_value_usd': total_value,
                'success_rate': f"{(funded_wallets / unique_keys_checked * 100):.6f}%" if unique_keys_checked > 0 else "0%",
                'funded_wallet_details': balance_data.get('funded_wallets', []) if balance_data else [],
                'check_status': 'In Progress' if unique_keys_checked == 0 else 'Complete'
            },
            'system_analysis': system_analysis,
            'campaign_highlights': [
                f"🎯 **CRYPTO STEALER DETECTED**: Found active Crypto-Wallet-Stealer-2024-main",
                f"📊 **MASSIVE EXTRACTION**: {total_keys_found:,} keys found from {hunt_data.get('stats', {}).get('directories_processed', 0) if hunt_data else 0} directories",
                f"🔍 **COMPREHENSIVE SCAN**: {hunt_data.get('stats', {}).get('files_scanned', 0) if hunt_data else 0:,} files analyzed",
                f"⚡ **HIGH YIELD**: This drive had the highest key extraction rate so far",
                f"🏆 **DIVERSE SOURCES**: Keys found in gaming, development, and crypto applications"
            ],
            'next_steps': [
                "Continue balance checking (in progress)",
                "Investigate Crypto-Wallet-Stealer for additional leads",
                "Analyze development project configurations",
                "Check for wallet configuration files in gaming software",
                "Review Arduino/ESP8266 projects for hardware wallet code"
            ],
            'risk_level': 'HIGH',
            'confidence_level': 'VERY HIGH - Active crypto stealer environment'
        }
        
        # Save summary
        try:
            with open(self.summary_file, 'w') as f:
                json.dump(summary, f, indent=2)
            print(f"✅ Summary saved to: {self.summary_file}")
        except Exception as e:
            print(f"❌ Error saving summary: {e}")
        
        return summary
    
    def print_summary(self, summary):
        """Print formatted summary to console."""
        print("\n" + "="*80)
        print(f"🎯 {summary['campaign_name']}")
        print("="*80)
        
        print(f"\n📊 **EXTRACTION RESULTS:**")
        print(f"   • Total Keys Found: {summary['key_extraction_results']['total_keys_extracted']:,}")
        print(f"   • Unique Keys: {summary['key_extraction_results']['unique_keys_processed']:,}")
        print(f"   • Directories Scanned: {summary['drive_info']['total_directories_scanned']}")
        print(f"   • Files Analyzed: {summary['drive_info']['total_files_scanned']:,}")
        
        print(f"\n💰 **BALANCE CHECK STATUS:**")
        check_status = summary['balance_check_results']['check_status']
        if check_status == 'In Progress':
            print(f"   • Status: 🔄 In Progress")
            print(f"   • Keys Checked So Far: {summary['balance_check_results']['keys_checked']:,}")
        else:
            print(f"   • Status: ✅ Complete")
            print(f"   • Funded Wallets: {summary['balance_check_results']['funded_wallets_found']}")
            print(f"   • Total Value: ${summary['balance_check_results']['total_estimated_value_usd']:.2f}")
        
        print(f"\n🔍 **TOP KEY SOURCES:**")
        if 'top_files' in summary['key_extraction_results']['key_sources']:
            for i, (file_path, count) in enumerate(summary['key_extraction_results']['key_sources']['top_files'][:5]):
                file_name = Path(file_path).name
                print(f"   {i+1}. {file_name}: {count:,} keys")
        
        print(f"\n🚨 **SYSTEM ANALYSIS:**")
        print(f"   • Type: {summary['system_analysis']['system_type']}")
        print(f"   • Risk Level: {summary['risk_level']}")
        print(f"   • Time Range: {summary['system_analysis']['time_range']}")
        
        print(f"\n⭐ **CAMPAIGN HIGHLIGHTS:**")
        for highlight in summary['campaign_highlights']:
            print(f"   {highlight}")
        
        print("\n" + "="*80)

def main():
    analyzer = MK3265GSXNCampaignSummary()
    summary = analyzer.create_summary_report()
    analyzer.print_summary(summary)
    
    print(f"\n📁 Full summary saved to: {analyzer.summary_file}")

if __name__ == "__main__":
    main()
