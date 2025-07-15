import json
import time
from pathlib import Path
from urllib.parse import urljoin

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


# ------------ configuration ------------
START_URL      = "https://f1store.formula1.com"
OUTFILE        = Path("f1_store_items.json")

WAIT_PAGE      = 10     # general explicit wait
SCROLL_PAUSE   = 0.35   # smooth scroll pause
WAIT_DETAILS   = 10     # wait inside product page
HEADLESS       = False  # set True if you do not need a visible browser
# ----------------------------------------


def launch_browser() -> webdriver.Chrome:
    """Return a Selenium Chrome driver with sane defaults."""
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    if HEADLESS:
        options.add_argument("--headless=new")

    driver = webdriver.Chrome(
        service=ChromeService(ChromeDriverManager().install()),
        options=options
    )
    return driver


# ---------- list page helpers ----------
def wait_for_cards(driver):
    """Wait for product cards to appear"""
    try:
        WebDriverWait(driver, WAIT_PAGE).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.ds-card"))
        )
    except:
        WebDriverWait(driver, WAIT_PAGE).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "[class*='product-card'], article[class*='card']"))
        )


def scroll_to_bottom(driver):
    last_h = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(SCROLL_PAUSE)
        new_h = driver.execute_script("return document.body.scrollHeight")
        if new_h == last_h:
            break
        last_h = new_h


def extract_cards(driver, container: list):
    wait_for_cards(driver)
    scroll_to_bottom(driver)

    cards = driver.find_elements(By.CSS_SELECTOR, "div.ds-card")
    if not cards:
        cards = driver.find_elements(By.CSS_SELECTOR, "[class*='product-card'], article[class*='card']")
    
    for card in cards:
        try:
            link  = card.find_element(By.CSS_SELECTOR, "a")
            title = card.find_element(By.CSS_SELECTOR, "[class*='title'], [class*='name'], h2, h3, h4").text.strip()
        except Exception:
            continue

        url = link.get_attribute("href") or ""
        if url.startswith("/"):
            url = urljoin(START_URL, url)

        # Extract prices - keep it simple
        current_price = ""
        original_price = ""
        try:
            price_container = card.find_element(By.CSS_SELECTOR, "[class*='price']").text.strip()
            price_lines = price_container.splitlines()
            
            if price_lines:
                # First line is usually current/sale price
                current_price = price_lines[0].strip()
                
                # If there's a second line, it's the original price
                if len(price_lines) > 1:
                    original_price = price_lines[1].strip()
                    
        except Exception:
            pass

        container.append({
            "title": title,
            "price": current_price,
            "original_price": original_price,
            "url": url,
            "available_sizes": []  # Will be filled from detail page
        })


def click_next(driver) -> bool:
    """Clicks the next-page arrow. Returns False if no more pages."""
    try:
        nxt = driver.find_element(By.CSS_SELECTOR, "a[data-trk-id='next-page']")
        if nxt.get_attribute("aria-disabled") == "true":
            return False
        driver.execute_script("arguments[0].scrollIntoView()", nxt)
        time.sleep(0.5)
        nxt.click()
        WebDriverWait(driver, WAIT_PAGE).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "a.page-link.current-page"))
        )
        return True
    except Exception:
        return False


# ---------- product-detail helpers ----------
def parse_detail(driver) -> list[str]:
    """Return available_sizes only"""
    # Wait for page to load
    try:
        WebDriverWait(driver, WAIT_DETAILS).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".size-selector-list, [class*='size-selector']"))
        )
        time.sleep(0.5)
    except:
        return []

    # Get available sizes
    available_sizes = []
    try:
        available_labels = driver.find_elements(
            By.CSS_SELECTOR, 
            "label.size-selector-button.available"
        )
        
        for label in available_labels:
            try:
                size_input = label.find_element(By.CSS_SELECTOR, "input[name='size-selector']")
                size_value = size_input.get_attribute("value")
                if size_value and size_value not in available_sizes:
                    available_sizes.append(size_value)
            except:
                size_text = label.find_element(By.CSS_SELECTOR, ".size-text, span").text.strip()
                if size_text and size_text not in available_sizes:
                    available_sizes.append(size_text)
    except:
        pass

    return available_sizes


def enrich_with_detail(driver, items: list):
    """Open each URL in a new tab, scrape sizes."""
    home = driver.current_window_handle

    for idx, item in enumerate(items, 1):
        url = item["url"]
        print(f"  [{idx}/{len(items)}] Getting sizes → {item['title'][:50]}...")
        
        driver.execute_script("window.open(arguments[0]);", url)
        driver.switch_to.window(driver.window_handles[-1])

        try:
            sizes = parse_detail(driver)
            item["available_sizes"] = sizes
            
            if sizes:
                print(f"    ✓ Found sizes: {', '.join(sizes)}")
                
        except Exception as e:
            print(f"    ⚠ Error: {e}")
            item["available_sizes"] = []

        driver.close()
        driver.switch_to.window(home)


def scrape_session(driver):
    """Single scraping session"""
    items = []
    page = 1
    
    while True:
        print(f"\n─── Scraping list page {page} ───", flush=True)
        try:
            extract_cards(driver, items)
            print(f"   Found {len(items)} total items so far")
        except Exception as e:
            print(f"   ⚠ Error on page {page}: {e}")
            break

        if not click_next(driver):
            break
        page += 1

    print(f"\nCollected {len(items)} items from list pages.", flush=True)
    
    if items:
        print("Now visiting product pages for sizes…\n", flush=True)
        enrich_with_detail(driver, items)
    
    return items


def main():
    print("▶  STARTING …", flush=True)

    try:
        print("   – Launching browser", flush=True)
        driver = launch_browser()
    except Exception as e:
        print("✖  Could not launch browser:", e)
        return

    all_items = []
    
    while True:
        print("\n" + "="*50)
        print("   – Opening F1 Store", flush=True)
        driver.get(START_URL)
        
        print(
            "\nMANUAL STEP:\n"
            " 1. Apply any filters you wish in the browser window.\n"
            " 2. When you see the first page of results, come back here and press ENTER.",
            flush=True,
        )
        input("Press ENTER to start scraping… ")
        
        session_items = scrape_session(driver)
        
        # Add to all items (avoiding duplicates by URL)
        existing_urls = {item['url'] for item in all_items}
        new_items = [item for item in session_items if item['url'] not in existing_urls]
        all_items.extend(new_items)
        
        print(f"\n✓ Added {len(new_items)} new items (Total: {len(all_items)})")
        
        print("\n" + "-"*50)
        choice = input("Do you want to scrape more items? (y/n): ").strip().lower()
        
        if choice != 'y':
            break
    
    # Save all results
    if all_items:
        try:
            OUTFILE.write_text(
                json.dumps(all_items, ensure_ascii=False, indent=2), 
                encoding="utf-8"
            )
            print(f"\n✓  Done! Saved {len(all_items)} items to {OUTFILE.resolve()}", flush=True)
            
            # Print summary
            items_with_sizes = sum(1 for item in all_items if item.get("available_sizes"))
            print(f"\nSummary:")
            print(f"  - Total items: {len(all_items)}")
            print(f"  - Items with available sizes: {items_with_sizes}")
        except Exception as e:
            print(f"\n✖ Error saving file: {e}")
            # Try to save with a different name
            backup_file = Path(f"f1_store_items_backup_{int(time.time())}.json")
            backup_file.write_text(
                json.dumps(all_items, ensure_ascii=False, indent=2), 
                encoding="utf-8"
            )
            print(f"✓  Saved backup to {backup_file.resolve()}")
    else:
        print("\n✖ No items were collected.")
    
    close = input("\nClose browser? (y/n): ").strip().lower()
    if close == 'y':
        driver.quit()
        print("Browser closed.")
    else:
        print("Browser left open. Close it manually when done.")


if __name__ == "__main__":
    main()