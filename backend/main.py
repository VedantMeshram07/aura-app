# Aura Mental Health App - Main Application
import os
import time
import threading
from flask import Flask, render_template, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore

# Watsonx.ai imports
try:
    from ibm_watsonx_ai.foundation_models import ModelInference
    from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams
    from ibm_watsonx_ai.credentials import Credentials
    WATSONX_AVAILABLE = True
except ImportError:
    ModelInference = None
    Credentials = None
    WATSONX_AVAILABLE = False

# Agent blueprint imports
try:
    from agents.auth_agent import auth_bp
    from agents.kai_agent import kai_bp
    from agents.elara_agent import elara_bp, set_watsonx_model as set_elara_model
    from agents.vero_agent import vero_bp, set_watsonx_model as set_vero_model
    from agents.aegis_agent import aegis_bp
    from agents.orion_analyzer import run_analysis
    from agents.session_agent import session_bp
    AGENTS_AVAILABLE = True
except ImportError:
    AGENTS_AVAILABLE = False

# Initialize Firebase globally
def initialize_firebase():
    """Initialize Firebase outside of app context."""
    try:
        backend_dir = os.path.abspath(os.path.dirname(__file__))
        service_account_path = os.path.join(backend_dir, "serviceAccountKey.json")
        
        if not os.path.exists(service_account_path):
            print("Firebase service account key not found")
            return False
        else:
            cred = credentials.Certificate(service_account_path)
            firebase_admin.initialize_app(cred)
            print("Firebase initialized successfully")
            return True
    except Exception as e:
        print(f"Firebase initialization failed: {e}")
        return False

# Initialize Firebase
firebase_available = initialize_firebase()

def create_app():
    """Create and configure Flask application."""
    load_dotenv()
    backend_dir = os.path.abspath(os.path.dirname(__file__))
    frontend_dir = os.path.join(os.path.dirname(backend_dir), 'frontend')

    app = Flask(__name__, template_folder=frontend_dir, static_folder=frontend_dir, static_url_path='')
    CORS(app)
    app.firebase_available = firebase_available

    with app.app_context():
        # Watsonx.ai setup
        try:
            watsonx_api_key = os.getenv("WATSONX_API_KEY")
            watsonx_project_id = os.getenv("WATSONX_PROJECT_ID")
            watsonx_url = os.getenv("WATSONX_URL")

            if not WATSONX_AVAILABLE:
                app.watsonx_model = None
            elif not watsonx_api_key or not watsonx_project_id:
                app.watsonx_model = None
            else:
                try:
                    creds = Credentials(api_key=watsonx_api_key, url=watsonx_url)
                    generate_params = {
                        GenParams.DECODING_METHOD: "greedy",
                        GenParams.MAX_NEW_TOKENS: 200,
                        GenParams.MIN_NEW_TOKENS: 1,
                        GenParams.TEMPERATURE: 0.7,
                        GenParams.STOP_SEQUENCES: ["\n\n", "User:", "Elara:"]
                    }

                    model = ModelInference(
                        model_id="ibm/granite-3-8b-instruct",
                        credentials=creds,
                        project_id=watsonx_project_id,
                        params=generate_params
                    )
                    
                    if AGENTS_AVAILABLE:
                        set_elara_model(model)
                        set_vero_model(model)
                    app.watsonx_model = model
                except Exception as e:
                    print(f"Watsonx.ai initialization failed: {e}")
                    app.watsonx_model = None
        except Exception as e:
            print(f"Watsonx.ai setup error: {e}")
            app.watsonx_model = None

    # Static file serving
    @app.route('/styles.css')
    def serve_css():
        return send_from_directory(frontend_dir, 'styles.css')

    @app.route('/script.js')
    def serve_js():
        return send_from_directory(frontend_dir, 'script.js')

    @app.route('/favicon.svg')
    def serve_favicon():
        return send_from_directory(frontend_dir, 'favicon.svg')

    @app.route('/')
    def serve_index():
        return render_template('index.html')

    # Register blueprints
    if AGENTS_AVAILABLE:
        try:
            app.register_blueprint(auth_bp)
            app.register_blueprint(kai_bp)
            app.register_blueprint(elara_bp)
            app.register_blueprint(vero_bp)
            app.register_blueprint(aegis_bp)
            app.register_blueprint(session_bp)
        except Exception as e:
            print(f"Error registering blueprints: {e}")

    return app


def orion_background_worker(app_instance):
    """Background worker for Orion analysis."""
    time.sleep(15)
    while True:
        try:
            with app_instance.app_context():
                if hasattr(app_instance, 'firebase_available') and app_instance.firebase_available:
                    db = firestore.client()
                    if AGENTS_AVAILABLE:
                        run_analysis(db)
        except Exception as e:
            print(f"Orion background worker error: {e}")
        time.sleep(3600)


app = create_app()

if __name__ == '__main__':
    try:
        threading.Thread(target=orion_background_worker, args=(app,), daemon=True).start()
    except Exception as e:
        print(f"Could not start Orion background agent: {e}")

    app.run(debug=True, use_reloader=False, host='0.0.0.0', port=5000)
