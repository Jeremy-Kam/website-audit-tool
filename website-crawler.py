from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import WebDriverException
from collections import deque
from urllib.parse import urlparse
import time

def scrape_site(start_url):
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    
    visited = set()
    queue = deque([start_url])
    all_links = []

    # Extract domain from start_url to restrict crawling
    parsed_start = urlparse(start_url)
    base_domain = parsed_start.netloc

    while queue:
        current_url = queue.popleft()
        current_domain = urlparse(current_url).netloc

        # Skip if visited or wrong domain
        if current_url in visited or current_domain != base_domain:
            continue

        try:
            driver.get(current_url)
            time.sleep(1)  # allow page to load
        except WebDriverException:
            print(f"Failed to open {current_url}")
            visited.add(current_url)
            continue

        visited.add(current_url)
        all_links.append(current_url)
        print(f"Visited: {current_url}")

        # Find all <a> tags and extract href
        try:
            a_tags = driver.find_elements(By.TAG_NAME, "a")
            for a in a_tags:
                href = a.get_attribute("href")
                if href and href not in visited:
                    href_domain = urlparse(href).netloc
                    # Only add links that are on the same domain and not visited
                    if href_domain == base_domain:
                        queue.append(href)
        except Exception as e:
            print(f"Error extracting links from {current_url}: {e}")

    driver.quit()
    return all_links

if __name__ == "__main__":
    start_url = "https://hormoz.dfci.harvard.edu/"  # replace with target site
    all_links_found = scrape_site(start_url)
    
    print("\nAll links found:")
    for link in all_links_found:
        print(link)
