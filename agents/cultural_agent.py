from services.gemini_service import GeminiService
from services.rag_service import RAGService

class CulturalAgent:
    def __init__(self, gemini_service: GeminiService, rag_service: RAGService):
        self.gemini_service = gemini_service
        self.rag_service = rag_service

    def get_local_content(self, query: str) -> str:
        context = self.rag_service.search_kb(query, 'cultural_content')
        
        prompt = f"""
You are a helpful teaching assistant. A teacher asked: '{query}'.
Use the following local context to provide a simple, culturally relevant answer suitable for a young student.
If the context is relevant, use it. If not, answer the question based on your general knowledge.

Context:
'{context['content'] if context else 'No specific local context found.'}'

Your answer should be simple and easy to understand.
"""
        return self.gemini_service.generate_text_response([prompt])

