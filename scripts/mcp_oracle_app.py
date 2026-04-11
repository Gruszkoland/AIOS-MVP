"""
ORACLE-MCP Application
Decision Routing & 162D Space Navigation (Port 9003)
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import logging
from mcp_servers.oracle_mcp import OracleMCP

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger("ORACLE-MCP")

server = OracleMCP()


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "service": "ORACLE-MCP"}), 200


@app.route("/classify", methods=["POST"])
def classify_intent():
    payload = request.get_json()
    result = server.handle_classify_intent(
        query=payload.get("query"),
        context=payload.get("context", {})
    )
    return jsonify(result["result"]), 200 if result["success"] else 400


@app.route("/route", methods=["POST"])
def route_decision():
    payload = request.get_json()
    result = server.handle_route_decision(
        intent=payload.get("intent"),
        state=payload.get("state", {}),
        available_agents=payload.get("available_agents", [])
    )
    return jsonify(result["result"]), 200 if result["success"] else 400


@app.route("/pattern/match", methods=["POST"])
def pattern_match():
    payload = request.get_json()
    result = server.handle_pattern_match(
        state=payload.get("state", {}),
        vector_162d=payload.get("vector_162d", [0, 0, 0])
    )
    return jsonify(result["result"]), 200 if result["success"] else 400


@app.route("/options", methods=["POST"])
def generate_options():
    payload = request.get_json()
    result = server.handle_generate_options(
        decision_point=payload.get("decision_point", {})
    )
    return jsonify(result["result"]), 200 if result["success"] else 400


@app.route("/stats", methods=["GET"])
def stats():
    return jsonify(server.get_routing_stats()), 200


if __name__ == "__main__":
    logger.info("Starting ORACLE-MCP on 0.0.0.0:9003")
    app.run(host="0.0.0.0", port=9003, debug=False)
