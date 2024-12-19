import requests
from bs4 import BeautifulSoup
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time
from googlesearch import search


# Selenium WebDriver setup
def get_selenium_driver():
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    return driver


# Extract emails from website content
def extract_emails_from_content(content):
    emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', content)
    return emails


# Scrape emails from a specific URL
def scrape_emails_from_website(url):
    print(f"Scraping emails from: {url}")
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        emails = extract_emails_from_content(response.text)
        return emails
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return []


# Search for company website via Google
def search_company_website(company_name):
    print(f"Searching for {company_name} website on Google...")
    for result in search(f"{company_name} official site", num_results=5):
        if "contact" in result or "about" in result:
            print(f"Found website: {result}")
            return result
    return None


# Scrape a website using requests or Selenium
def scrape_website(input_url):
    print(f"Scraping website: {input_url}")

    # Try using requests first (for static sites)
    try:
        response = requests.get(input_url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        company_info = []

        # Look for relevant links or content (like 'contact' or 'about' sections)
        for a_tag in soup.find_all('a', href=True):
            link = a_tag['href']
            if 'contact' in link or 'about' in link:
                company_info.append({'url': link, 'emails': scrape_emails_from_website(link)})

        return company_info
    except Exception as e:
        print(f"Error scraping {input_url} with requests: {e}")

    # If requests fails, use Selenium for JavaScript-rendered sites
    driver = get_selenium_driver()
    driver.get(input_url)
    time.sleep(5)  # Wait for content to load
    company_info = []

    try:
        # Look for links to contact pages or relevant sections in the page
        links = driver.find_elements(By.TAG_NAME, 'a')
        for link in links:
            href = link.get_attribute('href')
            if href and ('contact' in href or 'about' in href):
                company_info.append({'url': href, 'emails': scrape_emails_from_website(href)})
        return company_info
    except Exception as e:
        print(f"Error scraping {input_url} with Selenium: {e}")
    finally:
        driver.quit()


# Main function to process companies
def process_company(input_url):
    print(f"Processing company URL: {input_url}")

    # First, attempt scraping directly from the given URL
    company_data = scrape_website(input_url)
    if company_data:
        return company_data

    # If no data found, attempt to search for the company and get its contact details
    print(f"Attempting to find contact details via Google...")
    company_name = input_url.split("//")[1].split("/")[0]  # Extract company name from URL
    company_website = search_company_website(company_name)
    if company_website:
        return scrape_website(company_website)

    return []


# Example Input: Website URL of a government or company list page
input_url = input("Enter the website URL: ")

# Process the given input URL
contacts = process_company(input_url)

# Output to CSV
import csv

with open("company_contacts.csv", "w", newline="") as file:
    writer = csv.DictWriter(file, fieldnames=["url", "emails"])
    writer.writeheader()
    for contact in contacts:
        writer.writerow(contact)

print("Scraping complete. Results saved to 'company_contacts.csv'.")
