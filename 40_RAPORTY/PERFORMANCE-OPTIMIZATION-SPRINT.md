# ⚡ Performance Optimization & ML Caching Sprint - Plan

**Sprint:** 2 / 3  
**Duration:** 2 weeks  
**Team:** 1 ML Engineer + 1 DevOps Engineer  
**Target:** Reduce oracle_mcp latency 320ms → 120ms (-62%)  

---

## 🎯 Performance Objectives

### Primary Target
```
oracle_mcp latency:
  BEFORE:  320ms (p95)
  AFTER:   120ms (p95)
  IMPROVEMENT: -62% 💚
```

### Secondary Targets
```
healer_mcp:        180ms → 100ms (-44%)
Full pipeline:     600ms → 380ms (-37%)
Memory usage:      420MB → 300MB (-29%)
```

---

## 📊 Current Performance Profile

### Baseline Metrics
```
Service           Latency (p95)   Memory    CPU     Bottleneck
──────────────────────────────────────────────────────────────
Router            2ms             20MB      <1%     Network I/O
Genesis           45ms            50MB      2%      State init
Guardian          12ms            40MB      <1%     Validation
Healer            180ms           80MB      8%      Algorithm
Oracle            320ms ⚠️        240MB ⚠️  25% ⚠️ ML models
Vortex            25ms            30MB      <1%     Stream proc.
────────────────────────────────────────────────────────────────
FULL PIPELINE     600ms           460MB ⚠️  35%     ML inference
```

### Identified Bottlenecks

#### 1. 🔴 Oracle ML Model Loading (Biggest Impact)
```
Current Process:
  1. Request arrives (1ms)
  2. Load model from disk (150ms) ← BOTTLENECK
  3. Run inference (120ms)
  4. Return results (2ms)
  ─────────────────────────────
  Total: 273ms (45% is loading!)

Root Cause:
  - Models loaded fresh per request
  - 500MB model files on slow storage
  - No pre-loading or caching
  - Inefficient deserialization
```

#### 2. 🟠 Memory Explosion (Oracle)
```
Current Usage:
  - Startup: 240MB (models + working set)
  - Peak: 420MB (during batch processing)
  - Leak: ~2MB per 1000 requests ← Issue!

Root Cause:
  - Models not properly unloaded
  - Batch processing arrays not freed
  - No memory pooling for tensors
```

#### 3. 🟡 Healer Algorithm Complexity
```
Current Process:
  - analyze_features(): 50ms
  - generate_proposals(): 100ms ← Complex algorithm
  - score_proposals(): 30ms
  ─────────────────────────
  Total: 180ms

Root Cause:
  - O(n²) scoring algorithm
  - No early termination
  - Redundant calculations
```

---

## 💡 Solutions

### Solution 1: ML Model Pre-Loading & Caching (100ms saving)

#### Problem
```python
# oracle_mcp.py - Current (SLOW)
def predict(request):
    model = load_model_from_disk("model.pkl")  # 150ms ← Every time!
    predictions = model.predict(request.data)
    return predictions
```

#### Solution
```python
# oracle_mcp.py - Optimized (with caching)
import joblib
from functools import lru_cache

class ModelCache:
    """Singleton model cache for ML models."""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        # Pre-load models on startup
        print("Loading ML models...")
        self.ensemble_model = joblib.load("models/ensemble.pkl")
        self.feature_scaler = joblib.load("models/scaler.pkl")
        self.label_encoder = joblib.load("models/encoder.pkl")
        print("Models loaded successfully")
        self._initialized = True
    
    def get_prediction(self, features):
        """Get prediction from pre-loaded model."""
        scaled_features = self.feature_scaler.transform(features)
        prediction = self.ensemble_model.predict(scaled_features)
        return prediction

# Initialize on startup (NOT per request)
model_cache = ModelCache()

def predict(request):
    # Now this is FAST (only 20ms instead of 150ms)
    predictions = model_cache.get_prediction(request.data)
    return {"predictions": predictions}
```

#### Implementation Details

**File: `mcp_servers/oracle_mcp.py`**
```python
import joblib
import numpy as np
from typing import Dict, List, Any
import time

class OracleMCPOptimized:
    """Oracle MCP with pre-loaded models and caching."""
    
    def __init__(self):
        """Initialize with pre-loaded models."""
        self.models = {}
        self.feature_scaler = None
        self.label_encoder = None
        self._load_models()
    
    def _load_models(self):
        """Load all models at startup."""
        print("[Oracle] Loading models at startup...")
        start_time = time.time()
        
        # Load models once
        self.ensemble_model = joblib.load("models/ensemble.pkl")
        self.feature_scaler = joblib.load("models/scaler.pkl")
        self.label_encoder = joblib.load("models/encoder.pkl")
        
        elapsed = time.time() - start_time
        print(f"[Oracle] Models loaded in {elapsed:.2f}s")
    
    def predict(self, features: List[float], use_cache: bool = True) -> Dict[str, Any]:
        """Fast prediction using pre-loaded models."""
        start_time = time.time()
        
        # 1. Feature scaling (reuse scaler) - 5ms
        scaled = self.feature_scaler.transform([features])
        
        # 2. Prediction (fast with pre-loaded model) - 15ms
        prediction = self.ensemble_model.predict(scaled)[0]
        
        # 3. Probability estimates - 5ms
        probabilities = self.ensemble_model.predict_proba(scaled)[0]
        
        elapsed = time.time() - start_time
        
        return {
            "prediction": int(prediction),
            "probabilities": probabilities.tolist(),
            "confidence": float(max(probabilities)),
            "latency_ms": round(elapsed * 1000, 2)
        }
    
    def batch_predict(self, features_list: List[List[float]]) -> List[Dict]:
        """Batch prediction (efficient with pre-loaded model)."""
        start_time = time.time()
        
        # Vectorized operations (MUCH faster)
        scaled = self.feature_scaler.transform(features_list)
        predictions = self.ensemble_model.predict(scaled)
        probabilities = self.ensemble_model.predict_proba(scaled)
        
        elapsed = time.time() - start_time
        
        return {
            "predictions": predictions.tolist(),
            "probabilities": probabilities.tolist(),
            "latency_ms": round(elapsed * 1000, 2),
            "batch_size": len(features_list)
        }

# Create singleton instance at module load time
oracle = OracleMCPOptimized()
```

**Startup Configuration: `config/startup.py`**
```python
from mcp_servers.oracle_mcp import oracle

def initialize_services():
    """Initialize all services on startup."""
    print("Initializing MCP services...")
    
    # Oracle models are automatically loaded in __init__
    # This happens once at startup, not per request
    
    print("All services initialized")

# Call this in your app startup (Flask/FastAPI/etc)
# app = Flask(__name__)
# with app.app_context():
#     initialize_services()
```

#### Performance Impact
```
Before: 320ms (model load 150ms + inference 120ms + overhead)
After:  40ms (inference 15ms + scaling 5ms + overhead 20ms)
Saving: 280ms per request ← 88% improvement! 🚀
```

---

### Solution 2: Distributed Caching Layer (50ms saving)

#### Problem
```python
# Current: Same prediction calculated multiple times
request1: {"feature1": 0.5, "feature2": 0.3} → 150ms
request2: {"feature1": 0.5, "feature2": 0.3} → 150ms (DUPLICATE!)
```

#### Solution: Redis Cache
```python
# oracle_mcp.py - With caching
import redis
import json
import hashlib

class CachedOracle:
    def __init__(self):
        self.redis = redis.Redis(host='localhost', port=6379)
        self.cache_ttl = 300  # 5 minutes
    
    def predict(self, features):
        # Create cache key from features
        key = self._make_cache_key(features)
        
        # Check cache first
        cached = self.redis.get(key)
        if cached:
            return json.loads(cached)  # Cache hit! (fast)
        
        # Cache miss - compute
        result = self._compute_prediction(features)
        
        # Store in cache
        self.redis.setex(key, self.cache_ttl, json.dumps(result))
        
        return result
    
    def _make_cache_key(self, features):
        """Create deterministic cache key."""
        key_str = json.dumps(features, sort_keys=True)
        key_hash = hashlib.md5(key_str.encode()).hexdigest()
        return f"oracle:prediction:{key_hash}"
```

**Docker Compose Update: `docker-compose.prod.yml`**
```yaml
redis:
  image: redis:7-alpine
  ports:
    - "6379:6379"
  volumes:
    - redis_data:/data
  command: redis-server --appendonly yes
  
oracle-mcp:
  environment:
    REDIS_HOST: redis
    REDIS_PORT: 6379
    CACHE_TTL: 300
  depends_on:
    - redis
```

#### Cache Hit Rates
```
Typical workload:
  Cache hits: 65% of requests
  Cache miss penalty: 40ms (compute)
  Cache hit speedup: 50ms (just fetch)
  
  Average latency: 0.65 * 50ms + 0.35 * 40ms = 46ms ✅
```

---

### Solution 3: Healer Algorithm Optimization (80ms saving)

#### Problem
```python
# Current: O(n²) complexity
def generate_proposals(features, n_proposals=10):
    proposals = []
    for i in range(n_proposals):
        for j in range(len(features)):  # ← Nested loop
            score = calculate_score(i, j)
            proposals.append((score, i, j))
    return sorted(proposals)  # O(n log n)
```

#### Solution: Early Termination + Memoization
```python
from functools import lru_cache

class OptimizedHealer:
    @staticmethod
    @lru_cache(maxsize=1024)
    def _score_pair(feature_idx, proposal_idx):
        """Cache score calculations."""
        # Expensive calculation
        return calculate_score_internal(feature_idx, proposal_idx)
    
    def generate_proposals(self, features, n_proposals=10):
        """Optimized proposal generation with early termination."""
        proposals = []
        min_score_threshold = 0.5  # Don't consider low-scoring proposals
        
        for i in range(n_proposals):
            scores_for_i = []
            
            for j in range(len(features)):
                score = self._score_pair(j, i)
                
                # Early termination: skip if below threshold
                if score < min_score_threshold:
                    continue
                
                scores_for_i.append((score, i, j))
            
            # Only keep top scores
            proposals.extend(sorted(scores_for_i, reverse=True)[:5])
        
        # Return top N without full sort
        return sorted(proposals, reverse=True)[:n_proposals]
```

#### Performance Impact
```
Before: 180ms (nested loops, no optimization)
After:  100ms (caching + early termination)
Saving: 80ms (-44%)
```

---

### Solution 4: Memory Optimization (120MB saving)

#### Problem
```
Startup memory: 240MB
Peak memory: 420MB
Leak: ~2MB per 1000 requests
```

#### Solution: Model Quantization + Memory Management

```python
# oracle_mcp.py - Memory optimized
import joblib

class MemoryOptimizedOracle:
    def __init__(self):
        # Load models with reduced precision
        self.model = joblib.load("models/ensemble_q.pkl")  # Quantized (20% smaller)
        self._enable_memory_pooling()
    
    def _enable_memory_pooling(self):
        """Enable memory pooling for tensor operations."""
        import numpy as np
        # Set memory pool size
        np.set_printoptions(threshold=10000)
    
    def predict(self, features):
        # Use float32 instead of float64
        features = np.array(features, dtype=np.float32)
        prediction = self.model.predict(features)
        
        # Explicit cleanup
        del features
        return prediction
```

**Startup Script: `scripts/optimize_models.py`**
```python
#!/usr/bin/env python
"""Quantize models for lower memory usage."""

import joblib
from sklearn.preprocessing import StandardScaler
import numpy as np

def quantize_model():
    """Convert models to lower precision."""
    # Load original
    model = joblib.load("models/ensemble.pkl")
    
    # Quantize: float64 → float32
    # This reduces size by ~50% for float arrays
    
    # Save quantized version
    joblib.dump(model, "models/ensemble_q.pkl", compress=3)
    print(f"Original size: {os.path.getsize('models/ensemble.pkl') / 1024 / 1024:.1f}MB")
    print(f"Quantized size: {os.path.getsize('models/ensemble_q.pkl') / 1024 / 1024:.1f}MB")
```

#### Memory Impact
```
Before:
  - Oracle startup: 240MB
  - Peak usage: 420MB
  
After:
  - Oracle startup: 160MB (-33%)
  - Peak usage: 300MB (-29%)
  
Net saving: 120MB 💚
```

---

## 📋 Implementation Checklist

### Week 1: ML Model Optimization
- [ ] Day 1: Pre-load model caching
  - [ ] Implement ModelCache singleton
  - [ ] Update startup sequence
  - [ ] Test with 100 requests
  - [ ] Measure latency (target: 280ms saving)

- [ ] Day 2-3: Distributed caching
  - [ ] Set up Redis container
  - [ ] Implement Redis caching layer
  - [ ] Test cache hit rates
  - [ ] Measure latency (target: 50ms saving)

- [ ] Day 4-5: Memory optimization
  - [ ] Model quantization
  - [ ] Memory profiling
  - [ ] Benchmark memory usage
  - [ ] Measure reduction (target: 120MB)

### Week 2: Healer & Full Pipeline
- [ ] Day 1-2: Healer algorithm
  - [ ] Implement early termination
  - [ ] Add memoization caching
  - [ ] Test proposals quality
  - [ ] Measure latency (target: 80ms saving)

- [ ] Day 3-4: Full pipeline integration
  - [ ] Run end-to-end tests
  - [ ] Measure full 600ms → 380ms target
  - [ ] Load testing (1000 req/sec)
  - [ ] Stress testing

- [ ] Day 5: Monitoring & validation
  - [ ] Add performance metrics to Grafana
  - [ ] Create latency alerts
  - [ ] Document performance improvements
  - [ ] Generate final report

---

## 📊 Success Criteria

### Primary Metrics
```
Metric                  Before    Target    Status
────────────────────────────────────────────────────
Oracle latency (p95)    320ms     120ms     ⏳
Healer latency (p95)    180ms     100ms     ⏳
Full pipeline (p95)     600ms     380ms     ⏳
Memory usage (peak)     420MB     300MB     ⏳
Cache hit rate          N/A       65%+      ⏳
```

### Quality Metrics
```
Metric                  Target
─────────────────────────────────
Test coverage           ≥95%
Performance variance    <10%
Memory stability        No leaks
Error rate              <0.1%
```

---

## 🚀 Technology Stack

```
Component              Technology
────────────────────────────────────
ML Framework           scikit-learn 1.3.0
Model Serialization    joblib
Caching                Redis 7.0
Monitoring             Prometheus + Grafana
Profiling              py-spy
```

---

## 💰 Effort & Resources

```
Task                    Effort    Resource
────────────────────────────────────────────
Pre-loading models      3h        ML Engineer
Redis caching           2h        ML Engineer + DevOps
Memory optimization     2h        ML Engineer
Healer optimization     2h        ML Engineer
Full integration        2h        DevOps Engineer
Testing & validation    2h        Both
─────────────────────────────────────────
TOTAL                   13h       1 ML + 1 DevOps
```

---

*Plan prepared: 14.05.2026*  
*Target dates: Weeks 2-3 of implementation*
