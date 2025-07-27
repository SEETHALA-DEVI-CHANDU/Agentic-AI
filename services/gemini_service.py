import google.generativeai as genai
from PIL import Image
import io
import logging
from config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GeminiService:
    """A wrapper for Google Gemini AI models."""
    def __init__(self):
        try:
            genai.configure(api_key=Config.GEMINI_API_KEY)
            self.text_model = genai.GenerativeModel('gemini-2.5-pro')
            self.vision_model = genai.GenerativeModel('gemini-2.5-pro')
            # gemini-1.5-flash-latest
            logger.info("✅ Gemini service initialized successfully.")
        except Exception as e:
            logger.critical(f"🚨 CRITICAL: Failed to initialize Gemini. Error: {e}")
            raise

    def generate_text_response(self, prompt_parts: list):
        """Generates a text response from a list of prompt parts."""
        try:
            response = self.text_model.generate_content(prompt_parts)
            return response.text
        except Exception as e:
            logger.error(f"Gemini text generation error: {e}")
            return f"Error generating response: {e}"

    def analyze_image(self, image_bytes: bytes, prompt_parts: list):
        """Analyzes an image with a given prompt."""
        try:
            img = Image.open(io.BytesIO(image_bytes))
            full_prompt = prompt_parts + [img]
            response = self.vision_model.generate_content(full_prompt)
            return response.text
        except Exception as e:
            logger.error(f"Gemini image analysis error: {e}")
            return f"Error analyzing image: {e}"
        
    def generate_content(self, prompt_parts: list):
        """Generates content using Gemini's text model."""
        try:
            response = self.text_model.generate_content(prompt_parts)
            return response.text
        except Exception as e:
            logger.error(f"Gemini content generation error: {e}")
            return f"Error generating content: {e}"