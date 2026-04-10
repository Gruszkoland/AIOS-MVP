# QUICKSTART — OpenRouter Deployment (30 minutes)

## Prerequisites
- OpenRouter account (free at openrouter.ai)
- OpenRouter API Key
- Python 3.9+
- Docker (optional, for containerized deployment)

## STEP 1: Get OpenRouter API Key (5 min)

1. Visit https://openrouter.ai/keys
2. Sign up or log in
3. Click "Create Key" button
4. Copy the key (starts with \sk-or-v1-\)
5. Keep it safe — treat like password

## STEP 2: Configure Environment (5 min)

\\\ash
# Copy production template
cp 1_env_templates/.env.openrouter-production .env

# Edit with your editor
nano .env  # or use your editor

# Find and replace:
OPENROUTER_API_KEY=sk-or-v1-PLACEHOLDER_YOUR_KEY_HERE
# With your actual key:
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxx
\\\

## STEP 3: Validate Configuration (2 min)

\\\ash
# Run validation script
bash 2_scripts/deployment/validate-openrouter-key.sh

# Expected output:
# ✅ OpenRouter key is valid
# ✅ API endpoint reachable
# ✅ Rate limits checked
\\\

## STEP 4: Install Dependencies (5 min)

\\\ash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate

# Install requirements
pip install -r requirements.txt

# Verify OpenRouter SDK installed
python -c "import openrouter; print('✅ OpenRouter SDK ready')"
\\\

## STEP 5: Run Tests (5 min)

\\\ash
# Run quick sanity tests
cd 4_tests
pytest test_openrouter_basic.py -v

# Expected output:
# test_openrouter_alive ... PASSED
# test_llm_chat_basic ... PASSED
# test_canary_routing ... PASSED
\\\

## STEP 6: Start Service (3 min)

\\\ash
# Option A: Local (development)
python wsgi.py

# Option B: Docker
docker-compose -f 6_docker/docker-compose.openrouter.yml up

# Verify service is running
curl http://localhost:8001/api/arbitrage/status
\\\

## ✅ SUCCESS! You're Ready

Your ADRION 369 with OpenRouter is now running!

### Next: Check Documentation
- **Full Setup:** Read OPENROUTER_CONFIG.md
- **API Reference:** See 5_docs/COMPLETE_API_REFERENCE.md
- **Monitoring:** Check monitoring/openrouter/ dashboards
- **Troubleshooting:** See 5_docs/TROUBLESHOOTING.md

### Common Tasks

**Check OpenRouter usage:**
\\\ash
bash 2_scripts/deployment/check-openrouter-usage.sh
\\\

**View KPI metrics:**
\\\ash
tail -f monitoring/llm_kpi_events.jsonl
\\\

**Switch models:**
\\\ash
# Edit .env
LLM_MODEL=google/gemma-2-9b-it:free
# Restart service
\\\

**Enable canary testing:**
\\\ash
bash 2_scripts/deployment/enable-canary-rollout.sh 20 openrouter
\\\

---
**Status: ✅ Ready for Development**  
**Time to Setup: ~30 minutes**
**Support: See 5_docs folder**
