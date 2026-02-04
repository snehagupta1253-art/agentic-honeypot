from fastapi import FastAPI, Header, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Union, Optional
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
# REQUEST MODELS
# =============================
class ScamRequest(BaseModel):
    conversation_id: str
    message: str


class GuviMessage(BaseModel):
    sender: str
    text: str
    timestamp: Optional[int] = None


class GuviRequest(BaseModel):
    sessionId: str
    message: GuviMessage
    conversationHistory: Optional[list] = []
    metadata: Optional[dict] = {}

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

    return {
        "is_scam": score >= 0.3,
        "confidence": round(min(score, 1.0), 2),
        "reasons": reasons
    }

# =============================
# AGENT BEHAVIOR
# =============================
def agent_reply(message: str, history: list) -> str:
    msg = message.lower()

    if len(history) <= 1:
        return "Why is my account being suspended?"

    if "upi" in msg:
        return "Please explain why UPI details are required."
    if "otp" in msg:
        return "I am not sure about sharing OTP. Can you clarify?"
    if "link" in msg:
        return "Is there any other way to verify?"

    return "Please explain the issue clearly."

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
        pass

# =============================
# ROOT
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
    data: Union[ScamRequest, GuviRequest],
    background_tasks: BackgroundTasks,
    x_api_key: str = Header(None)
):
    # API key validation
    if not x_api_key or x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")

    # Normalize input
    if isinstance(data, ScamRequest):
        conversation_id = data.conversation_id
        message_text = data.message
        is_guvi = False
    else:
        conversation_id = data.sessionId
        message_text = data.message.text
        is_guvi = True

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
        "message": message_text,
        "time": now
    })

    detection = detect_scam(message_text)
    reply = agent_reply(message_text, convo["messages"])

    # Store agent reply
    convo["messages"].append({
        "role": "agent",
        "message": reply,
        "time": datetime.utcnow()
    })

    # GUVI callback (background, non-blocking)
    if detection["is_scam"]:
        guvi_payload = {
            "sessionId": conversation_id,
            "scamDetected": True,
            "totalMessagesExchanged": len(convo["messages"]),
            "extractedIntelligence": {},
            "agentNotes": reply
        }
        background_tasks.add_task(send_guvi_callback, guvi_payload)

    # ✅ GUVI TESTER EXPECTED RESPONSE
    if is_guvi:
        return {
            "status": "success",
            "reply": reply
        }

    # Full response for normal API users
    return {
        "conversation_id": conversation_id,
        "scam_detected": detection["is_scam"],
        "agent_reply": reply,
        "engagement_metrics": {
            "turns": len(convo["messages"]),
            "engagement_duration_seconds": int(
                (now - convo["start_time"]).total_seconds()
            )
        }
    }
