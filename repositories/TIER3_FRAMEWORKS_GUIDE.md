# TIER 3: LLM FRAMEWORKS + STATE MANAGEMENT GUIDE

## 📚 Contents (3 Repositories)

1. **LangChain + LangGraph** (⭐ 133k + 28.9k) — State management backbone
2. **GenAI_Agents** (⭐ 21.1k) — Learning patterns
3. **AgentOps** (⭐ 5.4k) — Agent monitoring

---

## 🎯 ADRION 369 Integration Points

### LangGraph State Machine for Trinity→Hexagon→Guardians

```python
from langgraph.graph import StateGraph
from typing import TypedDict, Any

class DecisionState(TypedDict):
    """Complete decision state tracking"""
    # Trinity layer
    trinity_scores: dict  # {material, intellectual, essential, overall}

    # Hexagon layer
    hexagon_stage: int    # 0-5 (Inventory→Action)
    stage_results: list   # Results from each stage

    # Guardian layer
    guardian_evaluations: dict  # {law: {passed, score, reason}}
    guardian_violations: int    # Count of violations

    # Metadata
    job_context: dict
    decision_history: list
    timestamp: str

# Build the state graph
graph = StateGraph(DecisionState)

# NODE 1: Trinity Evaluation
def trinity_node(state: DecisionState) -> DecisionState:
    """Parallel evaluation of 3 perspectives"""
    material_score = evaluate_material(state["job_context"])
    intellectual_score = evaluate_intellectual(state["job_context"])
    essential_score = evaluate_essential(state["job_context"])

    trinity = {
        "material": material_score,
        "intellectual": intellectual_score,
        "essential": essential_score,
        "overall": (material_score * intellectual_score * essential_score) ** (1/3),
    }

    return {
        **state,
        "trinity_scores": trinity,
    }

# NODES 2-7: Hexagon Stages
def inventory_node(state: DecisionState) -> DecisionState:
    result = inventory_stage(state)
    return {**state, "hexagon_stage": 0, "stage_results": [*state["stage_results"], result]}

def empathy_node(state: DecisionState) -> DecisionState:
    result = empathy_stage(state)
    return {**state, "hexagon_stage": 1, "stage_results": [*state["stage_results"], result]}

# ... process, debate, healing, action nodes ...

# NODE 8: Guardian Laws Evaluation
def guardians_node(state: DecisionState) -> DecisionState:
    evaluations = {}
    violations = 0

    for law_name, law_rule in GUARDIAN_LAWS.items():
        result = law_rule.evaluate(state)
        evaluations[law_name] = result
        if not result["passed"]:
            violations += 1

    return {
        **state,
        "guardian_evaluations": evaluations,
        "guardian_violations": violations,
    }

# Build graph
graph.add_node("trinity", trinity_node)
graph.add_node("inventory", inventory_node)
graph.add_node("empathy", empathy_node)
graph.add_node("process", process_node)
graph.add_node("debate", debate_node)
graph.add_node("healing", healing_node)
graph.add_node("action", action_node)
graph.add_node("guardians", guardians_node)

# Connect edges (Trinity → Hexagon → Guardians)
graph.add_edge("trinity", "inventory")
graph.add_edge("inventory", "empathy")
graph.add_edge("empathy", "process")
graph.add_edge("process", "debate")
graph.add_edge("debate", "healing")
graph.add_edge("healing", "action")
graph.add_edge("action", "guardians")
graph.add_edge("guardians", END)

# Add conditional edge for Guardian violations
def should_deny(state: DecisionState) -> str:
    if state["guardian_violations"] >= 2:
        return "DENY"
    return "APPROVE"

graph.add_conditional_edges("guardians", should_deny)
graph.add_edge("DENY", END)
graph.add_edge("APPROVE", END)

# Compile
decision_graph = graph.compile()
```

### LangChain Tool Calling for Guardian Laws

```python
from langchain.tools import tool
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain import ChatOpenAI

# Define Guardian Laws as Tools
@tool
def evaluate_unity_law(context: dict) -> dict:
    """Evaluate Unity (interconnectedness) law"""
    # Check if decision respects all stakeholders
    passed = check_unity(context)
    return {"law": "Unity", "passed": passed, "reason": "..."}

@tool
def evaluate_truth_law(context: dict) -> dict:
    """Evaluate Truth (transparency) law"""
    passed = check_truth_requirement(context)
    return {"law": "Truth", "passed": passed, "reason": "..."}

# ... more tools for each law ...

tools = [
    evaluate_unity_law,
    evaluate_truth_law,
    evaluate_rhythm_law,
    # ... all 9 laws
]

# Create agent
llm = ChatOpenAI(model="gpt-4")
agent = create_tool_calling_agent(llm, tools, prompt)

# Execute
executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
result = executor.invoke({"input": json.dumps(decision_context)})
```

### GenAI_Agents Learning Patterns

```python
# From GenAI_Agents notebooks - applicable patterns:

# 1. Multi-agent collaboration pattern
class MultiAgentDecisionSystem:
    def __init__(self):
        self.trinity_agents = [material_agent, intellectual_agent, essential_agent]
        self.hexagon_agents = [inventory_agent, empathy_agent, ...]
        self.guardian_agents = [law1_agent, law2_agent, ...]

    def execute(self):
        # Parallel Trinity
        trinity_results = asyncio.gather(*[
            agent.run(job) for agent in self.trinity_agents
        ])

        # Sequential Hexagon
        hexagon_results = []
        state = trinity_results
        for agent in self.hexagon_agents:
            result = agent.run(state)
            hexagon_results.append(result)

        # Guardian validation
        guardian_results = asyncio.gather(*[
            agent.run(state) for agent in self.guardian_agents
        ])

# 2. Feedback loop pattern (for decision refinement)
class RefinementLoop:
    def __init__(self, max_iterations=3):
        self.max_iterations = max_iterations

    def refine_decision(self, initial_decision):
        decision = initial_decision
        for i in range(self.max_iterations):
            # Evaluate
            feedback = self._evaluate(decision)

            # Refine based on feedback
            if feedback["needs_refinement"]:
                decision = self._refine(decision, feedback)
            else:
                break

        return decision
```

### AgentOps Monitoring Integration

```python
import agentops

# Decorate Trinity evaluation
@agentops.track()
def evaluate_trinity(job, analysis):
    # AgentOps automatically tracks:
    # - Function execution time
    # - Token usage (LLM calls)
    # - Agent interactions
    # - Cost tracking

    material_score = evaluate_material(job, analysis)
    intellectual_score = evaluate_intellectual(job, analysis)
    essential_score = evaluate_essential(job, analysis)

    return {
        "material": material_score,
        "intellectual": intellectual_score,
        "essential": essential_score,
    }

# Custom events
agentops.log_action(
    action_type="trinity_evaluation",
    details={
        "material": 0.8,
        "intellectual": 0.7,
        "essential": 0.9,
    }
)

# Dashboard: agentops.com — see real-time metrics
agentops.init(api_key="your_api_key")
```

---

## 🚀 Quick Start (8-12 hours)

### Installation

```bash
cd repositories/tier3-frameworks

# LangChain + LangGraph
cd langchain
pip install -e ".[langgraph]"
pip install langgraph
cd ..

# GenAI_Agents (notebooks)
cd GenAI_Agents
pip install -r requirements.txt
# Open notebooks for learning
jupyter notebook
cd ..

# AgentOps
cd agentops
pip install -e .
cd ..
```

### POC: Replace HexagonProcessor with LangGraph

**Before (current):**

```python
class HexagonProcessor:
    def process(self, trinity_scores):
        self.trinity = trinity_scores
        self.inventory_result = self.inventory_stage()
        self.empathy_result = self.empathy_stage()
        # ... all 6 stages sequentially
```

**After (LangGraph):**

```python
from langgraph.graph import StateGraph

graph = StateGraph(DecisionState)
# Add nodes + edges (see above)
decision_graph = graph.compile()

# Execute
result = decision_graph.invoke({
    "job_context": job,
    "trinity_scores": trinity_scores,
    "hexagon_stage": 0,
    "stage_results": [],
})
```

### Test State Persistence

```python
# State is automatically persisted
graph = decision_graph.compile(
    store=InMemoryStore()  # Can use PostgreSQL: PostgresStore
)

# Recover state after crash
state = store.get("decision_123")  # Retrieve saved state
```

---

## 📋 Integration Checklist

- [ ] LangChain + LangGraph installed
- [ ] DecisionState TypedDict defined
- [ ] StateGraph with 8 nodes + edges created
- [ ] Trinity → Inventory → Empathy → Process → Debate → Healing → Action → Guardians flow verified
- [ ] Guardian Laws as Tool Calling agents (optional)
- [ ] GenAI_Agents notebooks reviewed for patterns
- [ ] AgentOps dashboard integrated
- [ ] Performance benchmarked (state graph latency vs current)
- [ ] Tests written for state transitions
- [ ] Genesis Record updated with state history

---

## 🔗 Key References

- **LangGraph Docs:** https://python.langchain.com/docs/langgraph/
- **StateGraph Tutorial:** https://python.langchain.com/docs/langgraph/how-tos/map-state
- **Tool Calling:** https://python.langchain.com/docs/langgraph/how-tos/tool-calling
- **GenAI Notebooks:** https://github.com/NirDiamant/GenAI_Agents/tree/main/notebooks
- **AgentOps:** https://docs.agentops.ai/

---

## 🎯 Expected Outcomes

- ✅ Complete state tracking (Trinity → Hexagon → Guardians)
- ✅ Automatic persistence (state recovery on crash)
- ✅ Observable decision pipeline (LangSmith integration)
- ✅ Scalable to 100k+ concurrent decisions (LangGraph supports it)
- ✅ Monitoring dashboard (AgentOps)

---

**Integration Time:** 8-12 hours
**Difficulty:** ⭐⭐⭐ (Medium to Hard)
**Priority:** 🟡 IMPORTANT
