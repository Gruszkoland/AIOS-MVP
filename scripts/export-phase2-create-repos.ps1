#!/usr/bin/env pwsh
# Export 8 new projects to GitHub (Phase 2)
# Creates repos + initializes git + pushes

$OWNER = "Gruszkoland"
$BASE_PATH = "C:\Users\adiha\.1_Projekty"

$PROJECTS = @(
    @{
        name        = "adrion-architecture"
        local_path  = "adrion-369-architecture"
        description = "ADRION system architecture, Guardian Laws, 162D decision space"
        homepage    = "https://github.com/Gruszkoland/adrion-369"
    },
    @{
        name        = "adrion-deploy"
        local_path  = "adrion-deploy"
        description = "Kubernetes, Docker Compose, Prometheus, Grafana, Caddy configs"
        homepage    = "https://github.com/Gruszkoland/adrion-369"
    },
    @{
        name        = "consultacao-ai"
        local_path  = "Consultacja-Wielomodelowa-AI"
        description = "Multi-model LLM consultation system (Claude, GPT, local Ollama)"
        homepage    = "https://github.com/Gruszkoland/adrion-369"
    },
    @{
        name        = "embedding-ab-test"
        local_path  = "embedding-ab-test-framework"
        description = "AB testing framework for embeddings and ML models"
        homepage    = "https://github.com/Gruszkoland/adrion-369"
    },
    @{
        name        = "leadgen-comet"
        local_path  = "leadgen-comet-pipeline"
        description = "Lead generation pipeline with async agents and webhooks"
        homepage    = "https://github.com/Gruszkoland/adrion-369"
    },
    @{
        name        = "punkt-odniesienia"
        local_path  = "Punkt odniesienia"
        description = "Benchmark and reference implementation for core ADRION patterns"
        homepage    = "https://github.com/Gruszkoland/adrion-369"
    },
    @{
        name        = "n8n-workflows-prod"
        local_path  = "n8n-produkcja"
        description = "Production n8n workflows, automation, orchestration"
        homepage    = "https://github.com/Gruszkoland/adrion-369"
    },
    @{
        name        = "kyc-provider-guide"
        local_path  = "kyc-provider-integration-guide"
        description = "KYC provider integration guide (Sumsub, IDnow, etc.)"
        homepage    = "https://github.com/Gruszkoland/adrion-369"
    }
)

$SuccessCount = 0
$FailCount = 0
$CreatedRepos = @()

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Phase 2: Create 8 GitHub Repos + Push" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

foreach ($project in $PROJECTS) {
    $repo_name = $project.name
    $local_path = "$BASE_PATH\$($project.local_path)"
    $repo_url = "https://github.com/$OWNER/$repo_name.git"
    
    Write-Host "📦 Processing: $repo_name" -ForegroundColor Yellow
    
    # Check if local path exists
    if (-not (Test-Path $local_path)) {
        Write-Host "   ❌ Local path not found: $local_path" -ForegroundColor Red
        $FailCount++
        Write-Host ""
        continue
    }
    
    # Create GitHub repo
    Write-Host "   🔨 Creating GitHub repo..." -ForegroundColor Cyan
    try {
        $create_cmd = gh repo create "$OWNER/$repo_name" `
            --public `
            --description $project.description `
            --homepage $project.homepage `
            --source=$local_path `
            --remote=origin `
            --push 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "   ✅ Repo created & pushed" -ForegroundColor Green
            $CreatedRepos += $repo_name
            $SuccessCount++
        }
        else {
            Write-Host "   ⚠️  Repo may already exist, attempting git init + push..." -ForegroundColor Yellow
            
            # Fallback: init + push if repo exists
            Push-Location $local_path
            if (-not (Test-Path ".git")) {
                git init
                git add -A
                git commit -m "Initial commit: $($project.description)"
            }
            git remote remove origin 2>$null
            git remote add origin $repo_url
            git branch -M master
            git push -u origin master 2>&1 | Out-Null
            Pop-Location
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host "   ✅ Fallback push succeeded" -ForegroundColor Green
                $CreatedRepos += $repo_name
                $SuccessCount++
            }
            else {
                Write-Host "   ❌ Failed" -ForegroundColor Red
                $FailCount++
            }
        }
    }
    catch {
        Write-Host "   ❌ Error: $_" -ForegroundColor Red
        $FailCount++
    }
    
    Write-Host ""
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Summary: ✅ $SuccessCount success | ❌ $FailCount failed" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

if ($CreatedRepos.Count -gt 0) {
    Write-Host "Created repositories:" -ForegroundColor Green
    $CreatedRepos | ForEach-Object { 
        Write-Host "  🟢 https://github.com/$OWNER/$_" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Verify all repos on GitHub: https://github.com/$OWNER?tab=repositories" -ForegroundColor Gray
Write-Host "2. Update cross-project references in adrion-369 README" -ForegroundColor Gray
Write-Host "3. Pin related repos as topics" -ForegroundColor Gray
