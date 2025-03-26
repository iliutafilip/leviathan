from datetime import datetime, timedelta

from google.cloud import firestore
import yaml

with open("configs/db-config.yaml") as file:
    db_config = yaml.safe_load(file)

CREDENTIALS_FILE_PATH = db_config.get("firebase-credentials-path")
COLLECTION_NAME = db_config.get("firebase-collection-name")

DATABASE = firestore.Client.from_service_account_json(CREDENTIALS_FILE_PATH)
SESSION_COLLECTION = DATABASE.collection(COLLECTION_NAME)

class UserHistoryStore:
    """Handles Firestore interactions for storing user session history."""

    @staticmethod
    def load_user_history(username):
        """Retrieve user session history from Firestore."""
        doc = SESSION_COLLECTION.document(username).get()
        if doc.exists:
            return doc.to_dict().get("history", [])
        return []

    @staticmethod
    def save_user_history(username, history):
        """Save user session history to Firestore."""
        SESSION_COLLECTION.document(username).set({"history": history})

    @staticmethod
    def add_to_user_history(username, data):
        """
        Adds user's command and server's response to user's session history to Firestore.
        Updates cleanup_timestamp at every interaction.
        """
        doc_ref = SESSION_COLLECTION.document(username)
        doc = doc_ref.get()

        history = doc.to_dict().get("history", []) if doc.exists else []
        updated_history = history + data

        cleanup_timestamp = datetime.now() + timedelta(hours=1)

        doc_ref.set({
            "history": updated_history,
            "expireAt": cleanup_timestamp
        }, merge=True)

