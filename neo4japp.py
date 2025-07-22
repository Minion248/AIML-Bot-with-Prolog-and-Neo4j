from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import os
from neo4jbot import FamilyChatbot
from dotenv import load_dotenv
from datetime import datetime
import json
import re

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "supersecretkey")

# Initialize chatbot
chatbot = FamilyChatbot()

# Temperature storage with thread safety
from threading import Lock

temp_lock = Lock()
current_temp = None
last_update = None


@app.before_request
def before_request():
    if 'user_id' not in session:
        session['user_id'] = f"guest_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        chatbot.set_user(session['user_id'])
        session['conversation_id'] = str(datetime.now().timestamp())


@app.route("/")
def root():
    return redirect(url_for('start'))


@app.route("/start")
def start():
    return render_template("start.html")


@app.route("/login")
def login():
    user_id = request.args.get("user_id")
    if user_id:
        session['user_id'] = user_id
        chatbot.set_user(user_id)
        try:
            # Initialize all memory systems for the user
            memory_systems = {
                'social': lambda: chatbot.memory.social.register_user(user_id),
                'sensory': lambda: chatbot.memory.sensory.add_input(user_id, "login",
                                                                    f"User logged in at {datetime.now()}"),
                'motor': lambda: chatbot.memory.motor.store_action(user_id, "login"),
                'pam': lambda: chatbot.memory.pam.store_pam_analysis(user_id, {
                    'sentiment': {'label': 'neutral', 'polarity': 0},
                    'entities': [],
                    'pos_tags': [],
                    'gender': 'unknown'
                })
            }

            for system, init_func in memory_systems.items():
                if hasattr(chatbot.memory, system):
                    init_func()

            return redirect(url_for('home'))
        except Exception as e:
            print(f"Error during login initialization: {str(e)}")
    return redirect(url_for('start'))


@app.route("/home")
def home():
    if 'user_id' not in session:
        return redirect(url_for('start'))
    return render_template("hone.html", user_id=session['user_id'])


@app.route("/get")
def get_bot_response():
    if 'user_id' not in session:
        return jsonify({'response': "Please login first"})

    user_id = session['user_id']
    query = request.args.get('msg')

    if not query:
        return jsonify({'response': "Hello! How can I help you today?"})

    try:
        normalized_query = query.upper().strip()
        motor_commands = {
            "STORE GREETING": lambda: handle_motor_greeting(user_id, query),
            "SHOW GREETINGS": lambda: handle_show_greetings(user_id),
            "MOVE FORWARD": lambda: handle_motor_action(user_id, "move_forward"),
            "PERFORM ACTION": lambda: handle_perform_action(user_id, query),
            "HOW DO I WALK": lambda: handle_motor_action(user_id, "walk_instructions"),
            "EXECUTE SEQUENCE": lambda: handle_execute_sequence(user_id, query),
            "TEMPERATURE": lambda: handle_temperature_query()
        }

        for cmd_prefix, handler in motor_commands.items():
            if normalized_query.startswith(cmd_prefix):
                return handler()

        # Process through AIML for non-motor queries
        response = chatbot.process_query(query)
        return jsonify({'response': str(response)})

    except Exception as e:
        print(f"Error processing query '{query}': {str(e)}")
        return jsonify({'response': "Sorry, I encountered an error processing your request."})


# Motor command handlers
def handle_motor_greeting(user_id, query):
    greeting = query[len("STORE GREETING "):].strip()
    if greeting and hasattr(chatbot.memory, 'motor'):
        chatbot.memory.motor.store_greeting(user_id, greeting)
        return jsonify({'response': "Got it. I'll store this greeting pattern in motor memory."})
    return jsonify({'response': "Please provide a valid greeting to store."})


def handle_show_greetings(user_id):
    if hasattr(chatbot.memory, 'motor'):
        greetings = chatbot.memory.motor.recall_greetings(user_id)
        response = "I haven't learned any greetings yet."
        if greetings:
            response = "Here's what I've learned from motor memory:\n" + "\n".join(
                f"{i + 1}. {g}" for i, g in enumerate(greetings))
        return jsonify({'response': response})
    return jsonify({'response': "Motor memory system not available"})


def handle_motor_action(user_id, action):
    if hasattr(chatbot.memory, 'motor'):
        chatbot.memory.motor.store_action(user_id, action)
    return jsonify({'response': f"Command acknowledged: {action.replace('_', ' ')}. Logged in motor memory."})


def handle_perform_action(user_id, query):
    action = query[len("PERFORM ACTION "):].strip().lower()
    if hasattr(chatbot.memory, 'motor'):
        chatbot.memory.motor.store_action(user_id, f"perform_{action}")
    return jsonify({'response': f"Initiating motor sequence for: {action}. Pattern stored."})


def handle_execute_sequence(user_id, query):
    sequence = query[len("EXECUTE SEQUENCE "):].strip().lower()
    if hasattr(chatbot.memory, 'motor'):
        chatbot.memory.motor.store_action(user_id, f"execute_{sequence}")
    return jsonify({'response': f"Executing sequence: {sequence}. Referencing motor memory graph."})


def handle_temperature_query():
    with temp_lock:
        if current_temp is not None:
            return jsonify({'response': f"The current temperature is {current_temp}°C"})
        return jsonify({'response': "Temperature data is currently unavailable"})

##########################################################################
# Temperature endpoints
@app.route('/update_sensor', methods=['POST'])
def update_sensor():
    global current_temp
    try:
        temp = None

        if request.content_type and 'application/json' in request.content_type:
            data = request.get_json(silent=True)
            temp = data.get('temp') if data else None
        else:
            temp = request.form.get('temp')

        if temp is None:
            print("⚠️ Temperature value missing.")
            return jsonify({"error": "Temperature not provided"}), 400

        current_temp = float(temp)

        # 🧠 Set temperature as AIML variable
        if chatbot.current_user:
            chatbot.k.setPredicate("temperature", str(current_temp), chatbot.current_user)

        print(f"✅ Updated temperature: {current_temp}°C")
        return jsonify({"status": "success", "data_received": {"temp": current_temp}})

    except Exception as e:
        print("❌ Error:", e)
        return jsonify({"error": str(e)}), 500



######################################################################
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=True)








"""
without social memory 
from flask import Flask, render_template, request, jsonify, redirect, url_for
import os
from neo4jbot import FamilyChatbot
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Neo4j configuration
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "admin@123")

# Initialize chatbot with memory system
chatbot = FamilyChatbot(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)

@app.route("/")
def root():
    return redirect(url_for('start'))

@app.route("/start")
def start():
    return render_template("start.html")

@app.route("/home")
def home():
    return render_template("homee.html")

@app.route("/get")
def get_bot_response():
    query = request.args.get('msg')
    if query:
        try:
            response = chatbot.process_query(query)
            return jsonify({'response': str(response)})
        except Exception as e:
            print(f"Error processing query: {e}")
            return jsonify({'response': "Sorry, I encountered an error processing your request."})
    return jsonify({'response': "Hello! How can I help you today?"})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
"""