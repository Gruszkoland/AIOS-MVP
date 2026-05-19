#!/usr/bin/env python3
"""
approve_healing.py — Human approval gate for HEALER proposals.

Usage:
  python scripts/approve_healing.py            # interactive review of all pending
  python scripts/approve_healing.py --list     # list pending proposals
  python scripts/approve_healing.py --approve h001
  python scripts/approve_healing.py --reject  h001 --reason "Not safe yet"

HEALER proposals live in healing_proposals/*.json.
This script NEVER executes any change — it only updates proposal status.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PROPOSALS_DIR = Path(__file__).parent.parent / "healing_proposals"
DATE_FMT = "%Y-%m-%dT%H:%M:%SZ"


def _load(path: Path) -> dict:
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def _save(path: Path, data: dict) -> None:
    with path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
    print(f"  Saved: {path.name}")


def _pending() -> list[tuple[Path, dict]]:
    results = []
    for p in sorted(PROPOSALS_DIR.glob("*.json")):
        try:
            data = _load(p)
        except json.JSONDecodeError as exc:
            print(f"[WARN] Skipping malformed JSON: {p.name} ({exc})")
            continue
        if data.get("status") == "pending":
            results.append((p, data))
    return results


def cmd_list() -> None:
    pending = _pending()
    if not pending:
        print("No pending healing proposals.")
        return
    print(f"\n{'ID':<12} {'SEV':<8} {'COMPONENT':<16} {'SYMPTOM'}")
    print("-" * 70)
    for _, d in pending:
        print(
            f"{d.get('proposal_id','?'):<12} "
            f"{d.get('severity','?'):<8} "
            f"{d.get('component','?'):<16} "
            f"{d.get('symptom','?')[:60]}"
        )
    print()


def _find_proposal(proposal_id: str) -> tuple[Path, dict] | None:
    for p in PROPOSALS_DIR.glob("*.json"):
        try:
            data = _load(p)
        except json.JSONDecodeError:
            continue
        if data.get("proposal_id") == proposal_id:
            return p, data
    return None


def cmd_approve(proposal_id: str, approver: str = "operator") -> None:
    result = _find_proposal(proposal_id)
    if result is None:
        print(f"[ERROR] Proposal '{proposal_id}' not found.", file=sys.stderr)
        sys.exit(1)
    path, data = result
    if data.get("status") != "pending":
        print(f"[ERROR] Proposal '{proposal_id}' is already {data.get('status')}.", file=sys.stderr)
        sys.exit(1)

    print(f"\n=== Proposal {proposal_id} ===")
    for key in ("component", "severity", "symptom", "root_cause", "action", "env_changes", "rollback"):
        print(f"  {key}: {data.get(key)}")
    print()

    confirm = input("Approve this proposal? [yes/no]: ").strip().lower()
    if confirm not in ("yes", "y"):
        print("Aborted — no changes made.")
        sys.exit(0)

    data["status"] = "approved"
    data["approved_by"] = approver
    data["approved_at"] = datetime.now(timezone.utc).strftime(DATE_FMT)
    _save(path, data)
    print(f"[OK] Proposal '{proposal_id}' approved. Apply the action manually:\n  {data.get('action')}")


def cmd_reject(proposal_id: str, reason: str) -> None:
    result = _find_proposal(proposal_id)
    if result is None:
        print(f"[ERROR] Proposal '{proposal_id}' not found.", file=sys.stderr)
        sys.exit(1)
    path, data = result
    if data.get("status") != "pending":
        print(f"[ERROR] Proposal '{proposal_id}' is already {data.get('status')}.", file=sys.stderr)
        sys.exit(1)

    data["status"] = "rejected"
    data["rejected_reason"] = reason
    data["approved_at"] = datetime.now(timezone.utc).strftime(DATE_FMT)
    _save(path, data)
    print(f"[OK] Proposal '{proposal_id}' rejected.")


def cmd_interactive() -> None:
    pending = _pending()
    if not pending:
        print("No pending healing proposals.")
        return

    for path, data in pending:
        pid = data.get("proposal_id", path.stem)
        print(f"\n{'=' * 60}")
        print(f"Proposal: {pid}  |  Severity: {data.get('severity')}  |  Component: {data.get('component')}")
        print(f"Symptom:  {data.get('symptom')}")
        print(f"Cause:    {data.get('root_cause')}")
        print(f"Action:   {data.get('action')}")
        if data.get("env_changes"):
            print(f"Env changes: {data.get('env_changes')}")
        print(f"Rollback: {data.get('rollback')}")

        choice = input("\n[a]pprove / [r]eject / [s]kip? ").strip().lower()
        if choice in ("a", "approve"):
            data["status"] = "approved"
            data["approved_by"] = "operator"
            data["approved_at"] = datetime.now(timezone.utc).strftime(DATE_FMT)
            _save(path, data)
            print(f"  → Approved. Apply: {data.get('action')}")
        elif choice in ("r", "reject"):
            reason = input("  Rejection reason: ").strip() or "No reason given"
            data["status"] = "rejected"
            data["rejected_reason"] = reason
            data["approved_at"] = datetime.now(timezone.utc).strftime(DATE_FMT)
            _save(path, data)
            print("  → Rejected.")
        else:
            print("  → Skipped.")


def main() -> None:
    parser = argparse.ArgumentParser(description="HEALER healing proposal approval gate")
    parser.add_argument("--list", action="store_true", help="List pending proposals")
    parser.add_argument("--approve", metavar="ID", help="Approve proposal by ID")
    parser.add_argument("--reject", metavar="ID", help="Reject proposal by ID")
    parser.add_argument("--reason", metavar="TEXT", default="No reason given", help="Rejection reason")
    parser.add_argument("--approver", metavar="NAME", default="operator", help="Approver name/login")
    args = parser.parse_args()

    if args.list:
        cmd_list()
    elif args.approve:
        cmd_approve(args.approve, approver=args.approver)
    elif args.reject:
        cmd_reject(args.reject, reason=args.reason)
    else:
        cmd_interactive()


if __name__ == "__main__":
    main()
