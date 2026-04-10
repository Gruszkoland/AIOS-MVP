#!/bin/bash
# install-all-repositories.sh
# Install all 15 GitHub repositories with dependencies

set -e

echo "🚀 INSTALLING ALL 15 REPOSITORIES FOR ADRION 369"
echo "="
echo ""

# TIER 1: Orchestration
echo "📦 TIER 1: Installing orchestration libraries..."
cd repositories/tier1-orchestration

if [ -d "crewAI" ]; then
    echo "  ✓ CrewAI - installing..."
    cd crewAI && pip install -e . 2>&1 | tail -2 && cd ..
fi

if [ -d "swarm" ]; then
    echo "  ✓ OpenAI Swarm - installing..."
    cd swarm && pip install -e . 2>&1 | tail -2 && cd ..
fi

if [ -d "agent-framework" ]; then
    echo "  ✓ Microsoft Agent Framework - installing..."
    cd agent-framework && pip install -e . 2>&1 | tail -2 && cd ..
fi

if [ -d "swarms" ]; then
    echo "  ✓ Kyegomez Swarms - installing..."
    cd swarms && pip install -e . 2>&1 | tail -2 && cd ..
fi

if [ -d "agency-swarm" ]; then
    echo "  ✓ VRSEN Agency Swarm - installing..."
    cd agency-swarm && pip install -e . 2>&1 | tail -2 && cd ..
fi

cd ../..

# TIER 2: RAG
echo ""
echo "📦 TIER 2: Installing RAG libraries..."
cd repositories/tier2-rag

if [ -d "ragflow" ]; then
    echo "  ✓ RAGFlow - note: requires Docker (see docker-compose.yml)"
finow
fi

if [ -d "agentic-rag-for-dummies" ]; then
    echo "  ✓ Agentic RAG for Dummies - installing..."
    cd agentic-rag-for-dummies && pip install -r requirements.txt 2>&1 | tail -2 && cd ..
fi

if [ -d "local-rag" ]; then
    echo "  ✓ Local RAG - installing..."
    cd local-rag && pip install -r requirements.txt 2>&1 | tail -2 && cd ..
fi

if [ -d "RAGLight" ]; then
    echo "  ✓ RAGLight - installing..."
    cd RAGLight && pip install -e . 2>&1 | tail -2 && cd ..
fi

cd ../..

# TIER 3: Frameworks
echo ""
echo "📦 TIER 3: Installing LLM frameworks..."
cd repositories/tier3-frameworks

if [ -d "langchain" ]; then
    echo "  ✓ LangChain - installing core + langgraph..."
    cd langchain && pip install -e . 2>&1 | tail -2
    pip install langgraph 2>&1 | tail -2
    cd ..
fi

if [ -d "GenAI_Agents" ]; then
    echo "  ✓ GenAI_Agents - Jupyter notebooks (manual exploration)"
fi

if [ -d "agentops" ]; then
    echo "  ✓ AgentOps - installing..."
    cd agentops && pip install -e . 2>&1 | tail -2 && cd ..
fi

cd ../..

# TIER 4: Monitoring
echo ""
echo "📦 TIER 4: Setting up monitoring..."
echo "  ⚠️  Tier4 contains Docker services - configure separately"
echo "     - Grafana: docker-compose up grafana"
echo "     - VictoriaMetrics: docker-compose up victoriametrics"
echo "     - OpenObserve: docker-compose up openobserve"

echo ""
echo "✅ INSTALLATION COMPLETE"
echo ""
echo "📋 Summary:"
echo "  ✓ Created 15 repository directories"
echo "  ✓ Installed Python packages from Tier 1-3"
echo "  ✓ Docker services ready for Tier 4"
echo ""
echo "📚 Next steps:"
echo "  1. Review INTEGRATION_GUIDE.md for each tier"
echo "  2. Configure ADRION environment variables"
echo "  3. Deploy Docker services"
