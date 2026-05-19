# ============================================================================
# ANALYZE-THEMES.PS1 - Extract themes from Knowledge Bank documents
# Purpose: Analyze file paths and names to extract topics/themes
# Output: Generates THEMES.md with thematic index
# ============================================================================

param(
    [string]$VaultRoot = "C:\Users\adiha\Desktop\Dokumentacja\Obsydian-synchronizacja dokumentów\_PROJEKTY_SCALONE",
    [string]$OutputFile = "THEMES.md"
)

# Color configuration
$colors = @{
    Info = 'Cyan'
    Success = 'Green'
    Warning = 'Yellow'
    Error = 'Red'
}

function Write-Log {
    param([string]$Message, [string]$Type = 'Info')
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $color = $colors[$Type]
    Write-Host "[$timestamp] " -NoNewline -ForegroundColor DarkGray
    Write-Host $Message -ForegroundColor $color
}

# Theme definitions - patterns to recognize common topics
$themePatterns = @{
    'Architecture & Design' = @('architecture', 'design', 'schema', 'diagram', 'plan', 'blueprint', 'structure', 'topology')
    'Implementation' = @('implementation', 'code', 'src', 'backend', 'frontend', 'service', 'algorithm', 'logic', 'lib')
    'Testing & QA' = @('test', 'spec', 'qa', 'validation', 'verification', 'e2e', 'unit', 'integration')
    'Monitoring & Logging' = @('monitoring', 'logging', 'alert', 'metrics', 'health', 'telemetry', 'trace', 'debug')
    'Database & Storage' = @('database', 'db', 'sql', 'storage', 'cache', 'redis', 'postgres', 'mongo', 'data')
    'DevOps & Infrastructure' = @('docker', 'kubernetes', 'k8s', 'devops', 'infrastructure', 'deploy', 'aks', 'cloud', 'terraform', 'bicep')
    'Security' = @('security', 'auth', 'encryption', 'certificate', 'rbac', 'permission', 'access', 'vault', 'secret')
    'Documentation' = @('readme', 'guide', 'manual', 'doc', 'tutorial', 'howto', 'reference', 'api', 'spec')
    'Configuration' = @('config', 'settings', 'env', 'parameter', 'variable', 'yaml', 'json', 'toml')
    'Orchestration & Automation' = @('orchestration', 'workflow', 'automation', 'agent', 'crew', 'swarm', 'n8n', 'airflow')
    'API & Integration' = @('api', 'rest', 'graphql', 'integration', 'webhook', 'connector', 'adapter')
    'Scripting & Tools' = @('script', 'tool', 'utility', 'cli', 'command', 'bash', 'powershell', 'python')
}

function Get-ThemesFromPath {
    param([string]$Path)
    $themes = @()
    $pathLower = $Path.ToLower()
    
    foreach ($theme in $themePatterns.GetEnumerator()) {
        foreach ($pattern in $theme.Value) {
            if ($pathLower -match $pattern) {
                $themes += $theme.Name
                break
            }
        }
    }
    
    if ($themes.Count -eq 0) {
        $themes += "Miscellaneous"
    }
    
    return $themes | Select-Object -Unique
}

try {
    Write-Log "Starting theme analysis..." Info
    Write-Log "Vault root: $VaultRoot" Info
    
    if (-not (Test-Path $VaultRoot)) {
        Write-Log "ERROR: Vault root not found at $VaultRoot" Error
        exit 1
    }

    # Collect all markdown files
    $files = Get-ChildItem -Path $VaultRoot -Filter "*.md" -Recurse -File | 
        Where-Object { $_.Name -notmatch '^(INDEX|_MAPY|THEMES|IMPORTANCE)' }
    
    Write-Log "Found $($files.Count) markdown files to analyze" Info

    # Build theme map
    $themeMap = @{}
    foreach ($theme in $themePatterns.Keys) {
        $themeMap[$theme] = @()
    }
    $themeMap["Miscellaneous"] = @()

    # Analyze each file
    $processed = 0
    foreach ($file in $files) {
        $processed++
        if ($processed % 500 -eq 0) {
            Write-Log "Processed: $processed / $($files.Count)" Info
        }

        $relativePath = $file.FullName.Substring($VaultRoot.Length + 1)
        $themes = Get-ThemesFromPath -Path $relativePath
        
        foreach ($theme in $themes) {
            $themeMap[$theme] += @{
                Name = $file.Name
                Path = $relativePath
                Size = $file.Length
                Modified = $file.LastWriteTime
            }
        }
    }

    Write-Log "Analysis complete! Building markdown..." Success
    
    # Generate markdown output
    $markdown = @()
    $markdown += "# 📚 Tematyczny Indeks Knowledge Bank"
    $markdown += ""
    $markdown += "> **Mapa tematyczna** — Dokumenty zorganizowane wg dziedzin i tematów"
    $markdown += ""
    $markdown += "| Temat | Liczba Plików | Procent |"
    $markdown += "|-------|---------------|--------|"
    
    $totalDocs = ($themeMap.Values | Measure-Object -Sum { $_.Count }).Sum
    foreach ($theme in $themePatterns.Keys) {
        $count = $themeMap[$theme].Count
        $percent = [math]::Round(($count / $totalDocs) * 100, 1)
        $markdown += "| [$theme](#$($theme.ToLower().Replace(' ', '-').Replace('&', 'and'))) | $count | $percent% |"
    }
    
    $miscCount = $themeMap["Miscellaneous"].Count
    $miscPercent = [math]::Round(($miscCount / $totalDocs) * 100, 1)
    $markdown += "| [Miscellaneous](#miscellaneous) | $miscCount | $miscPercent% |"
    $markdown += ""
    $markdown += "---"
    $markdown += ""
    
    # Generate detailed sections
    $sortedThemes = $themeMap.Keys | Sort-Object { -$themeMap[$_].Count }
    
    foreach ($theme in $sortedThemes) {
        $docs = $themeMap[$theme] | Sort-Object -Property Modified -Descending
        if ($docs.Count -eq 0) { continue }
        
        $anchorName = $theme.ToLower().Replace(' ', '-').Replace('&', 'and')
        $markdown += "## $theme"
        $markdown += ""
        $markdown += "**$($docs.Count) dokumentów**"
        $markdown += ""
        $markdown += "| Dokument | Rozmiar | Ostatnia Modyfikacja |"
        $markdown += "|----------|---------|----------------------|"
        
        $samples = $docs | Select-Object -First 50
        foreach ($doc in $samples) {
            $sizeMB = [math]::Round($doc.Size / 1MB, 2)
            $modDate = $doc.Modified.ToString("yyyy-MM-dd HH:mm")
            $docLink = "[$(Split-Path $doc.Path -Leaf)]($($doc.Path))"
            $markdown += "| $docLink | $sizeMB MB | $modDate |"
        }
        
        if ($docs.Count -gt 50) {
            $markdown += "| ... i $($docs.Count - 50) więcej ... | | |"
        }
        
        $markdown += ""
        $markdown += "[⬆ Wróć do indeksu](#-tematyczny-indeks-knowledge-bank)"
        $markdown += ""
    }
    
    # Write output
    $outputPath = Join-Path $VaultRoot $OutputFile
    $markdown | Set-Content -Path $outputPath -Encoding UTF8 -NoNewline
    
    Write-Log "✓ Themes index written to: $outputPath" Success
    Write-Log "Total documents categorized: $totalDocs" Info
    Write-Log "Total themes: $($themeMap.Keys.Count)" Info
    
    # Summary statistics
    Write-Host ""
    Write-Host "📊 THEME DISTRIBUTION:" -ForegroundColor Cyan
    foreach ($theme in $sortedThemes) {
        $count = $themeMap[$theme].Count
        $percent = [math]::Round(($count / $totalDocs) * 100, 1)
        Write-Host "  • $theme: $count ($percent%)" -ForegroundColor Green
    }
    
}
catch {
    Write-Log "ERROR: $_" Error
    Write-Log $_.Exception.StackTrace Error
    exit 1
}
