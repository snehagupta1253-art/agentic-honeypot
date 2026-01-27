from fastapi import FastAPI, Header, HTTPException
import re
from datetime import datetime
import requests

app = FastAPI(title="Agentic HoneyPot API", version="1.0")

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
# CONFIG
# =============================
API_KEY = "my-secret-key-123"
MAX_TURNS = 20
GUVI_CALLBACK_URL = "https://hackathon.guvi.in/api/updateHoneyPotFinalResult"

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
        return "Which bank account is this? I have multiple accounts."
    if "upi" in msg:
        return "Okay, I use UPI. Please share the exact UPI ID."
    if "link" in msg:
        return "I am not comfortable clicking links. Is there another way?"
    if "otp" in msg:
        return "I received multiple OTPs. Which one do you need?"

    return "I am confused. Please guide me step by step."

# =============================
# INTELLIGENCE EXTRACTION
# =============================
def extract_intelligence(message: str):
    bank_accounts = re.findall(r"\b\d{9,18}\b", message)
    upi_ids = re.findall(r"\b[\w.-]+@[\w]+\b", message)
    urls = re.findall(r"https?://[^\s]+", message)

    return {
        "bankAccounts": bank_accounts,
        "upiIds": upi_ids,
        "phishingLinks": urls,
        "phoneNumbers": [],
        "suspiciousKeywords": []
    }

# =============================
# FINAL CALLBACK TO GUVI
# =============================
def send_final_callback(session_id, total_messages, intelligence, agent_notes):
    payload = {
        "sessionId": session_id,
        "scamDetected": True,
        "totalMessagesExchanged": total_messages,
        "extractedIntelligence": intelligence,
        "agentNotes": agent_notes
    }

    try:
        requests.post(GUVI_CALLBACK_URL, json=payload, timeout=5)
    except Exception:
        pass  # Do NOT fail main API on callback error

# =============================
# MAIN API ENDPOINT (GUVI FORMAT)
# =============================
@app.post("/scam")
def receive_scam(
    data: dict,
    x_api_key: str = Header(None)
):
    # --- Security ---
    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")

    # --- INPUT ADAPTER ---
    session_id = data.get("sessionId")
    message_obj = data.get("message", {})
    message_text = message_obj.get("text", "")
    conversation_history = data.get("conversationHistory", [])

    now = datetime.utcnow()

    # Init conversation
    if session_id not in conversation_store:
        conversation_store[session_id] = {
            "start_time": now,
            "messages": []
        }

    convo = conversation_store[session_id]

    if len(convo["messages"]) >= MAX_TURNS:
        raise HTTPException(status_code=429, detail="Max conversation turns exceeded")

    convo["messages"].append({
        "role": "scammer",
        "message": message_text,
        "time": now
    })

    detection = detect_scam(message_text)

    turns = len(convo["messages"])
    duration = int((now - convo["start_time"]).total_seconds())

    # --- DEFAULT RESPONSE ---
    response = {
        "status": "success",
        "scamDetected": detection["is_scam"],
        "engagementMetrics": {
            "engagementDurationSeconds": duration,
            "totalMessagesExchanged": turns
        },
        "extractedIntelligence": {
            "bankAccounts": [],
            "upiIds": [],
            "phishingLinks": []
        },
        "agentNotes": None
    }

    # --- AGENT HANDOFF ---
    if detection["is_scam"]:
        reply = agent_reply(message_text, convo["messages"])

        convo["messages"].append({
            "role": "user",
            "message": reply,
            "time": datetime.utcnow()
        })

        intelligence = extract_intelligence(message_text)
        agent_notes = "Scammer used urgency tactics and payment redirection"

        response["extractedIntelligence"] = {
            "bankAccounts": intelligence["bankAccounts"],
            "upiIds": intelligence["upiIds"],
            "phishingLinks": intelligence["phishingLinks"]
        }
        response["agentNotes"] = agent_notes

        # --- FINAL CALLBACK (MANDATORY) ---
        send_final_callback(
            session_id=session_id,
            total_messages=len(convo["messages"]),
            intelligence=intelligence,
            agent_notes=agent_notes
        )

    return response
