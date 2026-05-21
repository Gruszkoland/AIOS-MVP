"""
TIER 0b — Memories Persistence Loader
Ładuje trust_scores.json, ebdi_baseline.json, checkpoint.json
Używane przez Master Orchestrator do odtwarzania stanu między sesjami.
"""

import json
from pathlib import Path
from typing import Dict, Any


MEMORIES_ROOT = Path(__file__).parent / "memories"


class MemoriesPersistence:
    """TIER 0b: Zarządzanie perzystentnym stanem systemu między sesjami."""

    @staticmethod
    def load_trust_scores() -> Dict[str, Any]:
        """Ładuje Trust Scores (TSPA [1]) z memories/trust_scores.json"""
        fp = MEMORIES_ROOT / "trust_scores.json"
        if not fp.exists():
            raise FileNotFoundError(f"memories/trust_scores.json not found at {fp}")
        with open(fp) as f:
            data = json.load(f)
        return data

    @staticmethod
    def load_ebdi_baseline() -> Dict[str, Any]:
        """Ładuje EBDI Baseline (PHM [10]) z memories/ebdi_baseline.json"""
        fp = MEMORIES_ROOT / "ebdi_baseline.json"
        if not fp.exists():
            raise FileNotFoundError(f"memories/ebdi_baseline.json not found at {fp}")
        with open(fp) as f:
            data = json.load(f)
        return data

    @staticmethod
    def load_checkpoint() -> Dict[str, Any]:
        """Ładuje ostatni Checkpoint (RBC [3]) z memories/session/checkpoint.json"""
        fp = MEMORIES_ROOT / "session" / "checkpoint.json"
        if not fp.exists():
            raise FileNotFoundError(f"memories/session/checkpoint.json not found at {fp}")
        with open(fp) as f:
            data = json.load(f)
        return data

    @staticmethod
    def update_trust_score(agent_name: str, delta: float, reason: str):
        """Aktualizuje Trust Score dla agenta (TSPA update)."""
        data = MemoriesPersistence.load_trust_scores()
        if agent_name not in data["agents"]:
            raise ValueError(f"Unknown agent: {agent_name}")
        
        old_score = data["agents"][agent_name]["trust_score"]
        new_score = max(0.0, min(1.0, old_score + delta))
        data["agents"][agent_name]["trust_score"] = new_score
        data["agents"][agent_name]["history"].append({
            "date": "2026-04-05",  # TODO: use datetime.now()
            "action": "trust_update",
            "delta": f"{delta:+.2f}",
            "reason": reason,
            "old_score": old_score,
            "new_score": new_score
        })
        
        fp = MEMORIES_ROOT / "trust_scores.json"
        with open(fp, "w") as f:
            json.dump(data, f, indent=2)

    @staticmethod
    def update_ebdi_state(agent_name: str, state: Dict[str, float]):
        """Aktualizuje EBDI baseline dla agenta (PHM update)."""
        data = MemoriesPersistence.load_ebdi_baseline()
        if agent_name not in data["baseline_states"]:
            raise ValueError(f"Unknown agent: {agent_name}")
        
        data["baseline_states"][agent_name].update(state)
        
        fp = MEMORIES_ROOT / "ebdi_baseline.json"
        with open(fp, "w") as f:
            json.dump(data, f, indent=2)

    @staticmethod
    def add_checkpoint(checkpoint_id: str, git_hash: str, reason: str):
        """Dodaje nowy checkpoint do historii (RBC history)."""
        data = MemoriesPersistence.load_checkpoint()
        data["latest_checkpoint"] = {
            "id": checkpoint_id,
            "git_hash": git_hash,
            "datetime": "2026-04-05T00:00:00",  # TODO: use datetime.now()
            "type": "manual",
            "reason": reason,
        }
        data["checkpoint_history"].append(data["latest_checkpoint"])
        
        fp = MEMORIES_ROOT / "session" / "checkpoint.json"
        with open(fp, "w") as f:
            json.dump(data, f, indent=2)


if __name__ == "__main__":
    # Test load
    print("=== Trust Scores ===")
    ts = MemoriesPersistence.load_trust_scores()
    print(f"Loaded {len(ts['agents'])} agents")
    
    print("\n=== EBDI Baseline ===")
    eb = MemoriesPersistence.load_ebdi_baseline()
    print(f"Loaded {len(eb['baseline_states'])} baseline states")
    
    print("\n=== Checkpoint ===")
    cp = MemoriesPersistence.load_checkpoint()
    print(f"Latest checkpoint: {cp['latest_checkpoint']['id']}")
