"""
Browser Control Skill for Nova
Enables Nova to navigate tabs and read page content via the browser extension.
"""

def cmd_browser_nav(args):
    """Usage: browse to <url> or visit <url>"""
    url = args.lower().replace("browse to", "").replace("visit", "").replace("open website", "").strip()
    if not url:
        return "Which website should I open for you? 🌐"
    
    if not url.startswith("http"):
        url = "https://" + url
        
    return {
        "response": f"*nods* Opening {url} for you now! 🌐",
        "data": {
            "browser_action": "navigate",
            "url": url
        }
    }

def cmd_read_page(args):
    """Usage: read this page or what's on this website?"""
    return {
        "response": "Let me take a look at the current page for you... 🔍",
        "data": {
            "browser_action": "read_page"
        }
    }

def register(dispatcher):
    dispatcher.register("browse to", cmd_browser_nav)
    dispatcher.register("visit", cmd_browser_nav)
    dispatcher.register("open website", cmd_browser_nav)
    dispatcher.register("read this page", cmd_read_page)
    dispatcher.register("what's on this page", cmd_read_page)
