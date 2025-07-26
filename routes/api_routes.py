from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
import uuid
import logging
from datetime import datetime
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from services.gemini_service import GeminiService  # Your Gemini service
from agents.audio_agent import AudioAgent        # Your AudioAgent class
from services.transcription_service import transcribe_audio

# Service and Agent Imports (Implicitly used via injected agents)
from services.auth_service import AuthService

# Import the RAG processing function from your main module
from services.rag_service import RAGService


RagService = RAGService()

# Schema Imports (All schemas are needed here)
from schemas.request_schemas import (
    LoginRequest,
    SignupRequest,
    VisualRequest,
    AudioRequest,
    AskLearnRequest,
    PlanWeekRequest,
    FeedbackRequest
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic models for request/response (New chat functionality)
class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=1000, description="The user's question")
    grade: int = Field(..., ge=1, le=12, description="Grade level (1-12)")
    user_id: str = Field(..., min_length=1, description="User ID for conversation memory")
    
    @validator('question')
    def validate_question(cls, v):
        if not v.strip():
            raise ValueError('Question cannot be empty or just whitespace')
        return v.strip()
    
    @validator('user_id')
    def validate_user_id(cls, v):
        if not v.strip():
            raise ValueError('User ID cannot be empty')
        return v.strip()

class ChatResponse(BaseModel):
    response: str = Field(..., description="The chatbot's response")

def generate_user_id() -> str:
    """Generate a unique user ID."""
    return f"user_{uuid.uuid4().hex[:12]}"

def setup_api_routes(
    # This function now accepts all required agents
    auth_service: AuthService,
    textbook_agent,
    visual_agent,
    audio_agent,
    grade_agent,
    lesson_planner_agent,
    feedback_agent
):
    # --- AUTHENTICATION ROUTES ---

    @router.post("/signup")
    async def register_user(request: SignupRequest):
        user = auth_service.create_user(
            email=request.email,
            password=request.password,
            name=request.name,
            school=request.school
        )
        if not user:
            raise HTTPException(
                status_code=400,
                detail="Email is already registered."
            )
        # On successful registration, return the new user's details
        return {"user_details": user}

    @router.post("/login")
    async def login_for_access_token(request: LoginRequest):
        user = auth_service.authenticate_user(email=request.email, password=request.password)
        if not user:
            raise HTTPException(
                status_code=401,
                detail="Incorrect email or password.",
            )
        return {"user_details": user}

    # --- FUNCTIONAL AI ROUTES ---

    @router.post("/practice")
    async def handle_practice_page(difficulty: str = Form(...), image: UploadFile = File(...)):
        if not image.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="Invalid file type. Please upload an image.")
        image_bytes = await image.read()
        response_text = textbook_agent.generate_practice_material(image_bytes, difficulty)
        return JSONResponse(content={"response": response_text})

    @router.post("/visual-learning")
    async def handle_visual_learning(request: VisualRequest):
        svg_content = visual_agent.generate_visual(request.description)
        return JSONResponse(content={"svg": svg_content})

    # main.py
    
    def get_gemini_service():
        
        return GeminiService()

    def get_audio_agent(gemini_service: GeminiService = Depends(get_gemini_service)):
        """Provides an AudioAgent instance, which depends on the GeminiService."""
        return AudioAgent(gemini_service)

# --- API Endpoint Definition ---
    @router.post("/agents/audio_agent")
    async def handle_audio_query(
        audio: UploadFile = File(...),
        agent: AudioAgent = Depends(get_audio_agent)
    ):
        audio_bytes = await audio.read()
        
        # 1. Get the transcribed text (simple string)
        transcribed_text = transcribe_audio(audio_bytes)

        if not transcribed_text:
            raise HTTPException(status_code=400, detail="Could not understand audio.")
        
        # 2. Process it with the agent (which handles language detection)
        llm_response = agent.process_audio_query(transcribed_text)
        
        # 3. Return the final response
        return {
            "success": True,
            "response": {
                "transcript": transcribed_text,
                "response": llm_response
            }
        }

    @router.post("/ask-learn")
    async def handle_ask_learn(request: AskLearnRequest):
        response_text = grade_agent.answer_question(request.question, request.grade, request.difficulty)
        return JSONResponse(content={"response": response_text})

    @router.post("/plan-week")
    async def handle_plan_week(request: PlanWeekRequest):
        response_text = lesson_planner_agent.create_plan(request.grade, request.subject, request.chapter)
        return JSONResponse(content={"response": response_text})

    @router.post("/feedback")
    async def handle_feedback(request: FeedbackRequest):
        success = feedback_agent.submit_feedback(request.feedback_text)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to save feedback.")
        return JSONResponse(content={"message": "Feedback submitted successfully!"})

    # --- NEW RAG CHAT ROUTE ---
    
    @router.post("/chat")
    async def chat_endpoint(request: ChatRequest) -> ChatResponse:
        """
        Chat endpoint for the RAG chatbot.
        
        Args:
            request: ChatRequest containing question, grade, and user_id
            
        Returns:
            ChatResponse with the bot's answer
        """
        try:
            logger.info(f"Processing chat request for user {request.user_id}, grade {request.grade}")
            logger.info(f"Question: {request.question[:100]}...")  # Log first 100 chars
            
            # Process the RAG query with the provided user_id
            bot_response = await RagService.process_educational_query(
                user_question=request.question,
                user_id=request.user_id,
                grade=request.grade
            )
            
            # Check if the response indicates an error
            if bot_response.startswith("❌ Error:"):
                raise HTTPException(
                    status_code=500,
                    detail=f"RAG processing error: {bot_response}"
                )
            
            logger.info("Successfully processed request")
            
            return ChatResponse(response=bot_response)
            
        except HTTPException:
            # Re-raise HTTP exceptions
            raise
        except ValueError as e:
            logger.error(f"Validation error: {str(e)}")
            raise HTTPException(
                status_code=422,
                detail=f"Validation error: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Internal server error - please try again later"
            )

    # Return the single, fully configured router
    return router