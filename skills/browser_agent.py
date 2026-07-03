"""
Browser Agent Skill for NOVA
Autonomous web navigation, data extraction, and form filling using Playwright and DDGS.
"""

import os
import time
import logging
import concurrent.futures
from duckduckgo_search import DDGS

try:
    from playwright.sync_api import sync_playwright # type: ignore
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False

# Setup screenshot directory
SCREENSHOT_DIR = os.path.join("userdata", "screenshots")
if not os.path.exists(SCREENSHOT_DIR):
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)

class BrowserAgent:
    def __init__(self):
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        self._playwright = None
        self._browser = None
        self._context = None
        self._page = None
        self._last_error = ""


    def _block_ads(self, route):
        url = route.request.url
        ad_domains = [
            "doubleclick.net", "google-analytics.com", "googlesyndication.com",
            "facebook.net", "facebook.com/tr", "analytics.", "ads.", "tracker.",
            "adsystem.", "adserver.", "scorecardresearch.com", "quantserve.com",
            "amazon-adsystem.com", "outbrain.com", "taboola.com"
        ]
        if any(domain in url for domain in ad_domains) or "/ads/" in url or "/ad/" in url:
            route.abort()
        else:
            route.continue_()

    def _load_cookies(self):
        cookie_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "userdata", "config", "cookies.txt")
        if not os.path.exists(cookie_file):
            return
            
        try:
            print(f"[Browser] Loading cookies from {cookie_file}...")
            cookies_to_add = []
            with open(cookie_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.startswith('#') or not line.strip():
                        continue
                    parts = line.strip().split('	')
                    if len(parts) >= 7:
                        domain = parts[0]
                        path = parts[2]
                        secure = parts[3].upper() == 'TRUE'
                        name = parts[5]
                        value = parts[6]
                        
                        cookies_to_add.append({
                            "name": name,
                            "value": value,
                            "domain": domain,
                            "path": path,
                            "secure": secure
                        })
            if cookies_to_add and self._context:
                self._context.add_cookies(cookies_to_add)
                print(f"[Browser] Loaded {len(cookies_to_add)} cookies successfully.")
        except Exception as e:
            print(f"[Browser] Error loading cookies: {e}")

    def _ensure_browser(self):
        """Lazy load the browser ONLY when needed."""
        if self._page and self._page.is_closed():
            print("[Browser] Target was closed manually. Restarting engine...")
            self._do_close_internal()
            
        if not self._page:
            if not HAS_PLAYWRIGHT:
                print("[Browser] Playwright not installed. Please run 'pip install playwright' and then 'playwright install' in your terminal.")
                return False
            try:
                print("[Browser] Initializing Engine (Playwright)...")
                self._playwright = sync_playwright().start()
                self._browser = self._playwright.chromium.launch(headless=False)
                self._context = self._browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    viewport={'width': 1280, 'height': 720}
                )
                self._page = self._context.new_page()
                # Ad-blocking route interception
                self._context.route("**/*", self._block_ads)
                # Load cookies if they exist
                self._load_cookies()
                print("[Browser] Engine Ready")
            except Exception as e:
                print(f"[Browser] Init Error: {e}")
                self._last_error = str(e)
                return False
        return True

    def _run_in_browser_thread(self, func, *args, **kwargs):
        """Ensures all Playwright calls happen on a single dedicated thread."""
        def wrapper():
            if not self._ensure_browser():
                return "ERROR: Could not initialize browser engine."
            return func(*args, **kwargs)
        try:
            return self._executor.submit(wrapper).result()
        except Exception as e:
            return f"Browser Error: {e}"

    def _do_close_internal(self):
        if self._browser:
            try: self._browser.close()
            except: pass
        if self._playwright:
            try: self._playwright.stop()
            except: pass
        self._page = None
        self._browser = None
        self._context = None
        self._playwright = None
        print("[Browser] Engine Shutdown")

    def close(self):
        """Explicitly shut down the browser to save RAM."""
        try:
            self._executor.submit(self._do_close_internal).result()
        except Exception:
            pass

    def open_url(self, url):
        def _do_open_url(u):
            if not self._page:
                return "Error: Browser page not initialized."
            try:
                print(f"[Browser] Navigating to: {u}")
                self._page.goto(u, wait_until="domcontentloaded", timeout=15000)
                try: self._page.wait_for_load_state("networkidle", timeout=1000)
                except Exception:
                    pass
                return self._do_map_internal()
            except Exception as e:
                return f"Failed to open {u}: {str(e)}"
        return self._run_in_browser_thread(_do_open_url, url)

    def search_and_browse(self, query):
        """Uses DDGS to find the top result then visits it."""
        print(f"[Browser] Searching for: {query} using DDGS...")
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=1))
                if not results:
                    return f"Hmm, I couldn't find any results for '{query}' on DuckDuckGo."
                
                target_url = results[0]['href']
                title = results[0]['title']
                print(f"[Browser] Top Result: {title} ({target_url})")
                
                nav_response = self.open_url(target_url)
                return f"I searched for '{query}' and found: **{title}**.\n\n{nav_response}"
        except Exception as e:
            return f"Search failure: {str(e)}"

    def _do_map_internal(self):
        if not self._page:
            return "I don't have any page open right now. Open a site first!"
        try:
            print("[Browser] Injecting Antigravity DOM Annotator...")

            dom_map = self._page.evaluate(r"""() => {
                document.querySelectorAll('.nova-dom-label').forEach(el => el.remove());
                
                let elements = document.querySelectorAll('a, button, input, select, textarea, [role="button"], [role="link"], [role="menuitem"], [onclick]');
                let interactables = [];
                let id_counter = 1;
                
                elements.forEach(el => {
                    let rect = el.getBoundingClientRect();
                    let style = window.getComputedStyle(el);
                    let isVisible = rect.width > 0 && rect.height > 0 && 
                                    style.visibility !== 'hidden' && style.display !== 'none' && 
                                    style.opacity !== '0' &&
                                    rect.top >= 0 && rect.left >= 0 &&
                                    rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
                                    rect.right <= (window.innerWidth || document.documentElement.clientWidth);
                    
                    if (isVisible) {
                        let id = id_counter++;
                        el.setAttribute('nova-id', id);
                        
                        let label = document.createElement('div');
                        label.className = 'nova-dom-label';
                        label.textContent = id;
                        label.style.position = 'absolute';
                        label.style.left = (rect.left + window.scrollX) + 'px';
                        label.style.top = (rect.top + window.scrollY) + 'px';
                        label.style.backgroundColor = 'rgba(0, 255, 255, 0.9)';
                        label.style.color = '#000';
                        label.style.border = '1px solid #fff';
                        label.style.padding = '1px 3px';
                        label.style.fontSize = '12px';
                        label.style.fontWeight = 'bold';
                        label.style.zIndex = '999999';
                        label.style.pointerEvents = 'none';
                        label.style.boxShadow = '0 0 5px cyan';
                        document.body.appendChild(label);
                        
                        let text = (el.innerText || el.value || el.placeholder || el.getAttribute('aria-label') || '').trim();
                        if (text.length > 50) text = text.substring(0, 47) + '...';
                        
                        interactables.push(`[${id}] ${el.tagName.toLowerCase()} "${text}"`);
                    }
                });
                return {
                    title: document.title,
                    url: window.location.href,
                    map: interactables.join('\n')
                };
            }""")

            response = f"**Current Page:** {dom_map['title']}\n**URL:** {dom_map['url']}\n\n"
            response += f"**Interactable Elements (Visible on Screen):**\n{dom_map['map']}\n\n"
            response += "To interact, you can use `browser click [id]` or `browser type [id] [text]`."

            return response
        except Exception as e:
            return f"DOM mapping error: {str(e)}"

    def map_dom(self):
        """Autonomous DOM mapping for Antigravity-style LLM navigation."""
        return self._run_in_browser_thread(self._do_map_internal)

    def interact(self, action_type, selector_or_id, value=None):
        """Performs clicks or typing via CSS selector or nova-id."""
        def _do_interact(a_type, sel, val):
            if not self._page:
                return "No page is open for interaction."
                
            try:
                # Determine if it's an ID or a standard selector
                if str(sel).isdigit():
                    sel = f'[nova-id="{sel}"]'
                
                if a_type == "click":
                    self._page.click(sel, timeout=10000)
                elif a_type == "type":
                    self._page.fill(sel, val, timeout=10000)
                    self._page.press(sel, "Enter") # auto submit on type to be helpful
                elif a_type == "submit":
                    self._page.press(sel, "Enter")
                
                # Wait briefly for DOM to update after interaction
                try: self._page.wait_for_load_state("networkidle", timeout=1000)
                except: pass
                
                return self._do_map_internal()
            except Exception as e:
                return f"Interaction failed on {sel}: {str(e)}"
        return self._run_in_browser_thread(_do_interact, action_type, selector_or_id, value)

    def screenshot(self):
        """Captures a screenshot of the current page."""
        def _do_screenshot():
            if not self._page:
                return "Nothing to screenshot! Open a page first."
                
            try:
                import time, os
                filename = f"capture_{int(time.time())}.png"
                relative_path = os.path.join("userdata", "screenshots", filename)
                web_url = f"userdata/screenshots/{filename}"
                
                self._page.screenshot(path=relative_path)
                
                return {
                    "response": f"I've captured a screenshot of the current page! (Saved as {filename})",
                    "data": {
                        "type": "image",
                        "url": web_url
                    }
                }
            except Exception as e:
                return f"Screenshot failed: {str(e)}"
        return self._run_in_browser_thread(_do_screenshot)

# Singleton instance
agent = BrowserAgent()

# --- Dispatcher Commands ---

def cmd_browser_navigate(args):
    """Usage: browse to [url]"""
    url = args.lower().replace("browse to", "").replace("visit", "").replace("open", "").strip()
    if not url: return "Where should I go? Please provide a URL."
    if not url.startswith("http"): url = "https://" + url
    return agent.open_url(url)

def cmd_browser_search(args):
    """Usage: search and browse [query]"""
    query = args.lower().replace("search and browse", "").replace("find on web", "").strip()
    if not query: return "Search for what? Try 'search and browse latest bitcoin price'. "
    return agent.search_and_browse(query)

def cmd_browser_map(args):
    """Usage: auto browse or map dom"""
    args = args.lower().replace("auto browse", "").replace("map dom", "").strip()
    if args.startswith("to "):
        url = args[3:].strip()
        if not url.startswith("http"): url = "https://" + url
        return agent.open_url(url)
    elif args:
        return agent.search_and_browse(args)
    return agent.map_dom()

def cmd_browser_snap(args):
    """Usage: take screenshot or snap page"""
    return agent.screenshot()

def cmd_browser_fill(args):
    """Usage: browser type [selector] [value]"""
    parts = args.replace("browser type", "").strip().split(" ", 1)
    if len(parts) < 2: return "I need both a selector and the text to type!"
    return agent.interact("type", parts[0], parts[1])

def cmd_browser_click(args):
    """Usage: browser click [selector]"""
    selector = args.replace("browser click", "").strip()
    if not selector: return "What should I click? (Need a CSS selector) ️"
    return agent.interact("click", selector)

def cmd_browser_close(args):
    """Usage: close browser or stop agent"""
    agent.close()
    return "The Browser Engine has been shut down to save resources."

def register(dispatcher):
    """Registers the browser agent commands."""
    dispatcher.register("browse to", cmd_browser_navigate)
    dispatcher.register("visit", cmd_browser_navigate)
    dispatcher.register("search and browse", cmd_browser_search)
    dispatcher.register("find on web", cmd_browser_search)
    dispatcher.register("auto browse", cmd_browser_map)
    dispatcher.register("map dom", cmd_browser_map)
    dispatcher.register("take screenshot", cmd_browser_snap)
    dispatcher.register("snap page", cmd_browser_snap)
    dispatcher.register("browser click", cmd_browser_click)
    dispatcher.register("browser type", cmd_browser_fill)
    dispatcher.register("stop browser", cmd_browser_close)
    dispatcher.register("close browser", cmd_browser_close)
