#!/usr/bin/env python3
"""
Add GitHub topics to all 9 Gruszkoland repos
"""
import subprocess
import sys

repos_topics = {
    "adrion-369": ["ai-agents", "multi-agent-systems", "orchestration", "rope-framework", "llm", "autonomous-agents"],
    "adrion-architecture": ["system-architecture", "ai-design", "decision-frameworks", "enterprise-architecture"],
    "adrion-deploy": ["kubernetes", "docker", "devops", "infrastructure", "monitoring", "prometheus", "grafana", "caddy"],
    "consultacao-ai": ["llm", "conversational-ai", "multi-model", "claude", "openai", "ollama", "local-llm"],
    "embedding-ab-test": ["embeddings", "ml-testing", "ab-testing", "framework", "vector-search"],
    "leadgen-comet": ["lead-generation", "sales-automation", "google-maps", "llm", "b2b-automation"],
    "punkt-odniesienia": ["documentation", "knowledge-base", "synchronization", "notes"],
    "n8n-workflows-prod": ["n8n", "automation", "workflows", "orchestration", "production"],
    "kyc-provider-guide": ["kyc", "compliance", "integration", "identity-verification"],
}

def add_topics(repo_name, topics):
    """Add topics to a single repo"""
    print(f"📌 {repo_name}: Adding {len(topics)} topics...")
    
    # Build command with individual --add-topic flags
    cmd = ["gh", "repo", "edit", f"Gruszkoland/{repo_name}"]
    for topic in topics:
        cmd.extend(["--add-topic", topic])
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print(f"   ✅ {repo_name}: Success")
            return True
        else:
            print(f"   ❌ {repo_name}: {result.stderr.strip()}")
            return False
    except subprocess.TimeoutExpired:
        print(f"   ⏱️  {repo_name}: Timeout")
        return False
    except Exception as e:
        print(f"   ⚠️  {repo_name}: {str(e)}")
        return False

def main():
    print("\n" + "="*60)
    print("📦 Adding GitHub Topics to All Repos")
    print("="*60 + "\n")
    
    success_count = 0
    for repo_name, topics in repos_topics.items():
        if add_topics(repo_name, topics):
            success_count += 1
    
    print("\n" + "="*60)
    print(f"✅ Summary: {success_count}/{len(repos_topics)} repos updated")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
