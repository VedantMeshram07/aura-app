# Elara Agent - Conversational AI Companion
from flask import Blueprint, request, jsonify
from firebase_admin import firestore
from .agent_data import AEGIS_TRIGGERS
import re
import datetime

elara_bp = Blueprint('elara_agent', __name__)
watsonx_model = None

# Configuration
HISTORY_TURNS = 5
MAX_SENTENCES = 3

# Resource keywords for Vero handoff
RESOURCE_KEYWORDS = [
    "resource", "link", "guide", "reference", "article", "tutorial",
    "reading", "where can i", "provide me", "send me", "resource:", "help me",
    "technique", "exercise", "method", "strategy", "tool", "tip"
]


def set_watsonx_model(model):
    """Set Watsonx model for Elara."""
    global watsonx_model
    watsonx_model = model


def _is_resource_request(text: str) -> bool:
    """Check if user message requests a resource."""
    t = text.lower()
    for kw in RESOURCE_KEYWORDS:
        if kw in t:
            return True
    return False


def generate_mock_response(prompt, context=""):
    """Generate mock response when WatsonX.ai unavailable."""
    lowered = prompt.lower()
    if "greeting" in lowered:
        return "Hello! I'm Elara, your AI companion. I'm here to listen and support you. What's on your mind today?"
    if "stress" in lowered or "anxiety" in lowered:
        return ("I can sense you're feeling overwhelmed. That's completely understandable. "
                "Would you like to talk about what's causing this stress, or try a brief breathing exercise?")
    if "sad" in lowered or "depression" in lowered:
        return ("I hear that you're feeling down, and I want you to know that your feelings are valid. "
                "What's been on your mind lately?")
    return "I'm here to listen and support you. Tell me more about what you're experiencing."


def build_system_prompt(num_prev_messages: int) -> str:
    """Build system prompt for Elara."""
    base_prompt = """
<persona>
You are Elara, a caring AI companion. Your voice is warm, empathetic, and natural. You are not a robot. Use conversational language, be curious, and gently guide the conversation. Avoid clichés like "I'm sorry to hear that" on every message. Instead, ask open-ended questions, validate feelings ("That sounds incredibly tough."), and show you're listening.
</persona>
<instructions>
- Identify the user's core problem (e.g., stress, sadness).
- If you identify a problem, offer to find a technique using the format: [ACTION:find_technique|problem].
- Respond briefly (2-3 sentences max). Do not summarize the entire conversation unless the user asks.
</instructions>
"""
    if num_prev_messages == 0:
        base_prompt += "\n<instructions>Begin with a formal, respectful greeting. Introduce yourself as Elara and warmly acknowledge the user's presence.</instructions>"
    elif num_prev_messages == 1:
        base_prompt += "\n<instructions>Continue formal and respectful tone; begin gentle comfort.</instructions>"
    elif num_prev_messages < 4:
        base_prompt += "\n<instructions>Gradually shift toward a casual, supportive, and friendly tone.</instructions>"
    else:
        base_prompt += "\n<instructions>Now speak casually and comfortably, matching the user's style.</instructions>"
    return base_prompt


def sanitize_ai_response(raw_text: str) -> str:
    """Clean AI response to single Elara reply."""
    if not raw_text:
        return raw_text or ""

    t = raw_text.strip().strip('`"\' \n\r')
    t = re.sub(r'^\s*Elara[:\-\s]+', '', t, flags=re.I)

    lines = t.splitlines()
    first_nonempty_idx = 0
    for idx, ln in enumerate(lines):
        if ln.strip():
            first_nonempty_idx = idx
            break
    lines = lines[first_nonempty_idx:]

    cleaned_lines = []
    for ln in lines:
        if re.match(r'^\s*Elara[:\-\s]+', ln, flags=re.I):
            if not cleaned_lines:
                ln = re.sub(r'^\s*Elara[:\-\s]+', '', ln, flags=re.I)
                cleaned_lines.append(ln)
            else:
                break
        elif re.match(r'^\s*User[:\-\s]+', ln, flags=re.I):
            break
        else:
            cleaned_lines.append(ln)

    if cleaned_lines:
        t = "\n".join(cleaned_lines).strip()
    else:
        t = t.strip()

    if "\n\n" in t:
        t = t.split("\n\n", 1)[0].strip()

    sentences = re.split(r'(?<=[.!?])\s+', t)
    if len(sentences) > MAX_SENTENCES:
        t = " ".join(sentences[:MAX_SENTENCES]).strip()

    t = re.sub(r'\s+\n', '\n', t).strip()
    return t


def _find_latest_session_for_user(db, user_id: str):
    """Find most recent session for user."""
    try:
        q = db.collection('user_sessions').where('userId', '==', user_id).order_by('startTime', direction=firestore.Query.DESCENDING).limit(1).stream()
        for doc in q:
            return doc.id
    except Exception as e:
        print(f"Error finding latest session for user {user_id}: {e}")
    return None


def _create_session(db, user_id: str):
    """Create new session document."""
    try:
        doc_ref = db.collection('user_sessions').document()
        doc_ref.set({
            "userId": user_id,
            "startTime": firestore.SERVER_TIMESTAMP
        })
        return doc_ref.id
    except Exception as e:
        print(f"Error creating session for user {user_id}: {e}")
        return None


def _get_or_create_session(db, user_id: str, provided_session_id: str = None):
    """Get or create session for user."""
    if provided_session_id:
        try:
            doc = db.collection('user_sessions').document(provided_session_id).get()
            if doc.exists:
                return provided_session_id
        except Exception as e:
            print(f"Error verifying provided session_id {provided_session_id}: {e}")

    latest = _find_latest_session_for_user(db, user_id)
    if latest:
        return latest

    return _create_session(db, user_id)


def _store_vero_response(db, session_id, user_message, vero_response_text, resource_data=None):
    """Store Vero response in chat history."""
    try:
        if session_id:
            db.collection('user_sessions').document(session_id).collection('chatHistory').add({
                'user_message': user_message,
                'ai_response': vero_response_text,
                'ai_agent': 'Vero',
                'resource_data': resource_data,
                'timestamp': firestore.SERVER_TIMESTAMP
            })
    except Exception as e:
        print(f"Error storing Vero response in chat history for session {session_id}: {e}")


@elara_bp.route('/elara/greeting', methods=['POST'])
def get_greeting():
    """Generate personalized greeting."""
    db = firestore.client()
    user_metrics = request.json.get('metrics', {"anxiety": 50, "depression": 50, "stress": 50})
    user_id = request.json.get('userId')

    greeting_prompt = f"""
<role>You are Elara, a caring AI companion starting a conversation.</role>
<instructions>
Based on the user's long-term mental health metrics (0-100 scale), generate a SINGLE, short, natural, and welcoming opening message.
- If depression is high, be gentle and reassuring.
- If anxiety is high, be calm and grounding.
- If stress is high, be supportive and acknowledge their pressure.
- DO NOT mention the scores. Be human.
</instructions>
<user_metrics>
{user_metrics}
</user_metrics>
Your welcoming message:
"""

    try:
        if watsonx_model:
            response = watsonx_model.generate(prompt=greeting_prompt)
            ai_response_text = response.get('results', [{}])[0].get('generated_text', '').strip().strip('"""').strip()
        else:
            ai_response_text = generate_mock_response(greeting_prompt)
    except Exception as e:
        print(f"Error calling Watsonx AI for greeting: {e}")
        ai_response_text = generate_mock_response(greeting_prompt)

    session_id = None
    if user_id:
        session_id = _get_or_create_session(db, user_id, provided_session_id=None)

    if session_id:
        try:
            db.collection('user_sessions').document(session_id).collection('chatHistory').add({
                'user_message': None,
                'ai_response': ai_response_text,
                'timestamp': firestore.SERVER_TIMESTAMP,
            })
        except Exception as e:
            print(f"Error storing greeting in session {session_id}: {e}")

    return jsonify({"agent": "Elara", "response": ai_response_text, "sessionId": session_id})


@elara_bp.route('/elara/chat', methods=['POST'])
def handle_chat():
    """Handle chat messages and route to appropriate agents."""
    db = firestore.client()
    data = request.json or {}
    user_id = data.get('userId')
    user_message = data.get('message')
    provided_session_id = data.get('sessionId')
    user_region = data.get('region', 'GLOBAL').upper()

    if not user_id or not user_message:
        return jsonify({"error": "userId and message are required"}), 400

    # Crisis detection
    try:
        lowered = user_message.lower()
        for trig in AEGIS_TRIGGERS:
            pattern = r'\b' + re.escape(trig.lower()) + r'\b'
            if re.search(pattern, lowered):
                from .aegis_agent import get_helpline_info, format_crisis_response
                helplines = get_helpline_info(user_region)
                crisis_text = format_crisis_response(helplines, is_crisis=True)
                return jsonify({"agent": "Aegis", "response": crisis_text})
    except Exception as e:
        print(f"Aegis detection error: {e}")

    crisis_keywords = ["crisis line", "helpline", "help line", "phone number", "emergency number", "contact"]
    if any(kw in user_message.lower() for kw in crisis_keywords):
        from .aegis_agent import get_helpline_info, format_crisis_response
        helplines = get_helpline_info(user_region)
        crisis_text = format_crisis_response(helplines, is_crisis=False)
        return jsonify({"agent": "Aegis", "response": crisis_text})

    # Resource handoff
    try:
        if _is_resource_request(user_message):
            try:
                from .vero_agent import find_resource_for_query
                resource_result = find_resource_for_query(user_message, user_region)
                
                if isinstance(resource_result, dict):
                    resource_text = f"I found a helpful resource for you: {resource_result.get('title', 'A technique')}. "
                    if resource_result.get('description'):
                        resource_text += f"{resource_result['description']} "
                    resource_text += "Click the button below to see the detailed steps and instructions."
                    
                    session_id = _get_or_create_session(db, user_id, provided_session_id)
                    _store_vero_response(db, session_id, user_message, resource_text, resource_result)
                    
                    return jsonify({
                        "agent": "Vero", 
                        "response": resource_text,
                        "resource_data": resource_result,
                        "show_resource_button": True,
                        "sessionId": session_id
                    })
                elif isinstance(resource_result, list):
                    resource_text = "I found several helpful resources for you. Click the button below to access them."
                    
                    session_id = _get_or_create_session(db, user_id, provided_session_id)
                    _store_vero_response(db, session_id, user_message, resource_text, {"type": "list", "items": resource_result})
                    
                    return jsonify({
                        "agent": "Vero", 
                        "response": resource_text,
                        "resource_data": {"type": "list", "items": resource_result},
                        "show_resource_button": True,
                        "sessionId": session_id
                    })
                elif isinstance(resource_result, str):
                    session_id = _get_or_create_session(db, user_id, provided_session_id)
                    _store_vero_response(db, session_id, user_message, resource_result, {"type": "text", "text": resource_result})
                    
                    return jsonify({
                        "agent": "Vero", 
                        "response": resource_result,
                        "resource_data": {"type": "text", "text": resource_result},
                        "show_resource_button": True,
                        "sessionId": session_id
                    })
            except ImportError:
                pass
            except Exception as e:
                print(f"Resource agent error: {e}")
    except Exception as e:
        print(f"Resource-intent detection error: {e}")

    # Session handling
    session_id = _get_or_create_session(db, user_id, provided_session_id)

    # Retrieve chat history
    chat_history = []
    if session_id:
        try:
            rows = (
                db.collection('user_sessions').document(session_id)
                .collection('chatHistory')
                .order_by('timestamp', direction=firestore.Query.DESCENDING)
                .limit(HISTORY_TURNS)
                .stream()
            )
            for doc in rows:
                d = doc.to_dict()
                u = d.get('user_message')
                a = d.get('ai_response')
                if u is not None and a is not None:
                    chat_history.append((u, a))
                elif a is not None and (u is None):
                    chat_history.append((None, a))
        except Exception as e:
            print(f"Error retrieving chat history for session {session_id}: {e}")
            chat_history = []

    chat_history = list(reversed(chat_history))
    num_prev_messages = len([1 for u, a in chat_history if u is not None])

    # Build prompt
    system_prompt = build_system_prompt(num_prev_messages)
    history_text = ""
    for u_msg, ai_msg in chat_history:
        if u_msg is None and ai_msg is not None:
            history_text += f'Elara: "{ai_msg}"\n'
        elif u_msg is not None and ai_msg is not None:
            history_text += f'User: "{u_msg}"\nElara: "{ai_msg}"\n'

    final_prompt = (
        f"{system_prompt}\n\n{history_text}User: \"{user_message}\"\n"
        "<instructions>Respond with ONLY ONE Elara message. Do NOT include multiple 'Elara:' lines or simulate future turns. Keep it brief (1-3 sentences).</instructions>\n"
        "Elara:"
    )

    # Generate response
    try:
        if watsonx_model:
            response = watsonx_model.generate(prompt=final_prompt)
            ai_response_text = response.get('results', [{}])[0].get('generated_text', '')
            if not ai_response_text:
                ai_response_text = response.get('generated_text', '')
            ai_response_text = ai_response_text.strip()
        else:
            ai_response_text = generate_mock_response(final_prompt, history_text)
    except Exception as e:
        print(f"Error calling Watsonx AI for Elara: {e}")
        ai_response_text = generate_mock_response(final_prompt, history_text)

    ai_response_text = sanitize_ai_response(ai_response_text)

    # Store chat turn
    try:
        if session_id:
            db.collection('user_sessions').document(session_id).collection('chatHistory').add({
                'user_message': user_message,
                'ai_response': ai_response_text,
                'timestamp': firestore.SERVER_TIMESTAMP
            })
    except Exception as e:
        print(f"Error storing chat history for session {session_id}: {e}")

    return jsonify({"agent": "Elara", "response": ai_response_text, "sessionId": session_id})


@elara_bp.route('/elara/getHistoryList', methods=['POST'])
def get_history_list():
    """Get list of past chat sessions."""
    db = firestore.client()
    user_id = request.json.get('userId')
    try:
        sessions_ref = db.collection('user_sessions').where('userId', '==', user_id).order_by('startTime', direction=firestore.Query.DESCENDING).stream()
        session_list = []
        for doc in sessions_ref:
            doc_dict = doc.to_dict()
            start_time = doc_dict.get('startTime')
            date_str = "Date not available"
            try:
                if isinstance(start_time, datetime.datetime):
                    date_str = start_time.strftime('%B %d, %Y')
            except Exception:
                pass
            session_list.append({"id": doc.id, "date": date_str})
        return jsonify(session_list)
    except Exception as e:
        print(f"Error retrieving history list: {e}")
        return jsonify([])


@elara_bp.route('/elara/getSession', methods=['POST'])
def get_session():
    """Get chat history for specific session."""
    db = firestore.client()
    session_id = request.json.get('sessionId')
    try:
        history_ref = db.collection('user_sessions').document(session_id).collection('chatHistory').order_by('timestamp').stream()
        chat_history = [{"user": doc.to_dict().get('user_message'), "ai": doc.to_dict().get('ai_response')} for doc in history_ref]
        return jsonify(chat_history)
    except Exception as e:
        print(f"Error retrieving session: {e}")
        return jsonify([])
