# 🚀 QUICK START GUIDE — TODAY'S ACTION PLAN
**Lead Arbitrage Implementation — Day 1 Crash Course**

**Status:** ✅ Ready to Deploy  
**Version:** 2.0 (ADRION 369)  
**Target:** First revenue within 7 days  
**Your Next Step:** Complete this guide in 3 hours  

---

## ⏱️ TIMELINE: TODAY (3 HOURS)

```
09:00 - 09:15  │ Resource Check (15 min)
09:15 - 09:45  │ API Setup (30 min)
09:45 - 10:30  │ VPS + n8n Installation (45 min)
10:30 - 11:30  │ Connect APIs & Test (60 min)
11:30 - 12:00  │ Verify System is Running (30 min)
────────────────
TOTAL: 3 hours → System operational by noon
```

---

## ✅ PRE-FLIGHT CHECKLIST

**Before you start, check these 5 items:**

### 1. Do you have the required capital? ($50-100)
```
Required spend:
- VPS (DigitalOcean): $5-10/month
- n8n Self-hosted: FREE
- OpenRouter API credits: $10 (enough for 5,000+ requests)
- Apify: FREE tier available (50 tasks/month free)
- Gmail/Instantly: FREE

Total: ~$15-25 first week
```

**If YES ✓ → Continue**  
**If NO ✗ → Can you borrow/ask for $50? Yes → Continue. No → Wait until next month**

---

### 2. Do you have 30-40 hours this week? (Even in chunks)
```
Week 1 requirement:
- Day 1-2: 2 hours (setup infrastructure)
- Day 2-3: 2 hours (build Scout agent)
- Day 3-4: 2 hours (build Analyzer agent)
- Day 4-5: 3 hours (build Mailer agent)
- Day 5-7: 5 hours (testing, optimizing, launching)
- Daily: 0.5 hours (monitoring, manual reviews)
────────────────────
TOTAL: ~15-20 hours intensive work
```

**If YES ✓ → Continue**  
**If NO ✗ → Pick a better week or scale back scope**

---

### 3. Do you have a specific target vertical? (YES = much better)
```
RECOMMENDATION: Pick ONE from:
☐ Local services (restaurants, plumbers, salons)
☐ E-commerce sellers
☐ Service agencies (marketing, design, consulting)
☐ Medical/Professional services

PICK ONE NOW: _______________________
```

**If selected ✓ → Continue**

---

### 4. Do you have a email/domain for cold outreach?
```
OPTIONS:
A. Use personal Gmail (⚠️ higher spam risk, but works)
   → Create or use existing: leadgen@gmail.com
   
B. Use custom domain (✓ RECOMMENDED)
   → Buy: namecheap.com or godaddy.com (~$12/year)
   → DNS setup: 5 minutes
   → Email via Gmail (custom domain forwarding)
   
DECISION: Door A or B? _______________________
```

**If selected ✓ → Continue**

---

### 5. Do you understand the 3-agent model?
```
Scout Agent:
  ➜ Scrapes Google Maps for companies with pain points
  ➜ Filters: low rating + unanswered reviews
  ➜ OUTPUT: List of 40-60 qualified leads/day

Analyzer Agent:
  ➜ Uses LLM to validate pain points
  ➜ Determines HOW to approach each lead
  ➜ OUTPUT: Leads ready for outreach with angle

Mailer Agent:
  ➜ Generates personalized emails
  ➜ You manually approve before sending
  ➜ OUTPUT: Sent email + tracking
```

**If understood ✓ → Continue. If not sure? → Read the LEAD_ARBITRAGE_IMPLEMENTATION_PLAN.md first (30 min)**

---

## 🛠️ SETUP BY THE HOUR

### 09:00 - 09:15: CREATE REQUIRED ACCOUNTS

**Task 1.1: OpenRouter Account** (3 min)
```
1. Go to https://openrouter.ai
2. Sign up with email
3. Verify email
4. Go to Dashboard → Keys
5. Create new key (copy & save to password manager)
6. Note: This is your API key for LLM calls
```

**Task 1.2: Apify Account** (3 min)
```
1. Go to https://apify.com
2. Sign up
3. Verify email
4. Dashboard → API tokens
5. Create token (copy & save)
6. Note: Used for scraping Google Maps, emails, etc.
```

**Task 1.3: Gmail Setup** (5 min)
```
If using personal Gmail:
  1. Create or use existing email: leadgen@gmail.com
  2. Go to https://myaccount.google.com/apppasswords
  3. Generate "App Password" (NOT your regular password)
  4. Copy & save this password

If using custom domain:
  1. Buy domain (namecheap.com): ~$12/year
  2. Create email via your provider (or Google Workspace trial)
  3. Get App Password same as above
```

**✅ Checkpoint: All 3 accounts created + keys saved safely**

---

### 09:15 - 09:45: RENT VPS + PREPARE DOCKER

**Task 2.1: Rent VPS from DigitalOcean** (10 min)
```
1. Go to https://www.digitalocean.com
2. Sign up (use GitHub OAuth for speed)
3. Create new Droplet:
   - Region: Choose closest to you
   - OS: Ubuntu 22.04
   - Plan: Basic Droplet ($5/month)
   - Size: 2GB RAM minimum
4. Create droplet (wait 1-2 min for setup)
5. Once created, you'll get IP address (copy it)
   → Example: 167.99.123.456
```

**Task 2.2: SSH into VPS** (5 min)
```
On Windows (using PowerShell or Git Bash):
  ssh root@167.99.123.456
  
When prompted:
  - "Are you sure you want to continue connecting?" → type: yes
  - Enter password (given by DigitalOcean email)
  
✅ You should now be inside the VPS terminal
```

**Task 2.3: Install Docker** (15 min — mostly automated)
```
Inside VPS terminal, paste this entire command:

curl -fsSL https://get.docker.com -o get-docker.sh && sh get-docker.sh

Wait for it to complete (~10 min). Ignore any warnings.

Verify Docker is installed:
  docker --version
  
You should see: "Docker version 24.x.x" or similar
```

**✅ Checkpoint: Docker running on VPS**

---

### 09:45 - 10:30: INSTALL N8N

**Task 3.1: Create n8n Directory & Docker Compose** (10 min)
```
Still inside VPS. Run these commands:

mkdir n8n
cd n8n

Now create the docker-compose.yml file. 
Copy & paste the entire text below:

---BEGIN COPY---
version: '3.8'
services:
  n8n:
    image: n8nio/n8n:latest
    container_name: n8n
    restart: unless-stopped
    ports:
      - "5678:5678"
    environment:
      - N8N_HOST=0.0.0.0
      - N8N_PORT=5678
      - N8N_PROTOCOL=http
      - N8N_ENCRYPTION_KEY=change_me_to_something_random_12345
      - DB_TYPE=sqlite
      - EXECUTIONS_PROCESS=main
    volumes:
      - ./data:/home/node/.n8n
    networks:
      - n8n_network

networks:
  n8n_network:
    driver: bridge
---END COPY---

Paste into terminal:
  nano docker-compose.yml

Then:
  1. Paste the text
  2. Press Ctrl+X
  3. Press Y
  4. Press Enter

Verify file was created:
  cat docker-compose.yml
```

**Task 3.2: Start n8n with Docker Compose** (5 min)
```
Still in n8n folder, run:
  docker-compose up -d

Wait 30 seconds. Then verify it's running:
  docker ps
  
You should see "n8n" in the list of running containers.
```

**Task 3.3: Access n8n Web Interface** (1 min)
```
Open your browser and go to:
  http://167.99.123.456:5678
  
(Replace 167.99.123.456 with YOUR VPS IP address)

You should see n8n login screen.
Complete the setup (create admin user).
```

**✅ Checkpoint: n8n running and accessible via browser**

---

### 10:30 - 11:30: CONNECT APIS IN N8N

**Task 4.1: Add OpenRouter Credentials** (10 min)
```
Inside n8n (logged in):
1. Click Settings (bottom left gear icon)
2. Click "Credentials"
3. Click "New → Create new Credential"
4. Search: "OpenRouter" (if not available, use "HTTP" + custom headers)
5. Fill in:
   - Name: "OpenRouter API Key"
   - API Key: (paste your OpenRouter key from 09:15)
6. Test and Save
```

**Task 4.2: Add Apify Credentials** (5 min)
```
1. Settings → Credentials → New
2. Search: "Apify" (or use "HTTP")
3. Fill in:
   - Token: (paste your Apify token)
4. Test and Save
```

**Task 4.3: Add Gmail Credentials** (10 min)
```
1. Settings → Credentials → New
2. Search: "Gmail"
3. Click OAuth2:
   - Click "Create"
   - You'll be redirected to Gmail permission
   - Grant permissions (n8n needs access to send/read emails)
   - Confirm
4. Credentials auto-saved
```

**Task 4.4: Test All Credentials** (5 min)
```
Inside n8n:
1. Create new workflow (+ button)
2. Add HTTP node
3. In node config, try to select credential "OpenRouter API Key"
4. If successful → ✅
5. Repeat for Apify and Gmail

If any fail → Go back to credentials, check keys are correct
```

**✅ Checkpoint: All 3 APIs authenticated in n8n**

---

### 11:30 - 12:00: TEST THE SYSTEM

**Task 5.1: Import Pre-built Workflow** (5 min)
```
In n8n:
1. Go to Workflows
2. Click Import
3. Paste this JSON (we created it):
   → n8n-lead-arbitrage-workflow.json
4. Click Import

Your workflow should now be in n8n.
```

**Task 5.2: Run First Test** (10 min)
```
1. Open the imported workflow
2. Click each node and verify they're configured:
   - Scout node: Apify credential
   - Analyzer node: OpenRouter credential
   - Mailer node: Gmail credential
3. Click "Execute Workflow"
4. Watch for errors
5. First run will be slow (downloading images, etc)
```

**Task 5.3: Check for Errors** (5 min)
```
If errors appear:
- "API key invalid" → Go back to credentials, verify
- "Connection refused" → Wait, VPS might still be booting
- "Permission denied" → Delete and re-authenticate Gmail

If no errors:
  ✅ System is working!
```

**✅ Checkpoint: Full 3-agent pipeline tested successfully**

---

## 📋 END OF TODAY CHECKLIST

```
Infrastructure:
  ☐ VPS rented (IP: _______________)
  ☐ Docker installed
  ☐ n8n running (accessible via browser)
  ☐ n8n passwords saved securely

Credentials:
  ☐ OpenRouter API key added to n8n
  ☐ Apify API token added to n8n
  ☐ Gmail OAuth token added to n8n
  ☐ All tested (no "permission denied" errors)

System:
  ☐ n8n workflow imported
  ☐ First test run executed
  ☐ No critical errors
  ☐ Dashboard accessible

Documents:
  ☐ Saved: LEAD_ARBITRAGE_IMPLEMENTATION_PLAN.md
  ☐ Saved: SYSTEM_PROMPTS_LEAD_ARBITRAGE.md
  ☐ Saved: n8n-lead-arbitrage-workflow.json
  ☐ Saved: KPI_DASHBOARD_TEMPLATE.csv
```

**If all ✅ → You're ready for DAY 2!**

---

## 🎯 WHAT HAPPENS NEXT? (DAY 2-7)

### Day 2-3: Refine Scrapers
```
Target: 50-100 qualified leads scraped
Adjust Apify filters:
  - Geographic location (filter by city/zip)
  - Review count minimum
  - Specific keywords in reviews (e.g., "slow", "unresponsive")
Expected output: SQLite database with:
  name | website | phone | email | rating | problem
```

### Day 3-4: Test Analyzer Agent
```
Target: First 20 leads analyzed for fit
Manually review LLM output:
  - Are confidence scores reasonable?
  - Are approach angles specific & compelling?
  - Any red flags in the analysis?
Iterate on system prompt if needed.
```

### Day 4-5: Generate & Approve Emails
```
Target: 20 personalized emails generated
Process:
  1. LLM generates email
  2. YOU manually review (critical!)
  3. Review for: tone, personalization, typos
  4. Approve or edit
  5. Send
```

### Day 5-7: Launch & Optimize
```
Target: 50-100 emails sent, 1+ reply, first deal
Monitor:
  - Reply rate (target: 2-5%)
  - Positive reply rate
  - Email open rate
Scale if working, pivot if not.
```

---

## 🆘 IF YOU GET STUCK

| Problem | Solution | Time |
|---------|----------|------|
| Can't SSH into VPS | Use DigitalOcean console (web-based terminal) instead | 5 min |
| Docker won't install | Try: `sudo apt update && sudo apt upgrade -y` first | 10 min |
| n8n won't start | `docker logs n8n` to see errors, DM support on Slack | 15 min |
| API credentials fail | Go back to OpenRouter/Apify, verify keys are active (they auto-deactivate sometimes) | 5 min |
| Gmail OAuth loops | Use "Personal Google Account" (not Workspace). Delete + re-authenticate. | 10 min |
| Workflow has too many errors | Import fresh copy of n8n-lead-arbitrage-workflow.json | 5 min |

---

## ✅ TODAY'S FINAL CHECKPOINT

**System is ready if:**

1. ✅ n8n is running and accessible via browser
2. ✅ All 3 APIs are authenticated (no permission errors)
3. ✅ Workflow can run without critical errors
4. ✅ You know your target vertical (restaurants / plumbers / etc)
5. ✅ You have a Gmail account for cold outreach
6. ✅ You have $15-50 for first week of APIs

**If you have all 6 ✓ → You're cleared for Day 2**

**If you're missing any → Fix before moving forward (takes <1 hour each)**

---

## 📞 NEXT STEPS

**TODAY (Before 12:00):**
- [ ] Complete all tasks above
- [ ] Post your VPS IP in session notes (so you don't lose it)
- [ ] Mark this guide as ✅ COMPLETE

**TOMORROW (Day 2):**
- [ ] Start with Task 2.1 from LEAD_ARBITRAGE_IMPLEMENTATION_PLAN.md
- [ ] Run first Scout agent (Apify scraper)
- [ ] Get first 50 leads into SQLite

**THIS WEEK:**
- [ ] Follow 7-day roadmap
- [ ] Take 10 min daily to update KPI_DASHBOARD_TEMPLATE.csv
- [ ] By Day 7: First email sent, first reply, first call

---

## 🚀 FINAL THOUGHT

**This is the fastest path from "idea" to "first revenue" we have.**

Your job this week is only to:
1. **Get the system running** (today ✅)
2. **Find leads** (day 2-3)
3. **Validate they're real problems** (day 3-4)
4. **Send first batch** (day 4-5)
5. **Get first reply** (day 5-6)
6. **Get first deal** (day 7)

The system handles everything else. You just guide it.

**Ready? Open your terminal and start with Task 1.1 above.**

---

**Good luck. You've got this. 🎯**

**Version:** 2.0  
**Ready At:** March 30, 2026, 09:00 UTC  
**ADRION 369 — Lead Arbitrage System**
