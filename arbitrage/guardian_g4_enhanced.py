"""
Guardian G4_Truthfulness with Perplexity Web Context
Enhanced Guardian Law evaluation using real-time fact-checking
"""

import asyncio
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum

from arbitrage.guardian import Guardian, Decision
from mcp_servers.perplexity_gateway import PerplexityGateway

logger = logging.getLogger(__name__)


class ConfidenceLevel(Enum):
    """Confidence score levels"""
    VERY_LOW = 0.0  # 0-0.2
    LOW = 0.4       # 0.2-0.4
    MEDIUM = 0.6    # 0.4-0.6
    HIGH = 0.8      # 0.6-0.8
    VERY_HIGH = 1.0 # 0.8-1.0


@dataclass
class G4EvaluationResult:
    """Result of G4_Truthfulness evaluation with web context"""
    approved: bool
    confidence: float
    local_confidence: float  # Inference-only
    web_confidence: Optional[float]  # From Perplexity
    sources: list
    reasoning: str
    pii_found: Dict[str, int]
    evaluation_time_ms: float


class GuardianG4Enhanced:
    """Guardian Law G4_Truthfulness with web-context enhancement"""
    
    def __init__(self, guardian: Guardian, perplexity_gateway: PerplexityGateway):
        self.guardian = guardian
        self.perplexity = perplexity_gateway
    
    async def evaluate(
        self, 
        claim: str,
        context: Optional[Dict[str, Any]] = None,
        require_web_verification: bool = True
    ) -> G4EvaluationResult:
        """
        Evaluate truthfulness of a claim with web verification
        
        Args:
            claim: The claim to fact-check
            context: Optional context about the claim
            require_web_verification: If True, requires Perplexity verification
        
        Returns:
            G4EvaluationResult with approval decision and confidence scores
        """
        import time
        start_time = time.time()
        
        # Step 1: Local inference (existing Guardian logic)
        local_confidence = self._local_confidence_score(claim, context)
        logger.info(f"G4 Local confidence: {local_confidence:.2f}")
        
        # Step 2: Web fact-check via Perplexity
        web_result = None
        web_confidence = None
        sources = []
        pii_found = {}
        
        if require_web_verification:
            try:
                web_result = await self.perplexity.fact_check(claim)
                web_confidence = web_result.confidence
                sources = web_result.sources
                pii_found = {}  # Already redacted in perplexity_gateway
                
                logger.info(f"G4 Web verification: {web_result.verified} (confidence: {web_confidence:.2f})")
            
            except Exception as e:
                logger.warning(f"Web verification failed: {e}. Using local confidence only.")
                web_confidence = None
        
        # Step 3: Combine signals
        combined_confidence = self._combine_confidence_signals(
            local_confidence=local_confidence,
            web_confidence=web_confidence,
            web_available=web_confidence is not None
        )
        
        # Step 4: Decision logic
        approval_threshold = 0.5
        approved = combined_confidence >= approval_threshold
        
        reasoning = self._build_reasoning(
            claim=claim,
            local_confidence=local_confidence,
            web_confidence=web_confidence,
            web_result=web_result,
            approved=approved
        )
        
        elapsed_ms = (time.time() - start_time) * 1000
        
        result = G4EvaluationResult(
            approved=approved,
            confidence=combined_confidence,
            local_confidence=local_confidence,
            web_confidence=web_confidence,
            sources=sources,
            reasoning=reasoning,
            pii_found=pii_found,
            evaluation_time_ms=elapsed_ms
        )
        
        logger.info(f"G4 Decision: {'APPROVE' if approved else 'DENY'} "
                   f"(combined: {combined_confidence:.2f}, local: {local_confidence:.2f}, "
                   f"web: {web_confidence:.2f if web_confidence else 'N/A'})")
        
        return result
    
    def _local_confidence_score(self, claim: str, context: Optional[Dict] = None) -> float:
        """
        Calculate local inference confidence score (0.0-1.0)
        Based on: claim length, known facts, context consistency
        """
        score = 0.5  # Start neutral
        
        if not claim or len(claim) < 10:
            return 0.2  # Too short
        
        # Heuristics (existing ADRION logic)
        if "definitely" in claim.lower() or "absolutely" in claim.lower():
            score -= 0.1  # Overconfident claims suspicious
        
        if "I think" in claim or "probably" in claim:
            score -= 0.05  # Hedged claims less confident
        
        if any(word in claim.lower() for word in ["study", "research", "found", "showed"]):
            score += 0.1  # Citation of evidence
        
        # Clamp to [0, 1]
        return max(0.0, min(1.0, score))
    
    def _combine_confidence_signals(
        self,
        local_confidence: float,
        web_confidence: Optional[float],
        web_available: bool
    ) -> float:
        """
        Combine local inference and web verification signals
        Weights: local 40%, web 60% (web is more authoritative)
        """
        if not web_available or web_confidence is None:
            # Fallback to local, with penalty for missing web verification
            return local_confidence * 0.8
        
        # Combine with weighted average
        combined = (local_confidence * 0.4) + (web_confidence * 0.6)
        
        # If signals conflict, penalize
        signal_divergence = abs(local_confidence - web_confidence)
        if signal_divergence > 0.4:
            # Large disagreement → reduce confidence
            combined *= 0.9
        
        return combined
    
    def _build_reasoning(
        self,
        claim: str,
        local_confidence: float,
        web_confidence: Optional[float],
        web_result,
        approved: bool
    ) -> str:
        """Build human-readable reasoning for the decision"""
        
        parts = []
        
        # Local reasoning
        if local_confidence > 0.7:
            parts.append(f"Local analysis suggests likely truthful (confidence: {local_confidence:.2f})")
        elif local_confidence < 0.3:
            parts.append(f"Local analysis suggests likely false (confidence: {local_confidence:.2f})")
        else:
            parts.append(f"Local analysis inconclusive (confidence: {local_confidence:.2f})")
        
        # Web verification
        if web_confidence is not None:
            if web_result.verified:
                parts.append(f"Web verification: VERIFIED via {len(web_result.sources)} sources "
                           f"(confidence: {web_confidence:.2f})")
            else:
                parts.append(f"Web verification: NOT VERIFIED (confidence: {web_confidence:.2f})")
                if web_result.counter_claims:
                    parts.append(f"Counter-claims found: {', '.join(web_result.counter_claims[:2])}")
        else:
            parts.append("Web verification: UNAVAILABLE (circuit breaker or network error)")
        
        # Decision
        if approved:
            parts.append(f"✓ APPROVED: Sufficient confidence in truthfulness")
        else:
            parts.append(f"✗ DENIED: Insufficient confidence in truthfulness")
        
        return "\n".join(parts)
    
    async def to_genesis_record(self, result: G4EvaluationResult, claim: str) -> Dict[str, Any]:
        """
        Convert evaluation result to Genesis Record format for audit trail
        """
        return {
            "agent": "GUARDIAN",
            "law": "G4_Truthfulness",
            "version": "v12",  # Enhanced with Perplexity
            "claim": claim,
            "decision": "APPROVE" if result.approved else "DENY",
            "confidence": {
                "local": result.local_confidence,
                "web": result.web_confidence,
                "combined": result.confidence
            },
            "sources": result.sources,
            "reasoning": result.reasoning,
            "metadata": {
                "pii_detected": result.pii_found,
                "evaluation_time_ms": result.evaluation_time_ms,
                "web_verification_used": result.web_confidence is not None
            }
        }
