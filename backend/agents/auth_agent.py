# backend/agents/auth_agent.py

from flask import Blueprint, request, jsonify
from passlib.hash import pbkdf2_sha256
from firebase_admin import firestore
from datetime import datetime, timedelta, timezone

auth_bp = Blueprint('auth_agent', __name__)

@auth_bp.route('/auth/signup', methods=['POST'])
def signup():
    db = firestore.client()
    data = request.json
    email, password, name, age = data.get('email'), data.get('password'), data.get('name'), data.get('age')
    if not all([email, password, name, age]): return jsonify({"error": "Missing required fields"}), 400
    if db.collection('registered_users').where('email', '==', email).get(): return jsonify({"error": "User with this email already exists"}), 409
    
    hashed_password = pbkdf2_sha256.hash(password)
    user_data = {"name": name, "age": age, "email": email, "password_hash": hashed_password}
    user_ref, _ = db.collection('registered_users').add(user_data)
    
    # Create the persistent user state document upon signup
    db.collection('user_states').document(user_ref.id).set({
        "metrics": {"anxiety": 50, "depression": 50, "stress": 50},
        "last_updated": firestore.SERVER_TIMESTAMP
    })
    
    return jsonify({"message": "User created successfully"}), 201

@auth_bp.route('/auth/login', methods=['POST'])
def login():
    db = firestore.client()
    data = request.json
    email, password = data.get('email'), data.get('password')
    if not email or not password: return jsonify({"error": "Email and password are required"}), 400
    
    query_result = db.collection('registered_users').where('email', '==', email).limit(1).get()
    if not query_result: return jsonify({"error": "Invalid credentials"}), 401
    
    user_doc = query_result[0]
    user_data = user_doc.to_dict()

    if pbkdf2_sha256.verify(password, user_data.get('password_hash')):
        user_id = user_doc.id
        
        has_recent_screening = False
        user_metrics = {"anxiety": 50, "depression": 50, "stress": 50} # Default metrics

        # Check if the user_states document exists before trying to read from it.
        user_state_ref = db.collection('user_states').document(user_id)
        user_state_doc = user_state_ref.get()

        if user_state_doc.exists:
            user_state_data = user_state_doc.to_dict()
            user_metrics = user_state_data.get('metrics', user_metrics) # Use saved metrics if they exist
            last_screening_time = user_state_data.get('last_screening_timestamp')
            
            if last_screening_time and (datetime.now(timezone.utc) - last_screening_time < timedelta(days=7)):
                has_recent_screening = True
                print(f"User {user_id} has a recent screening. Skipping Kai.")
        
        # Return user data in the format expected by frontend
        return jsonify({
            "message": "Login successful",
            "user": {
                "id": user_id,
                "name": user_data.get('name'),
                "age": user_data.get('age'),
                "email": user_data.get('email'),
                "metrics": user_metrics,
                "region": "GLOBAL"
            },
            "hasRecentScreening": has_recent_screening
        })
    else:
        return jsonify({"error": "Invalid credentials"}), 401

@auth_bp.route('/auth/getMetrics', methods=['GET'])
def get_metrics():
    db = firestore.client()
    # Get user ID from query parameters or headers
    user_id = request.args.get('userId') or request.headers.get('X-User-ID')
    
    if not user_id:
        return jsonify({"error": "User ID is required"}), 400
    
    try:
        user_state_ref = db.collection('user_states').document(user_id)
        user_state_doc = user_state_ref.get()
        
        if user_state_doc.exists:
            user_state_data = user_state_doc.to_dict()
            metrics = user_state_data.get('metrics', {"anxiety": 50, "depression": 50, "stress": 50})
            return jsonify({"metrics": metrics})
        else:
            # Return default metrics if no user state exists
            return jsonify({"metrics": {"anxiety": 50, "depression": 50, "stress": 50}})
    except Exception as e:
        print(f"Error getting metrics for user {user_id}: {e}")
        return jsonify({"error": "Failed to get metrics"}), 500