from services.firebase_service import FirebaseService

class FeedbackAgent:
    def __init__(self, firebase_service: FirebaseService):
        self.firebase_service = firebase_service
        self.collection_name = "feedback"

    def submit_feedback(self, feedback_text: str) -> bool:
        """Saves feedback text to Firestore."""
        data = {"feedback": feedback_text}
        doc_id = self.firebase_service.add_document(self.collection_name, data)
        return doc_id is not None