from flask import Flask, request, jsonify, render_template
import firebase_admin
from firebase_admin import credentials, firestore
import json
import os

app = Flask(__name__, template_folder="../templates")  # template folder is one level up if needed

# ✅ Initialize Firebase Admin SDK
try:
    # Local environment
    cred = credentials.Certificate("serviceAccountKey.json")
except FileNotFoundError:
    # Render environment
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

# 🎯 Screening questions
SCREENING_QUESTIONS = [
    {"id": "q1", "text": "Over the last 2 weeks, how often have you been bothered by having little interest or pleasure in doing things?"},
    {"id": "q2", "text": "Over the last 2 weeks, how often have you been bothered by feeling down, depressed, or hopeless?"},
    {"id": "q3", "text": "Trouble falling or staying asleep, or sleeping too much?"},
    {"id": "q4", "text": "Feeling tired or having little energy?"},
    {"id": "q5", "text": "Poor appetite or overeating?"},
    {"id": "q6", "text": "Feeling bad about yourself — or that you are a failure or have let yourself or your family down?"},
    {"id": "q7", "text": "Trouble concentrating on things, such as reading the newspaper or watching television?"},
    {"id": "q8", "text": "Moving or speaking so slowly that other people could have noticed? Or the opposite — being so fidgety or restless that you have been moving around a lot more than usual?"},
    {"id": "q9", "text": "Thoughts that you would be better off dead or of hurting yourself in some way?"}
]

RESPONSE_OPTIONS = ["Not at all", "Several days", "More than half the days", "Nearly every day"]

# 🔁 PHQ-9 Screening Endpoint
@app.route('/kai/screening', methods=['POST'])
def handle_screening():
    data = request.json
    user_id = data.get('userId')
    answer_index = data.get('answerIndex')  # Optional

    if not user_id:
        return jsonify({"error": "userId is required"}), 400

    user_ref = db.collection('users').document(user_id)
    user_doc = user_ref.get()

    # First-time user
    if not user_doc.exists:
        user_ref.set({'currentQuestionIndex': 0, 'scores': {}})
        current_question_index = 0
    else:
        user_data = user_doc.to_dict()
        current_question_index = user_data.get('currentQuestionIndex', 0)

    # Save previous answer (if sent)
    if answer_index is not None and 0 <= current_question_index < len(SCREENING_QUESTIONS):
        question_id = SCREENING_QUESTIONS[current_question_index]['id']
        user_ref.update({f'scores.{question_id}': answer_index})

    # Move to next question
    current_question_index += 1

    # Completed screening
    if current_question_index >= len(SCREENING_QUESTIONS):
        user_ref.update({'currentQuestionIndex': current_question_index})
        return jsonify({
            "message": "Thank you for completing the screening. We will now connect you with Elara."
        })

    # Next question
    next_question = SCREENING_QUESTIONS[current_question_index]
    user_ref.update({'currentQuestionIndex': current_question_index})

    return jsonify({
        "question": next_question['text'],
        "options": RESPONSE_OPTIONS
    })

# 🧪 HTML Test Page Route
@app.route('/test')
def test_page():
    return render_template("test.html")

# Local run only
if __name__ == '__main__':
    app.run(debug=True)
