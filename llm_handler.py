import ollama
import json

# --- Configuration ---
# This is the default model we'll use. It assumes you have run 'ollama pull llama3.2'
MODEL_NAME = 'llama3.2'
# This is the default local endpoint for Ollama.
OLLAMA_ENDPOINT = 'http://localhost:11434'

def get_llm_client():
    """Initializes and returns an Ollama client."""
    try:
        client = ollama.Client(host=OLLAMA_ENDPOINT)
        # A quick check to see if the server is responsive
        client.list() 
        return client
    except Exception as e:
        print(f"Error connecting to Ollama at {OLLAMA_ENDPOINT}.")
        print("Please ensure the Ollama application is running and the model is available.")
        print(f"Underlying error: {e}")
        return None

def generate_candidate_insights(candidate_profile: dict, job_description: str):
    """
    Uses the local Llama 3.2 model to generate a personalized outreach sentence
    and scores for a candidate based on their profile and a job description.

    Args:
        candidate_profile (dict): A dictionary containing scraped data.
        job_description (str): The target job description.

    Returns:
        dict: A dictionary containing scores and a sentence, or None if an error occurs.
    """
    client = get_llm_client()
    if not client:
        return None

    # Construct a detailed, structured prompt for the LLM
    prompt = f"""
    You are an expert technical sourcer. Your task is to analyze a candidate's profile against a specific job description and generate actionable recruitment insights.

    **Target Job Description:**
    ---
    {job_description}
    ---

    **Candidate Profile:**
    - Name: {candidate_profile.get('Name', 'N/A')}
    - Current Role: {candidate_profile.get('Current Role', 'N/A')}
    - Location: {candidate_profile.get('Location', 'N/A')}
    - Core Skills: {candidate_profile.get('Core Skills', 'N/A')}
    - LinkedIn Summary/Experience: {candidate_profile.get('summary', 'N/A')}
    - Full Profile Text (for tenure analysis): {candidate_profile.get('full_text', 'N/A')}

    **Your Task:**
    Based *only* on the provided profile and job description, perform the following actions and provide the output in a single, valid JSON object:
    1.  **`relevance_score`**: On a scale of 1 to 10, how well does the candidate's experience (skills, titles, industry) match the job description?
    2.  **`tenure_score`**: On a scale of 1 to 10, estimate the candidate's readiness to move based on their time in the current role. A higher score (7-10) means they are in a typical window to consider a change (e.g., 1.5 to 4 years). A lower score means they are either too new (<1 year) or too tenured (>5 years).
    3.  **`activity_score`**: On a scale of 1 to 10, estimate the candidate's job-seeking activity. Look for explicit signals like an "Open to Work" banner or recent relevant posts. If no signals are present, give a neutral score of 3-5.
    4.  **`personalised_sentence`**: Write a short, compelling, and personalized sentence (max 250 characters) that a recruiter could use. This sentence must directly reference a specific detail from the candidate's profile *in relation to the job*.

    **Output Format (JSON only):**
    {{
      "relevance_score": <integer>,
      "tenure_score": <integer>,
      "activity_score": <integer>,
      "personalised_sentence": "<string>"
    }}
    """

    try:
        print(f"Sending request to local model '{MODEL_NAME}' for detailed analysis...")
        response = client.chat(
            model=MODEL_NAME,
            messages=[{'role': 'user', 'content': prompt}],
            format='json' # Use Ollama's built-in JSON mode for reliable output
        )
        
        # The response content should be a JSON string, so we parse it.
        insights = json.loads(response['message']['content'])
        
        # Standardize the keys to match our spreadsheet columns
        formatted_insights = {
            "Personalised Sentence": insights.get("personalised_sentence"),
            "Relevance Score": insights.get("relevance_score"),
            "Tenure Score": insights.get("tenure_score"),
            "Activity Score": insights.get("activity_score")
        }
        
        print("Successfully received and parsed detailed insights from the model.")
        return formatted_insights

    except json.JSONDecodeError as e:
        print(f"Error: Could not decode JSON from model response. Error: {e}")
        print(f"Raw response: {{response['message']['content']}}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred while communicating with the LLM: {e}")
        return None

# --- Example Usage ---
if __name__ == '__main__':
    # This is a test run.
    sample_job_description = """
    Senior Backend Engineer (Go) - We are looking for a seasoned backend engineer to join our platform team. You will be responsible for designing, developing, and deploying microservices that power our core product. Key requirements include 5+ years of experience with Go (Golang), deep knowledge of Kubernetes and AWS, and a proven track record of building distributed systems.
    """
    
    sample_candidate = {
        "Name": "Jane Doe",
        "Current Role": "Lead Software Engineer at InnovateCorp",
        "Location": "Berlin, Germany",
        "Core Skills": "Go, Kubernetes, AWS, Distributed Systems",
        "summary": "10+ years of experience leading teams to build scalable cloud-native applications. Passionate about open-source contributions, particularly in the CNCF landscape.",
        "full_text": "Lead Software Engineer at InnovateCorp (2 years). Previously Senior SRE at CloudScale (4 years)."
    }

    print("--- Running LLM Handler Test with Detailed Analysis ---")
    generated_data = generate_candidate_insights(sample_candidate, sample_job_description)

    if generated_data:
        print("\n--- Generated Insights ---")
        print(f"Personalised Sentence: {generated_data['Personalised Sentence']}")
        print(f"Relevance Score: {generated_data['Relevance Score']}")
        print(f"Tenure Score: {generated_data['Tenure Score']}")
        print(f"Activity Score: {generated_data['Activity Score']}")
        print("--------------------------")
    else:
        print("\n--- Test Failed ---")
        print("Could not generate insights. Please check the error messages above.")
