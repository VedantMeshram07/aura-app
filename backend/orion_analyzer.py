# orion_analyzer.py
import firebase_admin
from firebase_admin import credentials, firestore
import json
import os

# This script initializes Firebase independently
try:
    cred = credentials.Certificate("serviceAccountKey.json")
except FileNotFoundError:
    firebase_service_account_str = os.getenv('FIREBASE_SERVICE_ACCOUNT_JSON')
    firebase_service_account_dict = json.loads(firebase_service_account_str)
    cred = credentials.Certificate(firebase_service_account_dict)

# Prevent re-initialization error
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

db = firestore.client()

def analyze_users():
    print("🔭 Starting Orion analysis...")
    users_ref = db.collection('users')
    all_users = users_ref.stream()

    for user in all_users:
        user_id = user.id
        user_data = user.to_dict()
        scores = user_data.get('scores', {})
        
        # Simple Rule: Check if the PHQ-9 score is high (e.g., > 10)
        total_score = sum(v for v in scores.values() if isinstance(v, (int, float)))
        if total_score > 10:
            print(f"Insight found for user {user_id}: High PHQ-9 score ({total_score}).")
            # Write a flag to Firestore for Elara to see
            users_ref.document(user_id).update({
                'insight_flag': 'HIGH_PHQ9_SCORE'
            })

    print("✅ Orion analysis complete.")

if __name__ == '__main__':
    analyze_users()