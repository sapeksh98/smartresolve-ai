import os
os.makedirs("data", exist_ok=True)
os.makedirs("static", exist_ok=True)
os.makedirs("data/model_cache", exist_ok=True)

from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from agents.classifier_agent import classify_ticket
from agents.rag_agent import get_relevant_policy
from agents.resolution_agent import generate_resolution
from agents.risk_agent import check_risk
from agents.response_writer_agent import write_customer_reply
from utils.database import init_db, save_ticket, get_all_tickets, get_analytics, save_policy_upload, get_policy_uploads
from utils.rag_engine import retriever
import time, secrets, shutil

init_db()

app = FastAPI(title="SmartResolve AI", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True
)

# ✅ Load model AFTER server starts
@app.on_event("startup")
async def startup_event():
    print("[Startup] Initializing RAG engine...")
    retriever.initialize()
    print("[Startup] Ready!")

app.mount("/static", StaticFiles(directory="static"), name="static")
security = HTTPBasic()

def verify_admin(credentials: HTTPBasicCredentials = Depends(security)):
    correct_password = os.getenv("ADMIN_PASSWORD", "admin123")
    is_correct = secrets.compare_digest(
        credentials.password.encode("utf8"),
        correct_password.encode("utf8")
    )
    if not is_correct:
        raise HTTPException(
            status_code=401,
            detail="Wrong password",
            headers={"WWW-Authenticate": "Basic"}
        )
    return credentials.username


@app.get("/")
def serve_ui():
    return FileResponse("static/index.html")

@app.get("/admin")
def serve_admin(username: str = Depends(verify_admin)):
    return FileResponse("static/admin.html")

@app.get("/admin/data")
def admin_data(username: str = Depends(verify_admin)):
    return {
        "analytics": get_analytics(),
        "tickets": get_all_tickets(),
        "policy_uploads": get_policy_uploads()
    }

@app.post("/admin/upload-policy")
async def upload_policy(
    file: UploadFile = File(...),
    username: str = Depends(verify_admin)
):
    allowed = [".txt", ".pdf"]
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed:
        raise HTTPException(status_code=400, detail="Only .txt and .pdf files allowed")

    os.makedirs("data", exist_ok=True)
    upload_path = f"data/uploaded_policy{ext}"
    with open(upload_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    if ext == ".pdf":
        try:
            import pypdf
            reader = pypdf.PdfReader(upload_path)
            text = "\n\n".join([
                page.extract_text()
                for page in reader.pages
                if page.extract_text()
            ])
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"PDF read error: {str(e)}")
    else:
        with open(upload_path, "r", encoding="utf-8") as f:
            text = f.read()

    if not text.strip():
        raise HTTPException(status_code=400, detail="File appears to be empty")

    with open("data/company_policies.txt", "w", encoding="utf-8") as f:
        f.write(text)

    retriever.rebuild()
    chunks = len(retriever.chunks)
    save_policy_upload(file.filename, chunks)

    return {
        "message": "Policy uploaded and index rebuilt successfully!",
        "filename": file.filename,
        "chunks": chunks
    }

@app.post("/rebuild-index")
def rebuild_index(username: str = Depends(verify_admin)):
    retriever.rebuild()
    return {"message": "FAISS index rebuilt!", "chunks": len(retriever.chunks)}

class ComplaintRequest(BaseModel):
    complaint: str

@app.post("/resolve")
def resolve_complaint(request: ComplaintRequest):
    start = time.time()
    complaint = request.complaint
    classified = classify_ticket(complaint)
    policy = get_relevant_policy(classified["category"], complaint)
    resolution = generate_resolution(classified["category"], complaint, policy)
    risk = check_risk(classified["category"], complaint, classified["priority"])
    reply = write_customer_reply(complaint, resolution, risk)
    latency_ms = int((time.time() - start) * 1000)
    result = {
        "complaint": complaint,
        "category": classified["category"],
        "priority": classified["priority"],
        "summary": classified["summary"],
        "confidence": classified.get("confidence", 0.9),
        "relevant_policy": policy,
        "resolution": resolution,
        "risk_level": risk.get("risk_level", "MEDIUM"),
        "risk_score": risk.get("risk_score", 0),
        "risk_reason": risk.get("risk_reason", ""),
        "recommendation": risk.get("recommendation", ""),
        "should_escalate": risk.get("should_escalate", False),
        "customer_reply": reply,
        "latency_ms": latency_ms
    }
    save_ticket(result, latency_ms)
    return result

@app.get("/tickets")
def get_tickets():
    return get_all_tickets()

@app.get("/analytics")
def analytics():
    return get_analytics()