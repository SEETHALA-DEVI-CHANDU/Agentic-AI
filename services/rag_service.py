import json
import requests
import os
import asyncio
import numpy as np
from sentence_transformers import SentenceTransformer
import logging
from sklearn.metrics.pairwise import cosine_similarity
from dotenv import load_dotenv

# Import Firebase Admin SDK components
import firebase_admin
from firebase_admin import credentials, firestore

# Load environment variables from .env file
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Firebase Configuration (from your environment) ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY_HERE")
FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID", "sahayak-ai-agents")

# Your Firebase service account configuration
FIREBASE_SERVICE_ACCOUNT_CONFIG = {}

def validate_firebase_config(config):
    """Validate that all required Firebase config fields are present and not empty."""
    required_fields = [
        "type", "project_id", "private_key_id", "private_key", 
        "client_email", "client_id", "auth_uri", "token_uri"
    ]
    
    for field in required_fields:
        if not config.get(field) or config[field].strip() == "":
            return False, f"Missing or empty required field: {field}"
    
    # Additional validation for specific fields
    if not config["client_email"].endswith("@" + config["project_id"] + ".iam.gserviceaccount.com"):
        return False, "client_email format appears incorrect for service account"
    
    if not config["private_key"].startswith("-----BEGIN PRIVATE KEY-----"):
        return False, "private_key format appears incorrect"
    
    return True, "Configuration is valid"

# Initialize Firebase configuration
try:
    with open('firebase_service_account.json', 'r') as f:
        FIREBASE_SERVICE_ACCOUNT_CONFIG = json.load(f)
    print("Firebase service account configuration loaded from firebase_config.json.")
    
    # Validate the configuration
    is_valid, validation_message = validate_firebase_config(FIREBASE_SERVICE_ACCOUNT_CONFIG)
    if not is_valid:
        print(f"❌ Firebase configuration validation failed: {validation_message}")
        print("\n🔧 To fix this issue:")
        print("1. Go to the Firebase Console (https://console.firebase.google.com/)")
        print("2. Select your project 'sahayak-ai-agents'")
        print("3. Go to Project Settings > Service Accounts")
        print("4. Click 'Generate new private key'")
        print("5. Download the JSON file and replace your firebase_config.json")
        print("6. Make sure the JSON contains all required fields with actual values")
        FIREBASE_SERVICE_ACCOUNT_CONFIG = {}
    else:
        print("✅ Firebase configuration validation passed.")
        
except FileNotFoundError:
    print("❌ Error: firebase_config.json not found.")
    print("\n🔧 To fix this issue:")
    print("1. Go to the Firebase Console (https://console.firebase.google.com/)")
    print("2. Select your project 'sahayak-ai-agents'")
    print("3. Go to Project Settings > Service Accounts")
    print("4. Click 'Generate new private key'")
    print("5. Save the downloaded JSON file as 'firebase_config.json' in the same directory as this script")
    FIREBASE_SERVICE_ACCOUNT_CONFIG = {}
    
except json.JSONDecodeError as e:
    print(f"❌ Error: Could not decode firebase_config.json: {e}")
    print("Please check that the JSON file is properly formatted.")
    FIREBASE_SERVICE_ACCOUNT_CONFIG = {}

# Initialize Firebase
db = None
try:
    if FIREBASE_SERVICE_ACCOUNT_CONFIG and FIREBASE_SERVICE_ACCOUNT_CONFIG.get("project_id"):
        if "private_key" in FIREBASE_SERVICE_ACCOUNT_CONFIG and "\\n" in FIREBASE_SERVICE_ACCOUNT_CONFIG["private_key"]:
            FIREBASE_SERVICE_ACCOUNT_CONFIG["private_key"] = FIREBASE_SERVICE_ACCOUNT_CONFIG["private_key"].replace("\\n", "\n")

        try:
            firebase_admin.get_app()
            print("Firebase app already initialized.")
        except ValueError:
            cred = credentials.Certificate(FIREBASE_SERVICE_ACCOUNT_CONFIG)
            firebase_admin.initialize_app(cred, {
                'projectId': FIREBASE_SERVICE_ACCOUNT_CONFIG["project_id"]
            })
            print("✅ Firebase Admin SDK initialized successfully.")
        
        db = firestore.client()
        
    else:
        print("❌ Firebase service account configuration is incomplete or missing. Skipping Firebase initialization.")
        db = None
        
except Exception as e:
    print(f"❌ Error initializing Firebase Admin SDK: {e}")
    print("\nThis could be due to:")
    print("- Invalid service account credentials")
    print("- Network connectivity issues")
    print("- Incorrect project configuration")
    db = None

# Define a consistent app ID for Firestore collection paths
APP_ID = "rag-chatbot-app"

# --- Local Knowledge Base for Educational Content ---
LOCAL_KNOWLEDGE_BASE = [
    {
        "grade": 1,
        "subject": "Math",
        "chapter_number": 1,
        "chapter_name": "Basic Counting",
        "content": "First grade math focuses on counting numbers 1-100, basic addition and subtraction within 20, and understanding place value. Students learn to recognize and write numbers, compare quantities, and solve simple word problems."
    },
    {
        "grade": 1,
        "subject": "Science",
        "chapter_number": 1,
        "chapter_name": "Living vs Non-living",
        "content": "First grade science introduces the difference between living and non-living things. Students learn about basic needs of living things like food, water, air, and shelter. They explore plants, animals, and their habitats."
    },
    {
        "grade": 1,
        "subject": "English",
        "chapter_number": 1,
        "chapter_name": "Phonics and Reading",
        "content": "First grade English focuses on phonics, sight words, and basic reading skills. Students learn letter sounds, blend consonants and vowels, and read simple sentences. Writing includes forming letters and writing simple words."
    },
    {
        "grade": 2,
        "subject": "Math",
        "chapter_number": 1,
        "chapter_name": "Addition and Subtraction",
        "content": "Second grade math extends addition and subtraction skills to 100, introduces regrouping, and covers basic geometry shapes. Students work with money, time, and measurement using standard units."
    },
    {
        "grade": 2,
        "subject": "Science",
        "chapter_number": 1,
        "chapter_name": "Weather and Seasons",
        "content": "Second grade science covers weather patterns, seasons, and their effects on living things. Students learn about different types of weather, how to measure weather conditions, and seasonal changes in plants and animals."
    },
    {
        "grade": 3,
        "subject": "Math",
        "chapter_number": 1,
        "chapter_name": "Multiplication and Division",
        "content": "Third grade math introduces multiplication and division concepts, fractions as parts of a whole, and area and perimeter. Students work with larger numbers and solve multi-step word problems."
    },
    {
        "grade": 3,
        "subject": "Science",
        "chapter_number": 1,
        "chapter_name": "Plant and Animal Life Cycles",
        "content": "Third grade science explores life cycles of plants and animals, adaptation and survival, and basic concepts of inheritance. Students learn how organisms grow, reproduce, and adapt to their environments."
    },
    {
        "grade": 4,
        "subject": "Math",
        "chapter_number": 1,
        "chapter_name": "Multi-digit Operations",
        "content": "Fourth grade math focuses on multi-digit multiplication and division, equivalent fractions, and decimal notation. Students work with factors, multiples, and patterns in number sequences."
    },
    {
        "grade": 4,
        "subject": "Science",
        "chapter_number": 1,
        "chapter_name": "Energy and Motion",
        "content": "Fourth grade science covers energy forms (light, heat, sound, electrical, mechanical), motion and forces, and simple machines. Students explore how energy transfers and transforms in different situations."
    },
    {
        "grade": 5,
        "subject": "Math",
        "chapter_number": 1,
        "chapter_name": "Fractions and Decimals",
        "content": "Fifth grade math focuses on operations with fractions and decimals, volume and coordinate planes. Students learn to add, subtract, multiply, and divide fractions and decimals with understanding."
    },
    {
        "grade": 5,
        "subject": "Science",
        "chapter_number": 2,
        "chapter_name": "Ecosystems and Environment",
        "content": "Fifth grade science covers ecosystems, food chains and webs, water cycle, and human impact on environment. Students learn about interdependence of organisms and conservation practices."
    },
    {
        "grade": 5,
        "subject": "Social",
        "chapter_number": 3,
        "chapter_name": "American History Foundations",
        "content": "Fifth grade social studies covers early American history, including Native American cultures, European exploration, colonial life, and the founding of the United States."
    },
    {
        "grade": 5,
        "subject": "English",
        "chapter_number": 4,
        "chapter_name": "Reading Comprehension and Writing",
        "content": "Fifth grade English emphasizes reading comprehension strategies, vocabulary development, and structured writing. Students analyze texts, write narratives, and learn basic research skills."
    },
    {
        "grade": 6,
        "subject": "Math",
        "chapter_number": 1,
        "chapter_name": "Ratios and Proportions",
        "content": "Sixth grade math introduces ratios, rates, and proportional relationships. Students work with integers, rational numbers, and begin algebraic thinking with expressions and equations."
    },
    {
        "grade": 6,
        "subject": "Science",
        "chapter_number": 1,
        "chapter_name": "Earth's Systems",
        "content": "Sixth grade science explores Earth's systems including weather and climate, plate tectonics, and the rock cycle. Students learn about interactions between atmosphere, hydrosphere, geosphere, and biosphere."
    },
    {
        "grade": 7,
        "subject": "Math",
        "chapter_number": 1,
        "chapter_name": "Algebraic Expressions",
        "content": "Seventh grade math focuses on algebraic expressions and equations, proportional relationships, and probability. Students work with integers, rational numbers, and geometric constructions."
    },
    {
        "grade": 7,
        "subject": "Science",
        "chapter_number": 1,
        "chapter_name": "Life Science Fundamentals",
        "content": "Seventh grade science covers cell structure and function, genetics and heredity, evolution and natural selection. Students explore how organisms are organized and how traits are passed down."
    },
    {
        "grade": 8,
        "subject": "Math",
        "chapter_number": 1,
        "chapter_name": "Linear Functions",
        "content": "Eighth grade math introduces linear functions, systems of equations, and geometric transformations. Students work with the Pythagorean theorem, volume formulas, and scatter plots."
    },
    {
        "grade": 8,
        "subject": "Science",
        "chapter_number": 2,
        "chapter_name": "Physical Science Basics",
        "content": "Eighth grade science covers forces and motion, energy transfer, wave properties, and basic chemistry including atoms, elements, and chemical reactions."
    },
    {
        "grade": 8,
        "subject": "Social",
        "chapter_number": 3,
        "chapter_name": "American History through Civil War",
        "content": "Eighth grade social studies typically covers American history from colonial times through the Civil War, including the Constitution, westward expansion, and sectional conflicts."
    },
    {
        "grade": 8,
        "subject": "English",
        "chapter_number": 4,
        "chapter_name": "Literary Analysis and Composition",
        "content": "Eighth grade English focuses on literary analysis, argumentative writing, and research skills. Students read complex texts, analyze themes and literary devices, and write structured essays."
    },
    {
        "grade": 9,
        "subject": "Math",
        "chapter_number": 1,
        "chapter_name": "Algebra I Foundations",
        "content": "Ninth grade math typically covers Algebra I, including linear equations, quadratic functions, exponential functions, and statistical analysis. Students develop algebraic reasoning and problem-solving skills."
    },
    {
        "grade": 9,
        "subject": "Science",
        "chapter_number": 1,
        "chapter_name": "Biology Fundamentals",
        "content": "Ninth grade science often focuses on biology, covering cell biology, genetics, evolution, ecology, and human body systems. Students learn scientific method and conduct laboratory investigations."
    },
    {
        "grade": 10,
        "subject": "Math",
        "chapter_number": 1,
        "chapter_name": "Geometry and Advanced Algebra",
        "content": "Tenth grade math often includes Geometry (proofs, theorems, spatial reasoning) or Algebra II (polynomials, rational functions, logarithms, trigonometry basics)."
    },
    {
        "grade": 10,
        "subject": "Science",
        "chapter_number": 2,
        "chapter_name": "Chemistry Foundations",
        "content": "Tenth grade science typically covers chemistry fundamentals including atomic structure, chemical bonding, stoichiometry, and chemical reactions. Laboratory work emphasizes quantitative analysis."
    },
    {
        "grade": 10,
        "subject": "Social",
        "chapter_number": 3,
        "chapter_name": "World History and Geography",
        "content": "Tenth grade social studies often covers world history from ancient civilizations to modern times, with emphasis on cultural development, political systems, and global connections."
    },
    {
        "grade": 10,
        "subject": "English",
        "chapter_number": 4,
        "chapter_name": "Advanced Composition and Literature",
        "content": "Tenth grade English emphasizes critical analysis of literature, advanced composition techniques, research methodology, and persuasive writing. Students engage with complex themes and diverse perspectives."
    }
]


class RAGService:
    """Enhanced RAG service that handles both file-based knowledge bases and educational content."""

    def __init__(self):
        try:
            # Initialize SentenceTransformer model for embeddings
            self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
            
            # File-based knowledge bases (original functionality)
            self.knowledge_base = {}
            self.embeddings = {}
            
            # Educational knowledge base embeddings
            self.educational_embeddings = None
            
            # Initialize both knowledge base systems
            self.initialize_file_knowledge_base()
            self.initialize_educational_knowledge_base()
            
            logger.info("✅ Enhanced RAG service initialized with both file-based and educational knowledge bases.")
            
        except Exception as e:
            logger.critical(f"🚨 Failed to initialize RAG service. Error: {e}")
            raise

    def initialize_file_knowledge_base(self):
        """Loads file-based knowledge base (original functionality)."""
        kb_path = 'knowledge_base'
        
        # Check if knowledge_base directory exists
        if not os.path.exists(kb_path):
            logger.warning(f"📁 Knowledge base directory '{kb_path}' not found. Skipping file-based knowledge base initialization.")
            return
            
        for filename in os.listdir(kb_path):
            if filename.endswith('.json'):
                kb_name = filename.split('.')[0]
                filepath = os.path.join(kb_path, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        self.knowledge_base[kb_name] = json.load(f)
                    self._generate_embeddings_for_kb(kb_name)
                    logger.info(f"📚 Loaded knowledge base: {kb_name}")
                except Exception as e:
                    logger.error(f"❌ Error loading knowledge base {kb_name}: {e}")
        
        if self.knowledge_base:
            logger.info("📚 File-based knowledge bases loaded and embeddings generated.")
        else:
            logger.warning("📚 No file-based knowledge bases found.")

    def initialize_educational_knowledge_base(self):
        """Initialize embeddings for the educational knowledge base."""
        try:
            # Create embeddings for educational content
            texts = []
            for entry in LOCAL_KNOWLEDGE_BASE:
                # Combine all relevant fields for better context
                text = f"Grade {entry['grade']} {entry['subject']}: {entry['chapter_name']} - {entry['content']}"
                texts.append(text)
            
            if texts:
                embeddings_array = self.encoder.encode(texts, convert_to_tensor=False)
                self.educational_embeddings = {
                    'data': LOCAL_KNOWLEDGE_BASE,
                    'embeddings': embeddings_array,
                    'texts': texts
                }
                logger.info(f"📚 Educational knowledge base initialized with {len(texts)} entries.")
            else:
                logger.warning("📚 No educational knowledge base entries found.")
                
        except Exception as e:
            logger.error(f"❌ Error initializing educational knowledge base: {e}")
            self.educational_embeddings = None

    def _generate_embeddings_for_kb(self, kb_name: str):
        """Helper to create and store embeddings for a specific file-based knowledge base."""
        data = self.knowledge_base.get(kb_name, [])
        if not data:
            return
            
        # Combine title and content for better embedding context
        texts = [f"{item.get('topic', '')}: {item.get('content', '')}" for item in data]
        
        if texts:
            embeddings_array = self.encoder.encode(texts, convert_to_tensor=False)
            self.embeddings[kb_name] = {
                'data': data,
                'embeddings': embeddings_array
            }

    def search_kb(self, query: str, kb_name: str, top_k: int = 1):
        """Searches a specific file-based knowledge base for the most relevant content (original functionality)."""
        if kb_name not in self.embeddings:
            logger.warning(f"Knowledge base '{kb_name}' not found.")
            return None

        kb_data = self.embeddings[kb_name]
        query_embedding = self.encoder.encode([query])
        
        sim = cosine_similarity(query_embedding, kb_data['embeddings'])[0]
        top_index = np.argmax(sim)
        
        # Optional similarity threshold
        # if sim[top_index] < 0.3: return None
        
        return kb_data['data'][top_index]

    def get_educational_knowledge(self, grade: int, subject: str, query: str = None, top_k: int = 3):
        """
        Fetches relevant educational knowledge, optionally using semantic search.
        
        Args:
            grade (int): Grade level (1-10)
            subject (str): Subject name (Math, Science, English, Social)
            query (str, optional): Query for semantic search
            top_k (int): Number of top results to return
            
        Returns:
            list or str: Educational content entries or combined content string
        """
        try:
            # First, filter by grade and subject if specified
            relevant_entries = []
            for entry in LOCAL_KNOWLEDGE_BASE:
                if grade and entry['grade'] != grade:
                    continue
                if subject and subject.lower() not in entry.get('subject', '').lower():
                    continue
                relevant_entries.append(entry)
            
            if not relevant_entries:
                logger.info(f"📚 No educational content found for Grade {grade} {subject}")
                return None
            
            # If no query provided, return filtered results
            if not query:
                logger.info(f"📚 Found {len(relevant_entries)} educational entries for Grade {grade} {subject}")
                return relevant_entries[:top_k]
            
            # Use semantic search if query is provided and embeddings are available
            if self.educational_embeddings:
                query_embedding = self.encoder.encode([query])
                
                # Get indices of relevant entries in the original list
                relevant_indices = []
                for i, entry in enumerate(LOCAL_KNOWLEDGE_BASE):
                    if entry in relevant_entries:
                        relevant_indices.append(i)
                
                if relevant_indices:
                    # Calculate similarities only for relevant entries
                    relevant_embeddings = self.educational_embeddings['embeddings'][relevant_indices]
                    similarities = cosine_similarity(query_embedding, relevant_embeddings)[0]
                    
                    # Get top_k most similar entries
                    top_indices = np.argsort(similarities)[-top_k:][::-1]
                    results = [relevant_entries[i] for i in top_indices]
                    
                    logger.info(f"📚 Found {len(results)} semantically relevant educational entries")
                    return results
            
            # Fallback to simple filtering
            logger.info(f"📚 Found {len(relevant_entries)} educational entries (no semantic search)")
            return relevant_entries[:top_k]
            
        except Exception as e:
            logger.error(f"❌ Error fetching educational knowledge: {e}")
            return None

    def infer_subject(self, text: str) -> str:
        """Infers the subject from the given text using keyword matching."""
        text_lower = text.lower()
        
        # Math keywords
        math_keywords = ['math', 'algebra', 'geometry', 'equation', 'theorem', 'fraction', 'decimal', 'multiplication', 'division', 'linear', 'function']
        if any(keyword in text_lower for keyword in math_keywords):
            return 'Math'
        
        # Science keywords
        science_keywords = ['science', 'biology', 'physics', 'chemistry', 'ecosystem', 'water cycle', 'photosynthesis', 'energy', 'motion', 'cell', 'atom']
        if any(keyword in text_lower for keyword in science_keywords):
            return 'Science'
        
        # Social studies keywords
        social_keywords = ['history', 'war', 'ancient', 'revolution', 'civil war', 'geography', 'culture', 'government', 'social']
        if any(keyword in text_lower for keyword in social_keywords):
            return 'Social'
        
        # English keywords
        english_keywords = ['english', 'literature', 'grammar', 'writing', 'poem', 'story', 'reading']
        if any(keyword in text_lower for keyword in english_keywords):
            return 'English'
        
        return 'English'  # Default fallback

    async def ask_gemini(self, user_message: str, grade: int, conversation_history: list, retrieved_knowledge: str) -> str:
        """Interacts with the Gemini model to get a response."""
        if not GEMINI_API_KEY or GEMINI_API_KEY == "YOUR_GEMINI_API_KEY_HERE":
            return "❌ Error: Gemini API key not configured. Please set your GEMINI_API_KEY environment variable."
        
        # Construct the prompt for Gemini
        prompt = f"""You are a helpful educational assistant for a {grade}th grade student.

Here is the current conversation history:
{"\n".join([f"{m['role']}: {m['text']}" for m in conversation_history[-5:]])}

Here is some relevant knowledge base information for {grade}th grade:
{retrieved_knowledge if retrieved_knowledge else 'No specific knowledge found in the knowledge base.'}

Based on the conversation history and the provided knowledge, please answer the user's question: "{user_message}"

Please provide a comprehensive and age-appropriate answer for a {grade}th grade student. If the knowledge base doesn't contain specific information, use your general knowledge to provide a helpful educational response.
"""

        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "temperature": 0.7,
                "topK": 40,
                "topP": 0.95,
                "maxOutputTokens": 1024,
            }
        }

        api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"

        try:
            response = requests.post(
                api_url, 
                headers={'Content-Type': 'application/json'}, 
                data=json.dumps(payload),
                timeout=30
            )
            response.raise_for_status()

            result = response.json()

            if result.get('candidates') and result['candidates'][0].get('content') and result['candidates'][0]['content'].get('parts'):
                text = result['candidates'][0]['content']['parts'][0]['text']
                return text
            else:
                logger.warning(f"⚠️ Gemini API response structure unexpected: {result}")
                return "I'm sorry, I couldn't generate a response. Please try again."
                
        except requests.exceptions.Timeout:
            logger.warning("⚠️ Gemini API request timed out")
            return "I'm sorry, the request timed out. Please try again."
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error calling Gemini API: {e}")
            return "I encountered an error while processing your request. Please try again."

    async def process_educational_query(self, user_question: str, user_id: str, grade: int = 8) -> str:
        """
        Processes a user query using RAG for educational content with Gemini integration.

        Args:
            user_question (str): The question from the user.
            user_id (str): A unique identifier for the user/session.
            grade (int): The grade level for the question.

        Returns:
            str: The model's response.
        """
        current_conversation_history = []
        
        # Try to load conversation history from Firebase if available
        if db:
            try:
                conversation_memory_ref = db.collection(f'artifacts/{APP_ID}/users/{user_id}/conversation_memory')
                docs = conversation_memory_ref.order_by('timestamp').limit(10).stream()
                for doc in docs:
                    data = doc.to_dict()
                    if data and 'role' in data and 'text' in data:
                        current_conversation_history.append({'role': data['role'], 'text': data['text']})
                
                if current_conversation_history:
                    logger.info(f"💬 Loaded {len(current_conversation_history)} previous messages for user {user_id}")

            except Exception as e:
                logger.warning(f"⚠️ Error loading conversation memory from Firestore for user {user_id}: {e}")
                current_conversation_history = []
        else:
            logger.info("💬 Using in-memory conversation (Firebase not available)")

        # Add user message to conversation history
        user_message_data = {
            'role': 'user', 
            'text': user_question, 
            'timestamp': firestore.SERVER_TIMESTAMP if db else None, 
            'grade': grade
        }
        current_conversation_history.append({'role': 'user', 'text': user_question})

        # Determine subject from user message
        inferred_subject = self.infer_subject(user_question)
        logger.info(f"🎯 Inferred subject: {inferred_subject}")

        # Fetch relevant educational knowledge
        educational_entries = self.get_educational_knowledge(grade, inferred_subject, user_question, top_k=3)
        
        # Format retrieved knowledge for Gemini
        retrieved_knowledge = ""
        if educational_entries:
            retrieved_knowledge = "\n\n".join([
                f"Chapter: {entry['chapter_name']} - {entry['content']}" 
                for entry in educational_entries
            ])

        # Call Gemini with user message, grade, conversation history, and retrieved knowledge
        gemini_response = await self.ask_gemini(user_question, grade, current_conversation_history, retrieved_knowledge)

        # Add model response to conversation memory
        model_message_data = {
            'role': 'model', 
            'text': gemini_response, 
            'timestamp': firestore.SERVER_TIMESTAMP if db else None, 
            'grade': grade
        }

        # Save to Firebase if available
        if db:
            try:
                conversation_memory_ref = db.collection(f'artifacts/{APP_ID}/users/{user_id}/conversation_memory')
                conversation_memory_ref.add(user_message_data)
                conversation_memory_ref.add(model_message_data)
                logger.info(f"💾 Conversation messages saved to Firestore for user {user_id}")
            except Exception as e:
                logger.warning(f"⚠️ Error saving conversation memory to Firestore for user {user_id}: {e}")
        else:
            logger.info("💾 Conversation not saved (Firebase not available)")

        return gemini_response


# --- Example Usage ---
async def main():
    """Example usage of the enhanced RAG service."""
    try:
        # Initialize the enhanced RAG service
        rag_service = RAGService()
        
        print("\n" + "="*50)
        print("🤖 Enhanced RAG Service Examples")
        print("="*50)

        # Example 1: File-based knowledge base search (if available)
        if rag_service.knowledge_base:
            print("\n--- 📁 File-based Knowledge Base Search ---")
            kb_names = list(rag_service.knowledge_base.keys())
            if kb_names:
                result = rag_service.search_kb("example query", kb_names[0])
                print(f"Search result from {kb_names[0]}: {result}")

        # Example 2: Educational knowledge retrieval
        print("\n--- 📚 Educational Knowledge Retrieval ---")
        educational_content = rag_service.get_educational_knowledge(5, "Science", "ecosystems")
        if educational_content:
            print(f"Found {len(educational_content)} educational entries:")
            for entry in educational_content:
                print(f"- Grade {entry['grade']} {entry['subject']}: {entry['chapter_name']}")

        # Example 3: Educational query processing with Gemini
        print("\n--- 🤖 Educational Query Processing ---")
        test_user_id = "test_user_123"
        
        response = await rag_service.process_educational_query(
            "What are ecosystems and how do they work?", 
            user_id=test_user_id, 
            grade=5
        )
        print(f"🤖 Bot Response: {response}")
        
        print("\n" + "="*50)
        print("✅ All examples completed!")
        
    except Exception as e:
        logger.error(f"❌ Error in main function: {e}")

