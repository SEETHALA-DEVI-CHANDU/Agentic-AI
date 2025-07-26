import logging
from passlib.context import CryptContext
from .firebase_service import FirebaseService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AuthService:
    def __init__(self, firebase_service: FirebaseService):
        self.firebase_service = firebase_service
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.create_demo_users()

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        return self.pwd_context.hash(password)

    def create_user(self, email: str, password: str, name: str, school: str):
        """Creates a new user in the database."""
        # Check if user already exists
        if self.firebase_service.get_user_by_email(email):
            logger.warning(f"Signup attempt for existing email: {email}")
            return None

        hashed_password = self.get_password_hash(password)
        user_doc = {
            "email": email,
            "password_hash": hashed_password,
            "name": name,
            "school": school
        }
        # Use email as the document ID to prevent duplicates
        self.firebase_service.add_document('users', user_doc, document_id=email)
        
        # Return the user data (without the hash) for the frontend
        user_doc.pop('password_hash', None)
        return user_doc

    def authenticate_user(self, email: str, password: str):
        # ... (this method remains the same)
        user = self.firebase_service.get_user_by_email(email)
        if not user or not self.verify_password(password, user.get('password_hash', '')):
            return None
        user.pop('password_hash', None)
        return user

    def create_demo_users(self):
        # ... (this method remains the same)
        demo_users = [
            {"email": "teacher.priya@example.com", "password": "password123", "name": "Priya Sharma", "school": "Vidya Mandir School"},
            {"email": "teacher.ramesh@example.com", "password": "password123", "name": "Ramesh Kumar", "school": "Gyanodaya Public School"}
        ]
        for user_data in demo_users:
            if not self.firebase_service.get_user_by_email(user_data["email"]):
                self.create_user(**user_data)