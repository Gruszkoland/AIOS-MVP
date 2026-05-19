"""
Tests for micro-saas billing module.

Covers: TIERS structure, init_saas_db, get/create subscription, quota logic,
        daily counter reset, unlimited elite tier.

Run: pytest tests/test_saas_billing.py -v
"""
import sys
from pathlib import Path

# Resolve micro-saas path (folder name has hyphen, not importable as package)
_SAAS_DIR = Path(__file__).parent.parent / "micro-saas"
if str(_SAAS_DIR) not in sys.path:
    sys.path.insert(0, str(_SAAS_DIR))

import pytest
from billing import (
    TIERS,
    Subscription,
    check_bid_quota,
    consume_bid,
    create_subscription,
    get_subscription,
    init_saas_db,
    _DB_PATH,
    _get_conn,
)


# ── Fixtures ──────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    """Redirect SAAS_DB_PATH to a temp file and re-init schema before each test."""
    db_file = tmp_path / "test_subscriptions.db"
    monkeypatch.setenv("SAAS_DB_PATH", str(db_file))

    # Patch module-level _DB_PATH so _get_conn() uses the temp file
    import billing as billing_mod
    monkeypatch.setattr(billing_mod, "_DB_PATH", db_file)

    init_saas_db()
    yield db_file


# ── TIERS sanity ──────────────────────────────────────────────────────────

class TestTiersStructure:
    def test_all_tiers_present(self):
        assert set(TIERS) == {"free", "pro", "elite"}

    def test_free_tier_values(self):
        t = TIERS["free"]
        assert t["bids_per_day"] == 5
        assert t["price_eur_monthly"] == 0.0
        assert t["rag_enabled"] is False
        assert t["oracle_enabled"] is False

    def test_pro_tier_values(self):
        t = TIERS["pro"]
        assert t["bids_per_day"] == 100
        assert t["rag_enabled"] is True
        assert t["oracle_enabled"] is True

    def test_elite_tier_unlimited(self):
        t = TIERS["elite"]
        assert t["bids_per_day"] == -1
        assert t["mcp_access"] is True
        assert t["priority_llm"] is True

    def test_all_tiers_have_required_keys(self):
        required = {"bids_per_day", "rag_enabled", "oracle_enabled", "mcp_access",
                    "price_eur_monthly", "description"}
        for name, cfg in TIERS.items():
            assert required.issubset(cfg.keys()), f"Tier '{name}' missing keys"


# ── Subscription CRUD ─────────────────────────────────────────────────────

class TestSubscriptionCRUD:
    def test_get_subscription_none_for_unknown_user(self):
        assert get_subscription("ghost_user") is None

    def test_create_free_subscription(self):
        sub = create_subscription("user_a", "free")
        assert isinstance(sub, Subscription)
        assert sub.user_id == "user_a"
        assert sub.tier == "free"
        assert sub.status == "active"
        assert sub.sub_id  # non-empty UUID

    def test_create_and_retrieve_subscription(self):
        create_subscription("user_b", "pro")
        sub = get_subscription("user_b")
        assert sub is not None
        assert sub.tier == "pro"
        assert sub.status == "active"

    def test_upgrade_cancels_old_sub(self):
        create_subscription("user_c", "free")
        create_subscription("user_c", "pro")

        # Only one active subscription should exist
        with _get_conn() as conn:
            rows = conn.execute(
                "SELECT status FROM subscriptions WHERE user_id='user_c'"
            ).fetchall()

        statuses = [r["status"] for r in rows]
        assert statuses.count("active") == 1
        assert "cancelled" in statuses

    def test_create_invalid_tier_raises(self):
        with pytest.raises(ValueError, match="Unknown tier"):
            create_subscription("user_d", "diamond")

    def test_subscription_created_at_is_iso_string(self):
        sub = create_subscription("user_e", "elite")
        # Must parse as ISO datetime without raising
        from datetime import datetime
        datetime.fromisoformat(sub.created_at)


# ── Quota logic ───────────────────────────────────────────────────────────

class TestBidQuota:
    def test_no_subscription_denied(self):
        allowed, reason = check_bid_quota("no_sub_user")
        assert allowed is False
        assert "No active subscription" in reason

    def test_free_tier_allows_first_bid(self):
        create_subscription("q_user", "free")
        allowed, reason = check_bid_quota("q_user")
        assert allowed is True
        assert "remaining" in reason

    def test_free_tier_exhausted_after_limit(self):
        create_subscription("q_exhausted", "free")
        limit = TIERS["free"]["bids_per_day"]

        # Consume all bids
        for _ in range(limit):
            consume_bid("q_exhausted")

        allowed, reason = check_bid_quota("q_exhausted")
        assert allowed is False
        assert "Daily limit reached" in reason

    def test_elite_always_allowed(self):
        create_subscription("q_elite", "elite")
        for _ in range(50):
            consume_bid("q_elite")

        allowed, reason = check_bid_quota("q_elite")
        assert allowed is True
        assert reason == "unlimited"

    def test_daily_counter_resets_on_new_day(self, monkeypatch):
        import billing as billing_mod
        from datetime import datetime, timezone

        create_subscription("q_reset", "free")
        limit = TIERS["free"]["bids_per_day"]

        # Exhaust today's quota by direct DB write (simulate yesterday)
        sub = get_subscription("q_reset")
        with _get_conn() as conn:
            conn.execute(
                "UPDATE subscriptions SET bids_used_today=?, last_bid_date=? WHERE sub_id=?",
                (limit, "2000-01-01", sub.sub_id),
            )
            conn.commit()

        # Verify still blocked on old date
        allowed, _ = check_bid_quota("q_reset")
        # After reset (new day > 2000-01-01), counter resets → allowed
        assert allowed is True  # today != 2000-01-01 → reset triggered

    def test_consume_bid_increments_counter(self):
        create_subscription("q_incr", "pro")
        sub_before = get_subscription("q_incr")
        consume_bid("q_incr")

        with _get_conn() as conn:
            row = conn.execute(
                "SELECT bids_used_today FROM subscriptions WHERE user_id='q_incr' AND status='active'"
            ).fetchone()
        assert row["bids_used_today"] == 1
