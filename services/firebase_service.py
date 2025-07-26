import os
import logging
from datetime import datetime
from google.cloud import firestore
from config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FirebaseService:
    """Handles all interactions with Google Cloud Firestore."""
    
    def __init__(self):
        try:
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'firebase_service_account.json'
            self.db = firestore.Client(project=Config.FIREBASE_PROJECT_ID)
            logger.info("✅ Firebase Firestore service initialized successfully.")
        except Exception as e:
            logger.critical(f"🚨 CRITICAL: Failed to initialize Firestore. Error: {e}")
            raise

    def add_document(self, collection_name: str, data: dict, document_id: str = None):
        """Adds or updates a document in a specified collection."""
        try:
            collection_ref = self.db.collection(collection_name)
            data['updated_at'] = datetime.utcnow()
            
            if document_id:
                doc_ref = collection_ref.document(document_id)
                doc_ref.set(data, merge=True)
            else:
                data['created_at'] = datetime.utcnow()
                doc_ref = collection_ref.add(data)[1]
            
            logger.info(f"Document {doc_ref.id} saved in {collection_name}.")
            return doc_ref.id
        except Exception as e:
            logger.error(f"Error saving document to {collection_name}: {e}")
            return None

    def get_user_by_email(self, email: str):
        """
        Retrieves a single user document from the 'users' collection by their email.
        """
        try:
            # Get a reference to the 'users' collection
            users_ref = self.db.collection('users')
            
            # Create a query to find documents where the 'email' field matches
            query = users_ref.where('email', '==', email).limit(1)
            
            # Execute the query
            results = query.stream()

            # Loop through results (should be one at most) and return the data
            for doc in results:
                user_data = doc.to_dict()
                user_data['id'] = doc.id # Attach the document ID
                return user_data
            
            # If the loop completes without finding a document, no user was found
            return None
        except Exception as e:
            logger.error(f"Error getting user by email '{email}': {e}")
            return None