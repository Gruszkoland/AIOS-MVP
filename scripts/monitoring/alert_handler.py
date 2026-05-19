#!/usr/bin/env python3
"""
Alert Handler Service | ADRION 369
Integrates with Slack, Pagerduty, and custom webhooks for monitoring alerts
Guardian Law G5 (Transparency) — All alerts logged to audit trail
Guardian Law G8 (Nonmaleficence) — Safe error handling, no data leaks
"""

import os
import json
import logging
import requests
from datetime import datetime
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from flask import Flask, request, jsonify

# Load environment
load_dotenv()

# Configuration
HANDLER_PORT = int(os.getenv("HANDLER_PORT", 8090))
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "").strip()
PAGERDUTY_KEY = os.getenv("PAGERDUTY_KEY", "").strip()
ALERT_LOG_PATH = os.getenv("ALERT_LOG_PATH", "./monitoring/alerts/alerts.log")

# Ensure alert log directory exists
os.makedirs(os.path.dirname(ALERT_LOG_PATH), exist_ok=True)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(ALERT_LOG_PATH),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Flask app
app = Flask(__name__)

# ═══════════════════════════════════════════════════════════════
# ALERT ROUTING
# ═══════════════════════════════════════════════════════════════

def send_to_slack(alert: Dict[str, Any]) -> bool:
    """Send alert to Slack webhook"""
    if not SLACK_WEBHOOK_URL:
        logger.debug("SLACK_WEBHOOK_URL not configured, skipping Slack send")
        return False
    
    try:
        message = {
            "text": f"🚨 ADRION 369 Alert: {alert.get('title', 'Unnamed Alert')}",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"ADRION 369 — {alert.get('severity', 'INFO').upper()}",
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Title*\n{alert.get('title', 'N/A')}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Severity*\n{alert.get('severity', 'INFO')}"
                        }
                    ]
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"```{alert.get('message', 'No details')}```"
                    }
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"📨 {alert.get('source', 'Unknown')} | ⏰ {alert.get('timestamp', 'N/A')}"
                        }
                    ]
                }
            ]
        }
        
        response = requests.post(
            SLACK_WEBHOOK_URL,
            json=message,
            timeout=10
        )
        response.raise_for_status()
        logger.info(f"✅ Slack alert sent: {alert.get('title')}")
        return True
    except Exception as e:
        logger.error(f"❌ Slack alert failed: {str(e)}")
        return False


def send_to_pagerduty(alert: Dict[str, Any]) -> bool:
    """Send alert to Pagerduty"""
    if not PAGERDUTY_KEY:
        logger.debug("PAGERDUTY_KEY not configured, skipping Pagerduty send")
        return False
    
    try:
        severity_map = {
            "critical": "critical",
            "error": "error",
            "warning": "warning",
            "info": "info"
        }
        
        event = {
            "routing_key": PAGERDUTY_KEY,
            "event_action": "trigger",
            "dedup_key": alert.get("dedup_key", f"adrion-{datetime.now().timestamp()}"),
            "payload": {
                "summary": alert.get("title", "ADRION 369 Alert"),
                "severity": severity_map.get(alert.get("severity", "info").lower(), "info"),
                "source": alert.get("source", "ADRION 369"),
                "timestamp": alert.get("timestamp", datetime.utcnow().isoformat()),
                "custom_details": {
                    "message": alert.get("message", ""),
                    "container": alert.get("container", "unknown")
                }
            }
        }
        
        response = requests.post(
            "https://events.pagerduty.com/v2/enqueue",
            json=event,
            timeout=10
        )
        response.raise_for_status()
        logger.info(f"✅ PagerDuty alert sent: {alert.get('title')}")
        return True
    except Exception as e:
        logger.error(f"❌ PagerDuty alert failed: {str(e)}")
        return False


def route_alert(alert: Dict[str, Any]) -> Dict[str, Any]:
    """
    Route alert to appropriate handlers based on severity
    Implements Guardian Law G5 (Transparency) via logging
    """
    severity = alert.get("severity", "info").lower()
    
    # Log to audit trail (G5 — Transparency)
    logger.info(f"ALERT LOGGED | Severity: {severity} | Source: {alert.get('source')} | Title: {alert.get('title')}")
    
    # Route based on severity
    results = {
        "slack_sent": False,
        "pagerduty_sent": False,
        "logged": True
    }
    
    if severity in ["critical", "error"]:
        # Send to both Slack and PagerDuty for critical issues
        results["slack_sent"] = send_to_slack(alert)
        results["pagerduty_sent"] = send_to_pagerduty(alert)
    elif severity == "warning":
        # Send to Slack for warnings
        results["slack_sent"] = send_to_slack(alert)
    else:
        # Only log info and debug
        logger.debug(f"Info-level alert: {alert.get('title')}")
    
    return results


# ═══════════════════════════════════════════════════════════════
# API ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "adrion-alert-handler",
        "timestamp": datetime.utcnow().isoformat(),
        "slack_configured": bool(SLACK_WEBHOOK_URL),
        "pagerduty_configured": bool(PAGERDUTY_KEY)
    }), 200


@app.route("/alert", methods=["POST"])
def handle_alert():
    """Main alert handler endpoint"""
    try:
        alert_data = request.get_json() or request.form.to_dict()
        
        # Validate required fields
        alert = {
            "title": alert_data.get("alert", alert_data.get("title", "Unnamed Alert")),
            "message": alert_data.get("message", ""),
            "severity": alert_data.get("severity", "info"),
            "source": alert_data.get("source", "grafana"),
            "container": alert_data.get("container", "unknown"),
            "timestamp": datetime.utcnow().isoformat(),
            "dedup_key": alert_data.get("dedup_key")
        }
        
        # Route alert
        routing_result = route_alert(alert)
        
        return jsonify({
            "status": "received",
            "alert_id": alert.get("dedup_key"),
            "routing": routing_result
        }), 202
    
    except Exception as e:
        logger.error(f"❌ Alert handler error: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Failed to process alert",
            "details": str(e)
        }), 500


@app.route("/alert/test", methods=["POST"])
def test_alert():
    """Test alert delivery (dev only)"""
    test_alert_data = {
        "title": "🧪 Test Alert from ADRION",
        "message": "This is a test alert. If you see this, the alert handler is working!",
        "severity": request.args.get("severity", "warning"),
        "source": "alert-handler-test",
        "container": "adrion-alert-handler",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    result = route_alert(test_alert_data)
    logger.info(f"✅ Test alert processed: {result}")
    
    return jsonify({
        "status": "test_alert_sent",
        "alert": test_alert_data,
        "routing": result
    }), 200


@app.route("/alerts", methods=["GET"])
def get_recent_alerts():
    """Retrieve recent alerts from log (last N lines)"""
    limit = int(request.args.get("limit", 50))
    
    try:
        with open(ALERT_LOG_PATH, "r") as f:
            lines = f.readlines()
        
        recent_alerts = lines[-limit:]
        
        return jsonify({
            "total_lines": len(lines),
            "returned": len(recent_alerts),
            "alerts": recent_alerts
        }), 200
    except Exception as e:
        logger.error(f"Failed to read alert log: {str(e)}")
        return jsonify({"error": str(e)}), 500


# ═══════════════════════════════════════════════════════════════
# STARTUP & SHUTDOWN
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("🚀 ADRION 369 Alert Handler Service Starting")
    logger.info("=" * 60)
    logger.info(f"Port: {HANDLER_PORT}")
    logger.info(f"Slack Webhook: {'✅ Configured' if SLACK_WEBHOOK_URL else '❌ Not configured'}")
    logger.info(f"PagerDuty Key: {'✅ Configured' if PAGERDUTY_KEY else '❌ Not configured'}")
    logger.info(f"Alert Log: {ALERT_LOG_PATH}")
    logger.info("=" * 60)
    
    # Run Flask
    app.run(
        host="0.0.0.0",
        port=HANDLER_PORT,
        debug=os.getenv("DEBUG_MODE", "false").lower() == "true"
    )
