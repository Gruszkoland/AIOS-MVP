"""
Cross-Encoder Reranking for Hybrid Search

Uses sentence-transformers cross-encoder models for fine-grained ranking.
Reranks hybrid search results to improve top-K accuracy.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import asyncio

logger = logging.getLogger(__name__)


@dataclass
class RerankedFact:
    """Fact with cross-encoder reranking score"""
    claim: str
    fact_hash: str
    status: str
    confidence: float
    
    # Scores
    hybrid_score: float  # Original hybrid score (exact + semantic + vector)
    cross_encoder_score: float  # Cross-encoder reranking score (0-1)
    final_score: float  # Combined score for ranking
    
    # Metadata
    sources: List[str] = None
    reasoning: str = ""
    relevance_label: str = ""  # "highly_relevant", "relevant", "partially_relevant", "not_relevant"


class CrossEncoderReranker:
    """
    Cross-encoder based reranker for hybrid search results
    
    Uses sentence-transformers cross-encoder for fine-grained relevance scoring.
    Models: cross-encoder/ms-marco-MiniLM-L-6-v2 (fast), cross-encoder/ms-marco-MultiBERT (accurate)
    """

    def __init__(
        self,
        model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
        device: str = "cpu",
        batch_size: int = 32
    ):
        """
        Initialize cross-encoder reranker
        
        Args:
            model_name: Cross-encoder model from sentence-transformers
            device: "cpu" or "cuda"
            batch_size: Batch size for inference
        """
        self.model_name = model_name
        self.device = device
        self.batch_size = batch_size
        self.model = None
        self.loaded = False

    def load_model(self):
        """Load cross-encoder model"""
        try:
            from sentence_transformers import CrossEncoder
            
            self.model = CrossEncoder(self.model_name, device=self.device)
            self.loaded = True
            logger.info(f"✓ Loaded cross-encoder: {self.model_name}")
            
        except ImportError:
            logger.warning("sentence-transformers not installed, cross-encoder unavailable")
            self.loaded = False

    def rerank(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        top_k: int = 5,
        cross_encoder_weight: float = 0.4
    ) -> List[RerankedFact]:
        """
        Rerank candidates using cross-encoder
        
        Args:
            query: Query claim
            candidates: List of candidates with hybrid_score
            top_k: Return top-K reranked results
            cross_encoder_weight: Weight for cross-encoder score in final ranking
        
        Returns:
            List of reranked facts
        """
        if not self.loaded:
            logger.warning("Cross-encoder not loaded, returning original ranking")
            return candidates
        
        # Prepare query-candidate pairs
        pairs = [(query, c.get('claim', '')) for c in candidates]
        
        # Get cross-encoder scores
        try:
            ce_scores = self.model.predict(pairs, batch_size=self.batch_size)
            
            # Normalize to 0-1 range
            if len(ce_scores) > 0:
                min_score = min(ce_scores)
                max_score = max(ce_scores)
                
                if max_score > min_score:
                    ce_scores = [(s - min_score) / (max_score - min_score) for s in ce_scores]
                else:
                    ce_scores = [0.5] * len(ce_scores)
        
        except Exception as e:
            logger.warning(f"Cross-encoder inference failed: {e}")
            ce_scores = [0.5] * len(candidates)
        
        # Combine hybrid score + cross-encoder score
        reranked = []
        for idx, (candidate, ce_score) in enumerate(zip(candidates, ce_scores)):
            hybrid_score = candidate.get('hybrid_score', 0.5)
            
            # Weighted combination: (1 - weight) * hybrid + weight * cross_encoder
            final_score = (
                (1 - cross_encoder_weight) * hybrid_score +
                cross_encoder_weight * ce_score
            )
            
            # Determine relevance label based on cross-encoder score
            if ce_score > 0.8:
                relevance_label = "highly_relevant"
            elif ce_score > 0.6:
                relevance_label = "relevant"
            elif ce_score > 0.4:
                relevance_label = "partially_relevant"
            else:
                relevance_label = "not_relevant"
            
            reranked_fact = RerankedFact(
                claim=candidate.get('claim', ''),
                fact_hash=candidate.get('fact_hash', ''),
                status=candidate.get('status', 'unknown'),
                confidence=candidate.get('confidence', 0.0),
                hybrid_score=hybrid_score,
                cross_encoder_score=ce_score,
                final_score=final_score,
                sources=candidate.get('sources', []),
                relevance_label=relevance_label,
                reasoning=f"Hybrid: {hybrid_score:.3f} + CE: {ce_score:.3f} → {final_score:.3f}"
            )
            
            reranked.append(reranked_fact)
        
        # Sort by final score
        reranked.sort(key=lambda x: x.final_score, reverse=True)
        
        return reranked[:top_k]

    async def rerank_async(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        top_k: int = 5,
        cross_encoder_weight: float = 0.4
    ) -> List[RerankedFact]:
        """
        Async version of rerank (runs in thread pool)
        
        Args:
            query: Query claim
            candidates: List of candidates
            top_k: Top-K results
            cross_encoder_weight: Cross-encoder weight
        
        Returns:
            Reranked facts
        """
        loop = asyncio.get_event_loop()
        
        return await loop.run_in_executor(
            None,
            self.rerank,
            query,
            candidates,
            top_k,
            cross_encoder_weight
        )

    @staticmethod
    def get_model_recommendations() -> Dict[str, Dict[str, str]]:
        """Get recommended cross-encoder models with trade-offs"""
        return {
            "fast": {
                "model": "cross-encoder/ms-marco-MiniLM-L-6-v2",
                "description": "Small model, ~30KB, very fast",
                "latency_ms": "5-10ms",
                "accuracy": "Good (0.39 nDCG)",
                "use_case": "Real-time applications, latency-sensitive"
            },
            "balanced": {
                "model": "cross-encoder/ms-marco-TinyBERT-L-2-v2",
                "description": "Tiny model, ~30MB, fast & accurate",
                "latency_ms": "10-20ms",
                "accuracy": "Very Good (0.50 nDCG)",
                "use_case": "Production deployments, balanced trade-off"
            },
            "accurate": {
                "model": "cross-encoder/ms-marco-MiniLM-L-12-v2",
                "description": "Larger model, ~110MB, slower but accurate",
                "latency_ms": "20-50ms",
                "accuracy": "Excellent (0.47 nDCG)",
                "use_case": "Batch processing, offline ranking"
            }
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get reranker statistics"""
        return {
            "model": self.model_name,
            "loaded": self.loaded,
            "device": self.device,
            "batch_size": self.batch_size
        }
