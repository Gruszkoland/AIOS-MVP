"""
ADRION 369 — Kwantowy Moduł Decyzyjny (Vortex-Logic Engine)
Transpilacja z Go/Axum (PROGRAMATOR #9) na Python.

Logika Trójwartościowa Łukasiewicza:
  Stan 0   = Negacja (brak marży)
  Stan 0.5 = Superpozycja (anomalia trendu, wymaga analizy toroidalnej)
  Stan 1   = Afirmacja (czysty zysk > próg)

Mechanizmy:
  - quantum_decide():       główna funkcja decyzyjna 3-stanowa
  - entangle_markets():     splątanie rynków DE↔PL
  - scan_channel():         skan jednego kanału z filtrem Vortex
  - run_quantum_scan():     pełny skan wszystkich kanałów
  - autopojeza_reset():     auto-reset po 3 błędnych predykcjach (528Hz)
"""
import logging
import time
import requests
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

from .analyzer import digital_root, vortex_filter, calculate_market_resonance
from .config import QUANTUM_SCAN_CHANNELS

logger = logging.getLogger("adrion.quantum")

# ═══════════════════════════════════════════════════════════════
# TYPY I STAŁE
# ═══════════════════════════════════════════════════════════════

QuantumState = Literal[0, 0.5, 1]

# Progi decyzyjne
MARGIN_THRESHOLD_AFFIRM = 0.15      # >= 15% → Stan 1 (Afirmacja)
MARGIN_THRESHOLD_SUPERPOSITION = 0.08  # >= 8% < 15% → Stan ½ (Superpozycja)
AUTOPOJEZA_ERROR_LIMIT = 3           # Po 3 błędach → reset 528Hz
SCAN_INTERVAL_NORMAL_MS = 396        # Normalny interwał skanowania (ms)
SCAN_INTERVAL_HEALING_MS = 528       # Interwał po autopojezie (ms)


@dataclass
class QuantumDecision:
    """Wynik decyzji kwantowej."""
    state: float                     # 0 | 0.5 | 1
    state_label: str                 # "negation" | "superposition" | "affirmation"
    margin_pct: float
    resonance: int
    is_369: bool
    vortex_pass: bool
    channel_id: str
    action: str                      # "REJECT" | "ANALYZE" | "EXECUTE"
    confidence: float                # 0.0 - 1.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            "state": self.state,
            "state_label": self.state_label,
            "margin_pct": round(self.margin_pct, 4),
            "resonance": self.resonance,
            "is_369": self.is_369,
            "vortex_pass": self.vortex_pass,
            "channel_id": self.channel_id,
            "action": self.action,
            "confidence": round(self.confidence, 3),
            "timestamp": self.timestamp,
        }


# ═══════════════════════════════════════════════════════════════
# LOGIKA TRÓJWARTOŚCIOWA ŁUKASIEWICZA
# ═══════════════════════════════════════════════════════════════

def quantum_decide(
    price_source: float,
    price_target: float,
    channel_id: str = "AUDIO_PREMIUM",
) -> QuantumDecision:
    """
    Główna funkcja decyzyjna — Logika Trójwartościowa.
    Próbuje odpytać zewnętrzny Sentinel (Go) na porcie 1740.
    Jeśli Sentinel nie odpowiada, używa logiki lokalnej (Python fallback).
    """
    vortex_url = os.getenv("VORTEX_API_URL", "http://localhost:1740/decide")
    
    try:
        # 174ms timeout dla 174Hz synchronizacji
        resp = requests.post(
            vortex_url,
            json={
                "price_a": price_source,
                "price_b": price_target,
                "asset_a": "WHOLESALE",
                "asset_b": "RETAIL"
            },
            timeout=0.174
        )
        if resp.status_code == 200:
            data = resp.json()
            return QuantumDecision(
                state=data.get("state", 0),
                state_label=data.get("state_label", "negation"),
                margin_pct=data.get("margin_pct", 0.0),
                resonance=data.get("resonance", 0),
                is_369=data.get("is_singularity", False),
                vortex_pass=data.get("vortex_pass", False),
                channel_id=channel_id,
                action=data.get("action", "REJECT"),
                confidence=data.get("confidence", 0.0)
            )
    except Exception as e:
        logger.debug(f"Sentinel (Go) unavailable, using Python fallback: {e}")

    # ── FALLBACK LOKALNY (Python) ──
    if price_source <= 0 or price_target <= 0 or price_target <= price_source:
        return QuantumDecision(
            state=0, state_label="negation",
            margin_pct=0, resonance=0, is_369=False, vortex_pass=False,
            channel_id=channel_id, action="REJECT", confidence=1.0,
        )

    resonance_data = calculate_market_resonance(price_source, price_target)
    margin_pct = resonance_data["margin_pct"]
    resonance = resonance_data["resonance"]
    is_369 = resonance_data["is_369"]
    v_pass = resonance_data["vortex_pass"]

    # Sprawdź minimalną marżę dla kanału
    channel_min = _get_channel_min_margin(channel_id)

    # ── Stan 1: Afirmacja ──
    if margin_pct >= MARGIN_THRESHOLD_AFFIRM and margin_pct >= channel_min:
        confidence = min(1.0, margin_pct / 0.30)  # 30% = pełna pewność
        return QuantumDecision(
            state=1, state_label="affirmation",
            margin_pct=margin_pct, resonance=resonance, is_369=is_369,
            vortex_pass=v_pass, channel_id=channel_id,
            action="EXECUTE", confidence=confidence,
        )

    # ── Stan ½: Superpozycja ──
    if margin_pct >= MARGIN_THRESHOLD_SUPERPOSITION:
        # Analiza toroidalna 3-6-9 rozstrzyga superpozycję
        if is_369:
            # Rezonans 3-6-9 → kolaps do Afirmacji
            confidence = 0.5 + (margin_pct / 0.30) * 0.3
            return QuantumDecision(
                state=1, state_label="affirmation",
                margin_pct=margin_pct, resonance=resonance, is_369=True,
                vortex_pass=v_pass, channel_id=channel_id,
                action="EXECUTE", confidence=min(1.0, confidence),
            )
        else:
            # Brak rezonansu → pozostaje w superpozycji, wymaga dalszej analizy
            return QuantumDecision(
                state=0.5, state_label="superposition",
                margin_pct=margin_pct, resonance=resonance, is_369=False,
                vortex_pass=v_pass, channel_id=channel_id,
                action="ANALYZE", confidence=0.4,
            )

    # ── Stan 0: Negacja ──
    return QuantumDecision(
        state=0, state_label="negation",
        margin_pct=margin_pct, resonance=resonance, is_369=is_369,
        vortex_pass=v_pass, channel_id=channel_id,
        action="REJECT", confidence=min(1.0, 1.0 - margin_pct),
    )


# ═══════════════════════════════════════════════════════════════
# SPLĄTANIE RYNKOWE (Market Entanglement)
# ═══════════════════════════════════════════════════════════════

def entangle_markets(prices_de: list[float], prices_pl: list[float]) -> dict:
    """
    Analiza splątania między rynkami DACH↔PL.
    Zmiana w punkcie 3 (DE) natychmiast modyfikuje prawdopodobieństwo w punkcie 6 (PL).

    Returns dict z metrykami splątania.
    """
    if not prices_de or not prices_pl:
        return {"entanglement_score": 0, "pairs": 0, "opportunities": []}

    pairs = min(len(prices_de), len(prices_pl))
    opportunities = []
    resonance_sum = 0

    for i in range(pairs):
        decision = quantum_decide(prices_de[i], prices_pl[i])
        resonance_sum += decision.resonance
        if decision.state >= 0.5:
            opportunities.append(decision.to_dict())

    # Współczynnik splątania = średni rezonans normalizowany do 9
    avg_resonance = resonance_sum / pairs if pairs > 0 else 0
    entanglement_score = round(avg_resonance / 9.0, 4)

    return {
        "entanglement_score": entanglement_score,
        "avg_resonance": round(avg_resonance, 2),
        "pairs": pairs,
        "opportunities": opportunities,
        "affirmations": sum(1 for o in opportunities if o["state"] == 1),
        "superpositions": sum(1 for o in opportunities if o["state"] == 0.5),
    }


# ═══════════════════════════════════════════════════════════════
# SKANOWANIE KANAŁÓW (Channel Scanning)
# ═══════════════════════════════════════════════════════════════

def scan_channel(channel_id: str, deals: list[dict]) -> list[QuantumDecision]:
    """
    Skanuj listę okazji (deals) przez filtr kwantowy dla danego kanału.

    Każdy deal powinien mieć: wholesale_price, retail_price_de lub retail_price_pl
    """
    results = []
    for deal in deals:
        wp = deal.get("wholesale_price", 0)
        rp = deal.get("retail_price_de") or deal.get("retail_price_pl") or 0
        if wp <= 0 or rp <= 0:
            continue
        decision = quantum_decide(wp, rp, channel_id=channel_id)
        results.append(decision)
    return results


def run_quantum_scan(all_deals: dict[str, list[dict]]) -> dict:
    """
    Pełny skan wszystkich kanałów QUANTUM_SCAN_CHANNELS.

    Args:
        all_deals: dict mapping channel_id → list of deal dicts

    Returns:
        dict z wynikami per kanał + podsumowanie globalne
    """
    results = {}
    total_execute = 0
    total_analyze = 0
    total_reject = 0

    for channel in QUANTUM_SCAN_CHANNELS:
        cid = channel["id"]
        deals = all_deals.get(cid, [])
        decisions = scan_channel(cid, deals)

        execute = [d for d in decisions if d.action == "EXECUTE"]
        analyze = [d for d in decisions if d.action == "ANALYZE"]
        reject = [d for d in decisions if d.action == "REJECT"]

        results[cid] = {
            "frequency": channel["frequency"],
            "min_margin": channel["min_margin"],
            "scanned": len(decisions),
            "execute": len(execute),
            "analyze": len(analyze),
            "reject": len(reject),
            "top_opportunities": [d.to_dict() for d in sorted(
                execute + analyze,
                key=lambda x: x.margin_pct,
                reverse=True,
            )[:5]],
        }

        total_execute += len(execute)
        total_analyze += len(analyze)
        total_reject += len(reject)

    return {
        "channels": results,
        "summary": {
            "total_scanned": total_execute + total_analyze + total_reject,
            "total_execute": total_execute,
            "total_analyze": total_analyze,
            "total_reject": total_reject,
            "scan_timestamp": datetime.now().isoformat(),
        },
    }


# ═══════════════════════════════════════════════════════════════
# AUTOPOJEZA — Samonaprawa (528 Hz Reset)
# ═══════════════════════════════════════════════════════════════

class AutopoiezaTracker:
    """
    Śledzi błędne predykcje. Po AUTOPOJEZA_ERROR_LIMIT błędach
    resetuje parametry skanowania na tryb 528Hz (Regeneracja).
    """

    def __init__(self):
        self.consecutive_errors = 0
        self.total_resets = 0
        self.healing_mode = False
        self.last_reset: str | None = None

    def record_outcome(self, predicted_action: str, actual_profit: float) -> dict:
        """Rejestruj wynik decyzji i sprawdź czy potrzebna autopojeza."""
        was_correct = (
            (predicted_action == "EXECUTE" and actual_profit > 0)
            or (predicted_action == "REJECT" and actual_profit <= 0)
        )

        if was_correct:
            self.consecutive_errors = 0
            self.healing_mode = False
            return {"status": "ok", "healing_mode": False}

        self.consecutive_errors += 1
        logger.warning(
            "Quantum prediction error #%d (predicted=%s, profit=%.2f)",
            self.consecutive_errors, predicted_action, actual_profit,
        )

        if self.consecutive_errors >= AUTOPOJEZA_ERROR_LIMIT:
            return self._trigger_reset()

        return {
            "status": "warning",
            "consecutive_errors": self.consecutive_errors,
            "healing_mode": self.healing_mode,
        }

    def _trigger_reset(self) -> dict:
        """Resetuj częstotliwość skanowania na 528ms (Solfeggio Regeneracja)."""
        self.consecutive_errors = 0
        self.total_resets += 1
        self.healing_mode = True
        self.last_reset = datetime.now().isoformat()
        logger.info(
            "AUTOPOJEZA 528Hz RESET #%d — przejście w tryb regeneracji",
            self.total_resets,
        )
        return {
            "status": "autopojeza_reset",
            "healing_mode": True,
            "total_resets": self.total_resets,
            "scan_interval_ms": SCAN_INTERVAL_HEALING_MS,
            "frequency_hz": 528,
            "timestamp": self.last_reset,
        }

    def get_scan_interval(self) -> int:
        """Pobierz aktualny interwał skanowania (ms)."""
        return SCAN_INTERVAL_HEALING_MS if self.healing_mode else SCAN_INTERVAL_NORMAL_MS

    def get_status(self) -> dict:
        return {
            "consecutive_errors": self.consecutive_errors,
            "total_resets": self.total_resets,
            "healing_mode": self.healing_mode,
            "scan_interval_ms": self.get_scan_interval(),
            "last_reset": self.last_reset,
        }


# Globalny tracker autopojezy
_autopojeza = AutopoiezaTracker()


def get_autopojeza_status() -> dict:
    return _autopojeza.get_status()


def record_decision_outcome(predicted_action: str, actual_profit: float) -> dict:
    return _autopojeza.record_outcome(predicted_action, actual_profit)


# ═══════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════

def _get_channel_min_margin(channel_id: str) -> float:
    """Pobierz minimalną marżę dla kanału (jako ułamek, np. 0.15)."""
    for ch in QUANTUM_SCAN_CHANNELS:
        if ch["id"] == channel_id:
            return ch["min_margin"] / 100.0
    return MARGIN_THRESHOLD_AFFIRM
