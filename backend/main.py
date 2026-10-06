"""
FastAPI Backend for Socratic Math Tutor.
Provides API endpoints for multi-turn Socratic tutoring and session management.
"""

import uuid
from typing import Optional, Dict
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from backend.socratic_engine import SocraticTutor

app = FastAPI(
    title="Socratic Math Tutor API",
    description="Thin API layer connecting frontend interactions to the Socratic tutoring engine.",
    version="1.0.0",
)

# Enable CORS for local web frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory session store mapping session_id -> SocraticTutor instance
sessions: Dict[str, SocraticTutor] = {}


class ChatRequest(BaseModel):
    message: str = Field(..., description="Student's message or reasoning")
    session_id: Optional[str] = Field(None, description="Optional session identifier")


class ChatResponse(BaseModel):
    response: str
    misconception: Optional[str] = None
    status: str
    session_id: str


class ResetRequest(BaseModel):
    session_id: Optional[str] = Field(None, description="Optional session identifier to reset")


class ResetResponse(BaseModel):
    status: str
    message: str
    session_id: str


def get_or_create_session(session_id: Optional[str] = None) -> tuple[str, SocraticTutor]:
    """Retrieves an existing tutor session or creates a new one."""
    if session_id and session_id in sessions:
        return session_id, sessions[session_id]

    active_id = session_id.strip() if (session_id and session_id.strip()) else str(uuid.uuid4())
    try:
        tutor = SocraticTutor()
    except ValueError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Configuration error: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initialize tutoring session: {str(e)}",
        )

    sessions[active_id] = tutor
    return active_id, tutor


@app.get("/health")
def health():
    """Health check endpoint to verify backend status."""
    return {"status": "ok", "active_sessions": len(sessions)}


@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """
    Receives student reasoning, forwards it to the SocraticTutor session,
    and returns the structured response with misconception diagnostics.
    """
    stripped_message = request.message.strip()
    if not stripped_message:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    session_id, tutor = get_or_create_session(request.session_id)

    try:
        result = tutor.send_message(stripped_message)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Socratic engine error: {str(e)}",
        )

    # Return null in JSON if no misconception was detected
    misconception = result.get("misconception")
    if misconception in ("None", "", None):
        misconception = None

    return ChatResponse(
        response=result.get("response", ""),
        misconception=misconception,
        status=result.get("status", "IN_PROGRESS"),
        session_id=session_id,
    )


@app.post("/api/chat/image", response_model=ChatResponse)
async def chat_image(
    image: UploadFile = File(..., description="Handwritten math image"),
    message: Optional[str] = Form("", description="Optional student text message"),
    session_id: Optional[str] = Form(None, description="Optional session identifier"),
):
    """
    Receives handwritten math image and optional student message,
    forwards to SocraticTutor session, and returns the structured response.
    """
    allowed_types = {"image/jpeg", "image/png", "image/webp", "image/gif"}
    content_type = image.content_type or ""
    if content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported image type: '{content_type}'. Supported: JPEG, PNG, WEBP, GIF.",
        )

    image_bytes = await image.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Uploaded image file is empty.")

    active_session_id, tutor = get_or_create_session(session_id)

    student_text = (message or "").strip()

    try:
        result = tutor.send_message_with_image(
            image_bytes=image_bytes,
            mime_type=content_type,
            text=student_text,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Socratic engine error: {str(e)}",
        )

    misconception = result.get("misconception")
    if misconception in ("None", "", None):
        misconception = None

    return ChatResponse(
        response=result.get("response", ""),
        misconception=misconception,
        status=result.get("status", "IN_PROGRESS"),
        session_id=active_session_id,
    )


@app.post("/api/reset", response_model=ResetResponse)
def reset(request: Optional[ResetRequest] = None):
    """
    Resets the conversation for the specified session.
    """
    req_session_id = request.session_id.strip() if (request and request.session_id) else None

    if req_session_id and req_session_id in sessions:
        sessions[req_session_id].reset()
        active_id = req_session_id
    else:
        active_id, _ = get_or_create_session(req_session_id)

    return ResetResponse(
        status="ok",
        message="Session reset successfully.",
        session_id=active_id,
    )


# Serve the frontend — mount AFTER all API routes so /api/* takes priority
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
