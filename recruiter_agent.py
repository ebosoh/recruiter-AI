import os
import time
import random
from playwright.sync_api import sync_playwright, Page, BrowserContext
from dotenv import load_dotenv

# Import our custom handlers
import google_sheets_handler
import llm_handler

# --- Configuration ---
load_dotenv() # Load environment variables from .env file

# LinkedIn Credentials - Store these in your .env file
LINKEDIN_EMAIL = os.getenv("LINKEDIN_EMAIL")
LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD")

# Google Sheet Configuration
# IMPORTANT: Replace with your actual Google Sheet ID
SHEET_ID = "YOUR_GOOGLE_SHEET_ID_HERE" 
WORKSHEET_NAME = "Candidates"

# --- Job & Scoring Configuration ---
# PASTE THE FULL JOB DESCRIPTION HERE
JOB_DESCRIPTION = """
Senior Backend Engineer (Go) - We are looking for a seasoned backend engineer to join our platform team. 
You will be responsible for designing, developing, and deploying microservices that power our core product. 
Key requirements include 5+ years of experience with Go (Golang), deep knowledge of Kubernetes and AWS, 
and a proven track record of building distributed systems.
"""

# Weights for the final Lead Score calculation. Adjust as needed.
LEAD_SCORE_WEIGHTS = {
    'relevance': 0.5,
    'tenure': 0.3,
    'activity': 0.2
}

# Session Management
SESSION_FILE = "linkedin_session.json"

def human_like_delay(min_seconds=2, max_seconds=5):
    """Waits for a random duration to mimic human behavior."""
    time.sleep(random.uniform(min_seconds, max_seconds))

def login_to_linkedin(context: BrowserContext, page: Page):
    """Handles the login process for LinkedIn."""
    print("Navigating to LinkedIn login page...")
    page.goto("https://www.linkedin.com/login")
    human_like_delay()

    if not LINKEDIN_EMAIL or not LINKEDIN_PASSWORD:
        raise ValueError("LinkedIn credentials not found in .env file.")

    print("Entering credentials...")
    page.fill("input#username", LINKEDIN_EMAIL)
    page.fill("input#password", LINKEDIN_PASSWORD)
    human_like_delay(1, 2)
    
    print("Signing in...")
    page.click("button[type='submit']")

    # Wait for navigation to the feed page, which indicates a successful login.
    # If a security check or 2FA is required, this will time out.
    try:
        page.wait_for_url("**/feed/**", timeout=30000)
        print("Login successful!")
        # Save session state for future runs
        context.storage_state(path=SESSION_FILE)
        print(f"Session state saved to {SESSION_FILE}")
    except Exception:
        print("\n--- MANUAL ACTION REQUIRED ---")
        print("Login may require a 2FA code or security verification.")
        print("Please complete the login in the browser window.")
        print("The script will resume once you are on the main feed page.")
        page.wait_for_url("**/feed/**", timeout=120000) # Wait longer for manual login
        print("Resuming script...")
        context.storage_state(path=SESSION_FILE)
        print(f"Session state saved to {SESSION_FILE}")


def scrape_linkedin_profile(page: Page, profile_url: str) -> dict:
    """
    Scrapes the essential information from a LinkedIn profile.
    This is a simplified version and may need to be adjusted based on LinkedIn's structure.
    """
    print(f"Scraping profile: {profile_url}")
    page.goto(profile_url, wait_until="domcontentloaded")
    human_like_delay(3, 6) # Wait for the page to load fully

    # A robust scraper would handle variations in page layout.
    # For this example, we use selectors that are common, but might fail.
    try:
        # Click "See more" on the summary if it exists
        about_section = page.locator("section[data-section='about']")
        if about_section.locator("button:has-text('See more')").is_visible():
            about_section.locator("button:has-text('See more')").click()
            human_like_delay(1,2)

        name = page.locator("h1").first.inner_text()
        current_role = page.locator("div.text-body-medium.break-words").first.inner_text().strip()
        location = page.locator("span.text-body-small.inline.break-words").first.inner_text().strip()
        
        # Get summary and the full page text for better analysis
        summary = about_section.locator("div.display-flex.ph5 > div > div > span.visually-hidden").first.inner_text()
        full_text = page.locator("main").inner_text()


        # For skills, we'll just take the top 3 endorsed skills as a sample
        page.goto(profile_url + "/details/skills/", wait_until="domcontentloaded")
        human_like_delay(3, 5)
        skills_elements = page.locator("div.display-flex.ph5.pv3 > div > div > div > div > span.visually-hidden")
        skills = [skills_elements.nth(i).inner_text() for i in range(min(3, skills_elements.count()))]

        profile_data = {
            "LinkedIn": profile_url,
            "Name": name,
            "Current Role": current_role,
            "Location": location,
            "Core Skills": ", ".join(skills),
            "summary": summary,
            "full_text": full_text # Pass full text for tenure analysis
        }
        print("Successfully scraped basic profile data.")
        return profile_data

    except Exception as e:
        print(f"Error scraping profile {profile_url}. The page structure may have changed.")
        print(f"Error: {e}")
        return None

def calculate_lead_score(scores: dict) -> float:
    """Calculates the final lead score based on weighted inputs."""
    relevance = scores.get("Relevance Score", 0) or 0
    tenure = scores.get("Tenure Score", 0) or 0
    activity = scores.get("Activity Score", 0) or 0
    
    w = LEAD_SCORE_WEIGHTS
    
    lead_score = (relevance * w['relevance']) + (tenure * w['tenure']) + (activity * w['activity'])
    
    return round(lead_score, 2)


def run_agent():
    """Main function to run the recruitment agent."""
    
    # --- IMPORTANT ---
    # Define the list of candidate LinkedIn profiles to process.
    # For this example, we use a placeholder. Replace it with real URLs.
    candidate_urls = [
        "https://www.linkedin.com/in/williamhgates/" # Example profile
        # "https://www.linkedin.com/in/another-profile-url/",
    ]
    
    if SHEET_ID == "YOUR_GOOGLE_SHEET_ID_HERE":
        print("CRITICAL: Please replace 'YOUR_GOOGLE_SHEET_ID_HERE' in the script with your actual Google Sheet ID.")
        return
    
    if "Key requirements include" in JOB_DESCRIPTION:
        print("INFO: Using the default sample job description. Please update it with your target role.")


    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=50)
        
        # Use existing session if available, otherwise log in
        if os.path.exists(SESSION_FILE):
            print("Found existing session file. Loading state...")
            context = browser.new_context(storage_state=SESSION_FILE)
        else:
            print("No session file found. A new login will be performed.")
            context = browser.new_context()

        page = context.new_page()

        # Check if we are already logged in by going to the feed
        page.goto("https://www.linkedin.com/feed/")
        if "login" in page.url or "checkpoint" in page.url:
            print("Session is invalid or expired. Logging in again.")
            login_to_linkedin(context, page)
        else:
            print("Session loaded successfully. Already logged in.")

        # --- Main Loop: Process each candidate ---
        for url in candidate_urls:
            print(f"\n--- Processing Candidate: {url} ---")
            
            # 1. Scrape data from LinkedIn
            scraped_data = scrape_linkedin_profile(page, url)
            if not scraped_data:
                continue # Skip to the next candidate if scraping fails

            # 2. Generate insights with the local LLM, now with JD context
            llm_insights = llm_handler.generate_candidate_insights(scraped_data, JOB_DESCRIPTION)
            if not llm_insights:
                continue # Skip if LLM fails
            
            # 3. Calculate the final, weighted Lead Score
            lead_score = calculate_lead_score(llm_insights)
            llm_insights["Lead Score"] = lead_score
            print(f"Calculated final Lead Score: {lead_score}")

            # 4. Combine and save to Google Sheets
            final_candidate_record = {**scraped_data, **llm_insights}
            # We don't need these internal fields in the final sheet
            del final_candidate_record['summary'] 
            del final_candidate_record['full_text']
            
            google_sheets_handler.add_candidate_to_sheet(
                sheet_id=SHEET_ID,
                worksheet_name=WORKSHEET_NAME,
                candidate_data=final_candidate_record
            )
            
            human_like_delay(5, 10) # Wait before processing the next profile

        print("\n--- Agent has finished processing all candidates. ---")
        browser.close()


if __name__ == "__main__":
    run_agent()

