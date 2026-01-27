from fastapi import FastAPI, Header, HTTPException, BackgroundTasks
from pydantic import BaseModel
import re
from datetime import datetime
import os
import requests

app = FastAPI(title="Agentic HoneyPot API", version="1.0")

# =============================
# CONFIG
# =============================
API_KEY = os.getenv("API_KEY", "my-secret-key-123")
MAX_TURNS = 20

# =============================
# REQUEST MODEL
# =============================
class ScamRequest(BaseModel):
    conversation_id: str
    message: str

# =============================
# IN-MEMORY STORAGE
# =============================
conversation_store = {}

# =============================
# SCAM DETECTION RULES
# =============================
SCAM_KEYWORDS = {
    "blocked": 0.2,
    "urgent": 0.2,
    "verify": 0.2,
    "otp": 0.3,
    "upi": 0.3,
    "account": 0.2,
    "bank": 0.2,
    "link": 0.3,
    "suspended": 0.3
}

def detect_scam(message: str):
    msg = message.lower()
    score = 0.0
    reasons = []

    for word, weight in SCAM_KEYWORDS.items():
        if word in msg:
            score += weight
            reasons.append(word)

    score = min(score, 1.0)

    return {
        "is_scam": score >= 0.3,
        "confidence": round(score, 2),
        "reasons": reasons
    }

# =============================
# AGENT BEHAVIOR
# =============================
def agent_reply(message: str, history: list) -> str:
    msg = message.lower()

    if len(history) <= 1:
        return "Hello, I just received this message. Can you explain what happened?"

    if "account" in msg:
        return "Which bank account is this related to?"
    if "upi" in msg or "payment" in msg:
        return "Please share the exact UPI ID."
    if "link" in msg:
        return "I am not comfortable clicking links. Is there another way?"
    if "otp" in msg:
        return "I received multiple OTPs. Which one do you need?"

    return "Please guide me step by step."

# =============================
# INTELLIGENCE EXTRACTION
# =============================
def extract_intelligence(message: str):
    bank_accounts = re.findall(r"\b\d{9,18}\b", message)
    upi_ids = re.findall(r"\b[\w.-]+@[\w]+\b", message)
    urls = re.findall(r"https?://[^\s]+", message)

    confidence = 0.0
    if bank_accounts:
        confidence += 0.4
    if upi_ids:
        confidence += 0.3
    if urls:
        confidence += 0.3

    return {
        "bank_accounts": bank_accounts,
        "upi_ids": upi_ids,
        "phishing_urls": urls,
        "intelligence_confidence": round(min(confidence, 1.0), 2)
    }

# =============================
# GUVI CALLBACK (BACKGROUND)
# =============================
def send_guvi_callback(payload):
    try:
        requests.post(
            "https://hackathon.guvi.in/api/updateHoneyPotFinalResult",
            json=payload,
            timeout=5
        )
    except Exception:
        # Never block or crash main API
        pass

# =============================
# ROOT ENDPOINT
# =============================
@app.get("/")
def root():
    return {
        "status": "Agentic Honey-Pot API is running",
        "docs": "/docs",
        "endpoint": "/scam"
    }

# =============================
# MAIN API
# =============================
@app.post("/scam")
def receive_scam(
    data: ScamRequest,
    background_tasks: BackgroundTasks,
    x_api_key: str = Header(None)
):
    # API Key validation
    if not x_api_key or x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")

    conversation_id = data.conversation_id
    message = data.message
    now = datetime.utcnow()

    if conversation_id not in conversation_store:
        conversation_store[conversation_id] = {
            "start_time": now,
            "messages": []
        }

    convo = conversation_store[conversation_id]

    if len(convo["messages"]) >= MAX_TURNS:
        raise HTTPException(status_code=429, detail="Max conversation turns exceeded")

    # Store scammer message
    convo["messages"].append({
        "role": "scammer",
        "message": message,
        "time": now
    })

    detection = detect_scam(message)

    response = {
        "conversation_id": conversation_id,
        "scam_detected": detection["is_scam"],
        "scam_confidence": detection["confidence"],
        "detection_reasons": detection["reasons"],
        "engagement_metrics": {
            "turns": len(convo["messages"]),
            "engagement_duration_seconds": int(
                (now - convo["start_time"]).total_seconds()
            )
        },
        "agent_reply": None,
        "extracted_intelligence": {
            "bank_accounts": [],
            "upi_ids": [],
            "phishing_urls": [],
            "intelligence_confidence": 0.0
        }
    }

    if detection["is_scam"]:
        reply = agent_reply(message, convo["messages"])
        convo["messages"].append({
            "role": "agent",
            "message": reply,
            "time": datetime.utcnow()
        })

        response["agent_reply"] = reply
        response["extracted_intelligence"] = extract_intelligence(message)

        # GUVI callback payload
        guvi_payload = {
            "sessionId": conversation_id,
            "scamDetected": True,
            "totalMessagesExchanged": len(convo["messages"]),
            "extractedIntelligence": response["extracted_intelligence"],
            "agentNotes": reply
        }

        # Send callback in background (NON-BLOCKING)
        background_tasks.add_task(send_guvi_callback, guvi_payload)

    return response
