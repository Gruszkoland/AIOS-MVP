"""
MCP Router Application
Main orchestration service (Port 9000)

Coordinates routing between 5 MCP servers:
- VORTEX-MCP (9001)   — Orchestration
- GUARDIAN-MCP (9002) — Security
- ORACLE-MCP (9003)   — Routing
- GENESIS-MCP (9004)  — State
- HEALER-MCP (9005)   — Recovery
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import logging
from datetime import datetime
from mcp_servers.router import MCPRouter

#  Configuration
app = Flask(__name__)
CORS(app)

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="[%(asctime)s] %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("MCP-ROUTER")

# Initialize router
router = MCPRouter()


# ════════════════════════════════════════════════════════════════════════════
# HEALTH & STATUS ENDPOINTS
# ════════════════════════════════════════════════════════════════════════════

@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "MCP-ROUTER",
        "port": 9000,
        "timestamp": datetime.utcnow().isoformat(),
        "uptime": "running"
    }), 200


@app.route("/status", methods=["GET"])
def status():
    """Detailed status"""
    return jsonify({
        "status": "operational",
        "agents_health": router.get_agent_health(),
        "routing_stats": router.get_routing_stats(),
        "timestamp": datetime.utcnow().isoformat()
    }), 200


# ════════════════════════════════════════════════════════════════════════════
# ROUTING ENDPOINTS
# ════════════════════════════════════════════════════════════════════════════

@app.route("/route", methods=["POST"])
def route_query():
    """
    Main routing endpoint

    Request:
    {
        "query": "user query or intent",
        "context": {
            "audit_logged": bool,
            "backup_exists": bool,
            "arousal": float [0...1],
            ...
        }
    }

    Response:
    {
        "decision": "approved|blocked|escalated|crisis",
        "agent": "VORTEX|GUARDIAN|ORACLE|GENESIS|HEALER",
        "trace": {...routing trace...},
        "result": {...execution result...}
    }
    """
    try:
        payload = request.get_json()
        query = payload.get("query", "")
        context = payload.get("context", {})

        if not query:
            return jsonify({"error": "Missing 'query' field"}), 400

        result = router.route_query(query, context)
        logger.info(f"Routed query: {query[:50]} -> {result.get('decision', 'unknown')}")

        return jsonify(result), 200

    except Exception as e:
        logger.error(f"Routing error: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/agent/<agent_name>/health", methods=["GET"])
def agent_health(agent_name):
    """Health check for specific agent"""
    if agent_name not in router.agents:
        return jsonify({"error": f"Agent {agent_name} not found"}), 404

    agent_info = router.agents[agent_name]
    return jsonify({
        "agent": agent_name,
        "port": agent_info.get("port"),
        "trust_score": agent_info.get("trust_score"),
        "timestamp": datetime.utcnow().isoformat()
    }), 200


# ════════════════════════════════════════════════════════════════════════════
# STATISTICS ENDPOINTS
# ════════════════════════════════════════════════════════════════════════════

@app.route("/stats/routing", methods=["GET"])
def routing_stats():
    """Routing statistics"""
    return jsonify(router.get_routing_stats()), 200


@app.route("/stats/agents", methods=["GET"])
def agent_stats():
    """All agents' statistics"""
    return jsonify(router.get_agent_health()), 200


@app.route("/traces/recent", methods=["GET"])
def recent_traces():
    """Get recent routing traces"""
    count = request.args.get("count", default=10, type=int)
    traces = router.traces[-count:]

    return jsonify({
        "traces": [router._serialize_trace(t) for t in traces],
        "total": len(router.traces)
    }), 200


# ════════════════════════════════════════════════════════════════════════════
# ERROR HANDLERS
# ════════════════════════════════════════════════════════════════════════════

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal error: {str(error)}")
    return jsonify({"error": "Internal server error"}), 500


# ════════════════════════════════════════════════════════════════════════════
# RUN
# ════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    host = os.getenv("MCP_ROUTER_HOST", "0.0.0.0")
    port = int(os.getenv("MCP_ROUTER_PORT", 9000))
    debug = os.getenv("MCP_DEBUG", "false").lower() == "true"

    logger.info(f"Starting MCP Router on {host}:{port}")
    app.run(host=host, port=port, debug=debug)
