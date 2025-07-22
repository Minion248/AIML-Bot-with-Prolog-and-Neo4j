from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/update_sensor', methods=['POST'])  # Accept only POST
def update_sensor():
    try:
        data = request.get_json(force=True)  # Ensures it parses JSON
        if not data or 'temp' not in data:
            return jsonify({"error": "Missing 'temp' value"}), 400

        temp = data['temp']
        print(f"✅ Received temperature: {temp}°C")

        # Optional: You can store it in a file or database if needed

        return jsonify({
            "status": "success",
            "data_received": {"temp": temp}
        })

    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=True)
