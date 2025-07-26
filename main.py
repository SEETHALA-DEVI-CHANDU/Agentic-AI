# main.py

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import logging

# --- Service and Agent Imports ---
from services.firebase_service import FirebaseService
from services.gemini_service import GeminiService
from services.rag_service import RAGService
from services.auth_service import AuthService

from agents.textbook_agent import TextbookAgent
from agents.visual_agent import VisualAgent
from agents.audio_agent import AudioAgent
from agents.grade_agent import GradeAgent
from agents.lesson_planner_agent import LessonPlannerAgent
from agents.feedback_agent import FeedbackAgent

# --- Route Imports ---
from routes.api_routes import setup_api_routes, router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create the FastAPI app instance
app = FastAPI(
    title="Sahayak AI API",
    description="Backend services for the Sahayak AI educational platform with RAG Educational Chatbot.",
    version="1.0.0"
)

# --- CORS Middleware Configuration ---
# Add CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Dependency Injection and Initialization ---
try:
    # 1. Initialize core services (these have no dependencies on other services)
    firebase_service = FirebaseService()
    gemini_service = GeminiService()
    rag_service = RAGService()

    # 2. Initialize services that depend on other services
    auth_service = AuthService(firebase_service=firebase_service)

    # 3. Initialize agents and inject their service dependencies
    textbook_agent = TextbookAgent(gemini_service=gemini_service)
    visual_agent = VisualAgent(gemini_service=gemini_service)
    audio_agent = AudioAgent(gemini_service=gemini_service)
    grade_agent = GradeAgent(gemini_service=gemini_service, rag_service=rag_service)
    lesson_planner_agent = LessonPlannerAgent(gemini_service=gemini_service)
    feedback_agent = FeedbackAgent(firebase_service=firebase_service)

    # 4. Setup API routes by passing all initialized components
    api_router = setup_api_routes(
        auth_service=auth_service,
        textbook_agent=textbook_agent,
        visual_agent=visual_agent,
        audio_agent=audio_agent,
        grade_agent=grade_agent,
        lesson_planner_agent=lesson_planner_agent,
        feedback_agent=feedback_agent
    )

    # 5. Include the configured router in the main FastAPI app
    app.include_router(api_router)
    
    # 6. Include the new RAG Educational Chatbot router
    app.include_router(router)
    
    logger.info("✅ All services, agents, and routes initialized successfully.")

except Exception as e:
    logger.critical(f"🚨 A critical error occurred during application startup: {e}", exc_info=True)
    # You might want to exit or handle this more gracefully
    # For now, we'll let it raise to prevent a broken app from running
    raise


# --- Root Endpoint (Enhanced) ---
@app.get("/")
async def serve_home(request: Request):
    """
    Serves the main index.html file for the frontend and provides API information.
    This endpoint now serves dual purposes:
    1. Serves the frontend HTML file when accessed via browser
    2. Provides API information when accessed programmatically
    """
    # Check if the request is from a browser (simplified check)
    user_agent = request.headers.get("user-agent", "").lower()
    accept_header = request.headers.get("accept", "").lower()
    
    # If it looks like a browser request, serve the HTML file
    if "text/html" in accept_header and any(browser in user_agent for browser in ["mozilla", "chrome", "safari", "edge"]):
        try:
            return FileResponse('templates/index.html')
        except FileNotFoundError:
            # If HTML file doesn't exist, fall back to JSON response
            logger.warning("templates/index.html not found, serving JSON response instead")
    
    # Otherwise, return API information (for programmatic access)
    return {
        "message": "Sahayak AI API with RAG Educational Chatbot",
        "status": "running",
        "version": "1.0.0",
        "endpoints": {
            "frontend": "GET / (serves HTML)",
            "chat": "POST /chat (RAG Educational Chatbot)",
            "sahayak_api": "Various endpoints for Sahayak AI services",
            "docs": "GET /docs",
            "redoc": "GET /redoc"
        },
        "features": [
            "RAG Educational Chatbot for K-12 students",
            "Sahayak AI educational platform services",
            "Textbook, Visual, Audio, Grade, Lesson Planning, and Feedback agents",
            "Firebase integration",
            "Gemini AI integration"
        ]
    }


# --- Uvicorn Runner ---
# This allows running the app directly with 'python main.py'
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)