#!/usr/bin/env python3
"""Load and validate local secrets from .env without printing secret values."""

from pathlib import Path
import os
import sys

from dotenv import load_dotenv


REQUIRED_SECRETS = [
    "STRIPE_LOGIN_EMAIL",
    "STRIPE_LOGIN_PASSWORD",
    "STRIPE_BACKUP_CODE",
]


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    env_path = root / ".env"

    load_dotenv(env_path)

    missing = [name for name in REQUIRED_SECRETS if not os.getenv(name)]

    print(f"Loaded .env from: {env_path}")
    if missing:
        print("Missing required secrets:")
        for name in missing:
            print(f"- {name}")
        print("Set them in local .env or your password manager sync process.")
        return 1

    print("All required Stripe secret placeholders are set in local environment.")
    print("Values are intentionally not displayed for security reasons.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
