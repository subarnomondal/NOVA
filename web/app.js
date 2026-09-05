// CLIO Minimalist UI Application Logic

document.addEventListener('DOMContentLoaded', () => {
    
    // --- State & DOM Elements ---
    let currentMode = 'chat';
    
    const navButtons = document.querySelectorAll('.nav-btn[data-mode]');
    const modeViews = document.querySelectorAll('.mode-view');
    const settingsBtn = document.getElementById('settings-btn');
    const settingsModal = document.getElementById('settings-modal');
    const closeSettingsBtn = document.getElementById('close-settings');
    
    // Live Mode Background Toggle
    const liveBgBtn = document.getElementById('live-bg-btn');
    const liveSection = document.getElementById('mode-live');
    const backgrounds = ['bg-pastel-bedroom', 'bg-magical-library', 'bg-cozy-gaming', 'bg-fantasy-sky'];
    let currentBgIndex = 0;
    
    if (liveBgBtn) {
        liveBgBtn.addEventListener('click', () => {
            liveSection.classList.remove(backgrounds[currentBgIndex]);
            currentBgIndex = (currentBgIndex + 1) % backgrounds.length;
            const newBg = backgrounds[currentBgIndex];
            liveSection.classList.add(newBg);
            if (window.setVTuberLighting) window.setVTuberLighting(newBg);
        });
    }
    
    // Vibe Mode Toggle
    const liveVibeBtn = document.getElementById('live-vibe-btn');
    window.isVibing = false;
    
    if (liveVibeBtn) {
        liveVibeBtn.addEventListener('click', () => {
            window.isVibing = !window.isVibing;
            if (window.isVibing) {
                liveVibeBtn.classList.add('bg-white/20', 'text-white', 'border-white/50');
                liveVibeBtn.classList.remove('bg-white/5', 'border-white/10');
            } else {
                liveVibeBtn.classList.remove('bg-white/20', 'text-white', 'border-white/50');
                liveVibeBtn.classList.add('bg-white/5', 'border-white/10');
                
                // Reset spine/head if stopped vibing
                if (currentVrm && currentVrm.humanoid) {
                    const spine = currentVrm.humanoid.getNormalizedBoneNode('spine');
                    const head = currentVrm.humanoid.getNormalizedBoneNode('head');
                    if (spine) spine.rotation.set(0, 0, 0);
                    if (head) head.rotation.set(0, 0, 0);
                }
            }
        });
    }

    // Random Animation Toggle
    const liveAnimBtn = document.getElementById('live-anim-btn');
    const allEmotions = ['happy', 'sad', 'angry', 'thinking', 'dance', 'wave', 'shy', 'proud', 'yawn', 'excited', 'scared', 'confused', 'sleep'];
    
    if (liveAnimBtn) {
        liveAnimBtn.addEventListener('click', () => {
            const randomEmotion = allEmotions[Math.floor(Math.random() * allEmotions.length)];
            if (window.setVTuberEmotion) window.setVTuberEmotion(randomEmotion);
            if (window.setLiveEmotion) window.setLiveEmotion(randomEmotion);
            
            // Auto reset to neutral after 4 seconds
            setTimeout(() => {
                if (window.setVTuberEmotion) window.setVTuberEmotion('neutral');
                if (window.setLiveEmotion) window.setLiveEmotion('neutral');
            }, 4000);
        });
    }

    // Voice Chat Button
    const liveToggleBtn = document.getElementById('live-toggle-btn');
    const liveToggleText = document.getElementById('live-toggle-text');
    const liveTranscript = document.getElementById('live-transcript');
    
    let isLiveModeActive = false;
    
    if (liveToggleBtn) {
        liveToggleBtn.addEventListener('click', async () => {
            if (isLiveModeActive) {
                isLiveModeActive = false;
                window.isClioThinking = false;
                window.isClioSpeaking = false;
                if (liveToggleText) liveToggleText.innerText = 'Start Chat';
                liveToggleBtn.classList.remove('border-red-500', 'text-red-500');
                liveToggleBtn.querySelector('.material-symbols-outlined').classList.remove('animate-pulse', 'text-red-500');
                if (liveTranscript) liveTranscript.innerHTML = '<span class="italic opacity-50">Microphone Off</span>';
                return;
            }

            isLiveModeActive = true;
            if (liveToggleText) liveToggleText.innerText = 'Listening Continuously...';
            liveToggleBtn.classList.add('border-red-500', 'text-red-500');
            liveToggleBtn.querySelector('.material-symbols-outlined').classList.add('animate-pulse', 'text-red-500');
            
            while (isLiveModeActive) {
                if (window.isClioSpeaking || window.isClioThinking) {
                    await new Promise(r => setTimeout(r, 500));
                    continue;
                }

                if (liveTranscript) liveTranscript.innerHTML = '<span class="italic opacity-50 text-red-500">Listening...</span>';
                try {
                    const res = await fetch('/api/voice/trigger', { method: 'POST' });
                    if (!isLiveModeActive) break; // User stopped it during the request
                    
                    const data = await res.json();
                    if (data.status === 'success' && data.text) {
                        if (liveTranscript) liveTranscript.innerHTML = data.text;
                        chatInput.value = data.text;
                        sendMessage();
                    } else {
                        if (liveTranscript) liveTranscript.innerHTML = `<span class="italic opacity-50 text-red-300">Nothing heard...</span>`;
                        await new Promise(r => setTimeout(r, 500));
                    }
                } catch (e) {
                    console.error(e);
                    if (liveTranscript) liveTranscript.innerHTML = `<span class="italic opacity-50 text-red-500">Error. Retrying...</span>`;
                    await new Promise(r => setTimeout(r, 2000));
                }
            }
        });
    }
    
    const chatInput = document.getElementById('chat-input');
    const chatSend = document.getElementById('chat-send');
    const chatHistory = document.getElementById('chat-history');

    // --- Mode Switching ---
    navButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const mode = btn.getAttribute('data-mode');
            if (mode === currentMode) return;
            
            // Update Active Nav
            navButtons.forEach(b => {
                b.classList.remove('active');
                b.querySelector('span').classList.remove('text-primary');
                b.querySelector('span').classList.add('text-text-muted');
            });
            btn.classList.add('active');
            btn.querySelector('span').classList.add('text-primary');
            btn.querySelector('span').classList.remove('text-text-muted');

            // Update Views
            modeViews.forEach(view => {
                view.classList.add('hidden');
                view.classList.remove('active');
            });
            const targetView = document.getElementById(`mode-${mode}`);
            targetView.classList.remove('hidden');
            
            // Trigger reflow for animations
            void targetView.offsetWidth;
            targetView.classList.add('active');
            
            currentMode = mode;
            
            // Mode-specific initialization
            if (mode === 'live' && !vrmSceneInitialized) {
                initVTuber();
            }
            if (mode === 'live') {
                document.getElementById('mode-live').classList.add('live-active');
            } else {
                document.getElementById('mode-live').classList.remove('live-active');
            }
        });
    });

    // Default to Live Mode on startup
    const defaultLiveBtn = document.querySelector('.nav-btn[data-mode="live"]');
    if (defaultLiveBtn) {
        setTimeout(() => defaultLiveBtn.click(), 100);
    }

    // --- Settings Modal ---
    const settingsNavBtns = document.querySelectorAll('.settings-nav-btn');
    const settingsSections = document.querySelectorAll('.settings-section');

    settingsNavBtns.forEach((btn, index) => {
        btn.addEventListener('click', () => {
            // Update active state
            settingsNavBtns.forEach(b => {
                b.classList.remove('active', 'bg-primary/10', 'text-primary');
                b.classList.add('text-text-muted');
            });
            btn.classList.add('active', 'bg-primary/10', 'text-primary');
            btn.classList.remove('text-text-muted');

            // Scroll to section
            if (settingsSections[index]) {
                settingsSections[index].scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });
    });

    function openSettings() {
        settingsModal.classList.remove('hidden');
        // trigger reflow
        void settingsModal.offsetWidth;
        settingsModal.classList.remove('opacity-0');
        document.getElementById('settings-content').classList.remove('scale-95');
    }
    
    function closeSettings() {
        settingsModal.classList.add('opacity-0');
        document.getElementById('settings-content').classList.add('scale-95');
        setTimeout(() => {
            settingsModal.classList.add('hidden');
        }, 300);
    }
    
    settingsBtn.addEventListener('click', openSettings);
    closeSettingsBtn.addEventListener('click', closeSettings);
    settingsModal.addEventListener('click', (e) => {
        if (e.target === settingsModal) closeSettings();
    });

    // --- Background Selector ---
    const bgSelector = document.getElementById('bg-selector');
    bgSelector.addEventListener('change', (e) => {
        const liveMode = document.getElementById('mode-live');
        // Remove existing bg classes
        liveMode.classList.remove('bg-pastel-bedroom', 'bg-magical-library', 'bg-cozy-gaming', 'bg-fantasy-sky');
        // Add selected
        const newBg = e.target.value;
        liveMode.classList.add(newBg);
        if (window.setVTuberLighting) window.setVTuberLighting(newBg);
    });

    // --- Chat Logic ---
    window.appendMessage = function(sender, text) {
        // Remove empty state message if it exists
        const emptyState = chatHistory.querySelector('.opacity-50.select-none');
        if (emptyState) emptyState.remove();

        const msgDiv = document.createElement('div');
        msgDiv.className = `w-full flex animate-fade-in mb-4 ${sender === 'user' ? 'justify-end' : 'justify-start'}`;
        
        const bubble = document.createElement('div');
        bubble.className = sender === 'user'
            ? 'bg-[#8A2BE2] text-white ml-auto rounded-2xl rounded-tr-sm px-5 py-3 shadow-md max-w-[85%] text-sm'
            : 'bg-white/5 border border-white/10 text-white mr-auto rounded-2xl rounded-tl-sm px-5 py-3 shadow-md max-w-[85%] text-sm backdrop-blur-md';
        
        // Markdown parsing for bold, italics, links, and newlines
        let htmlText = text
            .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" class="text-blue-400 hover:underline cursor-pointer">$1</a>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/\n/g, '<br>');
        bubble.innerHTML = htmlText;
        
        msgDiv.appendChild(bubble);
        chatHistory.appendChild(msgDiv);
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }

    function showTyping() {
        const msgDiv = document.createElement('div');
        msgDiv.id = 'typing-indicator';
        msgDiv.className = 'w-full flex animate-fade-in mb-4 justify-start';
        
        const bubble = document.createElement('div');
        bubble.className = 'bg-white/5 border border-white/10 text-white mr-auto rounded-2xl rounded-tl-sm px-5 py-3 shadow-md max-w-[85%] backdrop-blur-md';
        
        bubble.innerHTML = `
            <div class="flex items-center gap-1.5 h-6 px-1">
                <span class="w-1.5 h-1.5 rounded-full bg-white opacity-60" style="animation: typingBounce 1.4s infinite ease-in-out both; animation-delay: -0.32s"></span>
                <span class="w-1.5 h-1.5 rounded-full bg-white opacity-60" style="animation: typingBounce 1.4s infinite ease-in-out both; animation-delay: -0.16s"></span>
                <span class="w-1.5 h-1.5 rounded-full bg-white opacity-60" style="animation: typingBounce 1.4s infinite ease-in-out both;"></span>
            </div>
        `;
        
        msgDiv.appendChild(bubble);
        chatHistory.appendChild(msgDiv);
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }

    function hideTyping() {
        const indicator = document.getElementById('typing-indicator');
        if (indicator) indicator.remove();
    }

    // --- Live Mode Emotion Reactivity ---
    function setLiveEmotion(emotion) {
        const liveSection = document.getElementById('mode-live');
        const themes = ['theme-neutral', 'theme-happy', 'theme-angry', 'theme-thinking', 'theme-sad'];
        
        // Remove all themes
        themes.forEach(t => liveSection.classList.remove(t));
        
        // Add new theme
        const themeMap = {
            'neutral': 'theme-neutral',
            'listening': 'theme-neutral',
            'thinking': 'theme-thinking',
            'happy': 'theme-happy',
            'angry': 'theme-angry',
            'sad': 'theme-sad',
            'error': 'theme-angry',
            'success': 'theme-happy'
        };
        const targetTheme = themeMap[emotion] || 'theme-neutral';
        liveSection.classList.add(targetTheme);
    }

    // Expose globally for testing/external scripts if needed
    window.setLiveEmotion = setLiveEmotion;

    async function sendMessage() {
        if (window.isClioThinking || window.isClioSpeaking) {
            console.log("Clio is currently busy. Please wait until she finishes.");
            return;
        }
        if (window.resetActivityTimer) window.resetActivityTimer();

        const text = chatInput.value.trim();
        if (!text) return;

        chatInput.value = '';
        appendMessage('user', text);
        showTyping();
        
        // VTuber starts "thinking"
        setLiveEmotion('thinking');
        setVTuberEmotion('thinking');
        window.isClioThinking = true;
        
        // Show "..." thought bubble immediately while waiting
        const bubble = document.getElementById('thought-bubble');
        const textBubble = document.getElementById('thought-bubble-text');
        if (bubble && textBubble) {
            textBubble.innerText = "...";
            bubble.style.opacity = '1';
            bubble.style.transform = 'scale(1)';
        }

        try {
            // Use the correct /api/command endpoint
            const res = await fetch('/api/command', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ command: text })
            });
            const data = await res.json();
            
            hideTyping();
            if (data.response) {
                appendMessage('clio', data.response);
                
                // Show thoughts in the thought bubble if they exist
                if (data.thoughts && data.thoughts.length > 0) {
                    const bubble = document.getElementById('thought-bubble');
                    const text = document.getElementById('thought-bubble-text');
                    if (bubble && text) {
                        // Display the most recent thought
                        const lastThought = data.thoughts[data.thoughts.length - 1];
                        text.innerText = lastThought.replace(/^•\s*/, ''); // clean bullet point
                        bubble.style.opacity = '1';
                        bubble.style.transform = 'scale(1)';
                        // Hide it after a few seconds
                        setTimeout(() => {
                            bubble.style.opacity = '0';
                            bubble.style.transform = 'scale(0.95)';
                        }, Math.max(4000, lastThought.length * 50));
                    }
                } else {
                    const bubble = document.getElementById('thought-bubble');
                    if (bubble) {
                        bubble.style.opacity = '0';
                        bubble.style.transform = 'scale(0.95)';
                    }
                }
                
                // Set emotion from backend response (or fallback to neutral)
                const backendEmotion = (data.emotion || 'neutral').toLowerCase();
                setLiveEmotion(backendEmotion);
                setVTuberEmotion(backendEmotion);
                
                let talkDuration = data.response.length * 50; // estimate
                
                if (data.audio_base64) {
                    const audio = new Audio('data:audio/mpeg;base64,' + data.audio_base64);
                    audio.crossOrigin = "anonymous";
                    window.isClioSpeaking = true;
                    
                    if (window.startAudioLipSync) {
                        window.startAudioLipSync(audio);
                    }
                    
                    audio.onended = () => { window.isClioSpeaking = false; };
                    audio.onerror = () => { window.isClioSpeaking = false; };
                    
                    audio.play().catch(e => {
                        console.error("Audio playback failed:", e);
                        window.isClioSpeaking = false;
                    });
                    
                    audio.onloadedmetadata = () => {
                        talkDuration = audio.duration * 1000;
                    };

                    audio.onplay = () => {
                        startTalking(talkDuration);
                        
                        setTimeout(() => {
                            setLiveEmotion('neutral');
                            setVTuberEmotion('neutral');
                        }, talkDuration + 500);
                    };
                } else {
                    startTalking(talkDuration);
                    
                    setTimeout(() => {
                        setLiveEmotion('neutral');
                        setVTuberEmotion('neutral');
                    }, talkDuration + 500);
                }
            }
        } catch (e) {
            console.error("Chat API Error:", e);
            hideTyping();
            appendMessage('clio', "Sorry, I couldn't connect to the server.");
            setLiveEmotion('error');
            setVTuberEmotion('angry');
            
            const bubble = document.getElementById('thought-bubble');
            if (bubble) {
                bubble.style.opacity = '0';
                bubble.style.transform = 'scale(0.95)';
            }
        } finally {
            window.isClioThinking = false;
        }
    }

    chatSend.addEventListener('click', sendMessage);
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });


});
