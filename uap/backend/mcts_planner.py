"""
Unified Admin Panel (UAP) — Graph-of-Thoughts (GoT) with MCTS
Monte Carlo Tree Search for task execution planning

Implements Drafting step with node exploration, backpropagation, UCT
"""
import sys
import math
import random
import json
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))
from db import get_db

@dataclass
class MCTSNode:
    """Monte Carlo Tree Search node."""
    node_id: str
    action: str  # e.g., "analyze", "scout", "heal"
    parent_id: Optional[str] = None
    children_ids: List[str] = None
    visits: int = 0
    reward: float = 0.0
    depth: int = 0
    guardian_laws_violations: int = 0  # Number of laws violated

    def __post_init__(self):
        if self.children_ids is None:
            self.children_ids = []

    def uct(self, parent_visits: int, exploration_constant: float = 1.41) -> float:
        """
        Calculate Upper Confidence Bound for Trees (UCT).
        UCT = exploitation + exploration
        """
        if self.visits == 0:
            return float('inf')

        exploitation = self.reward / self.visits
        exploration = exploration_constant * math.sqrt(math.log(parent_visits) / self.visits)
        return exploitation + exploration


class MCTSPlanner:
    """Graph-of-Thoughts planner using Monte Carlo Tree Search."""

    def __init__(self, depth_limit: int = 5):
        self.db = get_db()
        self.depth_limit = depth_limit
        self.nodes: Dict[str, MCTSNode] = {}
        self.root_node: Optional[MCTSNode] = None
        self.node_counter = 0

    def generate_node_id(self) -> str:
        """Generate unique node ID."""
        self.node_counter += 1
        return f"n-{self.node_counter}"

    def create_root_node(self, task_description: str) -> MCTSNode:
        """Create root node for task."""
        node = MCTSNode(
            node_id=self.generate_node_id(),
            action=f"root: {task_description[:50]}",
            depth=0
        )
        self.nodes[node.node_id] = node
        self.root_node = node
        return node

    def expand_node(self, parent_node: MCTSNode, possible_actions: List[str]) -> MCTSNode:
        """
        Expand parent node by creating a child node.
        MCTS Phase 1: Selection/Expansion
        """
        if len(parent_node.children_ids) >= len(possible_actions):
            return parent_node  # Already expanded

        action = possible_actions[len(parent_node.children_ids)]
        child = MCTSNode(
            node_id=self.generate_node_id(),
            action=action,
            parent_id=parent_node.node_id,
            depth=parent_node.depth + 1
        )

        parent_node.children_ids.append(child.node_id)
        self.nodes[child.node_id] = child
        return child

    def simulate(self, node: MCTSNode) -> float:
        """
        Simulate random playouts from node.
        MCTS Phase 2: Simulation
        Returns reward in [0, 1]
        """
        reward = 1.0

        # Penalty for violations
        reward -= node.guardian_laws_violations * 0.15

        # Reward for useful actions
        if "optimize" in node.action.lower():
            reward += 0.1
        if "validate" in node.action.lower():
            reward += 0.15
        if "heal" in node.action.lower():
            reward += 0.05

        # Penalty for risky actions
        if "reset" in node.action.lower() or "delete" in node.action.lower():
            reward -= 0.3

        return max(0.0, min(1.0, reward))

    def backpropagate(self, node: MCTSNode, reward: float):
        """
        Backpropagate reward upward through tree.
        MCTS Phase 3: Backpropagation
        """
        current = node
        while current:
            current.visits += 1
            current.reward += reward
            if current.parent_id:
                current = self.nodes.get(current.parent_id)
            else:
                break

    def best_child(self, parent: MCTSNode, exploration: float = 1.41) -> Optional[MCTSNode]:
        """Select best child using UCT."""
        if not parent.children_ids:
            return None

        children = [self.nodes[cid] for cid in parent.children_ids if cid in self.nodes]
        return max(children, key=lambda c: c.uct(parent.visits, exploration))

    def tree_policy(self) -> MCTSNode:
        """
        Tree policy: selection & expansion.
        Navigate tree using UCT until reaching expandable node.
        """
        node = self.root_node

        while node and node.depth < self.depth_limit:
            children_count = len(node.children_ids)

            if children_count < 3:  # Node is expandable
                action = ["analyze", "scout", "validate", "optimize"][children_count]
                return self.expand_node(node, ["analyze", "scout", "validate", "optimize"])

            best = self.best_child(node)
            if best:
                node = best
            else:
                break

        return node

    def plan_task(self, task_description: str, agent: str, iterations: int = 100) -> List[Dict[str, Any]]:
        """
        Plan task using MCTS.

        Returns: List of action nodes in execution order
        """
        # Create root
        root = self.create_root_node(task_description)

        # Run MCTS iterations
        for _ in range(iterations):
            # 1. Tree policy
            leaf = self.tree_policy()

            # 2. Simulate
            reward = self.simulate(leaf)

            # 3. Backpropagate
            self.backpropagate(leaf, reward)

        # Extract best path (exploitation only, exploration=0)
        best_path = []
        current = root

        while current and len(best_path) < self.depth_limit:
            if current.node_id != root.node_id:
                best_path.append({
                    "action": current.action,
                    "reward": current.reward / max(1, current.visits),
                    "visits": current.visits,
                    "feasibility": 1.0 - (current.guardian_laws_violations * 0.2),
                })

            next_child = self.best_child(current, exploration=0)  # Pure exploitation
            if next_child:
                current = next_child
            else:
                break

        return best_path

    def tree_to_json(self) -> Dict[str, Any]:
        """Export tree as JSON for visualization."""
        def node_to_dict(node_id: str) -> Dict:
            node = self.nodes.get(node_id)
            if not node:
                return {}

            return {
                "id": node.node_id,
                "action": node.action,
                "visits": node.visits,
                "reward": node.reward,
                "uct": node.uct(self.root_node.visits) if self.root_node else 0,
                "depth": node.depth,
                "children": [node_to_dict(cid) for cid in node.children_ids],
            }

        return node_to_dict(self.root_node.node_id) if self.root_node else {}

    def export_plan(self, task_id: str, plan: List[Dict[str, Any]]) -> bool:
        """Export plan to Genesis Record."""
        try:
            # Log plan to Genesis
            for i, action in enumerate(plan):
                notes = f"Plan step {i+1}: {action['action']}, Feasibility: {action['feasibility']:.2f}"
                self.db.insert_genesis_log(
                    task_id=task_id,
                    agent="Master",
                    status="planned",
                    action="MCTS_plan_step",
                    guards_passed=9,
                    notes=notes
                )
            return True
        except Exception as e:
            print(f"❌ Error exporting plan: {e}")
            return False


# Singleton instance
_planner = None

def get_planner() -> MCTSPlanner:
    global _planner
    if _planner is None:
        _planner = MCTSPlanner()
    return _planner
