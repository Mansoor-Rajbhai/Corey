# X:\Corey\utilities\browser_automation.py
from playwright.sync_api import sync_playwright
import time

def browse_and_interact(url: str, actions: list = None):
    """
    Launches a browser to navigate a site, processes macros, 
    and captures all raw text and link structures for the AI to parse.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=15000)
            time.sleep(2)
            
            if actions:
                for action in actions:
                    act_type = action.get("type")
                    if act_type == "scroll":
                        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                        time.sleep(1.5)
                    elif act_type == "click":
                        selector = action.get("selector")
                        if page.is_visible(selector):
                            page.click(selector, timeout=5000)
                            time.sleep(2)
            
            # Extract EVERY link structure on the page
            links = []
            for a in page.query_selector_all("a"):
                href = a.get_attribute("href")
                text = a.inner_text().strip()
                if href:
                    links.append({"text": text, "url": href})
            
            # Extract the absolute raw text string of the entire page layout
            raw_text = page.locator("body").inner_text()
            
            return {
                "status": "success",
                "current_url": page.url,
                "title": page.title(),
                "raw_text_content": raw_text,
                "discovered_links": links
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
        finally:
            browser.close()