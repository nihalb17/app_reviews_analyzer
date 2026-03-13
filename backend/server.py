import os
import sys
import json
import uuid
import datetime
import threading
from fastapi import FastAPI, BackgroundTasks, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Optional
from fastapi.staticfiles import StaticFiles
from pathlib import Path

# IST timezone offset (UTC+5:30)
IST_OFFSET = datetime.timedelta(hours=5, minutes=30)

def get_ist_datetime() -> datetime.datetime:
    """Get current datetime in IST timezone"""
    return datetime.datetime.now(datetime.timezone.utc) + IST_OFFSET

def format_ist_datetime(dt: datetime.datetime = None) -> str:
    """Format datetime as DD-MM-YYYY HH:MM in IST"""
    if dt is None:
        dt = get_ist_datetime()
    return dt.strftime("%d-%m-%Y %H:%M")

# Load .env file if exists
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ.setdefault(key, value)

# Add parent directory to path to import root coordinator
sys.path.insert(0, str(Path(__file__).parent.parent))
import coordinator

# Security setup
security = HTTPBearer(auto_error=False)
API_TOKEN = os.getenv("API_TOKEN", "your-secure-api-token-change-in-production")

app = FastAPI()

# Mount Static Files (Frontend UI)
BASE_DIR = Path(__file__).parent.parent.resolve()
UI_DIR = BASE_DIR / "frontend"
# Mount css and js folders individually for relative path support
app.mount("/css", StaticFiles(directory=str(UI_DIR / "css")), name="css")
app.mount("/js", StaticFiles(directory=str(UI_DIR / "js")), name="js")

# Mount Reports (Phase 4 Output)
REPORTS_DIR = BASE_DIR / "backend" / "Phase_4_Report_Generation" / "output"
if not REPORTS_DIR.exists():
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/reports", StaticFiles(directory=str(REPORTS_DIR)), name="reports")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

HISTORY_FILE = coordinator.HISTORY_FILE

class TriggerRequest(BaseModel):
    reviews_count: int
    weeks: int
    role: str
    recipient_name: Optional[str] = None
    recipient_email: Optional[str] = None
    mode: str  # 'email' or 'preview'
    type: Optional[str] = "Manual"  # 'Manual' or 'Scheduler'


class ScheduledTriggerRequest(BaseModel):
    weeks: int
    reviews_count: int
    role: str
    recipient_name: str
    recipient_email: str
    mode: str = "email"
    type: str = "Scheduler"


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify the Bearer token for GitHub Actions requests"""
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Authorization header missing",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    expected_token = os.getenv("API_TOKEN")
    if not expected_token:
        raise HTTPException(
            status_code=500,
            detail="API_TOKEN not configured on server"
        )
    
    if credentials.credentials != expected_token:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return credentials.credentials

@app.get("/api/history")
async def get_history():
    if not HISTORY_FILE.exists():
        return []
    with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

@app.post("/api/trigger")
async def trigger_analysis(req: TriggerRequest, background_tasks: BackgroundTasks):
    trigger_id = str(uuid.uuid4())
    
    new_entry = {
        "id": trigger_id,
        "date": format_ist_datetime(),
        "timestamp": str(get_ist_datetime()),
        "reviews": req.reviews_count,
        "weeks": req.weeks,
        "period": f"Last {req.weeks} Week{'s' if req.weeks > 1 else ''}",
        "role": req.role,
        "receiverName": req.recipient_name,
        "recipient_email": req.recipient_email,
        "status": "Started",
        "mode": req.mode,
        "type": req.type
    }
    
    # Only save 'email' mode to history as requested
    if req.mode == "email":
        history = []
        if HISTORY_FILE.exists():
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                history = json.load(f)
        history.insert(0, new_entry)
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=4)
            
    background_tasks.add_task(
        coordinator.run_full_pipeline,
        trigger_id, req.reviews_count, req.weeks, req.role, 
        req.recipient_name, req.recipient_email, req.mode
    )
    
    return {"status": "accepted", "id": trigger_id}


@app.post("/api/triggers/scheduled")
async def scheduled_trigger(
    req: ScheduledTriggerRequest, 
    background_tasks: BackgroundTasks,
    token: str = Depends(verify_token)
):
    """
    Endpoint for GitHub Actions to trigger scheduled reports.
    Requires Bearer token authentication.
    """
    trigger_id = str(uuid.uuid4())
    
    new_entry = {
        "id": trigger_id,
        "date": format_ist_datetime(),
        "timestamp": str(get_ist_datetime()),
        "reviews": req.reviews_count,
        "weeks": req.weeks,
        "period": f"Last {req.weeks} Week{'s' if req.weeks > 1 else ''}",
        "role": req.role,
        "receiverName": req.recipient_name,
        "recipient_email": req.recipient_email,
        "status": "Started",
        "mode": req.mode,
        "type": req.type
    }
    
    # Save to history
    history = []
    if HISTORY_FILE.exists():
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            history = json.load(f)
    history.insert(0, new_entry)
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=4)
    
    # Start the pipeline in background
    background_tasks.add_task(
        coordinator.run_full_pipeline,
        trigger_id, req.reviews_count, req.weeks, req.role, 
        req.recipient_name, req.recipient_email, req.mode
    )
    
    return {
        "status": "accepted", 
        "id": trigger_id,
        "message": "Scheduled report generation started",
        "config": {
            "weeks": req.weeks,
            "reviews_count": req.reviews_count,
            "role": req.role,
            "recipient_name": req.recipient_name,
            "recipient_email": req.recipient_email
        }
    }

@app.get("/api/view-pdf/{trigger_id}")
async def view_pdf(trigger_id: str):
    if not HISTORY_FILE.exists():
        raise HTTPException(status_code=404, detail="History not found")
        
    with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
        history = json.load(f)
        
    entry = next((e for e in history if e['id'] == trigger_id), None)
    if not entry:
        raise HTTPException(status_code=404, detail="Trigger not found")
    
    role = entry['role']
    safe_role = role.lower().replace('/', '_')
    pdf_filename = f"groww_insights_{safe_role}.pdf"
    pdf_path = REPORTS_DIR / pdf_filename
    
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail=f"PDF not found at {pdf_path}. Wait for processing to complete.")
        
    from fastapi.responses import FileResponse
    return FileResponse(pdf_path, media_type='application/pdf', filename=pdf_filename)

@app.post("/api/actions/view-pdf/{trigger_id}")
async def rerun_for_view(trigger_id: str, background_tasks: BackgroundTasks):
    # This usually means rerun phases 1-4
    # For now, we find the entry
    if not HISTORY_FILE.exists():
        raise HTTPException(status_code=404, detail="History not found")
        
    with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
        history = json.load(f)
        
    entry = next((e for e in history if e['id'] == trigger_id), None)
    if not entry:
        raise HTTPException(status_code=404, detail="Trigger not found")
        
    background_tasks.add_task(
        coordinator.run_full_pipeline,
        trigger_id, entry['reviews'], entry['weeks'], entry['role'], 
        entry['receiverName'], entry['recipient_email'], mode="preview"
    )
    return {"status": "rerunning"}

@app.post("/api/actions/send-mail/{trigger_id}")
async def send_mail_action(trigger_id: str, background_tasks: BackgroundTasks):
    if not HISTORY_FILE.exists():
        raise HTTPException(status_code=404, detail="History not found")
        
    with open(HISTORY_FILE, 'r') as f:
        history = json.load(f)
        
    entry = next((e for e in history if e['id'] == trigger_id), None)
    if not entry:
        raise HTTPException(status_code=404, detail="Trigger not found")
        
    background_tasks.add_task(
        coordinator.run_full_pipeline,
        trigger_id, entry['reviews'], entry['weeks'], entry['role'], 
        entry['receiverName'], entry['recipient_email'], mode="email"
    )
    return {"status": "rerunning"}

@app.delete("/api/history/{trigger_id}")
async def delete_history_item(trigger_id: str):
    """Delete a trigger from history"""
    if not HISTORY_FILE.exists():
        raise HTTPException(status_code=404, detail="History not found")
        
    with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
        history = json.load(f)
    
    # Find and remove the entry
    original_length = len(history)
    history = [e for e in history if e['id'] != trigger_id]
    
    if len(history) == original_length:
        raise HTTPException(status_code=404, detail="Trigger not found")
    
    # Save updated history
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=4)
    
    return {"status": "deleted", "id": trigger_id}

@app.post("/api/actions/retry/{trigger_id}")
async def retry_trigger(trigger_id: str, background_tasks: BackgroundTasks):
    """Retry a failed trigger - resumes from previous successful phase"""
    if not HISTORY_FILE.exists():
        raise HTTPException(status_code=404, detail="History not found")
        
    with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
        history = json.load(f)
        
    entry = next((e for e in history if e['id'] == trigger_id), None)
    if not entry:
        raise HTTPException(status_code=404, detail="Trigger not found")
    
    # Get current status to determine where to resume from
    current_status = entry.get('status', 'Started')
    
    # Extract the base status (remove "(Failed)" suffix if present)
    resume_from = current_status.replace('(Failed)', '')
    
    # Reset status to Started for retry
    entry['status'] = 'Started'
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=4)
        
    background_tasks.add_task(
        coordinator.run_full_pipeline,
        trigger_id, entry['reviews'], entry['weeks'], entry['role'], 
        entry['receiverName'], entry['recipient_email'], mode="email",
        resume_from=resume_from
    )
    return {"status": "retrying", "id": trigger_id, "resume_from": resume_from}

# Map index.html to root (must be after API routes)
@app.get("/")
async def read_index():
    from fastapi.responses import FileResponse
    return FileResponse(UI_DIR / "index.html")

# Also serve index.html for any unmatched routes (SPA support) - must be last
@app.get("/{path:path}")
async def read_index_spa(path: str):
    from fastapi.responses import FileResponse
    # If it's an API route, let it 404 naturally
    if path.startswith("api/"):
        raise HTTPException(status_code=404, detail="Not found")
    return FileResponse(UI_DIR / "index.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
