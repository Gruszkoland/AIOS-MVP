"""
GUARDIAN-MCP Application
Security & Compliance Engine (Port 9002)
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import logging
from mcp_servers.guardian_mcp import GuardianMCP

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger("GUARDIAN-MCP")

server = GuardianMCP()


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "service": "GUARDIAN-MCP"}), 200


@app.route("/validate", methods=["POST"])
def validate_policy():
    payload = request.get_json()
    result = server.handle_validate_policy(
        operation=payload.get("operation"),
        context=payload.get("context", {})
    )
    return jsonify(result["result"]), 200 if result["success"] else 400


@app.route("/audit/log", methods=["POST"])
def audit_log():
    payload = request.get_json()
    result = server.handle_audit_event(
        event=payload.get("event"),
        actor=payload.get("actor"),
        timestamp=payload.get("timestamp")
    )
    return jsonify(result["result"]), 200 if result["success"] else 400


@app.route("/laws/check", methods=["POST"])
def laws_check():
    payload = request.get_json()
    result = server.handle_law_enforcement(
        operation=payload.get("operation"),
        scope=payload.get("scope")
    )
    return jsonify(result["result"]), 200 if result["success"] else 400


@app.route("/privacy/scan", methods=["POST"])
def privacy_scan():
    payload = request.get_json()
    result = server.handle_privacy_scan(
        data=payload.get("data"),
        sensitivity=payload.get("sensitivity")
    )
    return jsonify(result["result"]), 200 if result["success"] else 400


@app.route("/audit/summary", methods=["GET"])
def audit_summary():
    return jsonify(server.get_audit_log_summary()), 200


if __name__ == "__main__":
    logger.info("Starting GUARDIAN-MCP on 0.0.0.0:9002")
    app.run(host="0.0.0.0", port=9002, debug=False)
