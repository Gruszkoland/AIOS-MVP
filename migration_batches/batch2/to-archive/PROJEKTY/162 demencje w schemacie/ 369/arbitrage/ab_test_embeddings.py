"""
A/B Testing Framework for Embedding Models

Compare text-embedding-3-small vs text-embedding-3-large:
- Accuracy (KB hit rate, vector search quality)
- Latency (embedding generation time)
- Cost (API token usage)
- Model-specific metrics
"""

import asyncio
import logging
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
import json

logger = logging.getLogger(__name__)


class EmbeddingModelSize(Enum):
    """Embedding model sizes"""
    SMALL = "text-embedding-3-small"    # 1536 dims, $0.02/1M tokens
    LARGE = "text-embedding-3-large"    # 3072 dims, $0.13/1M tokens


@dataclass
class ModelMetrics:
    """Metrics for a single model"""
    model: str  # "small" or "large"
    total_claims: int = 0
    
    # Accuracy metrics
    kb_hits: int = 0
    kb_misses: int = 0
    kb_hit_rate: float = 0.0
    
    vector_search_hits: int = 0  # Claims verified by vector similarity
    vector_accuracy: float = 0.0
    
    avg_vector_score: float = 0.0  # Average similarity score
    
    # Latency metrics (ms)
    avg_embedding_time: float = 0.0
    max_embedding_time: float = 0.0
    min_embedding_time: float = 0.0
    total_embedding_time: float = 0.0
    
    # Cost metrics
    total_tokens_used: int = 0
    estimated_cost_usd: float = 0.0
    cost_per_claim: float = 0.0
    
    # Ranking quality
    avg_top_1_ranking_score: float = 0.0
    avg_top_3_ranking_score: float = 0.0
    avg_top_5_ranking_score: float = 0.0
    
    # Collection of individual measurements
    embedding_times: List[float] = field(default_factory=list)
    vector_scores: List[float] = field(default_factory=list)
    ranking_scores: List[float] = field(default_factory=list)


@dataclass
class ABTestResult:
    """Complete A/B test result"""
    test_id: str
    timestamp: str
    dataset_size: int
    
    model_small: ModelMetrics
    model_large: ModelMetrics
    
    # Comparison metrics
    accuracy_improvement: float  # % improvement of large over small
    latency_diff_ms: float       # ms difference (small - large, positive = large is slower)
    cost_diff_monthly: float     # $ difference (large - small, positive = large is more expensive)
    
    # Recommendation
    recommendation: str  # "small" (cost-optimized), "large" (accuracy-optimized), "tie"
    reasoning: str
    
    winner: Optional[str] = None  # "small" or "large"


class EmbeddingABTestFramework:
    """A/B testing framework for embedding models"""

    # Pricing (as of 2024)
    PRICING = {
        EmbeddingModelSize.SMALL: 0.02 / 1_000_000,  # $0.02 per 1M tokens
        EmbeddingModelSize.LARGE: 0.13 / 1_000_000   # $0.13 per 1M tokens
    }

    def __init__(
        self,
        embedding_manager: 'EmbeddingManager',
        hybrid_search: 'HybridSearchEngine',
        neo4j_manager: 'Neo4jManager'
    ):
        """
        Initialize A/B test framework
        
        Args:
            embedding_manager: EmbeddingManager instance
            hybrid_search: HybridSearchEngine instance
            neo4j_manager: Neo4jManager instance
        """
        self.embedding_mgr = embedding_manager
        self.hybrid_search = hybrid_search
        self.neo4j = neo4j_manager

    async def run_ab_test(
        self,
        benchmark_claims: List['BenchmarkClaim'],
        test_id: str = "ab_test_default"
    ) -> ABTestResult:
        """
        Run A/B test comparing small vs large models
        
        Args:
            benchmark_claims: List of BenchmarkClaim objects
            test_id: Test identifier
        
        Returns:
            ABTestResult with comparison metrics
        """
        from datetime import datetime
        
        logger.info(f"Starting A/B test with {len(benchmark_claims)} claims")
        
        # Test both models
        small_metrics = await self._test_model(
            EmbeddingModelSize.SMALL,
            benchmark_claims
        )
        
        large_metrics = await self._test_model(
            EmbeddingModelSize.LARGE,
            benchmark_claims
        )
        
        # Compare results
        result = self._compare_models(
            test_id,
            small_metrics,
            large_metrics,
            benchmark_claims
        )
        
        return result

    async def _test_model(
        self,
        model: EmbeddingModelSize,
        benchmark_claims: List['BenchmarkClaim']
    ) -> ModelMetrics:
        """
        Test a single embedding model
        
        Args:
            model: Model to test
            benchmark_claims: Claims to evaluate
        
        Returns:
            ModelMetrics with test results
        """
        metrics = ModelMetrics(model=model.value)
        metrics.total_claims = len(benchmark_claims)
        
        logger.info(f"Testing model: {model.value}")
        
        for idx, claim in enumerate(benchmark_claims):
            # Generate embedding
            start_time = time.time()
            
            try:
                # Swap model temporarily
                original_model = self.embedding_mgr.model
                self.embedding_mgr.model = model.value
                
                embedding_result = await self.embedding_mgr.embed_text(claim.claim)
                
                embedding_time = (time.time() - start_time) * 1000  # ms
                metrics.embedding_times.append(embedding_time)
                
                # Run hybrid search with this embedding
                ranked_facts = await self.hybrid_search.hybrid_search(
                    claim.claim,
                    limit=5
                )
                
                if ranked_facts:
                    metrics.kb_hits += 1
                    
                    # Track ranking quality
                    top_1_score = ranked_facts[0].hybrid_score if len(ranked_facts) > 0 else 0
                    top_3_score = sum(f.hybrid_score for f in ranked_facts[:3]) / min(3, len(ranked_facts))
                    top_5_score = sum(f.hybrid_score for f in ranked_facts[:5]) / len(ranked_facts)
                    
                    metrics.ranking_scores.extend([f.hybrid_score for f in ranked_facts])
                    metrics.avg_top_1_ranking_score = max(metrics.avg_top_1_ranking_score, top_1_score)
                    metrics.avg_top_3_ranking_score = max(metrics.avg_top_3_ranking_score, top_3_score)
                    metrics.avg_top_5_ranking_score = max(metrics.avg_top_5_ranking_score, top_5_score)
                    
                    # Count vector search hits (verify by vector method)
                    for fact in ranked_facts:
                        if fact.ranking_method.value == "vector_similarity":
                            metrics.vector_search_hits += 1
                            metrics.vector_scores.append(fact.vector_score)
                else:
                    metrics.kb_misses += 1
                
                # Track tokens
                if hasattr(embedding_result, 'tokens_used'):
                    metrics.total_tokens_used += embedding_result.tokens_used
                
                # Restore original model
                self.embedding_mgr.model = original_model
                
            except Exception as e:
                logger.warning(f"Error testing claim {idx}: {e}")
                metrics.kb_misses += 1
                continue
            
            if (idx + 1) % 10 == 0:
                logger.debug(f"Tested {idx + 1}/{metrics.total_claims} claims")
        
        # Calculate aggregated metrics
        metrics = self._calculate_metrics(metrics, model)
        
        return metrics

    @staticmethod
    def _calculate_metrics(metrics: ModelMetrics, model: EmbeddingModelSize) -> ModelMetrics:
        """Calculate aggregated metrics from raw data"""
        
        # Hit rate
        total = metrics.kb_hits + metrics.kb_misses
        if total > 0:
            metrics.kb_hit_rate = metrics.kb_hits / total * 100
        
        # Latency
        if metrics.embedding_times:
            metrics.avg_embedding_time = sum(metrics.embedding_times) / len(metrics.embedding_times)
            metrics.max_embedding_time = max(metrics.embedding_times)
            metrics.min_embedding_time = min(metrics.embedding_times)
            metrics.total_embedding_time = sum(metrics.embedding_times)
        
        # Cost
        price_per_token = EmbeddingABTestFramework.PRICING[model]
        metrics.estimated_cost_usd = metrics.total_tokens_used * price_per_token
        
        if metrics.total_claims > 0:
            metrics.cost_per_claim = metrics.estimated_cost_usd / metrics.total_claims
        
        # Vector scores
        if metrics.vector_scores:
            metrics.avg_vector_score = sum(metrics.vector_scores) / len(metrics.vector_scores)
            metrics.vector_accuracy = metrics.vector_search_hits / metrics.total_claims * 100
        
        # Ranking scores
        if metrics.ranking_scores:
            metrics.avg_top_1_ranking_score = max(metrics.ranking_scores) if metrics.ranking_scores else 0
            if len(metrics.ranking_scores) >= 3:
                metrics.avg_top_3_ranking_score = sum(sorted(metrics.ranking_scores, reverse=True)[:3]) / 3
            if len(metrics.ranking_scores) >= 5:
                metrics.avg_top_5_ranking_score = sum(sorted(metrics.ranking_scores, reverse=True)[:5]) / 5
        
        return metrics

    @staticmethod
    def _compare_models(
        test_id: str,
        small_metrics: ModelMetrics,
        large_metrics: ModelMetrics,
        benchmark_claims: List['BenchmarkClaim']
    ) -> ABTestResult:
        """Compare two models and generate recommendation"""
        from datetime import datetime
        
        # Calculate differences
        accuracy_improvement = large_metrics.kb_hit_rate - small_metrics.kb_hit_rate
        latency_diff = large_metrics.avg_embedding_time - small_metrics.avg_embedding_time
        
        # Cost comparison for 1M claims/month
        small_monthly = small_metrics.cost_per_claim * 1_000_000
        large_monthly = large_metrics.cost_per_claim * 1_000_000
        cost_diff_monthly = large_monthly - small_monthly
        
        # Determine winner
        if accuracy_improvement > 2.0 and cost_diff_monthly < 100:
            winner = "large"
            recommendation = "large"
            reasoning = f"Large model provides {accuracy_improvement:.1f}% accuracy improvement for only ${cost_diff_monthly:.0f}/month extra"
        elif accuracy_improvement < 0.5 and cost_diff_monthly > 50:
            winner = "small"
            recommendation = "small"
            reasoning = f"Small model has comparable accuracy ({accuracy_improvement:.1f}% diff) but costs ${-cost_diff_monthly:.0f}/month less"
        elif latency_diff > 50 and accuracy_improvement < 1.0:
            winner = "small"
            recommendation = "small"
            reasoning = f"Small model is {latency_diff:.0f}ms faster with minimal accuracy loss"
        else:
            winner = "tie"
            recommendation = "context-dependent"
            reasoning = "Trade-offs roughly balanced; choose based on priorities (cost vs accuracy)"
        
        result = ABTestResult(
            test_id=test_id,
            timestamp=datetime.now().isoformat(),
            dataset_size=len(benchmark_claims),
            model_small=small_metrics,
            model_large=large_metrics,
            accuracy_improvement=accuracy_improvement,
            latency_diff_ms=latency_diff,
            cost_diff_monthly=cost_diff_monthly,
            winner=winner,
            recommendation=recommendation,
            reasoning=reasoning
        )
        
        return result

    @staticmethod
    def generate_report(result: ABTestResult) -> str:
        """Generate human-readable A/B test report"""
        
        report = f"""
╔════════════════════════════════════════════════════════════════════╗
║        EMBEDDING MODEL A/B TEST REPORT                            ║
╚════════════════════════════════════════════════════════════════════╝

Test ID: {result.test_id}
Timestamp: {result.timestamp}
Dataset Size: {result.dataset_size} claims

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 ACCURACY METRICS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Model: text-embedding-3-small
  KB Hit Rate: {result.model_small.kb_hit_rate:.1f}%
  Vector Accuracy: {result.model_small.vector_accuracy:.1f}%
  Avg Vector Score: {result.model_small.avg_vector_score:.3f}
  Top-1 Ranking Score: {result.model_small.avg_top_1_ranking_score:.3f}
  Top-5 Ranking Score: {result.model_small.avg_top_5_ranking_score:.3f}

Model: text-embedding-3-large
  KB Hit Rate: {result.model_large.kb_hit_rate:.1f}%
  Vector Accuracy: {result.model_large.vector_accuracy:.1f}%
  Avg Vector Score: {result.model_large.avg_vector_score:.3f}
  Top-1 Ranking Score: {result.model_large.avg_top_1_ranking_score:.3f}
  Top-5 Ranking Score: {result.model_large.avg_top_5_ranking_score:.3f}

📈 Accuracy Improvement: {result.accuracy_improvement:+.2f}%

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⏱️  LATENCY METRICS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Model: text-embedding-3-small
  Avg Embedding Time: {result.model_small.avg_embedding_time:.2f}ms
  Min: {result.model_small.min_embedding_time:.2f}ms
  Max: {result.model_small.max_embedding_time:.2f}ms
  Total: {result.model_small.total_embedding_time:.1f}ms

Model: text-embedding-3-large
  Avg Embedding Time: {result.model_large.avg_embedding_time:.2f}ms
  Min: {result.model_large.min_embedding_time:.2f}ms
  Max: {result.model_large.max_embedding_time:.2f}ms
  Total: {result.model_large.total_embedding_time:.1f}ms

⏱️  Latency Difference: {result.latency_diff_ms:+.2f}ms
   ({'Large is ' + str(abs(result.latency_diff_ms)) + 'ms slower' if result.latency_diff_ms > 0 else 'Large is ' + str(abs(result.latency_diff_ms)) + 'ms faster'})

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💰 COST METRICS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Model: text-embedding-3-small
  Total Tokens: {result.model_small.total_tokens_used:,}
  Cost Per Claim: ${result.model_small.cost_per_claim:.6f}
  Estimated Monthly Cost (1M claims): ${result.model_small.cost_per_claim * 1_000_000:.2f}

Model: text-embedding-3-large
  Total Tokens: {result.model_large.total_tokens_used:,}
  Cost Per Claim: ${result.model_large.cost_per_claim:.6f}
  Estimated Monthly Cost (1M claims): ${result.model_large.cost_per_claim * 1_000_000:.2f}

💰 Cost Difference: ${result.cost_diff_monthly:+.2f}/month
   (Large model costs {abs(result.cost_diff_monthly):.0f}% {'more' if result.cost_diff_monthly > 0 else 'less'})

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🏆 RECOMMENDATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Winner: {result.winner.upper() if result.winner else 'TIE'}
Recommendation: Use {result.recommendation.upper()} model

Reasoning:
{result.reasoning}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 DECISION MATRIX
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Choose SMALL if:
  ✓ Cost is primary concern
  ✓ Accuracy difference < 1% is acceptable
  ✓ Real-time latency is critical
  ✓ Server-constrained deployments

Choose LARGE if:
  ✓ Accuracy improvement > 2% is valuable
  ✓ Cost difference < $100/month is acceptable
  ✓ Complex/ambiguous claims are frequent
  ✓ Enterprise accuracy requirements

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        return report

    @staticmethod
    def export_result_json(result: ABTestResult, filepath: str):
        """Export test result as JSON"""
        result_dict = {
            "test_id": result.test_id,
            "timestamp": result.timestamp,
            "dataset_size": result.dataset_size,
            "model_small": asdict(result.model_small),
            "model_large": asdict(result.model_large),
            "comparison": {
                "accuracy_improvement": result.accuracy_improvement,
                "latency_diff_ms": result.latency_diff_ms,
                "cost_diff_monthly": result.cost_diff_monthly
            },
            "recommendation": {
                "winner": result.winner,
                "choice": result.recommendation,
                "reasoning": result.reasoning
            }
        }
        
        with open(filepath, 'w') as f:
            json.dump(result_dict, f, indent=2, default=str)
