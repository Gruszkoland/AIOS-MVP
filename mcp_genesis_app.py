"""
GENESIS-MCP Application
State Management, RAG & Local-First Persistence (Port 9004)
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import logging
from mcp_servers.genesis_mcp import GenesisMCP

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger("GENESIS-MCP")

server = GenesisMCP()


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "service": "GENESIS-MCP"}), 200


@app.route("/session/save", methods=["POST"])
def save_session():
    payload = request.get_json()
    result = server.handle_save_session(
        session_id=payload.get("session_id"),
        state=payload.get("state", {})
    )
    return jsonify(result["result"]), 200 if result["success"] else 400


@app.route("/memory/recall", methods=["POST"])
def recall_memory():
    payload = request.get_json()
    result = server.handle_recall_memory(
        query=payload.get("query"),
        scope=payload.get("scope", "local")
    )
    return jsonify(result["result"]), 200 if result["success"] else 400


@app.route("/rag/search", methods=["POST"])
def rag_search():
    payload = request.get_json()
    result = server.handle_rag_search(
        embedding=payload.get("embedding", []),
        top_k=payload.get("top_k", 5)
    )
    return jsonify(result["result"]), 200 if result["success"] else 400


@app.route("/log/append", methods=["POST"])
def log_append():
    payload = request.get_json()
    result = server.handle_log_event(
        event=payload.get("event"),
        level=payload.get("level", "info")
    )
    return jsonify(result["result"]), 200 if result["success"] else 400


@app.route("/checkpoint/create", methods=["POST"])
def checkpoint_create():
    payload = request.get_json()
    result = server.handle_checkpoint_create(
        checkpoint_id=payload.get("checkpoint_id"),
        data=payload.get("data", {})
    )
    return jsonify(result["result"]), 200 if result["success"] else 400


@app.route("/stats", methods=["GET"])
def stats():
    return jsonify(server.get_memory_stats()), 200


if __name__ == "__main__":
    logger.info("Starting GENESIS-MCP on 0.0.0.0:9004")
    app.run(host="0.0.0.0", port=9004, debug=False)
