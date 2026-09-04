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
    const backgrounds = ['bg-pastel-bedroom', 'bg-pastel-gaming', 'bg-pastel-clouds', 'bg-pastel-cafe'];
    let currentBgIndex = 0;
    
    if (liveBgBtn) {
        liveBgBtn.addEventListener('click', () => {
            liveSection.classList.remove(backgrounds[currentBgIndex]);
            currentBgIndex = (currentBgIndex + 1) % backgrounds.length;
            liveSection.classList.add(backgrounds[currentBgIndex]);
        });
    }
    
    // Vibe Mode Toggle
    const liveVibeBtn = document.getElementById('live-vibe-btn');
    let isVibing = false;
    
    if (liveVibeBtn) {
        liveVibeBtn.addEventListener('click', () => {
            isVibing = !isVibing;
            if (isVibing) {
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
        liveMode.classList.remove('bg-void', 'bg-cyber', 'bg-space', 'bg-banana', 'bg-studio');
        // Add selected
        liveMode.classList.add(e.target.value);
    });

    // --- Chat Logic ---
    function appendMessage(sender, text) {
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
                    window.isClioSpeaking = true;
                    
                    audio.onended = () => { window.isClioSpeaking = false; };
                    audio.onerror = () => { window.isClioSpeaking = false; };
                    
                    audio.play().catch(e => {
                        console.error("Audio playback failed:", e);
                        window.isClioSpeaking = false;
                    });
                    
                    audio.onloadedmetadata = () => {
                        talkDuration = audio.duration * 1000;
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


    // --- VTuber Logic (Three.js + VRM Setup) ---
    let vrmSceneInitialized = false;
    let currentVrm = null;
    
    function setVTuberEmotion(emotion) {
        if (!currentVrm || !currentVrm.expressionManager) return;
        
        // Reset all expressions first
        const presetNames = ['happy', 'angry', 'sad', 'relaxed', 'surprised', 'neutral'];
        presetNames.forEach(preset => {
            currentVrm.expressionManager.setValue(preset, 0.0);
        });

        // Map abstract emotion names to VRM preset blendshapes
        const vrmMap = {
            'happy': 'happy',
            'joy': 'happy',
            'success': 'happy',
            'angry': 'angry',
            'error': 'angry',
            'sad': 'sad',
            'sorrow': 'sad',
            'thinking': 'relaxed', // using relaxed for thinking
            'neutral': 'neutral',
            'listening': 'neutral',
            'surprised': 'surprised',
            'dance': 'happy',
            'wave': 'happy',
            'shy': 'sad',
            'proud': 'happy',
            'yawn': 'relaxed'
        };

        const targetExpression = vrmMap[emotion];
        if (targetExpression) {
            currentVrm.expressionManager.setValue(targetExpression, 1.0);
            currentVrm.expressionManager.update();
        }
        
        // Trigger body language animation based on emotion
        animateEmotionBodyLanguage(emotion);
    }
    window.setVTuberEmotion = setVTuberEmotion;
    
    // --- VTuber Animation Logic ---
    const targetPose = {
        head: {x:0, y:0, z:0},
        neck: {x:0, y:0, z:0},
        spine: {x:0, y:0, z:0},
        leftArm: {x:0, y:0, z:1.1}, // A-pose default
        rightArm: {x:0, y:0, z:-1.1},
        leftLowerArm: {x:0, y:0, z:0},
        rightLowerArm: {x:0, y:0, z:0},
        leftHand: {x:0, y:0, z:0},
        rightHand: {x:0, y:0, z:0}
    };
    
    let lastActivityTime = Date.now();
    let isSleeping = false;
    let isYawning = false;

    function resetActivityTimer() {
        lastActivityTime = Date.now();
        if (isSleeping || isYawning) {
            isSleeping = false;
            isYawning = false;
            
            // 1/10 chance to wake up angry
            if (Math.random() < 0.1) {
                setVTuberEmotion('angry');
                // Automatically calm down after 4 seconds
                setTimeout(() => setVTuberEmotion('neutral'), 4000);
            } else {
                setVTuberEmotion('neutral');
            }
            
            if (currentVrm && currentVrm.expressionManager) {
                currentVrm.expressionManager.setValue('blink', 0.0);
            }
        }
    }
    window.resetActivityTimer = resetActivityTimer;
    function setHandPose(humanoid, side, pose) {
        const prefix = side === 'left' ? 'left' : 'right';
        const fingers = ['Thumb', 'Index', 'Middle', 'Ring', 'Little'];
        const joints = ['Proximal', 'Intermediate', 'Distal'];
        
        let curlAmount = 0; // relaxed
        if (pose === 'fist') curlAmount = 1.2;
        if (pose === 'open') curlAmount = -0.1;
        
        fingers.forEach(finger => {
            joints.forEach(joint => {
                const bone = humanoid.getNormalizedBoneNode(`${prefix}${finger}${joint}`);
                if (bone) {
                    // Thumbs curl on a different axis slightly, but z-axis generally curls fingers inward for VRM A-pose
                    if (finger === 'Thumb') {
                        bone.rotation.set(0, side === 'left' ? curlAmount : -curlAmount, 0);
                    } else {
                        bone.rotation.set(0, 0, side === 'left' ? curlAmount : -curlAmount);
                    }
                }
            });
        });
    }

    function animateEmotionBodyLanguage(emotion) {
        if (!currentVrm || !currentVrm.humanoid) return;
        
        const h = currentVrm.humanoid;
        
        // Reset base pose targets
        targetPose.head = {x: 0, y: 0, z: 0};
        targetPose.neck = {x: 0, y: 0, z: 0};
        targetPose.spine = {x: 0, y: 0, z: 0};
        targetPose.leftArm = {x: 0, y: 0, z: 1.1}; // A-Pose
        targetPose.rightArm = {x: 0, y: 0, z: -1.1};
        targetPose.leftLowerArm = {x: 0, y: 0, z: 0};
        targetPose.rightLowerArm = {x: 0, y: 0, z: 0};
        targetPose.leftHand = {x: 0, y: 0, z: 0};
        targetPose.rightHand = {x: 0, y: 0, z: 0};
        
        setHandPose(h, 'left', 'relaxed');
        setHandPose(h, 'right', 'relaxed');
        
        switch (emotion.toLowerCase()) {
            case 'happy':
            case 'joy':
            case 'success':
                targetPose.head.x = -0.1; // look up slightly
                targetPose.spine.x = -0.05; // lean back slightly
                targetPose.leftArm.z = 0.8; // arms slightly raised
                targetPose.rightArm.z = -0.8;
                targetPose.leftLowerArm.z = -0.2;
                targetPose.rightLowerArm.z = 0.2;
                setHandPose(h, 'left', 'open');
                setHandPose(h, 'right', 'open');
                break;
            case 'sad':
            case 'sorrow':
                targetPose.head.x = 0.2; // look down
                targetPose.spine.x = 0.1; // slouch forward
                targetPose.neck.x = 0.1;
                targetPose.leftArm.z = 1.2;
                targetPose.rightArm.z = -1.2;
                break;
            case 'angry':
            case 'error':
                targetPose.head.x = 0.1; // stare down
                targetPose.spine.x = 0.1; // lean forward aggressive
                targetPose.leftArm.z = 1.3; // shoulders tense
                targetPose.rightArm.z = -1.3;
                targetPose.leftLowerArm.z = -0.5; // bend elbows
                targetPose.rightLowerArm.z = 0.5;
                setHandPose(h, 'left', 'fist'); // Clenched fists
                setHandPose(h, 'right', 'fist');
                break;
            case 'thinking':
                targetPose.head.x = -0.1;
                targetPose.head.y = 0.2; // look to the side
                targetPose.neck.y = 0.1;
                targetPose.leftArm.z = 1.0;
                targetPose.leftLowerArm.z = -2.0; // Hand to chin
                targetPose.leftHand.x = 0.5;
                setHandPose(h, 'left', 'fist'); // Pondering fist
                break;
            case 'surprised':
                targetPose.head.x = -0.15; // jerk head back
                targetPose.spine.x = -0.1; 
                targetPose.leftArm.z = 0.7; // arms up
                targetPose.rightArm.z = -0.7;
                targetPose.leftLowerArm.z = -1.0;
                targetPose.rightLowerArm.z = 1.0;
                setHandPose(h, 'left', 'open'); // hands splayed
                setHandPose(h, 'right', 'open');
                break;
            case 'yawn':
                targetPose.head.x = -0.1; // head tilted slightly back to stretch
                targetPose.spine.x = -0.15; // arch back
                targetPose.leftArm.z = 0.5; // arms stretching up and out
                targetPose.rightArm.z = -0.5;
                targetPose.leftLowerArm.z = -0.3;
                targetPose.rightLowerArm.z = 0.3;
                targetPose.leftArm.x = -0.6; // arms raised
                targetPose.rightArm.x = -0.6;
                setHandPose(h, 'left', 'open');
                setHandPose(h, 'right', 'open');
                break;
            case 'sleep':
                targetPose.head.x = 0.3; // head heavily down
                targetPose.head.z = 0.2; // head tilted side
                targetPose.neck.x = 0.1;
                targetPose.spine.x = 0.1; // slouched
                targetPose.leftArm.z = 1.15; // totally relaxed
                targetPose.rightArm.z = -1.15;
                setHandPose(h, 'left', 'relaxed');
                setHandPose(h, 'right', 'relaxed');
                break;
            case 'dance':
                targetPose.head.z = Math.sin(Date.now() / 300) * 0.1; // head bob
                targetPose.spine.z = Math.sin(Date.now() / 400) * 0.1; // body sway
                targetPose.leftArm.z = 0.5; // arms out dancing
                targetPose.rightArm.z = -0.5;
                targetPose.leftLowerArm.z = -0.5;
                targetPose.rightLowerArm.z = 0.5;
                setHandPose(h, 'left', 'open');
                setHandPose(h, 'right', 'open');
                break;
            case 'wave':
                targetPose.head.x = -0.05;
                targetPose.rightArm.z = 0.3; // Arm raised up and out
                targetPose.rightLowerArm.z = 1.2; // forearm pointing up
                // The wave motion will just be a static pose, but it looks like a wave
                targetPose.leftArm.z = 1.0; // left arm relaxed
                setHandPose(h, 'right', 'open');
                break;
            case 'shy':
                targetPose.head.x = 0.15; // look down
                targetPose.head.y = 0.15; // look away
                targetPose.leftArm.z = 1.1; 
                targetPose.rightArm.z = -1.1;
                targetPose.leftLowerArm.z = -1.0; // hands clasped in front
                targetPose.rightLowerArm.z = 1.0;
                targetPose.leftHand.x = 0.2;
                targetPose.rightHand.x = -0.2;
                setHandPose(h, 'left', 'relaxed');
                setHandPose(h, 'right', 'relaxed');
                break;
            case 'proud':
                targetPose.head.x = -0.15; // head up proud
                targetPose.spine.x = -0.1; // chest out
                targetPose.leftArm.z = 0.9;
                targetPose.rightArm.z = -0.9;
                targetPose.leftLowerArm.z = -0.8; // hands on hips
                targetPose.rightLowerArm.z = 0.8;
                setHandPose(h, 'left', 'fist');
                setHandPose(h, 'right', 'fist');
                break;
            default:
                // Neutral
                break;
        }
    }
    let isBlinking = false;
    let isTalking = false;
    let talkingTimer = null;
    let blinkTimer = null;

    function triggerBlink() {
        if (!currentVrm || !currentVrm.expressionManager || isBlinking) return;
        isBlinking = true;
        currentVrm.expressionManager.setValue('blink', 1.0);
        currentVrm.expressionManager.update();
        
        setTimeout(() => {
            if (currentVrm) {
                currentVrm.expressionManager.setValue('blink', 0.0);
                currentVrm.expressionManager.update();
            }
            isBlinking = false;
        }, 150); // Blink duration 150ms
    }

    function scheduleNextBlink() {
        const nextBlink = Math.random() * 4000 + 2000; // between 2s and 6s
        blinkTimer = setTimeout(() => {
            triggerBlink();
            scheduleNextBlink();
        }, nextBlink);
    }

    function simulateLipSync() {
        if (!currentVrm || !currentVrm.expressionManager || !isTalking) {
            // Reset mouth if not talking
            if (currentVrm) {
                ['aa', 'ih', 'ou', 'ee', 'oh'].forEach(shape => currentVrm.expressionManager.setValue(shape, 0.0));
                currentVrm.expressionManager.update();
            }
            return;
        }

        // Randomize mouth shapes to simulate talking
        const shapes = ['aa', 'ih', 'ou', 'ee', 'oh'];
        shapes.forEach(shape => currentVrm.expressionManager.setValue(shape, 0.0));
        
        const randomShape = shapes[Math.floor(Math.random() * shapes.length)];
        const intensity = Math.random() * 0.8 + 0.2; // 0.2 to 1.0
        
        currentVrm.expressionManager.setValue(randomShape, intensity);
        currentVrm.expressionManager.update();

        // Change mouth shape every 50-150ms
        setTimeout(simulateLipSync, Math.random() * 100 + 50);
    }

    function startTalking(durationMs) {
        if (window.resetActivityTimer) window.resetActivityTimer();
        isTalking = true;
        simulateLipSync();
        
        if (talkingTimer) clearTimeout(talkingTimer);
        if (durationMs > 0) {
            talkingTimer = setTimeout(() => {
                isTalking = false;
            }, durationMs);
        }
    }

    function stopTalking() {
        isTalking = false;
        if (talkingTimer) clearTimeout(talkingTimer);
    }
    // --- End VTuber Animation Logic ---
    function initVTuber() {
        const container = document.getElementById('vrm-container');
        
        // Scene, Camera, Renderer
        const scene = new THREE.Scene();
        const camera = new THREE.PerspectiveCamera(30.0, container.clientWidth / container.clientHeight, 0.1, 20.0);
        camera.position.set(0.0, 1.4, 2.5); // Zoomed out slightly to avoid UI overlap
        
        const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
        renderer.setSize(container.clientWidth, container.clientHeight);
        renderer.setPixelRatio(window.devicePixelRatio);
        container.appendChild(renderer.domElement);
        
        // Light (Lower contrast for a softer look)
        const light = new THREE.DirectionalLight(0xffffff, 0.4);
        light.position.set(1.0, 1.0, 1.0).normalize();
        scene.add(light);
        
        const ambient = new THREE.AmbientLight(0xffffff, 0.8); // Brighter ambient fill
        scene.add(ambient);

        // Resize handler
        window.addEventListener('resize', () => {
            if (currentMode !== 'live') return;
            camera.aspect = container.clientWidth / container.clientHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(container.clientWidth, container.clientHeight);
        });

        // Load VRM Model (three-vrm v1.x API)
        const loader = new THREE.GLTFLoader();
        loader.crossOrigin = 'anonymous';
        
        loader.register((parser) => {
            return new THREE_VRM.VRMLoaderPlugin(parser);
        });

        loader.load(
            '/assets/model.vrm',
            (gltf) => {
                const vrm = gltf.userData.vrm;
                if (vrm) {
                    THREE_VRM.VRMUtils.removeUnnecessaryJoints(gltf.scene);
                    scene.add(vrm.scene);
                    currentVrm = vrm;

                    // Setup basic pose or facing camera
                    vrm.scene.rotation.y = Math.PI; // Face the camera
                    
                    // Fix T-Pose by lowering the arms (A-Pose)
                    if (vrm.humanoid) {
                        const leftArm = vrm.humanoid.getNormalizedBoneNode('leftUpperArm');
                        if (leftArm) leftArm.rotation.z = 1.1; // roughly 60 degrees down
                        
                        const rightArm = vrm.humanoid.getNormalizedBoneNode('rightUpperArm');
                        if (rightArm) rightArm.rotation.z = -1.1; // negative Z for right arm down
                    }

                    console.log('VRM model loaded successfully!');
                    
                    // Start automatic blinking
                    scheduleNextBlink();

                    // Play Welcome Animation & Message (Silent Wave)
                    setTimeout(async () => {
                        const welcomeText = "Hi! I'm Clio, your Local Autonomous Responsive Agent! I'm fully loaded and ready whenever you are!";
                        appendMessage('clio', welcomeText + " 💖");

                        // Trigger the wave animation instead of playing audio
                        setVTuberEmotion('wave');
                        setLiveEmotion('happy');
                        
                        setTimeout(() => {
                            setVTuberEmotion('neutral');
                            setLiveEmotion('neutral');
                        }, 3000);
                    }, 5000);
                }
            },
            (progress) => console.log('Loading model...', Math.round(100.0 * (progress.loaded / progress.total)), '%'),
            (error) => console.error('Failed to load VRM:', error)
        );


        // Animation Loop
        const clock = new THREE.Clock();
        function animate() {
            requestAnimationFrame(animate);
            const delta = clock.getDelta();
            
            // Update VRM
            if (currentVrm) {
                currentVrm.update(delta);
                const time = clock.elapsedTime;
                
                // Sleep Tracker (prevent sleep if she is actively vibing to music)
                if (window.isVibing && (isSleeping || isYawning)) {
                    resetActivityTimer(); // Wake up immediately if she starts vibing
                }
                
                let idleTime = Date.now() - lastActivityTime;
                
                if (!isTalking && !window.isVibing && idleTime > 115000 && idleTime <= 120000 && !isYawning && !isSleeping) {
                    isYawning = true;
                    setVTuberEmotion('yawn');
                    if (currentVrm.expressionManager) {
                        currentVrm.expressionManager.setValue('aa', 0.8); // open mouth to yawn
                        currentVrm.expressionManager.setValue('blink', 0.7); // squint eyes
                    }
                }

                if (!isTalking && !window.isVibing && idleTime > 120000 && !isSleeping) {
                    isSleeping = true;
                    isYawning = false;
                    setVTuberEmotion('sleep');
                    if (currentVrm.expressionManager) {
                        currentVrm.expressionManager.setValue('aa', 0.0); // ensure mouth is closed
                        currentVrm.expressionManager.setValue('blink', 1.0);
                        isBlinking = true; // pause random blinks
                    }
                }
                
                // Enforce Pose Targets via Lerp (fixes T-pose snap)
                if (currentVrm.humanoid && typeof targetPose !== 'undefined') {
                    const h = currentVrm.humanoid;
                    const lerpSpeed = 5.0 * delta;
                    
                    const bones = {
                        'head': targetPose.head,
                        'neck': targetPose.neck,
                        'spine': targetPose.spine,
                        'leftUpperArm': targetPose.leftArm,
                        'rightUpperArm': targetPose.rightArm,
                        'leftLowerArm': targetPose.leftLowerArm,
                        'rightLowerArm': targetPose.rightLowerArm,
                        'leftHand': targetPose.leftHand,
                        'rightHand': targetPose.rightHand
                    };
                    
                    for (const [boneName, target] of Object.entries(bones)) {
                        const bone = h.getNormalizedBoneNode(boneName);
                        if (bone) {
                            bone.rotation.x = THREE.MathUtils.lerp(bone.rotation.x, target.x, lerpSpeed);
                            bone.rotation.y = THREE.MathUtils.lerp(bone.rotation.y, target.y, lerpSpeed);
                            bone.rotation.z = THREE.MathUtils.lerp(bone.rotation.z, target.z, lerpSpeed);
                        }
                    }
                }

                if (isVibing && currentVrm.humanoid) {
                    // Slow, chill lofi vibe (approx 60-70 BPM)
                    const slowTime = time * Math.PI * 1.2;
                    const bounce = Math.abs(Math.sin(slowTime)); 
                    const sway = Math.sin(slowTime * 0.5); 
                    const deepSway = Math.sin(slowTime * 0.25);
                    
                    const spine = currentVrm.humanoid.getNormalizedBoneNode('spine');
                    const head = currentVrm.humanoid.getNormalizedBoneNode('head');
                    const neck = currentVrm.humanoid.getNormalizedBoneNode('neck');
                    
                    if (spine) {
                        spine.rotation.x = targetPose.spine.x + (bounce * 0.05); // very subtle forward lean
                        spine.rotation.z = targetPose.spine.z + (deepSway * 0.03); // slow body sway
                    }
                    if (neck) neck.rotation.x = targetPose.neck.x - (bounce * 0.02);
                    if (head) {
                        head.rotation.x = targetPose.head.x + (bounce * 0.03); 
                        head.rotation.y = targetPose.head.y + (deepSway * 0.05); // slow looking left/right
                        head.rotation.z = targetPose.head.z - (sway * 0.08); // slow head tilt side-to-side
                    }
                } else if (currentVrm.humanoid && isSleeping) {
                    // Sleeping breathing
                    const spine = currentVrm.humanoid.getNormalizedBoneNode('spine');
                    if (spine) spine.rotation.x = targetPose.spine.x + Math.sin(time * 1.5) * 0.02;
                } else if (currentVrm.humanoid) {
                    // Normal Subtle breathing
                    const spine = currentVrm.humanoid.getNormalizedBoneNode('spine');
                    if (spine) spine.rotation.x = targetPose.spine.x + Math.sin(time * 2) * 0.01;
                }
            }

            renderer.render(scene, camera);
        }
        animate();
        
        vrmSceneInitialized = true;
        console.log("VTuber Three.js Engine Initialized");
    }
});
