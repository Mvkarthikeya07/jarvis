import time
import logging

logger = logging.getLogger(__name__)

class Memory:
    def __init__(self):
        self.conversations = []
        self.session_start = time.time()

    def add_conversation(self, user_input, response=None):
        """Store conversation history"""
        self.conversations.append({
            'input': user_input,
            'response': response,
            'timestamp': time.time()
        })

    def get_recent_context(self, count=3):
        """Get recent conversation context"""
        return self.conversations[-count:]