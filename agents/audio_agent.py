# agents/audio_agent.py

from services.gemini_service import GeminiService
import logging

logger = logging.getLogger(__name__)

class AudioAgent:
    def __init__(self, gemini_service: GeminiService):
        self.gemini_service = gemini_service
        self.base_prompt = """
You are an expert multilingual educational AI assistant. A teacher will provide transcribed text from an audio recording.

CRITICAL LANGUAGE RULE: You MUST respond in the language specified by the user. DO NOT use English unless explicitly requested.

Your task is to:
1. Analyze the transcribed text provided by the user.
2. Determine if the text is a question or informational content and provide a suitable explanation or answer.
3. Respond ENTIRELY in the specified target language - every single word, sentence, and explanation.

Your final response MUST be:
- 100% in the target language (NO English words mixed in)
- Simple, clear, and safe for educational use
- Include a relatable analogy if possible
- Culturally appropriate for the target language/region
- Educational and appropriate for classroom use

REMEMBER: If told to respond in Kannada, Tamil, Hindi, etc. - use ONLY that language. No English at all.
"""

    def process_audio_query(self, transcribed_text: str, target_language: str = None) -> str:
        """
        Process audio query with optional target language specification
        
        Args:
            transcribed_text: The transcribed audio text
            target_language: Optional target language for the response (e.g., "English", "Kannada", "Tamil", etc.)
        
        Returns:
            Response in the specified or detected language
        """
        try:
            prompt_parts = []
            
            if target_language:
                # Much stronger language enforcement
                language_instruction = f"""
MANDATORY INSTRUCTION: You MUST respond 100% in {target_language} language. 
- Do NOT use any English words
- Do NOT mix languages  
- Every word, every sentence must be in {target_language}
- If you don't know how to say something in {target_language}, use simple words in {target_language}
- This is absolutely required - NO EXCEPTIONS

Target Language: {target_language}
"""
                prompt_parts.append(language_instruction)
            
            prompt_parts.append(self.base_prompt)
            prompt_parts.append(f"Teacher's transcribed text: \"{transcribed_text}\"")
            
            if target_language:
                prompt_parts.append(f"REMINDER: Respond entirely in {target_language}. No English allowed.")
            
            response = self.gemini_service.generate_text_response(prompt_parts)
            logger.info(f"✅ Audio query processed successfully. Language: {target_language or 'auto-detect'}")
            return response
            
        except Exception as e:
            logger.error(f"❌ Error processing audio query: {e}")
            if target_language and target_language.lower() != 'english':
                return f"माफ़ करें, मुझे आपका अनुरोध संसाधित करने में त्रुटि हुई है। कृपया फिर से कोशिश करें।"  # Fallback in Hindi
            return "I apologize, but I encountered an error while processing your request. Please try again."

    def process_audio_query_with_language_detection(self, transcribed_text: str, user_specified_language: str = None) -> dict:
        """
        Enhanced method that returns both the response and detected/used language
        
        Args:
            transcribed_text: The transcribed audio text
            user_specified_language: Language specified by user (overrides detection)
        
        Returns:
            Dictionary with 'response', 'language_used', and 'language_source'
        """
        try:
            if user_specified_language:
                # User specified a language - use it
                response = self.process_audio_query(transcribed_text, user_specified_language)
                return {
                    'response': response,
                    'language_used': user_specified_language,
                    'language_source': 'user_specified'
                }
            else:
                # Auto-detect language first
                detection_prompt = [f"""
You are a language detection expert. Analyze this text and respond with ONLY the language name in English.

Text to analyze: "{transcribed_text}"

Respond with only one word - the language name (examples: English, Kannada, Tamil, Malayalam, Hindi, Telugu, Bengali, Gujarati, Marathi, etc.)
"""]
                detected_language = self.gemini_service.generate_text_response(detection_prompt).strip()
                logger.info(f"🔍 Detected language: {detected_language}")
                
                # Now get response in detected language
                response = self.process_audio_query(transcribed_text, detected_language)
                return {
                    'response': response,
                    'language_used': detected_language,
                    'language_source': 'auto_detected'
                }
                
        except Exception as e:
            logger.error(f"❌ Error in language detection/processing: {e}")
            return {
                'response': "I apologize, but I encountered an error while processing your request. Please try again.",
                'language_used': 'English',
                'language_source': 'error_fallback'
            }

    def test_language_response(self, test_question: str, target_language: str) -> dict:
        """
        Test method to verify language enforcement is working
        
        Args:
            test_question: A simple test question
            target_language: Target language to test
            
        Returns:
            Dictionary with test results
        """
        try:
            response = self.process_audio_query(test_question, target_language)
            
            # Basic check - count English words (this is approximate)
            english_words = ['the', 'is', 'are', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by']
            english_word_count = sum(1 for word in english_words if word.lower() in response.lower())
            
            return {
                'question': test_question,
                'target_language': target_language,
                'response': response,
                'english_words_detected': english_word_count,
                'likely_correct_language': english_word_count < 3  # Rough heuristic
            }
            
        except Exception as e:
            logger.error(f"❌ Error in language test: {e}")
            return {
                'question': test_question,
                'target_language': target_language,
                'response': f"Error: {e}",
                'english_words_detected': -1,
                'likely_correct_language': False
            }

    def get_supported_languages(self) -> list:
        """
        Test method to verify language enforcement is working
        
        Args:
            test_question: A simple test question
            target_language: Target language to test
            
        Returns:
            Dictionary with test results
        """
        try:
            response = self.process_audio_query(test_question, target_language)
            
            # Basic check - count English words (this is approximate)
            english_words = ['the', 'is', 'are', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by']
            english_word_count = sum(1 for word in english_words if word.lower() in response.lower())
            
            return {
                'question': test_question,
                'target_language': target_language,
                'response': response,
                'english_words_detected': english_word_count,
                'likely_correct_language': english_word_count < 3  # Rough heuristic
            }
            
        except Exception as e:
            logger.error(f"❌ Error in language test: {e}")
            return {
                'question': test_question,
                'target_language': target_language,
                'response': f"Error: {e}",
                'english_words_detected': -1,
                'likely_correct_language': False
            }
        """
        Returns a list of commonly supported languages for the educational context
        """
        return [
            "English",
            "Kannada", 
            "Tamil",
            "Malayalam", 
            "Telugu",
            "Hindi",
            "Bengali",
            "Gujarati",
            "Marathi",
            "Punjabi",
            "Urdu",
            "Odia",
            "Assamese"
        ]

# Example usage with your existing GeminiService:
"""
from services.gemini_service import GeminiService
from agents.audio_agent import AudioAgent

# Initialize the agent with your existing GeminiService
gemini_service = GeminiService()
audio_agent = AudioAgent(gemini_service)

# Test language enforcement
test_result = audio_agent.test_language_response("What is photosynthesis?", "Kannada")
print(f"Question: {test_result['question']}")
print(f"Target Language: {test_result['target_language']}")
print(f"Response: {test_result['response']}")
print(f"Likely correct language: {test_result['likely_correct_language']}")

# Production usage examples:

# Method 1: Force response in specific language
result1 = audio_agent.process_audio_query("What is water?", "Kannada")
print("Kannada response:", result1)

# Method 2: Enhanced method with language detection
result2 = audio_agent.process_audio_query_with_language_detection(
    "What is the sun?",  # English input
    "Tamil"  # But force Tamil response
)
print(f"Tamil Response: {result2['response']}")
print(f"Language used: {result2['language_used']}")

# Method 3: Auto-detect and respond in same language
result3 = audio_agent.process_audio_query_with_language_detection(
    "ಸೂರ್ಯ ಎಂದರೇನು?"  # Kannada question
)
print(f"Auto-detected response: {result3['response']}")
print(f"Detected language: {result3['language_used']}")
"""