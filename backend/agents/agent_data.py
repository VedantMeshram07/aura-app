# backend/agents/agent_data.py

# A central place for all static data used by the agents.

# --- KAI AGENT DATA ---
BASE_QUESTIONS = [
    {"id": "q1", "text": "Over the last 2 weeks, how often have you been bothered by having little interest or pleasure in doing things?"},
    {"id": "q2", "text": "Over the last 2 weeks, how often have you been bothered by feeling down, depressed, or hopeless?"},
    {"id": "q9", "text": "Thoughts that you would be better off dead or of hurting yourself in some way?"}
]
AGE_SPECIFIC_QUESTIONS = {
    "6-18": [{"id": "age_q1", "text": "How often have you felt worried about school, grades, or fitting in with friends?"}, {"id": "age_q2", "text": "Have you had trouble concentrating or staying still in class more than usual?"}],
    "18-30": [{"id": "age_q1", "text": "How often have you felt overwhelmed by pressure from work, college, or making major life decisions?"}, {"id": "age_q2", "text": "Have you experienced intense mood swings, from feeling very high and energetic to very low and sad?"}],
    "30-60": [{"id": "age_q1", "text": "How often have you felt 'burnt out' or emotionally drained from work or family responsibilities?"}, {"id": "age_q2", "text": "Have you worried excessively about financial security or the health of your loved ones?"}],
    "60+": [{"id": "age_q1", "text": "How often have you felt lonely or isolated from others?"}, {"id": "age_q2", "text": "Have you been worried about your physical health or coping with the loss of loved ones or independence?"}]
}
RESPONSE_OPTIONS = ["Not at all", "Several days", "More than half the days", "Nearly every day"]

# --- AEGIS AGENT DATA ---
AEGIS_TRIGGERS = ['suicide', 'kill myself', 'want to die', 'hurting myself', 'better off dead', 'end it all', 'no reason to live', 'tired of living']

# Comprehensive Global and Region-Specific Mental Health Helplines
MENTAL_HEALTH_HELPLINES = {
    # North America
    "US": {
        "crisis": {
            "name": "National Suicide Prevention Lifeline",
            "phone": "988",
            "text": "Text HOME to 741741 (Crisis Text Line)",
            "url": "https://suicidepreventionlifeline.org/",
            "hours": "24/7"
        },
        "general": [
            {
                "name": "SAMHSA National Helpline",
                "phone": "1-800-662-HELP (4357)",
                "url": "https://www.samhsa.gov/find-help/national-helpline",
                "description": "Treatment referral and information service"
            },
            {
                "name": "Crisis Text Line",
                "text": "Text HOME to 741741",
                "url": "https://www.crisistextline.org/",
                "description": "Free, 24/7 crisis counseling via text"
            }
        ]
    },
    "CA": {
        "crisis": {
            "name": "Crisis Services Canada",
            "phone": "1-833-456-4566",
            "text": "Text 45645",
            "url": "https://www.crisisservicescanada.ca/",
            "hours": "24/7"
        },
        "general": [
            {
                "name": "Canadian Mental Health Association",
                "phone": "1-800-875-6213",
                "url": "https://cmha.ca/",
                "description": "Mental health support and resources"
            }
        ]
    },
    
    # Europe
    "GB": {
        "crisis": {
            "name": "Samaritans",
            "phone": "116 123",
            "url": "https://www.samaritans.org/",
            "hours": "24/7"
        },
        "general": [
            {
                "name": "Mind",
                "phone": "0300 123 3393",
                "url": "https://www.mind.org.uk/",
                "description": "Mental health information and support"
            }
        ]
    },
    "DE": {
        "crisis": {
            "name": "Telefonseelsorge",
            "phone": "0800 111 0 111",
            "url": "https://www.telefonseelsorge.de/",
            "hours": "24/7"
        },
        "general": [
            {
                "name": "Deutsche DepressionsLiga",
                "phone": "0800 3344533",
                "url": "https://www.deutsche-depressionsliga.de/",
                "description": "Depression support and information"
            }
        ]
    },
    "FR": {
        "crisis": {
            "name": "SOS Amitié",
            "phone": "09 72 39 40 50",
            "url": "https://www.sos-amitie.com/",
            "hours": "24/7"
        },
        "general": [
            {
                "name": "UNAFAM",
                "phone": "01 42 63 03 03",
                "url": "https://www.unafam.org/",
                "description": "Support for families and friends of mentally ill"
            }
        ]
    },
    
    # Asia-Pacific
    "IN": {
        "crisis": {
            "name": "KIRAN Mental Health Helpline",
            "phone": "1800-599-0019",
            "url": "https://www.mohfw.gov.in/",
            "hours": "24/7"
        },
        "general": [
            {
                "name": "Vandrevala Foundation",
                "phone": "1860 2662 345",
                "url": "https://www.vandrevalafoundation.com/",
                "description": "Mental health support and counseling"
            }
        ]
    },
    "AU": {
        "crisis": {
            "name": "Lifeline Australia",
            "phone": "13 11 14",
            "url": "https://www.lifeline.org.au/",
            "hours": "24/7"
        },
        "general": [
            {
                "name": "Beyond Blue",
                "phone": "1300 22 4636",
                "url": "https://www.beyondblue.org.au/",
                "description": "Depression and anxiety support"
            }
        ]
    },
    "JP": {
        "crisis": {
            "name": "Tokyo English Life Line",
            "phone": "03-5774-0992",
            "url": "https://telljp.com/",
            "hours": "9:00 AM - 11:00 PM"
        },
        "general": [
            {
                "name": "Japan Helpline",
                "phone": "0570-000-911",
                "url": "https://jhelp.com/",
                "description": "General support and information"
            }
        ]
    },
    
    # Latin America
    "BR": {
        "crisis": {
            "name": "Centro de Valorização da Vida (CVV)",
            "phone": "188",
            "url": "https://www.cvv.org.br/",
            "hours": "24/7"
        },
        "general": [
            {
                "name": "Sistema Único de Saúde (SUS)",
                "phone": "136",
                "url": "https://www.gov.br/saude/",
                "description": "Public health system mental health support"
            }
        ]
    },
    "MX": {
        "crisis": {
            "name": "Línea de la Vida",
            "phone": "800 911 2000",
            "url": "https://www.gob.mx/salud/",
            "hours": "24/7"
        },
        "general": [
            {
                "name": "Instituto Nacional de Psiquiatría",
                "phone": "55 4160 5000",
                "url": "https://www.gob.mx/inprfm/",
                "description": "National psychiatric institute"
            }
        ]
    },
    
    # Africa
    "ZA": {
        "crisis": {
            "name": "South African Depression and Anxiety Group",
            "phone": "0800 456 789",
            "url": "https://www.sadag.org/",
            "hours": "8:00 AM - 8:00 PM"
        },
        "general": [
            {
                "name": "Lifeline South Africa",
                "phone": "0861 322 322",
                "url": "https://lifeline.org.za/",
                "description": "Crisis intervention and counseling"
            }
        ]
    },
    "NG": {
        "crisis": {
            "name": "Mental Health Foundation Nigeria",
            "phone": "0800 888 8888",
            "url": "https://mentalhealthfoundationng.org/",
            "hours": "24/7"
        },
        "general": [
            {
                "name": "Nigerian Mental Health",
                "phone": "0800 888 8888",
                "url": "https://nigerianmentalhealth.org/",
                "description": "Mental health support and resources"
            }
        ]
    },
    
    # Middle East
    "AE": {
        "crisis": {
            "name": "Emirates Foundation",
            "phone": "800 46342",
            "url": "https://www.emiratesfoundation.ae/",
            "hours": "24/7"
        },
        "general": [
            {
                "name": "Al Amal Psychiatric Hospital",
                "phone": "04 337 1200",
                "url": "https://www.dha.gov.ae/",
                "description": "Mental health services"
            }
        ]
    },
    
    # Global Fallback
    "GLOBAL": {
        "crisis": {
            "name": "International Association for Suicide Prevention",
            "phone": "112",
            "url": "https://www.iasp.info/resources/Crisis_Centres/",
            "hours": "24/7",
            "description": "Global crisis center directory"
        },
        "general": [
            {
                "name": "Befrienders Worldwide",
                "url": "https://www.befrienders.org/",
                "description": "International emotional support network"
            },
            {
                "name": "International Federation of Red Cross",
                "url": "https://www.ifrc.org/",
                "description": "Emergency and crisis support"
            }
        ]
    }
}

# --- VERO AGENT DATA ---
VERO_RESOURCES = {
    "breathing_exercise_1": {
        "title": "Box Breathing (4-4-4-4)",
        "source": "A technique used by Navy SEALs and healthcare professionals to manage stress.",
        "source_url": "https://www.webmd.com/balance/what-is-box-breathing",
        "steps": [
            "Find a comfortable, quiet place to sit or lie down.",
            "Close your eyes and slowly exhale all the air from your lungs.",
            "**Inhale** slowly through your nose for a count of 4.",
            "**Hold** your breath for a count of 4.",
            "**Exhale** slowly through your mouth for a count of 4.",
            "**Hold** the empty breath for a count of 4.",
            "Repeat the cycle for at least 5 minutes to feel the calming effects."
        ]
    }
}