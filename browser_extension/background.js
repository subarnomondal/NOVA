// Nova Extensions - Browser Control Service Worker
// Handles persistent browser actions and tab management

// Cross-browser shim
const ext = (typeof chrome !== "undefined") ? chrome : (typeof browser !== "undefined") ? browser : {};

ext.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "navigate") {
        ext.tabs.update({ url: request.url }, (tab) => {
            sendResponse({ status: "Navigated to " + request.url 
    if (request.action === "get_dom_map") {
        ext.tabs.query({ active: true, currentWindow: true }, (tabs) => {
            if (tabs[0]) {
                ext.scripting.executeScript({
                    target: { tabId: tabs[0].id },
                    func: () => {
                        // Remove existing
                        document.querySelectorAll('.nova-dom-label').forEach(el => el.remove());
                        
                        let elements = document.querySelectorAll('a, button, input, select, textarea, [role="button"], [role="link"], [role="menuitem"], [onclick]');
                        let interactables = [];
                        let id_counter = 1;
                        
                        elements.forEach(el => {
                            let rect = el.getBoundingClientRect();
                            let style = window.getComputedStyle(el);
                            let isVisible = rect.width > 0 && rect.height > 0 && 
                                            style.visibility !== 'hidden' && style.display !== 'none' && 
                                            style.opacity !== '0';
                            
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
                        return interactables.join('\n');
                    }
                }, (results) => {
                    if (results && results[0]) {
                        sendResponse({ data: results[0].result });
                    } else {
                        sendResponse({ error: "Failed to map DOM" });
                    }
                });
            } else {
                sendResponse({ error: "No active tab" });
            }
        });
        return true;
    }

    if (request.action === "click_element" || request.action === "type_element") {
        ext.tabs.query({ active: true, currentWindow: true }, (tabs) => {
            if (tabs[0]) {
                ext.scripting.executeScript({
                    target: { tabId: tabs[0].id },
                    args: [request.nova_id, request.action, request.value],
                    func: (novaId, actionType, val) => {
                        let el = document.querySelector(`[nova-id="${novaId}"]`);
                        if (!el) return { success: false, error: "Element not found" };
                        
                        if (actionType === "click_element") {
                            el.click();
                            return { success: true, message: `Clicked element ${novaId}` };
                        } else if (actionType === "type_element") {
                            el.value = val;
                            el.dispatchEvent(new Event('input', { bubbles: true }));
                            el.dispatchEvent(new Event('change', { bubbles: true }));
                            return { success: true, message: `Typed into element ${novaId}` };
                        }
                    }
                }, (results) => {
                    if (results && results[0]) {
                        sendResponse({ data: results[0].result });
                    } else {
                        sendResponse({ error: "Action failed" });
                    }
                });
            } else {
                sendResponse({ error: "No active tab" });
            }
        });
        return true;
    }
});
        });
        return true;
    }

    if (request.action === "get_active_tab_content") {
        ext.tabs.query({ active: true, currentWindow: true }, (tabs) => {
            if (tabs[0]) {
                ext.scripting.executeScript({
                    target: { tabId: tabs[0].id },
                    func: () => {
                        return {
                            title: document.title,
                            url: window.location.href,
                            content: document.body.innerText.substring(0, 3000) // Limit content
                        };
                    }
                }, (results) => {
                    if (results && results[0]) {
                        sendResponse({ data: results[0].result });
                    } else {
                        sendResponse({ error: "Could not read page content" });
                    }
                });
            } else {
                sendResponse({ error: "No active tab found" });
            }
        });
        return true;
    }
});
