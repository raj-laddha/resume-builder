from fastapi import UploadFile, HTTPException
from datetime import datetime
from ..helpers.parser import DocumentParser
from ..managers.session_manager import session_manager
from ..helpers.response_utils import create_session_response

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB in bytes

def handle_file_upload(file: UploadFile, session_id: str = None):
    allowed_types = [".pdf", ".docx", ".txt"]
    file_ext = file.filename.lower().split(".")[-1]
    if f".{file_ext}" not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Please upload one of: {', '.join(allowed_types)}"
        )
    # Read file content
    file_content = file.file.read()
    if len(file_content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE/1024/1024}MB"
        )
    # Parse the file
    parser = DocumentParser()
    text_content = parser.parse_file(file_content, file_ext)
    if text_content is None:
        raise HTTPException(
            status_code=500,
            detail="Failed to parse file content"
        )
    
    # Validate parsed content
    if not text_content or not text_content.strip():
        raise HTTPException(
            status_code=400,
            detail="Uploaded file contains no readable text content"
        )
    
    # Create or get session
    if not session_id or not session_manager.is_valid_session(session_id):
        session_id = session_manager.create_session()
    # Store parsed data
    user_profile = {
        "filename": file.filename,
        "content_type": file.content_type,
        "size": len(file_content),
        "content": text_content,
        "parsed_at": datetime.utcnow().isoformat()
    }
    if not session_manager.update_user_profile(session_id, user_profile):
        raise HTTPException(
            status_code=500,
            detail="Failed to store resume data"
        )
    return create_session_response(
        session_id=session_id,
        message="File uploaded and parsed successfully"
    ) 