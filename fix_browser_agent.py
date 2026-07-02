import sys

with open('skills/browser_agent.py', 'r', encoding='utf-8') as f:
    code = f.read()

start_marker = '    def __init__(self):'
end_marker = '            except Exception as e:\n                return f"Screenshot failed: {str(e)}"'

start_idx = code.find(start_marker)
end_idx = code.find(end_marker)

if start_idx == -1 or end_idx == -1:
    print('Failed to find markers')
    sys.exit(1)

end_idx += len(end_marker)

replacement = r'''    def __init__(self):
        import concurrent.futures
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        self._playwright = None
        self._browser = None
        self._context = None
        self._page = None

    def _ensure_browser(self):
        """Lazy load the browser ONLY when needed."""
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

    def close(self):
        """Explicitly shut down the browser to save RAM."""
        def _do_close():
            if self._browser:
                self._browser.close()
            if self._playwright:
                self._playwright.stop()
            self._page = None
            self._browser = None
            self._playwright = None
            print("[Browser] Engine Shutdown")
        try:
            self._executor.submit(_do_close).result()
        except Exception:
            pass

    def open_url(self, url):
        def _do_open_url(u):
            try:
                print(f"[Browser] Navigating to: {u}")
                self._page.goto(u, wait_until="domcontentloaded", timeout=30000)
                try: self._page.wait_for_load_state("networkidle", timeout=5000)
                except: pass
                title = self._page.title()
                return f"*nods* I've arrived at the page: '{title}'. What should I look for here?"
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

    def extract_page_data(self):
        """Heuristic-based data extraction for prices, news, and tables."""
        def _do_extract():
            if not self._page:
                return "I don't have any page open right now. Open a site first!"
                
            try:
                print("[Browser] Extracting page data intelligently...")
                
                data = self._page.evaluate(r"""() => {
                    const getVisibleText = (el) => el.innerText.trim();
                    const priceMatch = document.body.innerText.match(/(\$|£|€|₹)\s?(\d{1,3}(,\d{3})*(\.\d{2})?)/g);
                    const tables = Array.from(document.querySelectorAll('table')).map(t => {
                        const rows = Array.from(t.rows).slice(0, 5).map(r => 
                            Array.from(r.cells).map(c => c.innerText.trim()).join(' | ')
                        ).join('\n');
                        return rows;
                    });
                    return {
                        title: document.title,
                        url: window.location.href,
                        prices: priceMatch ? priceMatch.slice(0, 5) : [],
                        tables: tables.slice(0, 3),
                        main_content: document.body.innerText.substring(0, 1500).replace(/\s+/g, ' ')
                    };
                }""")
                
                response = f" **Extracted Data from {data['title']}**\n\n"
                if data['prices']:
                    response += f" **Potential Prices Found:** {', '.join(data['prices'])}\n\n"
                
                if data['tables']:
                    response += " **Detected Tables (Preview):**\n"
                    for i, table in enumerate(data['tables'], 1):
                        response += f"Table {i}:\n{table}\n\n"
                
                response += f" **Content Preview:**\n{data['main_content'][:500]}..."
                
                return {
                    "response": response,
                    "data": {
                        "type": "browser_extraction",
                        "details": data
                    }
                }
            except Exception as e:
                return f"Extraction error: {str(e)}"
        return self._run_in_browser_thread(_do_extract)

    def interact(self, action_type, selector, value=None):
        """Performs clicks or typing."""
        def _do_interact(a_type, sel, val):
            if not self._page:
                return "No page is open for interaction."
                
            try:
                if a_type == "click":
                    self._page.click(sel, timeout=10000)
                    return f"Successfully clicked: `{sel}`"
                elif a_type == "type":
                    self._page.fill(sel, val, timeout=10000)
                    return f"Typed '{val}' into `{sel}`"
                elif a_type == "submit":
                    self._page.press(sel, "Enter")
                    return f"Pressed Enter on `{sel}`"
            except Exception as e:
                return f"Interaction failed on `{sel}`: {str(e)}"
        return self._run_in_browser_thread(_do_interact, action_type, selector, value)

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
        return self._run_in_browser_thread(_do_screenshot)'''

new_code = code[:start_idx] + replacement + code[end_idx:]

with open('skills/browser_agent.py', 'w', encoding='utf-8') as f:
    f.write(new_code)
print('Replaced successfully!')
