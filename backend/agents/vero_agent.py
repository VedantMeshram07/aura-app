# Vero Agent - Resource Provider
from flask import Blueprint, request, jsonify
from datetime import datetime

vero_bp = Blueprint('vero_agent', __name__)
watsonx_model = None

def set_watsonx_model(model):
    """Set Watsonx model for Vero."""
    global watsonx_model
    watsonx_model = model

def find_resource_for_query(query, region='GLOBAL'):
    """Find resources for user queries with proper source attribution."""
    query_lower = query.lower()
    
    if "stress" in query_lower or "anxiety" in query_lower:
        return {
            "type": "technique",
            "title": "Box Breathing Technique",
            "description": "A simple breathing exercise used by Navy SEALs to reduce stress and anxiety",
            "source": "Sourced from: Navy SEALs and healthcare professionals",
            "source_url": "https://www.webmd.com/balance/what-is-box-breathing",
            "steps": [
                "Find a comfortable, quiet place to sit or lie down.",
                "Close your eyes and slowly exhale all the air from your lungs.",
                "Inhale slowly through your nose for a count of 4.",
                "Hold your breath for a count of 4.",
                "Exhale slowly through your mouth for a count of 4.",
                "Hold the empty breath for a count of 4.",
                "Repeat the cycle for at least 5 minutes to feel the calming effects."
            ]
        }
    elif "focus" in query_lower or "concentration" in query_lower:
        return {
            "type": "technique",
            "title": "Pomodoro Technique",
            "description": "A time management method to improve focus and productivity",
            "source": "Sourced from: Francesco Cirillo",
            "source_url": "https://francescocirillo.com/pages/pomodoro-technique",
            "steps": [
                "Choose a task you want to work on.",
                "Set a timer for 25 minutes.",
                "Work on the task until the timer rings.",
                "Take a 5-minute break.",
                "After 4 pomodoros, take a longer 15-30 minute break.",
                "Repeat the cycle as needed."
            ]
        }
    elif "sad" in query_lower or "depression" in query_lower:
        return {
            "type": "exercise",
            "title": "Gratitude Listing Exercise",
            "description": "A simple exercise to shift perspective and improve mood",
            "source": "Sourced from: PositivePsychology.com",
            "source_url": "https://positivepsychology.com/gratitude-exercises/",
            "steps": [
                "Find a quiet moment to sit comfortably.",
                "Take a few deep breaths to center yourself.",
                "Write down three specific things you are grateful for today.",
                "Be as specific as possible (e.g., 'the warm sunlight on my face' rather than 'the weather').",
                "Reflect on why each item brings you gratitude.",
                "Repeat this exercise daily for best results."
            ]
        }
    else:
        return {
            "type": "technique",
            "title": "5-4-3-2-1 Grounding Technique",
            "description": "A sensory grounding exercise to help with overwhelming feelings",
            "source": "Sourced from: Healthline",
            "source_url": "https://www.healthline.com/health/grounding-techniques",
            "steps": [
                "Look around and name 5 things you can see.",
                "Touch and name 4 things you can feel.",
                "Listen and name 3 things you can hear.",
                "Smell and name 2 things you can smell.",
                "Taste and name 1 thing you can taste.",
                "Take a deep breath and notice how you feel."
            ]
        }

def generate_mock_resource(query):
    """Generate mock resource when WatsonX.ai unavailable."""
    query_lower = query.lower()
    
    if "stress" in query_lower or "anxiety" in query_lower:
        return {
            "title": "Box Breathing Technique",
            "source": "Sourced from: Navy SEALs and healthcare professionals",
            "source_url": "https://www.webmd.com/balance/what-is-box-breathing",
            "steps": [
                "Find a comfortable, quiet place to sit or lie down.",
                "Close your eyes and slowly exhale all the air from your lungs.",
                "Inhale slowly through your nose for a count of 4.",
                "Hold your breath for a count of 4.",
                "Exhale slowly through your mouth for a count of 4.",
                "Hold the empty breath for a count of 4.",
                "Repeat the cycle for at least 5 minutes to feel the calming effects."
            ]
        }
    elif "focus" in query_lower or "concentration" in query_lower:
        return {
            "title": "Pomodoro Technique",
            "source": "Sourced from: Francesco Cirillo",
            "source_url": "https://francescocirillo.com/pages/pomodoro-technique",
            "steps": [
                "Choose a task you want to work on.",
                "Set a timer for 25 minutes.",
                "Work on the task until the timer rings.",
                "Take a 5-minute break.",
                "After 4 pomodoros, take a longer 15-30 minute break.",
                "Repeat the cycle as needed."
            ]
        }
    elif "sad" in query_lower or "depression" in query_lower:
        return {
            "title": "Gratitude Listing Exercise",
            "source": "Sourced from: PositivePsychology.com",
            "source_url": "https://positivepsychology.com/gratitude-exercises/",
            "steps": [
                "Find a quiet moment to sit comfortably.",
                "Take a few deep breaths to center yourself.",
                "Write down three specific things you are grateful for today.",
                "Be as specific as possible (e.g., 'the warm sunlight on my face' rather than 'the weather').",
                "Reflect on why each item brings you gratitude.",
                "Repeat this exercise daily for best results."
            ]
        }
    else:
        return {
            "title": "5-4-3-2-1 Grounding Technique",
            "source": "Sourced from: Healthline",
            "source_url": "https://www.healthline.com/health/grounding-techniques",
            "steps": [
                "Look around and name 5 things you can see.",
                "Touch and name 4 things you can feel.",
                "Listen and name 3 things you can hear.",
                "Smell and name 2 things you can smell.",
                "Taste and name 1 thing you can taste.",
                "Take a deep breath and notice how you feel."
            ]
        }

@vero_bp.route('/vero/getResource', methods=['POST'])
def get_resource():
    """Get resource for user query."""
    data = request.json
    problem_query = data.get('query')
    if not problem_query:
        return jsonify({"error": "A query is required to find a resource"}), 400

    knowledge_base = """
    1. For stress and anxiety, the 'Box Breathing' technique is very effective. It involves inhaling for 4 seconds, holding for 4, exhaling for 4, and holding for 4. It is used by Navy SEALs. Source: WebMD.
    2. For problems with focus or concentration, the 'Pomodoro Technique' is a great tool. It involves working in a 25-minute focused block, followed by a 5-minute break. This cycle is repeated. Source: Francesco Cirillo.
    3. When feeling sad or down, a 'Gratitude Listing' exercise can help shift perspective. The steps are simply to take a moment to write down three specific things you are grateful for, no matter how small. Source: PositivePsychology.com.
    4. For overwhelming feelings or panic, the '5-4-3-2-1 Grounding Technique' is excellent. The steps are: name 5 things you can see, 4 things you can feel, 3 things you can hear, 2 things you can smell, and 1 thing you can taste. Source: Healthline.
    """
    
    try:
        if watsonx_model:
            summarization_prompt = f"""
<role>
You are an expert at extracting simple, actionable, step-by-step instructions from a knowledge base.
</role>
<instructions>
Read the knowledge base and find the single best technique for a user struggling with "{problem_query}".
Your output MUST be in this exact format, with no extra conversation:
Title: [Title of the technique]
Source: [Name of the source]
Steps:
- Step 1...
- Step 2...
- Step 3...
</instructions>
<knowledge_base>
{knowledge_base}
</knowledge_base>

The best technique for "{problem_query}" is:
"""
            response = watsonx_model.generate(prompt=summarization_prompt)
            summarized_exercise = response['results'][0]['generated_text'].strip()

            lines = summarized_exercise.split('\n')
            title = lines[0].replace("Title:", "").strip()
            source = lines[1].replace("Source:", "").strip()
            steps = [line.replace("-", "").strip() for line in lines if line.startswith('-')]
            
            response_data = {
                "title": title,
                "source": f"Sourced from: {source}",
                "source_url": "https://www.google.com",
                "steps": steps
            }
        else:
            response_data = generate_mock_resource(problem_query)
            
    except Exception as e:
        print(f"Error during Vero's AI summarization: {e}")
        response_data = generate_mock_resource(problem_query)

    return jsonify(response_data)

@vero_bp.route('/vero/getMentalHealthTip', methods=['POST'])
def get_mental_health_tip():
    """Get personalized mental health tip."""
    try:
        if watsonx_model:
            tip_prompt = """
<role>
You are a compassionate mental health expert providing daily wellness tips.
</role>
<instructions>
Generate a single, encouraging, and actionable mental health tip. Keep it brief (1-2 sentences) and positive. Focus on practical self-care, mindfulness, or emotional wellness.
</instructions>

Your daily mental health tip:
"""
            response = watsonx_model.generate(prompt=tip_prompt)
            tip = response['results'][0]['generated_text'].strip().strip('"""').strip()
        else:
            fallback_tips = [
                "Take a moment to breathe deeply - it can help reduce stress and anxiety.",
                "Remember, it's okay to not be okay. Reach out to someone you trust.",
                "Small acts of self-care can make a big difference in your mental health.",
                "Practice gratitude by writing down three things you're thankful for today.",
                "Physical activity, even a short walk, can boost your mood significantly.",
                "Set aside 5 minutes today to do something that brings you joy.",
                "Connect with nature - even looking out the window can be grounding.",
                "Be kind to yourself today. You're doing better than you think."
            ]
            tip = fallback_tips[hash(str(datetime.now().date())) % len(fallback_tips)]
        
        return jsonify({"tip": tip})
    except Exception as e:
        print(f"Error generating mental health tip: {e}")
        return jsonify({"tip": "Remember to be kind to yourself today. You're doing great!"})