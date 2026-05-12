# Build and push 7 ADRION 369 services to ghcr.io
# Usage: ./scripts/build-push-docker.ps1

$REGISTRY = "ghcr.io/gruszkoland"
$DOCKERFILE = "Dockerfile.multi-stage"
$SERVICES = @(
    "genesis-mcp:9100",
    "guardian-mcp:9101",
    "healer-mcp:9102",
    "vortex-mcp:1740",
    "oracle-mcp:9103",
    "mcp-router:9000",
    "mcp-tier:8002"
)

$ErrorCount = 0
$SuccessCount = 0

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "ADRION 369 Docker Build & Push Pipeline" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

foreach ($service in $SERVICES) {
    $target = $service.Split(":")[0]
    $port = $service.Split(":")[1]
    $image_tag = "$REGISTRY/adrion-$target`:latest"
    
    Write-Host "🔨 Building: $target (port: $port)" -ForegroundColor Yellow
    Write-Host "   Target image: $image_tag" -ForegroundColor Gray
    
    # Build image with multi-stage Dockerfile
    $build_cmd = @(
        "docker", "build",
        "--target", $target,
        "-t", $image_tag,
        "-f", $DOCKERFILE,
        "--build-arg", "SERVICE_PORT=$port",
        "."
    )
    
    $build_result = & $build_cmd[0] @($build_cmd[1..($build_cmd.Count - 1)]) 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ Build successful" -ForegroundColor Green
        
        # Push to registry
        Write-Host "   📤 Pushing to registry..." -ForegroundColor Yellow
        $push_result = docker push $image_tag 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "   ✅ Push successful" -ForegroundColor Green
            $SuccessCount += 1
        }
        else {
            Write-Host "   ❌ Push failed" -ForegroundColor Red
            $ErrorCount += 1
        }
    }
    else {
        Write-Host "   ❌ Build failed" -ForegroundColor Red
        $ErrorCount += 1
    }
    
    Write-Host ""
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Summary: ✅ $SuccessCount successful | ❌ $ErrorCount failed" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
