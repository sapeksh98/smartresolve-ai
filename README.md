⚡ SmartResolve AI
A multi-agent RAG system for automated customer support ticket resolution. Five specialized AI agents work in a pipeline to classify, retrieve policy, generate resolutions, assess risk, and draft customer replies — all grounded in company policy documents.

🏗️ Architecture
Customer Complaint
       │
       ▼
┌─────────────────┐
│  Agent 1        │  classify_ticket()       → category, priority, summary
│  Classifier     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Agent 2        │  get_relevant_policy()   → RAG retrieval from FAISS
│  Policy RAG     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Agent 3        │  generate_resolution()   → policy-grounded resolution
│  Resolution     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Agent 4        │  check_risk()            → risk level, score, escalation
│  Risk Assessor  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Agent 5        │  write_customer_reply()  → polished email draft
│  Reply Writer   │
└────────┬────────┘
         │
         ▼
  Human Approval → Send / Edit / Escalate
Tech Stack:

Backend: FastAPI + Uvicorn
LLM: Groq API (llama-3.1-8b-instant)
RAG: FAISS + SentenceTransformers (all-MiniLM-L6-v2)
Database: SQLite
Frontend: Vanilla HTML/CSS/JS


🚀 Local Setup
1. Clone the repo
bashgit clone https://github.com/yourusername/smartresolve-ai.git
cd smartresolve-ai
2. Create virtual environment
bashpython -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows
3. Install dependencies
bashpip install -r requirements.txt
4. Set up environment variables
bashcp .env.example .env
# Edit .env and add your GROQ_API_KEY and ADMIN_PASSWORD
Get a free Groq API key at: https://console.groq.com
5. Add your company policies
Place your policy document at:
data/company_policies.txt
The FAISS index will be built automatically on first run.
6. Run the server
bashuvicorn main:app --reload
Open http://localhost:8000 in your browser.


📁 Project Structure
smartresolve-ai/
├── main.py                      # FastAPI app, routes, pipeline orchestration
├── requirements.txt
├── render.yaml                  # Render deployment config
├── .env.example
│
├── agents/
│   ├── classifier_agent.py      # Agent 1 — ticket classification
│   ├── rag_agent.py             # Agent 2 — policy retrieval
│   ├── resolution_agent.py      # Agent 3 — resolution generation
│   ├── risk_agent.py            # Agent 4 — risk assessment
│   └── response_writer_agent.py # Agent 5 — customer reply
│
├── utils/
│   ├── llm.py                   # Groq LLM wrapper
│   ├── rag_engine.py            # FAISS retriever
│   └── database.py              # SQLite operations
│
├── static/
│   ├── index.html               # Customer-facing UI
│   └── admin.html               # Admin dashboard
│
└── data/
    └── company_policies.txt     # RAG knowledge base (add your own)

🔌 API Endpoints
MethodEndpointAuthDescriptionGET/—Customer UIPOST/resolve—Run full agent pipelineGET/tickets—List all ticketsGET/analytics—Aggregated statsGET/admin✅ BasicAdmin dashboardGET/admin/data✅ BasicTickets + analytics JSONPOST/rebuild-index✅ BasicRebuild FAISS index
POST /resolve — Example
Request:
json{
  "complaint": "I was charged twice for my subscription this month."
}
Response:
json{
  "category": "BILLING",
  "priority": "HIGH",
  "summary": "Customer reports duplicate charge on subscription.",
  "relevant_policy": "• Duplicate charges are refunded within 3 business days...",
  "resolution": "RESOLUTION: Issue a full refund for the duplicate charge...",
  "risk_level": "MEDIUM",
  "risk_score": 45,
  "risk_reason": "Duplicate charge confirmed by policy.",
  "recommendation": "Process refund and send confirmation.",
  "should_escalate": false,
  "customer_reply": "Dear Customer, we sincerely apologize...",
  "latency_ms": 4200
}

🛡️ Admin Panel
Navigate to /admin and enter your ADMIN_PASSWORD.
Features:

📊 Dashboard with live stats (total tickets, high risk, escalations, avg latency)
🎫 All tickets table with category, priority, risk, escalation status
🚨 Escalated tickets view with risk reasons and recommendations
📈 Analytics charts (category distribution, risk distribution, latency by category, priority breakdown)
Auto-refreshes every 30 seconds


☁️ Deploying to Render

Push your repo to GitHub
Go to render.com → New Web Service
Connect your GitHub repo
Render auto-detects render.yaml — confirm the settings
Add environment variables in the Render dashboard:

GROQ_API_KEY
ADMIN_PASSWORD


Deploy — first build takes ~3-5 minutes due to faiss-cpu compilation


Note: The persistent disk keeps your SQLite database and FAISS index alive across restarts. First request after a cold start may take 20-30 seconds while the embedding model loads.


🔑 Environment Variables
VariableRequiredDefaultDescriptionGROQ_API_KEY✅—Groq API keyADMIN_PASSWORD✅admin123Admin panel password

📄 License
MIT License — feel free to use and modify for your own projects.