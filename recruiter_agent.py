import os
import time
import random
import csv
from urllib.parse import quote
from playwright.sync_api import sync_playwright, Page, BrowserContext
from dotenv import load_dotenv

# Import our custom handlers
# import google_sheets_handler
import llm_handler
from config import SEARCH_JOB_TITLE, MAX_CANDIDATES_TO_FIND, JOB_DESCRIPTION, LEAD_SCORE_WEIGHTS, REQUIRED_KEYWORDS

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

def search_for_candidates(page: Page, job_title: str, max_candidates: int) -> list[str]:
    """
    Searches LinkedIn for candidates, validates them on the search page,
    handles pagination, and returns a list of relevant profile URLs.
    """
    print(f"Starting search for '{job_title}'...")

    encoded_job_title = quote(job_title)
    search_url = f"https://www.linkedin.com/search/results/people/?keywords={encoded_job_title}&origin=GLOBAL_SEARCH_HEADER"
    print(f"Constructed search URL: {search_url}")
    page.goto(search_url)
    human_like_delay()

    print("Extracting and validating candidate profile URLs...")
    page.wait_for_selector("div.search-results-container", timeout=15000)

    candidate_urls = []
    processed_items = set() # Keep track of items we've already processed

    while len(candidate_urls) < max_candidates:
        # Find all list items that could be a search result
        list_items = page.locator("div.search-results-container li")
        
        if list_items.count() == 0:
            print("No search result items found on the page.")
            break

        all_items_processed = True
        for i in range(list_items.count()):
            item = list_items.nth(i)
            
            # Create a unique identifier for the item to avoid reprocessing
            item_html = item.inner_html()
            if item_html in processed_items:
                continue
            
            all_items_processed = False
            processed_items.add(item_html)

            # Extract the headline/role text from the search result item
            primary_subtitle_locator = item.locator("div.entity-result__primary-subtitle")
            headline = primary_subtitle_locator.inner_text().lower() if primary_subtitle_locator.count() > 0 else ""

            # Check if all required keywords are in the headline
            if all(keyword.lower() in headline for keyword in REQUIRED_KEYWORDS):
                link_locator = item.locator("a[href*='/in/']").first
                if link_locator.count() > 0:
                    href = link_locator.get_attribute("href")
                    if href:
                        clean_url = href.split('?')[0]
                        if clean_url not in candidate_urls:
                            print(f"Found relevant candidate: {headline}")
                            candidate_urls.append(clean_url)
                            if len(candidate_urls) >= max_candidates:
                                break
            else:
                # This is commented out to avoid cluttering the output
                # print(f"Skipping candidate, headline does not match: {headline}")
                pass

        if len(candidate_urls) >= max_candidates:
            break

        # If we've processed all items on the page, try to scroll or go to the next page
        if all_items_processed:
            print("All items on the current page have been processed.")
        
        # Scroll down to load more results
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        human_like_delay(2, 4)
        
        # Try to click the "Next" button if it exists and is enabled
        next_button = page.locator("button:has-text('Next')")
        if next_button.is_visible() and next_button.is_enabled():
            print("Scrolling finished. Clicking 'Next' page button...")
            next_button.click()
            human_like_delay(3, 6)
            processed_items.clear() # Clear processed items when moving to a new page
        else:
            # If there's no "Next" button, we assume we've reached the end
            print("Reached the end of the search results.")
            break
            
    if not candidate_urls:
        print("\n--- COULD NOT FIND ANY RELEVANT PROFILE LINKS ---")
        print("The script could not find any candidates matching the required keywords.")
        print("This might be due to a change in LinkedIn's page structure or no matching profiles.")
        return []

    print(f"Successfully extracted {len(candidate_urls)} unique and relevant candidate URLs.")
    return candidate_urls[:max_candidates]


def scrape_linkedin_profile(page: Page, profile_url: str) -> dict:
    """Scrapes the essential information from a LinkedIn profile."""
    print(f"Scraping profile: {profile_url}")
    page.goto(profile_url, wait_until="domcontentloaded", timeout=60000)
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
    all_candidates_data = [] # To store data for CSV export

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=50)
        
        if os.path.exists(SESSION_FILE):
            print("Found existing session file. Loading state...")
            context = browser.new_context(storage_state=SESSION_FILE)
        else:
            print("No session file found. A new login will be performed.")
            context = browser.new_context()

        page = context.new_page()

        page.goto("https://www.linkedin.com/feed/", timeout=90000)
        if "login" in page.url or "checkpoint" in page.url:
            print("Session is invalid or expired. Logging in again.")
            login_to_linkedin(context, page)
        else:
            print("Session loaded successfully. Already logged in.")

        candidate_urls = search_for_candidates(page, SEARCH_JOB_TITLE, MAX_CANDIDATES_TO_FIND)
        
        if not candidate_urls:
            print("No candidates found. Exiting.")
            return

        for i, url in enumerate(candidate_urls):
            print(f"\n--- Processing Candidate {i+1}/{len(candidate_urls)}: {url} ---")
            
            try:
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
                
                # --- Store data for CSV export ---
                all_candidates_data.append(final_candidate_record)
                
                # --- The original Google Sheets logic is preserved below ---
                # google_sheets_handler.add_candidate_to_sheet(
                #     sheet_id=SHEET_ID,
                #     worksheet_name=WORKSHEET_NAME,
                #     candidate_data=final_candidate_record
                # )
                
                human_like_delay(5, 10)
            except Exception as e:
                print(f"An error occurred while processing {url}. Skipping.")
                print(f"Error: {e}")
                continue

    # --- Write all collected data to a CSV file ---
    if all_candidates_data:
        output_filename = "recruited_candidates.csv"
        print(f"\nWriting {len(all_candidates_data)} candidates to {output_filename}...")
        
        # Get the headers from the first record
        headers = all_candidates_data[0].keys()
        
        with open(output_filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=headers)
            writer.writeheader()
            writer.writerows(all_candidates_data)
            
        print(f"Successfully saved candidates to {output_filename}")
    else:
        print("\nNo candidate data was collected to write to CSV.")

    print("\n--- Agent has finished processing all candidates. ---")

if __name__ == "__main__":
    run_agent()
