# ADRION Architecture Formula

## Mission Statement (Formula Repository)

This repository is the canonical source of truth for ADRION model definitions.

It owns the 3-6-9 semantics, D162 decision-space contracts, Guardian Law definitions,
architecture decision records, and machine-readable schemas consumed by downstream repositories.

It does not own product runtime code, operational deployment automation,
or environment-specific infrastructure execution.

## Repository Role

- Upstream canonical governance for ADRION
- Contract source for Architecture and System repositories
- Stable, versioned, implementation-agnostic definitions

## Dependency Rule

Formula -> Architecture -> System

No downstream repository should redefine canonical contracts locally.
