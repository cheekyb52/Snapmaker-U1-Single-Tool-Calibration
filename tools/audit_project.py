"""Scan this publishable project offline; report locations without secret values."""
import ipaddress
import json
import os
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_DIRS = {'.local', 'backups', '.venv', 'venv', '__pycache__', 'node_modules'}
FORBIDDEN_SUFFIXES = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp', '.tif', '.tiff',
                      '.mp4', '.mov', '.avi', '.webm', '.log', '.jsonl', '.pem', '.key',
                      '.pyc', '.zip', '.tar', '.gz', '.7z'}
PATTERNS = {
    'personal_windows_path': re.compile(r'[A-Z]:[\\/]+Users[\\/]+[^\\/\s]+', re.I),
    'personal_unix_path': re.compile(r'/(?:Users|home)/(?!lava/)[\w.-]+/'),
    'private_device_alias': re.compile(r'\bCheeky_\d+\b', re.I),
    'private_key': re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----'),
    'github_token': re.compile(r'\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{30,})\b'),
    'cloud_access_key': re.compile(r'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b'),
    'credential_assignment': re.compile(r'\b(?:password|passwd|api_key|api_secret|access_token|'
                                        r'auth_token)\s*[=:]\s*[\x22\x27]'
                                        r'([^\x22\x27\n]{3,})[\x22\x27]', re.I),
}
IPV4 = re.compile(r'(?<![\w.])(?:\d{1,3}\.){3}\d{1,3}(?![\w.])')
EMAIL = re.compile(r'[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}')


def audit(root=ROOT):
    root = root.resolve()
    findings, count, byte_count = [], 0, 0

    def flag(path, rule, line=None):
        item = {'path': path.relative_to(root).as_posix(), 'rule': rule}
        if line is not None:
            item['line'] = line
        findings.append(item)

    for directory, dirs, files in os.walk(root, followlinks=False):
        base = Path(directory)
        for name in list(dirs):
            path = base / name
            if path.is_symlink():
                flag(path, 'symlink')
                dirs.remove(name)
            elif name == '.git':
                dirs.remove(name)  # Local VCS metadata is not a publishable file.
            elif name in FORBIDDEN_DIRS:
                flag(path, 'private_or_generated_directory')
                # Still inspect every file beneath it; ignore rules are not privacy checks.
        for name in sorted(files):
            path = base / name
            count += 1
            if path.is_symlink():
                flag(path, 'symlink')
                continue
            if path.suffix.lower() in FORBIDDEN_SUFFIXES or name.startswith('.env'):
                flag(path, 'private_or_generated_file')
            if re.search(r'(?:^|[-_])(?:before|after|live|monitor|camera|snapshot)(?:[-_.]|$)', name, re.I):
                flag(path, 'raw_device_artifact_name')
            content = path.read_bytes()
            byte_count += len(content)
            try:
                source = content.decode('utf-8')
            except UnicodeDecodeError:
                flag(path, 'unreviewed_binary')
                continue
            for number, line in enumerate(source.splitlines(), 1):
                for rule, pattern in PATTERNS.items():
                    match = pattern.search(line)
                    if match is not None:
                        if rule == 'credential_assignment' and match[1].startswith('<'):
                            continue
                        flag(path, rule, number)
                for match in IPV4.finditer(line):
                    try:
                        address = ipaddress.ip_address(match[0])
                    except ValueError:
                        continue
                    if address.is_private and not address.is_loopback:
                        flag(path, 'private_ip_address', number)
                for match in EMAIL.finditer(line):
                    if match[0] == 'kevin@koconnor.net' and 'Copyright' in line:
                        continue  # Preserved public upstream copyright attribution.
                    flag(path, 'email_requires_review', number)
    return {'scope': 'publishable calibration project only', 'files_scanned': count,
            'bytes_scanned': byte_count, 'findings': findings, 'passed': not findings,
            'limitations': 'Pattern checks plus file-type/scope review; not every secret format is detectable.'}


if __name__ == '__main__':
    report = audit()
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report['passed'] else 1)
