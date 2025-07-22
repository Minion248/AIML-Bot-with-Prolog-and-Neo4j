from neo4j import GraphDatabase
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class SocialMemory:
    def __init__(self, driver):
        """Initialize Social Memory system with existing Neo4j driver.

        Args:
            driver: Neo4j driver instance (GraphDatabase.driver)
        """
        if not hasattr(driver, 'session'):
            raise ValueError("Driver must be a Neo4j GraphDatabase driver instance")

        self.driver = driver
        self._initialize_schema()
        logger.info("SocialMemory initialized successfully")

    def _initialize_schema(self):
        """Initialize database constraints and indexes"""
        try:
            with self.driver.session() as session:
                session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (u:SocialUser) REQUIRE u.id IS UNIQUE")
                session.run("CREATE INDEX IF NOT EXISTS FOR (p:SocialPost) ON (p.timestamp)")
                session.run("CREATE INDEX IF NOT EXISTS FOR (m:Memory) ON (m.memory_type)")
            logger.debug("SocialMemory schema initialized")
        except Exception as e:
            logger.error(f"Schema initialization failed: {e}")
            raise

    def register_user(self, user_id):
        """Register a new social user"""
        try:
            with self.driver.session() as session:
                session.run("""
                    MERGE (u:SocialUser {id: $user_id})
                    SET u.created_at = datetime(),
                        u:Memory,
                        u.memory_type = 'social'
                """, user_id=user_id)
            logger.info(f"Registered social user {user_id}")
        except Exception as e:
            logger.error(f"Failed to register user: {e}")
            raise

    def log_interaction(self, user_id, message):
        """Log a social interaction"""
        try:
            timestamp = datetime.now().isoformat()
            with self.driver.session() as session:
                session.run("""
                    MERGE (u:SocialUser {id: $user_id})
                    CREATE (m:SocialPost {
                        text: $message,
                        timestamp: $timestamp,
                        memory_type: 'social'
                    })
                    SET m:Memory
                    MERGE (u)-[:POSTED]->(m)
                """, user_id=user_id, message=message, timestamp=timestamp)
            logger.info(f"Logged interaction for user {user_id}")
        except Exception as e:
            logger.error(f"Failed to log interaction: {e}")
            raise

    def get_interaction_count(self, user_id):
        """Get count of interactions for a user"""
        try:
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (u:SocialUser {id: $user_id})-[:POSTED]->(post)
                    RETURN count(post) as count
                """, user_id=user_id)
                return result.single()["count"]
        except Exception as e:
            logger.error(f"Failed to get interaction count: {e}")
            return 0

    def visualize_social_memories(self, user_id=None):
        """Visualize social memories in Neo4j"""
        try:
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (u:SocialUser)-[r:POSTED]->(m)
                    WHERE ($uid IS NULL OR u.id = $uid)
                    AND m:Memory AND m.memory_type = 'social'
                    RETURN u, r, m
                    LIMIT 100
                """, uid=user_id)
                return list(result)
        except Exception as e:
            logger.error(f"Failed to visualize memories: {e}")
            return []

    def get_social_insights(self, user_id):
        """Get social insights for a user"""
        try:
            with self.driver.session() as session:
                stats = session.run("""
                    MATCH (u:SocialUser {id: $user_id})-[:POSTED]->(post)
                    RETURN count(post) as post_count
                """, user_id=user_id).single()

                topics = session.run("""
                    MATCH (u:SocialUser {id: $user_id})-[:POSTED]->(post)
                    RETURN post.text as text, count(*) as freq
                    ORDER BY freq DESC
                    LIMIT 5
                """, user_id=user_id).data()

                return {
                    'post_count': stats["post_count"] if stats else 0,
                    'top_topics': topics
                }
        except Exception as e:
            logger.error(f"Failed to get social insights: {e}")
            return {'post_count': 0, 'top_topics': []}

    def close(self):
        """Close the Neo4j driver connection."""
        try:
            if hasattr(self, 'driver') and self.driver:
                self.driver.close()
                logger.info("SocialMemory connection closed")
        except Exception as e:
            logger.error(f"Error closing connection: {e}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()