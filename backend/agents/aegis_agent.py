# backend/agents/aegis_agent.py

from flask import Blueprint, request, jsonify
from firebase_admin import firestore
from .agent_data import AEGIS_TRIGGERS, MENTAL_HEALTH_HELPLINES

aegis_bp = Blueprint('aegis_agent', __name__)

def get_helpline_info(region_code):
    """Get comprehensive helpline information for a specific region"""
    region_code = region_code.upper()
    
    # Get region-specific helplines or fall back to global
    helplines = MENTAL_HEALTH_HELPLINES.get(region_code, MENTAL_HEALTH_HELPLINES["GLOBAL"])
    
    return helplines

def format_crisis_response(helplines, is_crisis=False):
    """Format helpline information into a user-friendly response"""
    crisis_info = helplines.get("crisis", {})
    general_info = helplines.get("general", [])
    
    response = ""
    
    if is_crisis:
        response += "🚨 **CRISIS SUPPORT** 🚨\n\n"
        response += "If you are in immediate danger, please call emergency services right away.\n\n"
    
    # Crisis helpline
    if crisis_info:
        response += f"**Primary Crisis Helpline:**\n"
        response += f"📞 {crisis_info['name']}\n"
        response += f"☎️ Phone: {crisis_info['phone']}\n"
        
        if 'text' in crisis_info:
            response += f"💬 Text: {crisis_info['text']}\n"
        
        if 'hours' in crisis_info:
            response += f"⏰ Hours: {crisis_info['hours']}\n"
        
        if 'url' in crisis_info:
            response += f"🌐 More info: {crisis_info['url']}\n"
        
        response += "\n"
    
    # Additional general helplines
    if general_info:
        response += "**Additional Support Resources:**\n\n"
        for i, resource in enumerate(general_info, 1):
            response += f"{i}. **{resource['name']}**\n"
            
            if 'phone' in resource:
                response += f"   ☎️ Phone: {resource['phone']}\n"
            
            if 'text' in resource:
                response += f"   💬 Text: {resource['text']}\n"
            
            if 'description' in resource:
                response += f"   📝 {resource['description']}\n"
            
            if 'url' in resource:
                response += f"   🌐 Website: {resource['url']}\n"
            
            response += "\n"
    
    # Add supportive message
    if is_crisis:
        response += "💙 **You are not alone.** Help is available 24/7. Please reach out to any of these resources if you need immediate support.\n\n"
        response += "Remember: Your life has value, and there are people who care about you and want to help."
    else:
        response += "💙 These resources are here to support you whenever you need them. Don't hesitate to reach out."
    
    return response

@aegis_bp.route('/aegis/crisis-detection', methods=['POST'])
def detect_crisis():
    """Detect crisis triggers and provide immediate helpline information"""
    data = request.json
    user_message = data.get('message', '').lower()
    user_region = data.get('region', 'GLOBAL').upper()
    
    # Check for crisis triggers
    crisis_detected = any(trigger in user_message for trigger in AEGIS_TRIGGERS)
    
    if crisis_detected:
        helplines = get_helpline_info(user_region)
        crisis_response = format_crisis_response(helplines, is_crisis=True)
        
        return jsonify({
            "agent": "Aegis",
            "response": crisis_response,
            "crisis_detected": True,
            "region": user_region
        })
    
    return jsonify({
        "agent": "Aegis",
        "crisis_detected": False
    })

@aegis_bp.route('/aegis/get-helplines', methods=['POST'])
def get_helplines():
    """Get comprehensive helpline information for any region"""
    data = request.json
    user_region = data.get('region', 'GLOBAL').upper()
    include_global = data.get('include_global', True)
    
    helplines = get_helpline_info(user_region)
    response = format_crisis_response(helplines, is_crisis=False)
    
    # Include global helplines if requested and not already global
    if include_global and user_region != "GLOBAL":
        global_helplines = MENTAL_HEALTH_HELPLINES["GLOBAL"]
        response += "\n\n" + "="*50 + "\n"
        response += "**Global Resources (Available Worldwide):**\n\n"
        response += format_crisis_response(global_helplines, is_crisis=False)
    
    return jsonify({
        "agent": "Aegis",
        "response": response,
        "region": user_region,
        "helplines": helplines
    })

@aegis_bp.route('/aegis/request-help', methods=['POST'])
def request_help():
    """Handle explicit requests for help or helpline information"""
    data = request.json
    user_message = data.get('message', '').lower()
    user_region = data.get('region', 'GLOBAL').upper()
    
    # Keywords that indicate someone is asking for help
    help_keywords = [
        'help', 'helpline', 'crisis line', 'phone number', 'emergency number',
        'contact', 'support', 'someone to talk to', 'counseling', 'therapy',
        'mental health', 'depression', 'anxiety', 'suicide', 'crisis'
    ]
    
    if any(keyword in user_message for keyword in help_keywords):
        helplines = get_helpline_info(user_region)
        response = format_crisis_response(helplines, is_crisis=False)
        
        return jsonify({
            "agent": "Aegis",
            "response": response,
            "region": user_region
        })
    
    return jsonify({
        "agent": "Aegis",
        "response": "I'm here to help! If you need mental health support or crisis resources, just let me know and I can provide you with helpline information for your region."
    })

@aegis_bp.route('/aegis/available-regions', methods=['GET'])
def get_available_regions():
    """Get list of available regions with helpline support"""
    regions = list(MENTAL_HEALTH_HELPLINES.keys())
    region_info = {}
    
    for region in regions:
        helplines = MENTAL_HEALTH_HELPLINES[region]
        crisis_info = helplines.get("crisis", {})
        region_info[region] = {
            "name": crisis_info.get("name", "Mental Health Support"),
            "phone": crisis_info.get("phone", "Emergency Services"),
            "hours": crisis_info.get("hours", "24/7")
        }
    
    return jsonify({
        "agent": "Aegis",
        "available_regions": region_info,
        "total_regions": len(regions)
    })
