# ADRION 369 + Ecosystem Integration Strategy
**Analiza Zastosowania GitHub Repositories w Architekturze ADRION 369**

---

## Executive Summary

Ten dokument mapuje 5 kluczowych ekosystemów open-source na architekturę ADRION 369, identyfikując punkty integracji, potencjalne ulepszenia i strategie wdrażania. Każde repo adresuje konkretne gap w systemie:

| Ekosystem | Zastosowanie | Status | Impact |
|-----------|--------------|--------|--------|
| **MCP Servers** | Standardowy protokół komunikacji AI+Tools | ✅ Live (6 serwerów) | CRÍTICO - Fundament |
| **Perplexity MCP** | Web search + real-time reasoning | 🟡 Planowany | HIGH - Knowledge layer |
| **Claude-Mem** | Persistent context across sessions | 🟡 Komplementarny | HIGH - Memory tier |
| **Glif MCP Server** | AI workflow orchestration | 🔴 Future phase | MEDIUM - Automation |
| **Graphify** | Knowledge graph visualization + querying | 🔴 Future phase | MEDIUM - Observability |

---

## 1. Model Context Protocol (MCP) Servers Ecosystem

### 1.1 Current State in ADRION 369

**Status:** ✅ **LIVE** - Wbudowany w Phase 4  
**Live Implementation:** 6 MCP servers expose w `arbitrage/blueprints/mcp_bp.py`

```python
MCP_SERVERS = {
    "genesis": {"module": "arbitrage.gateway", "class": "GenesisRecord"},
    "guardian": {"module": "arbitrage.guardian", "class": "Guardian"},
    "healer": {"module": "arbitrage.memory", "class": "Healer"},
    "oracle": {"module": "arbitrage.core", "class": "Oracle"},
    "router": {"module": "arbitrage.gateway", "class": "Router"},
    "vortex": {"module": "arbitrage.core", "class": "Vortex"},
}
```

### 1.2 Repository Analysis

**GitHub:** https://github.com/modelcontextprotocol/servers  
**Stars:** 85.5k | **Forks:** 10.7k | **Contributors:** 904  
**License:** Apache 2.0 + MIT  

#### Architektura MCP:
```
┌─────────────────────────────────────────┐
│  MCP Protocol (Standardized JSON-RPC)   │
├─────────────────────────────────────────┤
│  Transport Layer (Stdio/SSE/HTTP)       │
├─────────────────────────────────────────┤
│  Tools (Callable Functions)             │
│  Resources (Data Sources)               │
│  Prompts (System Instructions)          │
└─────────────────────────────────────────┘
```

#### Dostępne Reference Servers:
- **Memory** - Knowledge graph persistence (ADRION: LTM layer)
- **Sequential Thinking** - Reasoning pipeline (ADRION: Guardian Laws evaluation)
- **Git** - Repository operations (ADRION: Genesis record versioning)
- **Fetch** - Web content retrieval (ADRION: Planning for Perplexity integration)
- **Filesystem** - Safe file operations (ADRION: Memory layer storage)

### 1.3 Integration Points for ADRION 369

#### A. Direct Integration (Immediate)
```
MCP Router ──→ [Guardian Checkpoint] ──→ [CVC + LTM] ──→ Genesis Record
   |               |                         |
   ├─→ Invoke Tool ├─→ Evaluate Laws        ├─→ Store Observation
   └─→ Route Args  └─→ Return Decision      └─→ Audit Trail
```

**Current State:** `POST /api/mcp/invoke/<server>` already routes to MCP servers using HARMONIA-GATEWAY compression.

#### B. Recommendation: Adopt MCP SDK for New Servers
- **Current:** Python Flask endpoints + manual routing
- **Target:** Standardize on MCP Python SDK for new Guardian laws (G12+) or Healer extensions

```python
# Future: Native MCP server pattern
from mcp.server.fastapi import FastAPIMCPServer

server = FastAPIMCPServer("adrion-guardian-v12")

@server.tool()
def evaluate_law_g12(request: EvaluationRequest) -> EvaluationResult:
    """New Guardian law evaluation via MCP interface"""
    return guardian.evaluate(request)

# Clients auto-discover tools:
# - Claude Desktop config: {"command": "python", "args": ["-m", "adrion_guardian"]}
```

#### C. Multi-Framework Support
MCP servers available for:
- **TypeScript/Node.js** - `@modelcontextprotocol/python-sdk`
- **Python** - `modelcontextprotocol` (currently used)
- **Java, Go, Rust, C#, Kotlin, Ruby, PHP, Swift** - SDKs available
- **Elixir, Perl, R** - Community SDKs

**ADRION Recommendation:** Keep Python, expand with TypeScript for n8n node templates.

---

## 2. Perplexity API + MCP Server

### 2.1 Repository Analysis

**GitHub:** https://github.com/perplexityai/modelcontextprotocol  
**Stars:** 2.2k | **Forks:** 324 | **License:** MIT  
**Status:** Active, maintained by Perplexity AI

#### Capabilities:
```
┌──────────────────────────────────┐
│  Perplexity Sonar Models         │
├──────────────────────────────────┤
│ 1. perplexity_search   (Web API) │  ← Real-time search results
│ 2. perplexity_ask      (Sonar)   │  ← QA with web context
│ 3. perplexity_research (Deep)    │  ← Comprehensive research
│ 4. perplexity_reason   (Pro)     │  ← Advanced reasoning
└──────────────────────────────────┘
```

### 2.2 Current ADRION Knowledge Sources
- **Phase 2:** Guardian Laws (static, rule-based)
- **Phase 3:** LTM profiles + TSPA scores (session-local)
- **Gap:** Real-time information, web context, external knowledge

### 2.3 Integration Strategy for ADRION 369

#### A. New MCP Server: `adrion-perplexity-gateway`

```python
# Adrian will gain:
class PerplexityGateway(MCPServer):
    """Real-time knowledge layer for Guardian Laws evaluation"""
    
    async def search_for_context(self, query: str) -> SearchResult:
        """Search web + reasoning for law evaluation context"""
        # Example: G4_Truthfulness needs fact-checking
        result = await perplexity.search(query, mode="sonar-pro")
        return result
    
    async def evaluate_with_web_context(self, law_id: str, context: str):
        """Enhanced Guardian evaluation with real-time data"""
        web_context = await self.search_for_context(context)
        return self.guardian.evaluate(law_id, web_context=web_context)
```

#### B. Endpoint Mapping

| ADRION Endpoint | New MCP Tool | Use Case |
|-----------------|-------------|----------|
| `POST /api/mcp/guardian/checkpoint` | `evaluate_with_facts` | G4_Truthfulness verification |
| `GET /api/mcp/ltm/profile` | `research_user_context` | Fetch user context from web |
| `POST /api/mcp/invoke/<server>` | `web_search_tool` | Router needs current info |

#### C. Implementation Timeline

**Phase 5A (Kubernetes + CI/CD):**
1. Create `mcp_servers/perplexity_gateway.py` with MCP SDK
2. Add Perplexity API key to Kubernetes Secrets
3. Wire Perplexity MCP server into n8n workflow nodes

**Phase 5B (Enhanced Guardian):**
1. Update Guardian v12 with web-context-aware evaluation
2. Add confidence scores based on freshness (real-time data > cached > inference)
3. New alert rule: `Guardian_FactCheckRequired` when confidence < 0.75

#### D. Privacy & Security Considerations
- **Perplexity API sends queries externally** → Implement query sanitization
- Recommended: Encrypt PII before sending to Perplexity
- Use `PERPLEXITY_PROXY` for corporate networks
- Store search results in Genesis Record with `EXTERNAL_SOURCE` tag for audit

### 2.4 Cost Estimate

```
Sonar Pro: $0.01 per 1K input tokens, $0.03 per 1K output tokens
Estimated ADRION usage: 50-100 queries/day during Guardian evaluation
Monthly cost: ~$15-30 (acceptable for production)
```

---

## 3. Claude-Mem: Persistent Context Compression

### 3.1 Repository Analysis

**GitHub:** https://github.com/thedotmack/claude-mem  
**Stars:** 75.1k | **Forks:** 6.4k | **License:** Apache 2.0  
**Status:** Actively maintained, 270+ releases

#### Architecture:
```
┌─────────────────────────────────────┐
│  7 Lifecycle Hooks                  │
├─────────────────────────────────────┤
│ SessionStart → UserPromptSubmit      │  Capture phase
│             → PostToolUse            │
│             → SessionEnd             │
├─────────────────────────────────────┤
│  Worker Service (Port 37777)         │  Process phase
│  - SQLite Database + FTS5 Search     │
│  - Chroma Vector DB (embeddings)    │
│  - Web Viewer UI                     │
├─────────────────────────────────────┤
│  3-Layer MCP Search Workflow        │  Query phase
│ 1. search() → compact index          │  (~50-100 tokens)
│ 2. timeline() → chronological view   │  (~100-200 tokens)
│ 3. get_observations() → full details │  (~500-1000 tokens)
└─────────────────────────────────────┘
```

### 3.2 ADRION Current Memory Architecture

**Implemented (Phase 3):**
- CVC (Cumulative Violation Counter) - per-session state
- LTM (Long-Term Memory) - user profiles + TSPA scores
- Genesis Record - append-only audit trail

**Gap:** No cross-session context recovery; each new conversation restarts from K0

### 3.3 Integration Strategy

#### A. Enhanced LTM with Claude-Mem Pattern

Instead of:
```python
# Current: Single TSPA baseline per session
TSPA_BASELINE = {
    "SENTINEL": 0.95,
    "ARCHITECT": 0.85,
    "LIBRARIAN": 0.90
}
```

Adopt Claude-Mem's progressive disclosure:
```python
class EnhancedLTM:
    def search_memory(self, query: str, budget: int = 100):
        """Step 1: Compact index with IDs"""
        return self.db.fts5_search(query, limit=5)  # ~50 tokens
    
    def get_timeline(self, observation_id: str, window: int = 10):
        """Step 2: Chronological context around match"""
        return self.db.timeline_around(observation_id, window)  # ~100 tokens
    
    def get_observations(self, ids: List[str]):
        """Step 3: Full details only for selected IDs"""
        return self.db.get_by_id(ids)  # ~500 tokens each
```

#### B. Storage Layer Integration

**Current:**
- `memories/cvc_state.json` - CVC 4-state machine
- `memories/ltm_profiles.json` - TSPA + EBDI
- `memories/genesis_record.jsonl` - Audit trail

**Proposed (Claude-Mem style):**
```
memories/
├── cvc_state.json           (existing)
├── ltm_profiles.json        (existing)
├── genesis_record.jsonl     (existing)
├── observations/            (NEW - Claude-Mem style)
│   ├── metadata.db          SQLite with FTS5
│   ├── embeddings/          Chroma vector DB
│   └── cache/               Dedup + compress
└── search/                  (NEW - MCP interface)
    ├── mcp_server.py        3-layer search
    └── web_viewer/          localhost:37777
```

#### C. MCP Endpoint: `claude-mem-mcp`

```python
@mcp_server.tool()
async def search_context(query: str, type_filter: str = None) -> SearchIndex:
    """Step 1: Search observations index"""
    return ltm_manager.search(query, type_filter)

@mcp_server.tool()
async def get_context_timeline(obs_id: str) -> TimelineView:
    """Step 2: Surrounding context"""
    return ltm_manager.timeline(obs_id)

@mcp_server.tool()
async def fetch_observations(ids: List[str]) -> ObservationList:
    """Step 3: Full details"""
    return ltm_manager.get_observations(ids)
```

#### D. n8n Workflow Integration

```json
{
  "nodes": [
    {
      "type": "mcp",
      "mcp_tool": "search_context",
      "query": "{{ $json.user_query }}",
      "type_filter": "bugfix"
    },
    {
      "type": "mcp",
      "mcp_tool": "get_context_timeline",
      "obs_id": "{{ $node.search.result[0].id }}"
    },
    {
      "type": "mcp",
      "mcp_tool": "fetch_observations",
      "ids": "{{ $node.timeline.result.relevant_ids }}"
    }
  ]
}
```

### 3.4 Cost-Benefit Analysis

| Benefit | Impact |
|---------|--------|
| **Cross-session continuity** | Users don't lose context on new conversation |
| **Progressive disclosure** | 10x token savings vs fetching all observations |
| **Vector search** | Semantic retrieval beyond keyword match |
| **Web viewer** | Real-time memory inspection for debugging |
| **Audit compliance** | FTS5 + chronological view satisfies compliance |

**Cost:** Adds ~100MB SQLite + Chroma embeddings per 1000 sessions (acceptable)

---

## 4. Glif MCP Server: Workflow Orchestration

### 4.1 Repository Analysis

**GitHub:** https://github.com/glifxyz/glif-mcp-server  
**Stars:** 119 | **Forks:** 23 | **License:** MIT  
**Status:** Active, ~3-month release cadence

#### Capabilities:
```
glif.app Platform
├── Workflow Execution      → Run AI workflows with inputs
├── Agent Management        → Load + orchestrate agents
├── Search & Discovery      → Find workflows by intent
└── Multi-Model Support     → Image gen, video, code, etc.
```

### 4.2 ADRION Use Cases

#### A. Workflow Instance 1: "Bugfix Analysis"
```
Trigger: Guardian denies code modification
  ↓
Glif Workflow 1: "Analyze Potential Bug"
  - Input: Code snippet + error
  - Steps:
    1. Analyze symptom (claude-3-opus)
    2. Search similar issues (perplexity)
    3. Generate fix proposal (claude-code)
  - Output: Structured analysis
  ↓
Guardian re-evaluates with analysis context
```

#### B. Workflow Instance 2: "Context Enrichment"
```
Trigger: User asks question, LTM search returns vague results
  ↓
Glif Workflow 2: "Fetch Rich Context"
  - Input: Observation ID + query
  - Steps:
    1. Get timeline (claude-mem MCP)
    2. Expand with web research (perplexity)
    3. Generate summary (sonar-research-pro)
  - Output: Rich context for Guardian evaluation
  ↓
Re-inject into conversation
```

### 4.3 Implementation in Phase 5

**Timeline:** Post-Kubernetes (Phase 6)

```python
# mcp_servers/glif_orchestrator.py
class GlifOrchestrator(MCPServer):
    """Workflow execution for complex ADRION tasks"""
    
    async def run_workflow(self, workflow_id: str, inputs: dict) -> WorkflowResult:
        """Execute glif.app workflow and return result"""
        # 1. Authenticate with Glif API
        # 2. Queue workflow execution
        # 3. Stream results back via MCP
        # 4. Log to Genesis Record
        pass
```

### 4.4 n8n Integration

```json
{
  "nodes": [
    {
      "type": "mcp",
      "mcp_server": "glif-orchestrator",
      "mcp_tool": "run_workflow",
      "workflow_id": "bugfix-analyzer",
      "inputs": {
        "code": "{{ $json.code }}",
        "error": "{{ $json.error }}"
      }
    }
  ]
}
```

---

## 5. Graphify: Knowledge Graph Visualization

### 5.1 Repository Analysis

**GitHub:** https://github.com/safishamsi/graphify  
**Stars:** 47k | **Forks:** 5.1k | **License:** MIT  
**Status:** Actively maintained, v0.7.15 (96 releases)

#### Architecture:
```
/graphify .
  ↓
┌─────────────────────────────────┐
│ AST Extraction (29 languages)   │  Local processing
├─────────────────────────────────┤
│ Semantic Clustering (Leiden)    │  Community detection
├─────────────────────────────────┤
│ Graph Construction              │
│  - Nodes: Code entities, docs   │
│  - Edges: Relationships         │
│  - Labels: Confidence scores    │
├─────────────────────────────────┤
│ Output Formats:                 │
│  - graph.html     (interactive) │
│  - GRAPH_REPORT.md (markdown)   │
│  - graph.json     (queryable)   │
│  - MCP server     (real-time)   │
└─────────────────────────────────┘
```

### 5.2 ADRION Use Cases

#### A. Observability Layer: "Guardian Laws Map"
```
/graphify ./arbitrage

Output:
  ├── graph.html
  │   - Node: "Guardian.evaluate()"
  │   - Connected to: G1_Unity, G2_Autonomy, ... G11_RelationalCare
  │   - Edges show which laws block which code paths
  │
  ├── GRAPH_REPORT.md
  │   - "God nodes": Guardian.evaluate (most connected)
  │   - "Surprising connections": CVC state affects TSPA scores indirectly
  │   - Suggested queries: "What blocks authentication modification?"
  │
  └── graph.json
      - Query: "Show all laws affecting memory layer"
```

#### B. Real-time MCP Server
```python
# python -m graphify.serve graphify-out/graph.json

# Then MCP tools:
@mcp.tool()
def query_graph(question: str) -> QueryResult:
    """Query ADRION architecture graph"""
    # Example: "Which laws affect the LTM memory layer?"
    # Returns: [G11_RelationalCare, G2_Autonomy] + edge weights

@mcp.tool()
def get_node_details(entity: str) -> NodeInfo:
    """Get code + docs for a given node"""
    # Example: "Guardian.G10_Evolution"
    # Returns: Source code + inline docstrings + tests
```

### 5.3 Integration Strategy (Phase 5B)

```bash
# Generate ADRION architecture graph
/graphify ./arbitrage \
  --directed \          # Preserve call-flow direction
  --mode deep \         # Aggressive relationship extraction
  --export callflow-html # Generate architecture diagrams

# Output: docs/ADRION_369_Architecture.html
# Features:
#   - Interactive call flows (Guardian → Laws → CVC → Genesis)
#   - Hover details on each component
#   - Filter by subsystem (Memory, Guardian, Metrics)
```

### 5.4 Observability Benefits

| Metric | Current | With Graphify |
|--------|---------|---------------|
| **Time to understand Guardian Laws** | Manual code review (30 min) | Graph query (30 sec) |
| **Spot missing links** | Code inspection | Graphify identifies orphaned nodes |
| **Impact analysis** | Grep dependencies | Graph traversal (shortest path) |
| **Documentation** | Outdated READMEs | Always-fresh from live code |

---

## 6. Missing Repositories Analysis

### 6.1 Firecrawl (Web Scraping)
**GitHub:** https://github.com/firecrawl/firecrawl-mcp-server  
**Status:** Could not fetch (repo may be private/archived)

**Alternative:** Use Perplexity Search API for most use cases

### 6.2 jcode & gstack
**Status:** Not accessible or not relevant to ADRION scope

---

## 7. Integration Timeline & Roadmap

### Phase 5A: Kubernetes + CI/CD (Current)
- ✅ Maintain MCP servers (6 live)
- 🟡 Plan Perplexity MCP gateway
- 🟡 Prepare Claude-Mem integration

### Phase 5B: Enhanced Memory & Web Context (Weeks 3-4)
- **Week 3:**
  - [ ] Implement Perplexity MCP server (`adrion-perplexity-gateway`)
  - [ ] Wire into Guardian v12 evaluation pipeline
  - [ ] Add web-context tests
  
- **Week 4:**
  - [ ] Implement Claude-Mem style LTM search
  - [ ] Add FTS5 + vector search to memory layer
  - [ ] Create web viewer UI (localhost:37777)

### Phase 5C: Workflow Orchestration (Weeks 5-6)
- **Week 5:**
  - [ ] Create `glif_orchestrator.py` MCP server
  - [ ] Design Glif workflow templates
  - [ ] Integrate with n8n

### Phase 6: Observability & Architecture Visualization (Weeks 7-8)
- **Week 7:**
  - [ ] Generate Graphify knowledge graph
  - [ ] Create interactive HTML visualization
  - [ ] Wire MCP graph query tools

---

## 8. Implementation Checklist

### Immediate (Next Sprint)
- [ ] Review MCP Python SDK current version compatibility
- [ ] Create `mcp_servers/` subdirectory structure
- [ ] Document MCP server lifecycle (startup, health checks, graceful shutdown)

### Short Term (2-4 Weeks)
- [ ] Implement Perplexity MCP gateway + tests
- [ ] Wire Perplexity into Guardian evaluation flow
- [ ] Update n8n workflow templates for web-context usage

### Medium Term (1-2 Months)
- [ ] Migrate LTM to SQLite + Chroma (Claude-Mem pattern)
- [ ] Implement 3-layer search MCP tools
- [ ] Add web viewer UI for memory inspection

### Long Term (2-3 Months)
- [ ] Glif workflow orchestration MCP server
- [ ] Graphify knowledge graph generation
- [ ] Production deployment with observability

---

## 9. Security & Compliance Considerations

### 9.1 Perplexity Integration
- **Data:** Queries sent externally → Implement PII scrubbing
- **Trust:** Add confidence scores based on source freshness
- **Audit:** Tag external sources in Genesis Record

### 9.2 Claude-Mem Integration
- **Storage:** Sensitive data encrypted at rest
- **Access:** Query sanitization to prevent injection
- **Compliance:** Retention policies aligned with data protection

### 9.3 MCP Server Security
- **Isolation:** Run each MCP server in isolated process
- **Timeout:** Set per-tool timeout to prevent hanging
- **Rate Limits:** Implement per-client rate limiting
- **Audit:** All MCP invocations logged to Genesis Record

---

## 10. Success Metrics

### Knowledge Layer (Perplexity)
- [ ] Guardian v12 has web-context-aware G4_Truthfulness evaluation
- [ ] 90%+ accuracy on fact-checking tasks
- [ ] < 500ms latency for web search + reasoning

### Memory Layer (Claude-Mem)
- [ ] Cross-session context recovery working
- [ ] 10x token savings via 3-layer search
- [ ] Vector search finding semantically similar observations

### Workflow Layer (Glif)
- [ ] 5+ workflow templates available
- [ ] n8n integration tested end-to-end
- [ ] Bugfix analysis workflow reduces manual analysis time by 50%

### Observability Layer (Graphify)
- [ ] Architecture graph generated automatically
- [ ] Graph queries answer 90%+ of "what connects X to Y" questions
- [ ] Interactive visualization accessible via web browser

---

## 11. Conclusion & Recommendations

**Priority 1 (Critical):** Keep MCP server foundation + Kubernetes deployment  
**Priority 2 (High):** Implement Perplexity MCP for real-time context  
**Priority 3 (High):** Migrate LTM to Claude-Mem pattern for cross-session memory  
**Priority 4 (Medium):** Add Glif workflow orchestration for complex tasks  
**Priority 5 (Medium):** Deploy Graphify for architecture visualization  

**Strategic Value:** Integrate all 5 ecosystems = production-grade AI agent platform with enterprise-level observability, memory, and knowledge capabilities.

---

**Document Generated:** 2026-05-12  
**ADRION 369 Version:** 5.3  
**Ecosystem Status:** Analyzed 5/10 repos (3 unavailable/not-applicable)  
**Next Review:** Post-Phase 5A Kubernetes deployment

---

## Appendix A: Repository Comparison Matrix

| Repo | Stars | Activity | Maturity | Licensing | Integration Effort |
|------|-------|----------|----------|-----------|-------------------|
| MCP Servers | 85.5k | Very High | ⭐⭐⭐⭐⭐ | Apache/MIT | Already Live |
| Perplexity MCP | 2.2k | High | ⭐⭐⭐⭐ | MIT | 2-3 days |
| Claude-Mem | 75.1k | Very High | ⭐⭐⭐⭐⭐ | Apache 2.0 | 3-5 days |
| Glif MCP | 119 | Medium | ⭐⭐⭐⭐ | MIT | 1-2 weeks |
| Graphify | 47k | Very High | ⭐⭐⭐⭐⭐ | MIT | 2-3 days |

---

## Appendix B: Cost Estimates (Monthly)

| Service | Usage | Cost |
|---------|-------|------|
| Perplexity Sonar Pro | 50-100 queries/day | $15-30 |
| Claude-Mem (local) | ~100MB storage | $0 |
| Glif Workflows | 10-20/day | ~$10-20 |
| Graphify (local) | ~200MB graph | $0 |
| **Total Monthly** | - | **~$25-50** |

---

**END OF DOCUMENT**
