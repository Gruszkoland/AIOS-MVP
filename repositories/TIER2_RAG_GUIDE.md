# TIER 2: RAG + LOCAL LLM INTEGRATION GUIDE

## 📚 Contents (4 Repositories)

1. **RAGFlow** (⭐ 77.7k) — Production-grade RAG engine
2. **Agentic RAG for Dummies** (⭐ 3.0k) — Learning + LangGraph
3. **Local RAG** (⭐ 0.7k) — Ollama-native setup
4. **RAGLight** (⭐ 0.7k) — Modular framework

---

## 🎯 ADRION 369 Integration Points

### RAGFlow for Intellectual Trinity Perspective

```python
from ragflow import RAGFlow
from arbitrage.trinity import evaluate_intellectual

# Setup RAGFlow with Ollama + local embeddings
rag = RAGFlow(
    llm="ollama://deepseek-coder-v2",  # Local LLM
    embedding="ollama://nomic-embed-text",  # Local embeddings
    db_type="milvus",  # Vector DB
)

# Ingest Guardian Laws and decision context
documents = [
    "guardian_laws.pdf",
    "past_decisions.jsonl",
    "legal_frameworks.md",
]
rag.ingest(documents)

# Intellectual Perspective: Knowledge-augmented scoring
class IntellectualAgentWithRAG:
    def evaluate(self, job_context):
        # Retrieve relevant guardian law context
        context_docs = rag.retrieve(
            query=f"Guardian Laws relevant to {job_context['type']}",
            top_k=5,
        )

        # Generate intellectual score
        reasoning = rag.reason(
            query=job_context,
            context=context_docs,
            prompt="""
            Evaluate the logical correctness and factual validity of this decision.
            Consider: consistency, evidence quality, contradiction detection.
            Return score 0-1.
            """
        )

        return reasoning["score"]
```

### Agentic RAG for 162D Decision Space Visualization

```python
from langgraph.graph import StateGraph
from agentic_rag import RAGAgent

# RAG-powered agent for decision context exploration
class DecisionSpaceExplorer:
    def __init__(self, rag_engine):
        self.rag = rag_engine

        # LangGraph state machine
        self.graph = StateGraph(DecisionState)
        self.graph.add_node("retrieve", self._retrieve_context)
        self.graph.add_node("reason", self._reason_about_decision)
        self.graph.add_node("synthesize", self._synthesize_insights)

    def _retrieve_context(self, state):
        """Retrieve relevant documents for decision"""
        docs = self.rag.retrieve(state["query"], top_k=10)
        return {**state, "context_docs": docs}

    def _reason_about_decision(self, state):
        """Use LLM to reason about decision with context"""
        reasoning = self.rag.reason(
            query=state["query"],
            context=state["context_docs"],
        )
        return {**state, "reasoning": reasoning}

    def _synthesize_insights(self, state):
        """Synthesize final insights"""
        return {**state, "decision_ready": True}
```

### Local RAG with Ollama (Privacy-First)

```python
import ollama
from local_rag import LocalRAG

# Privacy-first setup (zero cloud dependencies)
rag = LocalRAG(
    model="deepseek-coder-v2",
    embedding_model="nomic-embed-text",
    vector_db="milvus",  # Local
)

# Batch ingest
rag.batch_ingest(
    documents_path="./data/",
    chunk_size=500,
    overlap=50,
)

# Query for Trinity perspectives
def material_perspective_with_local_rag():
    context = rag.retrieve("Resource constraints and requirements")
    return evaluate_material(context)

def intellectual_perspective_with_local_rag():
    context = rag.retrieve("Factual correctness and consistency")
    return evaluate_intellectual(context)
```

---

## 🚀 Quick Start (2-3 hours)

### Setup RAGFlow Docker

```bash
# Option 1: Docker Compose
cd repositories/tier2-rag/ragflow
docker-compose up -d

# Option 2: Direct Docker
docker run -d \
  --name ragflow \
  -p 8000:8000 \
  -e LLM_MODEL=ollama://deepseek-coder-v2 \
  infiniflow/ragflow

# Verify
curl http://localhost:8000/health
```

### Ingest Guardian Laws

```python
from ragflow import RAGFlow

rag = RAGFlow(api_url="http://localhost:8000")

# Upload Guardian Laws document
rag.upload_document(
    path="docs/GUARDIAN_LAWS_CANONICAL.json",
    dataset_id="guardian_laws",
)

# Wait for ingestion
rag.wait_for_ingestion()

# Verify
results = rag.retrieve("Nonmaleficence")
print(f"Retrieved {len(results)} documents")
```

### Integrate into Trinity

```python
from arbitrage.trinity import TrinityScore, evaluate_trinity
from ragflow import RAGFlow

# Initialize RAG
rag = RAGFlow(api_url="http://localhost:8000")

# Original evaluate_trinity modified
def evaluate_trinity_with_rag(job, analysis):
    # ... Material & Essential as before ...

    # NEW: Intellectual with RAG context
    context = rag.retrieve(
        query=f"Evaluate factual correctness: {analysis['reasoning']}",
        top_k=5,
    )

    intellectual_score = _score_intellectual_with_context(analysis, context)

    return TrinityScore(
        material=material_score,
        intellectual=intellectual_score,
        essential=essential_score,
    )
```

---

## 📋 Integration Checklist

- [ ] RAGFlow Docker running (port 8000)
- [ ] Ollama containers available (local LLM)
- [ ] Guardian laws ingested into RAGFlow
- [ ] RAG retrieval tested
- [ ] Trinity Intellectual perspective integrated
- [ ] LangGraph state machine for decision context
- [ ] Performance tested (retrieval latency)
- [ ] Generis Record updated with RAG context logs

---

## 🔗 Key References

- **RAGFlow Docs:** https://docs.ragflow.io/
- **RAGFlow Examples:** https://github.com/infiniflow/ragflow/tree/main/examples
- **Ollama Setup:** https://ollama.ai/
- **LangGraph:** https://python.langchain.com/docs/langgraph/

---

## 🎯 Expected Outcomes

- ✅ Intellectual Trinity score now evidence-based (RAG-backed)
- ✅ Guardian Law decisions contextually informed
- ✅ Decision traceability (which documents influenced decision?)
- ✅ Privacy-preserved (Ollama local, no cloud)
- ✅ Performance: ~200-500ms retrieval latency

---

**Integration Time:** 2-3 hours
**Difficulty:** ⭐⭐ (Easy to Medium)
**Priority:** 🔴 CRITICAL
