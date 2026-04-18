const API_URL = 'http://localhost:5000/api';

// Cross-browser shim
const ext = (typeof chrome !== "undefined" && chrome.runtime) ? chrome : (typeof browser !== "undefined" && browser.runtime) ? browser : {};

// DOM Elements
const chatArea = document.getElementById('chat-area');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');
const statusDot = document.getElementById('status-dot');
const modelBadge = document.getElementById('model-badge');
const thinkToggle = document.getElementById('think-toggle');
const thinkingPanel = document.getElementById('thinking-panel');
const thinkingContent = document.getElementById('thinking-content');
const thinkModel = document.getElementById('think-model');

let isProcessing = false;
let isOnline = false;
let welcomeVisible = true;

// =====================
// CONNECTION CHECK
// =====================
async function checkConnection() {
    try {
        const res = await fetch(`${API_URL}/status`, { signal: AbortSignal.timeout(3000) });
        const data = await res.json();
        isOnline = true;
        statusDot.className = 'status-dot online';
        modelBadge.textContent = data.model || 'Connected';
        return true;
    } catch (e) {
        isOnline = false;
        statusDot.className = 'status-dot offline';
        modelBadge.textContent = 'Offline';
        return false;
    }
}

// =====================
// CHAT RENDERING
// =====================
function hideWelcome() {
    if (!welcomeVisible) return;
    const welcome = chatArea.querySelector('.welcome-state');
    if (welcome) {
        welcome.style.opacity = '0';
        welcome.style.transform = 'scale(0.95)';
        setTimeout(() => welcome.remove(), 200);
    }
    welcomeVisible = false;
}

function addMessage(text, type) {
    hideWelcome();

    const msgDiv = document.createElement('div');
    msgDiv.className = `msg ${type}`;

    const avatar = document.createElement('div');
    avatar.className = 'msg-avatar';
    avatar.textContent = type === 'user' ? '👤' : '✦';

    const bubble = document.createElement('div');
    bubble.className = 'msg-bubble';

    // Basic markdown-like formatting
    let formatted = text
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/\n/g, '<br>');
    bubble.innerHTML = formatted;

    msgDiv.appendChild(avatar);
    msgDiv.appendChild(bubble);
    chatArea.appendChild(msgDiv);
    chatArea.scrollTop = chatArea.scrollHeight;
}

function addSystemMsg(text) {
    hideWelcome();
    const div = document.createElement('div');
    div.className = 'system-msg';
    div.textContent = text;
    chatArea.appendChild(div);
}

function showThinking() {
    hideWelcome();
    const indicator = document.createElement('div');
    indicator.className = 'msg nova';
    indicator.id = 'thinking-indicator';
    indicator.innerHTML = `
        <div class="msg-avatar" style="background:linear-gradient(135deg,#8a2be2,#06b6d4);">✦</div>
        <div class="thinking-indicator">
            <span>Thinking</span>
            <div class="thinking-dots">
                <span></span><span></span><span></span>
            </div>
        </div>
    `;
    chatArea.appendChild(indicator);
    chatArea.scrollTop = chatArea.scrollHeight;
}

function hideThinking() {
    const el = document.getElementById('thinking-indicator');
    if (el) el.remove();
}

// =====================
// THINKING PANEL
// =====================
function renderThoughts(thoughts, model) {
    if (!thoughts || thoughts.length === 0) return;

    thinkingContent.innerHTML = '';

    thoughts.forEach((step, i) => {
        const stepDiv = document.createElement('div');
        stepDiv.className = 'think-step';
        stepDiv.textContent = step;
        stepDiv.style.animationDelay = `${i * 0.08}s`;
        thinkingContent.appendChild(stepDiv);
    });

    if (model) {
        const shortName = model.split('/').pop().replace(':free', '').toUpperCase();
        thinkModel.textContent = shortName;
        thinkModel.title = model;
    }

    // Auto-open thinking panel only if it wasn't manually closed
    if (thinkingPanel.dataset.manuallyClosed !== 'true') {
        thinkingPanel.classList.remove('collapsed');
        thinkToggle.classList.add('active');
    }

    // Always scroll to bottom of thoughts
    thinkingContent.scrollTop = thinkingContent.scrollHeight;
}

thinkToggle.addEventListener('click', () => {
    const isCollapsing = !thinkingPanel.classList.contains('collapsed');
    thinkingPanel.classList.toggle('collapsed');
    thinkToggle.classList.toggle('active');

    // Remember user preference for this session
    if (isCollapsing) {
        thinkingPanel.dataset.manuallyClosed = 'true';
    } else {
        thinkingPanel.dataset.manuallyClosed = 'false';
    }
});

// =====================
// SEND COMMAND
// =====================
async function sendCommand(text) {
    if (!text.trim() || isProcessing) return;

    isProcessing = true;
    sendBtn.disabled = true;

    const userText = text.trim();
    addMessage(userText, 'user');
    userInput.value = '';

    // Check connectivity
    if (!isOnline) {
        const connected = await checkConnection();
        if (!connected) {
            addSystemMsg('⚠️ Nova is offline. Make sure desktop.py is running.');
            isProcessing = false;
            sendBtn.disabled = false;
            return;
        }
    }

    showThinking();

    try {
        const res = await fetch(`${API_URL}/command`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                command: userText,
                language: 'en',
                source: 'browser_extension'
            })
        });

        const data = await res.json();
        hideThinking();

        if (data.response) {
            addMessage(data.response, 'nova');

            // Update thinking panel
            if (data.thoughts && data.thoughts.length > 0) {
                renderThoughts(data.thoughts, data.llm_model);
            }

            // Handle Browser Actions
            if (data.data && data.data.browser_action) {
                executeBrowserAction(data.data);
            }

            // Update model badge
            if (data.llm_model) {
                const shortName = data.llm_model.split('/').pop().replace(':free', '');
                modelBadge.textContent = shortName;
            } else if (data.skill_direct) {
                modelBadge.textContent = 'Skill';
            }
        } else {
            addSystemMsg('No response received.');
        }

    } catch (e) {
        hideThinking();
        console.error('Send error:', e);
        addSystemMsg('❌ Connection failed. Is Nova running?');
        isOnline = false;
        statusDot.className = 'status-dot offline';
        modelBadge.textContent = 'Offline';
    } finally {
        isProcessing = false;
        sendBtn.disabled = false;
        userInput.focus();
    }
}

// =====================
// BROWSER CONTROL
// =====================
async function executeBrowserAction(data) {
    if (data.browser_action === "navigate") {
        ext.runtime.sendMessage({ action: "navigate", url: data.url }, (response) => {
            console.log("Browser response:", response);
        });
    } else if (data.browser_action === "read_page") {
        ext.runtime.sendMessage({ action: "get_active_tab_content" }, (response) => {
            if (response && response.data) {
                // Send the page content back to Nova backend for analysis
                const summary = `I've read the page: "${response.data.title}". Here is the content Summary: ${response.data.content.substring(0, 500)}...`;
                addSystemMsg(`Reading: ${response.data.title}`);

                // Optional: Re-send to Nova for a deep dive if needed
                // For now, let's just confirm we read it
                addMessage("I can see that this page is about " + response.data.title + ". What would you like me to find here?", 'nova');
            } else {
                addMessage("I couldn't read the page content. Make sure you're on a valid website.", 'nova');
            }
        });
    }
}

// =====================
// EVENT LISTENERS
// =====================
sendBtn.addEventListener('click', () => {
    sendCommand(userInput.value);
});

userInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendCommand(userInput.value);
    }
});

// =====================
// INIT
// =====================
(async function init() {
    userInput.focus();
    await checkConnection();

    // Periodic connection check
    setInterval(checkConnection, 15000);
})();
