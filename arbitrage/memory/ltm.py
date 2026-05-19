"""
LTM (Long-Term Memory) & K0 Memory Restoration — ADRION 369 §IV

Implements K0 stage of operational loop (Memory Restoration).
Restores user preferences, session context, TSPA scores, and EBDI state.

Follows ADRION 369 §IV K0:
  1. Odczytaj memories/ltm.json
  2. Błąd/brak → Cold-Start: WARN:LTM_MISSING, pusty profil, kontynuuj
  3. Przywróć preferencje + last_session_summary

DSPy Signature (K0):
  In() → Out(ltm_profile:dict, success:bool, cold_start:bool, message:str)
"""

import json
import logging
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class TSPABaselines:
    """Trust Score & Performance Assessment baselines per agent."""
    SENTINEL: float = 0.95      # Etyka + bezpieczeństwo (nie może być wyłączony)
    ARCHITECT: float = 0.85     # Projektowanie + refaktoryzacja
    LIBRARIAN: float = 0.90     # Pamięć + dokumentacja + RAG


@dataclass
class EBDIState:
    """EBDI (Pleasure-Arousal-Dominance) state snapshot."""
    pleasure: float = 0.0       # [-1, +1] happiness/satisfaction
    arousal: float = 0.1        # [-1, +1] stress/energy level
    dominance: float = 0.0      # [-1, +1] control/assertiveness


@dataclass
class LTMProfile:
    """Long-Term Memory profile (user preferences + state)."""
    session_count: int = 0
    total_tokens_used: int = 0
    preferences: Dict[str, Any] = field(default_factory=dict)
    tspa_scores: Dict[str, float] = field(default_factory=dict)
    ebdi_state: EBDIState = field(default_factory=EBDIState)
    last_session: str = ""
    last_session_summary: str = ""
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict:
        d = asdict(self)
        d["ebdi_state"] = asdict(self.ebdi_state)
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "LTMProfile":
        """Deserialize from dict, with validation."""
        ebdi_data = data.pop("ebdi_state", {})
        profile = cls(**data)
        profile.ebdi_state = EBDIState(**ebdi_data)
        return profile


class LTMManager:
    """
    Long-Term Memory manager for user preferences and state persistence.
    
    DSPy Signature (K0):
        In() → Out(profile:LTMProfile, success:bool, cold_start:bool)
    """

    def __init__(self, storage_path: Path = Path("memories/ltm.json")):
        """Initialize LTM manager."""
        self.storage_path = storage_path
        self.profile = LTMProfile()
        self.cold_start = False

        # Try to restore
        self._load()

    def _load(self) -> None:
        """K0 Memory Restoration: Load LTM from disk or cold-start."""
        if not self.storage_path.exists():
            logger.warning("WARN:LTM_MISSING — Cold-start with empty profile")
            self.cold_start = True
            self._initialize_baselines()
            return

        try:
            with open(self.storage_path, "r") as f:
                data = json.load(f)
                self.profile = LTMProfile.from_dict(data)
                logger.info(
                    f"LTM restored: session_count={self.profile.session_count}, "
                    f"TSPA={self.profile.tspa_scores}"
                )
        except Exception as e:
            logger.warning(f"LTM load failed: {e} — cold-start")
            self.cold_start = True
            self._initialize_baselines()

    def _initialize_baselines(self) -> None:
        """Initialize TSPA baselines and default preferences."""
        baselines = TSPABaselines()
        self.profile.tspa_scores = {
            "SENTINEL": baselines.SENTINEL,
            "ARCHITECT": baselines.ARCHITECT,
            "LIBRARIAN": baselines.LIBRARIAN,
        }
        self.profile.preferences = {
            "language": "PL",
            "format": "SBAR",
            "verbosity": "normal",
            "enable_pme": True,
        }
        self.profile.ebdi_state = EBDIState()

    def _persist(self) -> None:
        """Persist LTM to storage."""
        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            self.profile.updated_at = datetime.utcnow().isoformat()
            with open(self.storage_path, "w") as f:
                json.dump(self.profile.to_dict(), f, indent=2)
            logger.info(f"LTM persisted: {self.storage_path}")
        except Exception as e:
            logger.error(f"Failed to persist LTM: {e}")

    def restore(self) -> Dict[str, Any]:
        """
        K0 Memory Restoration — Return full restored state.

        DSPy Signature:
            In() → Out(profile:dict, cold_start:bool, success:bool, message:str)
        """
        return {
            "profile": self.profile.to_dict(),
            "cold_start": self.cold_start,
            "success": True,
            "message": "LTM restored" if not self.cold_start else "Cold-start with empty profile",
        }

    def update_preferences(self, **kwargs) -> bool:
        """Update user preferences."""
        self.profile.preferences.update(kwargs)
        self._persist()
        return True

    def update_ebdi_state(self, pleasure: Optional[float] = None,
                         arousal: Optional[float] = None,
                         dominance: Optional[float] = None) -> EBDIState:
        """
        Update EBDI state (Pleasure-Arousal-Dominance).
        
        ADRION 369 §X: EBDI Thresholds
          - A ∈ [-0.3, 0.5]: NEUTRAL (normal)
          - A ∈ (0.5, 0.7]: ALERT (-30% output, default choices)
          - A > 0.7: STRESS (Empathic Shortcut, Sentinel routing)
        """
        if pleasure is not None:
            self.profile.ebdi_state.pleasure = max(-1, min(1, pleasure))
        if arousal is not None:
            self.profile.ebdi_state.arousal = max(-1, min(1, arousal))
        if dominance is not None:
            self.profile.ebdi_state.dominance = max(-1, min(1, dominance))

        self._persist()
        return self.profile.ebdi_state

    def update_tspa_score(self, agent: str, new_score: float) -> float:
        """
        Update TSPA (Trust Score & Performance Assessment) for agent.
        
        Follows ADRION 369 §IX.2: TSPA Feedback
          - Success: +0.05 (capped at baseline)
          - Failure: -0.20 (min 0.60)
        """
        agent = agent.upper()
        baseline = TSPABaselines.__dict__.get(agent, 0.80)
        current = self.profile.tspa_scores.get(agent, baseline)

        # Clamp score to reasonable range
        new_score = max(0.60, min(baseline, new_score))
        self.profile.tspa_scores[agent] = new_score

        self._persist()
        logger.info(f"TSPA updated: {agent}={current:.2f}→{new_score:.2f}")
        return new_score

    def record_session_end(self, summary: str) -> None:
        """Record session summary at end."""
        self.profile.session_count += 1
        self.profile.last_session = datetime.utcnow().isoformat()
        self.profile.last_session_summary = summary
        self._persist()
        logger.info(f"Session recorded: count={self.profile.session_count}")

    def load_profile(self, user_id: str) -> Optional[LTMProfile]:
        """
        Load LTM profile for specific user (for multi-user scenarios).
        
        For now, returns self.profile (single LTM instance).
        Future: Support multi-user LTM storage per user_id.
        """
        return self.profile if not self.cold_start else None

    def get_ebdi_action(self) -> Dict[str, Any]:
        """
        Determine action based on current EBDI state (ADRION §X).

        DSPy Signature:
            In(ebdi:EBDIState) → Out(action:str, label:str, recommendation:str)
        """
        a = self.profile.ebdi_state.arousal
        p = self.profile.ebdi_state.pleasure
        d = self.profile.ebdi_state.dominance

        # Determine state label
        if a > 0.7:
            if p < -0.5:
                label = "DISTRESS"
                recommendation = "Offer /sleep command; Empathic Shortcut; Sentinel routing"
            else:
                label = "STRESS"
                recommendation = "-30% detail; default choices; supportive tone"
        elif -0.3 <= a <= 0.5:
            label = "NEUTRAL"
            recommendation = "Continue normally"
        elif a > 0.5:
            label = "ALERT"
            recommendation = "-30% output; proactive defaults"
        else:
            label = "PASSIVE"
            recommendation = "Increase proactivity; don't wait for input"

        # Sentinel routing if stressed
        requires_sentinel = a > 0.7

        return {
            "state": label,
            "arousal": a,
            "pleasure": p,
            "dominance": d,
            "requires_sentinel": requires_sentinel,
            "recommendation": recommendation,
        }


# K0 Helper: Global LTM instance
_ltm_instance: Optional[LTMManager] = None


def get_ltm() -> LTMManager:
    """Get or create global LTM manager instance."""
    global _ltm_instance
    if _ltm_instance is None:
        _ltm_instance = LTMManager()
    return _ltm_instance


def k0_memory_restoration(user_id: Optional[str] = None, 
                          ltm_manager: Optional["LTMManager"] = None,
                          cvc: Optional[Any] = None) -> Dict[str, Any]:
    """
    ADRION 369 §IV K0 — Memory Restoration stage.

    Args:
        user_id: User identifier (optional, used for profile lookup)
        ltm_manager: LTMManager instance (optional, creates new if None)
        cvc: CVCManager instance (optional, for genesis logging)

    Returns complete LTM state for session initialization.

    DSPy Signature:
        In(user_id:str|None, ltm:LTMManager|None, cvc:CVCManager|None) 
        → Out(ltm:dict, cold_start:bool, ebdi:dict, tspa:dict, message:str)
    """
    if ltm_manager is None:
        ltm_manager = get_ltm()
    
    restored = ltm_manager.restore()
    ebdi_action = ltm_manager.get_ebdi_action()
    
    # Log K0 stage to Genesis Record if available
    if cvc:
        try:
            from arbitrage.gateway.harmonia import create_genesis_record
            payload = {
                "user_id": user_id or "default",
                "cvc_state": cvc.state,
                "cold_start": restored["cold_start"],
                "ebdi_state": ebdi_action["state"],
                "session_count": ltm_manager.profile.session_count,
            }
            gr = create_genesis_record(
                agent="LIBRARIAN",
                action_type="K0_RESTORE",
                payload=payload,
            )
            import json
            gr_path = __import__("pathlib").Path("memories/genesis_record.jsonl")
            gr_path.parent.mkdir(parents=True, exist_ok=True)
            with open(gr_path, "a") as f:
                f.write(gr.to_jsonl() + "\n")
        except Exception as e:
            logger.warning(f"Failed to log K0 to Genesis: {e}")

    return {
        "ltm": restored["profile"],
        "cold_start": restored["cold_start"],
        "message": restored["message"],
        "ebdi_current": ltm_manager.profile.ebdi_state.to_dict() if hasattr(ltm_manager.profile.ebdi_state, 'to_dict') else asdict(ltm_manager.profile.ebdi_state),
        "ebdi_action": ebdi_action,
        "tspa": ltm_manager.profile.tspa_scores,
        "session_count": ltm_manager.profile.session_count,
    }


if __name__ == "__main__":
    # Test K0 Memory Restoration
    print("=== K0 MEMORY RESTORATION TEST ===")
    
    result = k0_memory_restoration()
    print(f"Cold-start: {result['cold_start']}")
    print(f"Message: {result['message']}")
    print(f"Session count: {result['session_count']}")
    print(f"TSPA scores: {result['tspa']}")
    print(f"EBDI state: {result['ebdi_current']}")
    print(f"EBDI recommendation: {result['ebdi_action']['recommendation']}")
    
    # Test updates
    ltm = get_ltm()
    ltm.update_ebdi_state(arousal=0.6, pleasure=0.3)
    print(f"\nAfter arousal update: {ltm.get_ebdi_action()['state']}")
    
    print("\n✅ K0 Memory Restoration test successful")
