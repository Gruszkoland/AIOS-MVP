#!/bin/bash

# ADRION 369 Setup Script - macOS/Linux

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║         ADRION 369 - Quick Setup Script for macOS/Linux        ║"
echo "║   Multi-Persona AI Coding System with Trinity + EBDI           ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Check if Ollama is installed
echo "[1] Checking Ollama installation..."
if ! command -v ollama &> /dev/null; then
    echo ""
    echo "❌ Ollama not found"
    echo ""
    echo "📥 Please install Ollama from: https://ollama.ai/"
    echo ""
    echo "macOS: brew install ollama"
    echo "Linux: Follow instructions at https://ollama.ai/"
    echo ""
    exit 1
else
    echo "✅ Ollama found!"
    ollama --version
fi

echo ""
echo "[2] Checking installed models..."
ollama list

echo ""
echo "[3] Would you like to download deepseek-coder-v2:16b? (y/n)"
read -r download_model

if [[ "$download_model" == "y" ]]; then
    echo ""
    echo "📥 Downloading deepseek-coder-v2:16b (warning: ~9GB)..."
    echo ""
    ollama pull deepseek-coder-v2:16b
    if [ $? -eq 0 ]; then
        echo "✅ Model downloaded successfully!"
    else
        echo "❌ Download failed. Check internet connection."
        exit 1
    fi
fi

echo ""
echo "[4] Starting Ollama server..."
echo ""
echo "🚀 Ollama starting on localhost:11434"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""
ollama serve

