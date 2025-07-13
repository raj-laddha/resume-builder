from fastapi import FastAPI, WebSocket, UploadFile, HTTPException, File, Cookie, WebSocketDisconnect, WebSocketException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from dotenv import load_dotenv
from .managers.session_manager import session_manager
from .models.schemas import JobDescription
from .services.user_profile_service import handle_file_upload
from .services.job_description_service import handle_job_description
from .helpers.logger import get_logger
logger = get_logger(__name__)

# Load environment variables
load_dotenv()

# Constants
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB in bytes
SESSION_COOKIE_MAX_AGE = int(os.getenv('SESSION_COOKIE_MAX_AGE', 1800))  # 30 minutes default

app = FastAPI(title="Agentic Resume Builder")

# Configure CORS
frontend_url = os.getenv('FRONTEND_URL', '*')
allowed_origins = [frontend_url] if frontend_url != '*' else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files (except index.html) at /static
app.mount("/static", StaticFiles(directory="frontend"), name="frontend")

# Serve index.html at root
@app.get("/")
async def read_index():
    return FileResponse("frontend/index.html")

@app.get("/api/ping")
async def ping():
    return {"ok": True}

@app.get("/api/session/validate")
async def validate_session(session_id: str = Cookie(None)):
    """Validate if a session exists and is valid."""
    if not session_id:
        return {"valid": False, "message": "No session ID provided"}
    
    session = session_manager.get_session(session_id=session_id)
    if not session:
        return {"valid": False, "message": "Session not found"}
    
    return {"valid": True, "session_id": session_id}

def check_session_id(session_id: str):
    """Middleware/dependency to check if session_id is valid for WebSocket."""
    if not session_id or not session_manager.is_valid_session(session_id):
        raise WebSocketException(
            code=status.WS_1008_POLICY_VIOLATION,
            reason="Invalid or missing session_id"
        )

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """Websocket endpoint"""
    check_session_id(session_id)  # Validate session before accepting
    await websocket.accept()
    
    session_manager.update_websocket(session_id=session_id, websocket=websocket)
    
    try:
        while True:
            # Receive message
            message = await websocket.receive_json()
            
            # Process message
            ws_handler = session_manager.get_websocket_handler(session_id=session_id)
            await ws_handler.handle_message(message=message)
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket client disconnected for session_id: {session_id}")
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "message": f"Unexpected error: {str(e)}"
        })

@app.post("/api/user-profile/upload")
async def upload_file(file: UploadFile = File(...), session_id: str = Cookie(None)):
    try:
        # Delegate to service function
        return handle_file_upload(file, session_id)
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")  # Debug log
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/job-description")
async def submit_job_description(job_description: JobDescription, session_id: str = Cookie(None)):
    try:
        # Delegate to service function
        return handle_job_description(job_description, session_id)
    except Exception as e:
        logger.error(f"Job description error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 