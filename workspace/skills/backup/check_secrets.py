#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scan Nanobot workspace for real secrets before GitHub upload.
Skips documentation examples and known safe patterns.
"""
import pathlib
import re
import sys

NANOBOT = pathlib.Path.home() / ".nanobot"

SCAN_TARGETS = [
    NANOBOT / "workspace" / "skills",
    NANOBOT / "workspace" / "USER.md",
    NANOBOT / "workspace" / "projects",
    NANOBOT / "cron",
]

# Word-boundary patterns — won't match "tokenize", "secretary", "password_policy_doc"
SECRET_PATTERNS = [
    r"\bapi[_-]?key\b",
    r"\btoken\b",
    r"\bpassword\b",
    r"\bsecret\b",
    r"claw_[a-z]",   # Nanobot MoChat token prefix
    r"\bsk-[A-Za-z0-9]",   # OpenAI/Anthropic key prefix
    r"\bxoxb-",     # Slack bot token
    r"\bxapp-",     # Slack app token
]

# Values containing these substrings are documentation examples, not real secrets
EXAMPLE_INDICATORS = {
    "your_", "your-", "example", "sample", "test", "placeholder",
    "dummy", "fake", "xxx", "replace", "enter", "insert",
    "set_", "<", ">", "{", "}", "...", "***", "none", "null",
    "true", "false", "enabled", "disabled", "here", "key",
    "token", "secret",  # bare words without a real value
}

# Skip these file suffixes entirely — binary or irrelevant
SKIP_SUFFIXES = {".pyc", ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg",
                 ".zip", ".gz", ".tar", ".pdf"}

# Skip the backup skill's own files (they document secret patterns)
SKIP_SKILL_DIR = "backup"


def extract_value(line: str):
    """
    Extract the value after = or : in a line.
    Returns None if no value or value looks like a path/URL.
    """
    # Match: key = "value" or key: value
    m = re.search(r'[:=]\s*[\'"]?([A-Za-z0-9_\-\.+/=]{8,})[\'"]?\s*$', line)
    if not m:
        return None
    val = m.group(1)
    # Reject paths and URLs
    if re.search(r'[/\\]|://', val):
        return None
    # Reject file extensions
    if re.search(r'\.(py|md|txt|json|yml|yaml|sh|ps1|ini|toml|cfg)$', val, re.I):
        return None
    return val


def is_real_secret(value: str) -> bool:
    """Return True only if value looks like an actual secret, not an example."""
    if not value or len(value) < 8:
        return False
    # Only allow base64-safe chars
    if not re.fullmatch(r'[A-Za-z0-9_\-\.+/=]+', value):
        return False
    val_lower = value.lower()
    # Reject if contains any example indicator
    if any(ind in val_lower for ind in EXAMPLE_INDICATORS):
        return False
    # Reject paths and URLs (double-check)
    if re.search(r'[/\\]|://', value):
        return False
    # Must have some entropy — reject all-lowercase short words
    if re.fullmatch(r'[a-z]{4,20}', value):
        return False
    return True


def scan_file(path: pathlib.Path):
    """Return list of findings in a file."""
    findings = []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return findings

    already_found = False
    for pattern in SECRET_PATTERNS:
        if already_found:
            break
        for match in re.finditer(pattern, text, re.I):
            # Extract the full line containing the match
            line_start = text.rfind("\n", 0, match.start()) + 1
            line_end = text.find("\n", match.start())
            if line_end == -1:
                line_end = len(text)
            line = text[line_start:line_end].strip()

            # Skip comment lines
            if line.startswith("#") or line.startswith("//") or line.startswith("*"):
                continue

            value = extract_value(line)
            if value and is_real_secret(value):
                findings.append(f"[{pattern}] {value[:20]}...")
                already_found = True
                break

    return findings


def collect_files():
    """Yield all files to scan."""
    for target in SCAN_TARGETS:
        if not target.exists():
            continue
        if target.is_file():
            yield target
            continue
        for f in target.rglob("*"):
            if not f.is_file():
                continue
            if f.suffix in SKIP_SUFFIXES:
                continue
            # Skip backup skill's own files
            parts = f.parts
            if SKIP_SKILL_DIR in parts:
                skill_idx = parts.index(SKIP_SKILL_DIR) if SKIP_SKILL_DIR in parts else -1
                # Check it's inside skills/backup/
                if skill_idx > 0 and "skills" in parts[skill_idx - 1]:
                    continue
            yield f


def main():
    found = {}
    for f in collect_files():
        findings = scan_file(f)
        if findings:
            found[str(f)] = findings

    if found:
        print("СТОП! Найдены потенциальные секреты:")
        for filepath, items in found.items():
            for item in items:
                print(f"  - {filepath}: {item}")
        sys.exit(1)
    else:
        print("OK: секретов не обнаружено")


if __name__ == "__main__":
    main()
