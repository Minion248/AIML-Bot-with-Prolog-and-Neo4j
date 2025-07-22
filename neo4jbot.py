import aiml
import os
import json
import re
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from pyswip import Prolog
from neo4j import GraphDatabase
import logging
from memory_system.episodic_memory import EpisodicMemory
from memory_system.sensory_memory import SensoryMemory
from memory_system.motor_memory import MotorMemory
from memory_system.pam_memory import PAMMemory
from memory_system.semantic_memory import SemanticMemory
from memory_system.social_memory import SocialMemory

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


class FamilyChatbot:
    def __init__(self):
        self.BRAIN_FILE = "./pretrained_model/aiml_pretrained_model.dump"
        self.k= aiml.Kernel()
        self.user_log_dir = "./user_logs"
        os.makedirs(self.user_log_dir, exist_ok=True)
        self.current_user = None
        self.prolog = None
        self.driver = None
        self.memory = None

        self._initialize_components()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def _initialize_components(self):
        self._initialize_aiml()
        self._initialize_prolog()
        self._initialize_memories()

    def _initialize_aiml(self):
        if os.path.exists(self.BRAIN_FILE):
            logger.info("Loading brain from dump file...")
            self.k.loadBrain(self.BRAIN_FILE)
            if hasattr(self.k, '_categories'):
                logger.info(f"Brain loaded with {len(self.k._categories)} categories")
            elif hasattr(self.k, 'num_categories'):
                logger.info(f"Brain loaded with {self.k.num_categories} categories")
            else:
                logger.info("Brain loaded successfully")
        else:
            logger.info("Bootstrapping AIML kernel from scratch...")
            aiml_files = [
                "./pretrained_model/learningFileList.aiml",
                "./data/conversation.aiml",
                "./data/ai.aiml",
                "./data/food.aiml",
                "./data/knowledge.aiml",
                "./data/user_dob_facts.aiml",
                "./data/user_gender_facts.aiml",
                "./data/user_married_facts.aiml",
                "./data/user_query.aiml",
                "./data/user_relations_facts.aiml",
                "./data/words.aiml",
                "./data/sensory.aiml",
                "./data/semantic.aiml",
                "./data/pam.aiml",
                "./data/motor.aiml",
                "./ data/temperature.aiml"
                "./data/episodic.aiml"
            ]
            self.k.bootstrap(learnFiles=aiml_files, commands="load aiml")
            self.k.saveBrain(self.BRAIN_FILE)
            if hasattr(self.k, '_categories'):
                logger.info(f"Brain created with {len(self.k._categories)} categories")
            elif hasattr(self.k, 'num_categories'):
                logger.info(f"Brain created with {self.k.num_categories} categories")
            else:
                logger.info("Brain created and saved successfully")

    def _initialize_prolog(self):
        try:
            path = Path("data/family.pl").absolute()
            path_str = str(path).replace('\\', '/')
            self.prolog = Prolog()
            list(self.prolog.query(f"consult('{path_str}')"))
            logger.info("Prolog knowledge base initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Prolog: {e}")
            self.prolog = None

    def _initialize_memories(self):
        try:
            uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
            user = os.getenv("NEO4J_USER", "neo4j")
            password = os.getenv("NEO4J_PASS", "admin@123")

            logger.info(f"Connecting to Neo4j at {uri}...")
            self.driver = GraphDatabase.driver(uri, auth=(user, password))

            with self.driver.session() as session:
                result = session.run("RETURN 1 AS test")
                if result.single()[0] == 1:
                    logger.info("Neo4j connection verified")

            self.memory = type("Memory", (), {})()
            self.memory.episodic = EpisodicMemory(self.driver)
            self.memory.pam = PAMMemory(self.driver)
            self.memory.sensory = SensoryMemory(self.driver)
            self.memory.motor = MotorMemory(self.driver)
            self.memory.semantic = SemanticMemory(self.driver)
            self.memory.social = SocialMemory(self.driver)

            logger.info("All memory systems initialized successfully")
        except Exception as e:
            logger.error(f"Memory system initialization failed: {e}")
            if hasattr(self, 'driver') and self.driver:
                self.driver.close()
            raise

    def _get_user_log_path(self, user_id):
        return os.path.join(self.user_log_dir, f"{user_id}_log.json")

    def save_to_episodic_memory(self, user_id, message, role):
        """Dual storage in JSON and Neo4j"""
        # JSON log
        log_path = self._get_user_log_path(user_id)
        try:
            log = []
            if os.path.exists(log_path):
                with open(log_path, 'r') as f:
                    log = json.load(f)

            entry = {
                "timestamp": datetime.now().isoformat(),
                "role": role,
                "message": message
            }
            log.append(entry)

            with open(log_path, 'w') as f:
                json.dump(log, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save to JSON log: {e}")

        # Neo4j storage
        try:
            sentiment = None
            if role == "user" and hasattr(self.memory, 'pam'):
                sentiment_result = self.memory.pam.analyze_text(message)
                sentiment = sentiment_result.get('sentiment', {})
                sentiment = json.dumps(sentiment) if sentiment else None

            self.memory.episodic.record_interaction(
                user_id=user_id,
                utterance=message,
                role=role,
                sentiment=sentiment
            )
        except Exception as e:
            logger.error(f"Failed to save to episodic memory: {e}")

    def set_user(self, user_id):
        self.current_user = user_id
        try:
            memories = self.memory.episodic.recall_recent(user_id, 3)
            if memories:
                print("\nRecent interactions:")
                for mem in memories:
                    prefix = "You" if mem['role'] == "user" else "Bot"
                    print(f"{prefix}: {mem['message']}")
        except Exception as e:
            logger.error(f"Failed to recall memories: {e}")

    def process_query(self, user_query):
        if not user_query.strip():
            return "Please say something."

        if self.current_user:
            self.save_to_episodic_memory(self.current_user, user_query, "user")

        aiml_response = self.k.respond(user_query)

        # Enhanced memory recall handling
        if "<memory_recall>" in aiml_response.lower():
            try:
                recall_cmd = re.search(r"<memory_recall>(.*?)</memory_recall>", aiml_response, re.IGNORECASE).group(
                    1).strip()

                # Handle different recall command formats
                if recall_cmd.lower().startswith("last"):
                    try:
                        limit = int(recall_cmd.split()[-1])
                        memories = self.memory.episodic.recall_recent(self.current_user,
                                                                      limit) if self.current_user else []
                    except (ValueError, IndexError):
                        memories = self.memory.episodic.recall_recent(self.current_user, 5) if self.current_user else []
                else:
                    memories = self.memory.episodic.recall_related(self.current_user, recall_cmd,
                                                                   5) if self.current_user else []

                # Format the response based on the original AIML template
                if "Here's our recent conversation history:" in aiml_response:
                    # Format for "TELL ME WHAT WE DISCUSSED" pattern
                    if memories:
                        memory_list = []
                        for mem in memories:
                            prefix = "You" if mem['role'] == "user" else "Bot"
                            memory_list.append(f"{prefix}: {mem['message']}")
                        memory_text = "\n".join(memory_list)
                    else:
                        memory_text = "I don't have any recent conversations to recall."
                else:
                    # Default format for other memory recall patterns
                    if memories:
                        memory_list = []
                        for i, memory in enumerate(memories, 1):
                            prefix = "You" if memory['role'] == "user" else "I"
                            memory_list.append(f"{i}. {prefix} said: {memory['message']}")
                        memory_text = "\n".join(memory_list)
                    else:
                        memory_text = "I don't have any memories about that."

                aiml_response = re.sub(
                    r"<memory_recall>.*?</memory_recall>",
                    memory_text,
                    aiml_response,
                    flags=re.IGNORECASE
                )
            except Exception as e:
                logger.error(f"Memory recall failed: {e}")
                aiml_response = re.sub(
                    r"<memory_recall>.*?</memory_recall>",
                    "I had trouble accessing my memories.",
                    aiml_response,
                    flags=re.IGNORECASE
                )

        if not aiml_response.strip() or "is the" in aiml_response:
            match = re.match(r"who is (?:the )?(father|mother|parent|son|daughter) of ([a-zA-Z]+)", user_query.lower())
            if match:
                relation, person = match.groups()
                names = self.query_prolog(f"{relation}_of", person)
                if names:
                    aiml_response = f"{names[0]} is the {relation} of {person.capitalize()}." if len(names) == 1 else \
                        f"The {relation} of {person.capitalize()} could be: {', '.join(names)}"
                else:
                    aiml_response = f"I don't know who the {relation} of {person.capitalize()} is."

        if self.current_user:
            self.save_to_episodic_memory(self.current_user, aiml_response, "bot")

        return aiml_response

    def query_prolog(self, relation, person):
        if not self.prolog:
            return None
        try:
            query = f"{relation}(X, {person.lower()})"
            results = list(self.prolog.query(query))
            return [result['X'].capitalize() for result in results] if results else None
        except Exception as e:
            logger.error(f"Prolog query failed: {e}")
            return None

    def close(self):
        try:
            if hasattr(self, 'memory'):
                for component in ['episodic', 'pam', 'sensory', 'motor', 'semantic', 'social']:
                    if hasattr(self.memory, component):
                        try:
                            getattr(self.memory, component).close()
                        except Exception as e:
                            logger.error(f"Error closing {component}: {e}")

            if hasattr(self, 'driver') and self.driver:
                self.driver.close()
                logger.info("Neo4j driver closed")

            if hasattr(self, 'prolog'):
                del self.prolog
                logger.info("Prolog engine released")

            logger.info("All resources cleaned up")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


if __name__ == "__main__":
    try:
        with FamilyChatbot() as bot:
            user_id = input("Enter user ID: ").strip()
            if not user_id:
                print("User ID required")
                exit()

            bot.set_user(user_id)

            print("\nChat with the bot. Type 'exit' to quit.")
            while True:
                try:
                    query = input("You: ").strip()
                    if not query:
                        continue
                    if query.lower() == "exit":
                        break

                    response = bot.process_query(query)
                    print("Bot:", response)

                except KeyboardInterrupt:
                    print("\nGoodbye!")
                    break
                except Exception as e:
                    print(f"Error: {e}")
                    continue
    except Exception as e:
        logger.error(f"Chatbot initialization failed: {e}")
        print("Failed to start chatbot. Please check logs for details.")