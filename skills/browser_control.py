"""
Browser Control Skill for Clio
Enables Clio to navigate tabs and read page content via the browser extension.
"""

def cmd_browser_nav(args):
    """Usage: browse to <url> or visit <url>"""
    import re
    # Clean up common prefixes
    url = re.sub(r'^(?:browse to|visit|open website|go to)\s+', '', args, flags=re.IGNORECASE).strip()
    
    if not url:
        return "Which website should I open for you? "
    
    # Handle simple names (add .com if no dot)
    if '.' not in url:
        url += ".com"
        
    if not url.startswith("http"):
        url = "https://" + url
        
    return {
        "response": f"Opening **{url}** for you now! ",
        "data": {
            "browser_action": "navigate",
            "url": url
        }
    }

# ponytail: cmd_browser_search removed (duplicate handled by skills.browser_agent)

def cmd_read_page(args):
    """Usage: read this page or what's on this website?"""
    return {
        "response": "Alright, let me analyze the contents of this page for you... ",
        "data": {
            "browser_action": "read_page"
        }
    }

def register(dispatcher):
    dispatcher.register("browse to", cmd_browser_nav)
    dispatcher.register("visit", cmd_browser_nav)
    dispatcher.register("open website", cmd_browser_nav)
    # ponytail: browser search registration removed
    dispatcher.register("read this page", cmd_read_page)
    dispatcher.register("what's on this page", cmd_read_page)
