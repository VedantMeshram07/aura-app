# backend/agents/session_agent.py

from flask import Blueprint, request, jsonify
from firebase_admin import firestore

session_bp = Blueprint('session_agent', __name__)

@session_bp.route('/session/feedback', methods=['POST'])
def handle_feedback():
    db = firestore.client()
    data = request.json
    user_id = data.get('userId')
    rating = data.get('rating')
    
    if not user_id or not rating:
        return jsonify({"error": "User ID and rating are required."}), 400
        
    # This feedback will be used by Orion to update the user's long-term state
    db.collection('user_states').document(user_id).collection('feedback_history').add({
        "rating": rating,
        "timestamp": firestore.SERVER_TIMESTAMP
    })
    
    return jsonify({"message": "Feedback received. Thank you!"}), 200