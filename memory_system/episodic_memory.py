from datetime import datetime
import spacy
import uuid
import logging
import json
from neo4j import GraphDatabase

# Load NLP model
nlp = spacy.load("en_core_web_sm")
logger = logging.getLogger(__name__)


class EpisodicMemory:
    def __init__(self, driver):
        """Initialize the episodic memory with existing Neo4j driver

        Args:
            driver: Neo4j driver instance (GraphDatabase.driver)
        """
        if not hasattr(driver, 'session'):
            raise ValueError("Driver must be a Neo4j GraphDatabase driver instance")

        self.driver = driver
        self._initialize_schema()
        logger.info("EpisodicMemory initialized successfully")

    def _initialize_schema(self):
        """Create necessary database constraints and indexes"""
        try:
            with self.driver.session() as session:
                session.run("""
                    CREATE CONSTRAINT IF NOT EXISTS 
                    FOR (e:Episode) REQUIRE e.id IS UNIQUE
                """)
                session.run("""
                    CREATE INDEX IF NOT EXISTS 
                    FOR (e:Episode) ON (e.timestamp)
                """)
                session.run("""
                    CREATE INDEX IF NOT EXISTS 
                    FOR (w:MemoryWord) ON (w.text)
                """)
            logger.debug("EpisodicMemory schema initialized")
        except Exception as e:
            logger.error(f"Schema initialization failed: {e}")
            raise

    def record_interaction(self, user_id, utterance, role, sentiment=None, timestamp=None):
        """Store a conversation episode with sentiment analysis

        Args:
            user_id: ID of the user
            utterance: The text content
            role: 'user' or 'bot'
            sentiment: Optional sentiment data (as JSON string or None)
            timestamp: Optional custom timestamp
        """
        try:
            # Prepare sentiment properties
            sentiment_props = {}
            if sentiment:
                try:
                    # If sentiment is a string, parse it
                    if isinstance(sentiment, str):
                        sentiment_data = json.loads(sentiment)
                    else:
                        sentiment_data = sentiment

                    sentiment_props = {
                        'sentiment_polarity': float(sentiment_data.get('polarity', 0)),
                        'sentiment_subjectivity': float(sentiment_data.get('subjectivity', 0)),
                        'sentiment_label': str(sentiment_data.get('label', 'neutral'))
                    }
                except Exception as e:
                    logger.error(f"Failed to process sentiment data: {e}")

            with self.driver.session() as session:
                # Store the main episode with sentiment properties
                result = session.run("""
                    MERGE (u:User {id: $user_id})
                    CREATE (e:Episode {
                        id: $id,
                        text: $text,
                        role: $role,
                        timestamp: $timestamp
                    })
                    SET e += $sentiment_props
                    MERGE (u)-[:HAS_EPISODE]->(e)
                    RETURN id(e)
                """,
                                     user_id=user_id,
                                     id=str(uuid.uuid4()),
                                     text=utterance,
                                     role=role,
                                     timestamp=timestamp or datetime.now().isoformat(),
                                     sentiment_props=sentiment_props)

                episode_id = result.single()[0]

                # Tokenize and store important words
                doc = nlp(utterance)
                for token in doc:
                    if not token.is_stop and token.pos_ in ("NOUN", "PROPN", "VERB"):
                        session.run("""
                            MATCH (e:Episode) WHERE id(e) = $episode_id
                            MERGE (w:MemoryWord {text: $word})
                            MERGE (e)-[:CONTAINS_WORD]->(w)
                        """,
                                    episode_id=episode_id,
                                    word=token.lemma_.lower())

                logger.debug(f"Recorded interaction for user {user_id}")
        except Exception as e:
            logger.error(f"Failed to record interaction: {e}")
            raise

    def recall_recent(self, user_id, limit=5):
        """Get most recent episodes

        Args:
            user_id: ID of the user
            limit: Maximum number of episodes to return

        Returns:
            List of dictionaries containing message, role, and timestamp
        """
        try:
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (u:User {id: $user_id})-[:HAS_EPISODE]->(e:Episode)
                    RETURN e.text AS message, e.role AS role, e.timestamp AS timestamp
                    ORDER BY e.timestamp DESC
                    LIMIT $limit
                """, user_id=user_id, limit=limit)

                episodes = [dict(record) for record in result]
                logger.debug(f"Recalled {len(episodes)} recent episodes")
                return episodes
        except Exception as e:
            logger.error(f"Failed to recall recent episodes: {e}")
            return []

    def recall_related(self, user_id, query, limit=3):
        """Find related past episodes based on keywords

        Args:
            user_id: ID of the user
            query: Text to find related episodes for
            limit: Maximum number of episodes to return

        Returns:
            List of dictionaries containing message, role, and timestamp
        """
        try:
            keywords = self._extract_keywords(query)
            if not keywords:
                logger.debug("No keywords extracted for recall_related")
                return []

            with self.driver.session() as session:
                result = session.run("""
                    MATCH (u:User {id: $user_id})-[:HAS_EPISODE]->(e:Episode)
                    WHERE ANY(kw IN $keywords WHERE e.text CONTAINS kw)
                    RETURN e.text AS message, e.role AS role, e.timestamp AS timestamp
                    ORDER BY e.timestamp DESC
                    LIMIT $limit
                """, user_id=user_id, keywords=keywords, limit=limit)

                episodes = [dict(record) for record in result]
                logger.debug(f"Recalled {len(episodes)} related episodes")
                return episodes
        except Exception as e:
            logger.error(f"Failed to recall related episodes: {e}")
            return []

    def _extract_keywords(self, text):
        """Extract important keywords from text

        Args:
            text: Input text to analyze

        Returns:
            List of extracted keywords
        """
        try:
            doc = nlp(text)
            keywords = list(set([
                token.lemma_.lower()
                for token in doc
                if not token.is_stop and token.pos_ in ("NOUN", "PROPN", "VERB")
            ]))
            logger.debug(f"Extracted keywords: {keywords}")
            return keywords
        except Exception as e:
            logger.error(f"Failed to extract keywords: {e}")
            return []

    def close(self):
        """Close the Neo4j driver connection"""
        try:
            if hasattr(self, 'driver') and self.driver:
                self.driver.close()
                logger.info("EpisodicMemory connection closed")
        except Exception as e:
            logger.error(f"Error closing EpisodicMemory: {e}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()