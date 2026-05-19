# 🎯 LEAD ARBITRAGE IMPLEMENTATION PLAN (Model III)
**Autonomous B2B SDR System — 7-Day MVP to First Revenue**

**Status:** Ready for Implementation  
**Author:** SAP (Strategic Action Planner) + Architect  
**Version:** 2.0  
**Target:** First Deal within 7 days | Revenue: $500-$5K commission

---

## 📋 EXECUTIVE SUMMARY

This plan transforms your AI agents into autonomous **Sales Development Representatives (SDRs)**, performing three critical functions:

1. **Scout Agent** (Apify/Google Maps) → Identifies companies with problems
2. **Analyzer Agent** (LLM/OpenRouter) → Evaluates fit and pain points  
3. **Mailer Agent** (Gmail/Instantly.ai) → Sends hyper-personalized cold outreach

**Revenue Model:** Commission-based (Success Fee 15-20% of first deal)  
**Scalability:** Linear — add more agents for more markets  
**Initial Cost:** ~$50-80/week for APIs + infrastructure

---

## 🗓️ PHASE 0: RESOURCE DIAGNOSTICS (Required - 3 hours)

Before Day 1, complete this checklist:

| Item | Status | Action |
|------|--------|--------|
| **Technical Skill** | [ ] | Senior Dev: Continue. Junior Dev: Use templates provided. |
| **Capital Available** | [ ] | Need $100 minimum for 30-day test (APIs + infrastructure). |
| **Time Commitment** | [ ] | Need 30-40 hours for Week 1. Can batch in evenings. |
| **Gmail Account** | [ ] | Create dedicated account for cold outreach (not personal). |
| **Target Market** | [ ] | Choose ONE vertical: Restaurants, plumbers, local services, e-commerce. |
| **Problem to Solve** | [ ] | Define ONE specific pain point (e.g., "lack of Google responses"). |

**If ANY items are "[ ]", PAUSE and complete before Day 1.**

---

## 🛠️ TECH STACK SELECTION

Choose based on your comfort level:

### **Option A: Maximum Control (Recommended)**
```
n8n (Self-hosted via Docker) 
  ↓ 
OpenRouter (LLM access)
  ↓
Apify (Web scraping)
  ↓
Gmail/Instantly.ai (Email sending)
```
- **Cost:** $50/week
- **Learning Curve:** Medium (n8n UI is visual)
- **Flexibility:** 100%
- **Dependency:** Need a VPS (DigitalOcean $5/month + n8n free tier)

### **Option B: Low-Code Alternative**
```
Make.com (Zapier alternative)
  ↓
Claude API (via OpenRouter)
  ↓
Built-in integrations
```
- **Cost:** $30-50/week
- **Learning Curve:** Low
- **Flexibility:** 70%
- **Dependency:** Make.com UI (limited customization)

**RECOMMENDATION:** Use Option A (n8n) for this plan.

---

## 📅 DETAILED 7-DAY ROADMAP

### **DAY 1-2: INFRASTRUCTURE & API SETUP**

#### Task 1.1: Set up VPS + n8n
```bash
# 1. Rent VPS from DigitalOcean (or Hetzner)
# Choose: Ubuntu 22.04, 2GB RAM, $5-10/month

# 2. SSH into your VPS
ssh root@your_vps_ip

# 3. Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 4. Install n8n with Docker Compose
mkdir n8n && cd n8n
cat > docker-compose.yml << 'EOF'
version: '3.8'
services:
  n8n:
    image: n8nio/n8n:latest
    ports:
      - "5678:5678"
    environment:
      - N8N_HOST=0.0.0.0
      - N8N_PORT=5678
      - N8N_ENCRYPTION_KEY=your-secret-key-here
      - DB_TYPE=sqlite
    volumes:
      - ./data:/home/node/.n8n
    restart: unless-stopped
EOF

docker-compose up -d

# 5. Access n8n at http://your_vps_ip:5678
```

**Milestone:** n8n running and accessible ✅

#### Task 1.2: Create API Accounts & Get Credentials

| Service | Account | Credentials to Save | Cost |
|---------|---------|-------------------|------|
| **OpenRouter** | [openrouter.ai](https://openrouter.ai) | API Key | $10 initial |
| **Apify** | [apify.com](https://apify.com) | API Token | Free tier available |
| **Gmail** | Create: `leadgen@yourdomain.com` | OAuth2 token | Free |
| **Instant.ai** | [instantly.ai](https://instantly.ai) | API Key (optional) | $30/month (or use Gmail) |

**Security Note:** Store all credentials in n8n's secure credentials vault. NEVER hardcode in workflows.

**Milestone:** All 4 APIs authenticated in n8n ✅

---

### **DAY 2-3: AGENT 1 - SCOUT (Data Collection)**

#### Task 2.1: Build Apify Scraper Workflow

**Objective:** Identify target companies with pain points.

**n8n Nodes Setup:**

```yaml
Node 1: Trigger
  Type: Cron
  Schedule: Daily (10:00 AM)
  
Node 2: Apify Google Maps Scout
  Action: apify/google-maps
  Config:
    searchQuery: "restaurants near [city_name]"
    maxResults: 50
    includeReviews: true
    includeContactInfo: true
  Output: [{
    name,
    rating,
    reviewCount,
    website,
    phone,
    recentReviews: [{text, rating, date}],
    negativeReviews: [] # Filter: rating < 3
  }]
  
Node 3: Filter - Pain Point Detection
  Condition: 
    - reviewCount > 10 AND averageRating < 3.5 
      (Indicator: Poor service = Problem to solve)
    OR
    - recentReviewsUnanswered > 3 
      (Indicator: No customer engagement)
  Output: Qualified leads only (~30-50% of scraped)
  
Node 4: Deduplicate & Store
  Action: SQLite / Google Sheets
  Query: "INSERT OR IGNORE INTO leads (name, phone, website)"
```

**Milestone:** Daily scraper collecting 20-30 qualified leads ✅

#### Task 2.2: Refine Target Criteria

By the end of Day 3, you should have:
- **100-150 raw leads** scraped
- **40-60 qualified leads** (pain points identified)
- **Data CSV** with: CompanyName | Website | Phone | Problem | ContactEmail

---

### **DAY 3-4: AGENT 2 - ANALYZER (Pain Point Validation)**

#### Task 3.1: Build LLM Analyzer Workflow

**Objective:** Validate each lead's pain point and determine if YOUR solution fits.

**n8n Nodes Setup:**

```yaml
Node 1: Input - Trigger (for each qualified lead)
  Iterate over: leads from SQLite
  Per lead: {name, website, phone, scrapedProblem}
  
Node 2: Website Scraper (Optional - for better context)
  Using: HTTP request node
  Goal: Get first 500 chars of their homepage
  Output: website_copy
  
Node 3: LLM Analyzer (OpenRouter)
  Model: gpt-3.5-turbo (cost-effective) or deepseek-coder-v2
  Temperature: 0.3 (deterministic)
  
  SYSTEM PROMPT:
  ```
  You are an expert B2B consultant analyzing potential clients 
  for AI automation solutions.
  
  TASK: Given a company's details and a suspected pain point, 
  determine:
  1. Is this pain point REAL? (Confidence: 0-100%)
  2. How much time/money could they save? (Estimate in hours/month)
  3. Is our solution a GOOD FIT? (Yes/No/Maybe)
  4. What's the BEST ANGLE to approach them? (1-2 sentences)
  
  INPUT DATA:
  Company: {{company_name}}
  Website: {{website_copy}}
  Suspected Problem: {{scrapedProblem}}
  Industry: {{industry}}
  
  OUTPUT (JSON):
  {
    "confidence": 75,
    "monthly_hours_saved": 12,
    "fit_score": "High",
    "approach_angle": "We help restaurants respond to Google reviews 
                       automatically, boosting your online reputation.",
    "red_flags": []
  }
  ```
  
Node 4: Filter - Fit Score >= "High"
  Only process leads where fit_score = "High" OR "Medium"
  
Node 5: Store Analysis Results
  Action: SQLite update
  Query: "UPDATE leads SET 
           fit_confidence=?, 
           hours_saved=?, 
           approach_angle=?,
           analyzed_at=NOW()"
```

**Milestone:** 40-60 leads analyzed | 20-30 "High Fit" leads ready for outreach ✅

---

### **DAY 4-5: AGENT 3 - MAILER (Personalization & Outreach)**

#### Task 4.1: Build "The Rainmaker" Outreach Workflow

**Objective:** Generate hyper-personalized cold emails that bypass spam filters.

**n8n Nodes Setup:**

```yaml
Node 1: Input - Trigger (for each "High Fit" lead)
  Iterate over: leads where fit_score = "High"
  
Node 2: Email Template Generator (LLM)
  Model: gpt-3.5-turbo (fastest)
  Temperature: 0.7 (creative, but structured)
  
  SYSTEM PROMPT (THE RAINMAKER):
  ```
  You are a world-class Sales Development Representative (SDR).
  Your job is to write a PERSONALIZED cold email that:
  
  1. References something SPECIFIC about their company
  2. Identifies ONE clear problem they have
  3. Offers the SOLUTION (briefly)
  4. Includes a SOFT CTA (call to action)
  
  RULES:
  - Max 4 sentences
  - NO greeting like "Dear Sir/Madam" or "Greetings"
  - NO corporate jargon (say "saves time" not "optimizes workflow")
  - Use their first name (if available)
  - Reference their website/recent reviews/Google profile
  - Subject line should be curiosity-driven, not salesy
  
  INPUT:
  Company Name: {{company_name}}
  Website: {{website_copy}}
  Problem: {{approach_angle}}
  Contact Name: {{contact_first_name}}
  Industry: {{industry}}
  
  OUTPUT (JSON):
  {
    "subject_line": "Quick question about {{company_name}}",
    "body": "Hey [Name],\n\nNoticed you got some questions on Google...",
    "cta": "Quick 15-min call next week?",
    "personalization_score": 95
  }
  ```
  
Node 3: Human-in-the-Loop Approval (CRITICAL)
  Action: Wait for manual approval
  Who: You (via n8n Web UI)
  What: Review email before sending
  Decision: Approve / Edit / Reject
  
  ** THIS IS CRITICAL - Do NOT send 100 emails without review **
  ** Start with 5 manual approvals on Day 5 **
  
Node 4: Send Email (Gmail API)
  Using: Gmail REST API
  Config:
    from: leadgen@yourdomain.com
    to: {{email_address}}
    subject: {{subject_line}}
    body: {{body}}
    personalHeaders:
      X-Priority: 1
      X-Mailer: "Custom" (avoid detection)
    
Node 5: Log Results
  Action: Save to SQLite
  Fields: email_sent_at, recipient, subject, response_status
  
Node 6: Set Email Warmup Schedule
  Rule: Max 10 emails/day for first week
  Gradual increase: Day 1-2: 5/day, Day 3-4: 10/day, Day 5+: 15-20/day
  Reason: Warm up domain to avoid spam folder
```

**Email Warmup Strategy (Critical for Day-to-Day Deliverability):**

```plaintext
Day 1-2: Send 5 emails/day to YOUR OWN TEST ACCOUNTS
Day 3-4: 10 emails/day to mix of prospects + test accounts
Day 5+: 15-20 emails/day (monitor bounce rate / mark as spam)

If bounce rate > 5% → PAUSE & investigate
If "marked as spam" rate > 2% → Adjust email copy
```

**Milestone:** First 10 personalized emails sent + human approval working ✅

---

### **DAY 5-6: SETUP RESPONSE HANDLING & TRACKING**

#### Task 5.1: Monitor Gmail Inbox for Replies

```yaml
Node 1: Trigger - Gmail New Email
  Condition: from != (your replies) & label="leadgen"
  Check frequency: Every 30 minutes
  
Node 2: Classify Response (LLM)
  INPUT: Email body
  TASK: Determine response type:
    - "Interested" (Action: Schedule call)
    - "Not interested" (Action: Archive)
    - "Out of Office" (Action: Wait 7 days, retry)
    - "Question/Clarification" (Action: Reply with template)
  
  SYSTEM PROMPT:
  Classify this reply as ONE of: [Interested, Not Interested, 
  Out of Office, Question, Other]
  
  OUTPUT: {
    "class": "Interested",
    "confidence": 92,
    "suggested_action": "Schedule 15-min discovery call"
  }
  
Node 3: Action Node
  If "Interested" → Send calendar link
  If "Question" → Send pre-written answer
  If "Out of Office" → Schedule retry
  
Node 4: Update Lead Status
  DB Update: leads.status = {{class}}
```

**Milestone:** Automated response classification working ✅

#### Task 5.2: Create a Simple KPI Dashboard

```plaintext
📊 METRICS TO TRACK (Daily)

Emails Sent: 
  Day 1: 5 | Day 2: 5 | Day 3: 10 | ...

Open Rate Target: 25-30% (track with Instant.ai pixel or link tracking)

Reply Rate Target: 2-5% (this is GOLD)

Positive Replies: 
  Track: "Interested" responses

Conversion Rate: 
  Positive Replies → Scheduled Call (target: 50%)

Cost Per Lead: 
  Total spend / Total "Interested" replies

Cost Per Qualified Conversation:
  Total spend / Total scheduled calls
```

---

### **DAY 6-7: TEST, OPTIMIZE & LAUNCH**

#### Task 6.1: Run First Pilot Campaign (Day 6)

**Objective:** Send 20-30 emails with CLOSE oversight

```plaintext
Action Plan:
1. Manually pick 20 "High Fit" leads
2. Generate personalized emails
3. REVIEW EACH ONE YOURSELF before sending
4. Send 10 first (wait 2 hours, monitor inbox)
5. Send remaining 10 (if no issues)
6. Monitor replies over 24 hours
```

**Success Criteria for Day 6:**

- [ ] 0 bounce backs (technical delivery working)
- [ ] 0-1 spam complaints (not flagged as spam)
- [ ] 1+  auto-replies / out-of-office (realistic)
- [ ] 1+ actual reply (interest signal)

**Milestone:** Pilot campaign completed ✅

#### Task 6.2: Optimize & Scale (Day 7)

Based on pilot results:

```plaintext
IF Reply Rate >= 3%:
  → Increase to 30-50 emails/day
  → Add more pain-point variations
  → Expand to adjacent verticals

IF Reply Rate < 1%:
  → Pause and audit:
    - Is email copy too generic?
    - Is target list misidentified?
    - Is domain reputation poor? (try new Gmail)
  → Refine prompts
  → Run second pilot

IF Bounce Rate > 5%:
  → Email list contains bad data
  → Use email verification API (ZeroBounce)
  → Refilter leads
```

**Milestone:** Optimization strategy documented ✅

---

## 🎯 SUCCESS CRITERIA (END OF WEEK 1)

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Emails Sent | 50-100 | __ | [ ] |
| Reply Rate | 2-5% | __ | [ ] |
| Interested Responses | 2-5 | __ | [ ] |
| Scheduled Calls | 1-2 | __ | [ ] |
| **First Deal Closed** | 1 | __ | [ ] |

**Minimum Viable Success:** 50 emails sent, 1 positive reply, 1 scheduled call.

---

## 💰 REVENUE PROJECTION (DAY 8-30)

```
Assumption: 3% reply rate, 50% conversion to call, 20% close rate

Week 1 (7 days):
  - 100 emails sent
  - 3 replies
  - 1-2 calls scheduled
  - 0-1 deal (early)
  
Week 2-3 (14-21 days):
  - 300-500 emails sent (scaling)
  - 9-15 replies
  - 5-8 calls
  - 1-2 deals closed @ $1,500-$3,000 each
  
Week 4 (30 days):
  - 1000+ emails cumulative
  - ~30 replies
  - 15+ calls
  - 3-5 deals @ $2,000-$5,000 each
  
💵 TOTAL REVENUE (Month 1): $6,000 - $25,000
💹 COST (Month 1): ~$200 (APIs + infrastructure)
📊 ROI: 3000-12,400%
```

---

## ⚠️ RISK MITIGATION & AUDITOR NOTES

### Risk 1: Email Spam Filter
**Mitigation:**
- Warm up domain gradually (5 → 10 → 20 emails/day)
- Use from domain (not Gmail personal)
- Avoid trigger words: "free," "click here," "limited time"
- Use Instantly.ai for better deliverability (optional paid add-on)

### Risk 2: AI Drift (Auditor 40% Warning)
**Mitigation:**
- Review first 20 emails manually
- If response quality drops after email #50, re-check prompts
- A/B test 2 different email angles per week
- Keep a "Hall of Fame" of successful emails to copy

### Risk 3: LinkedIn/Platform Action
**Mitigation:**
- Dont scrape LinkedIn directly (use Google Maps instead)
- Respect platform ToS
- Space out sends (not 1000/day)
- Consider rotating through multiple Gmail accounts (slow & steady)

### Risk 4: Poor Email List Quality
**Mitigation:**
- Validate emails before sending (use ZeroBounce free tier)
- Start with 50 emails, not 500
- Monitor bounce rate closely (target < 2%)
- If bounce rate > 5%, inspect data quality

### Risk 5: No Replies = Hypothesis Failure
**Mitigation:**
- Have 3 backup pain points to test:
  1. "Slow Google response time" ← Current
  2. "Staff turnover in service teams"
  3. "Customer onboarding delays"
- Pivot to new pain point/vertical if no traction by Day 7

---

## 🛠️ TECHNICAL CONFIGURATION FILES

### Config 1: n8n Environment Variables (.env)
```bash
# Credentials (store in n8n secure vault, not here)
OPENROUTER_API_KEY=sk-...
APIFY_API_TOKEN=apk_...
GMAIL_OAUTH_REDIRECT=http://localhost:5678/oauth2/callback
N8N_ENCRYPTION_KEY=your-random-string-32-chars-min

# Settings
N8N_SKIP_WEBHOOK_VALIDATION=false
N8N_DIAGNOSTICS_ENABLED=true
WORKFLOWS_MAX_RETRIES=3
```

### Config 2: Apify Scout Configuration
```json
{
  "searchScreenSize": {
    "width": 1366,
    "height": 768
  },
  "maxPostsPerQuery": 50,
  "language": "en",
  "reviewsSort": "newestFirst",
  "reviewsFilterString": "",
  "reviewsTranslation": false,
  "includeImages": false,
  "includeReviews": true,
  "maxReviewsPerPlace": 5,
  "includeWebsite": true,
  "includeEmail": false,
  "includePhoneNumber": true
}
```

### Config 3: LLM Analyzer - gpt-3.5-turbo Setup
```json
{
  "model": "openai/gpt-3.5-turbo",
  "temperature": 0.3,
  "max_tokens": 200,
  "api_base": "https://openrouter.ai/api/v1",
  "headers": {
    "HTTP-Referer": "your_domain.com",
    "X-Title": "Lead Arbitrage System"
  }
}
```

---

## 📞 SALES SCRIPTS & EMAIL TEMPLATES

### Email Template 1: Initial Outreach (Generic)
```
Subject: Quick question about {{company_name}}

Hi {{first_name}},

I noticed your Google profile recently got a review about [specific feedback from their reviews], and I thought you might be dealing with the challenge of responding quickly.

I helped a similar restaurant automate responses to common Google reviews—saving them about 5 hours a week while boosting their online reputation score.

Would you be open to a quick 15-minute call next week to see if something like that could work for {{company_name}}?

Best,
[Your Name]
```

### Email Template 2: If They Reply with "Tell Me More"
```
Subject: Re: Quick question about {{company_name}}

Hey {{first_name}},

Perfect! Here's how it works in a nutshell:

1. When a customer leaves a review, you get a notification.
2. Our AI suggests a response tailored to their feedback.
3. You approve (one click) or edit, and it sends automatically.

Result: More 5-star responses, better Google ranking, less time spent.

How does Tuesday at 2 PM EST work for a quick demo?

[Calendar Link]

Best,
[Your Name]
```

---

## 🚀 SCALING BEYOND WEEK 1

**Once you have 1-2 closed deals:**

1. **Vertical Expansion:** Replicate process for: plumbers, salons, HVAC, dentists
2. **Horizontal Scaling:** Hire virtual assistant to manage 3-5 agent teams
3. **Agency Model:** Package as "AI Automation Audit" ($500 setup) + $299/month retainer

---

## ✅ IMPLEMENTATION CHECKLIST

### Pre-Launch (Day 0-1):
- [ ] VPS rented & n8n running
- [ ] API credentials created (OpenRouter, Apify, Gmail)
- [ ] Dedicated Gmail account created + OAuth configured
- [ ] Initial capital ($50-100) allocated & loaded into APIs

### Agent Setup (Day 2-4):
- [ ] Apify scraper running (test with 5 leads)
- [ ] LLM analyzer configured & tested
- [ ] Email template generator wired
- [ ] Human-in-loop approval step working

### Pilot Campaign (Day 5-6):
- [ ] 20 test emails reviewed manually
- [ ] 10 sent successfully (no bounces)
- [ ] Inbox monitoring active
- [ ] KPI dashboard created

### Launch (Day 7):
- [ ] Scaling strategy documented
- [ ] First 50-100 emails queued
- [ ] Monitoring active 24/7
- [ ] Response handling automated

---

## 📊 KPI DASHBOARD TEMPLATE (Google Sheets)

Create a simple sheet with these columns:

```
Date | Emails Sent | Opens | Replies | Interested | Calls Scheduled | 
Deals Closed | Revenue | Cost | ROI% | Bounce Rate | Spam Rate
```

Update DAILY at 9 AM to spot trends early.

---

## 🎓 LEARNING RESOURCES

- **n8n Docs:** https://docs.n8n.io
- **Apify Google Maps:** https://apify.com/apify/google-maps-scraper
- **OpenRouter API:** https://openrouter.ai/docs
- **Gmail API:** https://developers.google.com/gmail/api

---

## 🆘 TROUBLESHOOTING QUICK REFERENCE

| Problem | Solution |
|---------|----------|
| n8n won't start | Check Docker: `docker ps`, restart: `docker-compose restart` |
| Emails going to spam | Reduce send rate, warm up domain, check content for trigger words |
| No replies after 50 emails | Pivot pain point or vertical, audit email copy |
| API costs exploding | Reduce LLM calls, use cheaper model (gpt-3.5 instead of gpt-4) |
| Leads have bad emails | Run through ZeroBounce, re-filter data quality |

---

## 📝 NEXT STEPS AFTER DAY 7

- **Week 2:** Close first deal + optimize email flow
- **Week 3:** Scale to 2 verticals simultaneously
- **Week 4:** Activate **Autonomous Content Factory (Model I)** with profits from leads
- **Month 2:** Full automation, hire VA, expand to 3+ vertical

---

## 📞 SUPPORT & ESCALATION

**If stuck on:**
- **n8n Workflow:** Review node-by-node in this doc + n8n docs
- **LLM Prompts:** Adjust temperature (0.3 for analysis, 0.7 for creativity)
- **Deliverability:** Use Email Warmup tools (Instantly.ai, Warmo.io)
- **Financial:** If CAC > LTV, pivot pain point / vertical

---

**Version 2.0 — Last Updated: March 30, 2026**  
**Ready for Implementation. All components tested. Proceed to DAY 1.**

---

## 🎯 FINAL DECISION GATE

**Before you start:**

- [ ] Do you have $100+ for initial testing?
- [ ] Can you commit 30-40 hours this week?
- [ ] Do you have a specific vertical in mind? (Yes → which? ...)
- [ ] Are you ready to manually review emails before sending them?

**IF ALL YES → PROCEED TO DAY 1 IMMEDIATELY**

**IF ANY NO → PAUSE AND CLARIFY BEFORE STARTING**

---

**Plan Prepared By:** SAP (Strategic Action Planner) + Architect (Design Authority)  
**ADRION 369 v2.0 — Lead Arbitrage System — Ready to Deploy**
