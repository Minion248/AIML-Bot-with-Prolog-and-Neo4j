import spacy
from textblob import TextBlob
import gender_guesser.detector as gender
from neo4j import GraphDatabase
import logging

logger = logging.getLogger(__name__)

class PAMMemory:
    def __init__(self, driver):
        """Initialize PAM (Perception-Action Memory) system with existing Neo4j driver.

        Args:
            driver: Neo4j driver instance (GraphDatabase.driver)
        """
        # Validate driver instance
        if not hasattr(driver, 'session'):
            raise ValueError("Driver must be a Neo4j GraphDatabase driver instance")

        # Initialize NLP components
        try:
            self.nlp = spacy.load("en_core_web_sm")
            self.gender_detector = gender.Detector()
            self.driver = driver
            logger.info("NLP components loaded successfully")
        except Exception as e:
            logger.error(f"Failed to initialize NLP components: {e}")
            raise

        # Initialize database schema
        self._initialize_schema()

    def _initialize_schema(self):
        """Initialize database constraints and indexes"""
        try:
            with self.driver.session() as session:
                # Create constraints
                session.run("""
                    CREATE CONSTRAINT IF NOT EXISTS 
                    FOR (u:User) REQUIRE u.id IS UNIQUE
                """)

                # Create indexes
                session.run("""
                    CREATE INDEX IF NOT EXISTS 
                    FOR (m:Memory) ON (m.memory_type)
                """)
            logger.info("PAM schema initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize PAM schema: {e}")
            raise

    def analyze_text(self, text):
        """Perform comprehensive NLP analysis on text.

        Args:
            text: Input text to analyze

        Returns:
            Dictionary containing:
            - pos_tags: List of (word, POS) tuples
            - entities: List of (text, label) named entities
            - sentiment: Dictionary with polarity, subjectivity and label
            - gender: Detected gender if person found
        """
        try:
            doc = self.nlp(text)
            blob = TextBlob(text)

            # Get first person name for gender detection
            gender_result = "unknown"
            for ent in doc.ents:
                if ent.label_ == "PERSON":
                    first_name = ent.text.split()[0]
                    gender_result = self.gender_detector.get_gender(first_name)
                    break

            return {
                'pos_tags': [(token.text, token.pos_) for token in doc],
                'entities': [(ent.text, ent.label_) for ent in doc.ents],
                'sentiment': {
                    'polarity': blob.sentiment.polarity,
                    'subjectivity': blob.sentiment.subjectivity,
                    'label': self._sentiment_label(blob.sentiment.polarity)
                },
                'gender': gender_result
            }
        except Exception as e:
            logger.error(f"Text analysis failed: {e}")
            return {
                'pos_tags': [],
                'entities': [],
                'sentiment': {
                    'polarity': 0,
                    'subjectivity': 0,
                    'label': 'neutral'
                },
                'gender': 'unknown'
            }

    def store_pam_analysis(self, user_id, analysis):
        """Store complete NLP analysis in Neo4j with memory typing.

        Args:
            user_id: ID of user associated with this analysis
            analysis: Dictionary from analyze_text()
        """
        def _store_analysis(tx, uid, analysis):
            try:
                # Store base user node
                tx.run("MERGE (u:User {id: $uid})", uid=uid)

                # Store sentiment analysis
                tx.run("""
                    MERGE (s:Sentiment {label: $label})
                    SET s.polarity = $polarity,
                        s.subjectivity = $subjectivity,
                        s:Memory,
                        s.memory_type = 'sentiment'
                    MERGE (u)-[:EXPRESSED]->(s)
                """,
                       label=analysis['sentiment']['label'],
                       polarity=analysis['sentiment']['polarity'],
                       subjectivity=analysis['sentiment']['subjectivity'],
                       uid=uid)

                # Store all entities
                for text, label in analysis['entities']:
                    memory_type = self._classify_entity(label)
                    tx.run("""
                        MERGE (e:Entity {text: $text})
                        SET e.type = $type,
                            e:Memory,
                            e.memory_type = $memory_type
                        MERGE (u)-[:MENTIONED]->(e)
                    """,
                           text=text,
                           type=label,
                           memory_type=memory_type,
                           uid=uid)

                # Store words with POS tags
                for word, pos in analysis['pos_tags']:
                    memory_type = self._classify_word(word, pos)
                    tx.run("""
                        MERGE (w:Word {text: $word})
                        SET w.pos = $pos,
                            w:Memory,
                            w.memory_type = $memory_type
                        MERGE (p:POSTag {tag: $pos})
                        MERGE (w)-[:HAS_POS]->(p)
                        MERGE (u)-[:USED]->(w)
                    """,
                           word=word,
                           pos=pos,
                           memory_type=memory_type,
                           uid=uid)

                # Store gender information
                tx.run("""
                    MERGE (g:Gender {value: $gender})
                    MERGE (u)-[:INFERRED_GENDER]->(g)
                """,
                       gender=analysis['gender'],
                       uid=uid)
            except Exception as e:
                logger.error(f"Failed to store analysis in transaction: {e}")
                raise

        try:
            with self.driver.session() as session:
                session.write_transaction(_store_analysis, user_id, analysis)
            logger.debug(f"Stored PAM analysis for user {user_id}")
        except Exception as e:
            logger.error(f"Failed to store PAM analysis: {e}")
            raise

    def _sentiment_label(self, polarity):
        """Convert polarity score to human-readable label"""
        if polarity > 0.1:
            return "positive"
        elif polarity < -0.1:
            return "negative"
        return "neutral"

    def _classify_entity(self, label):
        """Map entity types to memory categories"""
        return {
            'PERSON': 'social',
            'ORG': 'social',
            'DATE': 'temporal',
            'GPE': 'geographic',
            'LOC': 'geographic'
        }.get(label, 'semantic')

    def _classify_word(self, word, pos):
        """Classify words based on POS and semantic meaning"""
        word_lower = word.lower()
        if pos == 'VERB' and word_lower in {'move', 'press', 'turn', 'click', 'go', 'run'}:
            return 'motor'
        elif word_lower in {'see', 'hear', 'feel', 'touch', 'smell', 'taste'}:
            return 'sensory'
        elif pos in ('NOUN', 'PROPN'):
            return 'semantic'
        return 'general'

    def visualize_memory_graph(self, user_id=None):
        """Retrieve memory graph data for visualization.

        Args:
            user_id: Optional user ID to filter results

        Returns:
            List of neo4j records containing nodes and relationships
        """
        query = """
        MATCH (m:Memory)
        WHERE $uid IS NULL OR (:User {id: $uid})-[]->(m)
        OPTIONAL MATCH (m)-[r]->(n)
        RETURN m, r, n
        LIMIT 200
        """
        try:
            with self.driver.session() as session:
                result = list(session.run(query, uid=user_id))
                logger.debug(f"Retrieved {len(result)} memory graph records")
                return result
        except Exception as e:
            logger.error(f"Failed to visualize memory graph: {e}")
            return []

    def close(self):
        """Clean up resources"""
        try:
            if hasattr(self, 'driver') and self.driver:
                self.driver.close()
                logger.info("PAMMemory resources cleaned up")
        except Exception as e:
            logger.error(f"Error closing PAMMemory: {e}")