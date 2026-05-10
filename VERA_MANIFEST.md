# VERA — Governance Manifest

Version: v0.4.x  
Status: Stability Phase (D)

This document defines the technical gate required before
feature expansion and productization.

------------------------------------------------------------

## 1. Definition of Done — Reifegrad D

VERA is considered D-compliant when ALL of the following
conditions are met:

### 1.1 Deterministic Execution
- Identical inputs produce identical outputs
- No uncontrolled randomness in core logic
- All stochastic behavior must be parameterized and documented

### 1.2 Automated Testing
- pytest runs successfully in CI
- Core modules (Bayesian engine, Query builder, Auditor) are covered
- GitHub Actions workflow passes

### 1.3 Error Resilience
- Graceful handling of:
  - API failures
  - Rate limits
  - Empty responses
  - Network interruptions
- No unhandled exceptions in production flow

### 1.4 Metric Transparency
- Every Evidence object contains:
  - Source
  - Weight
  - Timestamp
  - Provenance
- Belief updates are reproducible and traceable
- Health Score is explainable

### 1.5 Architectural Integrity
- Clear module boundaries
- Orchestrator separated from agents
- No circular dependencies between agents
- Core Bayesian engine is independent of UI layer

------------------------------------------------------------

## 2. Governance Rule

All roadmap items must respect the following:

- No feature may violate D stability.
- Any architectural change requires:
  - Manifest update
  - Validator update
  - CI verification

If D is not satisfied, Phase C (Productization) remains locked.

------------------------------------------------------------

## 3. Continuous Validation

The repository includes:

- scripts/validate_manifest.py
- GitHub Actions workflow: Manifest Gate

The CI pipeline is the enforcement mechanism of this manifest.

------------------------------------------------------------

## 4. Development Phases

### Phase A — Research
Experimental exploration, hypothesis testing.

### Phase D — Stability
Governed development with CI gates active.

### Phase B — Community
Documentation, transparency, feedback.

### Phase C — Productization
Deployment, scaling, distribution.
Only unlocked after D is fully satisfied.

------------------------------------------------------------

## 5. Version Policy

- Minor versions (v0.x) may evolve within D.
- Major version v1.0 requires full D compliance.