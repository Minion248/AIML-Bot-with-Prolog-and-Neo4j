from neo4j import GraphDatabase
import logging
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


class MotorMemory:
    def __init__(self, driver):
        """Initialize Motor Memory system with existing Neo4j driver.

        Args:
            driver: Neo4j driver instance (GraphDatabase.driver)
        """
        if not hasattr(driver, 'session'):
            raise ValueError("Driver must be a Neo4j GraphDatabase driver instance")

        self.driver = driver
        self._initialize_schema()
        logger.info("MotorMemory initialized successfully")

    def _initialize_schema(self):
        """Create necessary constraints and indexes"""
        try:
            queries = [
                "CREATE CONSTRAINT IF NOT EXISTS FOR (a:Action) REQUIRE a.id IS UNIQUE",
                "CREATE INDEX IF NOT EXISTS FOR (a:Action) ON (a.timestamp)"
            ]

            with self.driver.session() as session:
                for query in queries:
                    session.run(query)
            logger.debug("MotorMemory schema initialized")
        except Exception as e:
            logger.error(f"Schema initialization failed: {e}")
            raise

    def store_action(self, user_id, action_text):
        """Store a motor action in the database."""
        try:
            query = """
            MERGE (u:User {id: $user_id})
            MERGE (a:Action {text: $action_text})
            ON CREATE SET 
                a.id = randomUUID(),
                a.timestamp = datetime(),
                a:Memory,
                a.memory_type = 'motor'
            MERGE (u)-[:PERFORMED]->(a)
            """

            with self.driver.session() as session:
                session.run(query, user_id=user_id, action_text=action_text)
            logger.info(f"Stored motor action for user {user_id}")
        except Exception as e:
            logger.error(f"Failed to store action: {e}")
            raise

    def get_actions(self, user_id):
        """Retrieve actions for a specific user."""
        try:
            query = """
            MATCH (u:User {id: $user_id})-[:PERFORMED]->(a:Action)
            RETURN a.text AS action, a.timestamp AS time
            ORDER BY a.timestamp DESC
            """

            with self.driver.session() as session:
                result = session.run(query, user_id=user_id)
                return [dict(record) for record in result]
        except Exception as e:
            logger.error(f"Failed to get actions: {e}")
            return []

    def visualize_motor_memories(self, user_id=None):
        """Retrieve motor memories for visualization."""
        try:
            query = """
            MATCH (u:User)-[r:PERFORMED]->(a:Action)
            WHERE $user_id IS NULL OR u.id = $user_id
            RETURN u, r, a
            ORDER BY a.timestamp DESC
            LIMIT 50
            """

            with self.driver.session() as session:
                result = session.run(query, user_id=user_id)
                return list(result)
        except Exception as e:
            logger.error(f"Failed to visualize memories: {e}")
            return []

    def close(self):
        """Close the Neo4j driver connection."""
        try:
            if hasattr(self, 'driver') and self.driver:
                self.driver.close()
                logger.info("MotorMemory connection closed")
        except Exception as e:
            logger.error(f"Error closing connection: {e}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()