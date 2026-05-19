#!/usr/bin/env python3
import tempfile
import shutil
import subprocess
from pathlib import Path

def setup_dependabot_simple(repo_name, org="Gruszkoland"):
    """Clone repo, add Dependabot config, commit & push."""
    tmp_dir = Path(tempfile.gettempdir()) / f"adrion-{repo_name}"
    if tmp_dir.exists():
        shutil.rmtree(tmp_dir)
    tmp_dir.mkdir()
    
    repo_url = f"https://github.com/{org}/{repo_name}.git"
    repo_path = tmp_dir / repo_name
    
    try:
        # Clone
        subprocess.run(["git", "clone", repo_url, str(repo_path)], 
                       capture_output=True, timeout=30, check=False)
        
        if not (repo_path / ".git").exists():
            return False, "Clone failed"
        
        # Create .github/dependabot.yml
        gh_dir = repo_path / ".github"
        gh_dir.mkdir(exist_ok=True)
        
        dependabot_yml = """version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "daily"
      time: "02:00"
"""
        
        (gh_dir / "dependabot.yml").write_text(dependabot_yml)
        
        # Commit & push
        subprocess.run(["git", "-C", str(repo_path), "config", "user.name", "ADRION Bot"],
                       capture_output=True)
        subprocess.run(["git", "-C", str(repo_path), "config", "user.email", "bot@adrion.local"],
                       capture_output=True)
        subprocess.run(["git", "-C", str(repo_path), "add", "."],
                       capture_output=True)
        result = subprocess.run(["git", "-C", str(repo_path), "commit", "-m", 
                       "⚙️  chore: setup Dependabot"],
                       capture_output=True, text=True)
        
        if "nothing to commit" in result.stdout:
            return True, "Already configured"
            
        result = subprocess.run(["git", "-C", str(repo_path), "push"],
                               capture_output=True, text=True, timeout=30)
        
        return result.returncode == 0, result.stdout[:100] if result.returncode == 0 else result.stderr[:100]
    
    except Exception as e:
        return False, str(e)[:100]
    finally:
        if tmp_dir.exists():
            shutil.rmtree(tmp_dir)

# Test on 2 repos
print("Testing Dependabot setup...\n")
for repo in ["adrion-369", "adrion-architecture"]:
    success, msg = setup_dependabot_simple(repo)
    print(f"{repo}: {'✅' if success else '❌'}")
    print(f"  {msg}\n")
