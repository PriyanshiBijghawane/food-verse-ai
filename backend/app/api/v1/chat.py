from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.entities import User, ChatSession, ChatMessage
from app.schemas.dtos import ChatMessageIn, ChatMessageOut, AudioTranscribeResponse
from app.api.deps import get_current_user
from app.providers.factory import get_ai_provider

router = APIRouter(tags=["chat"])

@router.post("/chat", response_model=ChatMessageOut)
async def chat_cooking_assistant(
    req: ChatMessageIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    session = None
    if req.session_id:
        session = db.query(ChatSession).filter(ChatSession.id == req.session_id).first()

    if not session:
        session = ChatSession(user_id=current_user.id, title="Smart Culinary Chat")
        db.add(session)
        db.commit()
        db.refresh(session)

    # Save user message
    user_msg = ChatMessage(
        session_id=session.id,
        role="user",
        content=req.message,
    )
    db.add(user_msg)
    db.commit()

    # Generate culinary response
    user_prompt = req.message.lower()
    if "substitut" in user_prompt or "swap" in user_prompt:
        reply = (
            "For baking substitutions: 1 egg can be swapped with 1/4 cup unsweetened applesauce or 1 tbsp chia seeds + 3 tbsp water. "
            "For dairy milk: Oat milk provides a neutral flavor and similar viscosity. "
            "Always inspect for individual allergies before serving."
        )
    elif "temp" in user_prompt or "cook" in user_prompt:
        reply = (
            "Safe internal cooking temperatures (verified by USDA): "
            "Poultry (chicken/turkey): 74°C (165°F). "
            "Ground meats: 71°C (160°F). "
            "Whole cuts of beef, pork, and lamb: 63°C (145°F) with a 3-minute rest. "
            "Fish & shellfish: 63°C (145°F) until flesh is opaque and flakes easily."
        )
    elif "timer" in user_prompt:
        reply = (
            "I have noted your timer request! Use the interactive cooking timers in each step of your generated recipes to track prep and cook cycles accurately."
        )
    else:
        reply = (
            f"I am your culinary cooking assistant. I can help you adapt recipes, check ingredient substitutions, "
            f"and identify allergens in your dishes. You asked: '{req.message}'. Would you like me to generate a tailored recipe or suggest substitutions for specific ingredients?"
        )

    assistant_msg = ChatMessage(
        session_id=session.id,
        role="assistant",
        content=reply,
    )
    db.add(assistant_msg)
    db.commit()
    db.refresh(assistant_msg)

    return ChatMessageOut(
        id=assistant_msg.id,
        session_id=session.id,
        role=assistant_msg.role,
        content=assistant_msg.content,
        audio_transcribed=assistant_msg.audio_transcribed,
        created_at=assistant_msg.created_at,
    )

@router.post("/audio/transcribe", response_model=AudioTranscribeResponse)
async def transcribe_audio(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    audio_bytes = await file.read()
    if not audio_bytes or len(audio_bytes) < 100:
        return AudioTranscribeResponse(
            transcript="",
            confidence=0.0,
            audio_duration_seconds=0.0,
            fallback_note="No audio input detected or recording was too short. You can type your request directly."
        )

    provider = get_ai_provider()
    try:
        res = await provider.transcribe_audio(audio_bytes)
        return AudioTranscribeResponse(
            transcript=res.get("transcript", ""),
            confidence=res.get("confidence", 0.95),
            audio_duration_seconds=res.get("audio_duration_seconds", 3.0),
            fallback_note=res.get("fallback_note"),
        )
    except Exception as exc:
        return AudioTranscribeResponse(
            transcript="",
            confidence=0.0,
            audio_duration_seconds=0.0,
            fallback_note=f"Audio transcription provider unavailable ({exc}). Full text input is available."
        )
