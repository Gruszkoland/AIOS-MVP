#!/usr/bin/env python3
"""
Setup Dependabot and Codespaces for all 9 ADRION repos.
This script creates .github/dependabot.yml and .devcontainer/devcontainer.json
"""

import subprocess
import sys
import os
import json
import base64
import time
from pathlib import Path

# 9 ADRION repositories
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

# GitHub API base
GITHUB_API = "https://api.github.com"
ORG = "Gruszkoland"

# Template paths
SCRIPT_DIR = Path(__file__).parent.parent
DEPENDABOT_TEMPLATE = SCRIPT_DIR / "templates" / "dependabot-template.yml"
DEVCONTAINER_TEMPLATE = SCRIPT_DIR / "templates" / "devcontainer-template.json"

def run_command(cmd, timeout=30):
    """Execute shell command and return result."""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        return False, "", f"Command timed out after {timeout}s"
    except Exception as e:
        return False, "", str(e)

def read_template(template_path):
    """Read template file content."""
    if not template_path.exists():
        print(f"❌ Template not found: {template_path}")
        return None
    with open(template_path, 'r', encoding='utf-8') as f:
        return f.read()

def create_file_via_api(repo, file_path, content, message):
    """Create/update file in GitHub repo via REST API."""
    # Get the branch (usually main)
    get_branch_cmd = f'gh repo view {ORG}/{repo} --json defaultBranchRef --jq ".defaultBranchRef.name"'
    success, branch, _ = run_command(get_branch_cmd)
    
    if not success or not branch:
        branch = "main"
    
    # Encode content to base64
    content_b64 = base64.b64encode(content.encode('utf-8')).decode('utf-8')
    
    # Check if file exists and get SHA
    get_sha_cmd = f'gh api repos/{ORG}/{repo}/contents/{file_path} --jq ".sha" 2>/dev/null || echo ""'
    _, sha, _ = run_command(get_sha_cmd)
    
    # Create JSON payload
    payload = {
        "message": message,
        "content": content_b64,
        "branch": branch
    }
    
    if sha and sha.strip():
        payload["sha"] = sha.strip()
    
    # Use gh to create/update file
    # Since gh doesn't directly support file creation, we'll use git-based approach
    return create_file_via_git(repo, file_path, content, message)

def create_file_via_git(repo, file_path, content, message):
    """Create/update file using git clone, commit, push."""
    import tempfile
    import shutil
    
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_url = f"https://github.com/{ORG}/{repo}.git"
        repo_path = Path(tmpdir) / repo
        
        # Clone repo
        clone_cmd = f'cd {tmpdir} && git clone {repo_url}'
        success, _, err = run_command(clone_cmd, timeout=60)
        if not success:
            return False, f"Clone failed: {err}"
        
        # Create directory structure
        file_full_path = repo_path / file_path
        file_full_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write content
        with open(file_full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Configure git
        os.chdir(repo_path)
        run_command('git config user.name "Dependabot Setup Bot"')
        run_command('git config user.email "bot@gruszkoland.local"')
        
        # Check if changes exist
        status_cmd = 'git status --short'
        success, status, _ = run_command(status_cmd)
        
        if not status:
            return True, "No changes needed"
        
        # Add, commit, push
        run_command('git add .')
        commit_cmd = f'git commit -m "{message}"'
        success, _, err = run_command(commit_cmd)
        
        if not success and "nothing to commit" not in err:
            return False, f"Commit failed: {err}"
        
        push_cmd = 'git push'
        success, _, err = run_command(push_cmd, timeout=60)
        
        if not success:
            return False, f"Push failed: {err}"
        
        return True, "Success"

def setup_repo(repo):
    """Setup Dependabot and Codespaces for a single repo."""
    print(f"\n📌 Setting up {repo}...")
    
    # Read templates
    dependabot_content = read_template(DEPENDABOT_TEMPLATE)
    devcontainer_content = read_template(DEVCONTAINER_TEMPLATE)
    
    if not dependabot_content or not devcontainer_content:
        print(f"   ❌ Template read failed")
        return False
    
    # Setup Dependabot
    print(f"   🔧 Adding Dependabot config...")
    success, msg = create_file_via_git(
        repo,
        ".github/dependabot.yml",
        dependabot_content,
        "⚙️ chore: setup Dependabot for dependency updates"
    )
    
    if success:
        print(f"   ✅ Dependabot: {msg}")
    else:
        print(f"   ⚠️  Dependabot: {msg}")
    
    time.sleep(2)  # Rate limiting
    
    # Setup Codespaces
    print(f"   🚀 Adding Codespaces configuration...")
    success, msg = create_file_via_git(
        repo,
        ".devcontainer/devcontainer.json",
        devcontainer_content,
        "⚙️ chore: setup GitHub Codespaces devcontainer"
    )
    
    if success:
        print(f"   ✅ Codespaces: {msg}")
    else:
        print(f"   ⚠️  Codespaces: {msg}")
    
    time.sleep(2)  # Rate limiting
    
    return True

def main():
    """Main entry point."""
    print("=" * 60)
    print("🔧 ADRION Dependabot + Codespaces Setup")
    print("=" * 60)
    
    success_count = 0
    
    for repo in REPOS:
        try:
            if setup_repo(repo):
                success_count += 1
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print(f"✅ Summary: {success_count}/{len(REPOS)} repos configured")
    print("=" * 60)
    
    return 0 if success_count == len(REPOS) else 1

if __name__ == "__main__":
    sys.exit(main())
