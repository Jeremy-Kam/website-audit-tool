from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import WebDriverException
from collections import deque
import time

def scrape_site(start_url, max_depth=2):
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    
    visited = set()
    queue = deque([(start_url, 0)])
    all_links = []

    while queue:
        current_url, depth = queue.popleft()
        if current_url in visited or depth > max_depth:
            continue

        try:
            driver.get(current_url)
            time.sleep(1)
        except WebDriverException:
            print(f"Failed to open {current_url}")
            continue

        visited.add(current_url)
        all_links.append(current_url)
        print(f"Visited: {current_url}")

        try:
            a_tags = driver.find_elements(By.TAG_NAME, "a")
            for a in a_tags:
                href = a.get_attribute("href")
                if href and href.startswith(start_url) and href not in visited:
                    queue.append((href, depth + 1))
        except Exception as e:
            print(f"Error extracting links from {current_url}: {e}")

    driver.quit()
    return all_links

if __name__ == "__main__":
    start_url = "https://hormoz.dfci.harvard.edu/"  # replace with any website
    all_links_found = scrape_site(start_url)
    print("\nAll links found:")
    for link in all_links_found:
        print(link)
