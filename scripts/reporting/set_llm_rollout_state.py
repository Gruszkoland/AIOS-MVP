from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from arbitrage import llm


def print_settings() -> None:
    settings = llm.get_effective_canary_settings()
    print("LLM Rollout Settings")
    print(f" - source: {settings.get('source')}")
    print(f" - canary_enabled: {settings.get('canary_enabled')}")
    print(f" - canary_percent: {settings.get('canary_percent')}")
    print(f" - canary_backend: {settings.get('canary_backend')}")
    print(f" - state_path: {llm.LLM_ROLLOUT_STATE_PATH}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Manage local LLM canary rollout state."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("show", help="Show current effective rollout settings.")

    promote = subparsers.add_parser("promote", help="Enable canary at a given percentage.")
    promote.add_argument("--percent", type=float, default=5.0)
    promote.add_argument("--backend", default="openrouter")
    promote.add_argument("--reason", default="manual_promote")

    disable = subparsers.add_parser("disable", help="Disable canary traffic.")
    disable.add_argument("--reason", default="manual_disable")

    reset = subparsers.add_parser("reset", help="Remove rollout state override and return to ENV defaults.")

    args = parser.parse_args()

    if args.command == "show":
        print_settings()
        return 0

    if args.command == "promote":
        state = llm.set_canary_rollout(
            percent=args.percent,
            backend=args.backend,
            reason=args.reason,
        )
        print("OK: rollout updated")
        print(f" - canary_enabled: {state.get('canary_enabled')}")
        print(f" - canary_percent: {state.get('canary_percent')}")
        print(f" - canary_backend: {state.get('canary_backend')}")
        print(f" - reason: {state.get('reason')}")
        print(f" - state_path: {llm.LLM_ROLLOUT_STATE_PATH}")
        return 0

    if args.command == "disable":
        state = llm.force_canary_rollback(reason=args.reason)
        print("OK: rollout disabled")
        print(f" - canary_enabled: {state.get('canary_enabled')}")
        print(f" - canary_percent: {state.get('canary_percent')}")
        print(f" - reason: {state.get('reason')}")
        print(f" - state_path: {llm.LLM_ROLLOUT_STATE_PATH}")
        return 0

    if args.command == "reset":
        state_path = Path(llm.LLM_ROLLOUT_STATE_PATH)
        if state_path.exists():
            state_path.unlink()
            print(f"OK: removed rollout state override at {state_path}")
        else:
            print(f"OK: no rollout state override found at {state_path}")
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
