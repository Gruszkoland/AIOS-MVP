# Aider Usage Workflows for ADRION 369

## 📋 Table of Contents
1. [Normal Workflow](#normal-workflow)
2. [Crisis Mode](#crisis-mode)
3. [Healing Mode](#healing-mode)
4. [Architect Mode](#architect-mode)
5. [Real-World Scenarios](#real-world-scenarios)
6. [Best Practices](#best-practices)

---

## Normal Workflow

The standard approach for day-to-day development optimization.

### Step 1: Librarian Analysis
```
@librarian
Analyze the current project. Give me:
1. Summary of last 5 commits
2. Current code complexity (hot spots)
3. Test coverage status
4. Critical dependencies
5. Any technical debt flagged in comments
```

**Expected Output:**
- Git history summary
- File structure analysis
- Dependency versions
- Complexity metrics
- Recommendations for improvement

### Step 2: SAP Planning
```
@sap
Based on the Librarian's analysis, create a prioritized action plan for today.
Include:
- Priority (Critical/High/Medium/Low)
- Effort estimate (hours)
- Risk level (Low/Medium/High)
- Success criteria for each task
- Rollback strategy if needed
```

**Expected Output:**
- Structured plan with ranked tasks
- Risk/effort matrix
- Dependencies between tasks
- Estimated total time

### Step 3: Architecture Review (if needed)
```
@architect
Review this proposed solution against our architecture principles:
1. Follows existing design patterns?
2. Clear module boundaries?
3. Maintainable interfaces?
4. Future-proof design?
```

**Expected Output:**
- Design approval or suggested improvements
- Architectural principles applied
- Alternative designs considered

### Step 4: Implementation
```
# Tell Aider to implement the changes
Start with the highest-priority task from the SAP plan.
Only modify files needed; don't touch unrelated code.
Add comments explaining the "why" of changes.
```

### Step 5: Auditor Validation
```
@auditor
Validate these changes:
1. Code quality against our standards
2. All tests passing?
3. Performance regressions?
4. Security issues?
5. Backward compatibility maintained?
```

**Expected Output:**
- Audit report with quality scores
- Any flags or warnings
- Regression analysis

### Step 6: Sentinel Monitoring
```
@sentinel
Monitor the changes for issues:
1. Run the application
2. Check error logs
3. Verify performance metrics
4. Alert if anything breaks
```

**Expected Output:**
- Status report
- Any errors detected
- Performance impact
- Recommendations

---

## Crisis Mode

Immediate response to production errors or critical failures.

### Activation
```
@sentinel
CRITICAL ALERT: [describe the error]
We have production failures. Deploy immediate fixes.
```

**Sentinel's Response:**
1. ⚡ Detect root cause (< 10 seconds)
2. 🔨 Generate hotfix (< 30 seconds)
3. 📤 Deploy fix (< 1 minute)
4. ✅ Verify stability (< 1 minute)

### Post-Crisis Handoff
```
@healer
The crisis has been resolved temporarily with a hotfix.
Analyze root causes and design a proper long-term fix.
```

---

## Healing Mode

Continuous background optimization (runs every 4 hours or on-demand).

### Full Optimization Cycle
```
@healer
Run a complete optimization cycle on this codebase:
1. Identify technical debt
2. Find refactoring opportunities
3. Improve test coverage
4. Optimize performance
5. Update documentation
6. Clean up dependencies
```

### Targeted Healing
```
@healer
Focus on [specific area]:
- Reduce cyclomatic complexity in [module]
- Improve error handling in [component]
- Add missing documentation for [section]
```

**Expected Output:**
- Healing report with:
  - Debt items addressed
  - Complexity reduction
  - Coverage improvement
  - Performance gains
  - Documentation updates

### Validation After Healing
```
@auditor
Verify the healing changes:
1. No regressions introduced
2. All tests still pass
3. Performance maintained or improved
4. Code quality improved
```

---

## Architect Mode

Deep design review and validation before major changes.

### Pre-Implementation Architecture Review
```
@architect
Before we implement, review the design plan:
- Are we following the existing patterns?
- Should we introduce new abstractions?
- Is this scalable?
- What are the trade-offs?
- Document the key design decisions
```

### Post-Implementation Architecture Audit
```
@architect
Audit the architecture of [module/component]:
- Does it follow our principles?
- Are there violations of SOLID principles?
- Can it be simplified?
- Is the design cohesive?
```

---

## Real-World Scenarios

### Scenario 1: Adding a New Feature

```
👤 DEVELOPER:
I need to add authentication to the API.

📚 LIBRARIAN:
Let me analyze the codebase for existing auth patterns...
[Reports on current security architecture]

📋 SAP:
Here's the plan: 1) Design auth flow, 2) Add JWT support, 
3) Integrate with existing middleware, 4) Add tests

🏗️ ARCHITECT:
I recommend using the middleware pattern we established 
in the payment module. Here's the design...

👨‍💻 IMPLEMENTATION:
[Aider implements the auth feature]

✓ AUDITOR:
Tests pass, code quality good, no regressions. 
Coverage improved from 78% to 82%.

⚠️ SENTINEL:
Auth works correctly. Performance impact: +2ms per request 
(acceptable). All errors handled.

🔧 HEALER:
(runs later) Found unused JWT library dependency. 
Cleaned up. Refactored middleware to reduce complexity.
```

### Scenario 2: Performance Crisis

```
⚠️ ALERT: Response times increased 50%

🚨 SENTINEL:
CRITICAL: Database queries in payment module are slow.
Deploying index optimization immediately...

🔍 HEALER:
Root cause: Missing database index on user_id column.
Also found: N+1 query problem in order service.
Fix deployed. Monitoring for stability.

✓ AUDITOR:
- Regression: NONE
- Performance: Improved by 40%
- Tests: All passing
- Security: No issues
```

### Scenario 3: Technical Debt Reduction

```
📋 SAP:
Monthly maintenance plan ready. Priority: 
1) Unit test coverage (60% → 85%)
2) Refactor payment module (CC too high)
3) Update documentation

🔧 HEALER:
Running 4-hour optimization cycle...
- Refactored 3 complex functions
- Added 24 new unit tests
- Updated 5 doc files
- Updated 2 vulnerable dependencies

✓ AUDITOR:
All checks pass. Code quality: 7.2/10 → 8.1/10
