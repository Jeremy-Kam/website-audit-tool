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

# ---------------- CSV Loader ----------------
def load_strings_with_website(filename):
    """Load website URL and official/detect/fuzzy strings from CSV."""
    official_strings = []
    detect_strings = []
    spellcheck_strings = []
    start_url = None

    with open(filename, newline="", encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile)
        first_row = next(reader)
        if first_row[0].strip().lower() == "website":
            start_url = first_row[1].strip()
        else:
            raise ValueError("CSV must start with website row")

        for row in reader:
            if not row or len(row) < 2:
                continue
            t = row[0].strip().lower()
            strings = [s.strip() for s in row[1:] if s.strip()]
            if t == "official":
                official_strings.extend(strings)
            elif t == "detect":
                detect_strings.extend(strings)
            elif t == "fuzzy":
                spellcheck_strings.extend(strings)

    return start_url, official_strings, detect_strings, spellcheck_strings

# ---------------- Helper ----------------
def normalize_url(url):
    """Normalize a URL by removing fragments and query strings."""
    parsed = urlparse(url)
    normalized = urlunparse((parsed.scheme, parsed.netloc, parsed.path, '', '', ''))
    return normalized

# ---------------- Scraper ----------------
def scrape_site(start_url, official_strings, detect_strings, spellcheck_strings, regex_patterns=None, fuzzy_threshold=85):
    """Crawl a site, detect variations, fuzzy typos, and regex matches."""
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
        print(f"\nVisited: {current_url}")

        try:
            page_text = driver.find_element(By.TAG_NAME, "body").text

            # 1️⃣ Regex matches, skipping official strings
            if regex_patterns:
                for pattern in regex_patterns:
                    for match in pattern.findall(page_text):
                        if match in official_strings:
                            continue
                        matches.append((current_url, match, "regex"))
                        print(f"DEBUG: Regex matched '{match}' in {current_url}")

            # 2️⃣ Detect strings: exact substring matches
            for s in detect_strings:
                if s in official_strings:
                    continue
                pattern = re.compile(re.escape(s), re.IGNORECASE)
                for match in pattern.findall(page_text):
                    matches.append((current_url, match, f"detect '{s}'"))
                    print(f"DEBUG: Detected '{match}' for '{s}' in {current_url}")

            # 3️⃣ Fuzzy / spellcheck for typos
            for line in page_text.split("\n"):
                line_lower = line.lower()
                if any(s.lower() in line_lower for s in official_strings):
                    continue
                for s in spellcheck_strings:
                    score = fuzz.ratio(line_lower, s.lower())
                    if score >= fuzzy_threshold:
                        matches.append((current_url, line.strip(), f"fuzzy '{s}'"))
                        print(f"DEBUG: Fuzzy matched '{line.strip()}' for '{s}' in {current_url} (score={score})")

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

# ---------------- CSV Output ----------------
def save_matches_to_csv(matches, filename="matches.csv"):
    with open(filename, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["URL", "Matched_Text", "Match_Type"])
        for match in matches:
            writer.writerow(match)
    print(f"\nSaved {len(matches)} matches to {filename}")

# ---------------- Main ----------------
if __name__ == "__main__":
    # Load website and strings from CSV
    start_url, official_strings, detect_strings, spellcheck_strings = load_strings_with_website("strings_to_check.csv")

    # DEBUG
    print("---- DEBUG: Loaded CSV ----")
    print("Start URL:", start_url)
    print("Official strings:", official_strings)
    print("Detect strings:", detect_strings)
    print("Fuzzy strings:", spellcheck_strings)
    print("----------------------------\n")

    # Optional regex patterns
    regex_patterns = [
        re.compile(r"dana[-– ]?farber", re.IGNORECASE),
        re.compile(r"dfbcc", re.IGNORECASE)
    ]

    # Run scraper
    found_matches = scrape_site(
        start_url,
        official_strings,
        detect_strings,
        spellcheck_strings,
        regex_patterns=regex_patterns,
        fuzzy_threshold=85
    )

    # Save results
    save_matches_to_csv(found_matches)
