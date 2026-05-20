# AIOS MVP — Documentation Index

Welcome to the AIOS MVP documentation. This is your map to all technical specifications, design decisions, and contribution guidelines.

## Getting Started

- [**README.md**](../README.md) — Project overview, repository layout, architectural principles
- [**CONTRIBUTING.md**](../CONTRIBUTING.md) — How to contribute, PR process, unsafe code rules, Definition of Done

## Architecture & Design

- [**ARCHITECTURE.md**](./ARCHITECTURE.md) — High-level system design, data flows, kernel + IPC + agents topology
- [**CAPABILITY_MODEL.md**](./CAPABILITY_MODEL.md) — Security model, capability types, enforcement mechanisms
- [**162D Decision Space**](./decision-space.md) — 3 perspectives × 6 modes × 9 Guardian Laws topology

## RFC (Request for Comment)

Before implementing major architectural changes, read and participate in the RFC process:

- [**RFC Template**](./rfc/TEMPLATE.md) — How to propose an RFC
- [**RFC #0001: Cognitive Agent**](./rfc/0001-cognitive-agent.md) — LLM agent integration design
- [**Active RFCs**](./rfc/README.md) — List of all open and merged RFCs

## Project Management

- [**STATUS.md**](./STATUS.md) — Current Sprint status, completed milestones, next deliverables
- [**go-no-go.md**](./go-no-go.md) — Sprint 1 GO/NO-GO criteria and decision framework
- [**DECISIONS.md**](./decisions.md) — Architecture Decision Records (ADRs)

## Guardian Laws

- [**Guardian Laws Canonical**](./GUARDIAN_LAWS_CANONICAL.json) — Authoritative definition (9 laws, severities, veto rules)
- [**Evaluation Pipeline**](./guardian-pipeline.md) — How Guardian Laws are checked in code and CI

## Benchmarking & Performance

- [**Performance Baselines**](./performance-baselines.md) — Latency targets, IPC throughput, kernel overhead

## Troubleshooting & FAQs

- [**FAQ**](./FAQ.md) — Common questions, setup issues, debugging tips
- [**Troubleshooting**](./TROUBLESHOOTING.md) — Known issues and solutions

---

**Last updated:** 2026-05-20
**Maintainer:** Adrian Halicki (@Gruszkoland)
