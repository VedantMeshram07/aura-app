# backend/agents/orion_analyzer.py

from firebase_admin import firestore
from datetime import datetime, timedelta

def run_analysis(db):
    """
    Enhanced Orion analyzer that provides comprehensive mental health insights
    and recommendations for other agents to use in their interactions.
    """
    print("\n--- [Orion Agent] Starting enhanced periodic analysis... ---")
    
    try:
        # Analyze user states for insights
        user_states_ref = db.collection('user_states')
        docs = user_states_ref.stream()

        users_analyzed = 0
        insights_found = 0

        for doc in docs:
            users_analyzed += 1
            user_id = doc.id
            user_data = doc.to_dict()
            metrics = user_data.get('metrics', {})
            
            if metrics:
                depression = metrics.get('depression', 0)
                anxiety = metrics.get('anxiety', 0)
                stress = metrics.get('stress', 0)
                
                print(f"  -> Analyzing user: {user_id}, Metrics: D:{depression} A:{anxiety} S:{stress}")
                
                insights = []
                recommendations = {}
                risk_level = 'low'
                
                # Enhanced depression analysis
                if depression >= 80:
                    insights.append('severe_depression')
                    recommendations['depression'] = {
                        'priority': 'critical',
                        'suggestions': [
                            'Immediate professional help recommended',
                            'Crisis intervention may be needed',
                            'Monitor for suicidal thoughts',
                            'Encourage medical consultation'
                        ]
                    }
                    risk_level = 'critical'
                elif depression >= 70:
                    insights.append('high_depression')
                    recommendations['depression'] = {
                        'priority': 'high',
                        'suggestions': [
                            'Professional counseling recommended',
                            'Consider medication evaluation',
                            'Increase social support',
                            'Regular mood tracking'
                        ]
                    }
                    risk_level = 'high'
                elif depression >= 50:
                    insights.append('moderate_depression')
                    recommendations['depression'] = {
                        'priority': 'medium',
                        'suggestions': [
                            'Light therapy and exercise',
                            'Social activities',
                            'Mindfulness practices',
                            'Regular sleep schedule'
                        ]
                    }
                
                # Enhanced anxiety analysis
                if anxiety >= 80:
                    insights.append('severe_anxiety')
                    recommendations['anxiety'] = {
                        'priority': 'critical',
                        'suggestions': [
                            'Immediate professional intervention',
                            'Consider medication options',
                            'Crisis management techniques',
                            'Emergency contact information'
                        ]
                    }
                    risk_level = 'critical'
                elif anxiety >= 70:
                    insights.append('high_anxiety')
                    recommendations['anxiety'] = {
                        'priority': 'high',
                        'suggestions': [
                            'Cognitive behavioral therapy',
                            'Breathing exercises',
                            'Progressive muscle relaxation',
                            'Limit caffeine and stimulants'
                        ]
                    }
                    risk_level = 'high'
                elif anxiety >= 50:
                    insights.append('moderate_anxiety')
                    recommendations['anxiety'] = {
                        'priority': 'medium',
                        'suggestions': [
                            'Regular exercise',
                            'Meditation practices',
                            'Time management skills',
                            'Social support networks'
                        ]
                    }
                
                # Enhanced stress analysis
                if stress >= 80:
                    insights.append('severe_stress')
                    recommendations['stress'] = {
                        'priority': 'critical',
                        'suggestions': [
                            'Immediate stress relief needed',
                            'Consider medical leave',
                            'Professional stress management',
                            'Lifestyle changes required'
                        ]
                    }
                    risk_level = 'critical'
                elif stress >= 70:
                    insights.append('high_stress')
                    recommendations['stress'] = {
                        'priority': 'high',
                        'suggestions': [
                            'Work-life balance assessment',
                            'Regular breaks and downtime',
                            'Physical exercise routine',
                            'Stress management techniques'
                        ]
                    }
                    risk_level = 'high'
                elif stress >= 50:
                    insights.append('moderate_stress')
                    recommendations['stress'] = {
                        'priority': 'medium',
                        'suggestions': [
                            'Time management skills',
                            'Relaxation techniques',
                            'Healthy coping mechanisms',
                            'Support system building'
                        ]
                    }
                
                # Enhanced chat pattern analysis
                try:
                    chat_ref = db.collection('aura_sessions').document(user_id).collection('chatHistory')
                    chat_docs = chat_ref.order_by('timestamp', direction='DESCENDING').limit(20).stream()
                    
                    # Social anxiety patterns
                    social_anxiety_keywords = ['people', 'social', 'crowd', 'judge', 'embarrassed', 'awkward', 'alone', 'isolated']
                    social_anxiety_count = 0
                    
                    # Crisis indicators
                    crisis_keywords = ['suicide', 'kill myself', 'want to die', 'better off dead', 'end it all', 'no reason to live']
                    crisis_count = 0
                    
                    # Sleep issues
                    sleep_keywords = ['sleep', 'insomnia', 'tired', 'exhausted', 'rest', 'night']
                    sleep_count = 0
                    
                    # Relationship issues
                    relationship_keywords = ['relationship', 'partner', 'family', 'friend', 'love', 'breakup', 'divorce']
                    relationship_count = 0
                    
                    chat_messages = []
                    for chat_doc in chat_docs:
                        chat_data = chat_doc.to_dict()
                        user_message = chat_data.get('user_message', '').lower()
                        chat_messages.append(user_message)
                        
                        if any(keyword in user_message for keyword in social_anxiety_keywords):
                            social_anxiety_count += 1
                        if any(keyword in user_message for keyword in crisis_keywords):
                            crisis_count += 1
                        if any(keyword in user_message for keyword in sleep_keywords):
                            sleep_count += 1
                        if any(keyword in user_message for keyword in relationship_keywords):
                            relationship_count += 1
                    
                    # Pattern detection
                    if social_anxiety_count >= 3:
                        insights.append('social_anxiety')
                        recommendations['social_anxiety'] = {
                            'priority': 'medium',
                            'suggestions': [
                                'Gradual exposure therapy',
                                'Social skills training',
                                'Support groups',
                                'Professional counseling'
                            ]
                        }
                    
                    if crisis_count >= 1:
                        insights.append('crisis_risk')
                        recommendations['crisis'] = {
                            'priority': 'critical',
                            'suggestions': [
                                'Immediate crisis intervention',
                                'Emergency contact information',
                                'Safety planning',
                                'Professional help required'
                            ]
                        }
                        risk_level = 'critical'
                    
                    if sleep_count >= 3:
                        insights.append('sleep_issues')
                        recommendations['sleep'] = {
                            'priority': 'medium',
                            'suggestions': [
                                'Sleep hygiene practices',
                                'Regular sleep schedule',
                                'Relaxation techniques',
                                'Medical evaluation if persistent'
                            ]
                        }
                    
                    if relationship_count >= 3:
                        insights.append('relationship_stress')
                        recommendations['relationships'] = {
                            'priority': 'medium',
                            'suggestions': [
                                'Communication skills',
                                'Boundary setting',
                                'Couples therapy',
                                'Individual counseling'
                            ]
                        }
                    
                    # Sentiment analysis (basic)
                    positive_words = ['happy', 'good', 'great', 'better', 'improved', 'hope', 'love', 'joy']
                    negative_words = ['sad', 'bad', 'terrible', 'worse', 'hopeless', 'hate', 'angry', 'frustrated']
                    
                    positive_count = sum(1 for msg in chat_messages for word in positive_words if word in msg)
                    negative_count = sum(1 for msg in chat_messages for word in negative_words if word in msg)
                    
                    if negative_count > positive_count * 2:
                        insights.append('negative_trend')
                        recommendations['mood'] = {
                            'priority': 'high',
                            'suggestions': [
                                'Positive psychology techniques',
                                'Gratitude practices',
                                'Activity scheduling',
                                'Professional support'
                            ]
                        }
                
                except Exception as e:
                    print(f"    - Could not analyze chat data for user {user_id}: {e}")
                
                # Generate comprehensive analysis summary
                analysis_summary = {
                    'risk_level': risk_level,
                    'primary_concerns': insights,
                    'recommendations': recommendations,
                    'last_analysis': firestore.SERVER_TIMESTAMP,
                    'analysis_date': datetime.now().isoformat()
                }
                
                # Update user state with enhanced insights
                if insights:
                    insights_found += 1
                    user_states_ref.document(user_id).update({
                        'orion_insights': insights,
                        'orion_recommendations': recommendations,
                        'orion_risk_level': risk_level,
                        'orion_analysis_summary': analysis_summary,
                        'last_analysis': firestore.SERVER_TIMESTAMP
                    })
                    print(f"    - Enhanced insights saved for user {user_id}: {insights}")
                    print(f"    - Risk level: {risk_level}")
                    print(f"    - Recommendations: {len(recommendations)} categories")
        
        print(f"--- [Orion Agent] Enhanced Analysis Complete. Analyzed {users_analyzed} users and found {insights_found} new insights. ---")
        
    except Exception as e:
        print(f"--- [Orion Agent] Error during analysis: {e} ---")