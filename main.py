from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from typing import Optional
import os

app = FastAPI(title="Agentic HoneyPot API", version="1.0")

# =============================
# CONFIG
# =============================
API_KEY = os.getenv("API_KEY", "my-secret-key-123")

# =============================
# GUVI REQUEST MODELS
# =============================
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
# MAIN GUVI ENDPOINT
# =============================
@app.post("/scam")
def receive_scam(
    data: GuviRequest,
    x_api_key: str = Header(None)
):
    # API key validation
    if not x_api_key or x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")

    message_text = data.message.text.lower()

    # Simple human-like reply (as GUVI expects)
    reply = "Why is my account being suspended?"

    if "upi" in message_text:
        reply = "Why do you need my UPI details?"
    elif "otp" in message_text:
        reply = "I am not comfortable sharing OTP."
    elif "link" in message_text:
        reply = "Is there another way to verify?"

    # ✅ EXACT RESPONSE FORMAT REQUIRED BY GUVI
    return {
        "status": "success",
        "reply": reply
    }
