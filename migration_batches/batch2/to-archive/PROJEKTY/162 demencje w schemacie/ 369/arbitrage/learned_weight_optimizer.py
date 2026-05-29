"""
Learned Weight Optimizer for Hybrid Search

Optimizes hybrid search weights (exact, semantic, vector) based on historical KB evaluations.
Uses gradient descent to maximize KB hit rate for different claim types.
"""

import logging
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import json
import math

logger = logging.getLogger(__name__)


class ClaimType(Enum):
    """Types of claims for domain-specific weight optimization"""
    FACTUAL = "factual"           # Verifiable facts (science, history)
    MISCONCEPTION = "misconception" # False beliefs to debunk
    CONTEXTUAL = "contextual"     # Claims needing context
    OPINION = "opinion"           # Subjective or debatable
    RECENT = "recent"             # Recent events/news


@dataclass
class WeightOptimizationHistory:
    """Historical evaluation data for weight optimization"""
    claim: str
    claim_type: str
    kb_hit: bool  # Whether KB successfully verified
    hybrid_score: float
    exact_score: float
    semantic_score: float
    vector_score: float
    final_confidence: float


@dataclass
class OptimizedWeights:
    """Set of optimized weights"""
    exact_weight: float      # Weight for exact matching
    semantic_weight: float   # Weight for semantic similarity
    vector_weight: float     # Weight for vector embeddings
    cross_encoder_weight: float = 0.0  # Cross-encoder weight (if using reranking)
    
    claim_type: Optional[str] = None  # Domain-specific weights
    performance_metric: float = 0.0  # Achieved KB hit rate
    
    def normalize(self) -> 'OptimizedWeights':
        """Normalize weights to sum to 1.0"""
        total = self.exact_weight + self.semantic_weight + self.vector_weight
        
        if total == 0:
            return OptimizedWeights(0.33, 0.33, 0.34, self.cross_encoder_weight, self.claim_type)
        
        return OptimizedWeights(
            exact_weight=self.exact_weight / total,
            semantic_weight=self.semantic_weight / total,
            vector_weight=self.vector_weight / total,
            cross_encoder_weight=self.cross_encoder_weight,
            claim_type=self.claim_type,
            performance_metric=self.performance_metric
        )


class LearnedWeightOptimizer:
    """
    Optimizes hybrid search weights using historical evaluation data
    
    Algorithm: Gradient descent with momentum to maximize KB hit rate
    """

    def __init__(
        self,
        learning_rate: float = 0.01,
        momentum: float = 0.9,
        iterations: int = 100,
        batch_size: int = 32
    ):
        """
        Initialize weight optimizer
        
        Args:
            learning_rate: Learning rate for gradient descent
            momentum: Momentum for accelerated descent
            iterations: Number of optimization iterations
            batch_size: Batch size for mini-batch gradient descent
        """
        self.learning_rate = learning_rate
        self.momentum = momentum
        self.iterations = iterations
        self.batch_size = batch_size
        
        self.history: List[WeightOptimizationHistory] = []
        self.optimized_weights: Dict[str, OptimizedWeights] = {}

    def add_evaluation(
        self,
        claim: str,
        claim_type: str,
        kb_hit: bool,
        hybrid_score: float,
        exact_score: float,
        semantic_score: float,
        vector_score: float,
        final_confidence: float
    ):
        """Add evaluation result to history"""
        entry = WeightOptimizationHistory(
            claim=claim,
            claim_type=claim_type,
            kb_hit=kb_hit,
            hybrid_score=hybrid_score,
            exact_score=exact_score,
            semantic_score=semantic_score,
            vector_score=vector_score,
            final_confidence=final_confidence
        )
        
        self.history.append(entry)

    def optimize(self, global_only: bool = False) -> Dict[str, OptimizedWeights]:
        """
        Optimize weights using historical data
        
        Args:
            global_only: If True, optimize global weights; else optimize per claim-type
        
        Returns:
            Dictionary of optimized weight sets {claim_type: OptimizedWeights}
        """
        if len(self.history) < 10:
            logger.warning(f"Insufficient history for optimization ({len(self.history)} < 10)")
            return self._default_weights()
        
        if global_only:
            return self._optimize_global()
        else:
            return self._optimize_per_type()

    def _optimize_global(self) -> Dict[str, OptimizedWeights]:
        """Optimize global weights across all claim types"""
        
        logger.info("Optimizing global weights...")
        
        # Initialize with default weights
        weights = OptimizedWeights(0.33, 0.33, 0.34)
        velocity = OptimizedWeights(0.0, 0.0, 0.0)  # For momentum
        
        best_metric = 0.0
        best_weights = weights
        
        for iteration in range(self.iterations):
            # Calculate gradient
            gradients = self._calculate_gradients(weights, None)
            
            # Update velocity (momentum)
            velocity = OptimizedWeights(
                exact_weight=self.momentum * velocity.exact_weight + (1 - self.momentum) * gradients.exact_weight,
                semantic_weight=self.momentum * velocity.semantic_weight + (1 - self.momentum) * gradients.semantic_weight,
                vector_weight=self.momentum * velocity.vector_weight + (1 - self.momentum) * gradients.vector_weight
            )
            
            # Update weights
            weights = OptimizedWeights(
                exact_weight=weights.exact_weight + self.learning_rate * velocity.exact_weight,
                semantic_weight=weights.semantic_weight + self.learning_rate * velocity.semantic_weight,
                vector_weight=weights.vector_weight + self.learning_rate * velocity.vector_weight
            )
            
            weights = weights.normalize()
            
            # Evaluate metric
            metric = self._evaluate_weights(weights, None)
            weights.performance_metric = metric
            
            if metric > best_metric:
                best_metric = metric
                best_weights = weights
            
            if (iteration + 1) % 10 == 0:
                logger.debug(f"Iteration {iteration + 1}: KB Hit Rate = {metric*100:.1f}%")
        
        logger.info(f"✓ Global optimization complete: {best_metric*100:.1f}% KB hit rate")
        
        return {"global": best_weights}

    def _optimize_per_type(self) -> Dict[str, OptimizedWeights]:
        """Optimize weights per claim type"""
        
        logger.info("Optimizing per-type weights...")
        
        # Group history by claim type
        by_type = {}
        for entry in self.history:
            if entry.claim_type not in by_type:
                by_type[entry.claim_type] = []
            by_type[entry.claim_type].append(entry)
        
        optimized = {}
        
        for claim_type, entries in by_type.items():
            if len(entries) < 5:
                logger.warning(f"Insufficient data for {claim_type} ({len(entries)} < 5)")
                continue
            
            logger.info(f"  Optimizing {claim_type} ({len(entries)} samples)...")
            
            # Initialize weights
            weights = OptimizedWeights(0.33, 0.33, 0.34, claim_type=claim_type)
            velocity = OptimizedWeights(0.0, 0.0, 0.0, claim_type=claim_type)
            
            best_metric = 0.0
            best_weights = weights
            
            for iteration in range(self.iterations):
                # Calculate gradient for this type
                gradients = self._calculate_gradients(weights, claim_type)
                
                # Update velocity
                velocity = OptimizedWeights(
                    exact_weight=self.momentum * velocity.exact_weight + (1 - self.momentum) * gradients.exact_weight,
                    semantic_weight=self.momentum * velocity.semantic_weight + (1 - self.momentum) * gradients.semantic_weight,
                    vector_weight=self.momentum * velocity.vector_weight + (1 - self.momentum) * gradients.vector_weight,
                    claim_type=claim_type
                )
                
                # Update weights
                weights = OptimizedWeights(
                    exact_weight=weights.exact_weight + self.learning_rate * velocity.exact_weight,
                    semantic_weight=weights.semantic_weight + self.learning_rate * velocity.semantic_weight,
                    vector_weight=weights.vector_weight + self.learning_rate * velocity.vector_weight,
                    claim_type=claim_type
                )
                
                weights = weights.normalize()
                
                # Evaluate
                metric = self._evaluate_weights(weights, claim_type)
                weights.performance_metric = metric
                
                if metric > best_metric:
                    best_metric = metric
                    best_weights = weights
            
            logger.info(f"  ✓ {claim_type}: {best_metric*100:.1f}% KB hit rate")
            optimized[claim_type] = best_weights
        
        logger.info(f"✓ Per-type optimization complete: {len(optimized)} types optimized")
        
        return optimized

    def _calculate_gradients(
        self,
        weights: OptimizedWeights,
        claim_type: Optional[str]
    ) -> OptimizedWeights:
        """
        Calculate gradients for weights using numerical differentiation
        
        Args:
            weights: Current weights
            claim_type: Filter by claim type (None = all)
        
        Returns:
            Gradient vector
        """
        epsilon = 0.001
        
        # Evaluate at current point
        f0 = self._evaluate_weights(weights, claim_type)
        
        # Numerical gradients
        weights_plus = OptimizedWeights(
            exact_weight=weights.exact_weight + epsilon,
            semantic_weight=weights.semantic_weight,
            vector_weight=weights.vector_weight
        )
        grad_exact = (self._evaluate_weights(weights_plus, claim_type) - f0) / epsilon
        
        weights_plus = OptimizedWeights(
            exact_weight=weights.exact_weight,
            semantic_weight=weights.semantic_weight + epsilon,
            vector_weight=weights.vector_weight
        )
        grad_semantic = (self._evaluate_weights(weights_plus, claim_type) - f0) / epsilon
        
        weights_plus = OptimizedWeights(
            exact_weight=weights.exact_weight,
            semantic_weight=weights.semantic_weight,
            vector_weight=weights.vector_weight + epsilon
        )
        grad_vector = (self._evaluate_weights(weights_plus, claim_type) - f0) / epsilon
        
        return OptimizedWeights(grad_exact, grad_semantic, grad_vector)

    def _evaluate_weights(
        self,
        weights: OptimizedWeights,
        claim_type: Optional[str]
    ) -> float:
        """
        Evaluate KB hit rate with given weights
        
        Args:
            weights: Weight set to evaluate
            claim_type: Filter by claim type (None = all)
        
        Returns:
            KB hit rate (0.0-1.0)
        """
        relevant_entries = self.history
        
        if claim_type is not None:
            relevant_entries = [e for e in relevant_entries if e.claim_type == claim_type]
        
        if not relevant_entries:
            return 0.0
        
        # Calculate hybrid score with these weights
        hits = 0
        for entry in relevant_entries:
            # Normalize entry scores
            scores = [entry.exact_score, entry.semantic_score, entry.vector_score]
            max_score = max(scores) if scores else 1.0
            
            if max_score > 0:
                norm_exact = entry.exact_score / max_score
                norm_semantic = entry.semantic_score / max_score
                norm_vector = entry.vector_score / max_score
            else:
                norm_exact = norm_semantic = norm_vector = 0.0
            
            # Calculate combined score
            combined = (
                weights.exact_weight * norm_exact +
                weights.semantic_weight * norm_semantic +
                weights.vector_weight * norm_vector
            )
            
            # Consider it a hit if combined score > threshold
            if combined > 0.6:
                hits += 1
        
        return hits / len(relevant_entries) if relevant_entries else 0.0

    def _default_weights(self) -> Dict[str, OptimizedWeights]:
        """Return default weight sets"""
        return {
            "global": OptimizedWeights(0.3, 0.35, 0.35),
            "factual": OptimizedWeights(0.4, 0.3, 0.3),
            "misconception": OptimizedWeights(0.2, 0.5, 0.3),
            "contextual": OptimizedWeights(0.3, 0.3, 0.4)
        }

    def export_weights_json(self, filepath: str):
        """Export optimized weights as JSON"""
        weights_dict = {}
        
        for key, weights in self.optimized_weights.items():
            weights_dict[key] = {
                "exact_weight": weights.exact_weight,
                "semantic_weight": weights.semantic_weight,
                "vector_weight": weights.vector_weight,
                "cross_encoder_weight": weights.cross_encoder_weight,
                "claim_type": weights.claim_type,
                "performance_metric": weights.performance_metric
            }
        
        with open(filepath, 'w') as f:
            json.dump(weights_dict, f, indent=2)

    def get_statistics(self) -> Dict[str, Any]:
        """Get optimization statistics"""
        by_type = {}
        by_kb_hit = {"hit": 0, "miss": 0}
        
        for entry in self.history:
            # By type
            if entry.claim_type not in by_type:
                by_type[entry.claim_type] = 0
            by_type[entry.claim_type] += 1
            
            # By KB hit
            if entry.kb_hit:
                by_kb_hit["hit"] += 1
            else:
                by_kb_hit["miss"] += 1
        
        total = len(self.history)
        kb_hit_rate = by_kb_hit["hit"] / total if total > 0 else 0
        
        return {
            "total_evaluations": total,
            "kb_hit_rate": kb_hit_rate,
            "kb_hits": by_kb_hit["hit"],
            "kb_misses": by_kb_hit["miss"],
            "by_claim_type": by_type,
            "optimized_weights_count": len(self.optimized_weights)
        }
