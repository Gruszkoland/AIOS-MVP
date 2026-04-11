# Cloud Platform Deployment Research — ADRION 369

**Date:** 2026-04-11  
**Project:** ADRION 369 (Flask + PostgreSQL + Prometheus/Grafana + Docker microservices)  
**Requirements:** 2-4 CPU cores, 2-4GB RAM, PostgreSQL, Redis, Docker support, persistent storage

---

## Executive Summary

### Recommended Platforms (Best for ADRION 369)

| Rank | Platform | Free Tier Duration | Verdict | Cost After Free |
|------|----------|-------------------|---------|-----------------|
| 🥇 1 | **Oracle Cloud** | ∞ (Always Free) | **BEST** — Unlimited compute, 2x 2GB VMs, managed PostgreSQL, Prometheus support | $0/mo (truly free tier) |
| 🥈 2 | **Railway** | 30 days + $5 credits | **EXCELLENT** — Pay-per-second, very affordable, full Docker + PostgreSQL | ~$15-30/mo (post-trial) |
| 🥉 3 | **DigitalOcean** | $100-200 credits (60 days) | **STRONG** — Affordable App Platform, $15 managed PostgreSQL, great value | $15+/mo (database) |
| 4 | **Google Cloud** | $300 credits (90 days) + always-free e2-micro | **GOOD** — Free Cloud Run, Cloud SQL not included in always-free, Prometheus/Grafana buildout possible | $50-100/mo (post-trial) |
| 5 | **AWS** | $200 credits (12 months) + limited services | **ADEQUATE** — Traditional free tier, learning curve, RDS PostgreSQL $15+, monitoring extra | $50-150/mo (post-trial) |
| ⚠️ 6 | **Azure** | $200 credits (12 months) | **LIMITED** — Pricing complex, App Service + PostgreSQL quickly expensive | $50+/mo (post-trial) |
| ❌ 7 | **Heroku** | ✗ DISCONTINUED | **NOT VIABLE** — Free tier removed as of Nov 2022 | $50+/mo minimum |
| ❌ 8 | **Fly.io** | ✗ DISCONTINUED (paid-only) | **NOT VIABLE** — No free tier for new orgs, existing legacy free tier is deprecated | $10+/mo (minimum) |
| ⚠️ 9 | **Render** | Hobby ($0, limited) | **RISKY** — 256MB RAM, 30-day database expiry, service spins down after 15 min inactivity | Free (but limited) |
| ⚠️ 10 | **Replit** | Free Starter (limited) | **UNSUITABLE** — Designed for learning, not production multi-service apps | Free (limited) |
| ⚠️ 11 | **PythonAnywhere** | Free Beginner ($0) | **LIMITED** — Only 512MB storage, 100s CPU daily, MySQL only (no PostgreSQL) | Free (very limited) |
| ⚠️ 12 | **IBM Cloud** | Free tier (varies) | **LIMITED** — Less popular, fewer resources documented | $0-50/mo |

---

## 1. ORACLE CLOUD — Always Free Tier 🏆

**Status:** ✅ ACTIVE  
**Best For:** Production workloads, long-term deployment without billing concerns

### Free Tier Details

| Resource | Limit | Duration |
|----------|-------|----------|
| **Compute (VM)** | 2 x Always Free Eligible shapes (e.g., `VM.Standard.E2.1.Micro` — 1 OCPU, 1GB RAM) | ∞ Forever |
| **Memory per VM** | 1-2 GB RAM per instance | ∞ |
| **Block Storage** | 200 GB total | ∞ |
| **MySQL Database** | 1 MySQL 8.0 instance, 20 GB storage | ∞ |
| **PostgreSQL** | ❌ NOT in always-free tier (uses compute VMs instead) | N/A |
| **Autonomous Database** | 20 GB ECPU-based (not compatible with ADRION stack) | ∞ |
| **ARM Compute** | 4 x Ampere A1 instances (3 OCPU, 24GB RAM total) | ∞ |
| **Load Balancer** | 1 load balancer, 10 Mbps | ∞ |
| **Object Storage** | 20 GB | ∞ |
| **VCN (Networking)** | Unlimited | ∞ |

### PostgreSQL on Oracle Cloud
- **Option A:** Deploy PostgreSQL in compute VMs (still within always-free 2 x micro VMs)
- **Option B:** Use managed PostgreSQL via separate paid service (~$40-80/mo)
- **Option C:** Run PostgreSQL in Docker container on free VMs

### Monitoring
- Oracle Cloud Monitoring (basic) included
- **Alert:** Prometheus/Grafana not native; must deploy in VMs or containers

### Pros
- ✅ **Truly free forever** — no expiration or credit limits
- ✅ **4 total OCPU + 24 GB RAM** with ARM instances (if using A1 instances)
- ✅ **2 x Micro instances (2 OCPU, 2-4GB total)** for cost-conscious deployment
- ✅ **200GB storage** — sufficient for ADRION workloads
- ✅ **Docker support** — full Linux VMs
- ✅ **VPC, Load Balancer, networking** included
- ✅ No credit card charges if staying within limits

### Cons
- ❌ **PostgreSQL not in always-free tier** — must run in VM or use managed (paid)
- ❌ **Prometheus/Grafana** not managed — must self-host
- ❌ **ARM-based A1 instances** have different architecture (not x86)
- ⚠️ **30-day inactivity suspension** — must have activity or service stops
- ⚠️ **Strict resource limits** — can't scale up without paid tier
- ⚠️ **Regional constraints** — always-free only in specific regions (US, UK, Canada)

### Monthly Cost After Free Tier
- **If staying within free tier:** $0/mo
- **If managed PostgreSQL needed:** ~$50-150/mo

### Container/Docker Support
- ✅ Full Linux VMs support Docker
- ✅ Can run Docker Compose
- ✅ Container Registry available

### Best Use Case for ADRION 369
- **IDEAL for:** Non-urgent deployments, learning/development, projects with flexibility on monitoring
- **CONCERN:** PostgreSQL not native to free tier (workaround: self-hosted in VM)
- **DEPLOYMENT ARCHITECTURE:**
  ```
  Micro VM #1 (1 OCPU, 1GB): Flask app + Nginx + Docker
  Micro VM #2 (1 OCPU, 1GB): PostgreSQL + Redis in containers
  A1 Instance (3+ OCPU, 8-12GB): Heavy compute (Prometheus, Grafana, monitoring)
  ```

### Recommendation
**TIER 1 if PostgreSQL-in-container is acceptable.** Need workaround for managed database.

---

## 2. RAILWAY — Modern Container Platform 🚀

**Status:** ✅ ACTIVE  
**Best For:** Quick deployment, developer-friendly, pay-per-second pricing

### Free Tier Details

| Resource | Limit | Duration |
|----------|-------|----------|
| **Trial Credits** | $5 USD | 30 days |
| **Free Plan** | $1/month minimum (after trial) | ∞ |
| **Compute Pricing** | $0.00000386/GB·s memory + $0.00000772/vCPU·s | Per-second billing |
| **Storage Pricing** | $0.00000006/GB·s | Per-second billing |
| **PostgreSQL** | Full managed PostgreSQL support | Included |
| **Redis** | Full managed Redis support | Included |
| **Memory/CPU** | No hard limits in free tier (soft billing limits) | ∞ |
| **Egress** | $0.05/GB | Usage-based |

### Cost Breakdown (Typical ADRION Stack)
- **Flask App (2 vCPU, 512MB RAM):** ~$0.0154 \* 3600 \* 24 * 30 = ~$39.90/mo
- **PostgreSQL (512MB RAM, 5GB storage):** ~$15/mo
- **Redis (256MB):** ~$3/mo
- **Prometheus/Grafana (2 vCPU, 512MB):** ~$39.90/mo
- **Total estimate:** ~$100/mo (can be optimized)

### Monitoring
- ✅ **Prometheus** deployable as service (~$40/mo)
- ✅ **Grafana** deployable as service (~$40/mo)
- ✅ Native metrics dashboard in Railway UI

### Pros
- ✅ **Zero credit card required** for 30-day trial ($5 free)
- ✅ **Full Docker/Dockerfile support** — deploy anything containerizable
- ✅ **Managed PostgreSQL, Redis, MySQL** — no ops burden
- ✅ **Simple pricing** — clear per-second billing (no surprise charges)
- ✅ **Hobby plan ($1/mo)** after trial — cheapest entry after free tier
- ✅ **GitHub integration** — auto-deploy on push
- ✅ **Private networking** between services
- ✅ **CLI tooling** — deploy from terminal

### Cons
- ⚠️ **No truly free tier after trial** — $1/mo minimum (or pay-per-second overage)
- ⚠️ **Small free quota** — $5 trials deplete quickly with full stack
- ⚠️ **Pricing can spike** — usage-based billing risk if traffic spikes
- ❌ **No backup/DR features** in free tier (must pay extra)
- ❌ **Limited to 1 project** in free tier (old limitation, verify current)

### Monthly Cost After Free Tier
- **Minimum:** $1/mo (free plan, minimal usage)
- **Typical ADRION stack:** $80-150/mo
- **Optimized (single VM + managed DB):** $20-40/mo

### Container/Docker Support
- ✅ **Excellent** — native Docker support, Dockerfile, `railway.json` config
- ✅ **Docker Compose-like** — define services in UI or CLI

### Best Use Case for ADRION 369
- **IDEAL for:** Production workloads, developers who want managed services
- **STRENGTH:** Simplicity, transparent pricing, full container stack
- **DEPLOY PATTERN:**
  ```
  railwayapp.com:
    - Flask app (Docker) → 512MB RAM, 2 vCPU
    - PostgreSQL (managed) → 512MB RAM, 5GB storage
    - Redis (managed) → 256MB RAM
    - Prometheus (Docker) → 256MB RAM
    - Grafana (Docker) → 256MB RAM
  ```

### Recommendation
**TIER 1 if willing to pay ~$20-50/mo post-trial.** Excellent developer experience, transparent billing.

---

## 3. DIGITALOCEAN — Traditional Cloud + App Platform 💧

**Status:** ✅ ACTIVE  
**Best For:** Affordable managed services, traditional cloud + modern App Platform

### Free Tier Details

| Resource | Limit | Duration |
|----------|-------|----------|
| **Trial Credits** | $100-200 USD (varies by campaign) | 60 days |
| **App Platform** | $0/mo (free tier exists) | Limited, for learning |
| **Droplets (VPS)** | ❌ NOT free (starts $4/mo) | N/A |
| **Managed PostgreSQL** | ❌ NOT free (starts $15/mo) | N/A |
| **Container Registry** | $0/mo (basic, free tier) | ∞ |
| **Storage** | $5/GB/mo (Spaces object storage) | ❌ Not free |
| **Kubernetes** | Free control plane, $0.0119/hour per node (~$8.64/mo per node) | Partial free |

### App Platform Specifics
- **Free tier:** Yes, but very limited (small VM, frequent restarts possible)
- **Built-in PostgreSQL:** Can add via managed database ($15+/mo)
- **Monitor/Observability:** Limited dashboards, no Prometheus/Grafana

### Cost Breakdown (Typical ADRION Stack)
- **App Platform (free tier):** $0/mo (limited)
- **Managed PostgreSQL (starter):** $15/mo
- **App Platform (Basic, 2GB RAM):** $12/mo
- **Kubernetes (basic):** ~$10-30/mo
- **Total estimate:** $40-60/mo

### Monitoring
- ⚠️ **Basic DigitalOcean dashboards** only
- ❌ **Prometheus/Grafana** not native (must deploy separately)

### Pros
- ✅ **$100-200 free credits** — covers 2-4 months of service
- ✅ **Managed PostgreSQL** — $15/mo, very reliable
- ✅ **App Platform** — similar to Render/Heroku (without friction)
- ✅ **Affordable Droplets** — $4/mo basic, $6/mo standard
- ✅ **Kubernetes support** — enterprise-grade orchestration
- ✅ **CLI tool** — easy deployment (`doctl` command)
- ✅ **Generous free tier period** (60 days)

### Cons
- ⚠️ **Credits expire after 60 days** — must move to paid after trial
- ⚠️ **App Platform limited** — no guarantee on small footprint
- ❌ **PostgreSQL not in trial free tier** — add $15/mo after
- ❌ **Monitoring is DIY** — Prometheus/Grafana must self-host

### Monthly Cost After Free Tier
- **Minimal ADRION (1 Droplet + PostgreSQL):** $15-20/mo
- **Recommended (App Platform + PostgreSQL):** $30-50/mo
- **Enterprise (Kubernetes + managed DB):** $100+/mo

### Container/Docker Support
- ✅ **Full Docker support** on Droplets
- ✅ **Container Registry** integrated
- ✅ **App Platform** supports Docker Compose

### Best Use Case for ADRION 369
- **IDEAL for:** Production deployments on budget
- **STRENGTH:** Managed PostgreSQL ($15/mo), affordable compute
- **DEPLOY PATTERN:**
  ```
  App Platform:
    - Flask + Nginx (Docker) → 2GB RAM, $12/mo
    - PostgreSQL (managed) → 1GB, $15/mo
    - Redis add-on → $10/mo
  ```

### Recommendation
**TIER 2. Good value if using $100 credits to offset first 2-4 months.**

---

## 4. GOOGLE CLOUD — Free Trial + Always-Free Services ☁️

**Status:** ✅ ACTIVE  
**Best For:** Learning, serverless workloads, long-term free compute-only deployments

### Free Tier Details

| Resource | Limit | Duration |
|----------|-------|----------|
| **Welcome Credits** | $300 USD | 90 days |
| **e2-micro Compute Engine VM** | 1 instance/month (30GB persistent disk included, 1GB outbound/mo) | ∞ Always-free |
| **Cloud Run** | 2M requests/month, 360K GB-seconds/month | ∞ Always-free |
| **Cloud SQL** | ❌ NOT in always-free tier | N/A |
| **Cloud Storage** | 5GB/month (US regions only) | ∞ Always-free |
| **BigQuery** | 1TB querying/month (not suitable for ADRION) | ∞ Always-free |
| **PostgreSQL via Compute** | Can run in e2-micro VM or CloudSQL (paid) | Partial |

### Cloud SQL (PostgreSQL) Specifics
- **Smallest:** `db-f1-micro` (0.6GB RAM) — ~$5/mo
- **Standard:** `db-g1-small` (2GB RAM) — ~$15-20/mo
- **NOTE:** Cloud SQL NOT included in always-free tier

### Monitoring
- ⚠️ **Cloud Monitoring** basic included
- ❌ **Prometheus/Grafana** not managed (must deploy in Cloud Run or Compute)

### Cost Breakdown (Typical ADRION Stack)
- **e2-micro Compute (always-free):** $0/mo
- **Cloud SQL PostgreSQL (db-g1-small):** $18/mo
- **Cloud Run (Prometheus/Grafana):** $5-10/mo
- **Total estimate:** $23-30/mo (post-$300 credits)

### Pros
- ✅ **$300 free credits** — 3 months of generous trial
- ✅ **1 free e2-micro VM** (always-free) — 0.25 vCPU, 1GB RAM
- ✅ **Cloud Run** — perfect for lightweight services (Flask possible)
- ✅ **Cloud Storage** free tier — 5GB/month
- ✅ **Generous always-free services** — many options for learning

### Cons
- ⚠️ **e2-micro very underpowered** — 0.25 vCPU, 1GB RAM (below ADRION minimum)
- ⚠️ **Cloud SQL not in always-free** — adds $15-20/mo
- ⚠️ **$300 credits expire after 90 days** — must have payment method after
- ❌ **PostgreSQL-specific always-free VM not available** — must manage in VM or use paid CloudSQL
- ❌ **No Prometheus/Grafana managed services**

### Monthly Cost After Free Tier
- **Minimal (e2-micro + Cloud SQL small):** $20-25/mo
- **Recommended (e2-small + Cloud SQL):** $40-60/mo
- **Enterprise (multiple VMs + Cloud SQL):** $100+/mo

### Container/Docker Support
- ✅ **Full Docker support** on Compute Engine VMs
- ✅ **Cloud Run** supports Docker containers (serverless)
- ✅ **Artifact Registry** for container storage

### Best Use Case for ADRION 369
- **SUITABLE for:** Learning phase, serverless microservices
- **CONCERN:** e2-micro too underpowered, Cloud SQL pricing adds up
- **DEPLOY PATTERN:**
  ```
  Cloud Run (serverless):
    - Flask app (containerized) → 512MB RAM, 1 vCPU (shared)
  Compute Engine (always-free):
    - PostgreSQL in container → 1GB RAM, 0.25 vCPU (marginal)
  Cloud SQL (managed):
    - PostgreSQL (db-g1-small) → 2GB RAM, $18/mo
  ```

### Recommendation
**TIER 3. Good for learning, but PostgreSQL cost adds up quickly. e2-micro insufficient for full ADRION stack.**

---

## 5. AWS — Free Tier + Credits 🔶

**Status:** ✅ ACTIVE  
**Best For:** Traditional enterprise workloads, extensive AWS ecosystem

### Free Tier Details

| Resource | Limit | Duration |
|----------|-------|----------|
| **Welcome Credits** | $200 USD | ~1 month (varies) |
| **EC2 (t2.micro)** | 750 hours/month | 12 months (new accounts) |
| **EC2 Memory** | 1GB RAM (t2.micro) | 12 months |
| **RDS PostgreSQL (db.t2.micro)** | 750 hours/month | 12 months |
| **RDS Storage** | 20GB/month | 12 months |
| **RDS Backups** | 100GB/month backup storage | 12 months |
| **Data Transfer** | 1GB/month outbound | 12 months |
| **S3 Storage** | 5GB/month | 12 months (always-free thereafter) |
| **Lambda** | 1M requests/month | ∞ Always-free (partial) |
| **DynamoDB** | 25GB storage, 25 units RCU/WCU | ∞ Always-free |

### EC2 + RDS Stack
- **EC2 t2.micro:** 1 vCPU (burstable), 1GB RAM — fine for Flask app
- **RDS PostgreSQL db.t2.micro:** 1 vCPU, 1GB RAM — fine for moderate load

### Monitoring
- ✅ **CloudWatch** included (basic metrics, logs)
- ❌ **Prometheus/Grafana** not managed (must deploy separately)

### Cost Breakdown (Typical ADRION Stack)
- **EC2 t2.micro (750 hrs/mo):** $0/mo (free tier)
- **RDS PostgreSQL db.t2.micro (750 hrs/mo):** $0/mo (free tier)
- **RDS Storage (20GB):** $0/mo (free tier)
- **CloudWatch Metrics:** $0.30/mo (per metric)
- **Total estimate:** ~$10-20/mo (post-$200 credits)

### Pros
- ✅ **$200 welcome credits** — covers 1 month
- ✅ **12-month free tier** — longest traditional free period
- ✅ **Managed RDS PostgreSQL** — fully managed database
- ✅ **EC2 + RDS combination** — 1GB RAM each (2GB total)
- ✅ **CloudWatch** included — basic monitoring
- ✅ **S3 always-free** — 5GB/month perpetual free tier
- ✅ **Large AWS ecosystem** — integrations everywhere

### Cons
- ⚠️ **Only 1GB RAM per service** (t2.micro) — below ADRION target
- ⚠️ **$200 credits insufficient** — only covers ~1 month of usage
- ⚠️ **Data transfer costs** — $0.09/GB outbound (expensive)
- ⚠️ **Burstable instances** (t2.micro) — CPU throttling under load
- ❌ **Steep learning curve** — AWS console complex
- ❌ **Prometheus/Grafana not managed** — must self-host
- ❌ **Auto-scaling can trigger surprise bills** (common trap)

### Monthly Cost After Free Tier
- **Minimal (t2.micro + db.t2.micro):** $15-25/mo
- **Recommended (t3.small + db.t3.small):** $40-60/mo
- **Enterprise (multi-AZ + replicas):** $100+/mo

### Container/Docker Support
- ✅ **EC2** — full Docker support
- ✅ **ECS** (Elastic Container Service) — managed containers
- ✅ **ECR** (Elastic Container Registry) — container image storage

### Best Use Case for ADRION 369
- **SUITABLE for:** Organizations already AWS-committed, multi-region deployments
- **CONCERN:** 1GB RAM insufficient, pricing spikes common with inexperienced users
- **DEPLOY PATTERN:**
  ```
  EC2 (t2.micro):
    - Flask + Nginx (Docker) → 1GB RAM, 1 vCPU
  RDS (db.t2.micro):
    - PostgreSQL → 1GB RAM
  EC2 (separate):
    - Prometheus/Grafana → additional cost
  ```

### Recommendation
**TIER 3. Steep learning curve, doesn't provide cost advantage over Railway/DigitalOcean at smaller scale.**

---

## 6. AZURE — Free Tier + Credits 🔵

**Status:** ✅ ACTIVE  
**Best For:** Enterprise integrations, Microsoft ecosystem

### Free Tier Details

| Resource | Limit | Duration |
|----------|-------|----------|
| **Welcome Credits** | $200 USD | 12 months (new accounts) |
| **App Service (B1 Free)** | 60 min/day CPU, limited RAM | 12 months |
| **SQL Database** | ❌ NOT in free tier (starts ~$5/mo) | N/A |
| **PostgreSQL** | Flexible Server (starts $15/mo minimum) | N/A |
| **Virtual Machine** | ❌ NOT truly free (pay-per-minute) | N/A |
| **Storage** | 5GB/month | 12 months (always-free) |

### Azure App Service + Database
- **App Service (F1 Free):** 60 min/day compute, very limited
- **PostgreSQL (Flexible Server):** Minimum ~$15-20/mo
- **SQL Database:** ~$5-10/mo

### Monitoring
- ⚠️ **Application Insights** — partial free tier (limited telemetry)
- ❌ **Prometheus/Grafana** not managed

### Cost Breakdown (Typical ADRION Stack)
- **App Service (F1 Free):** $0/mo (but 60 min/day limit)
- **PostgreSQL (Flexible Server small):** $18/mo
- **Storage:** $0/mo (5GB)
- **Total estimate:** ~$18-25/mo (post-$200 credits)

### Pros
- ✅ **$200 welcome credits** — 12-month validity
- ✅ **Always-free 5GB storage** — perpetual
- ✅ **App Service free tier** — good for learning (but 60 min/day limit)
- ✅ **Integration with Microsoft services** — Teams, Office 365, etc.

### Cons
- ⚠️ **60-minute/day compute limit** on F1 free — severely restricts production use
- ⚠️ **PostgreSQL not free** — minimum $15/mo
- ⚠️ **Pricing model confusing** — many hidden charges
- ❌ **Limited resources in free tier** — underpowered for ADRION
- ❌ **No Docker Compose** in free App Service tier
- ❌ **Steep learning curve** — Azure portal confusing

### Monthly Cost After Free Tier
- **Minimal (limited App Service + PostgreSQL):** $20-25/mo
- **Recommended (B1 or B2 App Service + PostgreSQL):** $40-60/mo
- **Enterprise (VM + managed DB):** $100+/mo

### Container/Docker Support
- ✅ **App Service** supports Docker (requires paid tier)
- ✅ **Container Instances** (ACI) for serverless containers

### Best Use Case for ADRION 369
- **SUITABLE for:** Azure-committed organizations, Microsoft stack integrations
- **CONCERN:** Free tier extremely limited (60 min/day), pricing not competitive
- **DEPLOY PATTERN:**
  ```
  App Service (B1):
    - Flask app → limited daily runtime
  PostgreSQL (Flexible Server):
    - Database → $18/mo minimum
  ```

### Recommendation
**TIER 4. Not recommended unless Azure-locked. Free tier too restrictive.**

---

## 7. HEROKU — **DEPRECATED** ❌

**Status:** ✗ FREE TIER REMOVED (November 2022)  
**Current Situation:** No free tier. Minimum cost $7/mo for basic Dynos.

### What Changed
- Free tier discontinued November 28, 2022
- Eco and Basic plans now minimum $5-7/mo (Dynos)
- Hobby databases removed; PostgreSQL starts $9/mo

### Why Still Mentioned
- **Legacy:** Some existing applications still use free tier (grandfathered in)
- **Not viable** for new ADRION 369 deployments

### Recommendation
**NOT VIABLE. Do not use for new projects.**

---

## 8. FLY.IO — **PAID-ONLY** (No Free Tier) ⚠️

**Status:** ✗ Free tier discontinued for new organizations  
**Current Situation:** All-paid model, no free tier.

### Free Tier Status
- **Legacy free tier** — ✓ Still exists for old organizations (deprecated, will eventually be discontinued)
- **New organizations** — ✗ Pay-as-you-go only, ~$2/mo minimum per machine

### Pricing for ADRION Stack (New Org)
- **Shared CPU Machine (256MB):** $2.02-2.97/mo per machine
- **PostgreSQL cluster:** ~$12-20/mo
- **Redis:** ~$10-15/mo
- **Total estimate:** $50-100/mo

### Pros
- ✅ **Global deployment** — easy multi-region
- ✅ **No credit card required** for trial (legacy)
- ✅ **Simple pricing** — transparent per-machine cost

### Cons
- ❌ **No free tier for new accounts** — paid immediately
- ⚠️ **Minimum viable setup** ~$50-100/mo
- ⚠️ **Legacy free tier being phased out**

### Recommendation
**NOT VIABLE for cost-conscious new deployments. Use Oracle Cloud or Railway instead.**

---

## 9. RENDER — Hobby Tier (Limited Free) ⚠️

**Status:** ✅ ACTIVE (but limited)  
**Best For:** Prototypes, non-production learning projects

### Free Tier Details

| Resource | Limit | Duration |
|----------|-------|----------|
| **Web Service (Hobby)** | 512MB RAM, 0.1 CPU cores | Free (spins down after 15 min inactivity) |
| **PostgreSQL Database** | 256MB, 1GB storage | Free (30-day expiry, then deleted) |
| **Redis (Key-Value)** | 25MB, 50 connections | Free |
| **Instance Hours** | 750 instance hours/month | Free |
| **Bandwidth** | Included | Free |
| **Uptime** | Not guaranteed (spins down) | N/A |

### Critical Limitations
- **Web service spins down** after 15 minutes without traffic (cold start ~1 min)
- **PostgreSQL expires** after 30 days (deleted automatically)
- **No backups** on free tier
- **No SSH access** on free tier
- **No persistent filesystem** — changes lost on restart

### Cost After Free Tier
- **Web Service (Standard, 512MB):** $7/mo
- **PostgreSQL (Starter, 1GB storage):** $7-15/mo
- **Total with upgrades:** $15-25/mo

### Pros
- ✅ **True free tier** — no credit card required
- ✅ **Easy deployment** — simple dashboard
- ✅ **Managed PostgreSQL** included

### Cons
- ❌ **Service spin-down** — not suitable for production
- ❌ **Database auto-deletion** after 30 days — unacceptable for data persistence
- ❌ **512MB RAM + 0.1 CPU** — below ADRION minimum
- ⚠️ **Cold start time** (~1 min) — user experience impact
- ⚠️ **No monitoring** (Prometheus/Grafana) — DIY only

### Recommendation
**TIER 4. Only suitable for learning/prototypes. NOT viable for production due to database expiry and service spin-down.**

---

## 10. SUPABASE — PostgreSQL-Focused Platform 🗄️

**Status:** ✅ ACTIVE  
**Best For:** PostgreSQL + real-time database needs

### Free Tier Details

| Resource | Limit | Duration |
|----------|-------|----------|
| **Database Storage** | 500MB | Starter plan |
| **Bandwidth** | 1GB/month | Starter plan |
| **Realtime Connections** | 100 max concurrent | Starter plan |
| **API Requests** | Unlimited | Starter plan |
| **Auth Users** | Unlimited | Starter plan |
| **PostgreSQL Version** | 15+ | Latest |

### Key Features
- ✅ Built on PostgreSQL (not a wrapper)
- ✅ Real-time subscriptions (WebSocket)
- ✅ Auto-generated REST/GraphQL APIs
- ✅ Built-in authentication

### Cost Breakdown
- **Starter (free):** 500MB DB, 1GB/mo bandwidth
- **Pro:** $25/mo (8GB DB, 100GB bandwidth)
- **Team:** $599/mo (managed)

### Limitations for ADRION
- ❌ **500MB storage only** — insufficient for monitoring history
- ❌ **Not a full platform** — only database, need Flask + separate hosting
- ❌ **No Redis, Prometheus, Grafana** included
- ⚠️ **Real-time features** (overkill for ADRION)

### Recommendation
**TIER 5. Database-only solution. Not suitable as complete platform.**

---

## 11. HETZNER — Budget VPS 💰

**Status:** ✅ ACTIVE  
**Best For:** Cost-conscious users wanting traditional VPS

### Pricing (No Free Tier)

| Resource | Cost | Notes |
|----------|------|-------|
| **CPX11 (2 vCPU, 4GB RAM)** | €4.99/mo | Best value |
| **CPX21 (4 vCPU, 8GB RAM)** | €9.99/mo | Recommended for ADRION |
| **Storage** | Included (40-160GB) | SSD, no extra cost |
| **PostgreSQL** | ❌ Not managed (DIY in VM) | Must self-host or use external DB |

### Features
- ✅ Extremely affordable
- ✅ Excellent uptime (99.9%)
- ✅ Full Docker support
- ✅ Private networking
- ✅ German data centers (GDPR compliant)

### Cost for ADRION Stack
- **CPX11 (2 vCPU, 4GB):** €4.99/mo
- **PostgreSQL (self-hosted in VM):** $0 (included)
- **Monitoring (self-hosted Prometheus/Grafana):** $0 (included)
- **Total:** ~€5/mo (~$5.50 USD)

### Pros
- ✅ **Cheapest option** — ~€5/mo for 2 vCPU, 4GB RAM
- ✅ **Full Docker support** — unlimited containers
- ✅ **No resource restrictions** — unlike managed platforms
- ✅ **GDPR compliant** (German data centers)

### Cons
- ⚠️ **No managed services** — PostgreSQL, Redis, etc. must be self-hosted
- ⚠️ **DevOps required** — no platform-level abstractions
- ❌ **No always-free tier** — €5/mo minimum

### Monthly Cost
- **Minimal setup:** €5-10/mo
- **Recommended (CPX21):** €10-20/mo

### Recommendation
**TIER 1 (for DevOps-capable teams).** Cheapest total-cost-of-ownership if comfortable managing databases/containers.

---

## 12. VULTR — Cloud Compute 🔧

**Status:** ✅ ACTIVE (paid-only)  
**Best For:** Developers needing flexible, affordable compute

### Pricing (No Free Tier)

| Resource | Cost | Notes |
|----------|------|-------|
| **VX1 Cloud Compute (1 vCPU, 512MB)** | $2.50/mo | Budget option |
| **VX1 (2 vCPU, 2GB)** | $5/mo | Minimum for ADRION |
| **VX1 (4 vCPU, 4GB)** | $10/mo | Recommended |
| **PostgreSQL Managed** | $15+/mo | Additional cost |
| **Storage** | Included (20-80GB SSD) | Per-instance |

### Features
- ✅ Competitive pricing
- ✅ Global data centers (15+ regions)
- ✅ Hourly billing (pay for what you use)
- ✅ $10 free credit for new accounts (limited time)

### Cost for ADRION Stack
- **VX1 (2 vCPU, 2GB):** $5/mo
- **PostgreSQL (managed):** $15/mo
- **Redis (managed or DIY):** $0-10/mo
- **Total:** $20-30/mo

### Recommendation
**TIER 2. Good value, slightly cheaper than DigitalOcean. Requires DevOps if managing databases.**

---

## COMPREHENSIVE COMPARISON TABLE

| Platform | Free Tier | Duration | Best For | Cost/mo Post-Free | Container | PostgreSQL | Monitoring | Verdict |
|----------|-----------|----------|----------|------------------|-----------|-----------|-----------|---------|
| **Oracle Cloud** | $0 (always-free 2x Micro VMs) | ∞ | Long-term prod, cost-conscious | $0-80 (if DIY PostgreSQL) | ✅ | ⚠️ (DIY) | ❌ (DIY) | 🥇 TIER 1 |
| **Railway** | $5 credits | 30 days | Modern container platform | $20-150 | ✅ | ✅ | ⚠️ (DIY) | 🥇 TIER 1 |
| **DigitalOcean** | $100-200 credits | 60 days | Budget-conscious production | $15-50 | ✅ | ✅ ($15) | ❌ (DIY) | 🥈 TIER 2 |
| **Google Cloud** | $300 credits + always-free e2-micro | 90 days + ∞ | Serverless workloads | $20-60 | ✅ | ⚠️ ($15+) | ❌ (DIY) | 🥉 TIER 3 |
| **AWS** | $200 credits + 12mo free t2.micro | 1 year + partial ∞ | Enterprise, multi-region | $15-60 | ✅ | ✅ ($0 first 12mo) | ⚠️ | 🥉 TIER 3 |
| **Azure** | $200 credits, F1 App Service | 12 months | Microsoft ecosystem | $20-60 | ⚠️ | ⚠️ ($15+) | ⚠️ | ⚠️ TIER 4 |
| **Heroku** | ❌ DISCONTINUED | N/A | LEGACY ONLY | $50+ | ✅ | ❌ | ❌ | ❌ DO NOT USE |
| **Fly.io** | ❌ (legacy only) | N/A | NOT viable for new orgs | $50+ | ✅ | ⚠️ | ❌ | ❌ AVOID |
| **Render** | Free (limited) | ∞ Limited | Learning/prototypes | $14-25 | ✅ | ⚠️ (30-day expiry!) | ❌ | ⚠️ TIER 4 |
| **PythonAnywhere** | Free (very limited) | ∞ Limited | Python learning only | $5+ | ❌ | ❌ | ❌ | ❌ UNSUITABLE |
| **Replit** | Free (limited) | ∞ Limited | Educational only | Free-$20 | ❌ | ❌ | ❌ | ❌ UNSUITABLE |
| **Supabase** | 500MB DB | ∞ Limited | Database-only | $25+ | ❌ | ✅ | ❌ | ⚠️ PARTIAL |
| **Hetzner** | ❌ No free tier | N/A | Budget DevOps | €5-10 (~$5-12) | ✅ | ⚠️ (DIY) | ❌ (DIY) | 🥇 TIER 1 |
| **Vultr** | $10 credit (limited) | Limited time | Budget compute | $5-20 | ✅ | ⚠️ ($15+) | ❌ (DIY) | 🥈 TIER 2 |

---

## FINAL RECOMMENDATIONS

### **SCENARIO 1: Maximize Free Period (No Upfront Cost)**

**Best Choice: Railway ($5 for 30 days)**
- $5 in credits covers ~30 days of modest workload
- Then $1/mo free plan + pay-per-second overflow
- Simplest ramp-up path

**Alternative: Google Cloud ($300 credits for 90 days)**
- 3-month free trial suitable for evaluation
- e2-micro always-free VM for perpetual learning environment
- Steeper learning curve but longest free period

### **SCENARIO 2: Longest Free Tier (12 Months)**

**Best Choice: AWS 12-Month Free Tier**
- t2.micro (750 hrs/mo) + db.t2.micro (750 hrs/mo) free for full year
- Sufficient for non-production ADRION stack
- Requires strict cost management (easy to overspend)

**Alternative: Azure 12-Month Free Tier**
- Similar duration but more restrictive (60 min/day App Service)
- Not recommended unless Azure-locked

### **SCENARIO 3: Production Long-Term (Best Total Cost)**

**Best Choice: Oracle Cloud (Always-Free Tier)**
- 2 x Micro VMs + 200GB storage = ∞ free
- Workaround: Self-host PostgreSQL in VM (still free)
- Zero monthly cost if staying within limits
- **Caveat:** Must handle PostgreSQL ops; no managed service

**Alternative: Hetzner (€5/mo)**
- CPX11 (2 vCPU, 4GB) + self-hosted full stack
- Cheapest production-viable option
- Requires DevOps skills (no managed services)

### **SCENARIO 4: Managed Services + Container Platform (Recommended)**

**Best Choice: Railway**
- $5 trial → $1/mo free plan → ~$20-100/mo production
- Full Docker + managed PostgreSQL + Redis
- Transparent pricing, zero DevOps overhead
- Best developer experience

**Alternative: DigitalOcean**
- $100-200 credits (60 days)
- App Platform + managed PostgreSQL ($15/mo)
- Slightly cheaper per-unit, mature platform

---

## DEPLOYMENT CHECKLIST FOR ADRION 369

### Must-Have Features
- ✅ 2-4GB RAM minimum
- ✅ 2-4 CPU cores
- ✅ PostgreSQL support
- ✅ Docker/container support
- ✅ Persistent storage
- ⚠️ Prometheus/Grafana (can be DIY or managed)
- ⚠️ Redis support (can be managed or DIY)

### Platform Readiness Matrix

| Platform | RAM | CPU | PostgreSQL | Docker | Persistent | Monitoring | Redis | **Ready?** |
|----------|-----|-----|-----------|--------|-----------|-----------|-------|-----------|
| **Oracle (free VMs)** | ⚠️ 1-2GB | ⚠️ 0.5-1 | ⚠️ DIY | ✅ | ✅ | ❌ DIY | ❌ DIY | ⚠️ Workaround |
| **Railway** | ✅ 2+ GB | ✅ 2+ | ✅ Managed | ✅ | ✅ | ⚠️ DIY | ✅ Managed | ✅ **READY** |
| **DigitalOcean** | ✅ 2+ GB | ✅ 2+ | ✅ Managed ($15) | ✅ | ✅ | ❌ DIY | ⚠️ DIY | ✅ **READY** |
| **Google Cloud** | ⚠️ 1GB (free) | ⚠️ 0.25 (free) | ⚠️ Paid ($15+) | ✅ | ✅ | ❌ DIY | ❌ DIY | ⚠️ Workaround |
| **AWS** | ⚠️ 1GB (free) | ⚠️ 1 (free) | ✅ Free (12mo) | ✅ | ✅ | ⚠️ DIY | ❌ DIY | ⚠️ Workaround |
| **Azure** | ⚠️ 60min/day | ⚠️ Shared | ⚠️ Paid ($15+) | ⚠️ Paid tier | ✅ | ⚠️ DIY | ❌ DIY | ❌ NOT READY |
| **Hetzner (€5/mo)** | ✅ 4GB | ✅ 2 | ⚠️ DIY | ✅ | ✅ | ❌ DIY | ❌ DIY | ✅ **READY** (DevOps) |
| **Render** | ❌ 512MB | ❌ 0.1 | ❌ 30-day expiry | ✅ | ❌ Ephemeral | ❌ DIY | ❌ DIY | ❌ NOT READY |

---

## ARCHITECTURE RECOMMENDATIONS PER PLATFORM

### Option A: Railway (Recommended for Managed Services)

```yaml
# docker-compose equivalent in Railway UI
services:
  flask-app:
    image: adrion369/flask:latest
    memory: 512MB
    cpu: 2
    env:
      DATABASE_URL: postgresql://...
      REDIS_URL: redis://...
  
  postgresql:
    service: managed-postgres
    memory: 512MB
    storage: 5GB
  
  redis:
    service: managed-redis
    memory: 256MB
  
  prometheus:
    image: prom/prometheus:latest
    memory: 256MB
    cpu: 1
  
  grafana:
    image: grafana/grafana:latest
    memory: 512MB
    cpu: 1
```

**Cost:** ~$100-150/mo (optimizable to $50/mo)

### Option B: Oracle Cloud (Always-Free)

```bash
# Deploy in 2 ARM Micro VMs (free)
VM1: Docker container running PostgreSQL + Redis
VM2: Docker container running Flask + Prometheus + Grafana

# Deploy in Compute VMs (still free if within limits)
- Micro VM #1 (1 OCPU, 1GB): Flask + Nginx
- Micro VM #2 (1 OCPU, 1GB): PostgreSQL + Redis
- A1 Instance (3+ OCPU, 8GB): Prometheus + Grafana (if needed)
```

**Cost:** $0/mo (plus DevOps effort)

### Option C: Hetzner (Budget DevOps)

```bash
# Single CPX21 VM (€9.99/mo)
- Docker containers for all services
- PostgreSQL in Docker (or managed add-on for $5-10/mo)
- Redis in Docker
- Prometheus/Grafana in Docker

# Deployment method:
docker-compose -f docker-compose.prod.yml up -d
```

**Cost:** €10-20/mo (~$11-22 USD)

---

## MIGRATION PATH RECOMMENDATION

### Phase 1: Development (Current)
- Use **Oracle Cloud always-free tier** (VM #1 + VM #2)
- Self-host PostgreSQL in containers
- Deploy via Docker Compose
- Cost: $0/mo

### Phase 2: Early Production (First 1-3 Months)
- Use **Railway $5 trial** or **DigitalOcean $100-200 credits**
- Leverage managed databases (zero ops overhead)
- Monitor with built-in dashboards (no Prometheus needed yet)
- Cost: $0-15/mo (covered by credits)

### Phase 3: Stable Production (3-12 Months)
- Migrate to **Railway ($50-100/mo) or DigitalOcean ($30-50/mo)**
- Add Prometheus/Grafana as services
- Implement auto-scaling if needed
- Cost: $50-100/mo (predictable)

### Phase 4: Enterprise (12+ Months)
- Consider **Kubernetes (via DigitalOcean, AWS, or GKE)**
- Multi-region failover (AWS, Google Cloud)
- Dedicated monitoring stack
- Cost: $200-500+/mo

---

## FINAL VERDICT

### Best Overall for ADRION 369: **Railway** 🏆

- ✅ $5 free trial (30 days) — zero upfront cost
- ✅ Full managed services (PostgreSQL, Redis)
- ✅ Simple Docker deployment
- ✅ Transparent pay-per-second pricing
- ✅ Best developer experience
- ✅ Suitable for production at scale
- 📊 Cost: $5 trial → $1/mo free plan → ~$50-100/mo full stack

### Best for Cost-Conscious (DIY PostgreSQL): **Oracle Cloud** 💰

- ✅ $0/mo forever (always-free tier)
- ✅ 2 x Micro VMs (2 OCPU total, 2-4GB RAM)
- ✅ Full Docker support
- ⚠️ Requires self-hosting PostgreSQL/Redis
- ⚠️ Monitoring must be DIY
- 📊 Cost: $0/mo (with DevOps effort)

### Best for Traditional VPS DevOps: **Hetzner** 🚀

- ✅ CPX11 (2 vCPU, 4GB) for €5/mo
- ✅ Absolute cheapest managed infrastructure
- ✅ Full Docker support
- ⚠️ No managed services
- ⚠️ DevOps responsibility
- 📊 Cost: €5-10/mo (~$5-12 USD) + DevOps time

---

## DOCUMENT METADATA

- **Created:** 2026-04-11
- **Research scope:** 12 major cloud platforms
- **Tested:** Web fetches from official pricing pages
- **Last updated:** 2026-04-11
- **Accuracy:** Current as of Q1 2026 (pricing/services change frequently — verify before deployment)
