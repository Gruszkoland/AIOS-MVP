"""
VORTEX-MCP Application
Harmonic Orchestration @ 174Hz (Port 9001)
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import logging
from datetime import datetime
from mcp_servers.vortex_mcp import VortexMCP

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger("VORTEX-MCP")

server = VortexMCP()


@app.route("/health", methods=["GET"])
def health():
    result = server.handle_health_check()
    return jsonify(result["result"]), 200 if result["success"] else 500


@app.route("/canary/deploy", methods=["POST"])
def canary_deploy():
    payload = request.get_json()
    result = server.handle_canary_deploy(
        backend=payload.get("backend"),
        percent=payload.get("percent", 5),
        constraints=payload.get("constraints", [])
    )
    return jsonify(result["result"]), 200 if result["success"] else 400


@app.route("/logs/<service>", methods=["GET"])
def get_logs(service):
    lines = request.args.get("lines", 50, type=int)
    result = server.handle_container_logs(service, lines)
    return jsonify(result["result"]), 200 if result["success"] else 404


@app.route("/monitor/harmonic", methods=["GET"])
def monitor_harmonic():
    result = server.handle_monitor_harmonic()
    return jsonify(result["result"]), 200 if result["success"] else 500


@app.route("/status", methods=["GET"])
def status():
    return jsonify(server.to_dict()), 200


if __name__ == "__main__":
    logger.info("Starting VORTEX-MCP on 0.0.0.0:9001")
    app.run(host="0.0.0.0", port=9001, debug=False)
