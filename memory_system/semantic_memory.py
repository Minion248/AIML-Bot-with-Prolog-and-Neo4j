from neo4j import GraphDatabase
import logging

logger = logging.getLogger(__name__)


class SemanticMemory:
    def __init__(self, driver):
        """Initialize Semantic Memory system with existing Neo4j driver.

        Args:
            driver: Neo4j driver instance (GraphDatabase.driver)
        """
        if not hasattr(driver, 'session'):
            raise ValueError("Driver must be a Neo4j GraphDatabase driver instance")

        self.driver = driver
        self._initialize_schema()
        logger.info("SemanticMemory initialized successfully")

    def _initialize_schema(self):
        """Initialize database constraints and indexes"""
        try:
            with self.driver.session() as session:
                session.run("""
                    CREATE CONSTRAINT IF NOT EXISTS 
                    FOR (s:Subject) REQUIRE s.name IS UNIQUE
                """)
                session.run("""
                    CREATE INDEX IF NOT EXISTS 
                    FOR (f:Fact) ON (f.content)
                """)
                session.run("""
                    CREATE INDEX IF NOT EXISTS 
                    FOR (m:Memory) ON (m.memory_type)
                """)
            logger.debug("SemanticMemory schema initialized")
        except Exception as e:
            logger.error(f"Schema initialization failed: {e}")
            raise

    def add_fact(self, subject, description):
        """Store a semantic fact in the knowledge graph."""
        try:
            with self.driver.session() as session:
                session.run("""
                    MERGE (s:Subject {name: $subject})
                    SET s.description = $description,
                        s:Memory,
                        s.memory_type = 'semantic'
                    MERGE (f:Fact {content: $description})
                    SET f:Memory,
                        f.memory_type = 'semantic'
                    MERGE (s)-[:HAS_FACT]->(f)
                """, subject=subject, description=description)
            logger.info(f"Stored semantic fact: {subject} - {description}")
        except Exception as e:
            logger.error(f"Failed to add fact: {e}")
            raise

    def get_fact(self, subject):
        """Retrieve a specific fact by subject."""
        try:
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (s:Subject {name: $subject})
                    RETURN s.description AS desc
                """, subject=subject)
                record = result.single()
                return record["desc"] if record else None
        except Exception as e:
            logger.error(f"Failed to get fact: {e}")
            return None

    def get_facts(self, subject=None):
        """Get multiple facts with optional filtering."""
        try:
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (s:Subject)
                    WHERE $subject IS NULL OR s.name = $subject
                    RETURN s.name AS subject, s.description AS description
                    ORDER BY s.name
                """, subject=subject)
                return [dict(record) for record in result]
        except Exception as e:
            logger.error(f"Failed to get facts: {e}")
            return []

    def visualize_semantic_memories(self):
        """Visualize semantic memories in Neo4j."""
        try:
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (s:Subject)-[r:HAS_FACT]->(f:Fact)
                    WHERE s:Memory AND f:Memory
                    RETURN s, r, f
                    LIMIT 50
                """)
                return [dict(record) for record in result]
        except Exception as e:
            logger.error(f"Failed to visualize memories: {e}")
            return []

    def close(self):
        """Close the Neo4j driver connection."""
        try:
            if hasattr(self, 'driver') and self.driver:
                self.driver.close()
                logger.info("SemanticMemory connection closed")
        except Exception as e:
            logger.error(f"Error closing connection: {e}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()