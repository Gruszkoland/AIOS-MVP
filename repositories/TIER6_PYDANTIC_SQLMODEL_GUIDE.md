# TIER 6: PYDANTIC V2 + SQLMODEL DATA LAYER

## 📚 Overview

**Goals:**

- Type-safe data validation (Trinity, Hexagon, Guardian inputs)
- ORM + validation combined (SQLModel)
- Auto OpenAPI schema generation
- Better developer experience

**Repositories needed:**

- https://github.com/pydantic/pydantic (⭐ 20.8k)
- https://github.com/tiangolo/sqlmodel (⭐ 4k)

---

## 🎯 ADRION 369 Integration Points

### Current State (Class-based, manual validation)

```python
# arbitrage/api.py - Current

def create_trinity_analysis(job_data: dict):
    # Manual validation
    if "id" not in job_data:
        raise ValueError("Missing job id")
    if job_data.get("type") not in ["arbitrage", "analysis", "decision"]:
        raise ValueError("Invalid job type")

    # Pass raw dict
    trinity_result = evaluate_trinity(job_data)
    return trinity_result
```

### NEW State (Pydantic V2, type-safe)

```python
# arbitrage/models.py - NEW

from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime

class Job(BaseModel):
    """Job data model with validation"""
    id: str = Field(..., min_length=1, description="Unique job ID")
    type: str = Field(..., description="Job type")
    priority: int = Field(default=5, ge=1, le=10, description="Priority (1-10)")
    context: dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @field_validator('type')
    @classmethod
    def validate_type(cls, v):
        allowed = {"arbitrage", "analysis", "decision"}
        if v not in allowed:
            raise ValueError(f"type must be one of {allowed}")
        return v

class TrinityScores(BaseModel):
    """Trinity evaluation results"""
    material: float = Field(..., ge=0, le=1, description="Material feasibility score")
    intellectual: float = Field(..., ge=0, le=1, description="Intellectual correctness")
    essential: float = Field(..., ge=0, le=1, description="Essential alignment")
    overall: float = Field(..., ge=0, le=1, description="Combined score")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class HexagonStageResult(BaseModel):
    """Hexagon stage output"""
    stage_name: str  # inventory, empathy, process, debate, healing, action
    duration_ms: float
    result: dict
    errors: Optional[list] = None

class GuardianEvaluation(BaseModel):
    """Guardian Law validation"""
    law_name: str
    passed: bool
    score: float = Field(ge=0, le=1)
    reason: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class DecisionResult(BaseModel):
    """Complete decision output"""
    decision_id: str
    job: Job
    trinity_scores: TrinityScores
    hexagon_stages: list[HexagonStageResult]
    guardian_evaluations: list[GuardianEvaluation]
    final_decision: str  # APPROVED, DENIED, CONDITIONAL
    justification: str

# In FastAPI endpoint:
from fastapi import FastAPI, HTTPException

app = FastAPI(title="ADRION 369 API", version="2.0")

@app.post("/api/process", response_model=DecisionResult)
async def process_job(job: Job) -> DecisionResult:
    """Process job through Trinity→Hexagon→Guardians"""
    # Validation automatic (Pydantic)
    # OpenAPI schema auto-generated

    trinity_result = evaluate_trinity(job)
    hexagon_result = process_hexagon(trinity_result)
    guardian_result = evaluate_guardians(hexagon_result)

    return DecisionResult(
        decision_id=job.id,
        job=job,
        trinity_scores=trinity_result,
        hexagon_stages=hexagon_result,
        guardian_evaluations=guardian_result,
        final_decision="APPROVED" if guardian_result.passed else "DENIED",
        justification="..."
    )
```

---

## 🔄 SQLModel Integration (Database)

### Genesis Record ORM Models

```python
# arbitrage/models.py - SQLModel

from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from datetime import datetime
import uuid

class JobDB(SQLModel, table=True):
    """Jobs table"""
    __tablename__ = "jobs"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    type: str = Field(index=True)
    priority: int = Field(ge=1, le=10)
    context: dict = Field(sa_type=JSON)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    trinity_result: Optional["TrinityResultDB"] = Relationship(back_populates="job")
    hexagon_results: list["HexagonResultDB"] = Relationship(back_populates="job")
    guardian_evaluations: list["GuardianEvaluationDB"] = Relationship(back_populates="job")

class TrinityResultDB(SQLModel, table=True):
    """Trinity scores (immutable audit log)"""
    __tablename__ = "trinity_results"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    job_id: str = Field(foreign_key="jobs.id", index=True)
    material_score: float = Field(ge=0, le=1)
    intellectual_score: float = Field(ge=0, le=1)
    essential_score: float = Field(ge=0, le=1)
    overall_score: float = Field(ge=0, le=1)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    job: Optional[JobDB] = Relationship(back_populates="trinity_result")

class HexagonResultDB(SQLModel, table=True):
    """Hexagon stage results"""
    __tablename__ = "hexagon_results"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    job_id: str = Field(foreign_key="jobs.id", index=True)
    stage: str = Field(index=True)  # inventory, empathy, etc
    stage_order: int = Field(ge=0, le=5)
    duration_ms: float
    result: dict = Field(sa_type=JSON)
    errors: Optional[list] = Field(sa_type=JSON, default=None)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    job: Optional[JobDB] = Relationship(back_populates="hexagon_results")

class GuardianEvaluationDB(SQLModel, table=True):
    """Guardian Laws evaluations (audit trail)"""
    __tablename__ = "guardian_evaluations"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    job_id: str = Field(foreign_key="jobs.id", index=True)
    law_name: str = Field(index=True)
    passed: bool = Field(index=True)
    score: float = Field(ge=0, le=1)
    reason: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    job: Optional[JobDB] = Relationship(back_populates="guardian_evaluations")

# Usage in CRUD operations

from sqlalchemy.orm import Session
from sqlmodel import create_engine, Session, select

engine = create_engine("postgresql://...genesis_record")

def save_decision(session: Session, decision: DecisionResult):
    """Save complete decision to genesis_record"""
    job_db = JobDB(**decision.job.dict())
    session.add(job_db)
    session.flush()

    trinity_db = TrinityResultDB(
        job_id=job_db.id,
        **decision.trinity_scores.dict()
    )
    session.add(trinity_db)

    for stage in decision.hexagon_stages:
        hexagon_db = HexagonResultDB(
            job_id=job_db.id,
            **stage.dict()
        )
        session.add(hexagon_db)

    for guardian in decision.guardian_evaluations:
        guardian_db = GuardianEvaluationDB(
            job_id=job_db.id,
            **guardian.dict()
        )
        session.add(guardian_db)

    session.commit()

def query_decisions_by_law_violation(session: Session, law_name: str):
    """Query all decisions that violated a specific law"""
    statement = select(JobDB).join(GuardianEvaluationDB).where(
        (GuardianEvaluationDB.law_name == law_name) &
        (GuardianEvaluationDB.passed == False)
    )
    return session.exec(statement).all()
```

---

## 📋 Implementation Checklist

- [ ] Install Pydantic V2 + SQLModel: `pip install pydantic sqlmodel`
- [ ] Create `arbitrage/models.py` with all models
- [ ] Update `arbitrage/api.py` to use Pydantic models
- [ ] Update `arbitrage/trinity.py` to return Pydantic TrinityScores
- [ ] Update `arbitrage/database.py` to use SQLModel ORM
- [ ] Update tests to use Pydantic models
- [ ] Verify OpenAPI schema at `/docs` endpoint
- [ ] Migration: existing data → new schema (Alembic)

---

**Time to implement:** 2-3 days
**Benefits:** Type safety + validation + auto docs + ORM
