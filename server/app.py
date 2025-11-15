# server/app.py
import os
import re
import json
import logging
from typing import Dict, Any, List
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests

# ---------- CONFIG ----------
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_CHAT_ENDPOINT = f"{OLLAMA_HOST}/api/chat"
MODEL_NAME = os.getenv("OLLAMA_MODEL", "medllama2")   # change to your model
MAX_INPUT_LENGTH = int(os.getenv("MAX_INPUT_LENGTH", "4000"))
MODEL_TIMEOUT = int(os.getenv("MODEL_TIMEOUT", "30"))

# ---------- Logging ----------
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[logging.FileHandler("logs/server.log"), logging.StreamHandler()],
)
logger = logging.getLogger("ollama-backend")

# ---------- App ----------
app = Flask(__name__)
CORS(app)

# ---------- Simple PII redaction ----------
EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
PHONE_RE = re.compile(r"(\+?\d[\d -]{7,}\d)")

def redact_pii(text: str) -> str:
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
    lower = text.lower()
    for kw in EMERGENCY_KEYWORDS:
        if kw in lower:
            return True
    return False

# ---------- System prompt (instruct model to produce JSON) ----------
SYSTEM_PROMPT = """You are an informational medical assistant. RULES:
1) Do NOT give a definitive diagnosis. Provide probable conditions with numeric confidences between 0.0 and 1.0.
2) Output ONLY valid JSON in the schema:
{
  "plain_text": "<short user-friendly explanation>",
  "candidates": [{"condition":"", "confidence": 0.0, "evidence":["..."]}],
  "recommended_action": "<one-sentence action>",
  "follow_up_questions": ["..."],
  "disclaimer": "..."
}
3) If the user is in immediate danger (breathing difficulty, chest pain, unconscious), respond that they must call emergency services and output JSON consistent with above.
4) Keep answers concise and avoid alarming language.
"""

# ---------- Helper: call Ollama chat endpoint ----------
def call_ollama_chat(user_message: str) -> Dict[str, Any]:
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ],
        "stream": False,
        "format": "json"
    }

    resp = requests.post(OLLAMA_CHAT_ENDPOINT, json=payload, timeout=MODEL_TIMEOUT)
    resp.raise_for_status()
    return resp.json()

# ---------- Parse Ollama's response into our schema ----------
def parse_ollama_response(resp: Dict[str, Any]) -> Dict[str, Any]:
    # 1) Top-level keys
    for k in ("plain_text", "candidates", "recommended_action", "follow_up_questions"):
        if k in resp:
            return {
                "plain_text": resp.get("plain_text", ""),
                "candidates": resp.get("candidates", []),
                "recommended_action": resp.get("recommended_action", ""),
                "follow_up_questions": resp.get("follow_up_questions", []),
                "disclaimer": resp.get("disclaimer", "This is informational only.")
            }

    # 2) Look for likely text fields
    text_candidates = []
    for key in ("response", "output", "text", "reply"):
        v = resp.get(key)
        if isinstance(v, str) and v.strip():
            text_candidates.append(v)

    combined = "\n\n".join(text_candidates).strip()

    # 3) If combined looks like JSON, parse it
    if combined:
        try:
            start = combined.index("{")
            end = combined.rindex("}") + 1
            json_text = combined[start:end]
            parsed = json.loads(json_text)
            return {
                "plain_text": parsed.get("plain_text", combined),
                "candidates": parsed.get("candidates", []),
                "recommended_action": parsed.get("recommended_action", ""),
                "follow_up_questions": parsed.get("follow_up_questions", []),
                "disclaimer": parsed.get("disclaimer", "This is informational only.")
            }
        except Exception:
            return {
                "plain_text": combined,
                "candidates": [],
                "recommended_action": "If symptoms worsen, consult a physician.",
                "follow_up_questions": [],
                "disclaimer": "This is informational only."
            }

    return {
        "plain_text": "Sorry — no valid response from model.",
        "candidates": [],
        "recommended_action": "If unsure, consult a physician.",
        "follow_up_questions": [],
        "disclaimer": "This is informational only."
    }

# ---------- Make structured response ----------
def make_structured_response(plain_text: str, candidates: List[Dict[str, Any]], recommended_action: str, follow_up_questions: List[str]) -> Dict[str, Any]:
    return {
        "plain_text": plain_text,
        "candidates": candidates,
        "recommended_action": recommended_action,
        "follow_up_questions": follow_up_questions,
        "disclaimer": "This is informational only and not a medical diagnosis. Seek professional care for medical advice."
    }

# ---------- Routes ----------
@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "model": MODEL_NAME}), 200

@app.route("/api/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json(force=True)
    except Exception:
        return jsonify({"error": "Invalid JSON body."}), 400

    user_msg = (data.get("message") or "").strip()
    if not user_msg:
        return jsonify({"error": "Message is required."}), 400
    if len(user_msg) > MAX_INPUT_LENGTH:
        return jsonify({"error": "Message too long."}), 400

    # Emergency handling
    if detect_emergency(user_msg):
        logger.warning("Emergency detected (redacted): %s", redact_pii(user_msg))
        emergency_resp = make_structured_response(
            plain_text="This sounds like a medical emergency. Call emergency services immediately.",
            candidates=[],
            recommended_action="Call emergency services or go to the nearest emergency department immediately.",
            follow_up_questions=[]
        )
        return jsonify(emergency_resp), 200

    logger.info("Chat request (redacted): %s", redact_pii(user_msg)[:500])

    # Build and call Ollama
    try:
        ollama_resp = call_ollama_chat(user_msg)
        parsed = parse_ollama_response(ollama_resp)
        final = make_structured_response(
            plain_text=parsed.get("plain_text", ""),
            candidates=parsed.get("candidates", []),
            recommended_action=parsed.get("recommended_action", ""),
            follow_up_questions=parsed.get("follow_up_questions", [])
        )
        logger.info("Model reply (short): %s", redact_pii(final["plain_text"])[:400])
        return jsonify(final), 200
    except requests.exceptions.RequestException as e:
        logger.exception("Ollama request failed")
        return jsonify({"error": "Model request failed", "details": str(e)}), 502
    except Exception as e:
        logger.exception("Server error")
        return jsonify({"error": "Server error", "details": str(e)}), 500

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)
