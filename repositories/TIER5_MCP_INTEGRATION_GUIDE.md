# TIER 5: MODEL CONTEXT PROTOCOL (MCP) INTEGRATION GUIDE

## 📚 Repository

- **URL:** https://github.com/modelcontextprotocol/servers
- **Stars:** Growing rapidly (new standard from Anthropic)
- **Language:** Python, TypeScript, Rust
- **Status:** Official Anthropic spec

---

## 🎯 WHY MCP FOR ADRION 369?

### What is MCP?
Model Context Protocol is a **standardized interface** for connecting AI models to tools, data sources, and services. Think of it as a "universal adapter" for Claude to interact with anything.

### Benefits for ADRION 369
1. **Standardized Tool Integration** — Replace ad-hoc tool implementations with MCP spec
2. **Agent Capability Extension** — Add new tools without modifying core agent code
3. **Claude Native** — First-class support for Claude models
4. **Extensibility** — Easy to add monitoring, databases, APIs, etc.

---

## 🏗️ ADRION 369 MCP Architecture

```
┌─────────────────────────────────────────────────────┐
│  ADRION 369 Core (CrewAI + LangGraph)               │
├─────────────────────────────────────────────────────┤
│                                                      │
│  Trinity Crew ──┐                                   │
│  Hexagon Flow ──┼──> MCP Hub ──> Tools & Resources │
│  Guardians Eval─┘                                   │
│                                                      │
└─────────────────────────────────────────────────────┘
        ↓                              ↓
    Claude API            MCP Servers (standardized)
                          ├── PostgreSQL (genesis_record)
                          ├── Redis (AI-Binder IPC)
                          ├── Ollama (LLM bridge)
                          ├── Prometheus (metrics)
                          ├── File System (documents)
                          └── Custom Tools (Trinity perspectives)
```

---

## 🚀 MCP SERVERS FOR ADRION 369

### Available MCP Servers (from official repo):

1. **PostgreSQL Server** — Query genesis_record directly
2. **Redis Server** — Access AI-Binder IPC layer
3. **Filesystem Server** — Read/write documents for RAG
4. **GitHub Server** — Integration with version control
5. **Slack Server** — Notification & logging
6. **HTTP Client Server** — Call external APIs
7. **SQLite Server** — Local data queries
8. **AWS Services** — S3, DynamoDB access (if cloud)

### Custom MCP Servers to Build

```python
# mcp_trinity_server.py - Trinity perspectives as MCP

from mcp.server import Server
from mcp.types import Tool, TextContent

server = Server("trinity-perspectives")

@server.tool()
def evaluate_material(context: dict) -> dict:
    """MCP Tool: Material perspective scoring"""
    from arbitrage.trinity import _score_material
    return {"score": _score_material(context)}

@server.tool()
def evaluate_intellectual(context: dict) -> dict:
    """MCP Tool: Intellectual perspective with RAG"""
    from arbitrage.trinity import _score_intellectual
    return {"score": _score_intellectual(context)}

@server.tool()
def evaluate_essential(context: dict) -> dict:
    """MCP Tool: Essential perspective scoring"""
    from arbitrage.trinity import _score_essential
    return {"score": _score_essential(context)}

# Custom: Guardian Laws validator
@server.tool()
def validate_guardian_laws(decision: dict) -> dict:
    """MCP Tool: Validate decision against all 9 Guardian Laws"""
    from arbitrage.guardian import evaluate_guardians
    return evaluate_guardians(decision)

@server.tool()
def get_genesis_record(query: str, limit: int = 10) -> list:
    """MCP Tool: Query immutable audit log"""
    from arbitrage.database import query_genesis_record
    return query_genesis_record(query, limit)
```

---

## 🔧 QUICK START: Setup MCP Server

### 1. Install MCP SDK

```bash
pip install mcp
```

### 2. Create MCP Server for ADRION

```python
# mcp_adrion_server.py

from mcp.server import Server
from mcp.types import Tool, TextContent, JSONValue
import asyncio

class ADRIONMCPServer:
    def __init__(self):
        self.server = Server("adrion-tools")
        self.setup_tools()
    
    def setup_tools(self):
        """Register all ADRION tools as MCP resources"""
        
        # Trinity evaluation tool
        self.server.tool(
            name="trinity_evaluate",
            description="Evaluate decision using Trinity framework",
            input_schema={
                "type": "object",
                "properties": {
                    "job": {"type": "object", "description": "Job to evaluate"},
                    "analysis": {"type": "object", "description": "Analysis context"}
                }
            }
        )(self._trinity_evaluate)
        
        # Guardian validation tool
        self.server.tool(
            name="guardian_validate",
            description="Validate decision against Guardian Laws",
            input_schema={
                "type": "object",
                "properties": {
                    "decision": {"type": "object"}
                }
            }
        )(self._guardian_validate)
        
        # Genesis Record query
        self.server.tool(
            name="query_audit_log",
            description="Query immutable audit log",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "days": {"type": "integer", "default": 30}
                }
            }
        )(self._query_audit_log)
    
    async def _trinity_evaluate(self, job: dict, analysis: dict) -> dict:
        """Tool: Trinity evaluation"""
        from arbitrage.trinity import evaluate_trinity
        return evaluate_trinity(job, analysis)
    
    async def _guardian_validate(self, decision: dict) -> dict:
        """Tool: Guardian validation"""
        from arbitrage.guardian import evaluate_guardians
        return evaluate_guardians(decision)
    
    async def _query_audit_log(self, query: str, days: int = 30) -> list:
        """Tool: Audit log query"""
        # TODO: implement
        pass
    
    async def run(self, stdio: bool = False):
        """Start MCP server"""
        if stdio:
            await self.server.run_stdio()
        else:
            await self.server.run_sse()

# Start server
if __name__ == "__main__":
    server = ADRIONMCPServer()
    asyncio.run(server.run(stdio=True))
```

### 3. Use MCP Server from CrewAI Agent

```python
# Use Trinity Evaluation via MCP

from crewai import Agent, Task

# MCP-enabled agent
trinity_agent = Agent(
    role="Trinity Evaluator",
    goal="Evaluate decisions using standardized Trinity framework",
    backstory="Expert AI with access to Trinity MCP tools",
    tools_mcp=[
        "mcp://adrion-tools/trinity_evaluate",
        "mcp://adrion-tools/guardian_validate",
    ],
    verbose=True,
)

# Task that uses MCP tools
trinity_task = Task(
    description="Evaluate this job decision",
    agent=trinity_agent,
    expected_output="Trinity scores (material, intellectual, essential) + Guardian validation",
)
```

---

## 📋 MCP Integration with Existing ADRION Components

### PostgreSQL MCP Server (genesis_record)

```python
# Query audit log via MCP

from mcp.client import ClientSession
from mcp.types import JSONValue

async def query_genesis_via_mcp(query: str):
    """Query genesis_record through MCP"""
    async with ClientSession("postgresql://localhost/genesis_record") as session:
        result = await session.call_tool(
            "postgresql_query",
            {
                "query": query,
                "limit": 100
            }
        )
        return result

# Example: Get all Guardian Law violations
result = await query_genesis_via_mcp("""
    SELECT decision_id, law_name, violation_reason
    FROM guardian_evaluations
    WHERE passed = FALSE
    ORDER BY timestamp DESC
    LIMIT 50
""")
```

### Redis MCP Server (AI-Binder IPC)

```python
# Access Redis IPC layer via MCP

async def publish_hexagon_event_via_mcp(stage: str, result: dict):
    """Publish Hexagon stage result through MCP"""
    async with ClientSession("redis://localhost:6379") as session:
        await session.call_tool(
            "redis_publish",
            {
                "channel": f"hexagon:{stage}:complete",
                "data": result
            }
        )
```

### Filesystem MCP Server (RAG Documents)

```python
# Access RAG documents via MCP

async def load_guardian_laws_via_mcp():
    """Load Guardian Laws PDF through MCP filesystem"""
    async with ClientSession("file:///data/documents") as session:
        result = await session.call_tool(
            "read_file",
            {"path": "GUARDIAN_LAWS_CANONICAL.json"}
        )
        return result
```

---

## 🔗 Roadmap: MCP Integration Phases

### Phase 1: Foundation (1-2 weeks)
- [ ] Install MCP SDK
- [ ] Create `mcp_adrion_server.py` with Trinity + Guardian tools
- [ ] Setup stdio transport
- [ ] Test MCP tools manually

### Phase 2: CrewAI Integration (1 week)
- [ ] Integrate MCP tools into CrewAI agents
- [ ] Update Trinity Crew to use MCP evaluation
- [ ] Update Guardian evaluator to use MCP validation
- [ ] Test end-to-end

### Phase 3: Data Access (1 week)
- [ ] Setup PostgreSQL MCP server (genesis_record)
- [ ] Setup Redis MCP server (AI-Binder)
- [ ] Allow agents to query audit log
- [ ] Allow agents to publish hexagon events

### Phase 4: Extended Ecosystem (1-2 weeks)
- [ ] GitHub MCP server (version control)
- [ ] Slack MCP server (notifications)
- [ ] HTTP Client MCP (external APIs)
- [ ] AWS S3 MCP (if cloud deployment)

---

## 📚 Resources

- **MCP Spec:** https://modelcontextprotocol.io/
- **MCP Servers Repo:** https://github.com/modelcontextprotocol/servers
- **Official Examples:** https://github.com/modelcontextprotocol/servers/tree/main/src
- **Claude MCP Guide:** https://claude.ai/help/mcp

---

## 🎯 Expected Benefits

### Before MCP (current)
```
Tools: Hardcoded in Python
Integration: One-off implementations
Scalability: Limited
Maintainability: Scattered across codebase
```

### After MCP
```
Tools: Standardized interface
Integration: Plug-and-play
Scalability: Unlimited (add tools without modifying core)
Maintainability: Centralized in MCP servers
```

---

## ⚡ Quick Example: Trinity via MCP

```python
# Before (direct)
from arbitrage.trinity import evaluate_trinity
score = evaluate_trinity(job, analysis)

# After (MCP)
async with ClientSession("mcp://adrion-tools") as session:
    score = await session.call_tool("trinity_evaluate", {
        "job": job,
        "analysis": analysis
    })
```

**Result:** Same output, standardized interface, extensible architecture.

---

**Integration Time:** 1-2 weeks  
**Difficulty:** ⭐⭐⭐ (Medium to Hard)  
**Priority:** 🟢 NICE-TO-HAVE (but highly recommended for future scalability)  
**Future ROI:** ⭐⭐⭐⭐⭐ (Major — enables ecosystem)

