// Nova Extensions - Browser Control Service Worker
// Handles persistent browser actions and tab management

// Cross-browser shim
const ext = (typeof chrome !== "undefined") ? chrome : (typeof browser !== "undefined") ? browser : {};

ext.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "navigate") {
        ext.tabs.update({ url: request.url }, (tab) => {
            sendResponse({ status: "Navigated to " + request.url });
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
