# backend/agents/kai_agent.py

from flask import Blueprint, request, jsonify, Response
from firebase_admin import firestore
import json
from datetime import datetime, timedelta
from .agent_data import BASE_QUESTIONS, AGE_SPECIFIC_QUESTIONS, RESPONSE_OPTIONS

kai_bp = Blueprint('kai_agent', __name__)

def assess_user_metrics(scores):
    """
    ENHANCED 0-100 METRIC SYSTEM: Calculates comprehensive user state with multiple parameters.
    Missing or None values are treated as 0.
    """
    if not scores:
        return {
            "depression": 40, 
            "anxiety": 40, 
            "stress": 40,
            "social_anxiety": 30,
            "self_worth": 60,
            "sleep_quality": 50,
            "energy_level": 50,
            "coping_skills": 50,
            "social_support": 50,
            "life_satisfaction": 50
        }

    # Ensure all score values are numeric (default to 0 if None or missing)
    safe_scores = {k: (v if isinstance(v, (int, float)) else 0) for k, v in scores.items()}

    total_score = sum(safe_scores.values())
    num_questions = len(safe_scores)
    
    # Normalize score to a 0-100 scale (max score is num_questions * 3)
    normalized_score = min((total_score / (num_questions * 3)) * 100, 100)
    
    # Enhanced metrics calculation with more parameters
    metrics = {
        # Core mental health metrics
        "depression": int(normalized_score * 0.8),
        "anxiety": int(normalized_score * 0.6),
        "stress": int(normalized_score * 0.5),
        
        # Social and interpersonal metrics
        "social_anxiety": int(normalized_score * 0.4),
        "social_support": max(0, 100 - int(normalized_score * 0.3)),
        
        # Self-perception metrics
        "self_worth": max(0, 100 - int(normalized_score * 0.7)),
        "life_satisfaction": max(0, 100 - int(normalized_score * 0.6)),
        
        # Physical and lifestyle metrics
        "sleep_quality": max(0, 100 - int(normalized_score * 0.4)),
        "energy_level": max(0, 100 - int(normalized_score * 0.5)),
        
        # Coping and resilience metrics
        "coping_skills": max(0, 100 - int(normalized_score * 0.6)),
        "resilience": max(0, 100 - int(normalized_score * 0.5))
    }
    
    # Ensure all values are within 0-100 range
    for key in metrics:
        metrics[key] = max(0, min(100, metrics[key]))
    
    # Calculate overall mental health score
    negative_metrics = ["depression", "anxiety", "stress", "social_anxiety"]
    positive_metrics = ["self_worth", "life_satisfaction", "social_support", "coping_skills", "resilience"]
    
    negative_avg = sum(metrics[metric] for metric in negative_metrics) / len(negative_metrics)
    positive_avg = sum(metrics[metric] for metric in positive_metrics) / len(positive_metrics)
    
    # Overall score is inverse of negative metrics plus positive metrics
    overall_score = max(0, min(100, (100 - negative_avg + positive_avg) / 2))
    metrics["overall_mental_health"] = int(overall_score)
    
    # Determine mental health status
    if overall_score >= 80:
        status = "excellent"
    elif overall_score >= 60:
        status = "good"
    elif overall_score >= 40:
        status = "moderate"
    elif overall_score >= 20:
        status = "concerning"
    else:
        status = "critical"
    
    metrics["mental_health_status"] = status
    
    return metrics

def can_take_screening(db, user_id):
    """
    Check if user can take a new screening (24 hours since last screening).
    Returns True if user can take screening, False otherwise.
    """
    try:
        user_state_ref = db.collection('user_states').document(user_id)
        user_state_doc = user_state_ref.get()
        
        if not user_state_doc.exists:
            return True  # New user, can take screening
        
        last_screening = user_state_doc.to_dict().get('last_screening_timestamp')
        if not last_screening:
            return True  # No previous screening, can take screening
        
        # Check if 24 hours have passed since last screening
        if isinstance(last_screening, datetime):
            time_since_screening = datetime.now() - last_screening
            return time_since_screening >= timedelta(hours=24)
        else:
            return True
            
    except Exception as e:
        print(f"Error checking screening eligibility for user {user_id}: {e}")
        return True  # Allow screening if there's an error

def get_questions_for_user(age, orion_insights=None):
    """
    Builds a personalized question list based on age and insights from Orion.
    """
    questions = list(BASE_QUESTIONS)
    
    if 6 <= age <= 18: age_group = "6-18"
    elif 18 < age <= 30: age_group = "18-30"
    elif 30 < age <= 60: age_group = "30-60"
    elif age > 60: age_group = "60+"
    else: age_group = None
    
    if age_group:
        questions.extend(AGE_SPECIFIC_QUESTIONS.get(age_group, []))
        
    if orion_insights:
        print(f"Orion insights found: {orion_insights}. Tailoring Kai questions.")
        if 'social_anxiety' in orion_insights:
            questions.append({"id": "orion_q1", "text": "Lately, how often have you felt worried about what other people think of you?"})
        if 'low_self_worth' in orion_insights:
            questions.append({"id": "orion_q2", "text": "How often have you been feeling critical of yourself or that you aren't good enough?"})
    
    return questions

@kai_bp.route('/kai/screening', methods=['POST'])
def handle_screening():
    db = firestore.client()
    data = request.json
    user_id, user_age = data.get('userId'), data.get('userAge')
    if not user_id or not user_age: 
        return jsonify({"error": "userId and userAge are required"}), 400
    
    try:
        if not can_take_screening(db, user_id):
            return jsonify({
                "error": "screening_cooldown",
                "message": "You can take a new screening every 24 hours. Please try again later."
            }), 429
        
        user_state_ref = db.collection('user_states').document(user_id)
        user_state_doc = user_state_ref.get()
        
        orion_insights = user_state_doc.to_dict().get('orion_insights', []) if user_state_doc.exists else []
        questions = get_questions_for_user(user_age, orion_insights)
        
        is_starting = 'answerIndex' not in data
        
        screening_session_ref = db.collection('screening_sessions').document(user_id)
        screening_session_doc = screening_session_ref.get()

        if not screening_session_doc.exists or is_starting:
            index = 0
            screening_session_ref.set({'currentQuestionIndex': 0, 'scores': {}})
        else:
            screening_data = screening_session_doc.to_dict()
            index = screening_data.get('currentQuestionIndex', 0)
            if index > 0 and index <= len(questions):
                previous_question_id = questions[index - 1]['id']
                # Store answer safely (default 0 if None)
                answer_val = data.get('answerIndex')
                if answer_val is None:
                    answer_val = 0
                screening_session_ref.update({f'scores.{previous_question_id}': answer_val})

        if index >= len(questions):
            screening_session_data = screening_session_ref.get()
            final_scores = screening_session_data.to_dict().get('scores', {}) if screening_session_data.exists else {}
            
            new_metrics = assess_user_metrics(final_scores)
            
            user_state_ref.set({
                "metrics": new_metrics,
                "last_screening_timestamp": firestore.SERVER_TIMESTAMP,
                "last_updated": firestore.SERVER_TIMESTAMP,
                "orion_insights": firestore.DELETE_FIELD
            }, merge=True)

            print(f"Kai assessed and updated user {user_id} metrics: {new_metrics}")
            
            try:
                new_session_ref = db.collection('user_sessions').document()
                new_session_ref.set({
                    "userId": user_id,
                    "startTime": firestore.SERVER_TIMESTAMP
                })
                session_id = new_session_ref.id
            except Exception as e:
                print(f"Error creating session: {e}")
                session_id = "mock_session_id"

            try:
                screening_session_ref.delete()
            except Exception as e:
                print(f"Error deleting screening session: {e}")
            
            response_data = {
                "message": "Thank you for completing your check-in. Let's start a new chat with Elara.",
                "sessionId": session_id
            }
        else:
            response_data = {
                "question": questions[index]['text'], 
                "options": RESPONSE_OPTIONS,
                "currentQuestion": index + 1,
                "totalQuestions": len(questions)
            }
            screening_session_ref.update({'currentQuestionIndex': index + 1})
            
        return Response(response=json.dumps(response_data), status=200, mimetype='application/json')
    
    except Exception as e:
        print(f"Error in Kai screening: {e}")
        return jsonify({"error": "An error occurred during screening"}), 500

@kai_bp.route('/kai/checkScreeningEligibility', methods=['POST'])
def check_screening_eligibility():
    db = firestore.client()
    data = request.json
    user_id = data.get('userId')
    
    if not user_id:
        return jsonify({"error": "userId is required"}), 400
    
    try:
        can_take = can_take_screening(db, user_id)
        
        if can_take:
            return jsonify({
                "eligible": True,
                "message": "You can take a screening now."
            })
        else:
            user_state_ref = db.collection('user_states').document(user_id)
            user_state_doc = user_state_ref.get()
            
            if user_state_doc.exists:
                last_screening = user_state_doc.to_dict().get('last_screening_timestamp')
                if isinstance(last_screening, datetime):
                    next_available = last_screening + timedelta(hours=24)
                    time_remaining = next_available - datetime.now()
                    hours_remaining = max(0, int(time_remaining.total_seconds() / 3600))
                    minutes_remaining = max(0, int((time_remaining.total_seconds() % 3600) / 60))
                    
                    return jsonify({
                        "eligible": False,
                        "message": f"You can take a new screening in {hours_remaining}h {minutes_remaining}m",
                        "next_available": next_available.isoformat()
                    })
            
            return jsonify({
                "eligible": False,
                "message": "You can take a new screening every 24 hours. Please try again later."
            })
            
    except Exception as e:
        print(f"Error checking screening eligibility: {e}")
        return jsonify({"error": "An error occurred while checking eligibility"}), 500
