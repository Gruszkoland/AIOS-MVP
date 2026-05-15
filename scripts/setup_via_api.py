#!/usr/bin/env python3
"""
Setup Dependabot and Codespaces using GitHub REST API.
Faster approach without full repo clones.
"""

import subprocess
import sys
import json
import time
import base64
from pathlib import Path

REPOS = [
    "adrion-369",
    "adrion-architecture",
    "adrion-deploy",
    "consultacao-ai",
    "embedding-ab-test",
    "leadgen-comet",
    "punkt-odniesienia",
    "n8n-workflows-prod",
    "kyc-provider-guide"
]

ORG = "Gruszkoland"
SCRIPT_DIR = Path(__file__).parent.parent
DEPENDABOT_TEMPLATE = SCRIPT_DIR / "templates" / "dependabot-template.yml"
DEVCONTAINER_TEMPLATE = SCRIPT_DIR / "templates" / "devcontainer-template.json"

def read_file(path):
    """Read file content."""
    if not path.exists():
        print(f"ERROR: File not found: {path}")
        return None
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def gh_api_call(endpoint, data=None, method="POST"):
    """Call GitHub API using gh CLI."""
    cmd = ["gh", "api", endpoint]
    if method != "POST":
        cmd.append(f"-X {method}")
    if data:
        cmd.extend(["-f", json.dumps(data)])
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            return True, json.loads(result.stdout) if result.stdout else {}
        else:
            return False, result.stderr
    except Exception as e:
        return False, str(e)

def get_repo_default_branch(repo):
    """Get repository's default branch."""
    cmd = ["gh", "repo", "view", f"{ORG}/{repo}", "--json", "defaultBranchRef", "-q", ".defaultBranchRef.name"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            return result.stdout.strip() or "main"
    except:
        pass
    return "main"

def create_file_via_api(repo, file_path, content, message):
    """Create/update file in repo via GitHub API."""
    branch = get_repo_default_branch(repo)
    
    # Get existing file SHA if it exists
    sha = None
    cmd_get = ["gh", "api", f"repos/{ORG}/{repo}/contents/{file_path}", "-q", ".sha"]
    try:
        result = subprocess.run(cmd_get, capture_output=True, text=True, timeout=10)
        if result.returncode == 0 and result.stdout.strip():
            sha = result.stdout.strip()
    except:
        pass
    
    # Prepare payload
    content_b64 = base64.b64encode(content.encode('utf-8')).decode('utf-8')
    payload = {
        "message": message,
        "content": content_b64,
        "branch": branch
    }
    
    if sha:
        payload["sha"] = sha
    
    # Create/update file
    endpoint = f"repos/{ORG}/{repo}/contents/{file_path}"
    cmd = ["gh", "api", endpoint, "-X", "PUT", "-F", json.dumps(payload)]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return result.returncode == 0, result.stderr if result.returncode != 0 else "OK"
    except Exception as e:
        return False, str(e)

def setup_repo(repo):
    """Setup Dependabot and Codespaces for a repo."""
    print(f"\n📌 {repo}")
    
    # Read templates
    dependabot_content = read_file(DEPENDABOT_TEMPLATE)
    devcontainer_content = read_file(DEVCONTAINER_TEMPLATE)
    
    if not dependabot_content or not devcontainer_content:
        print(f"   ❌ Template read failed")
        return False
    
    # Setup Dependabot
    print(f"   ⚙️  Dependabot...", end=" ", flush=True)
    success, msg = create_file_via_api(
        repo,
        ".github/dependabot.yml",
        dependabot_content,
        "⚙️  chore: setup Dependabot"
    )
    print("✅" if success else f"⚠️  ({msg[:30]})")
    
    time.sleep(1)
    
    # Setup Codespaces
    print(f"   🚀 Codespaces...", end=" ", flush=True)
    success, msg = create_file_via_api(
        repo,
        ".devcontainer/devcontainer.json",
        devcontainer_content,
        "⚙️  chore: setup Codespaces"
    )
    print("✅" if success else f"⚠️  ({msg[:30]})")
    
    time.sleep(1)
    return True

def main():
    """Main entry point."""
    print("=" * 60)
    print("🔧 ADRION Dependabot + Codespaces Setup (via API)")
    print("=" * 60)
    
    for repo in REPOS:
        try:
            setup_repo(repo)
        except Exception as e:
            print(f"   ❌ {e}")
    
    print("\n" + "=" * 60)
    print(f"✅ Setup initiated for {len(REPOS)} repos")
    print("=" * 60)
    return 0

if __name__ == "__main__":
    sys.exit(main())
