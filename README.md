# Agentic Honey-Pot for Scam Detection & Intelligence Extraction

## 🚀 Project Overview
This project implements an **AI-powered Agentic Honey-Pot system** that detects scam messages and autonomously engages scammers to extract **actionable intelligence** such as bank account numbers, UPI IDs, and phishing URLs through **multi-turn conversations**.

The system is designed to behave like a **real human**, avoid exposing scam detection, and incrementally gather intelligence while maintaining ethical and stable behavior.

This solution is built as a **public REST API**, secured using an API key, and deployed for real-time evaluation.

---

## 🎯 Key Objectives
- Detect scam or fraudulent messages
- Activate an autonomous AI agent after scam detection
- Maintain believable, human-like conversation flow
- Support multi-turn conversations using memory
- Extract scam intelligence incrementally
- Return structured JSON responses for evaluation

---

## ✨ Features
- ✅ Scam intent detection with confidence scoring
- ✅ Autonomous agentic engagement (multi-turn)
- ✅ Human-like adaptive responses
- ✅ Incremental intelligence extraction:
  - Bank account numbers
  - UPI IDs
  - Phishing URLs
- ✅ Engagement metrics (turns & duration)
- ✅ API key–secured REST endpoint
- ✅ Public deployment for evaluation

---

## 🧠 Agent Behavior
- Adapts responses dynamically based on conversation context
- Avoids revealing scam detection
- Performs self-correction where required
- Does not hallucinate intelligence
- Extracts only information explicitly provided by the scammer

---

## 🔌 API Details

### Base URL
https://agentic-honeypot-2pn5.onrender.com
### Required Headers
x-api-key: my-secret-key-123
Content-Type: application/json


---

## 📥 Sample Request
```json
{
  "conversation_id": "demo-session",
  "message": "Your bank account is suspended. Send money to helpdesk@upi or visit https://secure-bank-login.com"
}
📤 Sample Response
{
  "scam_detected": true,
  "agent_reply": "Hello, I just received this message. Can you explain what happened?",
  "engagement_metrics": {
    "turns": 1,
    "engagement_duration_seconds": 0
  },
  "extracted_intelligence": {
    "upi_ids": ["helpdesk@upi"],
    "phishing_urls": ["https://secure-bank-login.com"]
  }
}

🔄 Multi-Turn Support
The system supports ongoing conversations using a shared conversation_id.
Engagement metrics and extracted intelligence are updated incrementally as the conversation progresses.

🛡️ Security
API access is secured using a required API key

Unauthorized requests are rejected

Designed for stable and low-latency responses

⚖️ Ethical Considerations
No impersonation of real individuals

No harassment or illegal instructions

No hallucinated or fabricated intelligence

Responsible handling of extracted data

🛠️ Tech Stack
Language: Python 3

Framework: FastAPI

Server: Uvicorn

Deployment: Render (Public API)

👥 Team
This is a group project submission for the Agentic Honey-Pot for Scam Detection & Intelligence Extraction challenge.

