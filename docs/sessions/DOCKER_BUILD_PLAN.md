# 🐳 ADRION 369 Docker Build & Push — Ready-to-Execute Plan

**Date**: 2026-05-12  
**Registry**: ghcr.io/gruszkoland  
**Dockerfile**: Dockerfile.multi-stage  
**Target Platform**: Linux/amd64

---

## 📋 Prerequisites (Before Running)

1. ✅ Docker Desktop running (`docker ps` should work)
2. ✅ Authenticated to ghcr.io: `docker login ghcr.io -u Gruszkoland --password-stdin`
3. ✅ Terminal in repo root: `C:\Users\adiha\.1_Projekty\162 demencje w schemacie 369`

---

## 🔨 Service Build Commands (Copy & Paste)

### Service 1: Genesis MCP (Port 9100)

```bash
docker build --target genesis-mcp -t ghcr.io/gruszkoland/adrion-genesis-mcp:latest -f Dockerfile.multi-stage --build-arg SERVICE_PORT=9100 .
docker push ghcr.io/gruszkoland/adrion-genesis-mcp:latest
```

### Service 2: Guardian MCP (Port 9101)

```bash
docker build --target guardian-mcp -t ghcr.io/gruszkoland/adrion-guardian-mcp:latest -f Dockerfile.multi-stage --build-arg SERVICE_PORT=9101 .
docker push ghcr.io/gruszkoland/adrion-guardian-mcp:latest
```

### Service 3: Healer MCP (Port 9102)

```bash
docker build --target healer-mcp -t ghcr.io/gruszkoland/adrion-healer-mcp:latest -f Dockerfile.multi-stage --build-arg SERVICE_PORT=9102 .
docker push ghcr.io/gruszkoland/adrion-healer-mcp:latest
```

### Service 4: Vortex MCP (Port 1740)

```bash
docker build --target vortex-mcp -t ghcr.io/gruszkoland/adrion-vortex-mcp:latest -f Dockerfile.multi-stage --build-arg SERVICE_PORT=1740 .
docker push ghcr.io/gruszkoland/adrion-vortex-mcp:latest
```

### Service 5: Oracle MCP (Port 9103)

```bash
docker build --target oracle-mcp -t ghcr.io/gruszkoland/adrion-oracle-mcp:latest -f Dockerfile.multi-stage --build-arg SERVICE_PORT=9103 .
docker push ghcr.io/gruszkoland/adrion-oracle-mcp:latest
```

### Service 6: MCP Router (Port 9000)

```bash
docker build --target mcp-router -t ghcr.io/gruszkoland/adrion-mcp-router:latest -f Dockerfile.multi-stage --build-arg SERVICE_PORT=9000 .
docker push ghcr.io/gruszkoland/adrion-mcp-router:latest
```

### Service 7: MCP Tier (Port 8002)

```bash
docker build --target mcp-tier -t ghcr.io/gruszkoland/adrion-mcp-tier:latest -f Dockerfile.multi-stage --build-arg SERVICE_PORT=8002 .
docker push ghcr.io/gruszkoland/adrion-mcp-tier:latest
```

---

## ⚡ One-Liner (Build All 7 Services)

```powershell
$services = @("genesis-mcp:9100", "guardian-mcp:9101", "healer-mcp:9102", "vortex-mcp:1740", "oracle-mcp:9103", "mcp-router:9000", "mcp-tier:8002"); foreach ($s in $services) { $t = $s.Split(":")[0]; $p = $s.Split(":")[1]; docker build --target $t -t ghcr.io/gruszkoland/adrion-$t`:latest -f Dockerfile.multi-stage --build-arg SERVICE_PORT=$p . ; docker push ghcr.io/gruszkoland/adrion-$t`:latest ; }
```

---

## 📥 docker-compose.yml Updates

After pushing images, update these files to reference new images:

### Files to Update

- `docker-compose.yml` (primary)
- `docker-compose.prod.yml`
- `docker-compose.local.yml`
- `docker-compose.k8s-integration.yml`

### Example Update

```yaml
# Before:
services:
  guardian:
    build:
      context: .
      dockerfile: Dockerfile.guardian-mcp

# After:
services:
  guardian:
    image: ghcr.io/gruszkoland/adrion-guardian-mcp:latest
    ports:
      - "9101:9101"
    environment:
      SERVICE_PORT: "9101"
```

---

## ✅ Verification Steps

After all pushes complete:

```bash
# 1. List pushed images
docker images | grep ghcr.io/gruszkoland

# 2. Pull and test one service
docker pull ghcr.io/gruszkoland/adrion-guardian-mcp:latest
docker run --rm ghcr.io/gruszkoland/adrion-guardian-mcp:latest --version

# 3. Check registry via curl (requires auth)
curl -H "Authorization: Bearer $TOKEN" https://ghcr.io/v2/gruszkoland/adrion-guardian-mcp/tags/list

# 4. Verify docker-compose can pull images
docker-compose config
```

---

## 🚀 Deployment to Production

Once images are verified:

```bash
# 1. Commit build commands to Git (optional)
git add scripts/build-push-docker.ps1 Dockerfile.multi-stage
git commit -m "docs: docker build and push commands for 7 services"
git push origin master

# 2. Update docker-compose files (in separate PR or commit)
# 3. Deploy to Kubernetes or Docker Swarm with updated compose files
# 4. Monitor health checks on all services (30s interval, 10s timeout)
```

---

## ⏱️ Estimated Build Times

| Service | Size (MB) | Build Time | Push Time |
|---------|-----------|-----------|-----------|
| genesis-mcp | 280 | 4-6 min | 1-2 min |
| guardian-mcp | 285 | 4-6 min | 1-2 min |
| healer-mcp | 282 | 4-6 min | 1-2 min |
| vortex-mcp (Go) | 120 | 3-5 min | 0.5-1 min |
| oracle-mcp | 283 | 4-6 min | 1-2 min |
| mcp-router | 280 | 4-6 min | 1-2 min |
| mcp-tier | 281 | 4-6 min | 1-2 min |
| **TOTAL** | **1,911** | **~30 min** | **~10 min** |

---

## 🔐 Security Notes

- ✅ Non-root user: `adrion:adrion` (enforced in Dockerfile)
- ✅ Health checks: 30s interval, 10s timeout, 3 retries
- ✅ Python 3.11-slim: Minimal attack surface
- ✅ Multi-stage: Only final binary/code copied (build artifacts discarded)
- ✅ Token used for login is temporary (consider rotating after push)

---

## 📊 Status Checklist

- [ ] Docker Desktop is running
- [ ] Authenticated to ghcr.io
- [ ] All 7 build commands executed
- [ ] All 7 push commands executed
- [ ] docker-compose.yml files updated
- [ ] Health checks verified on all services
- [ ] Pull test successful on random service
- [ ] Commit and push to master

---

**Next Step**: Start Docker Desktop, then execute the one-liner or individual build commands above.
