# backend/agents/auth_agent.py

from flask import Blueprint, request, jsonify
from passlib.hash import pbkdf2_sha256
from firebase_admin import firestore
from datetime import datetime, timedelta, timezone
import uuid

# In-memory fallbacks when Firebase is unavailable
_MEM_USERS_BY_ID = {}
_MEM_USERS_BY_EMAIL = {}
_MEM_USER_STATES = {}


def _get_db_or_none():
    try:
        return firestore.client()
    except Exception:
        return None


def _generate_id() -> str:
    return uuid.uuid4().hex

auth_bp = Blueprint('auth_agent', __name__)

# Default metrics for new users
DEFAULT_METRICS = {"anxiety": 0, "depression": 0, "stress": 0}

@auth_bp.route('/auth/signup', methods=['POST'])
def signup():
    db = _get_db_or_none()
    data = request.json

    email = (data.get('email') or '').strip()
    password = data.get('password')
    name = (data.get('name') or '').strip()
    age = data.get('age')
    region = (data.get('region') or 'GLOBAL').strip().upper()

    # Validation
    try:
        age = int(age)
    except Exception:
        return jsonify({"error": "Age must be a number"}), 400

    if not all([email, password, name, age, region]):
        return jsonify({"error": "Missing required fields"}), 400

    # Check if user already exists
    email_lower = email.lower()
    if db:
        try:
            existing_user = db.collection('registered_users').where('email_lower', '==', email_lower).limit(1).get()
            if existing_user and len(existing_user) > 0:
                return jsonify({"error": "User with this email already exists"}), 409
        except Exception:
            pass
    else:
        if email_lower in _MEM_USERS_BY_EMAIL:
            return jsonify({"error": "User with this email already exists"}), 409

    # Hash password
    hashed_password = pbkdf2_sha256.hash(password)

    # Create user with a new document ID
    if db:
        try:
            user_ref = db.collection('registered_users').document()
            user_ref.set({
                "name": name,
                "age": age,
                "email": email,
                "email_lower": email_lower,
                "password_hash": hashed_password,
                "created_at": firestore.SERVER_TIMESTAMP,
                "region": region
            })

            # Create persistent metrics state
            db.collection('user_states').document(user_ref.id).set({
                "metrics": DEFAULT_METRICS,
                "last_updated": firestore.SERVER_TIMESTAMP,
                "last_screening_timestamp": None
            })

            return jsonify({
                "message": "User created successfully",
                "userId": user_ref.id
            }), 201
        except Exception:
            pass

    # In-memory fallback
    user_id = _generate_id()
    user_doc = {
        "name": name,
        "age": age,
        "email": email,
        "email_lower": email_lower,
        "password_hash": hashed_password,
        "created_at": datetime.now(timezone.utc),
        "region": region
    }
    _MEM_USERS_BY_ID[user_id] = user_doc
    _MEM_USERS_BY_EMAIL[email_lower] = user_id
    _MEM_USER_STATES[user_id] = {
        "metrics": DEFAULT_METRICS.copy(),
        "last_updated": datetime.now(timezone.utc),
        "last_screening_timestamp": None
    }
    return jsonify({"message": "User created successfully", "userId": user_id}), 201


@auth_bp.route('/auth/login', methods=['POST'])
def login():
    db = _get_db_or_none()
    data = request.json
    raw_email = (data.get('email') or '').strip()
    email = raw_email.lower()
    password = data.get('password')

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    # Fetch user (prefer email_lower, fallback to legacy 'email' field)
    user_data = None
    user_id = None
    if db:
        try:
            query_result = db.collection('registered_users').where('email_lower', '==', email).limit(1).get()
            if not query_result:
                # Legacy fallback: try exact email match
                legacy = db.collection('registered_users').where('email', '==', raw_email).limit(1).get()
                if not legacy:
                    return jsonify({"error": "Invalid credentials"}), 401
                user_doc = legacy[0]
                # Backfill email_lower for future logins
                try:
                    db.collection('registered_users').document(user_doc.id).update({"email_lower": email})
                except Exception:
                    pass
            else:
                user_doc = query_result[0]
            user_data = user_doc.to_dict()
            user_id = user_doc.id
        except Exception:
            user_data = None
            user_id = None
    else:
        # In-memory lookup
        if email in _MEM_USERS_BY_EMAIL:
            user_id = _MEM_USERS_BY_EMAIL[email]
            user_data = _MEM_USERS_BY_ID.get(user_id)
        else:
            # Legacy exact email match
            for uid, doc in _MEM_USERS_BY_ID.items():
                if doc.get('email') == raw_email:
                    user_id = uid
                    user_data = doc
                    # Backfill email_lower
                    _MEM_USERS_BY_EMAIL[email] = uid
                    break
            if not user_data:
                return jsonify({"error": "Invalid credentials"}), 401

    # Verify password
    if not pbkdf2_sha256.verify(password, user_data.get('password_hash')):
        return jsonify({"error": "Invalid credentials"}), 401

    # Load metrics
    has_recent_screening = False
    user_metrics = DEFAULT_METRICS.copy()

    if db:
        try:
            user_state_ref = db.collection('user_states').document(user_id)
            user_state_doc = user_state_ref.get()

            if user_state_doc.exists:
                user_state_data = user_state_doc.to_dict()
                user_metrics = user_state_data.get('metrics', DEFAULT_METRICS)

                last_screening_time = user_state_data.get('last_screening_timestamp')
                if last_screening_time and isinstance(last_screening_time, datetime):
                    if (datetime.now(timezone.utc) - last_screening_time) < timedelta(days=7):
                        has_recent_screening = True
        except Exception:
            pass
    else:
        state = _MEM_USER_STATES.get(user_id)
        if state:
            user_metrics = state.get('metrics', DEFAULT_METRICS.copy())
            last_screen = state.get('last_screening_timestamp')
            if last_screen and isinstance(last_screen, datetime):
                if (datetime.now(timezone.utc) - last_screen) < timedelta(days=7):
                    has_recent_screening = True

    return jsonify({
        "message": "Login successful",
        "user": {
            "id": user_id,
            "name": user_data.get('name'),
            "age": user_data.get('age'),
            "email": user_data.get('email'),
            "metrics": user_metrics,
            "region": user_data.get('region') or "GLOBAL"
        },
        # Duplicate some fields at top-level for compatibility with older clients/tests
        "userId": user_id,
        "name": user_data.get('name'),
        "hasRecentScreening": has_recent_screening
    })


@auth_bp.route('/auth/cleanupUsersWithoutRegion', methods=['POST'])
def cleanup_users_without_region():
    """Delete all accounts that don't have a region field set."""
    db = _get_db_or_none()
    try:
        deleted_count = 0
        if db:
            users = db.collection('registered_users').stream()
            for doc in users:
                data = doc.to_dict()
                if not data.get('region'):
                    # Delete user state and sessions, then the user
                    try:
                        # Delete user state
                        db.collection('user_states').document(doc.id).delete()
                    except Exception:
                        pass
                    # Delete sessions
                    try:
                        sessions = db.collection('user_sessions').where('userId', '==', doc.id).stream()
                        for s in sessions:
                            # Delete chatHistory subcollection
                            try:
                                chats = db.collection('user_sessions').document(s.id).collection('chatHistory').stream()
                                for c in chats:
                                    db.collection('user_sessions').document(s.id).collection('chatHistory').document(c.id).delete()
                            except Exception:
                                pass
                            db.collection('user_sessions').document(s.id).delete()
                    except Exception:
                        pass
                    # Delete user doc
                    db.collection('registered_users').document(doc.id).delete()
                    deleted_count += 1
        else:
            # Memory cleanup
            for uid, data in list(_MEM_USERS_BY_ID.items()):
                if not data.get('region'):
                    _MEM_USERS_BY_ID.pop(uid, None)
                    email_l = data.get('email_lower')
                    if email_l:
                        _MEM_USERS_BY_EMAIL.pop(email_l, None)
                    _MEM_USER_STATES.pop(uid, None)
                    deleted_count += 1
        return jsonify({"deleted": deleted_count})
    except Exception as e:
        print(f"Cleanup error: {e}")
        return jsonify({"error": "Cleanup failed"}), 500


@auth_bp.route('/auth/getMetrics', methods=['GET'])
def get_metrics():
    db = _get_db_or_none()
    user_id = request.args.get('userId') or request.headers.get('X-User-ID')

    if not user_id:
        return jsonify({"error": "User ID is required"}), 400

    try:
        if db:
            user_state_ref = db.collection('user_states').document(user_id)
            user_state_doc = user_state_ref.get()

            if user_state_doc.exists:
                metrics = user_state_doc.to_dict().get('metrics', DEFAULT_METRICS)
            else:
                metrics = DEFAULT_METRICS
        else:
            state = _MEM_USER_STATES.get(user_id)
            metrics = state.get('metrics', DEFAULT_METRICS) if state else DEFAULT_METRICS

        return jsonify({"metrics": metrics})

    except Exception as e:
        print(f"Error getting metrics for user {user_id}: {e}")
        return jsonify({"error": "Failed to get metrics"}), 500
