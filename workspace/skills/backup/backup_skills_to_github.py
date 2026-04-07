#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Backup specified Nanobot workspace files to GitHub via gh CLI.
Requires: gh CLI with configured auth (gh auth login).

BACKUP_SOURCES defines what to copy and where in the repo.
Structure in repo mirrors .nanobot layout.
"""
import os
import pathlib
import subprocess
import json
import base64
import re
import datetime
import sys

# ─── Configuration ────────────────────────────────────────────────────────────

NANOBOT = pathlib.Path.home() / ".nanobot"

# Repository: owner/repo. Override via env var NANOBOT_GITHUB_REPO.
# Agent: read GITHUB_SKILLS_REPO from MEMORY.md and pass as env or arg.
REPO = os.environ.get("NANOBOT_GITHUB_REPO", "")
if not REPO and len(sys.argv) > 1:
    REPO = sys.argv[1]
if not REPO:
    print("ERROR: Repo not specified. Set NANOBOT_GITHUB_REPO or pass owner/repo as argument.")
    sys.exit(1)

# What to back up: list of (local_path, repo_path)
# local_path: absolute path on disk
# repo_path:  path inside the GitHub repository
BACKUP_SOURCES = [
    (NANOBOT / "workspace" / "skills",   "workspace/skills"),
    (NANOBOT / "workspace" / "USER.md",  "workspace/USER.md"),
    (NANOBOT / "workspace" / "projects", "workspace/projects"),
    (NANOBOT / "cron",                   "cron"),
]

README_PATH  = "README.md"
MARKER_START = "<!-- NANOBOT_SKILLS_START -->"
MARKER_END   = "<!-- NANOBOT_SKILLS_END -->"

# ─── gh CLI wrapper ───────────────────────────────────────────────────────────

def run_gh(args, input_data=None):
    """
    Run a gh command. Returns (returncode, stdout, stderr) as strings.
    Always uses UTF-8. Works on Windows with Cyrillic paths.
    """
    env = os.environ.copy()
    # Убираем PYTHONUTF8 на Windows, так как он может вызывать ошибку
    env.pop("PYTHONUTF8", None)
    env["GH_NO_UPDATE_NOTIFIER"] = "1"

    inp = input_data.encode("utf-8") if isinstance(input_data, str) else input_data
    r = subprocess.run(
        ["gh"] + args,
        capture_output=True,
        input=inp,
        env=env,
    )
    stdout = r.stdout.decode("utf-8", errors="replace") if r.stdout else ""
    stderr = r.stderr.decode("utf-8", errors="replace") if r.stderr else ""
    return r.returncode, stdout, stderr

# ─── GitHub API helpers ───────────────────────────────────────────────────────

def get_file_info(repo_path):
    """
    Fetch file info from GitHub.
    Returns (sha, content_bytes) if file exists, (None, None) otherwise.
    Single API call — avoids the double-request SHA race condition.
    """
    code, stdout, stderr = run_gh(["api", f"repos/{REPO}/contents/{repo_path}"])
    if code != 0:
        return None, None
    try:
        data = json.loads(stdout)
        sha = data["sha"]
        # GitHub inserts \n every 60 chars in base64 — strip before decoding
        b64 = data.get("content", "").replace("\n", "")
        content = base64.b64decode(b64) if b64 else b""
        return sha, content
    except Exception:
        return None, None

def upload_file(repo_path, local_bytes, sha=None, message=None):
    """
    Create or update a file in the repository.
    sha must be provided when updating an existing file (else HTTP 422).
    Returns True on success.
    """
    if message is None:
        message = f"backup: update {repo_path}"
    body = {
        "message": message,
        "content": base64.b64encode(local_bytes).decode("ascii"),
    }
    if sha:
        body["sha"] = sha

    code, stdout, stderr = run_gh(
        ["api", f"repos/{REPO}/contents/{repo_path}",
         "--method", "PUT", "--input", "-"],
        input_data=json.dumps(body),
    )
    if code != 0:
        print(f"  ERROR uploading {repo_path}: {stderr.strip()}")
        return False
    return True

# ─── Secrets check ────────────────────────────────────────────────────────────

def check_secrets():
    """Run check_secrets.py. Returns True if safe to proceed."""
    script = pathlib.Path(__file__).parent / "check_secrets.py"
    if not script.exists():
        print("WARNING: check_secrets.py not found, skipping secrets check.")
        return True
    env = os.environ.copy()
    env.pop("PYTHONUTF8", None)
    r = subprocess.run([sys.executable, str(script)], capture_output=True, env=env)
    output = r.stdout.decode("utf-8", errors="replace")
    # Безопасный вывод для Windows консоли
    try:
        print(output.strip())
    except UnicodeEncodeError:
        print(output.strip().encode("ascii", errors="ignore").decode())
    if r.returncode != 0 or "СТОП!" in output:
        return False
    return True

# ─── Secrets sanitization ─────────────────────────────────────────────────────

# Паттерны для поиска секретов (совпадают с check_secrets.py)
SECRET_PATTERNS = [
    r"\bapi[_-]?key\b",
    r"\btoken\b",
    r"\bpassword\b",
    r"\bsecret\b",
    r"claw_[a-z]",
    r"\bsk-[A-Za-z0-9]",
    r"\bxoxb-",
    r"\bxapp-",
]

EXAMPLE_INDICATORS = {
    "your_", "your-", "example", "sample", "test", "placeholder",
    "dummy", "fake", "xxx", "replace", "enter", "insert",
    "set_", "<", ">", "{", "}", "...", "***", "none", "null",
    "true", "false", "enabled", "disabled", "here", "key",
    "token", "secret",
}

def extract_value(line: str):
    """Extract the value after = or : in a line."""
    m = re.search(r'[:=]\s*[\'"]?([A-Za-z0-9_\-\.+/=]{8,})[\'"]?\s*$', line)
    if not m:
        return None
    val = m.group(1)
    if re.search(r'[/\\]|://', val):
        return None
    if re.search(r'\.(py|md|txt|json|yml|yaml|sh|ps1|ini|toml|cfg)$', val, re.I):
        return None
    return val

def is_real_secret(value: str) -> bool:
    """Return True only if value looks like an actual secret."""
    if not value or len(value) < 8:
        return False
    if not re.fullmatch(r'[A-Za-z0-9_\-\.+/=]+', value):
        return False
    val_lower = value.lower()
    if any(ind in val_lower for ind in EXAMPLE_INDICATORS):
        return False
    if re.search(r'[/\\]|://', value):
        return False
    if re.fullmatch(r'[a-z]{4,20}', value):
        return False
    return True

def sanitize_content(content: str) -> tuple[str, list[str]]:
    """
    Replace real secrets in content with '***'.
    Returns (sanitized_content, list_of_replaced_patterns).
    """
    replaced = []
    lines = content.split('\n')
    sanitized_lines = []
    
    for line in lines:
        sanitized_line = line
        # Skip comment lines
        if line.strip().startswith('#') or line.strip().startswith('//') or line.strip().startswith('*'):
            sanitized_lines.append(sanitized_line)
            continue
            
        for pattern in SECRET_PATTERNS:
            for match in re.finditer(pattern, line, re.I):
                # Find the line containing this match
                value = extract_value(line)
                if value and is_real_secret(value):
                    # Replace the value with ***
                    sanitized_line = sanitized_line.replace(value, '***')
                    if pattern not in replaced:
                        replaced.append(pattern)
        
        sanitized_lines.append(sanitized_line)
    
    return '\n'.join(sanitized_lines), replaced

# ─── File upload logic ────────────────────────────────────────────────────────

def upload_source(local_path, repo_prefix):
    """
    Upload a single file or all files in a directory to the repo.
    Skips files whose content hasn't changed.
    Sanitizes secrets before upload (replaces with ***).
    Returns (changed_count, skipped_count, sanitized_count).
    """
    changed = 0
    skipped = 0
    sanitized = 0

    if local_path.is_file():
        local_bytes = local_path.read_bytes()
        sha, remote_bytes = get_file_info(repo_prefix)
        if remote_bytes is not None and remote_bytes == local_bytes:
            print(f"  unchanged: {repo_prefix}")
            return 0, 1, 0
        
        # Sanitize secrets before upload
        content = local_bytes.decode('utf-8', errors='replace')
        sanitized_content, replaced_patterns = sanitize_content(content)
        
        if replaced_patterns:
            print(f"  ⚠️  sanitized: {repo_prefix} (replaced: {', '.join(replaced_patterns)})")
            sanitized += 1
            upload_bytes = sanitized_content.encode('utf-8')
        else:
            upload_bytes = local_bytes
        
        ok = upload_file(repo_prefix, upload_bytes, sha=sha)
        if ok:
            print(f"  uploaded:  {repo_prefix}")
            return 1, 0, sanitized
        return 0, 0, 0

    if local_path.is_dir():
        for f in sorted(local_path.rglob("*")):
            if not f.is_file():
                continue
            rel = f.relative_to(local_path)
            repo_path = repo_prefix + "/" + str(rel).replace("\\", "/")
            local_bytes = f.read_bytes()
            sha, remote_bytes = get_file_info(repo_path)
            if remote_bytes is not None and remote_bytes == local_bytes:
                skipped += 1
                continue
            
            # Sanitize secrets before upload
            content = local_bytes.decode('utf-8', errors='replace')
            sanitized_content, replaced_patterns = sanitize_content(content)
            
            if replaced_patterns:
                print(f"  [SANITIZED] {repo_path} (replaced: {', '.join(replaced_patterns)})")
                sanitized += 1
                upload_bytes = sanitized_content.encode('utf-8')
            else:
                upload_bytes = local_bytes
            
            ok = upload_file(repo_path, upload_bytes, sha=sha)
            if ok:
                print(f"  uploaded:  {repo_path}")
                changed += 1
        return changed, skipped, sanitized

    print(f"  SKIP (not found): {local_path}")
    return 0, 0, 0

# ─── README update ────────────────────────────────────────────────────────────

def update_readme():
    """
    Update only the skills table between MARKER_START and MARKER_END in README.md.
    All other content is preserved.
    """
    skills_dir = NANOBOT / "workspace" / "skills"
    if not skills_dir.exists():
        print("  skills dir not found, skipping README update")
        return

    def skill_info(d):
        md = d / "SKILL.md"
        desc = "—"
        if md.exists():
            txt = md.read_text(encoding="utf-8", errors="ignore")
            m = re.search(r"^description:\s*(.+)$", txt, re.M)
            if m:
                desc = m.group(1).strip().split(".")[0]
        return d.name, desc

    skills = [skill_info(d) for d in sorted(skills_dir.iterdir()) if d.is_dir()]
    now = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")
    rows = ["| Skill | Description |", "|-------|-------------|"]
    rows += [f"| `{n}` | {d} |" for n, d in skills]
    table = f"<!-- Updated: {now} -->\n" + "\n".join(rows)
    block = f"{MARKER_START}\n{table}\n{MARKER_END}"

    # Fetch current README (single call: get SHA + content together)
    sha, remote_bytes = get_file_info(README_PATH)
    if remote_bytes is not None:
        content = remote_bytes.decode("utf-8", errors="replace")
    else:
        content = f"# Nanobot Skills\n\n{MARKER_START}\n{MARKER_END}\n\n## Install\nCopy skill folder to ~/.nanobot/workspace/skills/\n"
        print("  README.md not found — will create from template")

    # Replace only the block between markers
    if MARKER_START in content and MARKER_END in content:
        before = content[: content.index(MARKER_START)]
        after = content[content.index(MARKER_END) + len(MARKER_END) :]
        new_content = before + block + after
    else:
        new_content = content.rstrip() + "\n\n" + block + "\n"
        print("  Markers not found — table appended to end")

    if new_content == content:
        print(f"  README.md unchanged ({len(skills)} skills)")
        return

    ok = upload_file(
        README_PATH,
        new_content.encode("utf-8"),
        sha=sha,
        message=f"docs: update skills table ({len(skills)} skills)",
    )
    if ok:
        print(f"  README.md updated: {len(skills)} skills")

# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    print(f"=== Nanobot GitHub Backup -> {REPO} ===\n")

    # 1. Check gh auth
    code, stdout, stderr = run_gh(["auth", "status"])
    if code != 0:
        print("ERROR: gh not authorized. Run: gh auth login")
        sys.exit(1)
    print("gh: authorized OK\n")

    # 2. Upload sources (secrets are sanitized automatically)
    total_changed = 0
    total_skipped = 0
    total_sanitized = 0
    for local_path, repo_path in BACKUP_SOURCES:
        print(f"Uploading: {local_path.name} -> {repo_path}")
        c, s, san = upload_source(local_path, repo_path)
        total_changed += c
        total_skipped += s
        total_sanitized += san
    print(f"\nFiles: {total_changed} updated, {total_skipped} unchanged, {total_sanitized} sanitized\n")

    # 3. Update README
    print("Updating README.md...")
    update_readme()

    print("\n=== Backup complete ===")

if __name__ == "__main__":
    main()
