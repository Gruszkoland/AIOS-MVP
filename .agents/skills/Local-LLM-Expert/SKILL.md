---
name: Local-LLM-Expert
description: Specialized knowledge for managing local LLM environments, including Ollama, LM Studio, and the ApliArte AI extension. Use when configuring local model endpoints or troubleshooting private LLM performance.
---

# Local LLM Expert

Use this skill when the user wants to set up, optimize, or troubleshoot local AI models. Focus on privacy (G7) and non-maleficence (G8) by keeping data on the user's hardware.

## Supported Environments

### 1. Ollama
- **Endpoint:** Usually `http://localhost:11434`
- **Commands:**
  - `ollama run <model>`: Run a model.
  - `ollama list`: See downloaded models.
  - `ollama pull <model>`: Download a new model.
- **Recommended Models:** Llama 3 (8B), Mistral, Phi-3, Gemma 2.

### 2. LM Studio
- **Endpoint:** Usually `http://localhost:1234/v1` (OpenAI compatible).
- **Optimization:** Use GGUF formats and GPU offloading (Metal/CUDA/Vulkan).

### 3. ApliArte AI Extension
- **ID:** `apliarte.apliarte-ai`
- **Key Settings:**
  - `apliarteAi.agentEndpoint`: URL to the local orchestration layer.
  - `apliarteAi.modelsDir`: Path to local model storage.
  - `apliarteAi.inlineCompletion`: Enable/Disable local code suggestions.

## Configuration Protocol

1. **Model Selection:** Prefer Llama 3 8B for general tasks and Qwen 2 for coding.
2. **Privacy Audit:** Ensure the endpoint is not exposed to the public internet (G7 compliance).
3. **Hardware Check:** Verify RAM/VRAM availability before recommending large models (Sustainability G9).
4. **Integration:** Connect local models to the ADRION 369 system via the MCP Layer or direct API endpoints.

## Troubleshooting
- **Latency:** Check context window size and GPU layers.
- **Connection Refused:** Ensure the local server (Ollama/LM Studio) is running and listening on the correct port.
- **Model Incompatibility:** Verify the quantization format (prefer GGUF for CPU/GPU balance).
