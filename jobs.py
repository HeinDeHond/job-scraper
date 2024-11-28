import json
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
import time

# File to store previously seen jobs
JOBS_SEEN_FILE = "jobs_seen.json"

# Email settings
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_SENDER = "terhaarfloris@gmail.com"
EMAIL_PASSWORD = "gdrx bhcf away stum"
EMAIL_RECEIVER = "terhaarfloris@gmail.com"

def load_seen_jobs():
    """Load seen jobs from the JSON file."""
    try:
        with open(JOBS_SEEN_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return []

def save_seen_jobs(seen_jobs):
    """Save seen jobs to the JSON file."""
    with open(JOBS_SEEN_FILE, "w") as file:
        json.dump(seen_jobs, file)

def send_email(new_jobs):
    """Send an email with the new job details."""
    if not new_jobs:
        subject = "No New Job Listings Found"
        body = "No new jobs were found."
    else:
        subject = "New Job Listings Found"
        body = "Here are the new jobs:\n\n"
        for job in new_jobs:
            body += f"Title: {job['title']}\n"
            body += f"Category: {job['category']}\n"
            body += f"Location: {job['location']}\n"
            body += f"Link: {job['link']}\n"
            body += f"Vacature-ID: {job['vacature_id']}\n\n"

    # Create email message
    msg = MIMEMultipart()
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECEIVER
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    # Send email
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.send_message(msg)
    print("Email sent successfully.")

def scrape_jobs(url, extractions):
    """Scrape jobs from a given URL."""
    service = Service("/Users/floris/Downloads/chromedriver-mac-x64/chromedriver")  # Replace with your ChromeDriver path
    driver = webdriver.Chrome(service=service)

    jobs = []

    if extractions == "jobsatpon":
        # Paginated scraping for Jobs at Pon
        page_number = 0
        while True:
            paginated_url = url.format(page_number * 10)
            driver.get(paginated_url)
            time.sleep(2)  # Wait for content to load

            # Extract the full page source after rendering
            page_source = driver.page_source

            # Parse with BeautifulSoup
            soup = BeautifulSoup(page_source, 'html.parser')
            found_new_jobs = False
            for element in soup.find_all('a', attrs={"aria-label": True}):
                aria_label = element.get('aria-label', '')
                if "Vacature-ID:" in aria_label:
                    job_title = aria_label.split(" Vacature-ID:")[0].strip()
                    job_category = element.get('data-ph-at-job-category-text', 'N/A')
                    job_location = element.get('data-ph-at-job-location-area-text', 'N/A')
                    job_link = element.get('href', 'N/A')
                    vacature_id = aria_label.split("Vacature-ID:")[-1].strip().split()[0]

                    jobs.append({
                        "title": job_title,
                        "category": job_category,
                        "location": job_location,
                        "link": job_link,
                        "vacature_id": vacature_id
                    })
                    found_new_jobs = True

            if not found_new_jobs:
                break  # Exit if no more jobs are found
            page_number += 1

    elif extractions == "adyen":
        # Static scraping for Adyen
        driver.get(url)
        time.sleep(3)  # Wait for content to load

        # Extract the full page source after rendering
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        vacancy_links = soup.find_all("a", href=lambda href: href and "/vacancies/" in href)
        for link in vacancy_links:
            title = link.get("aria-label", link.text.strip())
            href = link.get("href", "No link")
            vacature_id = href.split("/vacancies/")[-1].split("?")[0]

            jobs.append({
                "title": title,
                "category": "Analytics",  # Always "Analytics"
                "location": "Amsterdam",  # Always "Amsterdam"
                "link": f"https://careers.adyen.com{href}",  # Absolute link
                "vacature_id": vacature_id
            })

    driver.quit()
    return jobs

# Main logic
seen_jobs = load_seen_jobs()
all_new_jobs = []

# URLs and their extraction types
urls = [
    {"url": "https://www.jobsatpon.com/nl/nl/search-results?keywords=data&from={}", "type": "jobsatpon"},
    {"url": "https://careers.adyen.com/vacancies?location=Amsterdam&team=Data+Analytics", "type": "adyen"}
]

# Scrape jobs from each URL
for site in urls:
    all_jobs = scrape_jobs(site["url"], site["type"])
    # Filter for new jobs
    new_jobs = [job for job in all_jobs if job['vacature_id'] not in seen_jobs]
    all_new_jobs.extend(new_jobs)

    # Update the seen jobs file
    seen_jobs.extend(job['vacature_id'] for job in new_jobs)

# Save updated seen jobs
save_seen_jobs(seen_jobs)

# Send email with all new jobs
send_email(all_new_jobs)
