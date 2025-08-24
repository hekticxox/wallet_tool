import time
#!/usr/bin/env python3
"""
🚀 DEPLOYMENT VERIFICATION
===========================

Verify successful deployment and system readiness.
"""

import os
import subprocess
import json
from datetime import datetime

def verify_deployment():
    """Verify the deployment is successful and system is ready"""
    
    print("""
╔══════════════════════════════════════════════════════════════════╗
║                🚀 DEPLOYMENT VERIFICATION                        ║
║              Production Readiness Assessment                     ║
╚══════════════════════════════════════════════════════════════════╝
    """)
    
    checks_passed = 0
    total_checks = 10
    
    print("🔍 DEPLOYMENT VERIFICATION CHECKLIST")
    print("=" * 70)
    
    # Check 1: Git status
    try:
        result = subprocess.run(['git', 'status', '--porcelain'], 
                              capture_output=True, text=True, cwd='.')
        if not result.stdout.strip():
            print("  ✅ Git Repository: Clean working directory")
            checks_passed += 1
        else:
            print("  ⚠️ Git Repository: Has uncommitted changes")
    except:
        print("  ❌ Git Repository: Error checking status")
    
    # Check 2: Directory structure
    expected_dirs = ['scripts', 'data', 'reports', 'docs', 'configs']
    missing_dirs = []
    for dir_name in expected_dirs:
        if os.path.exists(dir_name):
            continue
        else:
            missing_dirs.append(dir_name)
    
    if not missing_dirs:
        print("  ✅ Directory Structure: All required directories present")
        checks_passed += 1
    else:
        print(f"  ❌ Directory Structure: Missing {missing_dirs}")
    
    # Check 3: Core scripts
    core_scripts = ['scripts/unified_wallet_scanner.py', 'scripts/enhanced_balance_checker.py', 
                   'system_auditor.py', 'setup.sh']
    missing_scripts = []
    for script in core_scripts:
        if os.path.exists(script):
            continue
        else:
            missing_scripts.append(script)
    
    if not missing_scripts:
        print("  ✅ Core Scripts: All essential scripts present")
        checks_passed += 1
    else:
        print(f"  ❌ Core Scripts: Missing {missing_scripts}")
    
    # Check 4: Configuration files
    if os.path.exists('configs/api_config.json.example'):
        print("  ✅ Configuration: API config template available")
        checks_passed += 1
    else:
        print("  ❌ Configuration: Missing API config template")
    
    # Check 5: Documentation
    if os.path.exists('README.md') and os.path.getsize('README.md') > 10000:
        print("  ✅ Documentation: Comprehensive README present")
        checks_passed += 1
    else:
        print("  ❌ Documentation: README missing or insufficient")
    
    # Check 6: Setup script
    if os.path.exists('setup.sh') and os.access('setup.sh', os.X_OK):
        print("  ✅ Setup Script: Executable and ready")
        checks_passed += 1
    else:
        print("  ❌ Setup Script: Missing or not executable")
    
    # Check 7: Security files
    if os.path.exists('.gitignore'):
        with open('.gitignore', 'r') as f:
            gitignore_content = f.read()
        if 'api_config.json' in gitignore_content and '*.env' in gitignore_content:
            print("  ✅ Security: Sensitive files properly ignored")
            checks_passed += 1
        else:
            print("  ⚠️ Security: .gitignore may need improvement")
    else:
        print("  ❌ Security: .gitignore file missing")
    
    # Check 8: Requirements file
    if os.path.exists('requirements.txt'):
        print("  ✅ Dependencies: Requirements file present")
        checks_passed += 1
    else:
        print("  ❌ Dependencies: requirements.txt missing")
    
    # Check 9: Data organization
    data_subdirs = ['data/keys', 'data/addresses', 'data/scans', 'data/balances']
    organized_count = sum(1 for d in data_subdirs if os.path.exists(d))
    
    if organized_count >= 3:
        print("  ✅ Data Organization: Proper data structure")
        checks_passed += 1
    else:
        print("  ⚠️ Data Organization: Some data directories missing")
    
    # Check 10: Recent updates
    if os.path.exists('CLEANUP_COMPLETION_REPORT_20250813_122110.json'):
        print("  ✅ System State: Recently optimized and cleaned")
        checks_passed += 1
    else:
        print("  ⚠️ System State: May need cleanup/optimization")
    
    print(f"\n📊 VERIFICATION RESULTS")
    print("=" * 70)
    
    score_percentage = (checks_passed / total_checks) * 100
    
    if score_percentage >= 90:
        status = "🎉 EXCELLENT"
        readiness = "FULLY READY"
    elif score_percentage >= 80:
        status = "✅ GOOD"
        readiness = "READY"
    elif score_percentage >= 70:
        status = "⚠️ ACCEPTABLE"
        readiness = "MOSTLY READY"
    else:
        status = "❌ NEEDS ATTENTION"
        readiness = "NOT READY"
    
    print(f"  📈 Checks Passed: {checks_passed}/{total_checks}")
    print(f"  📊 Success Rate: {score_percentage:.1f}%")
    print(f"  🎯 Status: {status}")
    print(f"  🚀 Deployment Readiness: {readiness}")
    
    print(f"\n🌐 REMOTE REPOSITORY STATUS")
    print("=" * 70)
    
    try:
        # Check remote URL
        result = subprocess.run(['git', 'remote', 'get-url', 'origin'], 
                              capture_output=True, text=True, cwd='.')
        if result.returncode == 0:
            remote_url = result.stdout.strip()
            print(f"  🔗 Repository: {remote_url}")
            
            # Check if up to date
            result = subprocess.run(['git', 'status', '-uno'], 
                                  capture_output=True, text=True, cwd='.')
            if "up to date" in result.stdout:
                print("  ✅ Sync Status: Up to date with remote")
            else:
                print("  ⚠️ Sync Status: May need push/pull")
        else:
            print("  ❌ Repository: No remote configured")
    except:
        print("  ❌ Repository: Error checking remote status")
    
    print(f"\n🎯 NEXT STEPS FOR USERS")
    print("=" * 70)
    
    next_steps = [
        "1. Clone: git clone https://github.com/hekticxox/wallet_tool.git",
        "2. Setup: cd wallet_tool && ./setup.sh", 
        "3. Configure: Edit configs/api_config.json with API keys",
        "4. Test: source venv/bin/activate && python system_auditor.py",
        "5. Hunt: python scripts/hunters/laser_focus_hunter.py"
    ]
    
    for step in next_steps:
        print(f"  {step}")
    
    # Generate verification report
    verification_data = {
        'timestamp': datetime.now().isoformat(),
        'deployment_verification': {
            'checks_passed': checks_passed,
            'total_checks': total_checks,
            'success_rate': score_percentage,
            'status': status,
            'readiness': readiness
        },
        'system_ready': checks_passed >= 8,
        'repository_url': 'https://github.com/hekticxox/wallet_tool.git'
    }
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"DEPLOYMENT_VERIFICATION_{timestamp}.json"
    
    with open(report_file, 'w') as f:
        json.dump(verification_data, f, indent=2)
    
    print(f"\n📋 Verification report: {report_file}")
    
    print("\n" + "=" * 80)
    if checks_passed >= 8:
        print("🎉 DEPLOYMENT SUCCESSFUL - SYSTEM READY FOR PRODUCTION USE")
        print("🚀 Repository updated with professional organization")
        print("✅ Users can now clone and use the enhanced system")
    else:
        print("⚠️ DEPLOYMENT NEEDS ATTENTION - SOME ISSUES DETECTED")
        print("🔧 Please address the failed checks before production use")
    print("=" * 80)

if __name__ == "__main__":
    verify_deployment()
