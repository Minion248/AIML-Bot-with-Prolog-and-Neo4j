from .sensory_memory import SensoryMemory
from .motor_memory import MotorMemory
from .pam_memory import PAMMemory
from .semantic_memory import SemanticMemory
from .social_memory import SocialMemory
from .episodic_memory import EpisodicMemory  # New import
from dotenv import load_dotenv
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

class MemorySystem:
    def __init__(self, uri=None, user=None, password=None):
        self.uri = uri or os.getenv("NEO4J_URI")
        self.user = user or os.getenv("NEO4J_USER")
        self.password = password or os.getenv("NEO4J_PASS")

        if not all([self.uri, self.user, self.password]):
            raise ValueError("Missing Neo4j credentials. Provide via .env or constructor")

        try:
            # Initialize all memory subsystems
            self.sensory = SensoryMemory(self.uri, self.user, self.password)
            self.motor = MotorMemory(self.uri, self.user, self.password)
            self.pam = PAMMemory(self.uri, self.user, self.password)
            self.semantic = SemanticMemory(self.uri, self.user, self.password)
            self.social = SocialMemory(self.uri, self.user, self.password)
            self.episodic = EpisodicMemory(self.uri, self.user, self.password)  # New memory system
            logger.info("All memory systems initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing memory systems: {e}")
            raise

    def close(self):
        """Close all Neo4j connections"""
        self.sensory.driver.close()
        self.motor.driver.close()
        self.pam.driver.close()
        self.semantic.driver.close()
        self.social.driver.close()
        self.episodic.driver.close()  # Close episodic memory connection