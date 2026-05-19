"""
GENESIS-MCP Application
State Management, RAG & Local-First Persistence (Port 9004)

Integrated with:
- Event Sourcing (CQRS pattern, immutable audit trail)
- RAG Context Optimization
- Guardian Law G5 (Transparency) via complete event logging
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import logging
from datetime import datetime
from mcp_servers.genesis_mcp import GenesisMCP
from scripts.event_sourcing import EventSourcingStore

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger("GENESIS-MCP")

server = GenesisMCP()

# Initialize Event Sourcing Store (CQRS pattern)
event_store = EventSourcingStore(
    log_file=os.path.join(os.path.dirname(__file__), "Genesis Record", "event_log.jsonl")
)
logger.info("✓ Event Sourcing Store initialized (Guardian Law G5: Transparency)")


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


# ==================== EVENT SOURCING ENDPOINTS (CQRS Pattern) ===================

@app.route("/event/record", methods=["POST"])
def record_event():
    """
    Record a new event in immutable event log.

    Payload:
        {
            "event_type": "TASK_COMPLETED",
            "entity_id": "agent_1",
            "data": {"task_id": "T123", "result": "success"}
        }

    Returns: Event ID + timestamp
    """
    try:
        payload = request.get_json()
        event = event_store.record_event(
            event_type=payload.get("event_type"),
            entity_id=payload.get("entity_id"),
            data=payload.get("data", {})
        )

        logger.info(f"Event recorded: {event.event_type} (entity={event.entity_id}, event_id={event.event_id})")

        return jsonify({
            "success": True,
            "event_id": event.event_id,
            "timestamp": event.timestamp,
            "entity_id": event.entity_id
        }), 201
    except Exception as e:
        logger.error(f"Failed to record event: {e}")
        return jsonify({"success": False, "error": str(e)}), 400


@app.route("/event/history/<entity_id>", methods=["GET"])
def get_entity_history(entity_id):
    """
    Get complete event history for an entity (audit trail).

    Returns: Chronological list of all events for entity
    """
    try:
        history = event_store.get_entity_history(entity_id)
        return jsonify({
            "success": True,
            "entity_id": entity_id,
            "event_count": len(history),
            "events": history
        }), 200
    except Exception as e:
        logger.error(f"Failed to retrieve history: {e}")
        return jsonify({"success": False, "error": str(e)}), 400


@app.route("/event/state/<entity_id>", methods=["GET"])
def get_entity_state(entity_id):
    """
    Get current state of entity (from materialized view).
    Much faster than replaying events.

    Returns: Current state with TS, task counts, etc.
    """
    try:
        state = event_store.get_entity_state(entity_id)
        return jsonify({
            "success": True,
            "entity_id": entity_id,
            "state": state
        }), 200
    except Exception as e:
        logger.error(f"Failed to get entity state: {e}")
        return jsonify({"success": False, "error": str(e)}), 400


@app.route("/event/replay/<entity_id>", methods=["GET"])
def replay_entity(entity_id):
    """
    Replay all events for entity to verify state reconstruction.
    Useful for debugging and compliance verification.

    Returns: Full replay history showing state evolution
    """
    try:
        replay = event_store.replay_entity(entity_id)
        return jsonify({
            "success": True,
            "entity_id": entity_id,
            "replay": replay,
            "event_count": len(replay.get("history", []))
        }), 200
    except Exception as e:
        logger.error(f"Failed to replay entity: {e}")
        return jsonify({"success": False, "error": str(e)}), 400


@app.route("/event/audit", methods=["GET"])
def get_audit_trail():
    """
    Get global audit trail (all events across all entities).

    Query params:
        - event_type: Filter by event type (optional)
        - limit: Max events to return (default 100)

    Returns: Paginated list of all events
    """
    try:
        event_type = request.args.get("event_type")
        limit = int(request.args.get("limit", 100))

        if event_type:
            events = event_store.event_log.get_by_type(event_type)[:limit]
        else:
            events = event_store.event_log.get_all()[:limit]

        return jsonify({
            "success": True,
            "event_count": len(events),
            "limit": limit,
            "events": events
        }), 200
    except Exception as e:
        logger.error(f"Failed to retrieve audit trail: {e}")
        return jsonify({"success": False, "error": str(e)}), 400


@app.route("/event/statistics", methods=["GET"])
def event_statistics():
    """
    Get event log statistics (for monitoring).

    Returns: Total events, entity count, log file size, view version
    """
    try:
        stats = event_store.get_statistics()
        return jsonify({
            "success": True,
            "statistics": stats
        }), 200
    except Exception as e:
        logger.error(f"Failed to get statistics: {e}")
        return jsonify({"success": False, "error": str(e)}), 400


# ==================== INTEGRATION WITH EXISTING ENDPOINTS ===================

@app.before_request
def log_request_event():
    """
    Auto-log HTTP requests to event store (audit trail).
    Records: method, path, status (after response).
    """
    # Store in request context for use in after_request hook
    request.event_context = {
        "method": request.method,
        "path": request.path,
        "timestamp": None
    }


@app.after_request
def log_response_event(response):
    """
    Auto-log HTTP responses to event store.
    Records: response status code, latency.
    """
    try:
        if hasattr(request, 'event_context') and request.path.startswith("/event/"):
            # Don't log event endpoints recursively
            return response

        # For tracked endpoints: /session, /memory, /checkpoint
        if any(prefix in request.path for prefix in ["/session", "/memory", "/checkpoint"]):
            event_store.record_event(
                event_type="HTTP_REQUEST",
                entity_id=f"genesis_mcp",
                data={
                    "method": request.method,
                    "path": request.path,
                    "status_code": response.status_code
                }
            )
    except Exception as e:
        logger.warning(f"Failed to log response event: {e}")

    return response


# ==================== COMPATIBILITY ALIASES (Simple API) ===================

@app.route("/events", methods=["GET"])
def get_events():
    """
    GET /events - Alias for /event/audit
    Returns all events in audit trail (compatibility endpoint)

    Query params:
        - since: <timestamp> (filter events after timestamp)
        - limit: max events to return (default 100)
    """
    try:
        limit = int(request.args.get("limit", 100))
        events = event_store.event_log.get_all()[:limit]

        return jsonify({
            "success": True,
            "count": len(events),
            "events": events,
            "timestamp": datetime.utcnow().isoformat()
        }), 200
    except Exception as e:
        logger.error(f"Failed to get events: {e}")
        return jsonify({"success": False, "error": str(e)}), 400


@app.route("/state", methods=["GET"])
def get_global_state():
    """
    GET /state - Global system state snapshot
    Returns materialized view of entire system state

    Returns:
        {
            "success": true,
            "state": {overall system state},
            "timestamp": <now>,
            "version": "1.0"
        }
    """
    try:
        # Aggregate state from all entities
        all_events = event_store.event_log.get_all()
        entity_ids = set(e.get("entity_id") for e in all_events if e.get("entity_id"))

        entities_state = {}
        for entity_id in entity_ids:
            try:
                entities_state[entity_id] = event_store.get_entity_state(entity_id)
            except:
                pass

        return jsonify({
            "success": True,
            "state": {
                "total_entities": len(entity_ids),
                "total_events": len(all_events),
                "entities": entities_state
            },
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0"
        }), 200
    except Exception as e:
        logger.error(f"Failed to get state: {e}")
        return jsonify({"success": False, "error": str(e)}), 400


@app.route("/history", methods=["GET"])
def get_global_history():
    """
    GET /history - Complete event replay history
    Returns all events grouped by entity

    Query params:
        - limit: max total events (default 500)
    """
    try:
        limit = int(request.args.get("limit", 500))
        all_events = event_store.event_log.get_all()[:limit]

        # Group by entity_id
        history_by_entity = {}
        for event in all_events:
            entity_id = event.get("entity_id", "unknown")
            if entity_id not in history_by_entity:
                history_by_entity[entity_id] = []
            history_by_entity[entity_id].append(event)

        return jsonify({
            "success": True,
            "total": len(all_events),
            "entities": len(history_by_entity),
            "history": history_by_entity
        }), 200
    except Exception as e:
        logger.error(f"Failed to get history: {e}")
        return jsonify({"success": False, "error": str(e)}), 400


@app.route("/replay", methods=["POST"])
def replay_events():
    """
    POST /replay - Replay events up to specific timestamp
    Reconstructs system state by replaying events

    Payload:
        {
            "timestamp": <ISO datetime>,  // Optional: replay up to this point
            "entity_id": "agent_1"        // Optional: replay specific entity only
        }

    Returns:
        {
            "success": true,
            "replayed": <count>,
            "state": {reconstructed state}
        }
    """
    try:
        payload = request.get_json() or {}
        target_timestamp = payload.get("timestamp")
        entity_id = payload.get("entity_id")

        # Get events to replay
        if entity_id:
            events = event_store.get_entity_history(entity_id)
        else:
            events = event_store.event_log.get_all()

        # Filter by timestamp if provided
        if target_timestamp:
            events = [e for e in events if e.get("timestamp", "") <= target_timestamp]

        # Build replayed state
        replayed_state = {"history": events}

        return jsonify({
            "success": True,
            "replayed": len(events),
            "status": "ok",
            "state": replayed_state
        }), 200
    except Exception as e:
        logger.error(f"Failed to replay events: {e}")
        return jsonify({"success": False, "error": str(e)}), 400


if __name__ == "__main__":
    logger.info("="*70)
    logger.info("GENESIS-MCP with Event Sourcing (CQRS Pattern)")
    logger.info("Starting on 0.0.0.0:9004")
    logger.info("Event Log: Genesis Record/event_log.jsonl")
    logger.info("Guardian Law G5: Complete transparency via immutable audit trail")
    logger.info("="*70)
    app.run(host="0.0.0.0", port=9004, debug=False)
