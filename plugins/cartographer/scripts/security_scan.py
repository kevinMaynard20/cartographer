#!/usr/bin/env python3
"""
Security Scan module for Cartographer.
Detects potential security concerns like hardcoded secrets, API keys, and credentials.
"""

import re
from pathlib import Path
from typing import List, Tuple
from dataclasses import dataclass


@dataclass
class SecurityFinding:
    """Represents a security finding."""
    severity: str  # 'critical', 'warning', 'info'
    category: str
    file: Path
    line: int
    description: str
    snippet: str


# Patterns for detecting secrets
SECRET_PATTERNS = [
    # API Keys
    (r'(?i)(api[_-]?key|apikey)\s*[=:]\s*["\']([a-zA-Z0-9_\-]{20,})["\']', 'critical', 'API Key'),
    (r'(?i)(secret[_-]?key|secretkey)\s*[=:]\s*["\']([a-zA-Z0-9_\-]{20,})["\']', 'critical', 'Secret Key'),

    # AWS
    (r'AKIA[0-9A-Z]{16}', 'critical', 'AWS Access Key'),
    (r'(?i)aws[_-]?secret[_-]?access[_-]?key\s*[=:]\s*["\']([^\'"]+)["\']', 'critical', 'AWS Secret Key'),

    # Passwords
    (r'(?i)(password|passwd|pwd)\s*[=:]\s*["\']([^\'"\s]{4,})["\']', 'warning', 'Hardcoded Password'),

    # Private keys
    (r'-----BEGIN (RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----', 'critical', 'Private Key'),
    (r'-----BEGIN PGP PRIVATE KEY BLOCK-----', 'critical', 'PGP Private Key'),

    # Tokens
    (r'(?i)(auth[_-]?token|access[_-]?token)\s*[=:]\s*["\']([a-zA-Z0-9_\-\.]{20,})["\']', 'critical', 'Auth Token'),
    (r'(?i)bearer\s+[a-zA-Z0-9_\-\.]{20,}', 'warning', 'Bearer Token'),
    (r'ghp_[a-zA-Z0-9]{36}', 'critical', 'GitHub Personal Access Token'),
    (r'gho_[a-zA-Z0-9]{36}', 'critical', 'GitHub OAuth Token'),
    (r'github_pat_[a-zA-Z0-9_]{22,}', 'critical', 'GitHub PAT'),

    # Database
    (r'(?i)mongodb(\+srv)?://[^\s\'"]+:[^\s\'"]+@', 'critical', 'MongoDB Connection String'),
    (r'(?i)postgres://[^\s\'"]+:[^\s\'"]+@', 'critical', 'PostgreSQL Connection String'),
    (r'(?i)mysql://[^\s\'"]+:[^\s\'"]+@', 'critical', 'MySQL Connection String'),

    # Other services
    (r'sk-[a-zA-Z0-9]{48}', 'critical', 'OpenAI API Key'),
    (r'xox[baprs]-[a-zA-Z0-9\-]{10,}', 'critical', 'Slack Token'),
    (r'(?i)stripe[_-]?(secret|api)[_-]?key\s*[=:]\s*["\']sk_[^\'"]+["\']', 'critical', 'Stripe Secret Key'),

    # Generic secrets
    (r'(?i)client[_-]?secret\s*[=:]\s*["\']([a-zA-Z0-9_\-]{20,})["\']', 'warning', 'Client Secret'),
    (r'(?i)encryption[_-]?key\s*[=:]\s*["\']([a-zA-Z0-9_\-/+=]{16,})["\']', 'warning', 'Encryption Key'),
]

# Patterns for insecure configurations
INSECURE_PATTERNS = [
    (r'(?i)debug\s*[=:]\s*["\']?true', 'warning', 'Debug Mode Enabled'),
    (r'(?i)verify\s*[=:]\s*["\']?false', 'warning', 'SSL Verification Disabled'),
    (r'(?i)insecure\s*[=:]\s*["\']?true', 'warning', 'Insecure Mode'),
    (r'(?i)allow_all_origins|allowallorigins', 'info', 'CORS Allow All'),
    (r'0\.0\.0\.0', 'info', 'Binding to All Interfaces'),
    (r'(?i)password\s*[=:]\s*["\']["\']', 'info', 'Empty Password'),
]

# Files to skip
SKIP_FILES = {
    '.env.example', '.env.sample', '.env.template',
    'package-lock.json', 'yarn.lock', 'Cargo.lock',
}


def should_scan_file(path: Path) -> bool:
    """Check if a file should be scanned."""
    if path.name in SKIP_FILES:
        return False

    # Skip binary files by extension
    binary_exts = {'.png', '.jpg', '.jpeg', '.gif', '.ico', '.woff', '.woff2', '.ttf', '.eot', '.pdf', '.zip', '.tar', '.gz'}
    if path.suffix.lower() in binary_exts:
        return False

    # Skip lock files
    if path.name.endswith('.lock'):
        return False

    return True


def scan_file(file_path: Path) -> List[SecurityFinding]:
    """Scan a single file for security issues."""
    if not should_scan_file(file_path):
        return []

    findings = []

    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
    except Exception:
        return []

    for line_num, line in enumerate(lines, 1):
        # Skip comments (basic detection)
        stripped = line.strip()
        if stripped.startswith('#') or stripped.startswith('//') or stripped.startswith('*'):
            continue

        # Check secret patterns
        for pattern, severity, category in SECRET_PATTERNS:
            if re.search(pattern, line):
                # Redact the actual secret in the snippet
                snippet = line.strip()[:100]
                if len(line.strip()) > 100:
                    snippet += "..."

                findings.append(SecurityFinding(
                    severity=severity,
                    category=category,
                    file=file_path,
                    line=line_num,
                    description=f"Potential {category} detected",
                    snippet=snippet
                ))
                break  # One finding per line

        # Check insecure patterns
        for pattern, severity, category in INSECURE_PATTERNS:
            if re.search(pattern, line):
                snippet = line.strip()[:100]
                findings.append(SecurityFinding(
                    severity=severity,
                    category=category,
                    file=file_path,
                    line=line_num,
                    description=f"{category}",
                    snippet=snippet
                ))

    return findings


def scan_codebase_security(files: List[Path]) -> List[SecurityFinding]:
    """Scan all files for security issues."""
    all_findings = []
    for file_path in files:
        findings = scan_file(file_path)
        all_findings.extend(findings)
    return all_findings


def generate_security_report(findings: List[SecurityFinding], root: Path) -> str:
    """Generate markdown report for security findings."""
    # Count by severity
    critical = [f for f in findings if f.severity == 'critical']
    warnings = [f for f in findings if f.severity == 'warning']
    info = [f for f in findings if f.severity == 'info']

    lines = [
        "# Security Scan Results",
        "",
        "## Summary",
        "",
        f"- **Critical**: {len(critical)}",
        f"- **Warning**: {len(warnings)}",
        f"- **Info**: {len(info)}",
        "",
    ]

    if not findings:
        lines.append("No security issues detected.")
        lines.append("")
        return '\n'.join(lines)

    # Critical findings
    if critical:
        lines.append("## Critical Findings")
        lines.append("")
        lines.append("These findings require immediate attention:")
        lines.append("")
        for f in critical:
            rel_path = f.file.relative_to(root) if f.file.is_relative_to(root) else f.file
            lines.append(f"### {f.category}")
            lines.append(f"- **File**: `{rel_path}:{f.line}`")
            lines.append(f"- **Description**: {f.description}")
            lines.append(f"- **Snippet**: `{f.snippet[:80]}...`" if len(f.snippet) > 80 else f"- **Snippet**: `{f.snippet}`")
            lines.append("")

    # Warnings
    if warnings:
        lines.append("## Warnings")
        lines.append("")
        for f in warnings:
            rel_path = f.file.relative_to(root) if f.file.is_relative_to(root) else f.file
            lines.append(f"- **{f.category}** at `{rel_path}:{f.line}`")
            lines.append(f"  - {f.description}")
        lines.append("")

    # Info
    if info:
        lines.append("## Informational")
        lines.append("")
        for f in info:
            rel_path = f.file.relative_to(root) if f.file.is_relative_to(root) else f.file
            lines.append(f"- **{f.category}** at `{rel_path}:{f.line}`")
        lines.append("")

    # Recommendations
    lines.extend([
        "## Recommendations",
        "",
        "1. **Never commit secrets to version control** - Use environment variables or secret management services",
        "2. **Use .gitignore** - Add `.env` files to `.gitignore`",
        "3. **Rotate exposed secrets** - If any secrets were committed, rotate them immediately",
        "4. **Use secret scanning** - Enable GitHub secret scanning or similar tools",
        "5. **Review debug settings** - Ensure debug mode is disabled in production",
        "",
    ])

    return '\n'.join(lines)


if __name__ == "__main__":
    import sys
    from scanner import scan_codebase

    path = sys.argv[1] if len(sys.argv) > 1 else "."
    root = Path(path).resolve()
    scan_results = scan_codebase(path)

    files = [r[0] for r in scan_results]
    findings = scan_codebase_security(files)

    print(generate_security_report(findings, root))
