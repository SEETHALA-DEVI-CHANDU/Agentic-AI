import os
from dotenv import load_dotenv

# This line finds and loads the variables from your .env file
load_dotenv()

class Config:
    """
    Centralized configuration class to load and validate environment variables.
    This acts as a single source of truth for all settings.
    """
    
    # --- Google AI Configuration ---
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    
    # --- Firebase Configuration ---
    FIREBASE_PROJECT_ID = os.getenv('FIREBASE_PROJECT_ID')

    # --- Validation Block ---
    # This is a crucial step. The application will immediately stop if a critical
    # environment variable is not found, preventing confusing errors later.
    if not GEMINI_API_KEY:
        raise ValueError("🔴 CRITICAL ERROR: 'GEMINI_API_KEY' is not set in the .env file.")
    
    if not FIREBASE_PROJECT_ID:
        raise ValueError("🔴 CRITICAL ERROR: 'FIREBASE_PROJECT_ID' is not set in the .env file.")