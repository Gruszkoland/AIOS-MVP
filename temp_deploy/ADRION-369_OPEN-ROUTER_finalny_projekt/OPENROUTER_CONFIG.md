# OpenRouter Integration Guide — Technical Documentation

## Architecture Overview

\\\
┌─────────────────────────────────────────────┐
│  ADRION 369 Arbitrage Engine                │
│                                             │
│  ┌───────────────────────────────────────┐  │
│  │ High-Level LLM Interface (chat())     │  │
│  └──────────────┬──────────────────────┘  │
│                 │                          │
│   ┌─────────────┴──────────────┐           │
│   ▼                            ▼           │
│  Backend Router         KPI Monitoring     │
│   │                      │                 │
│   ├─→ OpenRouter ──┐     └→ Metrics       │
│   ├─→ Ollama       │         │             │
│   └─→ Mock         └─────┬───┘             │
│                          │                 │
│                    Canary Rollout          │
│                    A/B Testing             │
│                    Rate Limiting           │
└─────────────────────────────────────────────┘
         │
         ▼
    OpenRouter.ai API
    (40+ models available)
\\\

## Supported Models

### Free Tier Models (Rate-limited)
| Model | Speed | Quality | Cost |
|-------|-------|---------|------|
| Llama 3.1 8B | ⭐⭐⭐⭐ | ⭐⭐⭐ | FREE |
| Mistral 7B | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | FREE |
| Gemma 2 9B | ⭐⭐⭐ | ⭐⭐⭐ | FREE |
| DeepSeek R1 70B | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | FREE |

### Paid Models (Recommended for Production)
| Model | Speed | Quality | Cost |
|-------|-------|---------|------|
| Claude 3.5 Sonnet | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | \/1M tokens |
| GPT-4 Turbo | ⭐⭐ | ⭐⭐⭐⭐⭐ | \/1M tokens |
| Claude 3 Opus | ⭐⭐ | ⭐⭐⭐⭐⭐ | \/1M tokens |

## Configuration Options

### Basic Configuration (.env)
\\\ash
# Primary model
LLM_BACKEND=openrouter
LLM_MODEL=meta-llama/llama-3.1-8b-instruct:free

# Fallback chain
LLM_FALLBACK_MODELS=mistralai/mistral-7b-instruct:free,google/gemma-2-9b-it:free

# API settings
OPENROUTER_API_KEY=sk-or-v1-xxxxx
OPENROUTER_TIMEOUT=60
OPENROUTER_RETRIES=3
\\\

### Advanced Configuration

#### Rate Limiting
\\\ash
# Requests per minute limit
OPENROUTER_RATE_LIMIT=100

# Handle exceeding limits
LLM_RATE_LIMIT_STRATEGY=queue  # or: drop, fallback
\\\

#### Canary Testing
\\\ash
# A/B test by routing percentage of traffic
LLM_CANARY_ENABLED=1
LLM_CANARY_PERCENT=20  # Send 20% to canary backend
LLM_CANARY_BACKEND=openrouter  # Canary backend
\\\

#### KPI Monitoring
\\\ash
# Automatic rollback if error rate exceeds threshold
LLM_KPI_MAX_ERROR_RATE=0.05  # 5% max error rate
LLM_KPI_MAX_P95_MS=8000      # 8000ms max latency
\\\

## Usage Examples

### Simple Chat
\\\python
from arbitrage.llm import chat

response = chat("What is the best marketing strategy?")
print(response)
\\\

### With System Prompt
\\\python
system_prompt = "You are an expert lead scorer for freelance platforms."
user_prompt = "Score this lead: title='Website Design', budget=5000"

response = chat(user_prompt, system=system_prompt)
print(response)
\\\

### Force Backend
\\\python
# Force OpenRouter (skip automatic selection)
response = chat(prompt, force_backend="openrouter")

# Force Ollama if available
response = chat(prompt, force_backend="ollama")
\\\

### Check Health
\\\python
from arbitrage.llm import is_ollama_alive, get_kpi_snapshot

# Check if Ollama running
if is_ollama_alive():
    print("Ollama available")

# Get KPI metrics
metrics = get_kpi_snapshot()
print(f"Error rate: {metrics['error_rate']:.2%}")
print(f"P95 latency: {metrics['p95_latency_ms']:.0f}ms")
\\\

## Cost Management

### Estimate Monthly Cost
\\\
Scenario: 150,000 analyses/month
Average: 2,000 tokens/analysis
Total: 300M tokens/month

Model Cost Calculation:
- Llama 3.1 8B (FREE): \
- Claude 3.5 Sonnet: 300M × \/1M = \
- GPT-4 Turbo: 300M × \/1M = \,000
\\\

### Cost Optimization
1. **Use FREE models for dev/testing**
2. **Canary rollout before paid upgrades**
3. **Profile token usage** — see monitoring/
4. **Prune unnecessary prompts** — shorten inputs
5. **Cache responses** — avoid duplicate calls

## Troubleshooting

### API Key Invalid
\\\ash
# Verify key format
echo "\" | grep -E "^sk-or-v1-"

# Test API call directly
curl -X POST https://openrouter.ai/api/v1/chat/completions \\
  -H "Authorization: Bearer \" \\
  -d '{"model":"meta-llama/llama-3.1-8b-instruct:free","messages":[{"role":"user","content":"test"}]}'
\\\

### Rate Limited
\\\ash
# Check current usage
bash 2_scripts/deployment/check-openrouter-usage.sh

# Upgrade to paid tier or wait for reset
# Default: rolling 24-hour window
\\\

### High Latency
\\\ash
# Check KPI metrics
tail -f monitoring/llm_kpi_events.jsonl

# Switch to faster model
LLM_MODEL=mistralai/mistral-7b-instruct:free
\\\

---
**Version:** 1.0  
**Last Updated:** 06-04-2026  
**Support:** See 5_docs/TROUBLESHOOTING.md
