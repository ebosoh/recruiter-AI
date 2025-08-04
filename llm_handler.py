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

def generate_candidate_insights(candidate_profile: dict):
    """
    Uses the local Llama 3.2 model to generate a personalized outreach sentence
    and scores for a candidate based on their profile.

    Args:
        candidate_profile (dict): A dictionary containing scraped data like
                                  'current_role', 'location', 'core_skills', etc.

    Returns:
        dict: A dictionary containing 'Personalised Sentence', 'Relevance Score',
              and 'Openness Score', or None if an error occurs.
    """
    client = get_llm_client()
    if not client:
        return None

    # Construct a detailed, structured prompt for the LLM
    prompt = f"""
    You are an expert recruitment assistant. Your task is to analyze a candidate's profile and generate specific, actionable insights for a recruiter.

    **Candidate Profile:**
    - Current Role: {candidate_profile.get('current_role', 'N/A')}
    - Location: {candidate_profile.get('location', 'N/A')}
    - Core Skills: {candidate_profile.get('core_skills', 'N/A')}
    - LinkedIn Summary/Experience: {candidate_profile.get('summary', 'N/A')}

    **Your Task:**
    Based *only* on the profile above, perform the following actions and provide the output in a single, valid JSON object:
    1.  **`relevance_score`**: Rate the candidate's relevance for a senior tech role on a scale of 1 to 10.
    2.  **`openness_score`**: Estimate how open the candidate might be to a new opportunity (1=not open, 10=actively looking). Base this on subtle cues like their profile summary or job history. If no cues, provide a neutral score of 5.
    3.  **`personalised_sentence`**: Write a short, compelling, and personalized sentence (max 250 characters) that a recruiter could use to start a conversation. This sentence must be unique and directly reference a specific detail from the candidate's profile.

    **Output Format (JSON only):**
    {{
      "relevance_score": <integer>,
      "openness_score": <integer>,
      "personalised_sentence": "<string>"
    }}
    """

    try:
        print(f"Sending request to local model '{MODEL_NAME}'...")
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
            "Openness Score": insights.get("openness_score")
        }
        
        print("Successfully received and parsed insights from the model.")
        return formatted_insights

    except json.JSONDecodeError as e:
        print(f"Error: Could not decode JSON from model response. Error: {e}")
        print(f"Raw response: {response['message']['content']}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred while communicating with the LLM: {e}")
        return None

# --- Example Usage ---
if __name__ == '__main__':
    # This is a test run.
    sample_candidate = {
        "current_role": "Lead Software Engineer at InnovateCorp",
        "location": "Berlin, Germany",
        "core_skills": "Go, Kubernetes, AWS, Distributed Systems",
        "summary": "10+ years of experience leading teams to build scalable cloud-native applications. Passionate about open-source contributions, particularly in the CNCF landscape."
    }

    print("--- Running LLM Handler Test ---")
    generated_data = generate_candidate_insights(sample_candidate)

    if generated_data:
        print("\n--- Generated Insights ---")
        print(f"Personalised Sentence: {generated_data['Personalised Sentence']}")
        print(f"Relevance Score: {generated_data['Relevance Score']}")
        print(f"Openness Score: {generated_data['Openness Score']}")
        print("--------------------------")
    else:
        print("\n--- Test Failed ---")
        print("Could not generate insights. Please check the error messages above.")
