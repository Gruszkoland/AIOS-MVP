---
name: Hetzner-Deployer
description: Specialized skill for managing deployment on Hetzner Cloud. Includes SSH management, Docker Compose orchestration, and security hardening for Ubuntu 24.04 servers.
---

# Hetzner Deployer

Use this skill for all operations related to the ADRION infrastructure on Hetzner Cloud.

## Infrastructure Specification
- **Provider:** Hetzner Cloud
- **Project:** `adrion-system`
- **Server:** CPX32 (Ubuntu 24.04)
- **IP:** `178.105.59.41`
- **SSH Key:** `adrion-vps` (Ed25519)

## Deployment Protocols

### 1. Security Hardening
- **Firewall (UFW):**
  - Allow: 22 (SSH), 80 (HTTP), 443 (HTTPS), 9000-9005 (MCP Layer).
  - Deny: All others.
- **Fail2Ban:** Active monitoring of SSH attempts.
- **Secrets:** Never store `.env` files in git. Use the `1_DANE_DO_WDROZENIA.md` checklist for secret generation.

### 2. Docker Orchestration
The stack consists of 11 healthy containers (checked via `docker ps`):
- `adrion_n8n`, `adrion_backend`, `adrion_caddy`, `adrion_frontend`
- `adrion_postgres`, `adrion_prometheus`, `adrion_grafana`
- `adrion_alertmanager`, `adrion_node_exporter`, `adrion_cadvisor`, `adrion_postgres_exporter`

### 3. Synchronization (rsync)
Primary method for code delivery:
```bash
rsync -avz --exclude='.venv' --exclude='__pycache__' --exclude='.git' \
  "/c/Users/adiha/.1_Projekty/<dir>/" \
  root@178.105.59.41:/opt/adrion-system/services/<service>/
```

## Maintenance Commands
- `vps-status`: Check health of all containers.
- `vps-logs`: View consolidated logs.
- `vps-deploy`: Trigger a full stack rebuild and redeploy.

## Backup (G9 Sustainability)
- Local backups are stored in `/opt/adrion-system/backups`.
- S3 Off-site backups (Optional): Bucket `adrion-backups` (G9 compliance).
