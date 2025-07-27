import random
import logging
from typing import List, Dict, Any
from services.gemini_service import GeminiService

# Configure logging
logger = logging.getLogger(__name__)

class GameAgent:
    """Agent for generating educational games like Two Truths and a Lie."""
    
    def __init__(self, gemini_service: GeminiService = None):
        """
        Initialize the GameAgent.
        
        Args:
            gemini_service: Optional GeminiService instance for AI generation
        """
        self.gemini_service = gemini_service or GeminiService()
    
    def generate_two_truths_one_lie(self, topic: str, difficulty: str) -> List[Dict[str, Any]]:
        """
        Generate 5 sets of "Two Truths and a Lie" games for the given topic and difficulty.
        
        Args:
            topic: The subject topic (e.g., "Solar System", "World War II", "Photosynthesis")
            difficulty: The difficulty level ("easy", "medium", "hard")
            
        Returns:
            List of dictionaries, each containing 3 statements and the correct answer
        """
        try:
            # Create the prompt for the AI model
            prompt = self._create_game_prompt(topic, difficulty)
            
            # Get response from Gemini service
            response = self.gemini_service.generate_content(prompt)
            
            # Parse the response into structured format
            games = self._parse_game_response(response)
            
            # Validate that we have exactly 5 games
            if len(games) != 5:
                logger.warning(f"Expected 5 games, got {len(games)}. Generating additional games with AI.")
                games = self._ensure_five_games(games, topic, difficulty)
            
            # Final validation - if we still don't have games, raise an error
            if not games:
                raise Exception("Failed to generate any games after multiple attempts")
            
            return games
            
        except Exception as e:
            logger.error(f"Error generating Two Truths and a Lie games: {str(e)}")
            # Try one more time with a simplified approach
            try:
                logger.info("Attempting simplified game generation as final fallback...")
                simple_games = self._generate_simple_games(topic, difficulty)
                if simple_games:
                    return simple_games
            except Exception as fallback_error:
                logger.error(f"Fallback generation also failed: {str(fallback_error)}")
            
            # If everything fails, raise an exception
            raise Exception(f"Unable to generate games for topic '{topic}' - please try again or choose a different topic")
    
    def _create_game_prompt(self, topic: str, difficulty: str) -> str:
        """Create a detailed prompt for generating the games."""
        
        difficulty_instruction = self._get_difficulty_instruction(difficulty)
        
        prompt = f"""
Generate exactly 5 "Two Truths and a Lie" games about the topic: {topic}

Difficulty level: {difficulty}
{difficulty_instruction}

For each game, provide:
1. Three statements (2 true, 1 false) that are specific and educational about {topic}
2. Clearly indicate which statement is the lie
3. Make the statements engaging and factually accurate (except for the lies)
4. Ensure the lies are plausible but clearly incorrect to someone with knowledge of {topic}
5. Vary the position of the lie across different games (don't always make it statement 3)
6. Include diverse aspects of {topic} - don't focus on just one area

Requirements:
- All true statements must be factually correct and verifiable
- Lies should be believable misconceptions or plausible-sounding falsehoods
- Cover different subtopics within {topic} for variety
- Make each game educational and interesting

Format your response as follows for each game:

GAME 1:
Statement 1: [specific factual statement about {topic}]
Statement 2: [another specific factual statement about {topic}]  
Statement 3: [plausible but false statement about {topic}]
The lie is: Statement [number]
Explanation: [detailed explanation of why it's false and what the truth is]

---

GAME 2:
Statement 1: [specific factual statement about {topic}]
Statement 2: [plausible but false statement about {topic}]
Statement 3: [another specific factual statement about {topic}]
The lie is: Statement [number]
Explanation: [detailed explanation of why it's false and what the truth is]

---

Continue this pattern for all 5 games, varying the position of the lie and covering different aspects of {topic}.
"""
        return prompt
    
    def _get_difficulty_instruction(self, difficulty: str) -> str:
        """Get difficulty-specific instructions for the AI prompt."""
        difficulty_instructions = {
            "easy": "Use simple vocabulary and basic concepts suitable for elementary/middle school students. Focus on fundamental facts that are easy to understand.",
            "medium": "Use moderate complexity suitable for high school students. Include some technical terms but explain them. Balance basic and intermediate concepts.",
            "hard": "Use advanced concepts and terminology appropriate for college level or experts. Include nuanced details, technical precision, and sophisticated understanding of the subject."
        }
        
        return difficulty_instructions.get(
            difficulty.lower(), 
            difficulty_instructions["medium"]
        )
    
    def _parse_game_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse the AI response into structured game data."""
        games = []
        
        try:
            # Split response into individual games
            game_sections = response.split("GAME ")
            
            for section in game_sections[1:]:  # Skip the first empty split
                game_data = self._parse_single_game(section)
                if game_data:
                    games.append(game_data)
        
        except Exception as e:
            logger.error(f"Error parsing game response: {str(e)}")
        
        return games
    
    def _parse_single_game(self, game_text: str) -> Dict[str, Any]:
        """Parse a single game section into structured data."""
        try:
            lines = game_text.strip().split('\n')
            statements = []
            lie_position = None
            explanation = ""
            
            for line in lines:
                line = line.strip()
                if line.startswith("Statement "):
                    # Extract statement text
                    statement = line.split(": ", 1)[1] if ": " in line else line
                    statements.append(statement)
                elif line.startswith("The lie is:"):
                    # Extract lie position
                    try:
                        lie_position = int(line.split("Statement ")[1]) - 1  # Convert to 0-based index
                    except (IndexError, ValueError):
                        lie_position = None
                elif line.startswith("Explanation:"):
                    explanation = line.split(": ", 1)[1] if ": " in line else ""
            
            # Validate we have 3 statements and a lie position
            if len(statements) == 3 and lie_position is not None and 0 <= lie_position <= 2:
                return {
                    "statements": statements,
                    "lie_position": lie_position,
                    "explanation": explanation,
                    "game_id": len(statements)  # Simple ID for now
                }
        
        except Exception as e:
            logger.error(f"Error parsing single game: {str(e)}")
        
        return None
    
    def _ensure_five_games(self, games: List[Dict[str, Any]], topic: str, difficulty: str) -> List[Dict[str, Any]]:
        """Ensure we have exactly 5 games, using AI to generate more if necessary."""
        if len(games) >= 5:
            return games[:5]  # Take first 5 if we have more
        
        # Generate additional games using AI if we have fewer than 5
        needed = 5 - len(games)
        logger.info(f"Need {needed} more games, generating with AI...")
        
        try:
            # Create prompt for generating only the needed number of games
            additional_prompt = f"""
Generate exactly {needed} "Two Truths and a Lie" games about: {topic}
Difficulty: {difficulty}

{self._get_difficulty_instruction(difficulty)}

Make sure these games are different from typical questions about {topic}. Be creative and educational.

Format each game as:
GAME [number]:
Statement 1: [statement]
Statement 2: [statement]
Statement 3: [statement]
The lie is: Statement [number]
Explanation: [brief explanation]

---
"""
            
            response = self.gemini_service.generate_content(additional_prompt)
            additional_games = self._parse_game_response(response)
            
            # Combine original games with additional ones
            combined_games = games + additional_games
            
            # Return exactly 5 games
            return combined_games[:5]
            
        except Exception as e:
            logger.error(f"Failed to generate additional games: {str(e)}")
            # If all else fails, try fallback method
            fallback_games = self._get_fallback_games(topic, difficulty)
            combined_games = games + fallback_games
            return combined_games[:5] if combined_games else []
    
    def _get_fallback_games(self, topic: str, difficulty: str) -> List[Dict[str, Any]]:
        """Generate fallback games when AI generation fails - using AI for backup too."""
        try:
            # Create a simplified prompt for fallback generation
            fallback_prompt = f"""
Generate exactly 5 simple "Two Truths and a Lie" games about: {topic}

Keep it simple but educational. For each game, provide exactly 3 statements where 2 are true and 1 is false.

Format each game as:
GAME [number]:
Statement 1: [factual statement about {topic}]
Statement 2: [another factual statement about {topic}]
Statement 3: [plausible but false statement about {topic}]
The lie is: Statement [number]
Explanation: [why the lie is incorrect]

---

Make sure statements are specific to {topic} and educational.
"""
            
            # Try to get AI-generated fallback
            response = self.gemini_service.generate_content(fallback_prompt)
            parsed_games = self._parse_game_response(response)
            
            if parsed_games and len(parsed_games) >= 5:
                return parsed_games[:5]
                
        except Exception as e:
            logger.error(f"Even fallback AI generation failed: {str(e)}")
        
        # Ultimate fallback - return empty list to indicate complete failure
        logger.error("All game generation methods failed")
        return []
    
    def _generate_simple_games(self, topic: str, difficulty: str) -> List[Dict[str, Any]]:
        """Generate games with a very simple, direct prompt as final fallback."""
        try:
            simple_prompt = f"""
Create 5 educational "Two Truths and a Lie" games about {topic}.

Each game needs exactly 3 statements: 2 true facts and 1 false statement.
Make the false statement believable but wrong.

Example format:
GAME 1:
Statement 1: [True fact about {topic}]
Statement 2: [True fact about {topic}]
Statement 3: [False but believable statement about {topic}]
The lie is: Statement 3
Explanation: [Why statement 3 is wrong]

Now create 5 different games following this exact format.
"""
            
            response = self.gemini_service.generate_content(simple_prompt)
            return self._parse_game_response(response)[:5]  # Ensure max 5 games
            
        except Exception as e:
            logger.error(f"Simple game generation failed: {str(e)}")
            return []