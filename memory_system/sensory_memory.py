from neo4j import GraphDatabase
import time
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class SensoryMemory:
    def __init__(self, driver):
        """Initialize Sensory Memory system with existing Neo4j driver.

        Args:
            driver: Neo4j driver instance (GraphDatabase.driver)
        """
        if not hasattr(driver, 'session'):
            raise ValueError("Driver must be a Neo4j GraphDatabase driver instance")

        self.driver = driver
        self.sensory_data = {}
        self.expiration_time = 2.0  # seconds
        self._initialize_schema()
        logger.info("SensoryMemory initialized successfully")

    def _initialize_schema(self):
        """Initialize database constraints and indexes"""
        try:
            with self.driver.session() as session:
                session.run("""
                    CREATE CONSTRAINT IF NOT EXISTS 
                    FOR (s:Sentence) REQUIRE s.timestamp IS UNIQUE
                """)
                session.run("""
                    CREATE INDEX IF NOT EXISTS 
                    FOR (w:Word) ON (w.text)
                """)
                session.run("""
                    CREATE INDEX IF NOT EXISTS 
                    FOR (s:Sentence) ON (s.timestamp)
                """)
            logger.debug("SensoryMemory schema initialized")
        except Exception as e:
            logger.error(f"Schema initialization failed: {e}")
            raise

    def add_input(self, user_id, input_type, data):
        """Store sensory input with sentence-word relationships tied to user"""
        try:
            timestamp = datetime.now().isoformat()
            self.sensory_data[timestamp] = {
                'type': input_type,
                'data': data,
                'expires': time.time() + self.expiration_time
            }

            memory_type = self._classify_input(data)

            with self.driver.session() as session:
                session.run("""
                    MERGE (u:User {id: $user_id})
                    SET u:SensoryUser
                """, user_id=user_id)

                sentence_result = session.run("""
                    MATCH (u:User {id: $user_id})
                    CREATE (s:Sentence {
                        text: $text, 
                        type: $input_type, 
                        memory_type: $memory_type,
                        timestamp: $timestamp
                    })
                    SET s:Sensory, s:Memory
                    MERGE (u)-[:PERCEIVED]->(s)
                    RETURN id(s)
                """, user_id=user_id, text=data, input_type=input_type,
                                              memory_type=memory_type, timestamp=timestamp)
                sentence_id = sentence_result.single()[0]

                words = data.split()
                for i, word in enumerate(words):
                    session.run("""
                        MATCH (s:Sentence) WHERE id(s) = $sentence_id
                        MERGE (w:Word {text: $word})
                        CREATE (s)-[r:CONTAINS {
                            position: $position,
                            timestamp: $timestamp
                        }]->(w)
                    """, sentence_id=sentence_id, word=word.lower(),
                                position=i, timestamp=timestamp)

            return timestamp
        except Exception as e:
            logger.error(f"Failed to add sensory input: {e}")
            raise

    def _classify_input(self, text):
        """Auto-classify sensory input into specific memory types"""
        text_lower = text.lower()
        if any(word in text_lower for word in ['see', 'saw', 'look']):
            return 'visual'
        elif any(word in text_lower for word in ['hear', 'sound', 'listen']):
            return 'auditory'
        return 'sensory'

    def get_sensory_inputs(self, user_id):
        """Get sensory inputs for a user"""
        try:
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (u:User {id: $uid})-[:PERCEIVED]->(s:Sentence)
                    RETURN s.text AS text, s.type AS type, s.timestamp AS timestamp
                    ORDER BY s.timestamp DESC
                """, uid=user_id)
                return [dict(record) for record in result]
        except Exception as e:
            logger.error(f"Failed to get sensory inputs: {e}")
            return []

    def visualize_sensory_memories(self, user_id=None):
        """Visualize sensory memories in Neo4j"""
        try:
            query = """
            MATCH (u:User)-[r:PERCEIVED]->(s:Sentence)-[c:CONTAINS]->(w:Word)
            WHERE $uid IS NULL OR u.id = $uid
            RETURN u, r, s, c, w
            ORDER BY s.timestamp DESC
            LIMIT 50
            """
            with self.driver.session() as session:
                result = session.run(query, uid=user_id)
                return list(result)
        except Exception as e:
            logger.error(f"Failed to visualize memories: {e}")
            return []

    def close(self):
        """Close the Neo4j driver connection."""
        try:
            if hasattr(self, 'driver') and self.driver:
                self.driver.close()
                logger.info("SensoryMemory connection closed")
        except Exception as e:
            logger.error(f"Error closing connection: {e}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()