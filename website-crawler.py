from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import WebDriverException
from collections import deque
from urllib.parse import urlparse, urlunparse
import time
import re
import csv
from rapidfuzz import fuzz

def normalize_url(url):
    """Normalize a URL by removing fragments and query strings."""
    parsed = urlparse(url)
    normalized = urlunparse((parsed.scheme, parsed.netloc, parsed.path, '', '', ''))
    return normalized

def scrape_site_variations(start_url, official_strings, detect_strings, spellcheck_strings, regex_patterns=None, fuzzy_threshold=85):
    """
    Crawl a site and find matches:
    - official_strings: correct strings to ignore completely
    - detect_strings: variations we want to detect
    - spellcheck_strings: strings to fuzzy-check for typos
    Returns list of (URL, matched_text, match_type)
    """
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    
    visited = set()
    queue = deque([normalize_url(start_url)])
    matches = []

    base_domain = urlparse(start_url).netloc

    while queue:
        current_url = queue.popleft()
        current_domain = urlparse(current_url).netloc

        if current_url in visited or current_domain != base_domain:
            continue

        try:
            driver.get(current_url)
            time.sleep(1)
        except WebDriverException:
            visited.add(current_url)
            continue

        visited.add(current_url)
        print(f"Visited: {current_url}")

        try:
            page_text = driver.find_element(By.TAG_NAME, "body").text

            # 1️⃣ Regex matches, skipping official strings
            if regex_patterns:
                for pattern in regex_patterns:
                    for match in pattern.findall(page_text):
                        if match in official_strings:
                            continue
                        matches.append((current_url, match, "regex"))
                        print(f"Regex matched '{match}' in {current_url}")

            # 2️⃣ Detect strings: capture exact matched substring
            for s in detect_strings:
                if s in official_strings:
                    continue
                pattern = re.compile(re.escape(s), re.IGNORECASE)
                for match in pattern.findall(page_text):
                    matches.append((current_url, match, f"detect '{s}'"))
                    print(f"Detected '{match}' for '{s}' in {current_url}")

            # 3️⃣ Fuzzy / spellcheck for typos
            for line in page_text.split("\n"):
                line_lower = line.lower()
                if any(s.lower() in line_lower for s in official_strings):
                    continue
                for s in spellcheck_strings:
                    score = fuzz.ratio(line_lower, s.lower())
                    if score >= fuzzy_threshold:
                        matches.append((current_url, line.strip(), f"fuzzy '{s}'"))
                        print(f"Fuzzy spellcheck matched '{line.strip()}' for '{s}' in {current_url}")

        except Exception as e:
            print(f"Error extracting text from {current_url}: {e}")

        # Enqueue same-domain links
        try:
            a_tags = driver.find_elements(By.TAG_NAME, "a")
            for a in a_tags:
                href = a.get_attribute("href")
                if href:
                    normalized_href = normalize_url(href)
                    href_domain = urlparse(normalized_href).netloc
                    if normalized_href not in visited and href_domain == base_domain:
                        queue.append(normalized_href)
        except Exception as e:
            print(f"Error extracting links from {current_url}: {e}")

    driver.quit()
    return matches

def save_matches_to_csv(matches, filename="matches.csv"):
    with open(filename, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["URL", "Matched_Text", "Match_Type"])
        for match in matches:
            writer.writerow(match)
    print(f"\nSaved {len(matches)} matches to {filename}")


if __name__ == "__main__":
    start_url = "https://hormoz.dfci.harvard.edu/"

    # ✅ Official correct strings (never flagged)
    official_strings = ["Dana-Farber"]

    # ✅ Variations to detect explicitly
    detect_strings = [
        "Dana Farber",
        "DFBCC",
        "the Dana-Farber",
        "DFCI",
    ]

    # ✅ Strings to fuzzy-check for typos
    spellcheck_strings = ["Dana-Farber"]

    # Regex patterns (optional)
    regex_patterns = [
        re.compile(r"dana[-– ]?farber", re.IGNORECASE),
        re.compile(r"dfbcc", re.IGNORECASE)
    ]

    found_matches = scrape_site_variations(
        start_url,
        official_strings,
        detect_strings,
        spellcheck_strings,
        regex_patterns=regex_patterns,
        fuzzy_threshold=85
    )

    save_matches_to_csv(found_matches)
