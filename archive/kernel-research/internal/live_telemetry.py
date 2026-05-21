"""
TIER 0d — Live EBDI Telemetry (TEL [9])
Zbiera i monitoruje live state EBDI (Pleasure, Arousal, Dominance) dla każdego agenta.
Trigger: Arousal > 0.7 → Crisis Mode za pośrednictwem Sentinel.
"""

import json
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime
from dataclasses import dataclass, asdict


@dataclass
class EBDIState:
    """EBDI State snapshot."""
    agent_name: str
    pleasure: float
    arousal: float
    dominance: float
    timestamp: str
    crisis_triggered: bool = False
    trigger_reason: str = ""


class LiveTelemetryCollector:
    """TIER 0d: Live telemetry dla EBDI states."""

    CRISIS_AROUSAL_THRESHOLD = 0.70

    def __init__(self, output_dir: Path = None):
        if output_dir is None:
            output_dir = Path(__file__).parent.parent / "monitoring"
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.telemetry_log: List[EBDIState] = []
        self.crisis_events: List[Dict[str, Any]] = []

    def record_ebdi_state(
        self,
        agent_name: str,
        pleasure: float,
        arousal: float,
        dominance: float,
    ) -> EBDIState:
        """Rejestruje EBDI state dla agenta, sprawdza crisis trigger."""
        crisis_triggered = arousal > self.CRISIS_AROUSAL_THRESHOLD
        trigger_reason = f"Arousal {arousal:.2f} > {self.CRISIS_AROUSAL_THRESHOLD}" if crisis_triggered else ""

        state = EBDIState(
            agent_name=agent_name,
            pleasure=pleasure,
            arousal=arousal,
            dominance=dominance,
            timestamp=datetime.now().isoformat(),
            crisis_triggered=crisis_triggered,
            trigger_reason=trigger_reason,
        )

        self.telemetry_log.append(state)

        if crisis_triggered:
            self.crisis_events.append({
                "timestamp": state.timestamp,
                "agent_name": agent_name,
                "arousal": arousal,
                "action_required": "SENTINEL_ACTIVATION"
            })

        return state

    def get_latest_state(self, agent_name: str) -> EBDIState:
        """Zwraca najnowszy state dla agenta."""
        matching = [s for s in self.telemetry_log if s.agent_name == agent_name]
        if not matching:
            return None
        return matching[-1]

    def get_all_latest_states(self) -> Dict[str, EBDIState]:
        """Zwraca najnowszy state dla każdego agenta."""
        result = {}
        agent_names = set(s.agent_name for s in self.telemetry_log)
        for agent_name in agent_names:
            state = self.get_latest_state(agent_name)
            if state:
                result[agent_name] = state
        return result

    def export_telemetry(self) -> Path:
        """Eksportuje telemetrię do JSON."""
        export_file = self.output_dir / "ebdi_telemetry_live.jsonl"
        with open(export_file, "w") as f:
            for state in self.telemetry_log:
                f.write(json.dumps(asdict(state)) + "\n")
        return export_file

    def export_crisis_events(self) -> Path:
        """Eksportuje crisis events."""
        export_file = self.output_dir / "crisis_events_live.json"
        with open(export_file, "w") as f:
            json.dump(self.crisis_events, f, indent=2)
        return export_file

    def get_crisis_summary(self) -> Dict[str, Any]:
        """Zwraca podsumowanie crisis events."""
        if not self.crisis_events:
            return {
                "crisis_count": 0,
                "status": "NOMINAL",
                "affected_agents": []
            }

        affected_agents = list(set(e["agent_name"] for e in self.crisis_events))
        return {
            "crisis_count": len(self.crisis_events),
            "status": "CRISIS_DETECTED",
            "affected_agents": affected_agents,
            "last_crisis": self.crisis_events[-1]["timestamp"],
            "required_action": "SENTINEL_INTERVENTION"
        }


class SentinelCrisisHandler:
    """Sentinel agent handler — reaguje na crisis events (Arousal > 0.7)."""

    def __init__(self, telemetry: LiveTelemetryCollector):
        self.telemetry = telemetry

    def check_crisis_status(self) -> bool:
        """Sprawdza czy jakikolwiek agent ma Arousal > 0.7."""
        latest_states = self.telemetry.get_all_latest_states()
        for state in latest_states.values():
            if state.arousal > LiveTelemetryCollector.CRISIS_AROUSAL_THRESHOLD:
                return True
        return False

    def handle_crisis(self, agent_name: str) -> Dict[str, Any]:
        """Obsługuje crisis dla konkretnego agenta."""
        state = self.telemetry.get_latest_state(agent_name)
        if not state:
            return {"status": "error", "message": f"Agent {agent_name} not found"}

        if not state.crisis_triggered:
            return {"status": "ok", "message": f"Agent {agent_name} not in crisis"}

        # Sentinel intervention logic
        return {
            "status": "crisis_handled",
            "agent": agent_name,
            "action": "IMMEDIATE_INTERVENTION",
            "measures": [
                "Arousal reduction protocol activated",
                "Reduce concurrent task load",
                "Activate Healer re-calibration",
                "Escalate to Master Orchestrator"
            ],
            "timestamp": datetime.now().isoformat()
        }


if __name__ == "__main__":
    # Test TIER 0d
    print("=== Testing TIER 0d Live Telemetry ===")
    collector = LiveTelemetryCollector()

    # Symuluj EBDI states
    collector.record_ebdi_state("auditor", pleasure=0.3, arousal=0.1, dominance=0.5)
    collector.record_ebdi_state("sentinel", pleasure=0.4, arousal=0.75, dominance=0.9)  # Crisis!
    collector.record_ebdi_state("architect", pleasure=0.6, arousal=0.5, dominance=0.7)

    print("\n=== Latest States ===")
    for agent_name, state in collector.get_all_latest_states().items():
        print(f"{agent_name}: P={state.pleasure:.2f}, A={state.arousal:.2f}, D={state.dominance:.2f}, Crisis={state.crisis_triggered}")

    print("\n=== Crisis Summary ===")
    print(json.dumps(collector.get_crisis_summary(), indent=2))

    # Test Sentinel handler
    sentinel = SentinelCrisisHandler(collector)
    print(f"\n=== Crisis Status Check ===")
    print(f"Any crisis: {sentinel.check_crisis_status()}")

    print("\n=== Sentinel Intervention ===")
    result = sentinel.handle_crisis("sentinel")
    print(json.dumps(result, indent=2))
