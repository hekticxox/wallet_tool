#!/usr/bin/env python3
"""
🔍 COMPREHENSIVE SYSTEM AUDIT
============================

Complete security, performance, and operational audit of the wallet recovery system.
"""

import json
import os
import sys
import hashlib
import time
from datetime import datetime, timedelta
from pathlib import Path
import subprocess
import re

class SystemAuditor:
    def __init__(self):
        self.audit_results = {
            'timestamp': datetime.now().isoformat(),
            'audit_version': '1.0',
            'security_assessment': {},
            'performance_metrics': {},
            'data_integrity': {},
            'operational_status': {},
            'recommendations': []
        }
        
    def security_audit(self):
        """Comprehensive security assessment"""
        print("🔒 SECURITY AUDIT")
        print("=" * 50)
        
        security = {}
        
        # Check sensitive file permissions
        sensitive_files = ['.env', 'api_config.json', '*_keys.json', '*JACKPOT*.json']
        security['file_permissions'] = {}
        
        for pattern in sensitive_files:
            import glob
            files = glob.glob(pattern)
            for file in files:
                if os.path.exists(file):
                    stat = os.stat(file)
                    permissions = oct(stat.st_mode)[-3:]
                    security['file_permissions'][file] = {
                        'permissions': permissions,
                        'secure': permissions in ['600', '644', '660']
                    }
                    
        # Check .gitignore coverage
        gitignore_items = []
        if os.path.exists('.gitignore'):
            with open('.gitignore', 'r') as f:
                gitignore_items = [line.strip() for line in f.readlines() if line.strip() and not line.startswith('#')]
        
        sensitive_patterns = ['.env', 'api_config.json', '*_keys.json', '*JACKPOT*.json', '*.log', '__pycache__']
        security['gitignore_coverage'] = {}
        
        for pattern in sensitive_patterns:
            covered = any(pattern in item or item in pattern for item in gitignore_items)
            security['gitignore_coverage'][pattern] = covered
            
        # API key security check
        api_keys_exposed = []
        if os.path.exists('api_config.json'):
            try:
                with open('api_config.json', 'r') as f:
                    api_data = json.load(f)
                
                for service, config in api_data.items():
                    if isinstance(config, dict) and 'api_key' in config:
                        key = config['api_key']
                        if len(key) > 10:  # Has actual key
                            # Check if key appears in any code files
                            for root, dirs, files in os.walk('.'):
                                for file in files:
                                    if file.endswith('.py') and not file.startswith('.'):
                                        try:
                                            with open(os.path.join(root, file), 'r') as f:
                                                content = f.read()
                                                if key[:10] in content:  # Partial match
                                                    api_keys_exposed.append({
                                                        'service': service,
                                                        'file': file,
                                                        'severity': 'HIGH'
                                                    })
                                        except:
                                            continue
            except:
                pass
                
        security['api_key_exposure'] = api_keys_exposed
        
        # Private key security
        private_key_files = []
        for root, dirs, files in os.walk('.'):
            for file in files:
                if any(keyword in file.lower() for keyword in ['key', 'private', 'secret', 'wallet']):
                    if file.endswith(('.json', '.txt', '.log')):
                        private_key_files.append(os.path.join(root, file))
        
        security['private_key_files'] = len(private_key_files)
        security['private_key_locations'] = private_key_files[:10]  # Sample
        
        # Archive security
        archive_secure = os.path.exists('Archive') or os.path.exists('archive')
        security['sensitive_data_archived'] = archive_secure
        
        self.audit_results['security_assessment'] = security
        
        # Print security summary
        issues = 0
        if api_keys_exposed:
            print(f"❌ API keys exposed in code: {len(api_keys_exposed)}")
            issues += len(api_keys_exposed)
            
        insecure_files = sum(1 for f, data in security['file_permissions'].items() if not data['secure'])
        if insecure_files:
            print(f"⚠️  Insecure file permissions: {insecure_files}")
            issues += insecure_files
            
        uncovered_patterns = sum(1 for pattern, covered in security['gitignore_coverage'].items() if not covered)
        if uncovered_patterns:
            print(f"⚠️  Unprotected sensitive patterns: {uncovered_patterns}")
            issues += uncovered_patterns
            
        if issues == 0:
            print("✅ Security assessment: GOOD")
        else:
            print(f"⚠️  Security issues found: {issues}")
            
        return security
    
    def performance_audit(self):
        """System performance analysis"""
        print("\n⚡ PERFORMANCE AUDIT")
        print("=" * 50)
        
        perf = {}
        
        # File system analysis
        total_files = 0
        total_size = 0
        large_files = []
        
        for root, dirs, files in os.walk('.'):
            for file in files:
                if not file.startswith('.') and 'venv' not in root:
                    filepath = os.path.join(root, file)
                    try:
                        size = os.path.getsize(filepath)
                        total_files += 1
                        total_size += size
                        
                        if size > 10 * 1024 * 1024:  # > 10MB
                            large_files.append({
                                'file': filepath,
                                'size_mb': size / (1024 * 1024)
                            })
                    except:
                        continue
        
        perf['filesystem'] = {
            'total_files': total_files,
            'total_size_mb': total_size / (1024 * 1024),
            'large_files': large_files
        }
        
        # Database analysis
        db_files = []
        for root, dirs, files in os.walk('.'):
            for file in files:
                if file.endswith('.db'):
                    filepath = os.path.join(root, file)
                    try:
                        size = os.path.getsize(filepath)
                        db_files.append({
                            'file': filepath,
                            'size_mb': size / (1024 * 1024)
                        })
                    except:
                        continue
        
        perf['databases'] = db_files
        
        # Log file analysis
        log_files = []
        log_size = 0
        for root, dirs, files in os.walk('.'):
            for file in files:
                if file.endswith('.log'):
                    filepath = os.path.join(root, file)
                    try:
                        size = os.path.getsize(filepath)
                        log_size += size
                        log_files.append({
                            'file': filepath,
                            'size_mb': size / (1024 * 1024)
                        })
                    except:
                        continue
        
        perf['logs'] = {
            'total_files': len(log_files),
            'total_size_mb': log_size / (1024 * 1024),
            'files': log_files
        }
        
        # Memory usage analysis (script count as proxy)
        python_files = []
        for root, dirs, files in os.walk('.'):
            for file in files:
                if file.endswith('.py') and not file.startswith('.') and 'venv' not in root:
                    python_files.append(file)
        
        perf['codebase'] = {
            'python_scripts': len(python_files),
            'estimated_complexity': 'HIGH' if len(python_files) > 50 else 'MODERATE' if len(python_files) > 20 else 'LOW'
        }
        
        self.audit_results['performance_metrics'] = perf
        
        # Print performance summary
        print(f"📁 Total files: {total_files}")
        print(f"💾 Total size: {total_size / (1024 * 1024):.2f} MB")
        print(f"📊 Python scripts: {len(python_files)}")
        print(f"🗄️  Database files: {len(db_files)}")
        print(f"📝 Log files: {len(log_files)} ({log_size / (1024 * 1024):.2f} MB)")
        
        if large_files:
            print(f"⚠️  Large files detected: {len(large_files)}")
            for lf in large_files[:3]:
                print(f"   └─ {lf['file']}: {lf['size_mb']:.2f} MB")
        else:
            print("✅ File sizes: Optimal")
            
        return perf
    
    def data_integrity_audit(self):
        """Data integrity and consistency check"""
        print("\n🔍 DATA INTEGRITY AUDIT")
        print("=" * 50)
        
        integrity = {}
        
        # JSON file validation
        json_files = []
        corrupted_files = []
        
        for root, dirs, files in os.walk('.'):
            for file in files:
                if file.endswith('.json') and 'venv' not in root:
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, 'r') as f:
                            json.load(f)
                        json_files.append(filepath)
                    except json.JSONDecodeError:
                        corrupted_files.append(filepath)
                    except:
                        pass
        
        integrity['json_validation'] = {
            'total_files': len(json_files),
            'corrupted_files': corrupted_files,
            'integrity_score': (len(json_files) - len(corrupted_files)) / len(json_files) if json_files else 1.0
        }
        
        # Key file consistency check
        key_files = []
        key_counts = {}
        
        for root, dirs, files in os.walk('.'):
            for file in files:
                if 'key' in file.lower() and file.endswith('.json'):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, 'r') as f:
                            data = json.load(f)
                            
                        count = 0
                        if isinstance(data, list):
                            count = len(data)
                        elif isinstance(data, dict):
                            if 'private_keys' in data:
                                count = len(data['private_keys'])
                            elif 'keys' in data:
                                count = len(data['keys'])
                        
                        key_counts[file] = count
                        key_files.append(filepath)
                    except:
                        continue
        
        integrity['key_files'] = {
            'total_files': len(key_files),
            'key_counts': key_counts,
            'total_keys': sum(key_counts.values())
        }
        
        # Result file consistency
        result_files = []
        for root, dirs, files in os.walk('.'):
            for file in files:
                if any(keyword in file.upper() for keyword in ['RESULT', 'REPORT', 'JACKPOT', 'DISCOVERY']):
                    if file.endswith('.json'):
                        result_files.append(os.path.join(root, file))
        
        integrity['result_files'] = len(result_files)
        
        # Backup verification
        backup_locations = ['Archive', 'archive', 'backup', 'Backup']
        backups_exist = any(os.path.exists(loc) for loc in backup_locations)
        
        integrity['backup_status'] = backups_exist
        
        self.audit_results['data_integrity'] = integrity
        
        # Print integrity summary
        print(f"📄 JSON files validated: {len(json_files)}")
        if corrupted_files:
            print(f"❌ Corrupted files: {len(corrupted_files)}")
            for cf in corrupted_files:
                print(f"   └─ {cf}")
        else:
            print("✅ JSON integrity: Perfect")
            
        print(f"🔑 Key files: {len(key_files)} ({sum(key_counts.values())} total keys)")
        print(f"📊 Result files: {len(result_files)}")
        print(f"💾 Backups: {'✅ Present' if backups_exist else '❌ Missing'}")
        
        return integrity
    
    def operational_audit(self):
        """Operational status and capabilities"""
        print("\n🚀 OPERATIONAL AUDIT")
        print("=" * 50)
        
        ops = {}
        
        # API configuration status
        api_status = {}
        if os.path.exists('api_config.json'):
            try:
                with open('api_config.json', 'r') as f:
                    api_data = json.load(f)
                
                for service, config in api_data.items():
                    if isinstance(config, dict) and 'api_key' in config:
                        key = config['api_key']
                        api_status[service] = {
                            'configured': len(key) > 10,
                            'key_length': len(key)
                        }
            except:
                pass
        
        ops['api_configuration'] = api_status
        
        # Core scripts inventory
        core_scripts = [
            'unified_wallet_scanner.py',
            'enhanced_balance_checker.py',
            'comprehensive_wallet_scanner.py',
            'laser_focus_hunter.py',
            'ultimate_jackpot_hunter.py',
            'api_manager.py'
        ]
        
        script_status = {}
        for script in core_scripts:
            exists = os.path.exists(script)
            if exists:
                try:
                    size = os.path.getsize(script)
                    script_status[script] = {
                        'exists': True,
                        'size_kb': size / 1024,
                        'functional': size > 1000  # Basic size check
                    }
                except:
                    script_status[script] = {'exists': True, 'functional': False}
            else:
                script_status[script] = {'exists': False, 'functional': False}
        
        ops['core_scripts'] = script_status
        
        # Dependencies check
        requirements_exist = os.path.exists('requirements.txt')
        venv_exist = os.path.exists('venv')
        
        ops['environment'] = {
            'requirements_file': requirements_exist,
            'virtual_environment': venv_exist,
            'python_ready': requirements_exist and venv_exist
        }
        
        # Recent activity analysis
        recent_files = []
        cutoff_time = time.time() - (24 * 60 * 60)  # 24 hours ago
        
        for root, dirs, files in os.walk('.'):
            for file in files:
                if not file.startswith('.') and 'venv' not in root:
                    filepath = os.path.join(root, file)
                    try:
                        mtime = os.path.getmtime(filepath)
                        if mtime > cutoff_time:
                            recent_files.append({
                                'file': filepath,
                                'modified': datetime.fromtimestamp(mtime).isoformat()
                            })
                    except:
                        continue
        
        ops['recent_activity'] = {
            'files_modified_24h': len(recent_files),
            'last_activity': max([f['modified'] for f in recent_files]) if recent_files else 'None'
        }
        
        # Jackpot tracking
        jackpot_files = []
        total_jackpots = 0
        
        for root, dirs, files in os.walk('.'):
            for file in files:
                if 'JACKPOT' in file.upper() and file.endswith('.json'):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, 'r') as f:
                            data = json.load(f)
                        
                        if isinstance(data, dict):
                            if 'jackpots' in data:
                                total_jackpots += len(data['jackpots'])
                            elif 'private_key' in data:
                                total_jackpots += 1
                        
                        jackpot_files.append(filepath)
                    except:
                        continue
        
        ops['jackpot_status'] = {
            'jackpot_files': len(jackpot_files),
            'total_jackpots': total_jackpots,
            'operational': total_jackpots > 0
        }
        
        self.audit_results['operational_status'] = ops
        
        # Print operational summary
        configured_apis = sum(1 for service, status in api_status.items() if status.get('configured', False))
        print(f"🔗 API services configured: {configured_apis}/{len(api_status)}")
        
        functional_scripts = sum(1 for script, status in script_status.items() if status.get('functional', False))
        print(f"🐍 Core scripts functional: {functional_scripts}/{len(core_scripts)}")
        
        print(f"🔧 Environment ready: {'✅ Yes' if ops['environment']['python_ready'] else '❌ No'}")
        print(f"📈 Recent activity: {len(recent_files)} files modified (24h)")
        print(f"💎 Jackpots discovered: {total_jackpots}")
        
        return ops
    
    def generate_recommendations(self):
        """Generate audit-based recommendations"""
        print("\n💡 RECOMMENDATIONS")
        print("=" * 50)
        
        recommendations = []
        
        # Security recommendations
        security = self.audit_results['security_assessment']
        
        if security.get('api_key_exposure'):
            recommendations.append({
                'category': 'Security',
                'priority': 'HIGH',
                'issue': 'API keys exposed in source code',
                'recommendation': 'Move all API keys to .env file and update .gitignore'
            })
        
        insecure_files = sum(1 for f, data in security.get('file_permissions', {}).items() if not data['secure'])
        if insecure_files:
            recommendations.append({
                'category': 'Security',
                'priority': 'MEDIUM',
                'issue': f'{insecure_files} files have insecure permissions',
                'recommendation': 'Set restrictive permissions (600/644) on sensitive files'
            })
        
        # Performance recommendations
        perf = self.audit_results['performance_metrics']
        
        if perf['logs']['total_size_mb'] > 100:
            recommendations.append({
                'category': 'Performance',
                'priority': 'MEDIUM',
                'issue': f'Log files consuming {perf["logs"]["total_size_mb"]:.2f} MB',
                'recommendation': 'Implement log rotation and cleanup'
            })
        
        if len(perf['filesystem']['large_files']) > 5:
            recommendations.append({
                'category': 'Performance',
                'priority': 'LOW',
                'issue': f'{len(perf["filesystem"]["large_files"])} large files detected',
                'recommendation': 'Archive or compress large data files'
            })
        
        # Data integrity recommendations
        integrity = self.audit_results['data_integrity']
        
        if integrity['json_validation']['corrupted_files']:
            recommendations.append({
                'category': 'Data Integrity',
                'priority': 'HIGH',
                'issue': f'{len(integrity["json_validation"]["corrupted_files"])} corrupted JSON files',
                'recommendation': 'Repair or remove corrupted data files'
            })
        
        if not integrity['backup_status']:
            recommendations.append({
                'category': 'Data Integrity',
                'priority': 'HIGH',
                'issue': 'No backup system detected',
                'recommendation': 'Implement automated backup for critical data'
            })
        
        # Operational recommendations
        ops = self.audit_results['operational_status']
        
        configured_apis = sum(1 for service, status in ops.get('api_configuration', {}).items() if status.get('configured', False))
        total_apis = len(ops.get('api_configuration', {}))
        
        if configured_apis < total_apis:
            recommendations.append({
                'category': 'Operations',
                'priority': 'MEDIUM',
                'issue': f'Only {configured_apis}/{total_apis} API services configured',
                'recommendation': 'Complete API configuration for optimal performance'
            })
        
        if ops['jackpot_status']['total_jackpots'] == 0:
            recommendations.append({
                'category': 'Operations',
                'priority': 'LOW',
                'issue': 'No jackpots discovered yet',
                'recommendation': 'Continue systematic hunting with expanded datasets'
            })
        
        self.audit_results['recommendations'] = recommendations
        
        # Print recommendations
        for i, rec in enumerate(recommendations, 1):
            priority_emoji = "🔴" if rec['priority'] == 'HIGH' else "🟡" if rec['priority'] == 'MEDIUM' else "🟢"
            print(f"{i}. {priority_emoji} [{rec['category']}] {rec['issue']}")
            print(f"   └─ {rec['recommendation']}")
            print()
        
        if not recommendations:
            print("✅ System is operating optimally - no critical recommendations")
        
        return recommendations
    
    def save_audit_report(self):
        """Save complete audit report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"SYSTEM_AUDIT_REPORT_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.audit_results, f, indent=2)
        
        print(f"\n📋 Audit report saved: {filename}")
        return filename
    
    def run_complete_audit(self):
        """Execute complete system audit"""
        print("""
╔══════════════════════════════════════════════════════════════╗
║                    🔍 SYSTEM AUDIT REPORT                     ║
║                   Wallet Recovery System                     ║
╚══════════════════════════════════════════════════════════════╝
        """)
        
        start_time = time.time()
        
        # Run all audit components
        self.security_audit()
        self.performance_audit()
        self.data_integrity_audit()
        self.operational_audit()
        self.generate_recommendations()
        
        # Calculate audit score
        security_score = 100
        if self.audit_results['security_assessment'].get('api_key_exposure'):
            security_score -= 30
        
        perf_score = 100
        if self.audit_results['performance_metrics']['logs']['total_size_mb'] > 100:
            perf_score -= 20
        
        integrity_score = int(self.audit_results['data_integrity']['json_validation']['integrity_score'] * 100)
        
        ops_score = 100
        configured_apis = sum(1 for service, status in self.audit_results['operational_status'].get('api_configuration', {}).items() if status.get('configured', False))
        total_apis = len(self.audit_results['operational_status'].get('api_configuration', {}))
        if total_apis > 0:
            ops_score = int((configured_apis / total_apis) * 100)
        
        overall_score = (security_score + perf_score + integrity_score + ops_score) / 4
        
        self.audit_results['audit_summary'] = {
            'security_score': security_score,
            'performance_score': perf_score,
            'integrity_score': integrity_score,
            'operational_score': ops_score,
            'overall_score': overall_score,
            'audit_duration': time.time() - start_time
        }
        
        # Final summary
        print("\n" + "=" * 70)
        print("🎯 AUDIT SUMMARY")
        print("=" * 70)
        print(f"🔒 Security Score:    {security_score}/100")
        print(f"⚡ Performance Score: {perf_score}/100")
        print(f"🔍 Integrity Score:   {integrity_score}/100")
        print(f"🚀 Operations Score:  {ops_score}/100")
        print(f"📊 OVERALL SCORE:     {overall_score:.1f}/100")
        
        if overall_score >= 90:
            print("🏆 Status: EXCELLENT - System operating at peak performance")
        elif overall_score >= 80:
            print("✅ Status: GOOD - Minor optimizations recommended")
        elif overall_score >= 70:
            print("⚠️  Status: FAIR - Several improvements needed")
        else:
            print("🔴 Status: NEEDS ATTENTION - Critical issues require immediate action")
        
        print(f"⏱️  Audit completed in {time.time() - start_time:.2f} seconds")
        print("=" * 70)
        
        # Save report
        report_file = self.save_audit_report()
        
        return report_file

def main():
    """Run comprehensive system audit"""
    auditor = SystemAuditor()
    report_file = auditor.run_complete_audit()
    
    print(f"\n🎯 Audit complete! Report saved as: {report_file}")

if __name__ == "__main__":
    main()
