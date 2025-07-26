# agents/audio_agent.py

from services.gemini_service import GeminiService

class AudioAgent:
    def __init__(self, gemini_service: GeminiService):
        self.gemini_service = gemini_service
        self.base_prompt = """
You are an expert multilingual educational AI assistant. A teacher will provide transcribed text from an audio recording.

Your task is to:
1.  Analyze the transcribed text provided by the user.
2.  **Detect the language of the transcribed text (e.g., English, Kannada, Tamil, Malayalam, etc.). Your entire response MUST be in that same detected language.**
3.  Determine if the text is a question or informational content and provide a suitable explanation or answer.

Your final response MUST be:
- Simple, clear, and safe.
- Written in the detected language.
- Include a relatable analogy if possible.
"""

    def process_audio_query(self, transcribed_text: str) -> str:
        prompt_parts = [
            self.base_prompt,
            f"Here is the transcribed text from the teacher: \"{transcribed_text}\""
        ]
        response = self.gemini_service.generate_text_response(prompt_parts)
        return response