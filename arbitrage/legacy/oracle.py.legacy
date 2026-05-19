"""
ADRION 369 — Predykcyjna Wyrocznia AI (Vortex Oracle)
Transpilacja z PROGRAMATOR #19/#20 na Python.

4 Warstwy:
  1. Mapowanie Enneagram (Heksada 1-4-2-8-5-7 vs Trójkąt 3-6-9)
  2. Logika Trójwartościowa Łukasiewicza (z quantum.py)
  3. Analiza Częstotliwościowa Solfeggio (wibracja trendu)
  4. Fibonacci Prediction ("Oko Spirali")

Wyrocznia nie pyta "ile zarobimy?", lecz "kiedy system osiągnie stan harmonii (9)?".
"""
import logging
import math
from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

from .analyzer import digital_root, calculate_market_resonance
from .quantum import quantum_decide, QuantumDecision

logger = logging.getLogger("adrion.oracle")

# ═══════════════════════════════════════════════════════════════
# STAŁE
# ═══════════════════════════════════════════════════════════════

# Fibonacci ratios for retracement / extension
FIBONACCI_RATIOS = [0.236, 0.382, 0.5, 0.618, 0.786, 1.0, 1.618, 2.618]

# "Eye of Spiral" — 38.2% / 61.8% focus zone
SPIRAL_EYE_LOW = 0.382
SPIRAL_EYE_HIGH = 0.618

# Enneagram hexad (material processes cycle)
HEXAD_SEQUENCE = [1, 4, 2, 8, 5, 7]

# Enneagram triangle (turning points)
TRIANGLE_NODES = [3, 6, 9]

# Solfeggio vibration thresholds
FREQ_396_HZ = 396   # Uwalnianie lęku — volatile products
FREQ_528_HZ = 528   # Regeneracja/Sukces — stable, high-margin
FREQ_174_HZ = 174   # Uśmierzanie napięcia — baseline scan

# Oracle signal types
SignalType = Literal["IMPULSE", "STABILIZATION", "SINGULARITY", "DORMANT"]


# ═══════════════════════════════════════════════════════════════
# TYPY
# ═══════════════════════════════════════════════════════════════

@dataclass
class OraclePrediction:
    """Wynik predykcji Wyroczni."""
    signal: SignalType           # IMPULSE(3) | STABILIZATION(6) | SINGULARITY(9) | DORMANT
    node: int                    # Węzeł Enneagramu (1-9)
    confidence: float            # 0.0 - 1.0
    predicted_margin_pct: float  # Przewidywana marża %
    fibonacci_level: float       # Poziom Fibonacciego (0.236 - 2.618)
    solfeggio_hz: int            # Przypisana częstotliwość trendu
    vibration_label: str         # "volatile" | "stable" | "dormant"
    action: str                  # "BUY" | "HOLD" | "WAIT" | "SELL"
    digital_root_price: int      # Redukcja cyfrowa ceny
    is_singularity: bool         # Czy Punkt 9 (Profit Singularity)?
    reasoning: str               # Wyjaśnienie decyzji
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            "signal": self.signal,
            "node": self.node,
            "confidence": round(self.confidence, 3),
            "predicted_margin_pct": round(self.predicted_margin_pct, 4),
            "fibonacci_level": self.fibonacci_level,
            "solfeggio_hz": self.solfeggio_hz,
            "vibration_label": self.vibration_label,
            "action": self.action,
            "digital_root_price": self.digital_root_price,
            "is_singularity": self.is_singularity,
            "reasoning": self.reasoning,
            "timestamp": self.timestamp,
        }


# ═══════════════════════════════════════════════════════════════
# 1. MAPOWANIE ENNEAGRAMU (Heksada vs Trójkąt)
# ═══════════════════════════════════════════════════════════════

def classify_enneagram_node(value: float) -> tuple[int, str]:
    """
    Klasyfikuj wartość na węzeł Enneagramu (1-9).
    Returns: (node, category)
      category: "hexad" (procesy materialne) | "triangle" (punkty zwrotne)
    """
    dr = digital_root(int(abs(value * 100)))
    if dr in TRIANGLE_NODES:
        return dr, "triangle"
    return dr, "hexad"


def detect_turning_point(prices: list[float]) -> tuple[SignalType, int]:
    """
    Wykryj punkt zwrotny w serii cenowej.

    Punkt 3 (Impuls): Nagły wzrost zapytań/cen (>10% zmiana).
    Punkt 6 (Stabilizacja): Cena osiąga najniższy punkt opłacalności.
    Punkt 9 (Osobliwość): Marża + popyt → najwyższy rezonans.
    """
    if len(prices) < 3:
        return "DORMANT", 0

    # Oblicz zmiany procentowe
    changes = []
    for i in range(1, len(prices)):
        if prices[i - 1] > 0:
            pct = (prices[i] - prices[i - 1]) / prices[i - 1]
            changes.append(pct)
        else:
            changes.append(0.0)

    if not changes:
        return "DORMANT", 0

    latest_change = changes[-1]
    avg_change = sum(changes) / len(changes)
    min_price = min(prices)
    current_price = prices[-1]

    # Punkt 3 — Impuls: nagły wzrost > 10%
    if latest_change > 0.10:
        return "IMPULSE", 3

    # Punkt 6 — Stabilizacja: cena blisko minimum
    if current_price <= min_price * 1.05 and abs(latest_change) < 0.03:
        return "STABILIZATION", 6

    # Punkt 9 — Osobliwość: redukcja cyfrowa średniej zmiany = 9
    magnitude = int(abs(avg_change * 10000))
    dr = digital_root(magnitude)
    if dr == 9:
        return "SINGULARITY", 9

    # Pozostałe — szukaj w heksadzie
    dr_price = digital_root(int(current_price))
    if dr_price in HEXAD_SEQUENCE:
        return "DORMANT", dr_price

    return "DORMANT", dr_price


# ═══════════════════════════════════════════════════════════════
# 2. FIBONACCI PREDICTION ("Oko Spirali")
# ═══════════════════════════════════════════════════════════════

def fibonacci_levels(high: float, low: float) -> dict[float, float]:
    """
    Oblicz poziomy Fibonacci retracement/extension.
    Returns: {ratio: price_level}
    """
    diff = high - low
    levels = {}
    for ratio in FIBONACCI_RATIOS:
        levels[ratio] = round(low + diff * ratio, 2)
    return levels


def find_spiral_eye(prices: list[float]) -> dict:
    """
    Znajdź "Oko Spirali" — punkt 38.2%/61.8% w danych cenowych.

    Wyrocznia oblicza, czy ścieżka ceny przetnie się z ofertą
    dokładnie w momencie najatrakcyjniejszej ceny.
    """
    if len(prices) < 2:
        return {"found": False, "reason": "insufficient_data"}

    high = max(prices)
    low = min(prices)
    if high == low:
        return {"found": False, "reason": "no_price_movement"}

    levels = fibonacci_levels(high, low)
    current = prices[-1]

    # Sprawdź czy cena jest w "Oku Spirali" (strefa 38.2% - 61.8%)
    eye_low_price = levels[SPIRAL_EYE_LOW]
    eye_high_price = levels[SPIRAL_EYE_HIGH]

    in_eye = eye_low_price <= current <= eye_high_price

    # Określ najbliższy poziom Fibonacciego
    closest_ratio = min(FIBONACCI_RATIOS, key=lambda r: abs(levels[r] - current))
    distance_pct = abs(levels[closest_ratio] - current) / high if high > 0 else 0

    return {
        "found": in_eye,
        "current_price": current,
        "eye_zone": [eye_low_price, eye_high_price],
        "closest_fib_ratio": closest_ratio,
        "closest_fib_price": levels[closest_ratio],
        "distance_to_fib_pct": round(distance_pct, 4),
        "all_levels": levels,
        "high": high,
        "low": low,
    }


# ═══════════════════════════════════════════════════════════════
# 3. ANALIZA CZĘSTOTLIWOŚCIOWA SOLFEGGIO
# ═══════════════════════════════════════════════════════════════

def assign_solfeggio(signal: SignalType, margin_pct: float) -> tuple[int, str]:
    """
    Przypisz częstotliwość Solfeggio trendowi.

    396 Hz (Uwalnianie lęku) — impuls rynkowy (volatile)
    528 Hz (Regeneracja/Sukces) — stabilne lub osobliwość (high-margin/singular)
    174 Hz (Baseline) — brak wyraźnego sygnału
    """
    if signal == "IMPULSE":
        return FREQ_396_HZ, "volatile"
    if signal in ("SINGULARITY", "STABILIZATION") or margin_pct >= 0.15:
        return FREQ_528_HZ, "stable"
    return FREQ_174_HZ, "dormant"


def calculate_volatility(prices: list[float]) -> float:
    """Standardized volatility: stdev / mean."""
    if len(prices) < 2:
        return 0.0
    mean = sum(prices) / len(prices)
    if mean <= 0:
        return 0.0
    variance = sum((p - mean) ** 2 for p in prices) / len(prices)
    return math.sqrt(variance) / mean


# ═══════════════════════════════════════════════════════════════
# 4. GŁÓWNA FUNKCJA WYROCZNI
# ═══════════════════════════════════════════════════════════════

def oracle_predict(
    wholesale_price: float,
    retail_price: float,
    price_history: list[float] | None = None,
    channel_id: str = "AUDIO_PREMIUM",
) -> OraclePrediction:
    """
    Predykcyjna Wyrocznia AI — główna funkcja.

    Łączy 4 warstwy:
      1. Enneagram (punkt zwrotny w historii cen)
      2. Quantum decide (Łukasiewicz 0/½/1)
      3. Solfeggio (wibracja trendu)
      4. Fibonacci (Oko Spirali)

    Sygnał "SINGULARITY" + Fibonacci Eye = Punkt 9 → BUY/EXECUTE.
    """
    history = price_history or []

    # ── Warstwa 1: Enneagram ──
    signal, node = detect_turning_point(history) if len(history) >= 3 else ("DORMANT", 0)

    # ── Warstwa 2: Quantum Decision ──
    qd: QuantumDecision = quantum_decide(wholesale_price, retail_price, channel_id)
    margin_pct = qd.margin_pct

    # ── Warstwa 3: Solfeggio ──
    solfeggio_hz, vibration_label = assign_solfeggio(signal, margin_pct)

    # ── Warstwa 4: Fibonacci ──
    spiral = find_spiral_eye(history) if len(history) >= 2 else {"found": False}
    fib_level = spiral.get("closest_fib_ratio", 0.0)
    in_eye = spiral.get("found", False)

    # ── Redukcja cyfrowa ceny (Digital Root) ──
    dr_price = digital_root(int(abs(retail_price * 100)))

    # ── Logika decyzyjna Wyroczni ──
    is_singularity = False
    reasoning_parts = []

    # Punkt 9: Osobliwość
    if signal == "SINGULARITY":
        is_singularity = True
        reasoning_parts.append("PUNKT_9: Rezonans rynkowy osiąga Osobliwość.")

    # Fibonacci Eye aktywne
    if in_eye:
        reasoning_parts.append(
            f"OKO_SPIRALI: Cena w strefie Fibonacciego ({SPIRAL_EYE_LOW}-{SPIRAL_EYE_HIGH})."
        )
        # Eye + quantum affirmation = Singularity override
        if qd.state == 1:
            is_singularity = True

    # Digital Root = 9 wzmacnia sygnał
    if dr_price == 9:
        reasoning_parts.append("DIGITAL_ROOT_9: Matematyczna stabilność transakcji.")
        if qd.state >= 0.5:
            is_singularity = True

    # Kwantowy verdict integracja
    if qd.state == 1:
        reasoning_parts.append(f"QUANTUM_AFFIRM: Marża {margin_pct:.1%} > próg, Vortex=PASS.")
    elif qd.state == 0.5:
        reasoning_parts.append(f"QUANTUM_SUPERPOSITION: Marża {margin_pct:.1%}, wymaga analizy.")
    else:
        reasoning_parts.append(f"QUANTUM_NEGATION: Marża {margin_pct:.1%} nie spełnia progów.")

    # Solfeggio kontekst
    reasoning_parts.append(f"SOLFEGGIO_{solfeggio_hz}Hz: Trend {vibration_label}.")

    # ── Finalna akcja ──
    if is_singularity and qd.state >= 0.5:
        action = "BUY"
        confidence = min(1.0, qd.confidence + 0.2)
        if signal != "SINGULARITY":
            signal = "SINGULARITY"
            node = 9
    elif qd.state == 1:
        action = "BUY"
        confidence = qd.confidence
    elif qd.state == 0.5:
        action = "HOLD"
        confidence = qd.confidence
    elif signal == "STABILIZATION":
        action = "WAIT"
        confidence = 0.5
    else:
        action = "WAIT"
        confidence = max(0.1, 1.0 - margin_pct)

    reasoning = " | ".join(reasoning_parts)

    prediction = OraclePrediction(
        signal=signal,
        node=node,
        confidence=confidence,
        predicted_margin_pct=margin_pct,
        fibonacci_level=fib_level,
        solfeggio_hz=solfeggio_hz,
        vibration_label=vibration_label,
        action=action,
        digital_root_price=dr_price,
        is_singularity=is_singularity,
        reasoning=reasoning,
    )

    logger.info(
        "Oracle → %s [Node %d] margin=%.1f%% fib=%.3f sol=%dHz action=%s",
        prediction.signal, prediction.node, margin_pct * 100,
        fib_level, solfeggio_hz, action,
    )

    return prediction


# ═══════════════════════════════════════════════════════════════
# BATCH ORACLE — Skan wielu produktów
# ═══════════════════════════════════════════════════════════════

def oracle_scan_products(products: list[dict], channel_id: str = "AUDIO_PREMIUM") -> dict:
    """
    Skanuj listę produktów przez Wyrocznię.

    Każdy produkt: {wholesale_price, retail_price, price_history?: list[float], name?: str}

    Returns: {predictions: list, summary: dict}
    """
    predictions = []
    singularities = 0
    buys = 0
    holds = 0
    waits = 0

    for product in products:
        pred = oracle_predict(
            wholesale_price=product.get("wholesale_price", 0),
            retail_price=product.get("retail_price", 0),
            price_history=product.get("price_history"),
            channel_id=channel_id,
        )
        entry = pred.to_dict()
        entry["name"] = product.get("name", "unknown")
        predictions.append(entry)

        if pred.is_singularity:
            singularities += 1
        if pred.action == "BUY":
            buys += 1
        elif pred.action == "HOLD":
            holds += 1
        else:
            waits += 1

    # Sortuj: singularities first, then by confidence
    predictions.sort(key=lambda p: (p["is_singularity"], p["confidence"]), reverse=True)

    return {
        "predictions": predictions,
        "summary": {
            "total_scanned": len(products),
            "singularities": singularities,
            "buys": buys,
            "holds": holds,
            "waits": waits,
            "scan_timestamp": datetime.now().isoformat(),
        },
    }
