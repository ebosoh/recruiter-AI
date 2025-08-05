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
SHEET_ID = "1Iezquet-B6_3t2bFTfcyWi_4WZrmUq7IAa53cddn_-Q" 
WORKSHEET_NAME = "Candidates"

# --- Sourcing & Scoring Configuration ---
# The exact job title you want to search for on LinkedIn
SEARCH_JOB_TITLE = "Senior C++ Developer"
# The location to filter by. Be specific (e.g., "Germany", "San Francisco Bay Area")
SEARCH_LOCATION = "Norway"
# The maximum number of candidate URLs to collect from the search.
MAX_CANDIDATES_TO_FIND = 25

# The full job description (used for scoring)
JOB_DESCRIPTION = """
Position: Senior C++ Developer

About the Company:
Kratos is the leading provider of satellite Control and Monitoring solutions, with 80% market share. Kratos is also a leading actor in modernizing SatCom ground infrastructure, by developing a new generation of software-defined Satellite Communication products based on Kratos OpenSpace® Platform. OpenSpace® utilize cutting-edge cloud technologies, optimized for  maximum flexibility and performance.
Kratos Norway is the Center of Excellence for VSAT technology within the Kratos group and has 20 years of track record developing highly efficient and advanced solutions for the satellite ground segment.
Kratos Norway is now looking for Software Developers to contribute to the development of the next generation of digital and virtualized satellite monitoring and communication products.

Key Responsibilities:

Development of software communication and monitoring products
Design, architecture and documentation
Collaboration with other Kratos teams (mainly in the US)
Supporting other parts of the organization (sales, delivery, customer support)
Support execution of agile and scrum processes

Requirements:
Higher technical education within software development, preferably a Master’s degree
Significant and documented experience in software design and development
Object-oriented programming background, preferably in C++
Experience with distributed systems built on Docker and Kubernetes
Experience with communication protocols such as TCP/IP, DVB, or 3GPP
Experience with Scrum and agile development processes and tools
Fluency in written and spoken English

Qualifications:
Result-oriented, methodical, and structured
Strong team player with good communication skills
What the Company Offers
Work with state-of-the-art technology with cutting-edge products and advanced solutions for the satellite communication industry
Open and informal organization
An international and engaging work environment
Flexible working hours
Competitive terms, including health insurance, travel insurance and good pension schemes
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

    try:
        page.wait_for_url("**/feed/**", timeout=30000)
        print("Login successful!")
        context.storage_state(path=SESSION_FILE)
        print(f"Session state saved to {SESSION_FILE}")
    except Exception:
        print("\n--- MANUAL ACTION REQUIRED ---")
        print("Login may require a 2FA code or security verification.")
        print("Please complete the login in the browser window.")
        page.wait_for_url("**/feed/**", timeout=120000)
        print("Resuming script...")
        context.storage_state(path=SESSION_FILE)
        print(f"Session state saved to {SESSION_FILE}")

def search_for_candidates(page: Page, job_title: str, location: str, max_candidates: int) -> list[str]:
    """Searches LinkedIn for candidates and returns a list of their profile URLs."""
    print(f"Starting search for '{job_title}' in '{location}'...")
    
    search_url = f"https://www.linkedin.com/search/results/people/?keywords={job_title.replace(' ', '%20')}&origin=GLOBAL_SEARCH_HEADER"
    page.goto(search_url)
    human_like_delay()

    try:
        page.locator("button:has-text('Locations')").click()
        human_like_delay(1, 2)
        location_input = page.locator("input[placeholder='Add a location']")
        location_input.fill(location)
        human_like_delay(1, 2)
        page.keyboard.press("Enter")
        human_like_delay(2, 3)
        page.locator("button:has-text('Show results')").first.click()
        print(f"Applied location filter: {location}")
    except Exception as e:
        print(f"Could not apply location filter, proceeding without it. Error: {e}")

    human_like_delay(3, 5)

    found_urls = set()
    for i in range(5):
        if len(found_urls) >= max_candidates:
            break
        print(f"Scrolling... ({i+1}/5)")
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        human_like_delay(2, 4)
        
        links = page.locator(".reusable-search__result-container a.app-aware-link[href*='/in/']").all()
        for link in links:
            href = link.get_attribute('href')
            clean_url = href.split('?')[0]
            if '/in/' in clean_url:
                found_urls.add(clean_url)
        
        print(f"Found {len(found_urls)} unique candidates so far...")

    print(f"\nSearch complete. Found {len(found_urls)} candidate URLs.")
    return list(found_urls)[:max_candidates]

def scrape_linkedin_profile(page: Page, profile_url: str) -> dict:
    """Scrapes the essential information from a LinkedIn profile."""
    print(f"Scraping profile: {profile_url}")
    page.goto(profile_url, wait_until="domcontentloaded")
    human_like_delay(3, 6)

    try:
        about_section = page.locator("section[data-section='about']")
        if about_section.locator("button:has-text('See more')").is_visible():
            about_section.locator("button:has-text('See more')").click()
            human_like_delay(1,2)

        name = page.locator("h1").first.inner_text()
        current_role = page.locator("div.text-body-medium.break-words").first.inner_text().strip()
        location = page.locator("span.text-body-small.inline.break-words").first.inner_text().strip()
        
        summary_element = about_section.locator("div.display-flex.ph5 > div > div > span.visually-hidden")
        summary = summary_element.first.inner_text() if summary_element.count() > 0 else "N/A"
        full_text = page.locator("main").inner_text()

        try:
            page.goto(profile_url + "/details/skills/", wait_until="domcontentloaded")
            human_like_delay(3, 5)
            skills_elements = page.locator("div.display-flex.ph5.pv3 > div > div > div > div > span.visually-hidden")
            skills = [skills_elements.nth(i).inner_text() for i in range(min(5, skills_elements.count()))]
        except Exception:
            print("Could not navigate to skills page, skipping skills.")
            skills = []

        profile_data = {
            "LinkedIn": profile_url,
            "Name": name,
            "Current Role": current_role,
            "Location": location,
            "Core Skills": ", ".join(skills),
            "summary": summary,
            "full_text": full_text
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
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=50)
        
        if os.path.exists(SESSION_FILE):
            print("Found existing session file. Loading state...")
            context = browser.new_context(storage_state=SESSION_FILE)
        else:
            print("No session file found. A new login will be performed.")
            context = browser.new_context()

        page = context.new_page()

        page.goto("https://www.linkedin.com/feed/")
        if "login" in page.url or "checkpoint" in page.url:
            print("Session is invalid or expired. Logging in again.")
            login_to_linkedin(context, page)
        else:
            print("Session loaded successfully. Already logged in.")

        candidate_urls = search_for_candidates(page, SEARCH_JOB_TITLE, SEARCH_LOCATION, MAX_CANDIDATES_TO_FIND)
        
        if not candidate_urls:
            print("No candidates found. Exiting.")
            browser.close()
            return

        for i, url in enumerate(candidate_urls):
            print(f"\n--- Processing Candidate {i+1}/{len(candidate_urls)}: {url} ---")
            
            scraped_data = scrape_linkedin_profile(page, url)
            if not scraped_data:
                continue

            llm_insights = llm_handler.generate_candidate_insights(scraped_data, JOB_DESCRIPTION)
            if not llm_insights:
                continue
            
            lead_score = calculate_lead_score(llm_insights)
            llm_insights["Lead Score"] = lead_score
            print(f"Calculated final Lead Score: {lead_score}")

            final_candidate_record = {**scraped_data, **llm_insights}
            del final_candidate_record['summary'] 
            del final_candidate_record['full_text']
            
            google_sheets_handler.add_candidate_to_sheet(
                sheet_id=SHEET_ID,
                worksheet_name=WORKSHEET_NAME,
                candidate_data=final_candidate_record
            )
            
            human_like_delay(5, 10)

        print("\n--- Agent has finished processing all candidates. ---")
        browser.close()

if __name__ == "__main__":
    run_agent()