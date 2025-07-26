
from services.gemini_service import GeminiService

class LessonPlannerAgent:
    def __init__(self, gemini_service: GeminiService):
        self.gemini_service = gemini_service

    def create_plan(self, grade: int, subject: str, chapter: str) -> str:
        prompt = f"""
Create a simple, one-week lesson plan for a teacher in a multi-grade classroom.
The plan should be for:
- Grade: {grade}
- Subject: {subject}
- Chapter/Topic: {chapter}

The lesson plan should be structured with 3-4 simple activities for the week. For each activity, suggest a small objective and a simple teaching method (e.g., storytelling, drawing, group activity).
Keep the language extremely simple. The output should be in a clean, easy-to-read format.
"""
        return self.gemini_service.generate_text_response([prompt])