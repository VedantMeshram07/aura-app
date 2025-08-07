import requests

API_KEY = "0hdsqfcV-287OL19uUyf5OpI1CPG4I5L-6IeXC1iQjvr"
IAM_URL = "https://iam.cloud.ibm.com/identity/token"

response = requests.post(
    IAM_URL,
    headers={"Content-Type": "application/x-www-form-urlencoded"},
    data={"grant_type": "urn:ibm:params:oauth:grant-type:apikey", "apikey": API_KEY}
)

print("Status Code:", response.status_code)
print("Response:", response.json())
from ibm_watsonx_ai.foundation_models import ModelInference

# ✅ Fill in your actual credentials below
credentials = {
    "apikey": "0hdsqfcV-287OL19uUyf5OpI1CPG4I5L-6IeXC1iQjvr",  # Replace with your real API key
    "url": "https://au-syd.ml.cloud.ibm.com"  # Sydney region endpoint
}

# ✅ Initialize the Watsonx model
try:
    watsonx_model = ModelInference(
        model_id="ibm/granite-3-8b-instruct",  # You can change model if needed
        credentials=credentials,
        project_id="bcf0a51a-266f-45a5-ac65-566ee023d881",  # Replace with your actual Project ID
        #region="au-syd"
    )

    # ✅ Generate a simple test prompt
    response = watsonx_model.generate(
        prompt="What are some common mental health coping strategies?",
        #max_tokens=100
    )

    # ✅ Print the model's response
    print("Response:\n", response)

except Exception as e:
    print("❌ Error occurred:")
    print(e)
