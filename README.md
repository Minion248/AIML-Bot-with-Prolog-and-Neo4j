
# 🤖 AIML Bot

AIML Bot is an intelligent virtual assistant framework that combines AIML (Artificial Intelligence Markup Language), Prolog for symbolic reasoning, and Neo4j for storing and querying different types of memory (semantic, episodic, social, etc.). It also features sensor integration (IoT) and user authentication via Flask.

## 📁 Project Structure

```
AIML Bot/
│
├── data/                    # AIML files for chatbot conversation
├── memory_system/          # Semantic, Episodic, Social memory code using Neo4j
├── pretrained_model/       # Preloaded AIML model dump
├── loginpage/              # Login system frontend php using XAMPP (HTML/CSS)
├── templates/              # Flask templates
├── user_logs/              # Stores user chat logs
│
├── neo4japp.py             # Main Flask app to run the bot
├── neo4jbot.py             # Backend logic for Neo4j integration
├── sensor_server.py        # Sensor (IoT) Flask API for temperature data
├── family.pl               # Prolog knowledge base (family relationships)
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (Neo4j credentials)
```

## 🧠 Features

- ✅ AIML-powered chatbot for predefined conversation patterns
- ✅ Prolog integration to handle symbolic reasoning (e.g. family tree)
- ✅ Neo4j-powered memory types:
  - Semantic Memory
  - Episodic Memory
  - Social Memory
  - PAM (Procedural Attachment Memory)
- ✅ Sensor data intake via Flask route (`sensor_server.py`)
- ✅ User authentication via HTML login page

## ⚙️ Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/AIML-Bot.git
cd AIML-Bot/AIML\ Bot
```

### 2. Install Dependencies

Make sure you have Python 3.10 or 3.11 installed. Then:

```bash
pip install -r requirements.txt
```

### 3. Configure Neo4j and .env

Create a `.env` file (already included) and update it with your Neo4j credentials:

```ini
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASS=your_password
```

> Ensure your Neo4j desktop/server is running and accessible.

### 4. Run the Chatbot Server

```bash
python neo4japp.py
```

Open browser and go to: [http://127.0.0.1:5000](http://127.0.0.1:5000)

### 5. (Optional) Enable IoT Temperature Sensor Server

To receive sensor data via HTTP POST:

```bash
python sensor_server.py
```

Send sensor data via:
```bash
curl -X POST http://127.0.0.1:5050/update_sensor      -H "Content-Type: application/json"      -d "{\"temp\": 31}"
```

### 6. AIML Files

Edit or add more `.aiml` files in the `data/` directory to expand the bot's knowledge base.

### 7. Prolog Reasoning

Modify `family.pl` to extend logical relationships:

```prolog
father(john, mike).
mother(sara, mike).
parent(X, Y) :- father(X, Y).
parent(X, Y) :- mother(X, Y).
```

## 🧪 Testing

Make sure the following endpoints work:

- ✅ `/` → Home/Login Page
- ✅ `/get` → Chatbot interaction
- ✅ `/update_sensor` → Sensor data endpoint

## 🧑‍💻 Contributors

- Sara Akmal (Project Lead)

## 📜 License

This project is open-source and available under the MIT License.
