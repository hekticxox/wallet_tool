#!/usr/bin/env python3
"""
Unified Results Analyzer
========================
Production-grade analysis tool that:
- Analyzes extraction results from all sources
- Provides comprehensive statistics and insights
- Identifies high-value findings
- Generates detailed reports
"""

import os
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - ANALYZER - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('analysis.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class UnifiedResultsAnalyzer:
    """Unified analyzer for all extraction and scanning results"""
    
    def __init__(self, results_dir: str = "."):
        self.results_dir = Path(results_dir)
        self.analysis_data = {}
    
    def find_result_files(self) -> Dict[str, List[Path]]:
        """Find all result files by category"""
        file_categories = {
            'extraction': [],
            'scanning': [],
            'balance_checks': [],
            'monitoring': [],
            'comprehensive': []
        }
        
        # Pattern matching for different result file types
        patterns = {
            'extraction': ['*extraction_results*.json', '*crypto_hunter*.json', '*metamask*.json'],
            'scanning': ['*scan_results*.json', '*fast_scan*.json', '*mega_scan*.json'],
            'balance_checks': ['*balance_check*.json', '*balance_results*.json'],
            'monitoring': ['*monitoring*.json', '*alerts*.json'],
            'comprehensive': ['*comprehensive*.json', '*final*.json', '*ultimate*.json']
        }
        
        for category, pattern_list in patterns.items():
            for pattern in pattern_list:
                file_categories[category].extend(self.results_dir.glob(pattern))
        
        return file_categories
    
    def analyze_extraction_results(self, files: List[Path]) -> Dict[str, Any]:
        """Analyze extraction result files"""
        extraction_summary = {
            'total_files_analyzed': 0,
            'total_findings': 0,
            'findings_by_type': {},
            'sources': {},
            'timeline': []
        }
        
        for file_path in files:
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                
                extraction_summary['total_files_analyzed'] += 1
                
                # Count findings
                findings = data.get('findings', [])
                if isinstance(findings, list):
                    extraction_summary['total_findings'] += len(findings)
                    
                    # Count by type
                    for finding in findings:
                        finding_type = finding.get('type', 'unknown')
                        extraction_summary['findings_by_type'][finding_type] = (
                            extraction_summary['findings_by_type'].get(finding_type, 0) + 1
                        )
                
                # Source tracking
                source = data.get('dataset_path', file_path.stem)
                extraction_summary['sources'][str(source)] = len(findings) if isinstance(findings, list) else 0
                
                # Timeline
                timestamp = data.get('scan_timestamp', data.get('timestamp', 'unknown'))
                extraction_summary['timeline'].append({
                    'file': file_path.name,
                    'timestamp': timestamp,
                    'findings': len(findings) if isinstance(findings, list) else 0
                })
                
            except Exception as e:
                logger.error(f"❌ Error analyzing {file_path}: {e}")
        
        return extraction_summary
    
    def analyze_balance_results(self, files: List[Path]) -> Dict[str, Any]:
        """Analyze balance check results"""
        balance_summary = {
            'total_checks_performed': 0,
            'funded_wallets_found': 0,
            'total_value_found_usd': 0.0,
            'networks_checked': set(),
            'high_value_findings': []
        }
        
        for file_path in files:
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                
                # Count checks
                balance_summary['total_checks_performed'] += data.get('total_keys_checked', 0)
                
                # Count funded wallets
                funded_btc = data.get('funded_bitcoin_wallets', [])
                funded_eth = data.get('funded_ethereum_wallets', [])
                funded_tokens = data.get('token_wallets', [])
                
                if isinstance(funded_btc, list):
                    balance_summary['funded_wallets_found'] += len([w for w in funded_btc if w.get('balance', 0) > 0])
                if isinstance(funded_eth, list):
                    balance_summary['funded_wallets_found'] += len([w for w in funded_eth if w.get('balance', 0) > 0])
                if isinstance(funded_tokens, list):
                    balance_summary['funded_wallets_found'] += len([w for w in funded_tokens if w.get('total_balance_usd', 0) > 0])
                
                # Track networks
                if funded_btc:
                    balance_summary['networks_checked'].add('Bitcoin')
                if funded_eth:
                    balance_summary['networks_checked'].add('Ethereum')
                if funded_tokens:
                    balance_summary['networks_checked'].add('ERC-20 Tokens')
                
                # High value findings (> $100)
                for wallet_list in [funded_btc, funded_eth, funded_tokens]:
                    if isinstance(wallet_list, list):
                        for wallet in wallet_list:
                            value = wallet.get('balance_usd', wallet.get('total_balance_usd', 0))
                            if value > 100:
                                balance_summary['high_value_findings'].append({
                                    'address': wallet.get('address', 'unknown'),
                                    'value_usd': value,
                                    'source_file': file_path.name
                                })
                            balance_summary['total_value_found_usd'] += value
                
            except Exception as e:
                logger.error(f"❌ Error analyzing balance file {file_path}: {e}")
        
        # Convert set to list for JSON serialization
        balance_summary['networks_checked'] = list(balance_summary['networks_checked'])
        
        return balance_summary
    
    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """Generate comprehensive analysis report"""
        logger.info("📊 Generating comprehensive analysis report...")
        
        # Find all result files
        file_categories = self.find_result_files()
        
        # Analyze each category
        report = {
            'analysis_timestamp': datetime.now().isoformat(),
            'report_version': '1.0',
            'summary': {
                'total_result_files_found': sum(len(files) for files in file_categories.values()),
                'categories_analyzed': list(file_categories.keys())
            },
            'extraction_analysis': {},
            'balance_analysis': {},
            'key_insights': [],
            'recommendations': []
        }
        
        # Analyze extractions
        if file_categories['extraction']:
            report['extraction_analysis'] = self.analyze_extraction_results(file_categories['extraction'])
            logger.info(f"✅ Analyzed {len(file_categories['extraction'])} extraction files")
        
        # Analyze balance checks
        balance_files = file_categories['balance_checks'] + file_categories['comprehensive']
        if balance_files:
            report['balance_analysis'] = self.analyze_balance_results(balance_files)
            logger.info(f"✅ Analyzed {len(balance_files)} balance check files")
        
        # Generate insights
        report['key_insights'] = self.generate_insights(report)
        report['recommendations'] = self.generate_recommendations(report)
        
        return report
    
    def generate_insights(self, report: Dict[str, Any]) -> List[str]:
        """Generate key insights from the analysis"""
        insights = []
        
        extraction = report.get('extraction_analysis', {})
        balance = report.get('balance_analysis', {})
        
        # Extraction insights
        if extraction.get('total_findings', 0) > 0:
            insights.append(f"🔑 Total crypto keys/data extracted: {extraction['total_findings']:,}")
            
            top_types = sorted(extraction.get('findings_by_type', {}).items(), 
                             key=lambda x: x[1], reverse=True)[:3]
            if top_types:
                insights.append(f"📊 Top finding types: {', '.join([f'{k}({v})' for k, v in top_types])}")
        
        # Balance insights
        if balance.get('total_checks_performed', 0) > 0:
            insights.append(f"💰 Total balance checks performed: {balance['total_checks_performed']:,}")
            insights.append(f"✅ Funded wallets discovered: {balance['funded_wallets_found']}")
            
            if balance.get('total_value_found_usd', 0) > 0:
                insights.append(f"💵 Total value found: ${balance['total_value_found_usd']:,.2f}")
            
            high_value = len(balance.get('high_value_findings', []))
            if high_value > 0:
                insights.append(f"🏆 High-value wallets (>$100): {high_value}")
        
        return insights
    
    def generate_recommendations(self, report: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        balance = report.get('balance_analysis', {})
        
        if balance.get('funded_wallets_found', 0) > 0:
            recommendations.append("🔄 Set up continuous monitoring for discovered funded wallets")
            recommendations.append("🔐 Secure and backup all private keys for funded wallets immediately")
        
        if balance.get('high_value_findings'):
            recommendations.append("⚠️  Priority: Review and secure high-value wallet findings immediately")
        
        recommendations.append("📈 Consider expanding balance checks to additional networks (Polygon, BSC, etc.)")
        recommendations.append("🔍 Implement periodic re-scanning of discovered wallets for balance changes")
        
        return recommendations
    
    def save_report(self, report: Dict[str, Any], output_file: Optional[str] = None) -> str:
        """Save analysis report to file"""
        if output_file is None:
            output_file = f"unified_analysis_report_{int(time.time())}.json"
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"📄 Analysis report saved to {output_file}")
        return output_file
    
    def print_summary(self, report: Dict[str, Any]):
        """Print analysis summary to console"""
        print("\n" + "=" * 60)
        print("🏆 UNIFIED WALLET RECOVERY ANALYSIS REPORT")
        print("=" * 60)
        
        extraction = report.get('extraction_analysis', {})
        balance = report.get('balance_analysis', {})
        
        print(f"\n📊 EXTRACTION SUMMARY:")
        print(f"   • Total findings: {extraction.get('total_findings', 0):,}")
        print(f"   • Result files analyzed: {extraction.get('total_files_analyzed', 0)}")
        
        if extraction.get('findings_by_type'):
            print(f"   • Finding types:")
            for finding_type, count in extraction['findings_by_type'].items():
                print(f"     - {finding_type}: {count}")
        
        print(f"\n💰 BALANCE CHECK SUMMARY:")
        print(f"   • Total checks performed: {balance.get('total_checks_performed', 0):,}")
        print(f"   • Funded wallets found: {balance.get('funded_wallets_found', 0)}")
        print(f"   • Total value found: ${balance.get('total_value_found_usd', 0):,.2f}")
        print(f"   • Networks checked: {', '.join(balance.get('networks_checked', []))}")
        
        print(f"\n🔍 KEY INSIGHTS:")
        for insight in report.get('key_insights', []):
            print(f"   • {insight}")
        
        print(f"\n💡 RECOMMENDATIONS:")
        for rec in report.get('recommendations', []):
            print(f"   • {rec}")
        
        print("\n" + "=" * 60)

def main():
    """Main analysis function"""
    import argparse
    parser = argparse.ArgumentParser(description="Unified Results Analyzer")
    parser.add_argument("--results-dir", default=".", help="Directory containing result files")
    parser.add_argument("--output", help="Output file name (optional)")
    
    args = parser.parse_args()
    
    analyzer = UnifiedResultsAnalyzer(args.results_dir)
    report = analyzer.generate_comprehensive_report()
    
    # Save report
    output_file = analyzer.save_report(report, args.output)
    
    # Print summary
    analyzer.print_summary(report)
    
    print(f"\n📄 Full report saved to: {output_file}")

if __name__ == "__main__":
    main()
