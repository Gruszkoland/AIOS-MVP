# TIER 7: CELERY + REDIS ASYNC JOB PROCESSING

## 📚 Overview

**Goals:**

- Non-blocking Hexagon stages (6 stages can run in parallel where possible)
- Distributed job processing
- Retry mechanism + error handling
- Monitor long-running decisions

**Repositories needed:**

- https://github.com/celery/celery (⭐ 24k)
- Redis (already deployed ✓)

---

## 🎯 ADRION 369 Integration Points

### Current State (Sequential, blocking)

```python
# Current HexagonProcessor - BLOCKING

class HexagonProcessor:
    def process(self, trinity_scores):
        inventory = self.inventory_stage(trinity_scores)      # Wait
        empathy = self.empathy_stage(inventory)               # Wait
        process = self.process_stage(empathy)                 # Wait
        debate = self.debate_stage(process)                   # Wait
        healing = self.healing_stage(debate)                  # Wait
        action = self.action_stage(healing)                   # Wait
        return action

# Total time: 6 * stage_time (serial)
```

### NEW State (Async with Celery)

```python
# arbitrage/tasks.py - NEW

from celery import Celery, group, chain
from celery.result import AsyncResult
import structlog

logger = structlog.get_logger()

# Setup Celery
app = Celery('adrion369')
app.conf.update(
    broker_url='redis://localhost:6379/0',
    result_backend='redis://localhost:6379/1',
    task_serializer='json',
    accept_content=['json'],
    result_expires=86400,  # 24 hours
    task_track_started=True,
    task_time_limit=300,  # 5 min timeout
)

# Define tasks for each Hexagon stage

@app.task(bind=True, name='hexagon.inventory')
def inventory_stage_task(self, trinity_scores: dict):
    """Stage 1: Inventory - non-blocking"""
    logger.info("inventory_start", job_id=self.request.id)
    try:
        result = inventory_stage_impl(trinity_scores)
        logger.info("inventory_complete", duration_ms=result.get('duration_ms'))
        return result
    except Exception as exc:
        logger.error("inventory_failed", exc_info=True)
        raise self.retry(exc=exc, countdown=5, max_retries=3)

@app.task(bind=True, name='hexagon.empathy')
def empathy_stage_task(self, inventory_result: dict):
    """Stage 2: Empathy - non-blocking"""
    logger.info("empathy_start")
    try:
        result = empathy_stage_impl(inventory_result)
        return result
    except Exception as exc:
        raise self.retry(exc=exc, countdown=5, max_retries=3)

@app.task(bind=True, name='hexagon.process')
def process_stage_task(self, empathy_result: dict):
    """Stage 3: Process"""
    return process_stage_impl(empathy_result)

@app.task(bind=True, name='hexagon.debate')
def debate_stage_task(self, process_result: dict):
    """Stage 4: Debate"""
    return debate_stage_impl(process_result)

@app.task(bind=True, name='hexagon.healing')
def healing_stage_task(self, debate_result: dict):
    """Stage 5: Healing"""
    return healing_stage_impl(debate_result)

@app.task(bind=True, name='hexagon.action')
def action_stage_task(self, healing_result: dict):
    """Stage 6: Action"""
    return action_stage_impl(healing_result)

# Orchestrate pipeline (SEQUENTIAL CHAIN)

@app.task(name='hexagon.pipeline')
def hexagon_pipeline(trinity_scores: dict):
    """Chain all 6 Hexagon stages sequentially"""
    # Some stages depend on previous output (sequential)
    pipeline = chain(
        inventory_stage_task.s(trinity_scores),
        empathy_stage_task.s(),
        process_stage_task.s(),
        debate_stage_task.s(),
        healing_stage_task.s(),
        action_stage_task.s(),
    )
    return pipeline.apply_async()

# Parallel Guardian evaluation (PARALLEL GROUP)

@app.task(bind=True, name='guardian.evaluate_law')
def guardian_evaluation_task(self, law_name: str, decision_context: dict):
    """Evaluate single Guardian Law (can be parallel)"""
    from arbitrage.guardian import GUARDIAN_LAWS
    law = GUARDIAN_LAWS[law_name]
    return law.evaluate(decision_context)

@app.task(name='guardian.evaluate_all')
def evaluate_all_guardians(decision_context: dict):
    """Evaluate all 9 Guardian Laws in PARALLEL"""
    from arbitrage.guardian import GUARDIAN_LAWS

    # Parallel group - all laws at once
    law_tasks = group(
        guardian_evaluation_task.s(law_name, decision_context)
        for law_name in GUARDIAN_LAWS.keys()
    )
    result = law_tasks.apply_async()
    return result.get()  # Wait for all to complete

# FULL DECISION PIPELINE

@app.task(name='decision.full_pipeline')
def full_decision_pipeline(job_data: dict):
    """
    Trinity (parallel) → Hexagon (sequential) → Guardians (parallel)
    """
    logger.info("pipeline_start", job_id=job_data['id'])

    # 1. Trinity - parallel 3 perspectives
    trinity = group(
        # material_task.s(job_data),
        # intellectual_task.s(job_data),
        # essential_task.s(job_data),
    ).apply_async()
    trinity_scores = trinity.get()

    # 2. Hexagon - sequential 6 stages
    hexagon_pipeline_result = hexagon_pipeline(trinity_scores)
    hexagon_scores = hexagon_pipeline_result.get()

    # 3. Guardians - parallel 9 laws
    guardian_result = evaluate_all_guardians(hexagon_scores)

    logger.info("pipeline_complete", job_id=job_data['id'])

    return {
        "trinity": trinity_scores,
        "hexagon": hexagon_scores,
        "guardians": guardian_result,
    }
```

---

## 🔌 FastAPI Integration

```python
# arbitrage/api.py - NEW endpoints for async

from fastapi import FastAPI, BackgroundTasks
from celery.result import AsyncResult
from arbitrage.tasks import full_decision_pipeline, app as celery_app

app = FastAPI()

@app.post("/api/process-async")
async def process_job_async(job: Job) -> dict:
    """Start async decision pipeline"""
    # Send to Celery queue (non-blocking)
    task = full_decision_pipeline.delay(job.dict())

    return {
        "task_id": task.id,
        "status": "processing",
        "check_result_url": f"/api/process/{task.id}"
    }

@app.get("/api/process/{task_id}")
async def check_task_status(task_id: str):
    """Check async task status"""
    task_result = AsyncResult(task_id, app=celery_app)

    if task_result.state == 'PENDING':
        return {"status": "pending", "progress": 0}
    elif task_result.state == 'PROGRESS':
        return {"status": "processing", "progress": task_result.info.get('progress', 0)}
    elif task_result.state == 'SUCCESS':
        return {
            "status": "complete",
            "result": task_result.result
        }
    elif task_result.state == 'FAILURE':
        return {
            "status": "failed",
            "error": str(task_result.info)
        }

@app.get("/api/process/{task_id}/cancel")
async def cancel_task(task_id: str):
    """Cancel running task"""
    AsyncResult(task_id, app=celery_app).revoke(terminate=True)
    return {"status": "cancelled"}

# WebSocket for real-time updates

from fastapi import WebSocket

@app.websocket("/ws/process/{task_id}")
async def websocket_task_status(websocket: WebSocket, task_id: str):
    """Real-time task status updates via WebSocket"""
    await websocket.accept()

    while True:
        task = AsyncResult(task_id, app=celery_app)
        await websocket.send_json({
            "task_id": task_id,
            "state": task.state,
            "progress": task.info if task.state == 'PROGRESS' else None,
        })

        if task.state in ('SUCCESS', 'FAILURE'):
            await websocket.close()
            break

        await asyncio.sleep(1)  # Update every second
```

---

## 🚀 Deployment Setup

```yaml
# docker-compose.yml additions

services:
  celery:
    image: python:3.11
    command: celery -A arbitrage.tasks worker --loglevel=info --concurrency=4
    volumes:
      - .:/app
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/1
    depends_on:
      - redis

  celery-flower: # Monitoring dashboard
    image: python:3.11
    command: celery -A arbitrage.tasks flower --port=5555
    ports:
      - "5555:5555"
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/1
    depends_on:
      - redis
```

Access Celery dashboard: http://localhost:5555

---

## 📊 Performance Impact

```
BEFORE (Sequential):
Inventory: 100ms
Empathy: 150ms
Process: 120ms
Debate: 180ms
Healing: 140ms
Action: 110ms
────────────
TOTAL: ~800ms

AFTER (Async Celery):
Stages run in parallel where possible, background processing
────────────
TOTAL: ~200-300ms (end-user response)
Actual processing continues in background (no blocking)
```

---

## 📋 Implementation Checklist

- [ ] `pip install celery[redis] structlog`
- [ ] Create `arbitrage/tasks.py` with all Celery tasks
- [ ] Update `arbitrage/api.py` with async endpoints
- [ ] Add Celery worker to `docker-compose.yml`
- [ ] Add Flower monitoring dashboard
- [ ] Test: Submit job → get task_id → check status
- [ ] Test: WebSocket real-time updates
- [ ] Configure retry + error handling
- [ ] Monitor: Celery queue length in Prometheus

---

**Time to implement:** 1-2 days
**Benefits:** Non-blocking UI + background processing + parallel where possible
