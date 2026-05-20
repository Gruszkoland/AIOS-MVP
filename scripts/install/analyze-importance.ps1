# ============================================================================
# ANALYZE-IMPORTANCE.PS1 - Rate document importance and usefulness
# Purpose: Assign importance tiers based on multiple criteria
# Output: Generates IMPORTANCE.md with categorized documents
# ============================================================================

param(
    [string]$VaultRoot = "C:\Users\adiha\Desktop\Dokumentacja\Obsydian-synchronizacja dokumentów\_PROJEKTY_SCALONE",
    [string]$OutputFile = "IMPORTANCE.md"
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

# Priority keywords for importance scoring
$criticalKeywords = @('MANIFEST', 'README', 'ARCHITECTURE', 'SECURITY', 'DEPLOYMENT', 'INTEGRATION', 'API', 'SCHEMA')
$highKeywords = @('config', 'setup', 'installation', 'guide', 'implementation', 'blueprint', 'standards', 'requirements')
$mediumKeywords = @('test', 'example', 'documentation', 'reference', 'script', 'utility', 'helper')

function Calculate-ImportanceScore {
    param(
        [PSObject]$File,
        [int]$LinkCount = 0
    )
    
    $score = 0
    $nameUpper = $File.Name.ToUpper()
    $pathLower = $File.FullName.ToLower()
    
    # 1. Filename-based scoring (0-30 points)
    foreach ($keyword in $criticalKeywords) {
        if ($nameUpper -match $keyword) {
            $score += 20
            break
        }
    }
    
    foreach ($keyword in $highKeywords) {
        if ($nameUpper -match $keyword) {
            $score += 10
            break
        }
    }
    
    # 2. File size scoring (0-20 points)
    $sizeKB = $File.Length / 1KB
    if ($sizeKB -gt 500) { $score += 20 }
    elseif ($sizeKB -gt 100) { $score += 15 }
    elseif ($sizeKB -gt 20) { $score += 10 }
    elseif ($sizeKB -gt 5) { $score += 5 }
    
    # 3. Path depth scoring (0-15 points) - root level docs are more important
    $depth = ($File.FullName.Split('\').Count - $VaultRoot.Split('\').Count)
    if ($depth -lt 2) { $score += 15 }
    elseif ($depth -lt 3) { $score += 10 }
    elseif ($depth -lt 4) { $score += 5 }
    
    # 4. File type scoring (0-20 points)
    if ($File.Extension -eq '.md') { $score += 15 }
    elseif ($File.Extension -match '\.(yaml|yml|json|toml)$') { $score += 10 }
    elseif ($File.Extension -match '\.(py|go|ts|js|sh)$') { $score += 8 }
    
    # 5. Modification recency (0-15 points)
    $daysSinceModified = (Get-Date) - $File.LastWriteTime
    if ($daysSinceModified.Days -lt 30) { $score += 15 }
    elseif ($daysSinceModified.Days -lt 90) { $score += 10 }
    elseif ($daysSinceModified.Days -lt 180) { $score += 5 }
    
    # 6. Link popularity bonus (0-10 points)
    if ($LinkCount -gt 10) { $score += 10 }
    elseif ($LinkCount -gt 5) { $score += 7 }
    elseif ($LinkCount -gt 2) { $score += 4 }
    
    return [Math]::Min($score, 100)
}

function Get-ImportanceTier {
    param([int]$Score)
    
    if ($Score -ge 85) { return '🔴 KRYTYCZNE' }
    elseif ($Score -ge 70) { return '🟠 WYSOKIE' }
    elseif ($Score -ge 50) { return '🟡 ŚREDNIE' }
    else { return '🟢 NISKIE' }
}

try {
    Write-Log "Starting importance analysis..." Info
    Write-Log "Vault root: $VaultRoot" Info
    
    if (-not (Test-Path $VaultRoot)) {
        Write-Log "ERROR: Vault root not found at $VaultRoot" Error
        exit 1
    }

    # Collect all markdown files with link counting
    Write-Log "Scanning files..." Info
    $files = Get-ChildItem -Path $VaultRoot -Filter "*.md" -Recurse -File | 
        Where-Object { $_.Name -notmatch '^(INDEX|_MAPY|THEMES|IMPORTANCE)' }
    
    Write-Log "Found $($files.Count) markdown files" Info
    
    # Build link map (count references to each file)
    Write-Log "Counting cross-references..." Info
    $linkMap = @{}
    $processed = 0
    
    foreach ($file in $files) {
        $processed++
        if ($processed % 500 -eq 0) {
            Write-Log "Processed: $processed / $($files.Count)" Info
        }
        
        try {
            $content = Get-Content $file.FullName -Raw -ErrorAction SilentlyContinue
            if ($null -ne $content) {
                # Find markdown links [text](path)
                $matches = [regex]::Matches($content, '\]\(([^)]+)\)')
                foreach ($match in $matches) {
                    $linkedPath = $match.Groups[1].Value
                    # Normalize path
                    $linkedPath = $linkedPath.Replace('/', '\')
                    $linkMap[$linkedPath] = ($linkMap[$linkedPath] -as [int]) + 1
                }
            }
        }
        catch { }
    }
    
    Write-Log "Calculating importance scores..." Info
    
    # Score each file
    $scoredFiles = @()
    foreach ($file in $files) {
        $relativePath = $file.FullName.Substring($VaultRoot.Length + 1)
        $linkCount = $linkMap[$relativePath] -as [int]
        $score = Calculate-ImportanceScore -File $file -LinkCount $linkCount
        $tier = Get-ImportanceTier -Score $score
        
        $scoredFiles += @{
            File = $file
            RelativePath = $relativePath
            Score = $score
            Tier = $tier
            LinkCount = $linkCount
            Size = $file.Length
            Modified = $file.LastWriteTime
        }
    }
    
    # Sort by score descending
    $scoredFiles = $scoredFiles | Sort-Object -Property Score -Descending
    
    Write-Log "Generating markdown report..." Success
    
    # Generate markdown output
    $markdown = @()
    $markdown += "# 🎯 Ważność i Przydatność Dokumentów"
    $markdown += ""
    $markdown += "> **Kategorie Ważności** — Dokumenty ocenione wg krytyczności i przydatności"
    $markdown += ""
    $markdown += "| Kategoria | Liczba | Średni Score |"
    $markdown += "|-----------|--------|-------------|"
    
    $tiers = @('🔴 KRYTYCZNE', '🟠 WYSOKIE', '🟡 ŚREDNIE', '🟢 NISKIE')
    foreach ($tier in $tiers) {
        $tierFiles = $scoredFiles | Where-Object { $_.Tier -eq $tier }
        if ($tierFiles.Count -gt 0) {
            $avgScore = [math]::Round(($tierFiles | Measure-Object -Property Score -Average).Average, 1)
            $markdown += "| $tier | $($tierFiles.Count) | $avgScore |"
        }
    }
    
    $markdown += ""
    $markdown += "---"
    $markdown += ""
    
    # Generate tier-based sections
    foreach ($tier in $tiers) {
        $tierFiles = $scoredFiles | Where-Object { $_.Tier -eq $tier }
        if ($tierFiles.Count -eq 0) { continue }
        
        $markdown += "## $tier"
        $markdown += ""
        $markdown += "**$($tierFiles.Count) dokumentów**"
        $markdown += ""
        $markdown += "| Dokument | Score | Links | Rozmiar | Ostatnia Zmiana |"
        $markdown += "|----------|-------|-------|---------|-----------------|"
        
        $samples = $tierFiles | Select-Object -First 100
        foreach ($doc in $samples) {
            $sizeMB = [math]::Round($doc.Size / 1MB, 2)
            $modDate = $doc.Modified.ToString("yyyy-MM-dd HH:mm")
            $docLink = "[$(Split-Path $doc.RelativePath -Leaf)]($($doc.RelativePath))"
            $markdown += "| $docLink | $($doc.Score) | $($doc.LinkCount) | $sizeMB MB | $modDate |"
        }
        
        if ($tierFiles.Count -gt 100) {
            $markdown += "| ... i $($tierFiles.Count - 100) więcej ... | | | | |"
        }
        
        $markdown += ""
    }
    
    # Add scoring criteria section
    $markdown += "---"
    $markdown += ""
    $markdown += "## 📊 Kryteria Oceny (0-100 punktów)"
    $markdown += ""
    $markdown += "1. **Słowa kluczowe** (do 20 pkt): README, MANIFEST, ARCHITECTURE, SECURITY, DEPLOYMENT"
    $markdown += "2. **Rozmiar pliku** (do 20 pkt): Większe = bardziej szczegółowe"
    $markdown += "3. **Głębokość ścieżki** (do 15 pkt): Root level dokumenty są bardziej centralne"
    $markdown += "4. **Typ pliku** (do 20 pkt): .md > .yaml > .py/.ts"
    $markdown += "5. **Świeżość** (do 15 pkt): Ostatnio modyfikowane są bardziej relevantne"
    $markdown += "6. **Popularność** (do 10 pkt): Liczba wewnętrznych linków do dokumentu"
    $markdown += ""
    $markdown += "**Kategorie:**"
    $markdown += "- 🔴 **KRYTYCZNE** (85-100): Fundamentalne dla całego Knowledge Bank'u"
    $markdown += "- 🟠 **WYSOKIE** (70-84): Ważne dla zdecydowanej większości projektów"
    $markdown += "- 🟡 **ŚREDNIE** (50-69): Przydatne, ale nie krytyczne"
    $markdown += "- 🟢 **NISKIE** (0-49): Specjalistyczne, niszowe, archiwalne"
    $markdown += ""
    
    # Write output
    $outputPath = Join-Path $VaultRoot $OutputFile
    $markdown | Set-Content -Path $outputPath -Encoding UTF8 -NoNewline
    
    Write-Log "✓ Importance index written to: $outputPath" Success
    
    # Summary statistics
    Write-Host ""
    Write-Host "📊 IMPORTANCE DISTRIBUTION:" -ForegroundColor Cyan
    foreach ($tier in $tiers) {
        $tierFiles = $scoredFiles | Where-Object { $_.Tier -eq $tier }
        if ($tierFiles.Count -gt 0) {
            $percent = [math]::Round(($tierFiles.Count / $scoredFiles.Count) * 100, 1)
            Write-Host "  $tier: $($tierFiles.Count) docs ($percent%)" -ForegroundColor Green
        }
    }
    
    Write-Host ""
    Write-Host "🏆 TOP 10 CRITICAL DOCUMENTS:" -ForegroundColor Yellow
    $scoredFiles | Select-Object -First 10 | ForEach-Object {
        Write-Host "  [$($_.Score)] $($_.RelativePath)" -ForegroundColor Cyan
    }
    
}
catch {
    Write-Log "ERROR: $_" Error
    Write-Log $_.Exception.StackTrace Error
    exit 1
}
