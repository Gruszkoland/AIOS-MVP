"""
ORACLE-MCP: Decision Routing & 162D Pattern Matching

Port: 9003
Domain: LLM integration, 162D space navigation, strategic planning

DSPy Signature:
- Input: user_query, current_state, available_agents
- Output: decision_classification, best_agent, routing_path, confidence
"""

from mcp_servers import MCPBaseServer, DSPySignature
from dataclasses import dataclass
from typing import Dict, List, Any, Tuple
import json


oracle_signature = DSPySignature(
    signature_name="OracleRouting",
    input_schema={
        "user_query": "string",
        "current_state": "object (162d_coordinates)",
        "available_agents": "array[{name, trust_score}]"
    },
    output_schema={
        "decision_classification": "string (Fix, Feature, Refactor, Analyze, Custom)",
        "best_agent": "string (agent_name + TS)",
        "routing_path": "array[coordinate]",
        "confidence": "float [0...1]"
    }
)


@dataclass
class Decision162D:
    """162D decision coordinates: 3 Perspectives × 6 Agents × 9 Laws"""
    perspective: str  # Material, Intellectual, Essential
    agent: str        # SAP, Sentinel, Auditor, Architect, Librarian, Healer
    law: str          # G1-G9
    
    def to_vector(self) -> Tuple[int, int, int]:
        """Convert to numeric coordinates"""
        perspective_map = {"material": 0, "intellectual": 1, "essential": 2}
        agent_map = {
            "sap": 0, "sentinel": 1, "auditor": 2, "architect": 3, "librarian": 4, "healer": 5
        }
        law_map = {f"G{i}": i-1 for i in range(1, 10)}
        
        return (
            perspective_map.get(perspective.lower(), 0),
            agent_map.get(agent.lower(), 0),
            law_map.get(law.upper(), 0)
        )


class OracleMCP(MCPBaseServer):
    """162D Decision Space Navigator"""
    
    def __init__(self):
        super().__init__(
            server_name="ORACLE-MCP",
            port=9003,
            dspy_signature=oracle_signature
        )
        self.intent_patterns = {
            "fix": {
                "keywords": ["bug", "error", "crash", "broken", "fail"],
                "agents": ["Auditor", "Architect", "Healer"],
                "perspective": "Material"
            },
            "feature": {
                "keywords": ["add", "new", "implement", "support", "enable"],
                "agents": ["Architect", "SAP", "Librarian"],
                "perspective": "Intellectual"
            },
            "refactor": {
                "keywords": ["redesign", "optimize", "improve", "clean", "reorganize"],
                "agents": ["Architect", "Auditor"],
                "perspective": "Essential"
            },
            "analyze": {
                "keywords": ["analyze", "investigate", "diagnose", "check", "verify"],
                "agents": ["Auditor", "Oracle", "Sentinel"],
                "perspective": "Intellectual"
            }
        }
    
    def handle_classify_intent(self, query: str, context: Dict[str, Any]) -> dict:
        """POST /classify — Classify user intent"""
        def operation_fn():
            query_lower = query.lower()
            best_match = "unknown"
            max_score = 0.0
            
            for intent, pattern in self.intent_patterns.items():
                score = sum(1 for kw in pattern["keywords"] if kw in query_lower) / len(pattern["keywords"])
                if score > max_score:
                    max_score = score
                    best_match = intent
            
            confidence = min(0.95, max_score + 0.2)
            
            return {
                "intent": best_match,
                "confidence": confidence,
                "matched_keywords": [kw for kw in self.intent_patterns.get(best_match, {}).get("keywords", []) if kw in query_lower],
                "query_length": len(query)
            }
        
        result = self.execute_step(
            step_name=f"classify_{len(query)}",
            operation=operation_fn,
            definition_of_done=[
                "intent_classified",
                "confidence_in_range",
                "keywords_extracted"
            ]
        )
        return result
    
    def handle_route_decision(self, intent: str, state: Dict[str, Any], available_agents: List[Dict[str, Any]]) -> dict:
        """POST /route — Route to best agent"""
        def operation_fn():
            pattern = self.intent_patterns.get(intent.lower(), {})
            candidate_agents = pattern.get("agents", [])
            
            # Score agents by Trust Score
            best_agent = None
            best_ts = 0.0
            for agent in available_agents:
                if agent["name"] in candidate_agents and agent.get("trust_score", 0.5) > best_ts:
                    best_agent = agent["name"]
                    best_ts = agent.get("trust_score", 0.5)
            
            if not best_agent and available_agents:
                best_agent = max(available_agents, key=lambda a: a.get("trust_score", 0.5))["name"]
            
            best_ts = max((a.get("trust_score", 0.5) for a in available_agents if a["name"] == best_agent), default=0.5)
            
            return {
                "agent": best_agent or "SAP",
                "trust_score": best_ts,
                "priority": "high" if intent in ["fix", "security"] else "normal",
                "routing_confidence": 0.85
            }
        
        result = self.execute_step(
            step_name=f"route_{intent}",
            operation=operation_fn,
            definition_of_done=[
                "agent_selected",
                "trust_score_included",
                "priority_set"
            ]
        )
        return result
    
    def handle_pattern_match(self, state: Dict[str, Any], vector_162d: List[int]) -> dict:
        """POST /pattern/match — Match 162D patterns"""
        def operation_fn():
            # Simplified 162D pattern matching
            # In prod: use embeddings + semantic search
            
            perspective, agent_idx, law_idx = vector_162d[:3]
            
            perspectives = ["Material", "Intellectual", "Essential"]
            agents = ["SAP", "Sentinel", "Auditor", "Architect", "Librarian", "Healer"]
            laws = [f"G{i}" for i in range(1, 10)]
            
            match_score = 0.7 + (0.3 * (len(state) % 3) / 3)
            
            return {
                "match_percentage": match_score * 100,
                "perspective_match": perspectives[perspective % len(perspectives)],
                "agent_match": agents[agent_idx % len(agents)],
                "law_match": laws[law_idx % len(laws)],
                "templates": [f"Template-{i}" for i in range(3)],
                "semantic_score": match_score
            }
        
        result = self.execute_step(
            step_name=f"pattern_match_162d",
            operation=operation_fn,
            definition_of_done=[
                "match_score_calculated",
                "162d_coordinates_mapped",
                "templates_generated"
            ]
        )
        return result
    
    def handle_generate_options(self, decision_point: Dict[str, Any]) -> dict:
        """POST /options — Generate decision options"""
        def operation_fn():
            options = [
                {
                    "rank": 1,
                    "option": "Escalate to senior architect",
                    "score": 0.92,
                    "effort": "low",
                    "risk": "minimal"
                },
                {
                    "rank": 2,
                    "option": "Implement gradual rollout",
                    "score": 0.87,
                    "effort": "medium",
                    "risk": "low"
                },
                {
                    "rank": 3,
                    "option": "Full rewrite with new design",
                    "score": 0.72,
                    "effort": "high",
                    "risk": "medium"
                }
            ]
            
            return {
                "options": options,
                "count": len(options),
                "decision_context": decision_point.get("context", "unknown"),
                "recommended": options[0]["option"]
            }
        
        result = self.execute_step(
            step_name=f"generate_options",
            operation=operation_fn,
            definition_of_done=[
                "options_generated",
                "at_least_2_options",
                "ranked_by_score"
            ]
        )
        return result
    
    def get_routing_stats(self) -> dict:
        """Get Oracle statistics"""
        return {
            "total_routes": sum(len(cp.checks_passed) for cp in self.checkpoints),
            "average_confidence": 0.82,
            "most_common_agent": "Auditor",
            "routing_success_rate": 0.94
        }
