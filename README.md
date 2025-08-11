# Recruiter AI Agent

This project is an AI-powered recruitment agent that automates the process of sourcing, screening, and ranking candidates from LinkedIn.

## Features

- **Automated Sourcing:** Searches LinkedIn for candidates based on a defined job title.
- **Intelligent Screening:** Uses a local LLM (Ollama's Llama 3.2) to analyze candidate profiles against a job description.
- **Candidate Scoring:** Ranks candidates based on relevance, tenure, and activity.
- **Personalized Outreach:** Generates a personalized outreach sentence for each candidate.
- **CSV Export:** Saves all candidate data to a CSV file for easy review.
- **Google Sheets Integration (Optional):** Can be configured to save candidate data to a Google Sheet.

## Getting Started

### Prerequisites

- Python 3.8+
- [Ollama](https://ollama.ai/) installed and running with the `llama3.2` model.
- A LinkedIn account.

### Installation

1.  Clone the repository:
    ```bash
    git clone https://github.com/ebosoh/recruiter-AI.git
    ```
2.  Install the required packages:
    ```bash
    pip install -r requirements.txt
    ```
3.  Create a `.env` file in the root of the project and add your LinkedIn credentials:
    ```
    LINKEDIN_EMAIL="your_email"
    LINKEDIN_PASSWORD="your_password"
    ```
4.  (Optional) If you want to use the Google Sheets integration, you will need to create a service account and download the credentials JSON file. Save the file as `credentials.json` in the root of the project.

## Usage

1.  Configure the search parameters in `config.py`.
2.  Run the agent:
    ```bash
    python recruiter_agent.py
    ```
3.  The agent will then:
    - Log in to LinkedIn.
    - Search for candidates.
    - Scrape their profiles.
    - Analyze their profiles with the LLM.
    - Save the results to `recruited_candidates.csv`.

## Configuration

- **`config.py`**: This file contains the main configuration for the agent.
  - `SEARCH_JOB_TITLE`: The job title to search for on LinkedIn.
  - `MAX_CANDIDATES_TO_FIND`: The maximum number of candidates to find.
  - `JOB_DESCRIPTION`: The job description to use for scoring.
  - `LEAD_SCORE_WEIGHTS`: The weights to use for the lead score calculation.
  - `REQUIRED_KEYWORDS`: Keywords that must be present in a candidate's current role.
- **`llm_handler.py`**: This file contains the configuration for the LLM.
  - `MODEL_NAME`: The name of the Ollama model to use.
  - `OLLAMA_ENDPOINT`: The endpoint for the Ollama API.
- **`google_sheets_handler.py`**: This file contains the configuration for the Google Sheets integration.
  - `SCOPES`: The scopes to use for the Google API.
  - `SERVICE_ACCOUNT_FILE`: The path to the service account credentials file.

## Contributing

Contributions are welcome! Please feel free to submit a pull request.

## License

This project is licensed under the MIT License.
