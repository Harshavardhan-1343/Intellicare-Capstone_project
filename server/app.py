"""
Flask-based Medical Diagnostic API
Combines orchestrator-based session management with Flask HTTP methods
"""

import os
import re
import json
import logging
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime

from flask import Flask, request, jsonify
from flask_cors import CORS

# Import your orchestrator
try:
    from orchestrator import MedicalOrchestrator
except ImportError as e:
    print(f"WARNING: Could not import orchestrator: {e}")
    MedicalOrchestrator = None

# ---------- CONFIG ----------
MODEL_NAME = os.getenv("OLLAMA_MODEL", "medllama2")
MAX_INPUT_LENGTH = int(os.getenv("MAX_INPUT_LENGTH", "4000"))

# ---------- Logging ----------
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[logging.FileHandler("logs/server.log"), logging.StreamHandler()],
)
logger = logging.getLogger("medical-diagnostic-api")

# ---------- App ----------
app = Flask(__name__)
CORS(app)

# ---------- Session Storage ----------
sessions: Dict[str, MedicalOrchestrator] = {}

# ---------- Simple PII redaction ----------
EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
PHONE_RE = re.compile(r"(\+?\d[\d -]{7,}\d)")

def redact_pii(text: str) -> str:
    """Redact personally identifiable information from text"""
    t = EMAIL_RE.sub("[REDACTED_EMAIL]", text)
    t = PHONE_RE.sub("[REDACTED_PHONE]", t)
    t = re.sub(r"\b\d{6,}\b", "[REDACTED_ID]", t)
    return t

# ---------- Emergency detection ----------
EMERGENCY_KEYWORDS = [
    "chest pain", "difficulty breathing", "shortness of breath", "severe bleeding",
    "loss of consciousness", "unconscious", "seizure", "stroke", "sudden weakness",
    "sudden numbness", "severe burn", "severe head injury", "suicidal", "homicidal"
]

def detect_emergency(text: str) -> bool:
    """Detect emergency keywords in user message"""
    lower = text.lower()
    for kw in EMERGENCY_KEYWORDS:
        if kw in lower:
            return True
    return False

# ---------- Initialize on startup ----------
DEFAULT_ORCHESTRATOR = None

def initialize_default_orchestrator():
    """Initialize default orchestrator on first request"""
    global DEFAULT_ORCHESTRATOR
    if DEFAULT_ORCHESTRATOR is None and MedicalOrchestrator is not None:
        try:
            logger.info("Initializing default orchestrator...")
            DEFAULT_ORCHESTRATOR = MedicalOrchestrator(model_name=MODEL_NAME)
            logger.info("✅ Default orchestrator ready (MedLlama2-powered)")
        except Exception as e:
            logger.error(f"❌ Error initializing orchestrator: {e}")
            raise

# ---------- Routes ----------

@app.route("/", methods=["GET"])
def root():
    """Root endpoint with API information"""
    return jsonify({
        "status": "running",
        "service": "IntelliCare Medical Diagnostic API",
        "model": MODEL_NAME,
        "version": "2.0",
        "features": [
            "Privacy-respecting (can skip personal questions)",
            "Medical history collection",
            "Smart triage system",
            "Comprehensive differential diagnosis"
        ],
        "endpoints": {
            "/": "GET - API information",
            "/api/health": "GET - Health check",
            "/api/chat": "POST - Send a message (creates/uses sessions)",
            "/api/session/<session_id>": "GET - Get session info",
            "/api/reset/<session_id>": "POST - Reset a session",
            "/api/session/<session_id>": "DELETE - Delete a session"
        }
    }), 200

@app.route("/api/health", methods=["GET"])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "active_sessions": len(sessions),
        "model": MODEL_NAME,
        "timestamp": datetime.now().isoformat()
    }), 200

@app.route("/api/chat", methods=["POST"])
def chat():
    """
    Main chat endpoint - handles conversation with session management
    
    Request body:
    {
        "message": "user message",
        "session_id": "optional-session-id"
    }
    
    Response:
    {
        "session_id": "uuid",
        "response": "assistant response",
        "is_final": false,
        "diagnosis_data": {...} (only if is_final=true),
        "report": "..." (only if is_final=true)
    }
    """
    # Validate request
    try:
        data = request.get_json(force=True)
    except Exception:
        logger.error("Invalid JSON body received")
        return jsonify({"error": "Invalid JSON body."}), 400

    user_msg = (data.get("message") or "").strip()
    session_id = data.get("session_id")

    # Validate message
    if not user_msg:
        return jsonify({"error": "Message is required."}), 400
    if len(user_msg) > MAX_INPUT_LENGTH:
        return jsonify({"error": f"Message too long. Maximum length is {MAX_INPUT_LENGTH} characters."}), 400

    # Check for orchestrator availability
    if MedicalOrchestrator is None:
        logger.error("MedicalOrchestrator not available")
        return jsonify({"error": "Orchestrator module not available. Please check server configuration."}), 503

    # Emergency detection - prioritize immediate safety
    if detect_emergency(user_msg):
        logger.warning(f"Emergency detected (redacted): {redact_pii(user_msg)}")
        
        # Create emergency response
        emergency_response = {
            "session_id": session_id or str(uuid.uuid4()),
            "response": "⚠️ This sounds like a medical emergency. Please call emergency services immediately (911 in US) or go to the nearest emergency department. Do not wait for online consultation.",
            "is_final": True,
            "diagnosis_data": {
                "triage_level": 1,
                "triage_level_name": "IMMEDIATE EMERGENCY",
                "triage_message": "🚨 IMMEDIATE EMERGENCY - Call 911 or go to ER NOW",
                "recommendation": "Call emergency services immediately",
                "emergency_detected": True,
                "diagnoses": [],
                "department": "Emergency Medicine"
            },
            "report": None
        }
        return jsonify(emergency_response), 200

    logger.info(f"Chat request (redacted): {redact_pii(user_msg)[:500]}")

    try:
        # Initialize default orchestrator if needed
        initialize_default_orchestrator()

        # Get or create session
        if not session_id:
            session_id = str(uuid.uuid4())
            logger.info(f"Created new session: {session_id}")
        
        if session_id not in sessions:
            logger.info(f"Initializing orchestrator for session: {session_id}")
            sessions[session_id] = MedicalOrchestrator(model_name=MODEL_NAME)
        
        orchestrator = sessions[session_id]
        
        # Process message through orchestrator
        result = orchestrator.chat(user_msg)
        
        # Handle the 3-tuple return format (response, is_final, report)
        if len(result) == 3:
            response, is_final, report = result
        else:
            raise ValueError(f"Unexpected return format from orchestrator.chat: {len(result)} elements")
        
        # Prepare response
        chat_response = {
            "session_id": session_id,
            "response": response,
            "is_final": is_final,
            "diagnosis_data": None,
            "report": None
        }
        
        # If conversation is complete, get diagnosis data and cleanup
        if is_final:
            logger.info(f"Session {session_id} completed, generating diagnosis")
            
            try:
                # Get diagnosis data from orchestrator
                diagnosis_data = orchestrator.get_diagnosis_data()
                
                # Add triage level name for frontend
                if diagnosis_data and 'triage_level' in diagnosis_data:
                    triage_names = {
                        1: "IMMEDIATE EMERGENCY",
                        2: "URGENT",
                        3: "PRIORITY",
                        4: "ROUTINE",
                        5: "NON-URGENT"
                    }
                    diagnosis_data['triage_level_name'] = triage_names.get(
                        diagnosis_data['triage_level'], 
                        "UNKNOWN"
                    )
                    # Also add recommendation (alias for triage_message)
                    diagnosis_data['recommendation'] = diagnosis_data.get('triage_message', '')
                
                chat_response["diagnosis_data"] = diagnosis_data
                chat_response["report"] = report
                
            except Exception as e:
                logger.exception(f"Error generating diagnosis data: {e}")
                chat_response["diagnosis_data"] = {
                    "error": "Could not generate diagnosis data",
                    "triage_level": 5,
                    "triage_level_name": "UNKNOWN",
                    "diagnoses": [],
                    "department": "General Medicine",
                    "triage_message": "Please consult a healthcare professional"
                }
                chat_response["report"] = report  # Still include report if available
            
            # Clean up session after diagnosis
            if session_id in sessions:
                del sessions[session_id]
                logger.info(f"Session {session_id} cleaned up")
        
        logger.info(f"Response generated for session {session_id}: {redact_pii(response)[:200]}")
        return jsonify(chat_response), 200

    except Exception as e:
        logger.exception(f"Error processing chat request: {e}")
        return jsonify({
            "error": "Server error processing your request",
            "details": str(e)
        }), 500

@app.route("/api/session/<session_id>", methods=["GET"])
def get_session_info(session_id: str):
    """
    Get information about an active session
    
    Response:
    {
        "session_id": "uuid",
        "turn_count": 5,
        "symptoms_collected": ["cough", "fever"],
        "info_collected": ["age", "symptoms", "duration"],
        "info_skipped": ["gender", "medical_history"]
    }
    """
    if session_id not in sessions:
        logger.warning(f"Session not found: {session_id}")
        return jsonify({"error": "Session not found"}), 404
    
    try:
        orchestrator = sessions[session_id]
        
        # Extract session information based on actual orchestrator structure
        session_info = {
            "session_id": session_id,
            "turn_count": 0,
            "symptoms_collected": [],
            "info_collected": [],
            "info_skipped": []  # NEW: Track skipped info
        }
        
        # Get turn count from state
        if hasattr(orchestrator, 'state') and hasattr(orchestrator.state, 'turn_count'):
            session_info["turn_count"] = orchestrator.state.turn_count
        
        # Get symptoms from patient profile
        if hasattr(orchestrator, 'patient'):
            if hasattr(orchestrator.patient, 'symptoms'):
                session_info["symptoms_collected"] = orchestrator.patient.symptoms or []
            
            # Get what information has been collected
            if hasattr(orchestrator, 'state'):
                if hasattr(orchestrator.state, 'collected'):
                    session_info["info_collected"] = list(orchestrator.state.collected)
                # NEW: Get skipped info
                if hasattr(orchestrator.state, 'skipped'):
                    session_info["info_skipped"] = list(orchestrator.state.skipped)
        
        logger.info(f"Session info retrieved for {session_id}")
        return jsonify(session_info), 200
    
    except Exception as e:
        logger.exception(f"Error retrieving session info: {e}")
        return jsonify({"error": "Error retrieving session information", "details": str(e)}), 500

@app.route("/api/reset/<session_id>", methods=["POST"])
def reset_session(session_id: str):
    """
    Reset a session to start over
    
    Response:
    {
        "status": "reset",
        "session_id": "uuid"
    }
    """
    if session_id not in sessions:
        logger.warning(f"Cannot reset - session not found: {session_id}")
        return jsonify({"error": "Session not found"}), 404
    
    try:
        orchestrator = sessions[session_id]
        
        # Reset the orchestrator (it has a reset method)
        orchestrator.reset()
        logger.info(f"Session {session_id} reset")
        return jsonify({"status": "reset", "session_id": session_id}), 200
    
    except Exception as e:
        logger.exception(f"Error resetting session: {e}")
        return jsonify({"error": "Error resetting session", "details": str(e)}), 500

@app.route("/api/session/<session_id>", methods=["DELETE"])
def delete_session(session_id: str):
    """
    Delete a session
    
    Response:
    {
        "status": "deleted",
        "session_id": "uuid"
    }
    """
    if session_id not in sessions:
        logger.warning(f"Cannot delete - session not found: {session_id}")
        return jsonify({"error": "Session not found"}), 404
    
    try:
        del sessions[session_id]
        logger.info(f"Session {session_id} deleted")
        return jsonify({"status": "deleted", "session_id": session_id}), 200
    
    except Exception as e:
        logger.exception(f"Error deleting session: {e}")
        return jsonify({"error": "Error deleting session", "details": str(e)}), 500

# ---------- Error Handlers ----------

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(e):
    logger.exception("Internal server error")
    return jsonify({"error": "Internal server error"}), 500

# ---------- Main ----------

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    
    logger.info(f"Starting IntelliCare Medical Diagnostic API on port {port}")
    logger.info(f"Model: {MODEL_NAME}")
    logger.info(f"Debug mode: {debug}")
    
    app.run(host="0.0.0.0", port=port, debug=debug)