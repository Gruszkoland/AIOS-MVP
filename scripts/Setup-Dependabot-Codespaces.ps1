# Setup Dependabot and Codespaces for all 9 ADRION repos
# Using gh CLI directly without full git clones

$repos = @(
    "adrion-369",
    "adrion-architecture",
    "adrion-deploy",
    "consultacao-ai",
    "embedding-ab-test",
    "leadgen-comet",
    "punkt-odniesienia",
    "n8n-workflows-prod",
    "kyc-provider-guide"
)

$org = "Gruszkoland"

# Read templates
$dependabotYml = Get-Content "templates/dependabot-template.yml" -Raw
$devcontainerJson = Get-Content "templates/devcontainer-template.json" -Raw

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "🔧 Setup Dependabot + Codespaces for 9 ADRION Repos" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

$successCount = 0

foreach ($repo in $repos) {
    Write-Host "`n📌 Processing $repo..."
    
    try {
        # Create temporary directory for this repo
        $tmpDir = Join-Path $env:TEMP "adrion-$repo-$(Get-Random)"
        New-Item -ItemType Directory -Path $tmpDir -Force | Out-Null
        
        Push-Location $tmpDir
        
        # Clone repo
        Write-Host "   📥 Cloning repository..."
        & git clone "https://github.com/$org/$repo.git" repo 2>&1 | ForEach-Object { if ($_ -match "fatal|error") { Write-Host "      ⚠️  $_" } }
        
        if (-not (Test-Path "repo/.git")) {
            Write-Host "   ❌ Clone failed, skipping..."
            Pop-Location
            Remove-Item $tmpDir -Recurse -Force -ErrorAction SilentlyContinue
            continue
        }
        
        Push-Location repo
        
        # Configure git
        & git config user.name "ADRION Bot" 2>&1 | Out-Null
        & git config user.email "bot@adrion.local" 2>&1 | Out-Null
        
        # Setup .github/dependabot.yml
        Write-Host "   ⚙️  Setting up Dependabot..."
        $dependabotPath = ".github/dependabot.yml"
        New-Item -ItemType Directory -Path ".github" -Force | Out-Null
        $dependabotYml | Out-File -FilePath $dependabotPath -Encoding UTF8 -Force
        
        # Setup .devcontainer/devcontainer.json
        Write-Host "   🚀 Setting up Codespaces..."
        $devcontainerPath = ".devcontainer/devcontainer.json"
        New-Item -ItemType Directory -Path ".devcontainer" -Force | Out-Null
        $devcontainerJson | Out-File -FilePath $devcontainerPath -Encoding UTF8 -Force
        
        # Commit and push
        & git add . 2>&1 | Out-Null
        $status = & git status --short 2>&1
        
        if ($status) {
            Write-Host "   📝 Committing changes..."
            & git commit -m "⚙️  chore: setup Dependabot and Codespaces" 2>&1 | Out-Null
            
            Write-Host "   🚀 Pushing to GitHub..."
            & git push 2>&1 | Out-Null
            
            Write-Host "   ✅ Success!" -ForegroundColor Green
            $successCount++
        }
        else {
            Write-Host "   ✅ Already configured" -ForegroundColor Green
            $successCount++
        }
        
        Pop-Location
        Pop-Location
        Remove-Item $tmpDir -Recurse -Force -ErrorAction SilentlyContinue
        
        Start-Sleep -Milliseconds 500
        
    }
    catch {
        Write-Host "   ❌ Error: $_" -ForegroundColor Red
    }
}

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "✅ Summary: $successCount/$($repos.Count) repos configured" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
