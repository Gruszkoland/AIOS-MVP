#!/bin/bash

# ADRION 369 — OpenRouter API Key Validator
# ===========================================

echo "🔐 ADRION 369 — OpenRouter API Key Validator"
echo "=============================================="
echo ""

# Check if .env exists
if [ ! -f "../../.env" ]; then
    echo "❌ .env file not found"
    exit 1
fi

# Extract API key
API_KEY=\

# Validate format
if [[ ! \ =~ ^sk-or-v ]]; then
    echo "❌ Invalid API key format. Should start with 'sk-or-v'"
    exit 1
fi

if [ -z "\" ]; then
    echo "❌ OPENROUTER_API_KEY not set"
    exit 1
fi

echo "✅ API key format validated"
echo "✅ Key starts with: sk-or-v...\..."
echo ""

# Optional: test connectivity
if command -v curl &> /dev/null; then
    echo "Testing API connectivity..."
    RESPONSE=\
    if echo "\" | grep -q "error"; then
        echo "❌ API connection failed"
        echo "Response: \"
        exit 1
    else
        echo "✅ API connectivity confirmed"
    fi
fi

echo ""
echo "✅ All validations passed!"
