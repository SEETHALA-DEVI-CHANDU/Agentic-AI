
from services.gemini_service import GeminiService
from services.rag_service import RAGService

class GradeAgent:
    def __init__(self, gemini_service: GeminiService, rag_service: RAGService):
        self.gemini_service = gemini_service
        self.rag_service = rag_service

    def answer_question(self, question: str, grade: int, difficulty: str) -> str:
        # RAG can be used here to find grade-specific content
        context = self.rag_service.search_kb(question, 'grade_content')

        prompt = f"""
You are an AI tutor. A teacher has a question for a student in Grade {grade} with a difficulty level of '{difficulty}'.
The question is: '{question}'

Use the following context if it's relevant to the question.
Context: '{context['content'] if context else 'No specific context found.'}'

Provide a clear, simple answer. For 'Basic' difficulty, include a simple analogy. For 'Advanced' difficulty, be a bit more detailed but still use easy language.
"""
        return self.gemini_service.generate_text_response([prompt])