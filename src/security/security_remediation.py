#!/usr/bin/env python3
"""
SECURITY REMEDIATION TOOL
Fixes critical security issues identified in the audit
"""

import os
import shutil
import json
from pathlib import Path
from datetime import datetime

class SecurityRemediator:
    def __init__(self):
        self.workspace_path = "/home/admin/wallet_tool"
        self.backup_dir = f"{self.workspace_path}/security_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.remediation_log = []
        
    def create_backup(self):
        """Create backup of sensitive files before remediation"""
        print("🔄 CREATING SECURITY BACKUP")
        print("-" * 50)
        
        os.makedirs(self.backup_dir, exist_ok=True)
        
        # Backup all JSON files and sensitive data
        for file_path in Path(self.workspace_path).glob("*.json"):
            if file_path.is_file():
                backup_path = Path(self.backup_dir) / file_path.name
                shutil.copy2(file_path, backup_path)
                self.remediation_log.append(f"Backed up: {file_path.name}")
        
        # Backup .env if it exists
        env_file = Path(self.workspace_path) / ".env"
        if env_file.exists():
            shutil.copy2(env_file, Path(self.backup_dir) / ".env")
            self.remediation_log.append("Backed up: .env")
        
        print(f"✅ Backup created at: {self.backup_dir}")
        print(f"   Files backed up: {len(self.remediation_log)}")
        
    def fix_file_permissions(self):
        """Fix file permissions for sensitive files"""
        print("\n🔒 FIXING FILE PERMISSIONS")
        print("-" * 50)
        
        sensitive_patterns = ["*.json", "*.env", "*key*", "*wallet*", "*private*"]
        fixed_files = []
        
        for pattern in sensitive_patterns:
            for file_path in Path(self.workspace_path).glob(pattern):
                if file_path.is_file():
                    try:
                        # Set to read/write owner only (600)
                        os.chmod(file_path, 0o600)
                        fixed_files.append(str(file_path.name))
                        self.remediation_log.append(f"Fixed permissions: {file_path.name}")
                    except Exception as e:
                        self.remediation_log.append(f"ERROR fixing {file_path.name}: {e}")
        
        print(f"✅ Fixed permissions for {len(fixed_files)} files")
        
        return fixed_files
    
    def secure_sensitive_data(self):
        """Remove or mask sensitive data in files"""
        print("\n🛡️ SECURING SENSITIVE DATA")
        print("-" * 50)
        
        # Files that may contain sensitive data
        sensitive_files = [
            "extracted_private_keys.json",
            "comprehensive_recheck_results_*.json",
            "PRIORITY_RICHEST_KEYS.json"
        ]
        
        secured_files = []
        
        for pattern in sensitive_files:
            files = list(Path(self.workspace_path).glob(pattern))
            for file_path in files:
                if file_path.exists():
                    try:
                        with open(file_path, 'r') as f:
                            data = json.load(f)
                        
                        # Mask private keys (keep first 8 and last 4 chars)
                        def mask_private_key(key):
                            if isinstance(key, str) and len(key) > 12:
                                return f"{key[:8]}...{key[-4:]}"
                            return key
                        
                        # Recursively mask sensitive data
                        def mask_sensitive_data(obj):
                            if isinstance(obj, dict):
                                masked = {}
                                for k, v in obj.items():
                                    if any(sensitive in k.lower() for sensitive in ['private', 'key', 'secret']):
                                        masked[k] = mask_private_key(v)
                                    else:
                                        masked[k] = mask_sensitive_data(v)
                                return masked
                            elif isinstance(obj, list):
                                return [mask_sensitive_data(item) for item in obj]
                            else:
                                return obj
                        
                        # Create masked version
                        masked_data = mask_sensitive_data(data)
                        
                        # Save masked version
                        masked_filename = f"{file_path.stem}_masked{file_path.suffix}"
                        with open(file_path.parent / masked_filename, 'w') as f:
                            json.dump(masked_data, f, indent=2)
                        
                        secured_files.append(masked_filename)
                        self.remediation_log.append(f"Created masked version: {masked_filename}")
                        
                    except Exception as e:
                        self.remediation_log.append(f"ERROR masking {file_path.name}: {e}")
        
        print(f"✅ Created {len(secured_files)} masked files")
        
        return secured_files
    
    def create_security_config(self):
        """Create security configuration files"""
        print("\n⚙️ CREATING SECURITY CONFIGURATION")
        print("-" * 50)
        
        # Create .gitignore for sensitive files
        gitignore_content = """
# Sensitive wallet recovery data
*.env
*private*
*key*
*wallet*
*.json
*backup*
*audit*
*recovery*

# Exception for documentation
!README.md
!*.md
!requirements.txt
!*.example

# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
venv/
"""
        
        with open(f"{self.workspace_path}/.gitignore", 'w') as f:
            f.write(gitignore_content.strip())
        
        self.remediation_log.append("Created .gitignore")
        
        # Create security policy
        security_policy = """# Security Policy

## Data Handling
- All sensitive files must have 600 permissions
- Private keys must be encrypted or masked
- Use environment variables for API keys
- Regular security audits required

## Access Control
- Limit access to wallet recovery tools
- Use multi-factor authentication
- Regular access reviews

## Incident Response
- Immediate isolation if breach suspected
- Change all API keys if compromised
- Document all security incidents

## Contact
For security issues, contact: security@example.com
"""
        
        with open(f"{self.workspace_path}/SECURITY.md", 'w') as f:
            f.write(security_policy)
        
        self.remediation_log.append("Created SECURITY.md")
        
        print("✅ Security configuration created")
    
    def generate_remediation_report(self):
        """Generate remediation report"""
        print("\n📊 GENERATING REMEDIATION REPORT")
        print("-" * 50)
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "backup_location": self.backup_dir,
            "actions_taken": len(self.remediation_log),
            "remediation_log": self.remediation_log,
            "security_improvements": [
                "Fixed file permissions (600 for sensitive files)",
                "Created masked versions of sensitive data",
                "Implemented .gitignore for sensitive files",
                "Created security policy documentation",
                "Created backup of original files"
            ],
            "remaining_risks": [
                "Original sensitive data still present",
                "Manual code review still required",
                "Professional security assessment recommended"
            ],
            "next_steps": [
                "Review and test masked data files",
                "Implement additional encryption",
                "Set up monitoring and logging",
                "Schedule regular security audits"
            ]
        }
        
        report_filename = f"SECURITY_REMEDIATION_REPORT_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(report_filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Set secure permissions on report
        os.chmod(report_filename, 0o600)
        
        print(f"✅ Remediation report saved: {report_filename}")
        print(f"   Total actions taken: {len(self.remediation_log)}")
        
        return report
    
    def run_remediation(self):
        """Run complete security remediation"""
        print("🛠️ SECURITY REMEDIATION PROCESS")
        print("=" * 70)
        
        self.create_backup()
        fixed_files = self.fix_file_permissions()
        secured_files = self.secure_sensitive_data()
        self.create_security_config()
        report = self.generate_remediation_report()
        
        print("\n" + "=" * 70)
        print("🎯 REMEDIATION SUMMARY")
        print("=" * 70)
        print(f"✅ Files with fixed permissions: {len(fixed_files)}")
        print(f"✅ Secured sensitive files: {len(secured_files)}")
        print(f"✅ Security configs created: 2")
        print(f"✅ Backup location: {self.backup_dir}")
        print("\n🔒 SECURITY POSTURE IMPROVED")
        print("=" * 70)
        
        return report

def main():
    remediator = SecurityRemediator()
    results = remediator.run_remediation()
    return results

if __name__ == "__main__":
    main()
