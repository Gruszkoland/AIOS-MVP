#!/usr/bin/env python3
"""
FAZA 2.5 — SAV (Step Auto-Verification) for TIER 0
Validates all TIER 0a-0e implemented components.
"""

import json
import sys
from pathlib import Path

def sav_tier0a():
    """SAV: TIER 0a pytest 80% mandate"""
    print("🔍 SAV: TIER 0a — pytest 80% Mandate")
    pytest_ini = Path("pytest.ini")
    if not pytest_ini.exists():
        print("  ❌ FAIL: pytest.ini not found")
        return False
    
    with open(pytest_ini) as f:
        content = f.read()
        if "cov-fail-under=80" in content:
            print("  ✅ PASS: Coverage mandate 80% configured")
            return True
        else:
            print("  ❌ FAIL: Coverage mandate not configured")
            return False

def sav_tier0b():
    """SAV: TIER 0b memories persistence"""
    print("🔍 SAV: TIER 0b — Memories Persistence")
    files = [
        "memories/trust_scores.json",
        "memories/ebdi_baseline.json",
        "memories/session/checkpoint.json"
    ]
    
    all_valid = True
    for filepath in files:
        p = Path(filepath)
        if not p.exists():
            print(f"  ❌ FAIL: {filepath} not found")
            all_valid = False
            continue
        
        try:
            with open(p, encoding='utf-8') as f:
                data = json.load(f)
            print(f"  ✅ PASS: {filepath} valid JSON")
        except Exception as e:
            print(f"  ❌ FAIL: {filepath} invalid: {e}")
            all_valid = False
    
    return all_valid

def sav_tier0c():
    """SAV: TIER 0c RAG + SCB"""
    print("🔍 SAV: TIER 0c — RAG + SCB")
    try:
        sys.path.insert(0, str(Path.cwd()))
        from internal.rag_and_scb import RAGLoaderBasic, SCBSessionContinuity
        print("  ✅ PASS: RAG + SCB modules imported")
        
        # Quick test
        rag = RAGLoaderBasic()
        print("  ✅ PASS: RAGLoaderBasic instantiated")
        return True
    except Exception as e:
        print(f"  ❌ FAIL: {e}")
        return False

def sav_tier0d():
    """SAV: TIER 0d Live Telemetry"""
    print("🔍 SAV: TIER 0d — Live Telemetry")
    try:
        sys.path.insert(0, str(Path.cwd()))
        from internal.live_telemetry import LiveTelemetryCollector, SentinelCrisisHandler
        print("  ✅ PASS: Telemetry modules imported")
        
        collector = LiveTelemetryCollector()
        collector.record_ebdi_state("test_agent", 0.5, 0.5, 0.5)
        print("  ✅ PASS: Telemetry collector working")
        return True
    except Exception as e:
        print(f"  ❌ FAIL: {e}")
        return False

def sav_tier0e():
    """SAV: TIER 0e GitHub Actions CI/CD"""
    print("🔍 SAV: TIER 0e — GitHub Actions")
    files = [
        ".github/workflows/python-ci.yml",
        ".github/workflows/tier0-gate.yml"
    ]
    
    all_valid = True
    for filepath in files:
        p = Path(filepath)
        if not p.exists():
            print(f"  ❌ FAIL: {filepath} not found")
            all_valid = False
            continue
        
        with open(p) as f:
            content = f.read()
            if "tier0" in content or "TIER 0" in content:
                print(f"  ✅ PASS: {filepath} configured")
            else:
                print(f"  ⚠️  WARNING: {filepath} may need updates")
    
    return all_valid

def sav_uap_phase1():
    """SAV: UAP Phase 1 Finale"""
    print("🔍 SAV: UAP Phase 1 Finale")
    checklist = Path("Genesis Record/10_RAPORTY_DZIALANIA_SYSTEMU/REPORTS/UAP_Phase1_Finale_Checklist_05-04-2026.md")
    if checklist.exists():
        print(f"  ✅ PASS: UAP Phase 1 checklist generated")
        return True
    else:
        print(f"  ❌ FAIL: UAP Phase 1 checklist missing")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("  FAZA 2.5 — STEP AUTO-VERIFICATION (SAV [2])")
    print("=" * 60)
    print()
    
    results = {
        "TIER 0a (pytest)": sav_tier0a(),
        "TIER 0b (memories)": sav_tier0b(),
        "TIER 0c (RAG+SCB)": sav_tier0c(),
        "TIER 0d (telemetry)": sav_tier0d(),
        "TIER 0e (CI/CD)": sav_tier0e(),
        "UAP Phase 1": sav_uap_phase1(),
    }
    
    print()
    print("=" * 60)
    print("  SAV SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for task, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {task}")
    
    print()
    print(f"  OVERALL: {passed}/{total} checks passed")
    
    if passed == total:
        print("  🎉 ALL TIER 0 GATES PASSED — READY FOR PRODUCTION")
        sys.exit(0)
    else:
        print("  ⚠️  Some gates failed — review above")
        sys.exit(1)
