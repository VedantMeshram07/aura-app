from flask import Flask, request, jsonify, render_template
import firebase_admin
from firebase_admin import credentials, firestore
import json
import os
from dotenv import load_dotenv
from ibm_watsonx_ai.foundation_models import ModelInference
from ibm_watsonx_ai.credentials import Credentials

# Load environment variables
load_dotenv()

app = Flask(__name__, template_folder="../templates")

# Firebase Initialization
try:
    cred = credentials.Certificate("serviceAccountKey.json")
except FileNotFoundError:
    firebase_service_account_str = os.getenv('FIREBASE_SERVICE_ACCOUNT_JSON')
    if firebase_service_account_str is None:
        raise ValueError("FIREBASE_SERVICE_ACCOUNT_JSON environment variable not set.")
    firebase_service_account_dict = json.loads(firebase_service_account_str)
    cred = credentials.Certificate(firebase_service_account_dict)

firebase_admin.initialize_app(cred)
db = firestore.client()

# Watsonx Initialization
watsonx_api_key = os.getenv("WATSONX_API_KEY")
watsonx_project_id = os.getenv("WATSONX_PROJECT_ID")
watsonx_creds_dict = {
    "apikey":watsonx_api_key,
    "project_id":watsonx_project_id,
    "url": "https://au-syd.ml.cloud.ibm.com"
}
watsonx_creds = Credentials.from_dict(watsonx_creds_dict)


watsonx_model = ModelInference(
    model_id="ibm/granite-3-8b-instruct",
    credentials=watsonx_creds,
    project_id=watsonx_project_id,
    params={
        "decoding_method": "greedy",
        "max_new_tokens": 100
    }
)

# Root Endpoint
@app.route('/')
def index():
    return "Welcome to Aura Backend! Use /kai/screening to start the screening."

# Kai - Mental Health Screening
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

@app.route('/kai/screening', methods=['POST'])
def handle_screening():
    data = request.json
    user_id = data.get('userId')
    answer_index = data.get('answerIndex')

    if not user_id:
        return jsonify({"error": "userId is required"}), 400

    user_ref = db.collection('users').document(user_id)
    user_doc = user_ref.get()

    if not user_doc.exists or answer_index is None:
        user_ref.set({'currentQuestionIndex': 0, 'scores': {}})
        current_question_index = 0
    else:
        user_data = user_doc.to_dict()
        current_question_index = user_data.get('currentQuestionIndex', 0)
        if current_question_index > 0:
            previous_question_id = SCREENING_QUESTIONS[current_question_index - 1]['id']
            user_ref.update({f'scores.{previous_question_id}': answer_index})

    if current_question_index >= len(SCREENING_QUESTIONS):
        return jsonify({
            "message": "Thank you for completing the screening. You can now chat with Elara."
        })

    next_question = SCREENING_QUESTIONS[current_question_index]
    user_ref.update({'currentQuestionIndex': current_question_index + 1})

    return jsonify({
        "question": next_question['text'],
        "options": RESPONSE_OPTIONS
    })

# Elara - Primary Chat Agent
@app.route('/elara/chat', methods=['POST'])
def handle_chat():
    data = request.json
    user_id = data.get('userId')
    user_message = data.get('message')

    if not user_id or not user_message:
        return jsonify({"error": "userId and message are required"}), 400

    # Aegis - Safety Filter
    AEGIS_TRIGGERS = ['suicide', 'kill myself', 'want to die', 'hurting myself', 'better off dead']
    if any(trigger in user_message.lower() for trigger in AEGIS_TRIGGERS):
        return jsonify({
            "agent": "Aegis",
            "response": "It sounds like you are in significant distress. It is vital to talk to someone right away. Please call or text 988 in the US. Help is available."
        })

    # Orion - Insight Check
    user_ref = db.collection('users').document(user_id)
    user_doc = user_ref.get()
    user_data = user_doc.to_dict()
    insight_flag = user_data.get('insight_flag')

    orion_prompt_injection = ""
    if insight_flag == 'HIGH_PHQ9_SCORE':
        orion_prompt_injection = "SYSTEM NOTE: An automated analysis detected that this user recently scored high on a depression screening. Be extra gentle and supportive, and perhaps check in on how they've been feeling lately."
        user_ref.update({'insight_flag': firestore.DELETE_FIELD})

    # Retrieve last 10 messages from Firestore
    history_ref = db.collection('users').document(user_id).collection('chatHistory').order_by('timestamp').limit(10)
    history_docs = history_ref.stream()

    chat_history = []
    for doc in history_docs:
        doc_data = doc.to_dict()
        chat_history.append(f"User: {doc_data.get('user_message')}")
        chat_history.append(f"Elara: {doc_data.get('ai_response')}")

    # Create prompt with Orion context if available
    prompt = ""
    if orion_prompt_injection:
        prompt += orion_prompt_injection + "\n"
    prompt += "\n".join(chat_history)
    prompt += f"\nUser: {user_message}\nElara:"

    # Generate response from Watsonx
    response = watsonx_model.generate(prompt=prompt)
    ai_response_text = response['results'][0]['generated_text']

    # Save chat to Firestore
    new_chat_doc_ref = db.collection('users').document(user_id).collection('chatHistory').document()
    new_chat_doc_ref.set({
        'user_message': user_message,
        'ai_response': ai_response_text,
        'timestamp': firestore.SERVER_TIMESTAMP
    })

    return jsonify({"agent": "Elara", "response": ai_response_text})

# A simple database of resources for Vero
VERO_RESOURCES = {
    "breathing_exercise_1": {
        "type": "Guided Exercise",
        "title": "Box Breathing",
        "steps": [
            "1. Inhale slowly for 4 seconds.",
            "2. Hold your breath for 4 seconds.",
            "3. Exhale slowly for 4 seconds.",
            "4. Hold the exhale for 4 seconds.",
            "5. Repeat for 2 minutes."
        ]
    }
}

# 🛠️ Vero Resource Endpoint
@app.route('/vero/getResource', methods=['POST'])
def get_resource():
    data = request.json
    action_id = data.get('actionId')

    if not action_id:
        return jsonify({"error": "actionId is required"}), 400

    resource = VERO_RESOURCES.get(action_id)

    if not resource:
        return jsonify({"error": "Resource not found"}), 404
        
    return jsonify(resource)

# Web template test
@app.route('/test')
def test_page():
    return render_template("test.html")

if __name__ == '__main__':
    for rule in app.url_map.iter_rules():
        print(rule.endpoint, rule.methods, rule.rule)

    app.run(debug=True)
