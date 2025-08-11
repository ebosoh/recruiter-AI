import gspread
import pandas as pd
from google.oauth2.service_account import Credentials

# The Agent will need access to Google Drive and Google sheets in order to write the final candidates data to a Google Sheet file
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file"
]

# In order to use the Google Sheets API, you need to create a service account and download the credentials JSON file.
SERVICE_ACCOUNT_FILE = 'credentials.json'

def get_sheet_client():
    """Initializes and returns an authenticated gspread client."""
    creds = Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    client = gspread.authorize(creds)
    return client

def add_candidate_to_sheet(sheet_id, worksheet_name, candidate_data):
    """
    Adds a candidate's data as a new row to the specified Google Sheet and worksheet.

    Args:
        sheet_id (str): The ID of the Google Sheet. You can find this in the URL
                        of your sheet (e.g., '.../spreadsheets/d/{sheet_id}/edit').
        worksheet_name (str): The name of the worksheet (tab) to add the data to.
        candidate_data (dict): A dictionary where keys are column headers and
                               values are the candidate's information.
    
    Returns:
        bool: True if the row was added successfully, False otherwise.
    """
    try:
        client = get_sheet_client()
        spreadsheet = client.open_by_key(sheet_id)
        worksheet = spreadsheet.worksheet(worksheet_name)

        # Converts the dictionary to a DataFrame, then to a list of lists
        # This ensures the data is in the correct format for appending.
        df = pd.DataFrame([candidate_data])
        
        # Get header from worksheet to ensure order
        header = worksheet.row_values(1)
        if not header:
            # If sheet is empty, write header first
            worksheet.update([df.columns.values.tolist()], 'A1')
            header = df.columns.values.tolist()

        # Reorder dataframe to match sheet header and append
        row_to_append = df[header].values.tolist()
        worksheet.append_rows(row_to_append)
        
        print(f"Successfully added candidate to '{worksheet_name}'.")
        return True
    except gspread.exceptions.SpreadsheetNotFound:
        print(f"Error: Spreadsheet with ID '{sheet_id}' not found or not shared.")
        return False
    except gspread.exceptions.WorksheetNotFound:
        print(f"Error: Worksheet '{worksheet_name}' not found in the spreadsheet.")
        return False
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return False

# --- Example Usage ---
if __name__ == '__main__':
    # This is a test run. Replace with your actual Sheet ID and data.
    TEST_SHEET_ID = "YOUR_GOOGLE_SHEET_ID_HERE" # <-- IMPORTANT: REPLACE
    TEST_WORKSHEET_NAME = "Candidates"

    # A sample use case for candidate data
    sample_candidate = {
        "LinkedIn": "https://linkedin.com/in/johndoe",
        "Current Role": "Software Engineer",
        "Location": "San Francisco, CA",
        "Core Skills": "Python, Django, React",
        "Personalised Sentence": "I saw your work on the open-source project X and was impressed.",
        "Relevance Score": 9,
        "Openness Score": 7
    }

    print("Running test to add a sample candidate to the Google Sheet...")
    print("Please ensure you have created 'credentials.json' and shared your sheet.")
    
    if TEST_SHEET_ID == "YOUR_GOOGLE_SHEET_ID_HERE":
        print("\nWARNING: Please replace 'YOUR_GOOGLE_SHEET_ID_HERE' with your actual Google Sheet ID.")
    else:
        # Create a dummy header in the sheet if it's empty
        # In a real scenario, you would set up the sheet with headers manually first.
        try:
            client = get_sheet_client()
            sheet = client.open_by_key(TEST_SHEET_ID)
            ws = sheet.worksheet(TEST_WORKSHEET_NAME)
            if not ws.row_values(1):
                headers = list(sample_candidate.keys())
                ws.update([headers], 'A1')
                print(f"Created headers in '{TEST_WORKSHEET_NAME}'.")
        except Exception as e:
            print(f"Could not pre-fill headers, please ensure the sheet and worksheet exist. Error: {e}")

        # Call the function to add the data
        add_candidate_to_sheet(TEST_SHEET_ID, TEST_WORKSHEET_NAME, sample_candidate)
