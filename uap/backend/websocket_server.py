"""
Unified Admin Panel (UAP) — WebSocket Server
Real-time telemetry push (<500ms latency)

Run: python websocket_server.py
Port: 8004
"""
import asyncio
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict

import websockets
from websockets.server import WebSocketServerProtocol

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

from db import get_db

WS_HOST = os.getenv("WS_HOST", "localhost")
WS_PORT = int(os.getenv("WS_PORT", "8004"))

# Store active WebSocket connections
clients: set[WebSocketServerProtocol] = set()

# In-memory EBDI state (replicated from API)
EBDI_STATE = {
    "Librarian": {"pleasure": 0.5, "arousal": 0.3, "dominance": 0.6},
    "SAP": {"pleasure": 0.6, "arousal": 0.4, "dominance": 0.7},
    "Auditor": {"pleasure": 0.55, "arousal": 0.35, "dominance": 0.65},
    "Sentinel": {"pleasure": 0.4, "arousal": 0.8, "dominance": 0.75},
    "Architect": {"pleasure": 0.65, "arousal": 0.3, "dominance": 0.6},
    "Healer": {"pleasure": 0.7, "arousal": 0.25, "dominance": 0.55},
    "Amplifier": {"pleasure": 0.6, "arousal": 0.5, "dominance": 0.65},
    "BoosterLever": {"pleasure": 0.55, "arousal": 0.45, "dominance": 0.6},
    "Chronos": {"pleasure": 0.5, "arousal": 0.3, "dominance": 0.62},
}

TRUST_SCORES = {
    "Librarian": 0.85, "SAP": 0.90, "Auditor": 0.88,
    "Sentinel": 0.92, "Architect": 0.87, "Healer": 0.83,
    "Amplifier": 0.80, "BoosterLever": 0.78, "Chronos": 0.82,
}


class TelemetryServer:
    """WebSocket server for real-time UAP telemetry."""

    def __init__(self):
        self.db = get_db()
        self.running = False

    async def register(self, websocket: WebSocketServerProtocol):
        """Register new WebSocket client."""
        clients.add(websocket)
        print(f"✅ Client connected: {websocket.remote_address}. Total: {len(clients)}")

    async def unregister(self, websocket: WebSocketServerProtocol):
        """Unregister WebSocket client."""
        clients.discard(websocket)
        print(f"❌ Client disconnected: {websocket.remote_address}. Total: {len(clients)}")

    async def handle_client(self, websocket: WebSocketServerProtocol, path: str):
        """Handle incoming WebSocket connections."""
        await self.register(websocket)

        try:
            async for message in websocket:
                await self.process_message(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            await self.unregister(websocket)

    async def process_message(self, websocket: WebSocketServerProtocol, message: str):
        """Process incoming WebSocket message."""
        try:
            data = json.loads(message)
            action = data.get("action")

            if action == "subscribe":
                # Client subscribes to telemetry stream
                channel = data.get("channel", "telemetry")
                response = {
                    "action": "subscribed",
                    "channel": channel,
                    "timestamp": datetime.now().isoformat(),
                }
                await websocket.send(json.dumps(response))

            elif action == "get_status":
                # Fetch current system status
                status = await self.get_system_status()
                await websocket.send(json.dumps(status))

            elif action == "get_ebdi":
                # Fetch EBDI telemetry
                ebdi_data = self.get_ebdi_telemetry()
                await websocket.send(json.dumps(ebdi_data))

        except Exception as e:
            print(f"❌ Error processing message: {e}")

    async def get_system_status(self) -> Dict:
        """Get current system status."""
        return {
            "action": "status",
            "timestamp": datetime.now().isoformat(),
            "agents_online": len(TRUST_SCORES),
            "clients_connected": len(clients),
            "uptime_seconds": time.time(),
        }

    def get_ebdi_telemetry(self) -> Dict:
        """Get EBDI telemetry with simulation."""
        # Simulate small changes in EBDI values
        for agent in EBDI_STATE:
            for key in EBDI_STATE[agent]:
                change = (os.urandom(1)[0] % 5 - 2) * 0.01
                EBDI_STATE[agent][key] += change
                EBDI_STATE[agent][key] = max(0, min(1, EBDI_STATE[agent][key]))

        crisis_agents = [
            agent for agent, pad in EBDI_STATE.items()
            if pad.get("arousal", 0) > 0.7
        ]

        return {
            "action": "telemetry",
            "timestamp": datetime.now().isoformat(),
            "telemetry": EBDI_STATE,
            "crisis_detected": len(crisis_agents) > 0,
            "crisis_agents": crisis_agents,
        }

    def get_trust_scores(self) -> Dict:
        """Get trust scores snapshot."""
        agents = [
            {
                "agent": agent,
                "trust_score": ts,
                "status": "operational" if ts >= 0.6 else "needs_recalibration",
            }
            for agent, ts in TRUST_SCORES.items()
        ]
        return {
            "action": "trust_scores",
            "timestamp": datetime.now().isoformat(),
            "agents": agents,
            "average": sum(TRUST_SCORES.values()) / len(TRUST_SCORES),
        }

    async def broadcast_telemetry(self):
        """Broadcast telemetry to all connected clients periodically."""
        while self.running:
            if clients:
                telemetry = self.get_ebdi_telemetry()
                message = json.dumps(telemetry)

                disconnected = set()
                for client in clients:
                    try:
                        await client.send(message)
                    except Exception:
                        disconnected.add(client)

                for client in disconnected:
                    await self.unregister(client)

            await asyncio.sleep(0.2)  # 200ms interval = <500ms latency

    async def broadcast_trust_scores(self):
        """Broadcast trust scores periodically."""
        while self.running:
            await asyncio.sleep(5)  # Every 5 seconds

            if clients:
                scores = self.get_trust_scores()
                message = json.dumps(scores)

                disconnected = set()
                for client in clients:
                    try:
                        await client.send(message)
                    except Exception:
                        disconnected.add(client)

                for client in disconnected:
                    await self.unregister(client)

    async def start(self):
        """Start WebSocket server."""
        self.running = True

        # Start broadcast tasks
        asyncio.create_task(self.broadcast_telemetry())
        asyncio.create_task(self.broadcast_trust_scores())

        # Start server
        async with websockets.serve(self.handle_client, WS_HOST, WS_PORT):
            print(f"✅ WebSocket server running: ws://{WS_HOST}:{WS_PORT}")
            while self.running:
                await asyncio.sleep(1)

    def stop(self):
        """Stop WebSocket server."""
        self.running = False


async def main():
    server = TelemetryServer()

    try:
        await server.start()
    except KeyboardInterrupt:
        print("\n✅ WebSocket server stopped")
        server.stop()


if __name__ == "__main__":
    print("╔════════════════════════════════════════════╗")
    print("║  Unified Admin Panel (UAP)                 ║")
    print("║  WebSocket Server for Real-Time Telemetry  ║")
    print(f"║  ws://{WS_HOST}:{WS_PORT}                    ║")
    print("╚════════════════════════════════════════════╝\n")

    asyncio.run(main())
