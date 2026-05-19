#!/usr/bin/env python3
"""
ADRION 369: Federated Learning Coordinator
Decentralized model training across agents.

Framework:
- Agents train locally on their own data (no data sharing)
- Agents send only gradients/weights back to coordinator
- Coordinator aggregates via FedAvg algorithm
- Loop back to agents with updated global model

Benefits:
- Privacy-preserving (raw data never leaves edge)
- Decentralized (agents work autonomously)
- Scalable (add more agents without central bottleneck)
"""

import sys
from typing import Dict, List, Tuple
import logging
import numpy as np
from dataclasses import dataclass
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)


@dataclass
class ModelWeights:
    """Container for model weights/gradients."""
    layer_name: str
    weights: np.ndarray
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class FederatedRoundStats:
    """Statistics for a federated training round."""
    round_num: int
    num_agents: int
    num_participants: int
    aggregation_method: str
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class FederatedLearningCoordinator:
    """
    Orchestrates federated learning across ADRION agents.

    Flow:
    1. Init: Send model v0 to all agents
    2. Local Training: Agents train on local data (independently)
    3. Gradient Collection: Agents compute ∇L and send to coordinator
    4. Aggregation: Coordinator averages gradients (FedAvg)
    5. Model Update: New model v1 = v0 - lr * avg_gradients
    6. Distribution: Send v1 to all agents for next round
    """

    def __init__(self,
                 num_agents: int = 6,
                 aggregation_method: str = "fedavg",
                 learning_rate: float = 0.01,
                 min_participation_rate: float = 0.5):
        """
        Initialize coordinator.

        Args:
            num_agents: Number of agents training
            aggregation_method: "fedavg" (default), "weighted_fedavg", "median"
            learning_rate: Global learning rate
            min_participation_rate: Min % agents required per round
        """
        self.num_agents = num_agents
        self.aggregation_method = aggregation_method
        self.learning_rate = learning_rate
        self.min_participation_rate = min_participation_rate

        # Global model (placeholder)
        self.global_model = self._init_model()

        # Agent state tracking
        self.agent_models = {i: self._init_model() for i in range(num_agents)}
        self.agent_data_sizes = {i: 1000 for i in range(num_agents)}  # Simulated

        # History
        self.round_history = []

        logger.info(f"FedLearning initialized: {num_agents} agents, {aggregation_method} aggregation")

    def _init_model(self) -> Dict[str, np.ndarray]:
        """Initialize model weights (simplified: 3 layers)."""
        return {
            "layer1": np.random.randn(100, 50),
            "layer2": np.random.randn(50, 20),
            "layer3": np.random.randn(20, 10),
        }

    def distribute_model(self, round_num: int):
        """
        Send current global model to all agents.
        (In production: send via gRPC/REST API)
        """
        for agent_id in range(self.num_agents):
            self.agent_models[agent_id] = {
                k: v.copy() for k, v in self.global_model.items()
            }
        logger.info(f"[Round {round_num}] Model distributed to {self.num_agents} agents")

    def collect_gradients(self, round_num: int) -> Dict[int, Dict]:
        """
        Collect gradients from agents after local training.
        (Simulated: in production, agents send real gradients)
        """
        gradients = {}
        participating = 0

        for agent_id in range(self.num_agents):
            # Simulation: compute gradient as random delta
            # In production: agent sends computed ∇L
            if np.random.random() > 0.2:  # 80% participation rate
                gradient = {}
                for layer_name in self.global_model.keys():
                    # Simulated gradient (small random perturbation)
                    gradient[layer_name] = np.random.randn(*self.global_model[layer_name].shape) * 0.01

                gradients[agent_id] = {
                    "gradient": gradient,
                    "data_size": self.agent_data_sizes[agent_id],
                    "timestamp": datetime.now()
                }
                participating += 1

        participation_rate = participating / self.num_agents

        if participation_rate < self.min_participation_rate:
            logger.warning(f"Low participation: {participation_rate:.0%}")

        logger.info(f"[Round {round_num}] Collected gradients from {participating}/{self.num_agents} agents")
        return gradients

    def aggregate_gradients(self, gradients: Dict[int, Dict]) -> Dict[str, np.ndarray]:
        """
        Aggregate gradients using specified method.

        Methods:
        - FedAvg: Simple averaging
        - Weighted: Weighted by agent data size
        - Median: Robust to outliers
        """
        if not gradients:
            logger.warning("No gradients to aggregate")
            return {}

        if self.aggregation_method == "fedavg":
            return self._fedavg(gradients)
        elif self.aggregation_method == "weighted_fedavg":
            return self._weighted_fedavg(gradients)
        elif self.aggregation_method == "median":
            return self._median(gradients)
        else:
            raise ValueError(f"Unknown aggregation: {self.aggregation_method}")

    def _fedavg(self, gradients: Dict[int, Dict]) -> Dict[str, np.ndarray]:
        """FedAvg: Simple averaging of gradients."""
        agent_ids = list(gradients.keys())

        # Average each layer
        avg_gradient = {}
        for layer_name in self.global_model.keys():
            layer_grads = [gradients[aid]["gradient"][layer_name] for aid in agent_ids]
            avg_gradient[layer_name] = np.mean(layer_grads, axis=0)

        return avg_gradient

    def _weighted_fedavg(self, gradients: Dict[int, Dict]) -> Dict[str, np.ndarray]:
        """Weighted FedAvg: weight by agent data size."""
        agent_ids = list(gradients.keys())

        # Compute weights
        total_data = sum(gradients[aid]["data_size"] for aid in agent_ids)
        weights = {aid: gradients[aid]["data_size"] / total_data for aid in agent_ids}

        # Weighted average
        avg_gradient = {}
        for layer_name in self.global_model.keys():
            layer_grads = [
                gradients[aid]["gradient"][layer_name] * weights[aid]
                for aid in agent_ids
            ]
            avg_gradient[layer_name] = np.sum(layer_grads, axis=0)

        return avg_gradient

    def _median(self, gradients: Dict[int, Dict]) -> Dict[str, np.ndarray]:
        """Robust aggregation using median (resistant to Byzantine agents)."""
        agent_ids = list(gradients.keys())

        # Median across agents
        avg_gradient = {}
        for layer_name in self.global_model.keys():
            layer_grads = np.array([
                gradients[aid]["gradient"][layer_name].flatten()
                for aid in agent_ids
            ])
            median = np.median(layer_grads, axis=0)
            avg_gradient[layer_name] = median.reshape(self.global_model[layer_name].shape)

        return avg_gradient

    def update_global_model(self, avg_gradient: Dict[str, np.ndarray]):
        """
        Update global model: model = model - lr * avg_gradient
        """
        for layer_name in self.global_model.keys():
            self.global_model[layer_name] -= self.learning_rate * avg_gradient[layer_name]

    def training_round(self, round_num: int) -> FederatedRoundStats:
        """
        Execute one federated training round.
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"FEDERATED ROUND {round_num}")
        logger.info(f"{'='*60}")

        # 1. Distribute
        self.distribute_model(round_num)

        # 2. Collect gradients
        gradients = self.collect_gradients(round_num)

        num_participants = len(gradients)

        if num_participants == 0:
            logger.error("No participants. Skipping round.")
            return None

        # 3. Aggregate
        avg_gradient = self.aggregate_gradients(gradients)

        # 4. Update global model
        self.update_global_model(avg_gradient)

        # 5. Statistics
        stats = FederatedRoundStats(
            round_num=round_num,
            num_agents=self.num_agents,
            num_participants=num_participants,
            aggregation_method=self.aggregation_method
        )

        self.round_history.append(stats)

        logger.info(f"[Round {round_num}] ✅ Complete. Participants: {num_participants}/{self.num_agents}")
        logger.info(f"[Round {round_num}] Global model updated via {self.aggregation_method}")

        return stats

    def run_training(self, num_rounds: int = 10):
        """Execute full federated training loop."""
        logger.info(f"\n{'#'*60}")
        logger.info(f"# FEDERATED LEARNING: {num_rounds} rounds")
        logger.info(f"# Agents: {self.num_agents}, Method: {self.aggregation_method}")
        logger.info(f"{'#'*60}\n")

        for r in range(1, num_rounds + 1):
            self.training_round(r)

        logger.info(f"\n{'#'*60}")
        logger.info(f"# TRAINING COMPLETE")
        logger.info(f"# Total rounds: {num_rounds}")
        logger.info(f"# Aggregation method: {self.aggregation_method}")
        logger.info(f"{'#'*60}\n")

        return self.round_history

    def get_statistics(self) -> Dict:
        """Get training statistics."""
        if not self.round_history:
            return {}

        return {
            "total_rounds": len(self.round_history),
            "final_participants": self.round_history[-1].num_participants if self.round_history else 0,
            "aggregation_method": self.aggregation_method,
            "learning_rate": self.learning_rate,
            "last_updated": self.round_history[-1].timestamp if self.round_history else None
        }


if __name__ == "__main__":
    # Demo: Federated Learning with 6 ADRION agents
    logger.info("Starting Federated Learning demo (6 agents, 10 rounds)...")

    coordinator = FederatedLearningCoordinator(
        num_agents=6,
        aggregation_method="fedavg",
        learning_rate=0.01
    )

    # Run training
    history = coordinator.run_training(num_rounds=5)

    # Print stats
    stats = coordinator.get_statistics()
    print(f"\nFinal Statistics:")
    for key, val in stats.items():
        print(f"  {key}: {val}")
