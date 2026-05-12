"""
MCP Wrapper: Guardian G4_Truthfulness Enhanced
Flask endpoint integrating Perplexity web context with Guardian evaluation
"""

from flask import Blueprint, request, jsonify
import asyncio
import logging
from typing import Optional, Dict, Any

from arbitrage.guardian import Guardian
from arbitrage.guardian_g4_enhanced import GuardianG4Enhanced, G4EvaluationResult
from mcp_servers.perplexity_gateway import PerplexityGateway
from arbitrage.gateway import create_genesis_record

logger = logging.getLogger(__name__)


def create_g4_enhanced_blueprint(
    guardian: Guardian,
    perplexity_gateway: PerplexityGateway
) -> Blueprint:
    """
    Create Flask Blueprint for Guardian G4 Enhanced endpoint
    
    Args:
        guardian: Guardian Laws engine instance
        perplexity_gateway: Perplexity MCP gateway instance
    
    Returns:
        Flask Blueprint with /guardian/g4-enhanced endpoint
    """
    
    bp = Blueprint('guardian_g4_enhanced', __name__, url_prefix='/api/mcp/guardian')
    
    # Initialize G4 Enhanced
    g4_enhanced = GuardianG4Enhanced(guardian, perplexity_gateway)
    
    @bp.route('/g4-enhanced', methods=['POST'])
    def evaluate_g4_enhanced():
        """
        Evaluate a claim using Guardian G4_Truthfulness with Perplexity web context
        
        Request JSON:
        {
            "claim": str (required),
            "context": dict (optional),
            "require_web_verification": bool (default: true),
            "user_id": str (optional, for Genesis logging)
        }
        
        Response JSON:
        {
            "approved": bool,
            "confidence": float (0.0-1.0),
            "local_confidence": float,
            "web_confidence": float or null,
            "sources": list,
            "reasoning": str,
            "evaluation_time_ms": float,
            "genesis_id": str (audit trail reference)
        }
        """
        
        try:
            data = request.get_json()
            
            # Validate required fields
            if not data or "claim" not in data:
                return jsonify({
                    "error": "Missing required field: 'claim'",
                    "code": "VALIDATION_ERROR"
                }), 400
            
            claim = data["claim"]
            context = data.get("context")
            require_web_verification = data.get("require_web_verification", True)
            user_id = data.get("user_id", "system")
            
            # Input validation
            if not isinstance(claim, str) or len(claim) < 5:
                return jsonify({
                    "error": "Claim must be non-empty string with at least 5 characters",
                    "code": "VALIDATION_ERROR"
                }), 400
            
            # Run async evaluation
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                result: G4EvaluationResult = loop.run_until_complete(
                    g4_enhanced.evaluate(
                        claim=claim,
                        context=context,
                        require_web_verification=require_web_verification
                    )
                )
            finally:
                loop.close()
            
            # Convert to Genesis Record
            genesis_record = loop.run_until_complete(
                g4_enhanced.to_genesis_record(result, claim)
            )
            
            # Log to Genesis
            genesis_id = None
            try:
                genesis_id = create_genesis_record(
                    agent="GUARDIAN",
                    law="G4_Truthfulness",
                    payload=genesis_record,
                    user_id=user_id
                )
                logger.info(f"G4 Enhanced evaluation logged to Genesis: {genesis_id}")
            except Exception as e:
                logger.warning(f"Failed to log to Genesis: {e}")
            
            # Build response
            response = {
                "approved": result.approved,
                "confidence": round(result.confidence, 3),
                "local_confidence": round(result.local_confidence, 3),
                "web_confidence": round(result.web_confidence, 3) if result.web_confidence else None,
                "sources": result.sources,
                "reasoning": result.reasoning,
                "evaluation_time_ms": round(result.evaluation_time_ms, 1),
                "genesis_id": genesis_id,
                "metadata": {
                    "pii_detected": result.pii_found,
                    "web_verification_used": result.web_confidence is not None
                }
            }
            
            logger.info(f"G4 Enhanced: {result.approved} (confidence: {result.confidence:.2f})")
            
            return jsonify(response), 200
        
        except Exception as e:
            logger.error(f"G4 Enhanced evaluation error: {e}", exc_info=True)
            return jsonify({
                "error": str(e),
                "code": "EVALUATION_ERROR"
            }), 500
    
    @bp.route('/g4-enhanced/batch', methods=['POST'])
    def evaluate_g4_enhanced_batch():
        """
        Batch evaluate multiple claims (rate-limited)
        
        Request JSON:
        {
            "claims": list[str] (max 50),
            "context": dict (optional, applied to all),
            "require_web_verification": bool
        }
        
        Response JSON:
        {
            "results": list[{approved, confidence, ...}],
            "processing_time_ms": float,
            "batch_id": str
        }
        """
        
        try:
            data = request.get_json()
            
            if not data or "claims" not in data:
                return jsonify({
                    "error": "Missing required field: 'claims'",
                    "code": "VALIDATION_ERROR"
                }), 400
            
            claims = data["claims"]
            
            if not isinstance(claims, list):
                return jsonify({
                    "error": "'claims' must be a list",
                    "code": "VALIDATION_ERROR"
                }), 400
            
            if len(claims) > 50:
                return jsonify({
                    "error": "Maximum 50 claims per batch",
                    "code": "RATE_LIMIT"
                }), 429
            
            context = data.get("context")
            require_web_verification = data.get("require_web_verification", True)
            
            # Run batch evaluation
            import time
            start_time = time.time()
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                results = []
                for claim in claims:
                    try:
                        result: G4EvaluationResult = loop.run_until_complete(
                            g4_enhanced.evaluate(
                                claim=claim,
                                context=context,
                                require_web_verification=require_web_verification
                            )
                        )
                        
                        results.append({
                            "claim": claim,
                            "approved": result.approved,
                            "confidence": round(result.confidence, 3),
                            "local_confidence": round(result.local_confidence, 3),
                            "web_confidence": round(result.web_confidence, 3) if result.web_confidence else None
                        })
                    except Exception as e:
                        logger.warning(f"Batch claim evaluation failed: {claim} - {e}")
                        results.append({
                            "claim": claim,
                            "error": str(e)
                        })
            finally:
                loop.close()
            
            processing_time_ms = (time.time() - start_time) * 1000
            
            response = {
                "results": results,
                "processing_time_ms": round(processing_time_ms, 1),
                "batch_size": len(claims),
                "success_count": len([r for r in results if "approved" in r]),
                "error_count": len([r for r in results if "error" in r])
            }
            
            return jsonify(response), 200
        
        except Exception as e:
            logger.error(f"Batch evaluation error: {e}", exc_info=True)
            return jsonify({
                "error": str(e),
                "code": "BATCH_ERROR"
            }), 500
    
    @bp.route('/g4-enhanced/health', methods=['GET'])
    def health_check():
        """Health check for G4 Enhanced endpoint"""
        
        try:
            # Check Perplexity gateway status
            perplexity_status = perplexity_gateway.circuit_breaker.state
            
            response = {
                "status": "healthy",
                "service": "guardian-g4-enhanced",
                "version": "v12",
                "perplexity_circuit_breaker": perplexity_status,
                "cache_size": len(perplexity_gateway.cache.cache)
            }
            
            return jsonify(response), 200
        
        except Exception as e:
            return jsonify({
                "status": "unhealthy",
                "error": str(e)
            }), 503
    
    @bp.route('/g4-enhanced/metrics', methods=['GET'])
    def get_metrics():
        """Get G4 Enhanced evaluation metrics"""
        
        try:
            # Get cache metrics
            cache_stats = {
                "cache_size": len(perplexity_gateway.cache.cache),
                "cache_ttl_seconds": perplexity_gateway.cache.ttl_seconds
            }
            
            # Get circuit breaker metrics
            cb_stats = {
                "state": perplexity_gateway.circuit_breaker.state,
                "failure_count": perplexity_gateway.circuit_breaker.failure_count,
                "last_failure_time": str(perplexity_gateway.circuit_breaker.last_failure_time) if perplexity_gateway.circuit_breaker.last_failure_time else None
            }
            
            response = {
                "cache": cache_stats,
                "circuit_breaker": cb_stats,
                "g4_version": "v12-enhanced"
            }
            
            return jsonify(response), 200
        
        except Exception as e:
            return jsonify({
                "error": str(e)
            }), 500
    
    return bp
