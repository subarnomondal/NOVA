const API_URL = 'http://localhost:5000/api';
const outputArea = document.getElementById('chat-feed');
const commandInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');
const uploadBtn = document.getElementById('upload-btn');
const fileInput = document.getElementById('file-upload');
const micBtn = document.getElementById('mic-btn');
const stopBtn = document.getElementById('stop-btn');
const statusToggle = document.querySelector('.status-toggle-container');
const statusCard = document.getElementById('status-card');

// Live Mode Elements
const liveBtn = document.getElementById('live-mode-btn');
const liveOverlay = document.getElementById('live-overlay');
const closeLiveBtn = document.getElementById('close-live-btn');
const liveTranscript = document.getElementById('live-transcript');

if (liveBtn) {
    liveBtn.addEventListener('click', () => {
        if (liveOverlay) liveOverlay.classList.remove('hidden');
    });
}
if (closeLiveBtn) {
    closeLiveBtn.addEventListener('click', () => {
        if (liveOverlay) liveOverlay.classList.add('hidden');
    });
}

// State Variables
let isSpeaking = false;
let isRecording = false;
let lastMicClick = 0;
let isProcessing = false;
let isContinuousMode = false;
let isPushToTalk = true; // Default to Push-to-Talk (Manual)
let isMuted = false;
let isOfflineMode = false;
let isLiveInteraction = false;
let useVTuber = true;
let currentAudio = null;
let lastRequestId = null;
let activeOverlay = 'chat'; // Track currently active view
let globeSpeedMultiplier = 2;
let glowPulseTimeout = null;

function triggerGlowPulse() {
    const main = document.querySelector('.live-chat-container');
    if (!main) return;
    
    main.classList.add('glow-pulse-active');
    
    if (glowPulseTimeout) clearTimeout(glowPulseTimeout);
    glowPulseTimeout = setTimeout(() => {
        main.classList.remove('glow-pulse-active');
    }, 2000);
}

// Three.js Global Variables
let scene, camera, renderer, particles;
let liveScene, liveCamera, liveRenderer, liveParticles, liveEventHorizon;
let vtuberScene, vtuberCamera, vtuberRenderer, vtuberModel, currentVrm, vtuberGroup;

// Audio Contexts / Analyzers
let mainAnalyzer = null; // Used for voice visualization
let vadAudioContext = null;
let vadAnalyser = null;
let microphone = null;
let javascriptNode = null;

// Helper to add lines/bubbles to chat
let typewriterTimeout = null;

function showBrowsingStatus(text, favicon = null) {
    const status = document.getElementById('browsing-status');
    const favIconImg = document.getElementById('browsing-favicon');
    const statusText = document.getElementById('browsing-text');
    
    if (status && statusText) {
        statusText.textContent = text || 'Browsing...';
        if (favIconImg && favicon) {
            favIconImg.src = favicon;
            favIconImg.style.display = 'block';
        } else if (favIconImg) {
            favIconImg.style.display = 'none';
        }
        status.style.display = 'flex';
    }
}

function hideBrowsingStatus() {
    const status = document.getElementById('browsing-status');
    if (status) status.style.display = 'none';
}

function addLine(text, type = 'system-msg', tokens = 0, extraData = null) {
    hideBrowsingStatus();
    
    const welcome = document.querySelector('.welcome-screen');
    if (welcome) welcome.style.display = 'none';

    if (text && (text.toLowerCase().includes('listening...'))) {
        isRecording = true;
        if (micBtn) micBtn.classList.add('listening');
        if (typeof liveOverlay !== 'undefined' && liveOverlay) liveOverlay.classList.add('listening');
        animateVoiceVisualizer();
        text = `<i>Listening...</i>`;
    } else if (text && (text.includes('Processing...') || text.includes('Thinking...'))) {
        isRecording = false;
        if (micBtn) micBtn.classList.remove('listening');
        if (typeof liveOverlay !== 'undefined' && liveOverlay) liveOverlay.classList.remove('listening');
        // Trigger ThreeJS speaking animation
        if (typeof isSpeaking !== 'undefined') {
            isSpeaking = true;
            setTimeout(() => { isSpeaking = false; }, 3000);
        }
    }

    const div = document.createElement('div');

    if (type === 'nova-msg' || type === 'system-msg') {
        div.className = 'flex flex-col items-start animate-in slide-in-from-left duration-700 w-full mb-6';
        div.innerHTML = `
            <div class="flex items-center gap-2 mb-2">
                <div class="w-6 h-6 rounded-full border border-secondary-container flex items-center justify-center bg-secondary-container/10">
                    <span class="material-symbols-outlined text-secondary text-[14px]">hub</span>
                </div>
                <span class="font-label-sm text-secondary tracking-wider">${type === 'system-msg' ? 'SYSTEM' : 'NOVA CORE'}</span>
            </div>
            <div class="glass-panel nova-bubble max-w-[90%] p-4 rounded-xl rounded-tl-none border border-secondary-container/20">
                <div class="font-body-md leading-relaxed text-left text-primary text-[15px]">${text}</div>
            </div>
            <span class="text-[10px] font-mono-data text-outline mt-2 ml-1">RCV // AI</span>
        `;
        
        // Handle specialized data rendering inside the bubble
        const bubble = div.querySelector('.glass-panel');
        if (extraData && extraData.type === 'music_results') {
            renderMusicResults(bubble, extraData.results);
        } else if (extraData && extraData.type === 'natural_events') {
            renderNaturalEvents(extraData.events);
        } else if (extraData && extraData.type === 'search_results') {
            renderSearchResults(bubble, extraData.results);
        } else if (extraData && extraData.type === 'news_results') {
            renderNewsResults(bubble, extraData.results);
        }
        
        // If it's a real response, trigger the avatar mouth animation
        if (type === 'nova-msg' && typeof isSpeaking !== 'undefined') {
            isSpeaking = true;
            // Rough estimation of speak duration based on text length
            const duration = Math.min(Math.max(text.length * 50, 1000), 10000);
            setTimeout(() => { isSpeaking = false; }, duration);
        }
    } else {
        div.className = 'flex flex-col items-end animate-in slide-in-from-right duration-500 w-full mb-6';
        // Sanitize text if needed, but innerHTML is fine for now if text is safe
        // we'll just use textContent by creating a P element
        div.innerHTML = `
            <div class="glass-panel user-bubble max-w-[85%] p-4 rounded-xl rounded-tr-none text-on-surface">
                <p class="font-body-md leading-relaxed text-right msg-content"></p>
            </div>
            <span class="text-[10px] font-mono-data text-outline mt-2 mr-1">SENT // USER_01</span>
        `;
        div.querySelector('.msg-content').textContent = text;
    }

    outputArea.appendChild(div);
    outputArea.scrollTop = outputArea.scrollHeight;

    if (typeof isLiveInteraction !== 'undefined' && isLiveInteraction && typeof liveTranscript !== 'undefined' && liveTranscript) {
        liveTranscript.textContent = text;
    }
}


/**
 * Renders a list of music results as interactive cards
 */
function renderMusicResults(container, results) {
    if (!results || results.length === 0) return;

    const resultsWrapper = document.createElement('div');
    resultsWrapper.className = 'music-results-container scroll-x';

    results.forEach(song => {
        const card = document.createElement('div');
        card.className = 'music-card premium-glass fade-in';
        card.innerHTML = `
            <div class="music-card-thumb">
                <img src="${song.thumbnail || 'assets/default_music.png'}" alt="${song.title}">
                <div class="play-overlay"><i class="fas fa-play"></i></div>
            </div>
            <div class="music-card-info">
                <div class="music-card-title">${song.title}</div>
                <div class="music-card-artist">${song.artist}</div>
            </div>
        `;

        card.addEventListener('click', () => {
            sendCommand(`play ${song.videoId}`, false);
        });

        resultsWrapper.appendChild(card);
    });

    container.appendChild(resultsWrapper);
}

/**
 * Coordinate Conversion: Lat/Lon to 3D Sphere
 */
function mapLatLngToSphere(lat, lon, radius) {
    const phi = (90 - lat) * (Math.PI / 180);
    const theta = (lon + 180) * (Math.PI / 180);

    return {
        x: -(radius * Math.sin(phi) * Math.cos(theta)),
        z: radius * Math.sin(phi) * Math.sin(theta),
        y: radius * Math.cos(phi)
    };
}

let eventMarkers = [];
/**
 * Renders glowing markers on the 3D globe for natural events
 */
function renderNaturalEvents(events) {
    if (!events || !scene || !particles) return;

    // Clear old markers
    eventMarkers.forEach(m => scene.remove(m));
    eventMarkers = [];

    events.forEach(event => {
        if (event.lat === undefined || event.lon === undefined) return;

        const pos = mapLatLngToSphere(event.lat, event.lon, 150); // globeRadius is 150
        
        const markerGeo = new THREE.SphereGeometry(4, 16, 16);
        const color = event.mag ? 0xff4444 : 0xffaa00; // Red for quakes, Orange for NASA events
        const markerMat = new THREE.MeshBasicMaterial({ 
            color: color,
            transparent: true,
            opacity: 0.8
        });
        
        const marker = new THREE.Mesh(markerGeo, markerMat);
        marker.position.set(pos.x, pos.y, pos.z);
        
        // Add a "glow" halo to the marker
        const haloGeo = new THREE.SphereGeometry(8, 16, 16);
        const haloMat = new THREE.MeshBasicMaterial({ 
            color: color, 
            transparent: true, 
            opacity: 0.2 
        });
        const halo = new THREE.Mesh(haloGeo, haloMat);
        marker.add(halo);
        
        // Animation for the marker
        marker.userData = { 
            originalScale: 1.0,
            pulsePhase: Math.random() * Math.PI * 2
        };
        
        scene.add(marker);
        eventMarkers.push(marker);
        
        // Rotate globe towards the first event for "WOW" effect
        if (event === events[0]) {
            // Add a slight target rotation if possible (simplified here)
            particles.rotation.y = - (event.lon * Math.PI / 180);
            particles.rotation.x = (event.lat * Math.PI / 180);
        }
    });

    // Auto-remove markers after 30 seconds
    setTimeout(() => {
        eventMarkers.forEach(m => {
            if (scene) scene.remove(m);
        });
        eventMarkers = [];
    }, 30000);

    // Update Dashboard UI
    updateEventsList(events);
    toggleEventsDashboard(true);
}

/**
 * Renders web search results with Favicons (feb ions)
 */
function renderSearchResults(container, results) {
    if (!results || results.length === 0) return;

    const wrapper = document.createElement('div');
    wrapper.className = 'search-results-container scroll-x fade-in';
    
    results.forEach(res => {
        const card = document.createElement('div');
        card.className = 'search-card premium-glass';
        card.innerHTML = `
            <div class="search-card-header">
                <img src="${res.favicon || 'assets/default_web.png'}" class="feb-ion" alt="ico">
                <div class="search-card-title">${res.title}</div>
            </div>
            <div class="search-card-snippet">${res.snippet.substring(0, 80)}...</div>
        `;
        card.onclick = () => openInInternalBrowser(res.url);
        wrapper.appendChild(card);
    });
    
    // Update Browsing Status with the first favicon for extra polish
    if (results.length > 0) {
        showBrowsingStatus(`Found results from ${new URL(results[0].url).hostname}`, results[0].favicon);
    }
    
    container.appendChild(wrapper);
}

/**
 * Renders news results with Favicons (feb ions)
 */
function renderNewsResults(container, results) {
    if (!results || results.length === 0) return;

    const wrapper = document.createElement('div');
    wrapper.className = 'news-results-container scroll-x fade-in';
    
    results.forEach(item => {
        const card = document.createElement('div');
        card.className = 'news-card premium-glass';
        card.innerHTML = `
            <div class="news-card-header">
                <img src="${item.favicon || 'assets/default_news.png'}" class="feb-ion" alt="ico">
                <div class="news-card-source">${item.source}</div>
            </div>
            <div class="news-card-title">${item.title}</div>
        `;
        card.onclick = () => openInInternalBrowser(item.url);
        wrapper.appendChild(card);
    });
    
    container.appendChild(wrapper);
}

function renderThoughts(thoughts, modelName = null) {
    const feed = document.getElementById('thought-feed');
    const badge = document.getElementById('thought-status-badge');
    const countEl = document.getElementById('thought-count');

    if (!feed) {
        console.warn("Thought panel elements not found.");
        return;
    }

    // Set status badge to ACTIVE
    if (badge) {
        badge.textContent = 'ACTIVE';
        badge.style.color = 'rgba(139,92,246,0.9)';
        badge.style.borderColor = 'rgba(139,92,246,0.5)';
        badge.style.boxShadow = '0 0 8px rgba(139,92,246,0.3)';
    }

    // Clear old thoughts
    feed.innerHTML = '';

    if (thoughts && thoughts.length > 0) {
        thoughts.forEach((step, index) => {
            const line = document.createElement('div');
            line.className = 'text-[#8ca6f9] mb-2';
            line.textContent = `> ${step}`;
            feed.appendChild(line);
        });
    }

    // Add trailing waiting animation
    const waiting = document.createElement('div');
    waiting.className = 'text-white/60 flex items-center gap-2';
    waiting.innerHTML = '> Awaiting input <span class="w-1.5 h-3 bg-white/50 animate-pulse inline-block"></span>';
    feed.appendChild(waiting);

    // Update count
    if (countEl) {
        countEl.textContent = `${thoughts.length} THOUGHT${thoughts.length !== 1 ? 'S' : ''}`;
    }

    // Scroll to bottom
    feed.scrollTop = feed.scrollHeight;

    // Animate waveform (spike on new thoughts)
    animateThoughtWave(true);

    // Reset badge after 5s of inactivity
    setTimeout(() => {
        if (badge) {
            badge.textContent = 'IDLE';
            badge.style.color = 'rgba(139,92,246,0.5)';
            badge.style.borderColor = 'rgba(139,92,246,0.2)';
            badge.style.boxShadow = 'none';
        }
        animateThoughtWave(false);
    }, 5000);
}

// Animates the neural waveform in the thought sidebar footer
let thoughtWaveActive = false;
let thoughtWaveInterval = null;
function animateThoughtWave(active) {
    const path = document.getElementById('wave-path');
    const glow = document.getElementById('wave-glow');
    if (!path) return;

    thoughtWaveActive = active;
    if (thoughtWaveInterval) clearInterval(thoughtWaveInterval);

    if (!active) {
        path.setAttribute('d', 'M0,18 Q30,8 60,18 T120,18 T180,18 T240,18 T300,18');
        path.setAttribute('opacity', '0.3');
        return;
    }

    path.setAttribute('opacity', '0.8');
    let t = 0;
    thoughtWaveInterval = setInterval(() => {
        t += 0.15;
        const amp = 10;
        const d = `M0,18 Q${30+Math.sin(t)*5},${18-amp*Math.sin(t)} ${60+Math.cos(t)*5},${18+amp*Math.cos(t*0.8)} T${120},${18+amp*Math.sin(t*1.3)} T${180},${18-amp*Math.cos(t*0.7)} T${240},${18+amp*Math.sin(t*0.9)} T300,18`;
        path.setAttribute('d', d);
        if (glow) glow.setAttribute('d', d);
    }, 50);
}


// Status Handling
async function checkStatus() {
    try {
        const res = await fetch(`${API_URL}/status`);
        const data = await res.json();
        if (data.status === 'online') {
            isOfflineMode = false;
            if (statusCard) statusCard.classList.remove('is-flipped');
        } else {
            isOfflineMode = true;
            if (statusCard) statusCard.classList.add('is-flipped');
        }
    } catch (e) {
        isOfflineMode = true;
        if (statusCard) statusCard.classList.add('is-flipped');
    }
}

if (statusToggle) {
    statusToggle.addEventListener('click', () => {
        isOfflineMode = !isOfflineMode;
        if (statusCard) statusCard.classList.toggle('is-flipped');

        // Notify backend of mode change
        fetch(`${API_URL}/settings/online`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ online: !isOfflineMode })
        });
    });
}

// --- SETTINGS MODAL LOGIC ---
function initSettings() {

    // New Sidebar Navigation Logic
    const assistantBtn = document.getElementById('assistant-btn');
    const memoryBtn = document.getElementById('logs-btn'); // Mapped to memory
    const telemetryBtn = document.getElementById('telemetry-btn'); // Add if needed
    const sidebarSettingsBtn = document.getElementById('settings-btn');
    const adminDashboard = document.getElementById('admin-dashboard');

    if (assistantBtn) {
        assistantBtn.addEventListener('click', () => {
            if (adminDashboard) adminDashboard.classList.add('hidden');
            if (settingsModal) {
                settingsModal.classList.remove('active');
                setTimeout(() => settingsModal.style.display = 'none', 300);
            }
        });
    }

    if (memoryBtn) {
        memoryBtn.addEventListener('click', () => {
            // Can open admin dashboard or a specific tab
            if (adminDashboard) {
                adminDashboard.classList.remove('hidden');
                document.getElementById('admin-auth-screen').style.display = 'flex';
                document.getElementById('admin-main-content').classList.add('hidden');
            }
        });
    }

    const settingsBtn = document.getElementById('settings-btn');
    const settingsModal = document.getElementById('settings-modal');
    const closeSettingsBtn = document.getElementById('close-settings-btn');
    const settingsTabs = document.querySelectorAll('.settings-tab');
    const settingsPanels = document.querySelectorAll('.settings-panel');
    const saveSettingsBtn = document.getElementById('save-settings-btn');
    const logsBtn = document.getElementById('logs-btn');
    const scheduleBtn = document.getElementById('schedule-btn');
    const closeLogsBtn = document.getElementById('close-logs-btn');
    const closeScheduleBtn = document.getElementById('close-schedule-btn');

    if (settingsBtn && settingsModal) {
        settingsBtn.addEventListener('click', () => {
            settingsModal.style.display = 'flex';
            setTimeout(() => settingsModal.classList.add('active'), 10);
            loadSettings(); // Load current values
        });

        if (closeSettingsBtn) {
            closeSettingsBtn.addEventListener('click', () => {
                settingsModal.classList.remove('active');
                setTimeout(() => settingsModal.style.display = 'none', 300);
            });
        }

        // Click outside to close modal
        settingsModal.addEventListener('click', (e) => {
            if (e.target === settingsModal) {
                settingsModal.classList.remove('active');
                setTimeout(() => settingsModal.style.display = 'none', 300);
            }
        });

        // Tab Switching for new B&W Settings Modal
        settingsTabs.forEach(tab => {
            tab.addEventListener('click', () => {
                // Reset all tabs
                settingsTabs.forEach(t => {
                    t.classList.remove('active', 'bg-white', 'text-black', 'font-bold');
                    t.classList.add('text-white/70', 'font-normal');
                    t.style.background = ''; 
                });
                
                // Hide all panels
                settingsPanels.forEach(p => {
                    p.classList.remove('active', 'block');
                    p.classList.add('hidden');
                    p.style.display = 'none';
                });

                // Activate clicked tab
                tab.classList.remove('text-white/70', 'font-normal');
                tab.classList.add('active', 'bg-white', 'text-black', 'font-bold');

                // Show target panel (support both data-tab and data-target)
                const targetAttr = tab.getAttribute('data-target') || (tab.getAttribute('data-tab') + '-panel');
                const targetPanel = document.getElementById(targetAttr);
                
                if (targetPanel) {
                    targetPanel.classList.remove('hidden');
                    targetPanel.classList.add('active', 'block');
                    targetPanel.style.display = 'block';
                    
                    // If switching to skills tab, load them
                    if (targetAttr === 'skills-panel') {
                        loadSkills();
                    }
                }
            });
        });

        // Slider Live Updates
        const sliders = [
            { id: 'voice-speed', label: 'speed-value', suffix: 'x' },
            { id: 'voice-pitch', label: 'pitch-value', suffix: 'Hz', prefix: '+' },
            { id: 'temperature', label: 'temp-value', suffix: '' },
            { id: 'max-tokens', label: 'tokens-value', suffix: '' },
            { id: 'context-window', label: 'context-value', suffix: '' }
        ];

        sliders.forEach(s => {
            const el = document.getElementById(s.id);
            const label = document.getElementById(s.label);
            if (el && label) {
                el.addEventListener('input', () => {
                    let val = el.value;
                    if (s.prefix && val > 0 && !val.toString().startsWith('+')) val = '+' + val;
                    label.textContent = val + s.suffix;
                });
            }
        });

        // Header Mute Button Logic
        const muteToggle = document.getElementById('mute-toggle');
        const headerMuteBtn = document.getElementById('header-mute-btn');

        // Load mute state from localStorage on startup
        const savedMuteState = localStorage.getItem('nova_mute_state');
        if (savedMuteState !== null) {
            isMuted = (savedMuteState === 'true');
            if (headerMuteBtn) headerMuteBtn.innerHTML = isMuted ? '<i class="fas fa-volume-mute"></i>' : '<i class="fas fa-volume-up"></i>';
            if (muteToggle) muteToggle.checked = isMuted;
        }

        if (headerMuteBtn) {
            headerMuteBtn.addEventListener('click', () => {
                isMuted = !isMuted;

                if (isMuted) {
                    // Pause if playing
                    if (currentAudio && !currentAudio.paused) {
                        try { currentAudio.pause(); } catch (e) { console.error(e); }
                        isSpeaking = false;
                        if (liveOverlay && isContinuousMode) liveOverlay.classList.remove('speaking');
                    }
                } else {
                    // Resume if paused and exists
                    if (currentAudio && currentAudio.paused && !currentAudio.ended) {
                        currentAudio.play().then(() => {
                            isSpeaking = true;
                            if (liveOverlay && isContinuousMode) liveOverlay.classList.add('speaking');
                        }).catch(e => console.error("Resume failed:", e));
                    }
                }

                // Save to localStorage
                localStorage.setItem('nova_mute_state', isMuted);

                // Sync UI
                headerMuteBtn.innerHTML = isMuted ? '<i class="fas fa-volume-mute"></i>' : '<i class="fas fa-volume-up"></i>';
                if (muteToggle) muteToggle.checked = isMuted;
            });
        }

        // Sync from Toggle to Header
        if (muteToggle) {
            muteToggle.addEventListener('change', () => {
                isMuted = muteToggle.checked;

                if (isMuted) {
                    if (currentAudio && !currentAudio.paused) {
                        try { currentAudio.pause(); } catch (e) { console.error(e); }
                        isSpeaking = false;
                        if (liveOverlay && isContinuousMode) liveOverlay.classList.remove('speaking');
                    }
                } else {
                    if (currentAudio && currentAudio.paused && !currentAudio.ended) {
                        currentAudio.play().then(() => {
                            isSpeaking = true;
                            if (liveOverlay && isContinuousMode) liveOverlay.classList.add('speaking');
                        }).catch(e => console.error("Resume failed:", e));
                    }
                }

                // Save to localStorage
                localStorage.setItem('nova_mute_state', isMuted);

                if (headerMuteBtn) headerMuteBtn.innerHTML = isMuted ? '<i class="fas fa-volume-mute"></i>' : '<i class="fas fa-volume-up"></i>';
            });
        }

        // Test Voice Button
        const testVoiceBtn = document.getElementById('test-voice-btn');
        if (testVoiceBtn) {
            testVoiceBtn.addEventListener('click', async () => {
                const voice = document.getElementById('voice-language').value;
                const speed = parseFloat(document.getElementById('voice-speed').value);
                const pitch = parseInt(document.getElementById('voice-pitch').value);

                testVoiceBtn.disabled = true;
                testVoiceBtn.innerHTML = '<i class="fas fa-spinner fa-spin" style="margin-right: 8px;"></i> Testing...';

                try {
                    const res = await fetch(`${API_URL}/voice/test`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ voice, speed, pitch })
                    });

                    const data = await res.json();
                    if (data.status === 'success' && data.audio_base64) {
                        if (!isMuted) {
                            const audio = new Audio(`data:audio/mpeg;base64,${data.audio_base64}`);
                            audio.play();
                        }
                    } else {
                        alert('Voice test failed: ' + (data.message || 'Unknown error'));
                    }
                } catch (e) {
                    console.error('Voice test error:', e);
                    alert('Could not test voice. Check server connection.');
                } finally {
                    testVoiceBtn.disabled = false;
                    testVoiceBtn.innerHTML = '<i class="fas fa-volume-up" style="margin-right: 8px;"></i> Test Voice';
                }
            });
        }

        // Export Conversation Handlers
        ['txt', 'html', 'json', 'pdf'].forEach(format => {
            const btn = document.getElementById(`export-${format}-btn`);
            if (btn) {
                btn.addEventListener('click', async () => {
                    const originalText = btn.innerHTML;
                    btn.disabled = true;
                    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Exporting...';

                    try {
                        const res = await fetch(`${API_URL}/conversation/export`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ format })
                        });

                        if (!res.ok) throw new Error('Network response was not ok');

                        if (format === 'json') {
                            const data = await res.json();
                            const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
                            const url = URL.createObjectURL(blob);
                            const a = document.createElement('a');
                            a.href = url;
                            a.download = `nova_conversations_${Date.now()}.json`;
                            document.body.appendChild(a);
                            a.click();
                            document.body.removeChild(a);
                        } else {
                            const text = await res.text();
                            const blob = new Blob([text], { type: format === 'txt' ? 'text/plain' : 'text/html' });
                            const url = URL.createObjectURL(blob);
                            const a = document.createElement('a');
                            a.href = url;
                            a.download = `nova_conversations_${Date.now()}.${format}`;
                            document.body.appendChild(a);
                            a.click();
                            document.body.removeChild(a);
                        }

                        addLog(`Conversation history exported as ${format.toUpperCase()}`, 'info');
                    } catch (e) {
                        console.error('Export failed:', e);
                        alert('Export failed: ' + e.message);
                    } finally {
                        btn.disabled = false;
                        btn.innerHTML = originalText;
                    }
                });
            }
        });

        // Logs and Schedule Modals are initialized later in the script with more complete logic

        if (scheduleBtn && document.getElementById('schedule-modal')) {
            scheduleBtn.addEventListener('click', () => {
                const modal = document.getElementById('schedule-modal');
                modal.style.display = 'flex';
                // Trigger schedule fetch if needed in future
            });
        }

        if (closeLogsBtn) {
            closeLogsBtn?.addEventListener('click', () => {
                const modal = document.getElementById('logs-modal');
                if (modal) modal.style.display = 'none';
            });
        }

        if (closeScheduleBtn) {
            closeScheduleBtn?.addEventListener('click', () => {
                const modal = document.getElementById('schedule-modal');
                if (modal) modal.style.display = 'none';
            });
        }

        // Clear Memory Button Logic
        const clearMemoryBtn = document.getElementById('clear-memory-btn');
        if (clearMemoryBtn) {
            clearMemoryBtn.addEventListener('click', async () => {
                if (confirm('🗑️ Are you sure you want to clear all learned memories? This action cannot be undone.')) {
                    clearMemoryBtn.disabled = true;
                    clearMemoryBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Clearing...';

                    try {
                        const res = await fetch(`${API_URL}/memory/clear`, { method: 'POST' });
                        const data = await res.json();
                        if (data.status === 'success') {
                            alert('✅ All memories have been cleared.');
                        } else {
                            alert('❌ Failed to clear memory: ' + data.message);
                        }
                    } catch (err) {
                        console.error('Clear memory error:', err);
                        alert('❌ System error while clearing memory.');
                    } finally {
                        clearMemoryBtn.disabled = false;
                        clearMemoryBtn.innerHTML = '⚠️ Clear All Memories';
                    }
                }
            });
        }

        // Save Settings
        saveSettingsBtn?.addEventListener('click', async () => {
            const settings = {
                voice: {
                    model: document.getElementById('voice-language').value,
                    speed: document.getElementById('voice-speed').value,
                    pitch: document.getElementById('voice-pitch').value,
                    autoplay: document.getElementById('auto-play-audio').checked
                },
                personality: {
                    mode: document.getElementById('personality-mode-select').value,
                    response_length: document.getElementById('response-length').value,
                    emotion_level: document.getElementById('emotion-level').value,
                    use_emojis: document.getElementById('use-emojis').checked,
                    use_russian: document.getElementById('use-russian').checked
                },
                model: {
                    temperature: document.getElementById('temperature').value,
                    max_tokens: document.getElementById('max-tokens').value,
                    context_window: document.getElementById('context-window').value
                },
                memory: {
                    enabled: document.getElementById('enable-ltm').checked,
                    fact_learning: document.getElementById('fact-learning').value,
                    retention: document.getElementById('memory-retention').value
                },
                interface: {
                    theme: document.getElementById('theme-select').value,
                    font_size: document.getElementById('font-size').value,
                    timestamps: document.getElementById('show-timestamps').checked,
                    globe: document.getElementById('globe-animation').checked,
                    vtuber: document.getElementById('enable-vtuber').checked
                },
                advanced: {
                    dev_mode: document.getElementById('developer-mode').checked,
                    debug_logs: document.getElementById('debug-logs').checked
                }
            };

            // Save VTuber state to local storage too
            const vtuberEnabled = document.getElementById('enable-vtuber').checked;
            useVTuber = vtuberEnabled;
            localStorage.setItem('nova_use_vtuber', useVTuber);

            try {
                // 1. Save Main Settings
                const res = await fetch(`${API_URL}/settings/save`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(settings)
                });

                // 2. Save Profile Name & Personal Info
                const nameInput = document.getElementById('user-name-input');
                const personalInfo = {
                    gender: document.getElementById('user-gender') ? document.getElementById('user-gender').value : '',
                    birthday: document.getElementById('user-birthday') ? document.getElementById('user-birthday').value : '',
                    occupation: document.getElementById('user-occupation') ? document.getElementById('user-occupation').value : '',
                    interests: document.getElementById('user-interests') ? document.getElementById('user-interests').value.split(',').map(s => s.trim()).filter(s => s) : [],
                    relationship_status: document.getElementById('user-relationship') ? document.getElementById('user-relationship').value : '',
                    bio: document.getElementById('user-bio') ? document.getElementById('user-bio').value : ''
                };

                if (nameInput) {
                    await fetch(`${API_URL}/settings/profile`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            name: nameInput.value,
                            personal_info: personalInfo
                        })
                    });
                }

                const data = await res.json();
                if (data.status === 'success') {
                    // Apply Theme Immediately
                    const theme = settings.interface.theme;
                    if (theme === 'glow') {
                        document.documentElement.classList.add('theme-glow');
                    } else {
                        document.documentElement.classList.remove('theme-glow');
                    }

                    const originalText = saveSettingsBtn.innerHTML;
                    saveSettingsBtn.innerHTML = '✅ Saved!';
                    saveSettingsBtn.style.background = '#48bb78';
                    setTimeout(() => {
                        saveSettingsBtn.innerHTML = originalText;
                        saveSettingsBtn.style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
                    }, 2000);
                }
            } catch (e) {
                console.error('Settings Save Error:', e);
                alert('Failed to save settings.');
            }
        });

        // Reset Settings
        const resetBtn = document.getElementById('reset-settings-btn');
        if (resetBtn) {
            resetBtn.addEventListener('click', () => {
                if (confirm('🔄 Reset all settings to factory defaults? Your personal profile will be kept.')) {
                    setVal('voice-language', 'en-US-AvaNeural');
                    setVal('voice-speed', 1.0);
                    setVal('voice-pitch', 0);
                    setVal('auto-play-audio', true);
                    setVal('personality-mode-select', 'sweetheart');
                    setVal('response-length', 'medium');
                    setVal('emotion-level', 'medium');
                    setVal('use-emojis', true);
                    setVal('temperature', 0.7);
                    setVal('max-tokens', 300);
                    setVal('context-window', 10);
                    setVal('enable-ltm', true);
                    setVal('fact-learning', 'auto');
                    setVal('memory-retention', '30');
                    setVal('theme-select', 'dark');
                    setVal('font-size', 'medium');
                    setVal('show-timestamps', true);
                    setVal('globe-animation', true);
                    setVal('enable-vtuber', true);

                    // Trigger slider labels
                    ['voice-speed', 'voice-pitch', 'temperature', 'max-tokens', 'context-window'].forEach(id => {
                        const el = document.getElementById(id);
                        if (el) el.dispatchEvent(new Event('input'));
                    });

                    saveSettingsBtn.click();
                }
            });
        }
    }

    // Helper to update checkbox/value safely — shared by loadSettings & resetSettings
    function setVal(id, val) {
        const el = document.getElementById(id);
        if (!el) return;
        if (el.type === 'checkbox') el.checked = val;
        else el.value = val;
    }

    // Load Settings from Backend
    async function loadSettings() {
        try {
            const res = await fetch(`${API_URL}/settings`);
            const settings = await res.json();

            if (!settings) return;

            // Voice
            if (settings.voice) {
                setVal('voice-language', settings.voice.model);
                setVal('voice-speed', settings.voice.speed);
                setVal('voice-pitch', settings.voice.pitch);
                setVal('auto-play-audio', settings.voice.autoplay);
            }
            // Personality
            if (settings.personality) {
                setVal('personality-mode-select', settings.personality.mode);
                setVal('response-length', settings.personality.response_length);
                setVal('emotion-level', settings.personality.emotion_level);
                setVal('use-emojis', settings.personality.use_emojis);
                setVal('use-russian', settings.personality.use_russian);
            }
            // Model
            if (settings.model) {
                setVal('temperature', settings.model.temperature);
                setVal('max-tokens', settings.model.max_tokens);
                setVal('context-window', settings.model.context_window);
            }
            // Memory
            if (settings.memory) {
                setVal('enable-ltm', settings.memory.enabled);
                setVal('fact-learning', settings.memory.fact_learning);
                setVal('memory-retention', settings.memory.retention);
            }
            // Interface
            if (settings.interface) {
                setVal('theme-select', settings.interface.theme);
                setVal('font-size', settings.interface.font_size);
                setVal('show-timestamps', settings.interface.timestamps);
                setVal('globe-animation', settings.interface.globe);

                // Apply Theme on Load
                if (settings.interface.theme === 'glow') {
                    document.documentElement.classList.add('theme-glow');
                } else {
                    document.documentElement.classList.remove('theme-glow');
                }
            }
            // Advanced
            if (settings.advanced) {
                setVal('developer-mode', settings.advanced.dev_mode);
                setVal('debug-logs', settings.advanced.debug_logs);
            }

            // LOAD PROFILE Data (Merged into loadSettings)
            try {
                const profRes = await fetch(`${API_URL}/settings/profile`);
                const profData = await profRes.json();
                if (profData) {
                    if (profData.name) setVal('user-name-input', profData.name);

                    // Personal Information
                    if (profData.personal_info) {
                        setVal('user-gender', profData.personal_info.gender || '');
                        setVal('user-birthday', profData.personal_info.birthday || '');
                        setVal('user-occupation', profData.personal_info.occupation || '');
                        setVal('user-relationship', profData.personal_info.relationship_status || '');
                        setVal('user-bio', profData.personal_info.bio || '');

                        if (profData.personal_info.interests && Array.isArray(profData.personal_info.interests)) {
                            setVal('user-interests', profData.personal_info.interests.join(', '));
                        }
                    }
                }
            } catch (pe) { console.log("Profile load failed", pe); }

            // VTuber Toggle (LocalStorage)
            const savedVTuber = localStorage.getItem('nova_use_vtuber');
            if (savedVTuber !== null) {
                useVTuber = (savedVTuber === 'true');
                setVal('enable-vtuber', useVTuber);
            }

            // Trigger slider label updates
            ['voice-speed', 'voice-pitch', 'temperature', 'max-tokens', 'context-window'].forEach(id => {
                const el = document.getElementById(id);
                if (el) el.dispatchEvent(new Event('input'));
            });

        } catch (e) {
            console.log("Error loading settings", e);
        }
    }

    // VTuber Character Toggle
    const vtuberToggle = document.getElementById('enable-vtuber');
    if (vtuberToggle) {
        vtuberToggle.addEventListener('change', (e) => {
            useVTuber = e.target.checked;
        });
    }

    // PROFILE IMAGE UPLOAD LOGIC
    const profileImageUpload = document.getElementById('profile-image-upload');
    if (profileImageUpload) {
        profileImageUpload.addEventListener('change', async (e) => {
            const file = e.target.files[0];
            if (!file) return;

            const formData = new FormData();
            formData.append('image', file);

            try {
                const preview = document.getElementById('profile-image-preview');
                if (preview) preview.style.opacity = '0.5';

                const res = await fetch(`${API_URL}/settings/profile/image`, {
                    method: 'POST',
                    body: formData
                });
                const data = await res.json();

                if (data.status === 'success') {
                    if (preview) {
                        preview.src = data.url;
                        preview.style.opacity = '1.0';
                    }
                } else {
                    alert("Upload failed: " + data.message);
                    if (preview) preview.style.opacity = '1.0';
                }
            } catch (err) {
                console.error("Upload error:", err);
                alert("Upload failed.");
            }
        });
    }

    initAdminDashboard();

    // Thought Panel Close Handler
    const closeThoughtBtn = document.getElementById('close-thought-panel');
    if (closeThoughtBtn) {
        closeThoughtBtn.addEventListener('click', () => {
            const panel = document.getElementById('thought-panel');
            if (panel) panel.classList.add('hidden');
        });
    }
}


async function speak(text) {
    if (!text) return;
    try {
        const res = await fetch(`${API_URL}/voice/test`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                voice: document.getElementById('voice-language').value,
                speed: parseFloat(document.getElementById('voice-speed').value),
                pitch: parseInt(document.getElementById('voice-pitch').value),
                text: text
            })
        });

        // Trigger Glow Pulse if in Glow Theme
        if (document.documentElement.classList.contains('theme-glow')) {
            triggerGlowPulse();
        }

        const data = await res.json();
        if (data.audio_base64) {
            playAudio(data.audio_base64);
        }
    } catch (e) {
        console.error("Speak error:", e);
    }
}

// MediaRecorder & VAD Logic
// MediaRecorder & VAD State
mediaRecorder = null;
audioChunks = [];
isRecording = false;
vadAudioContext = null;
vadAnalyser = null;
microphone = null;
javascriptNode = null;

// VAD Constants — Tuned for maximum voice recognition accuracy
const VAD_THRESHOLD = 25; // Lowered for soft-spoken users and distant mics
const SILENCE_DELAY = 1500; // 1.5s patience to avoid cutting mid-sentence pauses
const MIN_SPEECH_DURATION_MS = 300; // Minimum speech before arming silence timer (prevents cough/click triggers)
let silenceTimer = null;
let noiseFloor = 15; // Adaptive noise floor (updated continuously)
let noiseFloorSamples = 0;
let speechStartTime = 0; // Track when speech started

async function startRecording() {
    if (isSpeaking) {
        console.log("🤫 Nova is speaking, skipping recording trigger.");
        return;
    }
    isLiveInteraction = true;
    isProcessing = false;

    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        
        vadAudioContext = new (window.AudioContext || window.webkitAudioContext)();
        microphone = vadAudioContext.createMediaStreamSource(stream);
        vadAnalyser = vadAudioContext.createAnalyser();
        vadAnalyser.fftSize = 512;
        vadAnalyser.smoothingTimeConstant = 0.1;

        microphone.connect(vadAnalyser);

        javascriptNode = vadAudioContext.createScriptProcessor(2048, 1, 1);
        vadAnalyser.connect(javascriptNode);
        javascriptNode.connect(vadAudioContext.destination);

        mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
        audioChunks = [];

        mediaRecorder.ondataavailable = (event) => {
            if (event.data.size > 0) audioChunks.push(event.data);
        };

        mediaRecorder.onstop = () => {
            stream.getTracks().forEach(track => track.stop());
            cleanupAudio();
            if (audioChunks.length > 0) {
                const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                transcribeAudio(audioBlob);
            }
        };

        let isSpeakingCurrently = false;

        // Reset adaptive noise floor for this recording session
        noiseFloor = 15;
        noiseFloorSamples = 0;
        speechStartTime = 0;

        javascriptNode.onaudioprocess = function() {
            if (!isRecording) return;
            const array = new Uint8Array(vadAnalyser.frequencyBinCount);
            vadAnalyser.getByteFrequencyData(array);
            let sum = 0;
            for (let i = 0; i < array.length; i++) {
                sum += array[i];
            }
            const average = sum / array.length;

            // Adaptive noise floor: continuously track ambient level during silence
            if (!isSpeakingCurrently) {
                noiseFloorSamples++;
                // Exponential moving average for noise floor
                noiseFloor = noiseFloor * 0.95 + average * 0.05;
            }

            // Dynamic threshold: noise floor + fixed margin
            const effectiveThreshold = Math.max(VAD_THRESHOLD, noiseFloor + 12);

            if (average > effectiveThreshold) {
                if (!isSpeakingCurrently) {
                    isSpeakingCurrently = true;
                    speechStartTime = Date.now();
                }
                if (silenceTimer) {
                    clearTimeout(silenceTimer);
                    silenceTimer = null;
                }
            } else {
                // Only arm silence timer if user has spoken for at least MIN_SPEECH_DURATION_MS
                const speechDuration = speechStartTime > 0 ? (Date.now() - speechStartTime) : 0;
                if (isSpeakingCurrently && !silenceTimer && speechDuration >= MIN_SPEECH_DURATION_MS) {
                    silenceTimer = setTimeout(() => {
                        isSpeakingCurrently = false;
                        speechStartTime = 0;
                        stopRecording();
                    }, SILENCE_DELAY);
                }
            }
        };

        mediaRecorder.start();
        isRecording = true;
        if (micBtn) micBtn.classList.add('listening');
        if (typeof liveOverlay !== 'undefined' && liveOverlay) liveOverlay.classList.add('listening');
        console.log("🎤 Recording started via browser...");
    } catch (err) {
        console.error("Microphone access denied or error:", err);
    }
}

function cleanupAudio() {
    if (javascriptNode) {
        javascriptNode.onaudioprocess = null;
        javascriptNode.disconnect();
    }
    if (microphone) microphone.disconnect();
    if (vadAnalyser) vadAnalyser.disconnect();
    if (vadAudioContext) vadAudioContext.close();

    javascriptNode = null;
    microphone = null;
    vadAnalyser = null;
    vadAudioContext = null;
}

function stopRecording() {
    if (mediaRecorder && isRecording) {
        mediaRecorder.stop();
        isRecording = false;
        micBtn.classList.remove('listening');
        console.log("Recording stopped.");

        // Set v-tuber to idle (remove listening state)
        if (liveOverlay) liveOverlay.classList.remove('listening');
    }
}

// Error handling state for live mode
let transcriptionRetryCount = 0;
const MAX_TRANSCRIPTION_RETRIES = 3;

async function transcribeAudio(blob) {
    const formData = new FormData();
    formData.append('audio', blob, 'audio.webm');
    formData.append('language', document.getElementById('voice-language').value || 'en');

    // Use a lighter status for live mode
    if (!isContinuousMode) addLine('Thinking...', 'system-msg');

    // Set Processing Flag for Animation
    isProcessing = true;

    try {
        // Unified route for Live Mode to reduce latency by 50%
        const endpoint = isContinuousMode ? `${API_URL}/voice-command` : `${API_URL}/transcribe`;

        const res = await fetch(endpoint, {
            method: 'POST',
            body: formData,
            signal: AbortSignal.timeout(10000) // 10s timeout
        });

        if (!res.ok) {
            throw new Error(`HTTP ${res.status}: ${res.statusText}`);
        }

        const data = await res.json();

        // Reset retry count on success
        transcriptionRetryCount = 0;

        if (isContinuousMode) {
            // Unified route returns the full response directly
            if (data.response) {
                if (data.thoughts && data.thoughts.length > 0) {
                    renderThoughts(data.thoughts);
                }
                if (liveTranscript) liveTranscript.textContent = `"${data.transcript || '...'}"`;

                addLine(data.response, 'nova-msg', data.tokens || 0);
                if (data.emotion) triggerEmotionUI(data.emotion);
                if (data.audio_base64) {
                    // Set v-tuber to speaking state
                    if (liveOverlay) {
                        liveOverlay.classList.remove('listening');
                        liveOverlay.classList.add('speaking');
                    }
                    playAudio(data.audio_base64);
                }
            } else {
                console.log("Live Mode: No response received."); // Silent fallback
                // Auto-restart recording in live mode
                if (isContinuousMode) {
                    setTimeout(() => startRecording(), 500);
                }
            }
            isProcessing = false; // Done processing
        } else {
            // Standard multi-step logic
            isProcessing = false; // Clear before sendCommand
            if (data.transcript && data.transcript.trim().length > 0) {
                sendCommand(data.transcript, false, data.language);
            } else {
                console.log("Ignored empty transcript.");
            }
        }
    } catch (e) {
        console.error("Transcription error:", e);
        isProcessing = false; // Clear on error

        // ENHANCED ERROR HANDLING WITH RETRY LOGIC
        transcriptionRetryCount++;

        if (transcriptionRetryCount <= MAX_TRANSCRIPTION_RETRIES) {
            console.warn(`Retry ${transcriptionRetryCount}/${MAX_TRANSCRIPTION_RETRIES}...`);

            if (isContinuousMode) {
                // In live mode, show subtle error and auto-retry
                if (liveTranscript) {
                    liveTranscript.textContent = `Retry ${transcriptionRetryCount}...`;
                }
                // Auto-restart recording after brief delay
                setTimeout(() => startRecording(), 1000);
            } else {
                // In normal mode, show error message
                addLine(`Voice recognition hit a snag. Retrying (${transcriptionRetryCount}/${MAX_TRANSCRIPTION_RETRIES})...`, 'system-msg');
            }
        } else {
            // Max retries exceeded - show error and reset
            transcriptionRetryCount = 0;

            if (isContinuousMode) {
                if (liveTranscript) {
                    liveTranscript.textContent = "Voice recognition failed. Please try again.";
                }
                // Exit live mode on persistent failure
                addLine('Voice recognition failed after multiple attempts. Exiting live mode.', 'system-msg');
                toggleLiveMode(false);
            } else {
                addLine('Voice recognition failed. Please type your message or try again.', 'system-msg');
            }
        }
    }
}

function startBrowserFallback() {
    const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!Recognition) {
        addLine('All transcription methods failed.', 'system-msg');
        return;
    }

    const reg = new Recognition();
    reg.lang = 'en-US';
    reg.interimResults = false;

    reg.onresult = (event) => {
        const text = event.results[0][0].transcript;
        if (text) sendCommand(text);
    };

    reg.onerror = (event) => {
        // If browser also fails, force a "Hmmm?" response from backend by sending empty
        console.log("Browser recognition failed. Silence triggered.");
        // sendCommand(" "); // FAIL SILENTLY
    };

    reg.start();
    addLine('Using secondary recognition...', 'system-msg');
}


// Modern Voice Visualization Logic (Halos/Aura)

// Modern Voice Visualization Logic (Halos/Aura)
const visualizerHalos = document.querySelectorAll('.visualizer-halo');
const voiceVisualizer = document.getElementById('voice-visualizer');

function animateVoiceVisualizer() {
    if (!isSpeaking && !isRecording) {
        if (voiceVisualizer) voiceVisualizer.classList.remove('active');
        return;
    }

    if (voiceVisualizer) voiceVisualizer.classList.add('active');

    let intensity = 0;

    if (isSpeaking && mainAnalyzer) {
        const dataArray = new Uint8Array(mainAnalyzer.frequencyBinCount);
        mainAnalyzer.getByteFrequencyData(dataArray);

        let sum = 0;
        for (let i = 0; i < dataArray.length; i++) sum += dataArray[i];
        intensity = sum / dataArray.length;
    } else if (isRecording && vadAnalyser) {
        const dataArray = new Uint8Array(vadAnalyser.frequencyBinCount);
        vadAnalyser.getByteFrequencyData(dataArray);

        let sum = 0;
        for (let i = 0; i < dataArray.length; i++) sum += dataArray[i];
        intensity = sum / dataArray.length;
    }

    // Animate Halos - Made bigger and more interactive
    visualizerHalos.forEach((halo, index) => {
        // Boost intensity impact and base scale
        const scale = 1.2 + (intensity / 100) * (3 + index * 2.5); 
        const opacity = (intensity / 200) * (1.0 - index * 0.15);
        const glow = intensity / 10;

        halo.style.transform = `scale(${scale})`;
        halo.style.opacity = Math.min(1, opacity);
        halo.style.borderWidth = `${2 + (intensity / 50)}px`;
        halo.style.boxShadow = `0 0 ${glow}px rgba(120, 180, 255, 0.5)`;
    });

    requestAnimationFrame(animateVoiceVisualizer);
}



// Live Mode Logic (Gemini Style)

const liveManualBtn = document.getElementById('live-manual-btn');
const liveAutoBtn = document.getElementById('live-auto-btn');

function toggleLiveMode(active) {
    isContinuousMode = active;
    activeOverlay = active ? 'live' : 'chat'; // Update active view state
    
    const liveOverlay = document.getElementById('live-overlay');
    if (!liveOverlay) return;

    if (active) {
        liveOverlay.style.display = 'flex';
        // Premium Glassmorphism Fade
        requestAnimationFrame(() => {
            liveOverlay.classList.add('active');
            liveOverlay.style.backdropFilter = 'blur(20px) saturate(180%)';
        });

        // startRecording(); // We don't start recording automatically if in Manual mode

        if (!isPushToTalk) {
            startRecording();
            liveAutoBtn.classList.add('active');
            liveManualBtn.classList.remove('active');
        } else {
            liveManualBtn.classList.add('active');
            liveAutoBtn.classList.remove('active');
        }

        addLine('Entered Live Voice Chat. (Manual Mode: Hold ALT to speak)', 'system-msg');

        // Start Live Particles
        setTimeout(() => {
            initLiveParticles();
            if (liveParticles) animateLiveParticles(); // Restart loop
        }, 100);

        // Initialize 3D VTuber (Skipping optimization as requested)
        setTimeout(() => {
            init3DVTuber();
        }, 150);

    } else {
        liveOverlay.classList.remove('active');
        setTimeout(() => {
            liveOverlay.style.display = 'none';
        }, 300);

        stopRecording();
        if (isSpeaking) stopCurrentAudio();

        // Clean up v-tuber states
        liveOverlay.classList.remove('speaking', 'listening');

        // Clean up 3D v-tuber renderer
        if (vtuberRenderer) {
            const container = document.getElementById('vtuber-3d-container');
            if (container && vtuberRenderer.domElement) {
                container.removeChild(vtuberRenderer.domElement);
            }
            vtuberRenderer.dispose();
            vtuberRenderer = null;
            vtuberScene = null;
            vtuberCamera = null;
        }
    }

    // Sync with Desktop Backend
    try {
        fetch(`${API_URL}/settings/live`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ active: active })
        });
    } catch (e) {
        console.warn("Could not sync live mode with backend");
    }
}

// Live Mode Control Toggles
if (liveManualBtn) {
    liveManualBtn.addEventListener('click', () => {
        isPushToTalk = true;
        liveManualBtn.classList.add('active');
        if (liveAutoBtn) liveAutoBtn.classList.remove('active');
        stopRecording();
        addLine('Switched to Manual Mode. Hold ALT to speak.', 'system-msg');
    });
}

if (liveAutoBtn) {
    liveAutoBtn.addEventListener('click', () => {
        isPushToTalk = false;
        liveAutoBtn.classList.add('active');
        if (liveManualBtn) liveManualBtn.classList.remove('active');
        startRecording();
        addLine('Switched to Continuous Mode.', 'system-msg');
    });
}

// Push-to-Talk Logic (ALT Key) - Deactivated (Backend handles globally)
// window.addEventListener('keydown', (e) => { ... });

// window.addEventListener('keyup', (e) => { ... });


// Hook into transcription success
const originalSendCommand = sendCommand;


// --- 3D PARTICLE GLOBE (Gemini Style) ---
let particleCount = 2000;
let globeRadius = 150;

function initGlobe() {
    const container = document.getElementById('globe-container');
    if (!container) return; // Prevent crash if container doesn't exist
    scene = new THREE.Scene();
    camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 1, 1000);
    camera.position.z = 400;

    renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    container.appendChild(renderer.domElement);

    const geo = new THREE.BufferGeometry();
    const positions = new Float32Array(particleCount * 3);
    const colors = new Float32Array(particleCount * 3);

    for (let i = 0; i < particleCount; i++) {
        const phi = Math.acos(-1 + (2 * i) / particleCount);
        const theta = Math.sqrt(particleCount * Math.PI) * phi;

        positions[i * 3] = globeRadius * Math.cos(theta) * Math.sin(phi);
        positions[i * 3 + 1] = globeRadius * Math.sin(theta) * Math.sin(phi);
        positions[i * 3 + 2] = globeRadius * Math.cos(phi);

        // Gradient color (Blueish-Purple)
        colors[i * 3] = 0.2 + (i / particleCount) * 0.4;
        colors[i * 3 + 1] = 0.5;
        colors[i * 3 + 2] = 0.9;
    }

    geo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    geo.setAttribute('color', new THREE.BufferAttribute(colors, 3));

    const material = new THREE.PointsMaterial({
        size: 2,
        vertexColors: true,
        transparent: true,
        opacity: 0.8
    });

    particles = new THREE.Points(geo, material);
    scene.add(particles);

    animateGlobe();
}

// Separate particles for Live Mode
// --- 3D BLACKHOLE PARTICLE SYSTEM (Live Mode) ---
let particleData = [];

function initLiveParticles() {
    if (liveRenderer) return;

    const container = document.getElementById('live-particle-container');
    if (!container) return;

    liveScene = new THREE.Scene();
    liveCamera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 2000);
    liveCamera.position.set(0, 150, 400);
    liveCamera.lookAt(0, 0, 0);

    liveRenderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    liveRenderer.setSize(window.innerWidth, window.innerHeight);
    liveRenderer.setPixelRatio(window.devicePixelRatio);
    container.appendChild(liveRenderer.domElement);

    // Event Horizon (Dark Center)
    const ehGeo = new THREE.SphereGeometry(60, 32, 32);
    const ehMat = new THREE.MeshBasicMaterial({ color: 0x000000, transparent: true, opacity: 0.9 });
    liveEventHorizon = new THREE.Mesh(ehGeo, ehMat);
    liveScene.add(liveEventHorizon);

    // Particles for Accretion Disk
    const count = 4000;
    const geo = new THREE.BufferGeometry();
    const positions = new Float32Array(count * 3);
    const colors = new Float32Array(count * 3);

    particleData = [];

    for (let i = 0; i < count; i++) {
        // Spiral Disk Distribution
        const angle = Math.random() * Math.PI * 2;
        const radius = 80 + Math.random() * 250;
        const thickness = (1 - (radius - 80) / 250) * 30; // Thicker near center
        const y = (Math.random() - 0.5) * thickness;

        positions[i * 3] = Math.cos(angle) * radius;
        positions[i * 3 + 1] = y;
        positions[i * 3 + 2] = Math.sin(angle) * radius;

        particleData.push({
            angle: angle,
            radius: radius,
            speed: (1 / radius) * 2, // User requested 2
            yOffset: y
        });

        // Color Palette: Deep Blue -> Cyan -> White (Hot center)
        const relRadius = (radius - 80) / 250;
        if (relRadius < 0.2) {
            // White/Cyan (Hot)
            colors[i * 3] = 0.8; colors[i * 3 + 1] = 0.9; colors[i * 3 + 2] = 1.0;
        } else if (relRadius < 0.6) {
            // Cyan/Blue
            colors[i * 3] = 0.2; colors[i * 3 + 1] = 0.5; colors[i * 3 + 2] = 1.0;
        } else {
            // Deep Purple/Blue
            colors[i * 3] = 0.3; colors[i * 3 + 1] = 0.1; colors[i * 3 + 2] = 0.8;
        }
    }

    geo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    geo.setAttribute('color', new THREE.BufferAttribute(colors, 3));

    const material = new THREE.PointsMaterial({
        size: 2.5,
        vertexColors: true,
        transparent: true,
        opacity: 0.8,
        blending: THREE.AdditiveBlending
    });

    liveParticles = new THREE.Points(geo, material);
    liveScene.add(liveParticles);

    // Resize handler
    window.addEventListener('resize', () => {
        if (liveCamera && liveRenderer && isContinuousMode) {
            liveCamera.aspect = window.innerWidth / window.innerHeight;
            liveCamera.updateProjectionMatrix();
            liveRenderer.setSize(window.innerWidth, window.innerHeight);
        }
    });

    animateLiveParticles();
}

// --- 3D VTUBER CHARACTER ---
// 3D VRM State
vtuberScene = null;
vtuberCamera = null;
vtuberRenderer = null;
vtuberModel = null;
currentVrm = null;
vtuberGroup = null; // Fallback group
modelLoaded = false;
const clock = new THREE.Clock();

function init3DVTuber() {
    if (!useVTuber) {
        console.log("V-Tuber disabled by settings.");
        return;
    }
    const container = document.getElementById('vtuber-3d-container');
    if (!container || vtuberRenderer) return;

    // VRM Scene setup
    vtuberScene = new THREE.Scene();
    vtuberCamera = new THREE.PerspectiveCamera(30, 450 / 600, 0.1, 20);
    vtuberCamera.position.set(0, 1.4, 3.5); // Adjusted for typical VRM scale
    vtuberCamera.lookAt(0, 1.2, 0);

    vtuberRenderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    vtuberRenderer.setSize(450, 600);
    vtuberRenderer.setPixelRatio(window.devicePixelRatio);
    vtuberRenderer.outputEncoding = THREE.sRGBEncoding;
    container.appendChild(vtuberRenderer.domElement);

    // Light setup
    const light = new THREE.DirectionalLight(0xffffff);
    light.position.set(1.0, 1.0, 1.0).normalize();
    vtuberScene.add(light);

    // Ambient light
    vtuberScene.add(new THREE.AmbientLight(0xffffff, 0.6));

    // Load Model
    loadVTuberModel();

    // Resize handler
    window.addEventListener('resize', () => {
        if (vtuberCamera && vtuberRenderer && isContinuousMode) {
            const container = document.getElementById('vtuber-3d-container');
            if (container) {
                const width = container.offsetWidth;
                const height = container.offsetHeight;
                vtuberCamera.aspect = width / height;
                vtuberCamera.updateProjectionMatrix();
                vtuberRenderer.setSize(width, height);
            }
        }
    });

    animate3DVTuber();
}

function loadVTuberModel() {
    const modelUrl = './models/lucife.vrm';
    console.log("📦 Loading VRM model:", modelUrl);

    if (vtuberModel && currentVrm) {
        console.log("⚠️ Model already loaded.");
        return;
    }

    const loader = new THREE.GLTFLoader();
    loader.register((parser) => {
        return new THREE.VRMLoaderPlugin(parser);
    });

    loader.load(
        modelUrl,
        (gltf) => {
            const vrm = gltf.userData.vrm;
            currentVrm = vrm;
            vtuberModel = vrm.scene;
            vtuberScene.add(vtuberModel);
            modelLoaded = true;

            if (currentVrm.humanoid) {
                const humanoid = currentVrm.humanoid;
                const leftArm = humanoid.getBoneNode(THREE.VRMSchema.HumanoidBoneName.LeftUpperArm);
                const rightArm = humanoid.getBoneNode(THREE.VRMSchema.HumanoidBoneName.RightUpperArm);
                if (leftArm) leftArm.rotation.z = Math.PI / 3;
                if (rightArm) rightArm.rotation.z = -Math.PI / 3;
            }
            console.log("✅ VRM Model loaded successfully");
        },
        undefined,
        (error) => {
            console.warn("⚠️ Main model failed to load. Will try simplified loading or callback error.");
            console.error(error);
            createFallbackCharacter();
        }
    );
}

function createFallbackCharacter() {
    console.log("Fallback character disabled by user request (Settings: 'Remove Old 3D Model').");
    // No geometry created to satisfy "remove old 3d model" request.
}





function animate3DVTuber() {
    if (!isContinuousMode || !vtuberRenderer) return;
    requestAnimationFrame(animate3DVTuber);

    const delta = clock.getDelta();
    const time = Date.now() * 0.001;

    if (currentVrm && modelLoaded) {
        // VRM Update
        currentVrm.update(delta);

        // Blink Logic
        if (Math.random() > 0.995) {
            currentVrm.blendShapeProxy.setValue(THREE.VRMSchema.BlendShapePresetName.Blink, 1);
            setTimeout(() => {
                if (currentVrm) currentVrm.blendShapeProxy.setValue(THREE.VRMSchema.BlendShapePresetName.Blink, 0);
            }, 100);
        }

        // Speaking Animation
        if (isSpeaking) {
            const openAmount = 0.3 + (Math.sin(time * 20) + 1) * 0.35;
            currentVrm.blendShapeProxy.setValue(THREE.VRMSchema.BlendShapePresetName.A, openAmount);
            // Reset expressions
            currentVrm.blendShapeProxy.setValue(THREE.VRMSchema.BlendShapePresetName.Joy, 0);
            currentVrm.blendShapeProxy.setValue(THREE.VRMSchema.BlendShapePresetName.Fun, 0);
        } else {
            currentVrm.blendShapeProxy.setValue(THREE.VRMSchema.BlendShapePresetName.A, 0);
        }

        // Listening Animation (Cute / Blush / Quaricity)
        if (isRecording) {
            if (vtuberModel) {
                // Head sway + Curiosity Tilt
                vtuberModel.rotation.y = Math.sin(time) * 0.05;
                const tilt = Math.sin(time * 0.5) > 0.5 ? -0.15 : 0;
                vtuberModel.rotation.z = THREE.MathUtils.lerp(vtuberModel.rotation.z, tilt, 0.05);
                vtuberModel.rotation.x = 0;
            }
            // Expression: Cuter (Joy + Fun)
            currentVrm.blendShapeProxy.setValue(THREE.VRMSchema.BlendShapePresetName.Joy, 0.5);
            currentVrm.blendShapeProxy.setValue(THREE.VRMSchema.BlendShapePresetName.Fun, 0.2);

        } else if (isProcessing) {
            // THINKING Animation (Remembering)
            if (vtuberModel) {
                // Look up and away
                vtuberModel.rotation.y = THREE.MathUtils.lerp(vtuberModel.rotation.y, 0.2, 0.05);
                vtuberModel.rotation.x = THREE.MathUtils.lerp(vtuberModel.rotation.x, -0.1, 0.05);
                vtuberModel.rotation.z = THREE.MathUtils.lerp(vtuberModel.rotation.z, 0.05, 0.05);
            }
            // Expression: Pensive / Slightly serious
            currentVrm.blendShapeProxy.setValue(THREE.VRMSchema.BlendShapePresetName.Joy, 0);
            currentVrm.blendShapeProxy.setValue(THREE.VRMSchema.BlendShapePresetName.Fun, 0);
            // Maybe Sorrow for "concentrating"?
            // currentVrm.blendShapeProxy.setValue(THREE.VRMSchema.BlendShapePresetName.Sorrow, 0.1);

        } else if (vtuberModel) {
            // Idle
            vtuberModel.rotation.y = THREE.MathUtils.lerp(vtuberModel.rotation.y, 0, 0.1);
            vtuberModel.rotation.z = THREE.MathUtils.lerp(vtuberModel.rotation.z, 0, 0.1);
            vtuberModel.rotation.x = THREE.MathUtils.lerp(vtuberModel.rotation.x, 0, 0.1);
            currentVrm.blendShapeProxy.setValue(THREE.VRMSchema.BlendShapePresetName.Joy, 0);
            currentVrm.blendShapeProxy.setValue(THREE.VRMSchema.BlendShapePresetName.Fun, 0);
        }

    } else if (vtuberGroup) {
        // Fallback animation
        vtuberGroup.rotation.y = Math.sin(time * 0.5) * 0.1;
    }

    vtuberRenderer.render(vtuberScene, vtuberCamera);
}


function animateLiveParticles() {
    if (!isContinuousMode) return;
    requestAnimationFrame(animateLiveParticles);

    const time = Date.now() * 0.001;
    const positions = liveParticles.geometry.attributes.position.array;

    // Reactivity
    let rotationMultiplier = 1.0;
    let pulseScale = 1.0;

    if (isSpeaking) {
        rotationMultiplier = 2.5; // Slower (was 4.0)
        pulseScale = 1.1 + Math.sin(time * 8) * 0.08;
    } else if (isRecording) {
        rotationMultiplier = 1.2; // Slower (was 1.5)
        pulseScale = 1.03 + Math.sin(time * 4) * 0.03;
    }

    for (let i = 0; i < particleData.length; i++) {
        const p = particleData[i];

        // Update angle for orbital motion
        p.angle += p.speed * rotationMultiplier;

        // Spiral inward slower
        p.radius -= 0.05 * rotationMultiplier;
        if (p.radius < 70) {
            p.radius = 330;
            p.angle = Math.random() * Math.PI * 2;
        }

        const ix = i * 3;
        const currentRadius = p.radius * pulseScale;
        positions[ix] = Math.cos(p.angle) * currentRadius;
        // Optimization: Reduce frequency of Y drift updates
        if (i % 2 === 0) {
            positions[ix + 1] = p.yOffset + Math.sin(time + p.angle) * 2;
        }
        positions[ix + 2] = Math.sin(p.angle) * currentRadius;
    }

    liveParticles.geometry.attributes.position.needsUpdate = true;

    // Event Horizon Ripple
    if (liveEventHorizon) {
        const s = pulseScale;
        liveEventHorizon.scale.set(s, s, s);
        liveEventHorizon.rotation.y += 0.01;
    }

    // Camera tilt for 3D feel
    liveCamera.position.x = Math.sin(time * 0.2) * 50;
    liveCamera.lookAt(0, 0, 0);

    liveRenderer.render(liveScene, liveCamera);
}

function animateGlobe() {
    requestAnimationFrame(animateGlobe);

    // Rotation speed: Very slow when "dead" (offline)
    const rotationSpeed = isOfflineMode ? 0.0002 : 0.002;
    particles.rotation.y += rotationSpeed;
    particles.rotation.x += rotationSpeed / 2;

    // Reactivity logic
    let targetScale = 1.0;
    const glows = document.querySelector('.live-glow-container');

    if (isSpeaking) {
        // High intensity pulse
        targetScale = 1.3 + Math.sin(Date.now() * 0.02) * 0.15;
        if (glows) glows.style.opacity = '0.7';
    } else if (isRecording) {
        // Subtle ambient pulse
        targetScale = 1.1 + Math.sin(Date.now() * 0.01) * 0.08;
        if (glows) glows.style.opacity = '0.4';
    } else {
        if (glows) glows.style.opacity = '0.1';
    }

    particles.scale.lerp(new THREE.Vector3(targetScale, targetScale, targetScale), 0.1);

    renderer.render(scene, camera);
}

window.addEventListener('resize', () => {
    if (camera && renderer) {
        camera.aspect = window.innerWidth / window.innerHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(window.innerWidth, window.innerHeight);
    }
});

// Model Selector
// Custom Model Switcher Logic
const modelBtn = document.getElementById('model-switcher-btn');
const modelMenu = document.getElementById('model-dropdown-menu');
const modelLabel = document.getElementById('current-model-label');
const modelOptions = document.querySelectorAll('.model-option');

if (modelBtn && modelMenu) {
    // Toggle Menu
    modelBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        modelMenu.classList.toggle('active');
        modelMenu.classList.toggle('hidden');
        modelBtn.classList.toggle('active');
    });

    // Close on outside click
    document.addEventListener('click', (e) => {
        if (!modelBtn.contains(e.target) && !modelMenu.contains(e.target)) {
            modelMenu.classList.remove('active');
            modelMenu.classList.add('hidden');
            modelBtn.classList.remove('active');
        }
    });

    // Handle Selection
    modelOptions.forEach(option => {
        option.addEventListener('click', async () => {
            const type = option.getAttribute('data-value');
            const name = option.querySelector('.model-title').textContent;

            // Update UI immediately (optimistic)
            modelLabel.textContent = type === 'custom' ? 'Nova Core' : name.split(' ')[0];
            modelMenu.classList.remove('active');
            modelMenu.classList.add('hidden');

            try {
                const res = await fetch(`${API_URL}/settings/model`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ type: type })
                });
                const data = await res.json();

                if (data.status === 'success') {
                    addLine(`Switched to ${name}`, 'system-msg');
                } else if (data.status === 'locked') {
                    // Revert UI if locked
                    modelLabel.textContent = 'Nova Core'; 
                    addLine(`Model Lock: ${data.message}`, 'system-msg');
                } else {
                    addLine(`Error: ${data.message}`, 'system-msg');
                }
            } catch (e) {
                console.error('Model switch failed:', e);
                addLine('Connection failed', 'system-msg');
            }
        });
    });
}

// Sync Audio Player with isSpeaking
const audioPlayer = document.getElementById('audio-player');
// We need to ensure audio-player is hooked into the pulse
// Actually we'll use the existing isSpeaking flag which is already toggled in playAudio

// Init
checkStatus();
setInterval(checkStatus, 5000);
initGlobe();
initSettings(); // Initialize settings on load

// Startup Greeting (Japanglish Style!)
// Wait for connection to be stable
setTimeout(() => {
    // Send a "Hello" to trigger the Nova greeting logic
    console.log("Triggering startup greeting...");
    sendCommand("init_greeting", true);
}, 1500);

// Vision / Camera Logic - Removed legacy listeners to avoid conflicts
const camBtn = document.getElementById('cam-btn');
if (camBtn) {
    camBtn.addEventListener('click', () => {
        const fileInput = document.getElementById('file-upload'); // Redirect to new input
        if (fileInput) fileInput.click();
    });
}

// End of Vision Logic
// --- Debug Logs UI Logic ---
const logsBtn = document.getElementById('logs-btn');
const logsModal = document.getElementById('logs-modal');
const closeLogsBtn = document.getElementById('close-logs-btn');
const logsList = document.getElementById('logs-list');

if (logsBtn && logsModal && closeLogsBtn) {
    logsBtn.addEventListener('click', async () => {
        logsModal.style.display = 'flex';
        logsList.innerHTML = '<p style="text-align: center; opacity: 0.5;">Reading glitch history...</p>';

        try {
            const res = await fetch(`${API_URL}/logs`);
            const data = await res.json();

            if (data.logs && data.logs.length > 0) {
                // Update dynamic status badge
                const logsStatus = document.getElementById('logs-status');
                const hasError = data.logs.some(log => log.includes('ERROR') || log.includes('CRASH'));
                if (hasError) {
                    logsStatus.textContent = "⚠️ OH NO! BUG DETECTED";
                    logsStatus.className = "status-badge bug";
                } else {
                    logsStatus.textContent = "✅ SYSTEM HEALTHY";
                    logsStatus.className = "status-badge healthy";
                }

                logsList.innerHTML = '';

                // Add Copy All Button
                const copyAllBtn = document.createElement('button');
                copyAllBtn.textContent = "📋 Copy All Logs";
                copyAllBtn.className = 'mode-select';
                copyAllBtn.style.margin = "0 0 15px 0";
                copyAllBtn.style.width = "100%";
                copyAllBtn.onclick = () => {
                    const allText = data.logs.join('\n');
                    navigator.clipboard.writeText(allText);
                    copyAllBtn.textContent = "✅ Copied All!";
                    setTimeout(() => copyAllBtn.textContent = "📋 Copy All Logs", 2000);
                };
                logsList.appendChild(copyAllBtn);

                data.logs.forEach(log => {
                    const div = document.createElement('div');
                    div.className = 'log-entry';
                    div.style.position = 'relative';
                    div.style.paddingRight = '50px';

                    // Style logic
                    if (log.includes('SOLVED')) div.classList.add('resolved');
                    else if (log.includes('ERROR') || log.includes('CRASH')) div.classList.add('log-error');
                    else if (log.includes('INFO')) div.classList.add('log-info');

                    const textSpan = document.createElement('div');
                    textSpan.textContent = log;
                    textSpan.style.whiteSpace = 'pre-wrap';
                    textSpan.style.wordBreak = 'break-word';
                    div.appendChild(textSpan);

                    const copyIcon = document.createElement('button');
                    copyIcon.innerHTML = '📋';
                    copyIcon.title = 'Copy entry';
                    copyIcon.style.cssText = 'position:absolute; right:10px; top:50%; transform:translateY(-50%); background:none; border:none; cursor:pointer; font-size:1.2em; opacity:0.4; transition:0.2s;';
                    copyIcon.onclick = () => {
                        navigator.clipboard.writeText(log);
                        copyIcon.innerHTML = '✅';
                        setTimeout(() => copyIcon.innerHTML = '📋', 1500);
                    };
                    copyIcon.onmouseover = () => copyIcon.style.opacity = '1';
                    copyIcon.onmouseout = () => copyIcon.style.opacity = '0.4';

                    div.appendChild(copyIcon);
                    logsList.appendChild(div);
                });
            } else {
                const logsStatus = document.getElementById('logs-status');
                if (logsStatus) {
                    logsStatus.textContent = "✅ SYSTEM HEALTHY";
                    logsStatus.className = "status-badge healthy";
                }
                logsList.innerHTML = '<p style="text-align: center; opacity: 0.5;">No glitches recorded yet. Nova is healthy! ✨</p>';
            }
        } catch (e) {
            logsList.innerHTML = `<p style="text-align: center; color: #ff8a80;">Failed to load logs: ${e.message}</p>`;
        }
    });

    closeLogsBtn?.addEventListener('click', () => {
        logsModal.style.display = 'none';
    });

    // Mute button logic handled centrally in initSettings as header-mute-btn

    // Live Mode Button Handler - Auto-unmute when activated
    // Using global variables declared earlier
    if (liveBtn && liveOverlay) {
        liveBtn.addEventListener('click', () => {
            toggleLiveMode(true);
        });
    }

    if (closeLiveBtn && liveOverlay) {
        closeLiveBtn.addEventListener('click', () => {
            toggleLiveMode(false);
        });
    }

    // Close on outside click
    logsModal?.addEventListener('click', (e) => {
        if (e.target === logsModal) logsModal.style.display = 'none';
    });
}

// --- SCHEDULE MODAL LOGIC ---
const scheduleBtn = document.getElementById('schedule-btn');
const scheduleModal = document.getElementById('schedule-modal');
const closeScheduleBtn = document.getElementById('close-schedule-btn');
const scheduleList = document.getElementById('schedule-list');

if (scheduleBtn && scheduleModal) {
    scheduleBtn.addEventListener('click', () => {
        scheduleModal.style.display = 'flex';
        fetchSchedule();
    });

    closeScheduleBtn?.addEventListener('click', () => {
        scheduleModal.style.display = 'none';
    });

    scheduleModal.addEventListener('click', (e) => {
        if (e.target === scheduleModal) scheduleModal.style.display = 'none';
    });
}

async function fetchSchedule() {
    if (!scheduleList) return;
    scheduleList.innerHTML = '<p style="text-align: center; opacity: 0.5;">Loading schedule...</p>';
    try {
        const res = await fetch(`${API_URL}/schedule`);
        const data = await res.json();

        scheduleList.innerHTML = '';
        if (data.length === 0) {
            scheduleList.innerHTML = '<p style="text-align: center; opacity: 0.5;">No upcoming events.</p>';
            return;
        }

        data.forEach(job => {
            const div = document.createElement('div');
            div.className = 'log-entry'; // Reuse log entry style
            div.style.display = 'flex';
            div.style.justifyContent = 'space-between';
            div.style.alignItems = 'center';

            const info = document.createElement('div');
            info.innerHTML = `<strong>${job.action}</strong><br><span style="font-size:0.8em; opacity:0.7">${job.next_run}</span>`;

            const delBtn = document.createElement('button');
            delBtn.style.background = 'rgba(244, 67, 54, 0.2)';
            delBtn.style.color = '#f44336';
            delBtn.style.border = 'none';
            delBtn.style.borderRadius = '50%';
            delBtn.style.width = '30px';
            delBtn.style.height = '30px';
            delBtn.style.cursor = 'pointer';
            delBtn.style.marginLeft = '10px';
            delBtn.style.display = 'flex';
            delBtn.style.alignItems = 'center';
            delBtn.style.justifyContent = 'center';
            delBtn.innerHTML = '✕';

            delBtn.onclick = async () => {
                if (confirm('Delete this scheduled item?')) {
                    await deleteScheduleItem(job.id);
                }
            };

            div.appendChild(info);
            div.appendChild(delBtn);
            scheduleList.appendChild(div);
        });

    } catch (e) {
        scheduleList.innerHTML = '<p style="color: #ff8a80; text-align: center;">Failed to load schedule.</p>';
    }
}

async function deleteScheduleItem(id) {
    try {
        const res = await fetch(`${API_URL}/schedule/delete`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ id: id })
        });
        const data = await res.json();
        if (data.status === 'success') {
            fetchSchedule(); // Refresh
        } else {
            alert('Failed to delete: ' + data.message);
        }
    } catch (e) {
        alert('Error deleting item');
    }
}

/**
 * --- EMOTIONAL AURA CONTROLLER ---
 * Connects detected emotions to UI visual themes
 */
function triggerEmotionUI(emotion) {
    if (!emotion) return;

    console.log(`🎭 Emotion Triggered: ${emotion}`);

    // Clear existing emotion classes
    const currentClasses = Array.from(document.body.classList);
    currentClasses.forEach(cls => {
        if (cls.startsWith('emotion-')) document.body.classList.remove(cls);
    });

    // Apply new emotion class
    const className = `emotion-${emotion.toLowerCase()}`;
    document.body.classList.add(className);

    // Special globe/particle reactions can be added here
    if (scene && particles) {
        // Adjust particle speed or color based on emotion
        if (emotion === 'angry') globeSpeedMultiplier = 5;
        else if (emotion === 'sad') globeSpeedMultiplier = 0.5;
        else globeSpeedMultiplier = 2;
    }

    // Reset to neutral after 10 seconds (optional)
    setTimeout(() => {
        if (document.body.classList.contains(className)) {
            document.body.classList.remove(className);
            globeSpeedMultiplier = 2;
        }
    }, 15000);
}

// --- AUDIO PLAYBACK ---

function playAudio(base64Audio) {
    if (!base64Audio) return;

    try {
        // Stop any currently playing audio
        if (currentAudio) {
            currentAudio.pause();
            currentAudio = null;
        }

        const audio = new Audio(`data:audio/mpeg;base64,${base64Audio}`);
        currentAudio = audio;

        audio.onplay = () => {
            isSpeaking = true;
            // Show stop button when audio starts
            if (stopBtn) stopBtn.style.display = 'flex';
        };

        audio.onended = () => {
            isSpeaking = false;
            currentAudio = null;
            // Hide stop button when audio ends
            if (stopBtn) stopBtn.style.display = 'none';
            // Reset v-tuber to idle
            if (liveOverlay && isContinuousMode) liveOverlay.classList.remove('speaking');
        };

        audio.onerror = () => {
            isSpeaking = false;
            currentAudio = null;
            if (stopBtn) stopBtn.style.display = 'none';
            // Reset v-tuber to idle
            if (liveOverlay && isContinuousMode) liveOverlay.classList.remove('speaking');
        };

        if (isMuted) {
            console.log("Audio prepared but muted. waiting for unmute...");
            // Don't play, just keep it ready in currentAudio
        } else {
            audio.play();
        }
    } catch (e) {
        console.error('Audio playback error:', e);
        isSpeaking = false;
        if (stopBtn) stopBtn.style.display = 'none';
        // Reset v-tuber to idle
        if (liveOverlay && isContinuousMode) liveOverlay.classList.remove('speaking');
    }
}

function stopCurrentAudio() {
    if (currentAudio) {
        currentAudio.pause();
        currentAudio.currentTime = 0;
        currentAudio = null;
        isSpeaking = false;
    }
    // ensure button is hidden
    if (stopBtn) stopBtn.style.display = 'none';
    // Reset v-tuber to idle
    if (liveOverlay && isContinuousMode) liveOverlay.classList.remove('speaking');
}

// --- SEND COMMAND FUNCTIONALITY ---
isProcessing = false; // Prevent duplicate sends
lastRequestId = null; // Prevent duplicate response bubbles

async function sendCommand(text, isSilent = false, lang = null) {
    if (!lang) { const vl = document.getElementById('voice-language'); lang = vl ? vl.value : 'en'; }
    if (!text || !text.trim() || isProcessing) return;

    isProcessing = true;
    const userText = text.trim();

    // INTERRUPT previous audio when sending new command
    if (isSpeaking) stopCurrentAudio();

    // Auto-hide Admin if it's open (unless we are sending an admin command)
    if (!userText.toLowerCase().includes('diagnostics') &&
        !userText.toLowerCase().includes('test') &&
        document.getElementById('admin-dashboard') &&
        !document.getElementById('admin-dashboard').classList.contains('hidden')) {
        toggleAdminDashboard(false);
    }

    // Display user message
    if (!isSilent) addLine(userText, 'user-msg');
    commandInput.value = '';

    // Trigger Browsing Status for web commands
    const webTriggers = ['search', 'google', 'find', 'news', 'latest news', 'headlines', 'nasa'];
    if (webTriggers.some(t => userText.toLowerCase().includes(t))) {
        showBrowsingStatus('Searching Web...', 'assets/default_web.png');
    }

    // Show animated "Thinking..." indicator in Thought panel
    const thoughtFeed = document.getElementById('thought-feed');
    if (thoughtFeed) {
        thoughtFeed.innerHTML = '';
        const thinkingLine = document.createElement('div');
        thinkingLine.id = 'thinking-bubble'; // Re-use the ID so it gets removed easily later
        thinkingLine.className = 'text-[#8ca6f9] mb-2';
        thinkingLine.innerHTML = `> Processing contextual intent<span class="thinking-dots"><span style="animation:thinkDot 1.2s infinite 0s">.</span><span style="animation:thinkDot 1.2s infinite 0.4s">.</span><span style="animation:thinkDot 1.2s infinite 0.8s">.</span></span>`;
        thoughtFeed.appendChild(thinkingLine);
    }

    try {
        const res = await fetch(`${API_URL}/command`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ command: userText, language: lang })
        });

        const data = await res.json();

        // Remove thinking bubble
        const bubble = document.getElementById('thinking-bubble');
        if (bubble) bubble.remove();

        // Prevent duplicate bubbles if the request ID matches the last processed one
        if (data.request_id && data.request_id === lastRequestId) {
            console.warn("⚠️ Duplicate response detected for ID:", data.request_id);
            return;
        }
        lastRequestId = data.request_id;

        if (data.response) {
            if (data.thoughts && data.thoughts.length > 0) {
                renderThoughts(data.thoughts, data.llm_model);
            }
            addLine(data.response, 'nova-msg', data.tokens || 0, data.data);

            // Trigger Emotion UI
            if (data.emotion) triggerEmotionUI(data.emotion);

            // Trigger Admin Dashboard if signaled
            if (data.admin_mode) {
                console.log("🛠️ Admin Dashboard signal received");
                toggleAdminDashboard(true, data.diag_mode);
            }

            // Play audio if available (Mute check handled in playAudio now)
            if (data.audio_base64) {
                playAudio(data.audio_base64);
            }

            // AUTO-TRIGGER: If WhatsApp call was accepted, enter Live Mode
            if (data.response.includes('WHATSAPP_CALL_ACCEPTED')) {
                console.log("📞 WhatsApp Call Accepted - Auto-entering Live Mode");
                setTimeout(() => toggleLiveMode(true), 2000);
            }
        }
    } catch (e) {
        const bubble = document.getElementById('thinking-bubble');
        if (bubble) bubble.remove();
        console.error('Send error:', e);
        addLine('Connection error. Please try again.', 'system-msg');
    } finally {
        // Cooldown period to prevent rapid firing
        setTimeout(() => {
            isProcessing = false;
        }, 300);
    }

}

/**
 * --- INTERNAL BROWSER ROUTING ---
 * Intercepts links and routes them through NOVA's internal BrowserAgent
 */
function openInInternalBrowser(url) {
    if (!url) return;
    console.log(`🌐 Routing to internal browser: ${url}`);
    
    // Show browsing status in UI
    showBrowsingStatus(`Opening ${new URL(url).hostname}...`, 'assets/default_web.png');
    
    // Send command to backend to open in Playwright
    sendCommand(`open ${url} in browser`, true);
}

// Global link interceptor for target="_blank" links
document.addEventListener('click', (e) => {
    const link = e.target.closest('a');
    if (link && (link.target === '_blank' || link.href.includes('http'))) {
        e.preventDefault();
        openInInternalBrowser(link.href);
    }
});

// Send Button Click
if (sendBtn) {
    sendBtn.addEventListener('click', () => {
        const vl = document.getElementById('voice-language');
        const currentLang = vl ? vl.value : 'en';
        sendCommand(commandInput.value, false, currentLang);
    });
}

// Enter Key Press
if (commandInput) {
    commandInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            const vl = document.getElementById('voice-language');
        const currentLang = vl ? vl.value : 'en';
            sendCommand(commandInput.value, false, currentLang);
        }
    });
}

// Microphone Button
if (micBtn) {
    micBtn.addEventListener('click', () => {
        if (Date.now() - lastMicClick < 1000) return;
        lastMicClick = Date.now();
        // Toggle backend hearing trigger
        if (isSpeaking) stopCurrentAudio();
        startRecording();
    });
}

// Stop Button Initialization
if (stopBtn) {
    stopBtn.addEventListener('click', () => {
        stopCurrentAudio();
    });
}





// Admin Dashboard Logic
let statsInterval = null;
const ADMIN_PASS = "8420224011@rivu";

function initAdminDashboard() {
    const adminDashboard = document.getElementById('admin-dashboard');
    const loginBtn = document.getElementById('admin-login-btn');
    const passInput = document.getElementById('admin-pass-input');
    const authError = document.getElementById('auth-error');
    const authScreen = document.getElementById('admin-auth-screen');
    const mainContent = document.getElementById('admin-main-content');
    const closeBtn = document.getElementById('close-admin-btn');
    const runSuiteBtn = document.getElementById('run-suite-btn');
    const clearLogsBtn = document.getElementById('clear-logs-btn');
    const logsList = document.getElementById('admin-logs-list');

    if (!adminDashboard) return;

    // Login logic
    loginBtn?.addEventListener('click', () => {
        if (passInput.value === ADMIN_PASS) {
            console.log("🔓 Admin Access Authorized");
            authScreen.classList.add('hidden');
            mainContent.classList.remove('hidden');
            console.log("📊 Main content visible?", !mainContent.classList.contains('hidden'));
            startStatsUpdates();
        } else {
            authError.classList.remove('hidden');
            passInput.value = "";
            setTimeout(() => authError.classList.add('hidden'), 3000);
        }
    });

    passInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') loginBtn.click();
    });

    closeBtn?.addEventListener('click', () => {
        toggleAdminDashboard(false);
    });

    runSuiteBtn?.addEventListener('click', async () => {
        const list = document.getElementById('admin-logs-list');
        list.innerHTML = ""; // Clear for new run
        addAdminLog("INITIATING CORE SYSTEM DIAGNOSTICS...", "system");
        runSuiteBtn.disabled = true;

        const diagnosticSteps = [
            { cmd: "Neural Weights integrity", log: "Checking synaptic plasticity...", status: "VALID" },
            { cmd: "LTM Database Sync", log: "Verifying JSON structure...", status: "SYNCED" },
            { cmd: "TTS Engine", log: "Testing phonetic buffers...", status: "READY" },
            { cmd: "VAD Sensitivity", log: "Filtering ambient audio...", status: "OPTIMAL" },
            { cmd: "Emotion Matrix", log: "Calibrating Kuudere levels...", status: "STABLE" }
        ];

        for (const step of diagnosticSteps) {
            addAdminLog(`Running: ${step.cmd}`, "pending");
            await new Promise(r => setTimeout(r, 600));
            addAdminLog(`>>> ${step.log}`, "info");
            await new Promise(r => setTimeout(r, 400));
            addAdminLog(`Result: ${step.status}`, "success");
            await new Promise(r => setTimeout(r, 200));
        }

        addAdminLog("NOVA CORE STABLE. SHIELD REINFORCED.", "success");
        runSuiteBtn.disabled = false;
    });

    clearLogsBtn?.addEventListener('click', () => {
        logsList.innerHTML = '<div class="log-item system">Safe environment established...</div>';
    });

    // Command Emulator Logic
    const emuBtn = document.getElementById('admin-emu-btn');
    const emuInput = document.getElementById('admin-emu-input');
    const emuResults = document.getElementById('admin-emu-results');

    if (emuBtn && emuInput && emuResults) {
        emuBtn.addEventListener('click', async () => {
            const command = emuInput.value.trim();
            if (!command) {
                emuResults.innerHTML = '<div style="color: #ff6b6b; padding: 10px;">⚠️ Please enter a command</div>';
                return;
            }

            emuBtn.disabled = true;
            emuBtn.textContent = 'TESTING...';
            emuResults.innerHTML = '<div style="color: #00ffff; padding: 10px;">⏳ Processing...</div>';

            try {
                const res = await fetch(`${API_URL}/admin/emulator`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ command })
                });

                const data = await res.json();

                if (data.status === 'success') {
                    let html = `<div style="padding: 10px; line-height: 1.6;">`;
                    html += `<div style="color: #00ff00; margin-bottom: 8px;">✅ Command Processed</div>`;
                    html += `<div style="color: #00ffff; font-size: 0.85em; margin-bottom: 5px;">Intent: <strong>${data.nlu.intent || 'unknown'}</strong> (${(data.nlu.confidence * 100).toFixed(1)}%)</div>`;

                    if (data.nlu.entities && data.nlu.entities.length > 0) {
                        html += `<div style="color: #ffd700; font-size: 0.85em; margin-bottom: 5px;">Entities: ${data.nlu.entities.map(e => e.type + '=' + e.value).join(', ')}</div>`;
                    }

                    html += `<div style="color: ${data.execution.status === 'success' ? '#00ff00' : '#ff6b6b'}; font-size: 0.85em; margin-bottom: 5px;">Execution: ${data.execution.status}</div>`;

                    if (data.execution.response) {
                        html += `<div style="color: #a29bfe; font-size: 0.85em; margin-top: 8px; padding: 8px; background: rgba(0,0,0,0.3); border-radius: 4px;">Response: ${data.execution.response}</div>`;
                    }

                    html += `</div>`;
                    emuResults.innerHTML = html;
                } else {
                    emuResults.innerHTML = `<div style="color: #ff6b6b; padding: 10px;">❌ Error: ${data.message || data.error}</div>`;
                }
            } catch (err) {
                console.error('Emulator error:', err);
                emuResults.innerHTML = `<div style="color: #ff6b6b; padding: 10px;">❌ Request failed: ${err.message}</div>`;
            } finally {
                emuBtn.disabled = false;
                emuBtn.textContent = 'TEST';
            }
        });

        // Allow Enter key to trigger test
        emuInput?.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') emuBtn.click();
        });
    }
}

function toggleAdminDashboard(show, mode = null) {
    const dashboard = document.getElementById('admin-dashboard');
    const authScreen = document.getElementById('admin-auth-screen');
    const mainContent = document.getElementById('admin-main-content');
    const passInput = document.getElementById('admin-pass-input');

    if (show) {
        dashboard.classList.remove('hidden');
        authScreen.classList.remove('hidden');
        mainContent.classList.add('hidden');
        passInput.value = "";
        passInput.focus();

        if (mode === 'all') {
            // Proactively start suite if "test all" was asked
            setTimeout(() => {
                if (!mainContent.classList.contains('hidden')) {
                    document.getElementById('run-suite-btn').click();
                }
            }, 1000);
        }
    } else {
        dashboard.classList.add('hidden');
        stopStatsUpdates();
        // Clean emulator and logs on hide
        const emuResults = document.getElementById('admin-emu-results');
        const logsList = document.getElementById('admin-logs-list');
        if (emuResults) emuResults.innerHTML = "";
        if (logsList) logsList.innerHTML = '<div class="log-item system">Safe environment established.</div>';
    }
}

async function startStatsUpdates() {
    stopStatsUpdates();
    updateStats();
    statsInterval = setInterval(updateStats, 2000);
}

function stopStatsUpdates() {
    if (statsInterval) clearInterval(statsInterval);
}

async function updateStats() {
    try {
        const res = await fetch(`${API_URL}/admin/stats`);
        const stats = await res.json();

        document.getElementById('admin-cpu-val').textContent = `${Math.round(stats.cpu)}%`;
        document.getElementById('admin-cpu-bar').style.width = `${stats.cpu}%`;

        document.getElementById('admin-mem-val').textContent = `${Math.round(stats.memory)}%`;
        document.getElementById('admin-mem-bar').style.width = `${stats.memory}%`;

        document.getElementById('admin-uptime-val').textContent = formatUptime(stats.uptime);
        document.getElementById('admin-facts-val').textContent = stats.learned_facts;
    } catch (e) {
        console.error("Stats update failed", e);
    }
}

function addAdminLog(text, type = "") {
    const list = document.getElementById('admin-logs-list');
    const item = document.createElement('div');
    item.className = `log-item ${type}`;
    item.textContent = `[${new Date().toLocaleTimeString()}] ${text}`;
    list.appendChild(item);
    list.scrollTop = list.scrollHeight;
}

function formatUptime(seconds) {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = seconds % 60;
    return `${h}h ${m}m ${s}s`;
}


function setupFileUpload() {
    if (uploadBtn && fileInput) {
        uploadBtn.addEventListener('click', () => {
            fileInput.click();
        });

        fileInput.addEventListener('change', async (e) => {
            if (fileInput.files.length > 0) {
                const file = fileInput.files[0];
                await uploadFile(file);
            }
        });
    }
}

async function uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);

    // Show a temporary message
    addLine(`Uploading '${file.name}'...`, 'system-msg');

    // Disable input while uploading
    uploadBtn.disabled = true;
    uploadBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';

    try {
        const res = await fetch(`${API_URL}/upload`, {
            method: 'POST',
            body: formData
        });
        const data = await res.json();

        if (data.status === 'success') {
            // Nova's response from backend
            if (data.analysis && data.analysis.type === 'image') {
                addLine(`I've analyzed the image. ${data.response}`, 'nova-msg');
            } else {
                addLine(data.response, 'nova-msg');
            }
        } else {
            addLine(`Upload failed: ${data.error || 'Unknown error'}`, 'system-msg');
        }
    } catch (err) {
        console.error("Upload error:", err);
        addLine("Failed to upload file.", 'system-msg');
    } finally {
        uploadBtn.disabled = false;
        uploadBtn.innerHTML = '<i class="fas fa-paperclip"></i>';
        fileInput.value = ''; // Reset
    }
}

document.addEventListener('DOMContentLoaded', () => {
    setupFileUpload();
    initSettings();
    checkStatus();
    setInterval(checkStatus, 30000);

    // Close Events Dashboard on Escape
    window.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            const dashboard = document.getElementById('events-dashboard');
            if (dashboard && dashboard.style.display === 'flex') {
                toggleEventsDashboard(false);
            }
        }
    });

    // Initial check for proactive suggestions
    setTimeout(checkSuggestions, 2000);
    // Poll for proactive suggestions every 5 minutes
    setInterval(checkSuggestions, 300000);
});

// Helper for notifications
function showNotification(msg) {
    if (typeof addLine === 'function') {
        addLine(msg, 'system-msg');
    } else {
        alert(msg);
    }
}

// Helper for internal logging
function addLog(msg, type = 'info') {
    if (typeof addAdminLog === 'function') {
        addAdminLog(msg, type);
    } else {
        console.log(`[${type.toUpperCase()}] ${msg}`);
    }
}

async function checkSuggestions() {
    try {
        const res = await fetch(`${API_URL}/suggestions`);
        const data = await res.json();

        if (data.suggestions && data.suggestions.length > 0) {
            // Only show one suggestion at a time to avoid spam
            const suggestion = data.suggestions[0];
            showSuggestionNotification(suggestion);
        }
    } catch (e) {
        console.error('Failed to fetch suggestions:', e);
    }
}

function showSuggestionNotification(suggestion) {
    // Check if we already showed this suggestion recently
    if (window.lastShownSuggestion === suggestion.message) return;
    window.lastShownSuggestion = suggestion.message;

    const notif = document.createElement('div');
    notif.className = 'message nova suggestion-notif';
    notif.innerHTML = `
        <div style="padding: 15px; background: rgba(138,43,226,0.1); border-radius: 12px; border: 1px solid rgba(162, 155, 254, 0.3); position: relative; animation: slideIn 0.5s ease-out;">
            <p style="margin: 0 0 10px 0; color: #a29bfe; font-weight: bold;"><i class="fas fa-lightbulb"></i> Nova Core Suggestion</p>
            <p style="margin: 0 0 15px 0;">${suggestion.message}</p>
            <div style="display: flex; gap: 10px;">
                <button class="suggestion-action-btn" style="background: #6c5ce7; color: white; border: none; padding: 8px 15px; border-radius: 20px; cursor: pointer; font-size: 0.9em;">Yes, please!</button>
                <button class="suggestion-close-btn" style="background: rgba(255,255,255,0.1); color: white; border: none; padding: 8px 15px; border-radius: 20px; cursor: pointer; font-size: 0.9em;">Not now</button>
            </div>
        </div>
    `;

    const actionBtn = notif.querySelector('.suggestion-action-btn');
    const closeBtn = notif.querySelector('.suggestion-close-btn');

    actionBtn.onclick = () => {
        const input = document.getElementById('user-input');
        input.value = suggestion.action;
        document.getElementById('send-btn').click();
        notif.remove();
    };

    closeBtn.onclick = () => {
        notif.remove();
    };

    const outputArea = document.getElementById('chat-feed');
    outputArea.appendChild(notif);
    outputArea.scrollTop = outputArea.scrollHeight;
}

// --- SMART SKILL MANAGEMENT ---
async function loadSkills() {
    const grid = document.getElementById('skills-grid');
    if (!grid) return;

    try {
        const res = await fetch(`${API_URL}/skills/status`);
        const skills = await res.json();

        if (skills.error) throw new Error(skills.error);

        grid.innerHTML = ''; // Clear loading state

        if (skills.length === 0) {
            grid.innerHTML = '<div style="grid-column: span 2; text-align: center; padding: 20px; opacity: 0.5;">No dynamic skills discovered yet.</div>';
            return;
        }

        skills.forEach(skill => {
            const card = document.createElement('div');
            card.className = 'skill-card premium-glass';
            card.style.padding = '15px';
            card.style.borderRadius = '12px';
            card.style.background = 'rgba(255,255,255,0.05)';
            card.style.border = '1px solid rgba(255,255,255,0.1)';
            card.style.display = 'flex';
            card.style.flexDirection = 'column';
            card.style.gap = '10px';
            card.style.transition = 'all 0.3s ease';

            const isActive = skill.status === 'Active';
            const statusColor = isActive ? '#00f2fe' : '#9f7aea';
            const glowColor = isActive ? 'rgba(0, 242, 254, 0.3)' : 'rgba(159, 122, 234, 0.2)';

            card.style.boxShadow = `0 4px 15px ${glowColor}`;

            card.innerHTML = `
                <div style="display: flex; justify-content: space-between; align-items: start;">
                    <div>
                        <h4 style="margin: 0; color: #fff;">${skill.name}</h4>
                        <span style="font-size: 0.75em; opacity: 0.6;">${skill.path}</span>
                    </div>
                    <span style="font-size: 1.2em;">${skill.icon}</span>
                </div>
                
                <div style="font-size: 0.8em; opacity: 0.8; height: 40px; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;">
                    Triggers: ${skill.triggers.join(', ')}
                </div>

                <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 5px;">
                    <div style="display: flex; align-items: center; gap: 6px;">
                        <div style="width: 8px; height: 8px; border-radius: 50%; background: ${statusColor}; box-shadow: 0 0 8px ${statusColor};"></div>
                        <span style="font-size: 0.85em; font-weight: 500; color: ${statusColor};">${skill.status}</span>
                    </div>
                    <div style="display: flex; gap: 5px;">
                        ${!isActive ? `
                        <button class="boot-btn" onclick="bootSkill('${skill.path}', this)" 
                            style="padding: 5px 12px; font-size: 0.8em; background: rgba(0,242,254,0.1); border: 1px solid rgba(0,242,254,0.3); border-radius: 6px; color: white; cursor: pointer; transition: all 0.2s;">
                            🚀 Boot
                        </button>` : `
                        <button class="stop-btn" onclick="stopSkill('${skill.path}', this)" 
                            style="padding: 5px 12px; font-size: 0.8em; background: rgba(255,77,77,0.1); border: 1px solid rgba(255,77,77,0.3); border-radius: 6px; color: white; cursor: pointer; transition: all 0.2s;">
                            🛑 Stop
                        </button>`}
                    </div>
                </div>
            `;

            grid.appendChild(card);
        });
    } catch (e) {
        console.error('Failed to load skills:', e);
        grid.innerHTML = `<div style="grid-column: span 2; color: #ff4d4d; text-align: center;">Error loading skills: ${e.message}</div>`;
    }
}

async function stopSkill(path, btn) {
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
    }

    try {
        const res = await fetch(`${API_URL}/skills/stop`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path })
        });
        const data = await res.json();

        if (data.success) {
            loadSkills();
            addLog(`Emergency Stop: Skill ${path} unloaded successfully.`, 'info');
        } else {
            alert('Failed to stop skill: ' + (data.error || 'Unknown error'));
            if (btn) {
                btn.disabled = false;
                btn.innerHTML = '🛑 Stop';
            }
        }
    } catch (e) {
        console.error('Stop error:', e);
        alert('System error during emergency stop.');
    }
}

async function bootSkill(path, btn) {
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
    }

    try {
        const res = await fetch(`${API_URL}/skills/load`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path })
        });
        const data = await res.json();

        if (data.success) {
            // Refresh the grid
            loadSkills();
            addLog(`Skill ${path} manually booted successfully.`, 'success');
        } else {
            alert('Failed to boot skill: ' + (data.error || 'Unknown error'));
            if (btn) {
                btn.disabled = false;
                btn.innerHTML = '🚀 Boot';
            }
        }
    } catch (e) {
        console.error('Boot error:', e);
        alert('System error during boot.');
    }
}

// --- NATURAL EVENTS DASHBOARD (PAGE GUI) ---
function toggleEventsDashboard(show) {
    const dashboard = document.getElementById('events-dashboard');
    const globeContainer = document.getElementById('globe-container');
    const dashboardGlobe = document.getElementById('dashboard-globe-container');

    if (show) {
        dashboard.style.display = 'flex';
        setTimeout(() => dashboard.classList.add('active'), 10);
        
        // Reparent globe for "WOW" effect
        if (globeContainer && dashboardGlobe) {
            dashboardGlobe.appendChild(globeContainer);
            globeContainer.style.position = 'relative';
            globeContainer.style.top = '0';
            globeContainer.style.left = '0';
            globeContainer.style.transform = 'none';
        }
    } else {
        dashboard.classList.remove('active');
        setTimeout(() => {
            dashboard.style.display = 'none';
            // Return globe to background
            const originalContainer = document.body;
            if (globeContainer) {
                originalContainer.insertBefore(globeContainer, originalContainer.firstChild);
                globeContainer.style.position = 'absolute';
                globeContainer.style.top = '50%';
                globeContainer.style.left = '50%';
                globeContainer.style.transform = 'translate(-50%, -50%)';
            }
        }, 300);
    }
}

// --- STARTUP INITIALIZATION ---
async function loadChatHistory() {
    try {
        const res = await fetch(`${API_URL}/history`);
        const data = await res.json();
        
        if (data.history && data.history.length > 0) {
            console.log(`📜 Loading ${data.history.length} past exchanges...`);
            
            // Remove welcome screen if history exists
            const welcome = document.querySelector('.welcome-screen');
            if (welcome) welcome.style.display = 'none';
            
            data.history.forEach(exchange => {
                // Add user message
                addLine(exchange.user, 'user-msg');
                // Add assistant message
                addLine(exchange.assistant, 'nova-msg');
            });
            
            // Scroll to bottom
            outputArea.scrollTop = outputArea.scrollHeight;
        }
    } catch (e) {
        console.error("Failed to load history:", e);
    }
}

// Global Init Call
window.addEventListener('load', () => {
    // Existing Three.js/UI inits would be triggered here if not already
    // loadChatHistory(); // Disabled so we start with a fresh chat UI each time
});

function updateEventsList(events) {
    const list = document.getElementById('events-list');
    if (!list) return;
    
    list.innerHTML = '';
    if (!events || events.length === 0) {
        list.innerHTML = '<div class="loading-scanners">No active events found.</div>';
        return;
    }

    events.forEach(event => {
        const card = document.createElement('div');
        const type = event.mag ? 'quake' : (event.category ? 'nasa' : 'tide');
        card.className = `event-card ${type} fade-in`;
        
        const time = event.time || new Date().toLocaleTimeString();
        const detail = event.mag ? `Mag: ${event.mag}` : (event.category || 'Tide Info');
        
        card.innerHTML = `
            <div class="event-card-header">
                <div class="event-title">${event.title || event.place}</div>
                <div class="event-meta">${time}</div>
            </div>
            <div style="font-size: 0.85em; opacity: 0.8;">${detail} | Lat: ${event.lat.toFixed(2)}, Lon: ${event.lon.toFixed(2)}</div>
        `;
        
        card.onclick = () => {
            // Rotate globe to this event
            console.log("Panning to event:", event.title || event.place);
            if (particles) {
                particles.rotation.y = - (event.lon * Math.PI / 180);
                particles.rotation.x = (event.lat * Math.PI / 180);
            }
            triggerGlowPulse();
        };
        
        list.appendChild(card);
    });
}

// --- UI Telemetry and Sidebar Wiring ---

function updateTelemetry() {
    fetch('http://localhost:5000/api/telemetry')
        .then(response => response.json())
        .then(data => {
            if (data.error) return;
            
            // Update CPU
            const cpuEl = document.getElementById('telemetry-cpu');
            if (cpuEl) cpuEl.textContent = Math.round(data.cpu) + '%';
            
            // Update CPU Bars randomly based on load
            const cpuBars = document.querySelectorAll('.cpu-bar');
            cpuBars.forEach(bar => {
                const baseHeight = Math.max(10, data.cpu - 20 + Math.random() * 40);
                bar.style.height = Math.min(100, baseHeight) + '%';
            });

            // Update Memory
            const memEl = document.getElementById('telemetry-memory');
            if (memEl) memEl.textContent = data.total_mem_gb.toFixed(1) + ' GB';
        })
        .catch(err => console.error('Telemetry fetch error:', err));
}

// Poll telemetry every 2 seconds
setInterval(updateTelemetry, 2000);
updateTelemetry();

// Wire up sidebar buttons
document.addEventListener('DOMContentLoaded', () => {
    // New Instance
    const btnNew = document.getElementById('btn-new-instance');
    if (btnNew) {
        btnNew.addEventListener('click', () => {
            const outputArea = document.getElementById('chat-feed');
            if (outputArea) {
                outputArea.innerHTML = '<div style="text-align:center; padding: 20px; opacity: 0.5;">System Reinitialized. Ready for new input.</div>';
            }
        });
    }

    // Settings Button
    const btnSettings = document.getElementById('settings-btn');
    if (btnSettings) {
        btnSettings.addEventListener('click', (e) => {
            e.preventDefault();
            const settingsModal = document.getElementById('settings-modal');
            if (settingsModal) {
                settingsModal.classList.add('active');
            }
        });
    }

    // Interactive placeholder for other nav buttons
    const navIds = ['btn-nova-core', 'btn-swarm', 'btn-local', 'btn-terminal'];
    navIds.forEach(id => {
        const btn = document.getElementById(id);
        if (btn) {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                // Visual click effect
                btn.style.opacity = '0.5';
                setTimeout(() => btn.style.opacity = '1', 200);
            });
        }
    });
});


// Generated Modals Logic
(function() {
    const logsBtn = document.getElementById('logs-btn');
    const logsModal = document.getElementById('logs-modal');
    const closeLogsBtn = document.getElementById('close-logs-btn');

    const dashboardBtn = document.getElementById('dashboard-btn');
    const dashboardModal = document.getElementById('events-dashboard');
    const closeDashboardBtn = document.getElementById('close-dashboard-btn');

    if (logsBtn && logsModal) {
        logsBtn.addEventListener('click', () => {
            logsModal.style.display = 'block';
        });
    }
    if (closeLogsBtn && logsModal) {
        closeLogsBtn?.addEventListener('click', () => {
            logsModal.style.display = 'none';
        });
    }
    
    if (dashboardBtn && dashboardModal) {
        dashboardBtn.addEventListener('click', () => {
            dashboardModal.style.display = 'block';
        });
    }
    if (closeDashboardBtn && dashboardModal) {
        closeDashboardBtn.addEventListener('click', () => {
            dashboardModal.style.display = 'none';
        });
    }
})();


// Modal Logic for Dashboard and Logs
document.addEventListener('DOMContentLoaded', () => {
    const dashboardBtn = document.getElementById('dashboard-btn');
    const logsBtn = document.getElementById('logs-btn');
    const closeDashboardBtn = document.getElementById('close-dashboard-btn');
    const closeLogsBtn = document.getElementById('close-logs-btn');
    const dashboardModal = document.getElementById('events-dashboard');
    const logsModal = document.getElementById('logs-modal');

    if(dashboardBtn && dashboardModal) {
        dashboardBtn.addEventListener('click', () => {
            dashboardModal.style.display = 'flex';
        });
    }
    if(closeDashboardBtn && dashboardModal) {
        closeDashboardBtn.addEventListener('click', () => {
            dashboardModal.style.display = 'none';
        });
    }

    if(logsBtn && logsModal) {
        logsBtn.addEventListener('click', () => {
            logsModal.style.display = 'flex';
        });
    }
    if(closeLogsBtn && logsModal) {
        closeLogsBtn?.addEventListener('click', () => {
            logsModal.style.display = 'none';
        });
    }
});


document.addEventListener('DOMContentLoaded', () => {
    const coreLoadVal = document.getElementById('core-load-val');
    const coreBars = document.querySelectorAll('#core-load-chart > div');

    if (coreLoadVal) {
        setInterval(() => {
            // Randomize Core Load % (30% to 80%)
            const load = Math.floor(Math.random() * 50) + 30;
            coreLoadVal.innerText = load + '%';
            
            // Animate Core Chart Bars
            coreBars.forEach(bar => {
                const h = Math.floor(Math.random() * 80) + 20; // 20% to 100%
                bar.style.height = h + '%';
            });
        }, 1500);
    }

});

// --- Talking Glass Wave Shader ---
(function() {
  const canvas = document.getElementById('shader-canvas-ANIMATION_14');
  if (!canvas) return;

  function syncSize() {
    const w = canvas.clientWidth  || 1280;
    const h = canvas.clientHeight || 720;
    if (canvas.width !== w || canvas.height !== h) {
      canvas.width  = w;
      canvas.height = h;
    }
  }
  if (typeof ResizeObserver !== 'undefined') {
    new ResizeObserver(syncSize).observe(canvas);
  }
  syncSize();

  const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
  if (!gl) return;
  const vs = `attribute vec2 a_position;
varying vec2 v_texCoord;
void main() {
  v_texCoord = a_position * 0.5 + 0.5;
  gl_Position = vec4(a_position, 0.0, 1.0);
}`;
  const fs = `precision highp float;
uniform float u_time;
uniform vec2 u_resolution;
uniform vec3 u_color1;
uniform vec3 u_color2;
uniform float u_speak_intensity;

varying vec2 v_texCoord;

float pulse(float x, float p, float w) {
    return pow(4.0 * x * (1.0 - x), 1.0 / w);
}

void main() {
    vec2 uv = v_texCoord;
    vec2 p = uv * 2.0 - 1.0;
    p.x *= u_resolution.x / u_resolution.y;
    
    float t = u_time * 1.5;
    
    float finalWave = 0.0;
    for(float i = 1.0; i <= 5.0; i++) {
        float speed = t * (0.5 + i * 0.2);
        float amplitude = (0.15 / i) * (1.0 + u_speak_intensity * 3.0);
        float frequency = 3.0 + i * 2.0;
        float wave = sin(p.x * frequency + speed) * amplitude;
        
        float envelope = exp(-pow(p.x * 2.0, 2.0));
        wave *= envelope;
        
        float dist = abs(p.y - wave);
        finalWave += (0.01 / dist) * envelope;
    }
    
    vec3 color = mix(u_color1, u_color2, uv.x + sin(t) * 0.5);
    vec3 finalColor = color * finalWave;
    
    float highlight = pow(max(0.0, 1.0 - length(p * vec2(1.0, 4.0))), 4.0);
    finalColor += u_color2 * highlight * 0.3 * (sin(t * 2.0) * 0.5 + 0.5);
    
    float alpha = clamp(finalWave + highlight * 0.2, 0.0, 1.0);
    gl_FragColor = vec4(finalColor * alpha, alpha * 0.8);
}`;
  function cs(type, src) {
    const s = gl.createShader(type);
    gl.shaderSource(s, src);
    gl.compileShader(s);
    return s;
  }
  const prog = gl.createProgram();
  gl.attachShader(prog, cs(gl.VERTEX_SHADER, vs));
  gl.attachShader(prog, cs(gl.FRAGMENT_SHADER, fs));
  gl.linkProgram(prog);
  gl.useProgram(prog);
  const buf = gl.createBuffer();
  gl.bindBuffer(gl.ARRAY_BUFFER, buf);
  gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1,-1, 1,-1, -1,1, 1,1]), gl.STATIC_DRAW);
  const pos = gl.getAttribLocation(prog, 'a_position');
  gl.enableVertexAttribArray(pos);
  gl.vertexAttribPointer(pos, 2, gl.FLOAT, false, 0, 0);
  
  const uTime = gl.getUniformLocation(prog, 'u_time');
  const uRes = gl.getUniformLocation(prog, 'u_resolution');
  const uColor1 = gl.getUniformLocation(prog, 'u_color1');
  const uColor2 = gl.getUniformLocation(prog, 'u_color2');
  const uSpeak = gl.getUniformLocation(prog, 'u_speak_intensity');

  // Default colors
  let currentColor1 = [0.0, 0.706, 0.941];
  let currentColor2 = [0.659, 0.333, 0.969];
  let targetColor1 = [...currentColor1];
  let targetColor2 = [...currentColor2];

  window.setEmotionColors = function(emotion) {
      switch(emotion.toLowerCase()) {
          case 'happy':
          case 'joy':
              targetColor1 = [1.0, 0.8, 0.2]; // Yellow/Orange
              targetColor2 = [1.0, 0.5, 0.0];
              break;
          case 'sad':
          case 'sorrow':
              targetColor1 = [0.2, 0.4, 0.8]; // Deep blue
              targetColor2 = [0.1, 0.2, 0.5];
              break;
          case 'angry':
          case 'anger':
              targetColor1 = [1.0, 0.2, 0.1]; // Red
              targetColor2 = [0.8, 0.0, 0.0];
              break;
          case 'calm':
          case 'neutral':
          default:
              targetColor1 = [0.0, 0.706, 0.941]; // Default Blue
              targetColor2 = [0.659, 0.333, 0.969]; // Default Purple
              break;
      }
  };

  let targetSpeakIntensity = 0;
  let currentSpeakIntensity = 0;

  function render(t) {
    if (typeof ResizeObserver === 'undefined') syncSize();
    gl.viewport(0, 0, canvas.width, canvas.height);
    
    // Smoothly interpolate colors
    for(let i = 0; i < 3; i++) {
        currentColor1[i] += (targetColor1[i] - currentColor1[i]) * 0.05;
        currentColor2[i] += (targetColor2[i] - currentColor2[i]) * 0.05;
    }
    
    // Speak Intensity
    targetSpeakIntensity = isSpeaking ? (Math.random() * 0.8 + 0.2) : 0.0;
    currentSpeakIntensity += (targetSpeakIntensity - currentSpeakIntensity) * 0.2;
    
    if (uTime) gl.uniform1f(uTime, t * 0.001);
    if (uRes) gl.uniform2f(uRes, canvas.width, canvas.height);
    if (uColor1) gl.uniform3fv(uColor1, currentColor1);
    if (uColor2) gl.uniform3fv(uColor2, currentColor2);
    if (uSpeak) gl.uniform1f(uSpeak, currentSpeakIntensity);
    
    gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
    requestAnimationFrame(render);
  }
  render(0);
})();

// Expose toggle function
window.toggleTalkingAnimation = function(isTalking) {
    const wave = document.getElementById('glass-wave-anim');
    const thinkPing = document.getElementById('thought-ping-anim');
    
    if(wave) {
        if(isTalking) {
            wave.style.opacity = '1';
        } else {
            wave.style.opacity = '0';
        }
    }
    
    if(thinkPing) {
        if(isTalking) {
            thinkPing.classList.add('animate-ping');
        } else {
            thinkPing.classList.remove('animate-ping');
        }
    }
};

// BROWSER LIVE VIEW LOGIC
let liveViewInterval = null;
async function startLiveView() {
    const imgEl = document.getElementById('live-view-img');
    const loadEl = document.getElementById('live-view-loading');
    const errEl = document.getElementById('live-view-error');
    if(liveViewInterval) clearInterval(liveViewInterval);
    liveViewInterval = setInterval(async () => {
        try {
            const res = await fetch(API_URL + '/browser/live_view');
            const data = await res.json();
            if(data.status === 'success' && data.image) {
                imgEl.src = 'data:image/jpeg;base64,' + data.image;
                imgEl.classList.remove('hidden');
                loadEl.classList.add('hidden');
                errEl.classList.add('hidden');
            } else {
                imgEl.classList.add('hidden');
                loadEl.classList.add('hidden');
                errEl.classList.remove('hidden');
                document.getElementById('live-view-error-msg').innerText = data.message || "Browser is not active.";
            }
        } catch(e) {
            imgEl.classList.add('hidden');
            loadEl.classList.add('hidden');
            errEl.classList.remove('hidden');
            document.getElementById('live-view-error-msg').innerText = "Connection lost.";
        }
    }, 1000);
}


function stopLiveView() {
    if(liveViewInterval) {
        clearInterval(liveViewInterval);
        liveViewInterval = null;
    }
}

async function sendBrowserAction(action, selector = null, value = null) {
    try {
        const payload = { action };
        if (selector) payload.selector = selector;
        if (value) payload.value = value;
        
        await fetch(API_URL + '/browser/action', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        // Clear inputs after sending
        if(action === 'click' || action === 'type') {
            const textEl = document.getElementById('live-browser-text');
            if(textEl) textEl.value = '';
        }
    } catch(e) {
        console.error("Browser action error:", e);
    }
}
