import json
import re
from typing import Dict, List, Any, Optional
from html import unescape

class TextbookAgent:
    def __init__(self, gemini_service, rag_service=None, research_service=None):
        self.gemini_service = gemini_service
        self.rag_service = rag_service
        self.research_service = research_service

    def generate_practice_material(self, image_bytes: bytes, difficulty: str,
                                   grade_levels: List[str] = None, 
                                   specified_language: Optional[str] = None,
                                   question_text: Optional[str] = None) -> str:
        """
        Generate educational content based on difficulty level in the appropriate language
        
        Args:
            image_bytes: The textbook page image
            difficulty: 'basic', 'intermediate', or 'advanced'
            grade_levels: List of specific grade levels if known
            specified_language: Explicitly specified language if needed
            question_text: The original question text for language context
        
        Returns:
            Clean plain text string ready for display in the appropriate language
        """
        
        # Validate difficulty level
        if difficulty not in ["basic", "intermediate", "advanced"]:
            difficulty = "basic"  # Default to basic if invalid
        
        # Create language context for the prompt
        language_context = self._create_language_context(specified_language, question_text)
        
        # Define difficulty-specific parameters
        if difficulty == "basic":
            prompt = self._create_prompt(
                level_name="Basic (6-10 year olds)",
                language_style="Use very simple words, short sentences, and a fun, playful tone. Explain concepts using analogies to toys, games, or animals.",
                section1_title="SIMPLE EXPLANATIONS",
                section1_desc="Explain the main idea in a way an 8-year-old can easily understand.",
                section2_title="STORY TIME",
                section2_desc="Tell a short, exciting story about kids or animals learning about this topic.",
                section3_title="FUN ACTIVITIES",
                section3_desc="Suggest hands-on, playful activities like drawing or building with blocks.",
                language_context=language_context
            )
        elif difficulty == "intermediate":
            prompt = self._create_prompt(
                level_name="Intermediate (11-14 year olds)",
                language_style="Use proper academic vocabulary but explain all new terms clearly. The tone should be engaging and connect to real-world technology and science.",
                section1_title="CLEAR CONCEPTS",
                section1_desc="Explain the main ideas using proper academic terms, providing clear definitions and detailed examples.",
                section2_title="REAL-WORLD APPLICATIONS",
                section2_desc="Show how this topic is used in real jobs, modern technology, or science.",
                section3_title="PRACTICE ACTIVITIES",
                section3_desc="Suggest research topics, simple experiments, or problem-solving exercises.",
                language_context=language_context
            )
        else:  # advanced
            prompt = self._create_prompt(
                level_name="Advanced (16+ year olds)",
                language_style="Use sophisticated, university-level academic language and assume strong foundational knowledge. The tone should be formal and analytical.",
                section1_title="DETAILED CONCEPTS",
                section1_desc="Provide a comprehensive theoretical explanation, referencing multiple perspectives and current research findings.",
                section2_title="CUTTING-EDGE APPLICATIONS",
                section2_desc="Discuss the latest research developments, emerging technologies, and interdisciplinary applications of this topic.",
                section3_title="RESEARCH PROJECTS",
                section3_desc="Suggest advanced research opportunities, literature review projects, or original analysis tasks.",
                language_context=language_context
            )
        
        # Generate content using Gemini
        response_text = self.gemini_service.analyze_image(image_bytes, [prompt])
        
        # Clean and format the response
        clean_response = self._clean_response(response_text)
        
        # Add difficulty level validation
        validated_response = self._validate_difficulty_level(clean_response, difficulty)
        
        return validated_response

    def _create_language_context(self, specified_language: Optional[str] = None, 
                                 question_text: Optional[str] = None) -> str:
        """
        Create language context instructions for the prompt.
        """
        language_instruction = """
CRITICAL LANGUAGE REQUIREMENT:
- Detect the primary language from the image content (text, labels, captions, etc.)
- If a specific language is mentioned in the user's question or request, use that language
- Generate ALL content (including section titles) in the same language as detected/specified
- Use native vocabulary, grammar, expressions, and cultural context appropriate for that language
- If no clear language is detected, default to English

"""
        
        if specified_language:
            language_instruction += f"OVERRIDE: Generate content specifically in {specified_language}.\n\n"
        
        if question_text:
            language_instruction += f"CONTEXT: Consider this user input for language cues: \"{question_text}\"\n\n"
        
        return language_instruction

    def _create_prompt(self, level_name: str, language_style: str, section1_title: str,
                       section1_desc: str, section2_title: str, section2_desc: str,
                       section3_title: str, section3_desc: str, language_context: str) -> str:
        """Creates a dynamically structured prompt for a specific difficulty level and language."""
        
        return f"""
Analyze the provided image. Based on its content, generate educational material with the following specifications.

{language_context}CRITICAL INSTRUCTION: You MUST generate content for the specified difficulty level: {level_name}.

MANDATORY LANGUAGE STYLE:
{language_style}

MANDATORY STRUCTURE:
Create content with these THREE sections. Translate section titles to match the detected/specified language:

1. {section1_title}:
{section1_desc}

2. {section2_title}:
{section2_desc}

3. {section3_title}:
{section3_desc}

FINAL CHECK: Ensure the vocabulary, tone, and complexity perfectly match the target {level_name} audience and that ALL content is in the appropriate language detected from the image or specified in the request.
"""

    def _validate_difficulty_level(self, response_text: str, difficulty: str) -> str:
        """Validate that the response matches the expected difficulty level"""
        
        basic_indicators = ["simple", "easy", "fun", "kids", "children", "like", "play", "story"]
        advanced_indicators = ["theoretical", "methodology", "framework", "analysis", "research", "sophisticated", "complex", "paradigm"]
        
        words = response_text.lower().split()
        
        if difficulty == "basic":
            advanced_word_count = sum(1 for word in words if any(indicator in word for indicator in advanced_indicators))
            if advanced_word_count > 2: # Lowered threshold for stricter check
                return f"SIMPLIFIED FOR YOUNG LEARNERS:\n\n{response_text}"
        
        elif difficulty == "advanced":
            basic_word_count = sum(1 for word in words if any(indicator in word for indicator in basic_indicators))
            if basic_word_count > 5: # Lowered threshold
                return f"ADVANCED ACADEMIC CONTENT:\n\n{response_text}"
        
        # Note: Your original function didn't have a check for 'intermediate'. 
        # You could add one if desired.
        
        return response_text

    def _clean_response(self, response_text: str) -> str:
        """Clean the response text to remove any unwanted formatting"""
        
        clean_text = re.sub(r'<[^>]+>', '', response_text)
        clean_text = re.sub(r'\*\*([^*]+)\*\*', r'\1', clean_text)
        clean_text = re.sub(r'\*([^*]+)\*', r'\1', clean_text)
        clean_text = re.sub(r'#{1,6}\s*', '', clean_text)
        clean_text = unescape(clean_text)
        clean_text = re.sub(r'\n\s*\n\s*\n', '\n\n', clean_text)
        # Ensure section headers have a double newline after them for readability
        clean_text = re.sub(r'([A-Z0-9 -]+:)\n([A-Za-z])', r'\1\n\n\2', clean_text)
        clean_text = clean_text.strip()
        
        return clean_text

    def generate_multiple_difficulty_levels(self, image_bytes: bytes, 
                                            specified_language: Optional[str] = None,
                                            question_text: Optional[str] = None) -> Dict[str, str]:
        """Generate materials for all difficulty levels in the detected/specified language"""
        results = {}
        
        for difficulty in ["basic", "intermediate", "advanced"]:
            results[difficulty] = self.generate_practice_material(
                image_bytes, difficulty, 
                specified_language=specified_language,
                question_text=question_text
            )
        
        return results