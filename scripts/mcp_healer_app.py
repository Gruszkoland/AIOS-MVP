"""
HEALER-MCP Application
Automated Recovery, Health Monitoring & Alerts (Port 9005)
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import logging
from mcp_servers.healer_mcp import HealerMCP

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger("HEALER-MCP")

server = HealerMCP()


@app.route("/health", methods=["GET"])
def health():
    result = server.handle_health_report()
    return jsonify(result["result"]), 200 if result["success"] else 500


@app.route("/health/report", methods=["GET"])
def health_report():
    result = server.handle_health_report()
    return jsonify(result["result"]), 200 if result["success"] else 500


@app.route("/rollback", methods=["POST"])
def trigger_rollback():
    payload = request.get_json()
    result = server.handle_trigger_rollback(
        checkpoint_id=payload.get("checkpoint_id"),
        scope=payload.get("scope", "local")
    )
    return jsonify(result["result"]), 200 if result["success"] else 400


@app.route("/heal/auto", methods=["POST"])
def auto_heal():
    payload = request.get_json()
    result = server.handle_self_heal(
        anomaly_type=payload.get("anomaly_type", "unknown")
    )
    return jsonify(result["result"]), 200 if result["success"] else 400


@app.route("/telemetry/alert", methods=["POST"])
def telemetry_alert():
    payload = request.get_json()
    result = server.handle_telemetry_alert(
        metric=payload.get("metric"),
        value=payload.get("value")
    )
    return jsonify(result["result"]), 200 if result["success"] else 400


@app.route("/stats", methods=["GET"])
def stats():
    return jsonify(server.get_recovery_stats()), 200


if __name__ == "__main__":
    logger.info("Starting HEALER-MCP on 0.0.0.0:9005")
    app.run(host="0.0.0.0", port=9005, debug=False)
