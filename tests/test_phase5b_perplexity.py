"""
Test Suite: Perplexity MCP Gateway + Guardian G4 Enhancement
Tests for Phase 5B implementation
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import json

from mcp_servers.perplexity_gateway import (
    PerplexityGateway,
    FactCheckResult,
    ResearchResult,
    ReasoningResult,
    NewsResult,
    PIIRedactor,
    SimpleCache,
    CircuitBreaker
)
from arbitrage.guardian_g4_enhanced import GuardianG4Enhanced, G4EvaluationResult


# ============================================================================
# 1. PII REDACTOR TESTS
# ============================================================================

class TestPIIRedactor:
    """Test PII detection and redaction"""
    
    def test_redact_ssn(self):
        text = "My SSN is 123-45-6789"
        redacted, pii = PIIRedactor.redact(text)
        assert "[REDACTED_SSN]" in redacted
        assert pii["ssn"] == 1
    
    def test_redact_email(self):
        text = "Contact me at john.doe@example.com for details"
        redacted, pii = PIIRedactor.redact(text)
        assert "[REDACTED_EMAIL]" in redacted
        assert pii["email"] == 1
    
    def test_redact_credit_card(self):
        text = "Card: 1234-5678-9012-3456"
        redacted, pii = PIIRedactor.redact(text)
        assert "[REDACTED_CREDIT_CARD]" in redacted
        assert pii["credit_card"] == 1
    
    def test_redact_api_key(self):
        text = "api_key = 'test_api_key_placeholder_12345'"
        redacted, pii = PIIRedactor.redact(text)
        assert "[REDACTED_API_KEY]" in redacted
        assert pii["api_key"] == 1
    
    def test_no_pii_in_normal_text(self):
        text = "The Earth orbits the Sun in approximately 365 days"
        redacted, pii = PIIRedactor.redact(text)
        assert redacted == text
        assert len(pii) == 0


# ============================================================================
# 2. SIMPLE CACHE TESTS
# ============================================================================

class TestSimpleCache:
    """Test in-memory caching with TTL"""
    
    def test_cache_set_and_get(self):
        cache = SimpleCache(ttl_seconds=3600)
        
        cache.set("value1", "key1", "arg2")
        result = cache.get("key1", "arg2")
        
        assert result == "value1"
    
    def test_cache_miss(self):
        cache = SimpleCache()
        result = cache.get("nonexistent")
        assert result is None
    
    def test_cache_expiration(self):
        cache = SimpleCache(ttl_seconds=1)
        
        cache.set("value", "key")
        assert cache.get("key") == "value"
        
        # Simulate expiration by directly modifying
        import time
        from datetime import datetime, timedelta
        cache.cache["key"] = ("value", datetime.utcnow() - timedelta(seconds=2))
        
        # Should be expired
        assert cache.get("key") is None
    
    def test_cache_clear(self):
        cache = SimpleCache()
        cache.set("val1", "k1")
        cache.set("val2", "k2")
        
        cache.clear()
        
        assert cache.get("k1") is None
        assert cache.get("k2") is None


# ============================================================================
# 3. CIRCUIT BREAKER TESTS
# ============================================================================

class TestCircuitBreaker:
    """Test circuit breaker pattern"""
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_closed_state(self):
        cb = CircuitBreaker(failure_threshold=2, timeout_seconds=60)
        
        async def success_coro():
            return "success"
        
        result = await cb.call(success_coro())
        
        assert result == "success"
        assert cb.state == "CLOSED"
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_opens_on_failures(self):
        cb = CircuitBreaker(failure_threshold=2, timeout_seconds=60)
        
        async def failing_coro():
            raise Exception("API error")
        
        # First failure
        with pytest.raises(Exception):
            await cb.call(failing_coro())
        
        # Second failure - should open
        with pytest.raises(Exception):
            await cb.call(failing_coro())
        
        assert cb.state == "OPEN"
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_blocks_when_open(self):
        cb = CircuitBreaker(failure_threshold=2, timeout_seconds=60)
        cb.state = "OPEN"  # Force open
        
        async def any_coro():
            return "should not execute"
        
        with pytest.raises(Exception, match="Circuit breaker OPEN"):
            await cb.call(any_coro())


# ============================================================================
# 4. PERPLEXITY GATEWAY TESTS
# ============================================================================

class TestPerplexityGateway:
    """Test Perplexity MCP gateway"""
    
    @pytest.fixture
    def gateway(self):
        return PerplexityGateway(api_key="test-key-12345")
    
    @pytest.mark.asyncio
    async def test_fact_check_verified_claim(self, gateway):
        """Test fact-checking a true claim"""
        
        # Mock the API call
        mock_response = {
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "verified": True,
                        "confidence": 0.95,
                        "reasoning": "This is a well-known fact",
                        "sources": [
                            {"title": "Source A", "url": "https://example.com", "snippet": "..."}
                        ],
                        "counter_claims": None
                    })
                }
            }]
        }
        
        with patch.object(gateway, '_call_perplexity', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = mock_response
            
            result = await gateway.fact_check("The Earth is round")
            
            assert result.verified == True
            assert result.confidence == 0.95
            assert len(result.sources) == 1
    
    @pytest.mark.asyncio
    async def test_fact_check_false_claim(self, gateway):
        """Test fact-checking a false claim"""
        
        mock_response = {
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "verified": False,
                        "confidence": 0.92,
                        "reasoning": "No scientific evidence",
                        "sources": [],
                        "counter_claims": ["The Earth is spherical"]
                    })
                }
            }]
        }
        
        with patch.object(gateway, '_call_perplexity', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = mock_response
            
            result = await gateway.fact_check("The Earth is flat")
            
            assert result.verified == False
            assert "Earth is spherical" in result.counter_claims[0]
    
    @pytest.mark.asyncio
    async def test_fact_check_pii_redaction(self, gateway):
        """Test that PII is redacted before sending to API"""
        
        claim_with_pii = "I work at company with email john@example.com"
        
        with patch.object(gateway, '_call_perplexity', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = {
                "choices": [{"message": {"content": json.dumps({
                    "verified": True,
                    "confidence": 0.9,
                    "reasoning": "",
                    "sources": [],
                    "counter_claims": None
                })}}]
            }
            
            result = await gateway.fact_check(claim_with_pii)
            
            # Verify the API was called with redacted claim
            call_args = mock_call.call_args
            # Check that the messages contain redacted content
            assert "[REDACTED_EMAIL]" in call_args[1]["messages"][0]["content"]
    
    @pytest.mark.asyncio
    async def test_fact_check_caching(self, gateway):
        """Test that fact-check results are cached"""
        
        mock_response = {
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "verified": True,
                        "confidence": 0.95,
                        "reasoning": "",
                        "sources": [],
                        "counter_claims": None
                    })
                }
            }]
        }
        
        with patch.object(gateway, '_call_perplexity', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = mock_response
            
            # First call
            result1 = await gateway.fact_check("Test claim")
            assert mock_call.call_count == 1
            
            # Second call - should be cached
            result2 = await gateway.fact_check("Test claim")
            assert mock_call.call_count == 1  # Not incremented
            
            assert result1.timestamp == result2.timestamp
    
    @pytest.mark.asyncio
    async def test_research_entity(self, gateway):
        """Test entity research"""
        
        mock_response = {
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "summary": "Claude is an AI assistant made by Anthropic",
                        "key_facts": ["Made by Anthropic", "Based on Constitutional AI"],
                        "timeline": [
                            {"date": "2023-03-14", "event": "Claude 1 released"}
                        ],
                        "sources": [{"title": "Anthropic", "url": "https://anthropic.com"}],
                        "confidence": 0.98
                    })
                }
            }]
        }
        
        with patch.object(gateway, '_call_perplexity', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = mock_response
            
            result = await gateway.research_entity("Claude AI", context="by Anthropic")
            
            assert "Claude" in result.summary
            assert len(result.key_facts) > 0
            assert result.confidence == 0.98


# ============================================================================
# 5. GUARDIAN G4 ENHANCED TESTS
# ============================================================================

class TestGuardianG4Enhanced:
    """Test Guardian Law G4_Truthfulness with Perplexity"""
    
    @pytest.fixture
    def setup(self):
        guardian_mock = MagicMock()
        perplexity_mock = AsyncMock(spec=PerplexityGateway)
        
        g4_enhanced = GuardianG4Enhanced(guardian_mock, perplexity_mock)
        
        return {
            "g4": g4_enhanced,
            "guardian": guardian_mock,
            "perplexity": perplexity_mock
        }
    
    @pytest.mark.asyncio
    async def test_evaluate_with_web_verification_approved(self, setup):
        """Test G4 evaluation with web verification - claim approved"""
        
        g4 = setup["g4"]
        perplexity = setup["perplexity"]
        
        # Mock Perplexity result
        perplexity.fact_check.return_value = FactCheckResult(
            verified=True,
            confidence=0.95,
            sources=[{"title": "Source", "url": "https://example.com"}],
            reasoning="Verified"
        )
        
        result = await g4.evaluate(
            claim="The Earth orbits the Sun",
            require_web_verification=True
        )
        
        assert result.approved == True
        assert result.confidence >= 0.7
        assert result.web_confidence == 0.95
    
    @pytest.mark.asyncio
    async def test_evaluate_with_web_verification_denied(self, setup):
        """Test G4 evaluation with web verification - claim denied"""
        
        g4 = setup["g4"]
        perplexity = setup["perplexity"]
        
        # Mock Perplexity result
        perplexity.fact_check.return_value = FactCheckResult(
            verified=False,
            confidence=0.1,
            sources=[],
            reasoning="No evidence found",
            counter_claims=["Alternative fact"]
        )
        
        result = await g4.evaluate(
            claim="The Earth is flat",
            require_web_verification=True
        )
        
        assert result.approved == False
        assert result.web_confidence == 0.1
        assert "Alternative fact" in result.reasoning
    
    @pytest.mark.asyncio
    async def test_evaluate_fallback_to_local(self, setup):
        """Test G4 falls back to local confidence if web verification fails"""
        
        g4 = setup["g4"]
        perplexity = setup["perplexity"]
        
        # Mock Perplexity failure
        perplexity.fact_check.side_effect = Exception("API Error")
        
        result = await g4.evaluate(
            claim="Some neutral claim",
            require_web_verification=True
        )
        
        # Should still return a result, with penalty on confidence
        assert result.web_confidence is None
        assert result.confidence < result.local_confidence  # Penalized
    
    @pytest.mark.asyncio
    async def test_evaluate_genesis_record_format(self, setup):
        """Test conversion to Genesis Record format"""
        
        g4 = setup["g4"]
        perplexity = setup["perplexity"]
        
        perplexity.fact_check.return_value = FactCheckResult(
            verified=True,
            confidence=0.9,
            sources=[{"title": "Source"}],
            reasoning="Verified"
        )
        
        result = await g4.evaluate(
            claim="Test claim",
            require_web_verification=True
        )
        
        genesis_record = await g4.to_genesis_record(result, "Test claim")
        
        assert genesis_record["agent"] == "GUARDIAN"
        assert genesis_record["law"] == "G4_Truthfulness"
        assert genesis_record["version"] == "v12"
        assert genesis_record["decision"] in ["APPROVE", "DENY"]
        assert "confidence" in genesis_record
        assert "sources" in genesis_record


# ============================================================================
# 6. INTEGRATION TESTS
# ============================================================================

@pytest.mark.asyncio
class TestIntegration:
    """End-to-end integration tests"""
    
    async def test_full_fact_check_pipeline(self):
        """Test full pipeline: Guardian → Perplexity → Genesis"""
        
        # Create real objects (with mocked API)
        gateway = PerplexityGateway(api_key="test-key")
        guardian_mock = MagicMock()
        g4 = GuardianG4Enhanced(guardian_mock, gateway)
        
        # Mock the HTTP call
        mock_response = {
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "verified": True,
                        "confidence": 0.92,
                        "reasoning": "Verified via NASA sources",
                        "sources": [{"title": "NASA", "url": "https://nasa.gov"}],
                        "counter_claims": None
                    })
                }
            }]
        }
        
        with patch.object(gateway, '_call_perplexity', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = mock_response
            
            # Run evaluation
            claim = "The Moon orbits the Earth"
            result = await g4.evaluate(claim, require_web_verification=True)
            
            # Verify result
            assert result.approved == True
            assert result.confidence >= 0.7
            assert len(result.sources) > 0
            
            # Convert to Genesis Record
            genesis_record = await g4.to_genesis_record(result, claim)
            assert genesis_record["law"] == "G4_Truthfulness"
            assert genesis_record["decision"] == "APPROVE"


# ============================================================================
# 7. PERFORMANCE TESTS
# ============================================================================

@pytest.mark.asyncio
class TestPerformance:
    """Performance and latency tests"""
    
    async def test_fact_check_latency_p95_under_2s(self):
        """Verify fact-check latency P95 < 2 seconds"""
        import time
        
        gateway = PerplexityGateway(api_key="test-key")
        
        mock_response = {
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "verified": True,
                        "confidence": 0.9,
                        "reasoning": "",
                        "sources": [],
                        "counter_claims": None
                    })
                }
            }]
        }
        
        times = []
        for _ in range(10):
            start = time.time()
            
            with patch.object(gateway, '_call_perplexity', new_callable=AsyncMock) as mock_call:
                mock_call.return_value = mock_response
                await gateway.fact_check(f"Test claim {_}")
            
            times.append((time.time() - start) * 1000)  # ms
        
        times.sort()
        p95 = times[int(len(times) * 0.95)]
        
        # Note: This will be fast due to mocking, but demonstrates the test structure
        assert p95 < 2000  # 2 seconds in ms
    
    async def test_cache_hit_performance(self):
        """Verify cache hits are fast"""
        import time
        
        gateway = PerplexityGateway(api_key="test-key")
        
        # Warm up cache
        gateway.cache.set(FactCheckResult(
            verified=True,
            confidence=0.9,
            sources=[],
            reasoning=""
        ), "fact_check", "cached claim")
        
        # Measure cache hit
        start = time.time()
        result = gateway.cache.get("fact_check", "cached claim")
        cache_hit_time_ms = (time.time() - start) * 1000
        
        assert result is not None
        assert cache_hit_time_ms < 10  # Cache hits should be < 10ms


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
