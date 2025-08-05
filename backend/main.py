from flask import Flask, request, jsonify
import firebase_admin
from firebase_admin import credentials, firestore
import json 
import os

app = Flask(__name__)

# Initialize Firebase Admin SDK
try:
    # Running locally, use the JSON file
    cred = credentials.Certificate("serviceAccountKey.json")
except FileNotFoundError:
    # Running on Render, use the environment variable
    firebase_service_account_str = os.getenv('FIREBASE_SERVICE_ACCOUNT_JSON')
    if firebase_service_account_str is None:
        raise ValueError("FIREBASE_SERVICE_ACCOUNT_JSON environment variable not set.")

    firebase_service_account_dict = json.loads(firebase_service_account_str)
    cred = credentials.Certificate(firebase_service_account_dict)

firebase_admin.initialize_app(cred)
db = firestore.client()

# 🟢 Index route
@app.route('/')
def index():
    return "Welcome to Aura Backend! Use /kai/screening to start the screening."

# 🧠 Screening questions
SCREENING_QUESTIONS = [
    {"id": "q1", "text": "Over the last 2 weeks, how often have you been bothered by having little interest or pleasure in doing things?"},
    {"id": "q2", "text": "Over the last 2 weeks, how often have you been bothered by feeling down, depressed, or hopeless?"},
    # ... Add all 9 PHQ-9 questions here
]

RESPONSE_OPTIONS = ["Not at all", "Several days", "More than half the days", "Nearly every day"]

# 🔁 Screening route
@app.route('/kai/screening', methods=['POST'])
def handle_screening():
    data = request.json
    user_id = data.get('userId')
    answer_index = data.get('answerIndex')  # 0 to 3

    if not user_id:
        return jsonify({"error": "userId is required"}), 400

    user_ref = db.collection('users').document(user_id)
    user_doc = user_ref.get()

    if not user_doc.exists:
        # First-time user
        user_ref.set({'currentQuestionIndex': 0, 'scores': {}})
        current_question_index = 0
    else:
        current_question_index = user_doc.to_dict().get('currentQuestionIndex', 0)

    # Save answer if provided
    if answer_index is not None and current_question_index > 0:
        question_id = SCREENING_QUESTIONS[current_question_index - 1]['id']
        user_ref.update({f'scores.{question_id}': answer_index})

    # End of screening
    if current_question_index >= len(SCREENING_QUESTIONS):
        return jsonify({
            "message": "Thank you for completing the screening. We will now connect you with Elara."
        })

    # Send next question
    next_question = SCREENING_QUESTIONS[current_question_index]
    user_ref.update({'currentQuestionIndex': current_question_index + 1})

    return jsonify({
        "question": next_question['text'],
        "options": RESPONSE_OPTIONS
    })

# 🏁 Run the app
if __name__ == '__main__':
    app.run(debug=True)
