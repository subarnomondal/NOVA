// VTuber and VRM Animation Engine
// Extracted from app.js

    // --- VTuber Logic (Three.js + VRM Setup) ---
    let vrmSceneInitialized = false;
    let currentVrm = null;

    // --- Math & Easing Utilities ---
    function springLerp(current, target, delta, stiffness = 5.0, damping = 1.0) {
        // A simple exponential ease-out behaves nicely for poses
        return THREE.MathUtils.lerp(current, target, stiffness * delta);
    }

    // Pseudo-Perlin Noise: Combines multiple prime-frequency sine waves to create chaotic, non-repeating organic noise
    function noise(t) {
        return (Math.sin(t) + Math.sin(t * 1.37) + Math.sin(t * 1.73)) / 3.0;
    }

    
    function setVTuberEmotion(emotion) {
        if (!currentVrm || !currentVrm.expressionManager) return;
        
        // Reset all expressions first
        const presetNames = ['happy', 'angry', 'sad', 'relaxed', 'surprised', 'neutral'];
        presetNames.forEach(preset => {
            targetExpressions[preset] = 0.0;
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
            'yawn': 'relaxed',
            'excited': 'happy',
            'amazed': 'surprised',
            'wow': 'surprised',
            'scared': 'sad',
            'fear': 'sad',
            'terrified': 'sad',
            'confused': 'neutral',
            'huh': 'neutral',
            'what': 'surprised'
        };

        const targetExpression = vrmMap[emotion];
        if (targetExpression) {
            targetExpressions[targetExpression] = 1.0;
            // Add a slight mouth opening to the smile so it looks natural, not creepy
            if (targetExpression === 'happy') {
                targetExpressions['aa'] = 0.25; 
            } else {
                targetExpressions['aa'] = 0.0;
            }
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
        rightHand: {x:0, y:0, z:0},
        leftUpperLeg: {x:0, y:0, z:0},
        rightUpperLeg: {x:0, y:0, z:0},
        leftLowerLeg: {x:0, y:0, z:0},
        rightLowerLeg: {x:0, y:0, z:0},
        leftFoot: {x:0, y:0, z:0},
        rightFoot: {x:0, y:0, z:0},
        leftToes: {x:0, y:0, z:0},
        rightToes: {x:0, y:0, z:0},
        leftFingerCurls: { Thumb: 0, Index: 0, Middle: 0, Ring: 0, Little: 0 },
        rightFingerCurls: { Thumb: 0, Index: 0, Middle: 0, Ring: 0, Little: 0 }
    };

    const currentPose = {
        head: {x:0, y:0, z:0},
        neck: {x:0, y:0, z:0},
        spine: {x:0, y:0, z:0},
        leftArm: {x:0, y:0, z:1.1},
        rightArm: {x:0, y:0, z:-1.1},
        leftLowerArm: {x:0, y:0, z:0},
        rightLowerArm: {x:0, y:0, z:0},
        leftHand: {x:0, y:0, z:0},
        rightHand: {x:0, y:0, z:0},
        leftUpperLeg: {x:0, y:0, z:0},
        rightUpperLeg: {x:0, y:0, z:0},
        leftLowerLeg: {x:0, y:0, z:0},
        rightLowerLeg: {x:0, y:0, z:0},
        leftFoot: {x:0, y:0, z:0},
        rightFoot: {x:0, y:0, z:0},
        leftToes: {x:0, y:0, z:0},
        rightToes: {x:0, y:0, z:0}
    };
    
    const currentFingerCurls = { 
        left: { Thumb: 0, Index: 0, Middle: 0, Ring: 0, Little: 0 }, 
        right: { Thumb: 0, Index: 0, Middle: 0, Ring: 0, Little: 0 } 
    };
    
    const targetExpressions = {
        'happy': 0, 'angry': 0, 'sad': 0, 'relaxed': 0, 'surprised': 0, 'neutral': 0,
        'blink': 0, 'aa': 0, 'ih': 0, 'ou': 0, 'ee': 0, 'oh': 0
    };
    const currentExpressions = { ...targetExpressions };
    
    let lastActivityTime = Date.now();
    let isSleeping = false;
    let isYawning = false;

    function resetActivityTimer() {
        lastActivityTime = Date.now();
        if (isSleeping || isYawning) {
            isSleeping = false;
            isYawning = false;
            
            if (Math.random() < 0.1) {
                setVTuberEmotion('angry');
                // Automatically calm down after 4 seconds
                setTimeout(() => setVTuberEmotion('neutral'), 4000);
            } else {
                setVTuberEmotion('neutral');
            }
            
            targetExpressions['blink'] = 0.0;
            isBlinking = false;
        }
    }
    window.resetActivityTimer = resetActivityTimer;

    // --- Mouse Tracking Logic ---
    let mousePos = { x: 0, y: 0 };
    let isTrackingMouse = false;
    let nextMouseCheckTime = Date.now() + 5000;

    document.addEventListener('mousemove', (e) => {
        // Normalize mouse pos to -1 to 1
        mousePos.x = (e.clientX / window.innerWidth) * 2 - 1;
        mousePos.y = -(e.clientY / window.innerHeight) * 2 + 1; // Invert Y
        resetActivityTimer();
        isTrackingMouse = true; // Instantly snap attention to mouse movement
        nextMouseCheckTime = Date.now() + 2500; // Wander away if mouse stops moving for 2.5s
    });
    function setHandPose(humanoid, side, pose) {
        let curls = { Thumb: 0.1, Index: 0.2, Middle: 0.3, Ring: 0.4, Little: 0.5 }; // relaxed
        
        if (pose === 'fist') {
            curls = { Thumb: 1.2, Index: 1.2, Middle: 1.2, Ring: 1.2, Little: 1.2 };
        } else if (pose === 'open') {
            curls = { Thumb: -0.1, Index: -0.1, Middle: -0.1, Ring: -0.1, Little: -0.1 };
        } else if (pose === 'point') {
            curls = { Thumb: 1.2, Index: 0.0, Middle: 1.2, Ring: 1.2, Little: 1.2 };
        } else if (pose === 'peace') {
            curls = { Thumb: 1.2, Index: 0.0, Middle: 0.0, Ring: 1.2, Little: 1.2 };
        } else if (pose === 'explain') {
            curls = { Thumb: -0.2, Index: 0.1, Middle: 0.3, Ring: 0.5, Little: 0.7 };
        }
        
        if (side === 'left') {
            targetPose.leftFingerCurls = curls;
        } else {
            targetPose.rightFingerCurls = curls;
        }
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
        
        // Reset base leg stance (slightly spread, flat feet)
        targetPose.leftUpperLeg = {x: 0, y: 0, z: 0.03};
        targetPose.rightUpperLeg = {x: 0, y: 0, z: -0.03};
        targetPose.leftLowerLeg = {x: 0, y: 0, z: 0};
        targetPose.rightLowerLeg = {x: 0, y: 0, z: 0};
        targetPose.leftFoot = {x: 0, y: 0, z: -0.03};
        targetPose.rightFoot = {x: 0, y: 0, z: 0.03};
        targetPose.leftToes = {x: 0, y: 0, z: 0};
        targetPose.rightToes = {x: 0, y: 0, z: 0};
        
        setHandPose(h, 'left', 'relaxed');
        setHandPose(h, 'right', 'relaxed');
        
        switch (emotion.toLowerCase()) {
            case 'happy':
            case 'joy':
            case 'success':
                targetPose.head.x = -0.1; // look up slightly
                targetPose.head.z = 0.05; // slight cute tilt
                targetPose.spine.x = -0.05; // lean back slightly
                // Cute peace sign pose with left hand
                targetPose.leftArm.z = 0.4; // Arm raised up and out
                targetPose.leftArm.x = -0.3; // Arm slightly forward
                targetPose.leftLowerArm.z = -2.0; // Elbow bent up to face
                targetPose.leftHand.y = 0.0; // Fixed wrist twist
                targetPose.leftHand.z = 0.2; // Angle hand slightly
                // Right arm relaxed but slightly energetic
                targetPose.rightArm.z = -1.0;
                targetPose.rightArm.x = -0.2;
                targetPose.rightLowerArm.z = 0.5;
                // Legs bouncy stance
                targetPose.leftUpperLeg.z = -0.1; // Knees together slightly
                targetPose.rightUpperLeg.z = 0.1;
                targetPose.leftLowerLeg.x = 0.05; // Slight bounce bend
                targetPose.rightLowerLeg.x = 0.05;
                setHandPose(h, 'left', 'peace');
                setHandPose(h, 'right', 'open');
                break;
            case 'sad':
            case 'sorrow':
                targetPose.head.x = 0.2; // look down
                targetPose.spine.x = 0.1; // slouch forward
                targetPose.neck.x = 0.1;
                targetPose.leftArm.z = 1.2;
                targetPose.rightArm.z = -1.2;
                targetPose.leftUpperLeg.z = -0.08; // Knees pulled in
                targetPose.rightUpperLeg.z = 0.08;
                targetPose.leftLowerLeg.x = 0.1; // Slouched leg bend
                targetPose.rightLowerLeg.x = 0.1;
                break;
            case 'angry':
            case 'error':
                targetPose.head.x = 0.1; // stare down
                targetPose.spine.x = 0.1; // lean forward aggressive
                targetPose.leftArm.z = 1.3; // shoulders tense
                targetPose.rightArm.z = -1.3;
                targetPose.leftLowerArm.z = -0.5; // bend elbows
                targetPose.rightLowerArm.z = 0.5;
                targetPose.leftUpperLeg.z = 0.12; // Wide aggressive stance
                targetPose.rightUpperLeg.z = -0.12;
                targetPose.leftFoot.z = -0.12; // Feet flat on wide stance
                targetPose.rightFoot.z = 0.12;
                setHandPose(h, 'left', 'fist'); // Clenched fists
                setHandPose(h, 'right', 'fist');
                break;
            case 'excited':
            case 'amazed':
            case 'wow':
                targetPose.head.x = -0.15; // look up
                targetPose.spine.x = -0.1; // arch back
                targetPose.leftArm.z = 0.5; // Arms up (V shape)
                targetPose.leftArm.x = 0.2; // Arms slightly back
                targetPose.rightArm.z = -0.5;
                targetPose.rightArm.x = 0.2;
                targetPose.leftLowerArm.z = -2.5; // Forearms pointing straight up
                targetPose.rightLowerArm.z = 2.5;
                // Fix wrists to face forward/inward naturally
                targetPose.leftHand.y = 0.0; 
                targetPose.rightHand.y = 0.0;
                targetPose.leftHand.x = -0.2; // palms tilted up
                targetPose.rightHand.x = -0.2;
                targetPose.leftUpperLeg.z = -0.15; // Knees bent outwards (bouncy stance)
                targetPose.rightUpperLeg.z = 0.15;
                targetPose.leftLowerLeg.x = 0.2; // Deep knee bend
                targetPose.rightLowerLeg.x = 0.2;
                targetPose.leftFoot.x = -0.1; // Up on tiptoes slightly
                targetPose.rightFoot.x = -0.1;
                setHandPose(h, 'left', 'open'); // Hands open wide
                setHandPose(h, 'right', 'open');
                break;
            case 'scared':
            case 'fear':
            case 'terrified':
                targetPose.head.x = 0.25; // Tuck chin
                targetPose.spine.x = 0.2; // Hunch back deeply
                targetPose.leftArm.z = 1.3; // Bring arms tight against body
                targetPose.leftArm.x = -0.4;
                targetPose.rightArm.z = -1.3;
                targetPose.rightArm.x = -0.4;
                targetPose.leftLowerArm.z = -1.5; // Cross forearms tight across chest
                targetPose.rightLowerArm.z = 1.5;
                // Fix wrists/palms to clutch chest (moved twists from elbow)
                targetPose.leftHand.z = 0.5;
                targetPose.leftHand.y = 0.0;
                targetPose.leftHand.x = -0.8; 
                targetPose.rightHand.z = -0.5;
                targetPose.rightHand.y = 0.0;
                targetPose.rightHand.x = -0.8;
                targetPose.leftUpperLeg.z = -0.1; // Knees knocked together (pigeon toed)
                targetPose.rightUpperLeg.z = 0.1;
                targetPose.leftUpperLeg.y = 0.2; // Twist inward
                targetPose.rightUpperLeg.y = -0.2;
                targetPose.leftLowerLeg.x = 0.25; // Crouched down low
                targetPose.rightLowerLeg.x = 0.25;
                targetPose.leftFoot.z = 0.15; // Feet turned inwards
                targetPose.rightFoot.z = -0.15;
                setHandPose(h, 'left', 'fist'); // Clenched hands
                setHandPose(h, 'right', 'fist');
                break;
            case 'confused':
            case 'huh':
            case 'what':
                targetPose.head.x = -0.05;
                targetPose.head.z = 0.25; // Severe dog-tilt to the side
                targetPose.spine.z = -0.1; // Lean slightly opposite to balance
                targetPose.leftArm.z = 0.4; // Arm up for head scratching
                targetPose.leftArm.x = -0.5;
                targetPose.leftLowerArm.z = -2.8; // Elbow bent fully
                // Fix scratching wrist so palm faces head (moved twists from elbow)
                targetPose.leftHand.y = 0.0; 
                targetPose.leftHand.z = 0.5;
                targetPose.leftHand.x = 0.8; 
                targetPose.rightArm.z = -0.6; // Other arm out asking a question
                targetPose.rightArm.x = -0.2;
                targetPose.rightLowerArm.z = 1.5; // Elbow bent out
                // Fix questioning wrist so palm faces perfectly up (moved twists from elbow)
                targetPose.rightHand.x = 0.5; 
                targetPose.rightHand.y = 0.0;
                targetPose.leftUpperLeg.z = -0.1;
                targetPose.rightUpperLeg.z = -0.1; // Asymmetric leg stance (one straight, one bent)
                targetPose.rightLowerLeg.x = 0.15; // Right knee bent
                targetPose.leftFoot.x = -0.05; // Weight on left foot
                setHandPose(h, 'left', 'fist'); // Scratching hand
                setHandPose(h, 'right', 'open'); // Questioning hand
                break;
            case 'thinking':
                targetPose.head.x = -0.1;
                targetPose.head.y = 0.3; // look to the side (transferred neck twist)
                targetPose.leftArm.z = 0.8; // Raise arm
                targetPose.leftArm.x = -0.6; // Bring arm forward
                targetPose.leftArm.y = -0.2; // Bring arm inward
                targetPose.leftLowerArm.z = -2.2; // Bend elbow fully to reach face
                targetPose.leftHand.x = -0.5;
                setHandPose(h, 'left', 'point'); // Pondering index finger
                break;
            case 'surprised':
                targetPose.head.x = -0.15; // jerk head back
                targetPose.spine.x = -0.1; 
                targetPose.leftArm.z = 0.8; // arms slightly raised
                targetPose.rightArm.z = -0.8;
                targetPose.leftArm.x = -0.4; // arms forward
                targetPose.rightArm.x = -0.4;
                targetPose.leftArm.y = -0.3; // arms inward
                targetPose.rightArm.y = 0.3;
                targetPose.leftLowerArm.z = -2.0; // bend elbows up toward chest/face
                targetPose.rightLowerArm.z = 2.0;
                targetPose.leftUpperLeg.x = -0.1; // Weight shifted back
                targetPose.rightUpperLeg.x = -0.1;
                targetPose.leftLowerLeg.x = 0.15; // Knees bent
                targetPose.rightLowerLeg.x = 0.15;
                setHandPose(h, 'left', 'open'); // hands splayed
                setHandPose(h, 'right', 'open');
                break;
            case 'yawn':
                targetPose.head.x = -0.1; // head tilted slightly back
                targetPose.spine.x = -0.1; 
                targetPose.leftArm.z = 0.8; // raise arm
                targetPose.leftArm.x = -0.6; // forward
                targetPose.leftArm.y = -0.2; // inward
                targetPose.leftLowerArm.z = -2.2; // bend elbow to face
                targetPose.leftHand.x = -0.5; // move twist to hand
                // right arm relaxed
                targetPose.rightArm.z = -1.15;
                setHandPose(h, 'left', 'relaxed');
                setHandPose(h, 'right', 'relaxed');
                break;
            case 'sleep':
                targetPose.head.x = 0.4; // head heavily down (moved neck bend)
                targetPose.head.z = 0.2; // head tilted side
                targetPose.spine.x = 0.1; // slouched
                targetPose.leftArm.z = 1.15; // totally relaxed
                targetPose.rightArm.z = -1.15;
                targetPose.leftUpperLeg.z = -0.05; // Knees collapse inwards
                targetPose.rightUpperLeg.z = 0.05;
                targetPose.leftLowerLeg.x = 0.1; // Legs buckled slightly
                targetPose.rightLowerLeg.x = 0.1;
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
                targetPose.leftUpperLeg.z = 0.1; // Wide stance for dancing
                targetPose.rightUpperLeg.z = -0.1;
                targetPose.leftLowerLeg.x = 0.1; // Bouncy knees
                targetPose.rightLowerLeg.x = 0.1;
                setHandPose(h, 'left', 'open');
                setHandPose(h, 'right', 'open');
                break;
            case 'wave':
                targetPose.head.x = -0.05;
                // Human-like relaxed wave pose
                targetPose.rightArm.z = -0.7; // Arm lowered to side
                targetPose.rightArm.x = -0.2; // Arm brought forward slightly
                targetPose.rightLowerArm.z = 2.5; // Elbow bent up to face level
                targetPose.rightHand.y = 0; // Don't over-twist the wrist, default faces mostly forward/inward
                targetPose.rightHand.x = 0; // Neutral angle
                targetPose.leftArm.z = 1.0; // Left arm relaxed
                targetPose.leftUpperLeg.z = -0.1; // Cute stance (knees slightly in)
                targetPose.rightUpperLeg.z = 0.1;
                targetPose.leftLowerLeg.x = 0.05; // Slight bend
                targetPose.rightLowerLeg.x = 0.05;
                setHandPose(h, 'right', 'open');
                
                window.isWaving = true;
                window.waveStartTime = Date.now();
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
                targetPose.leftUpperLeg.z = -0.15; // Pigeon-toed / knees tightly together
                targetPose.rightUpperLeg.z = 0.15;
                targetPose.leftLowerLeg.x = 0.05; 
                targetPose.rightLowerLeg.x = 0.05;
                targetPose.leftFoot.z = 0.1; // Feet turned inward
                targetPose.rightFoot.z = -0.1;
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
                targetPose.leftUpperLeg.z = 0.15; // Very wide confident stance
                targetPose.rightUpperLeg.z = -0.15;
                targetPose.leftFoot.z = -0.15; // Feet flat on wide stance
                targetPose.rightFoot.z = 0.15;
                setHandPose(h, 'left', 'fist');
                setHandPose(h, 'right', 'explain');
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
        // Variable blink speed (100-200ms) — humans aren't metronomes
        const blinkDuration = 100 + Math.random() * 100;
        targetExpressions['blink'] = 1.0;
        
        setTimeout(() => {
            if (currentVrm && !isSleeping) {
                targetExpressions['blink'] = 0.0;
            }
            isBlinking = false;

            // 40% chance of a cute double-blink (very human, very anime)
            if (Math.random() < 0.4 && !isSleeping) {
                setTimeout(() => {
                    if (!isBlinking && currentVrm && !isSleeping) {
                        isBlinking = true;
                        targetExpressions['blink'] = 1.0;
                        setTimeout(() => {
                            targetExpressions['blink'] = 0.0;
                            isBlinking = false;
                        }, 80); // second blink is faster
                    }
                }, 120); // tiny gap between double-blinks
            }
        }, blinkDuration);
    }

    function scheduleNextBlink() {
        // Humans blink every 2-8s, more frequently when talking
        const base = isTalking ? 1500 : 2500;
        const range = isTalking ? 2000 : 5500;
        const nextBlink = Math.random() * range + base;
        blinkTimer = setTimeout(() => {
            triggerBlink();
            scheduleNextBlink();
        }, nextBlink);
    }

    // --- Cute Idle Micro-Expressions ---
    // Tiny facial twitches that make her feel alive between emotions
    let microExprTimer = null;
    function scheduleMicroExpression() {
        const delay = 8000 + Math.random() * 7000; // every 8-15 seconds
        microExprTimer = setTimeout(() => {
            if (!currentVrm || isSleeping || isTalking) { scheduleMicroExpression(); return; }
            
            const roll = Math.random();
            if (roll < 0.35) {
                // Tiny smile flicker (cute!)
                targetExpressions['happy'] = 0.3;
                setTimeout(() => { targetExpressions['happy'] = 0; }, 1500 + Math.random() * 1000);
            } else if (roll < 0.55) {
                // Curious squint
                targetExpressions['relaxed'] = 0.25;
                setTimeout(() => { targetExpressions['relaxed'] = 0; }, 1200);
            } else if (roll < 0.70) {
                // Tiny pout (adorable)
                targetExpressions['ou'] = 0.15;
                setTimeout(() => { targetExpressions['ou'] = 0; }, 800);
            }
            // else: nothing, variety includes no-reaction
            scheduleMicroExpression();
        }, delay);
    }

    // --- REAL-TIME AUDIO LIP SYNC ---
    let audioContext = null;
    let audioAnalyser = null;
    let audioDataArray = null;

    window.startAudioLipSync = function(audioElement) {
        try {
            if (!audioContext) {
                audioContext = new (window.AudioContext || window.webkitAudioContext)();
            }
            if (audioContext.state === 'suspended') {
                audioContext.resume();
            }
            
            // Only connect once
            if (!audioElement.sourceConnected) {
                const source = audioContext.createMediaElementSource(audioElement);
                audioAnalyser = audioContext.createAnalyser();
                audioAnalyser.fftSize = 256;
                audioDataArray = new Uint8Array(audioAnalyser.frequencyBinCount);
                
                source.connect(audioAnalyser);
                audioAnalyser.connect(audioContext.destination);
                audioElement.sourceConnected = true;
            }
            
            isTalking = true;
            audioElement.addEventListener('ended', () => {
                isTalking = false;
                ['aa', 'ih', 'ou', 'ee', 'oh'].forEach(shape => targetExpressions[shape] = 0.0);
                if (targetExpressions['happy'] > 0.5) targetExpressions['aa'] = 0.25; // Restore smile
            });
            audioElement.addEventListener('pause', () => {
                isTalking = false;
                ['aa', 'ih', 'ou', 'ee', 'oh'].forEach(shape => targetExpressions[shape] = 0.0);
                if (targetExpressions['happy'] > 0.5) targetExpressions['aa'] = 0.25; // Restore smile
            });
            audioElement.addEventListener('play', () => {
                isTalking = true;
                if (audioContext.state === 'suspended') {
                    audioContext.resume();
                }
            });
            
        } catch (err) {
            console.error("Audio lip sync setup failed:", err);
            // Fallback to basic open mouth if AudioContext fails (e.g. CORS or permission issues)
            isTalking = true;
            targetExpressions['aa'] = 0.4;
            setTimeout(() => { targetExpressions['aa'] = 0.0; isTalking = false; }, 2000);
        }
    };

    function startTalking(durationMs) {
        if (window.resetActivityTimer) window.resetActivityTimer();
        isTalking = true;
        
        // This is only called when text-only responses are generated (no audio).
        // Since we don't have audio here, we fall back to a random mouth flap timer.
        simulateLipSyncFallback();
        
        if (talkingTimer) clearTimeout(talkingTimer);
        if (durationMs > 0) {
            talkingTimer = setTimeout(() => {
                isTalking = false;
            }, durationMs);
        }
    }
    
    function simulateLipSyncFallback() {
        if (!isTalking || audioAnalyser) return; // Yield to FFT if active
        ['aa', 'ih', 'ou', 'ee', 'oh'].forEach(shape => targetExpressions[shape] = 0.0);
        const phonemes = ['aa', 'ih', 'ee'];
        targetExpressions[phonemes[Math.floor(Math.random() * phonemes.length)]] = 0.2 + Math.random() * 0.4;
        setTimeout(simulateLipSyncFallback, 100 + Math.random() * 150);
    }

    function stopTalking() {
        isTalking = false;
        ['aa', 'ih', 'ou', 'ee', 'oh'].forEach(shape => targetExpressions[shape] = 0.0);
        if (targetExpressions['happy'] > 0.5) targetExpressions['aa'] = 0.25; // Restore smile
        if (talkingTimer) clearTimeout(talkingTimer);
    }
    // --- End VTuber Animation Logic ---
    function initVTuber() {
        const container = document.getElementById('vrm-container');
        
        // Scene, Camera, Renderer
        const scene = new THREE.Scene();
        const camera = new THREE.PerspectiveCamera(30.0, container.clientWidth / container.clientHeight, 0.1, 20.0);
        
        // Initial Framing (Knee to Head default)
        camera.position.set(0.0, 1.0, 4.0); 

        // Frame Adjuster Slider Logic
        const frameSlider = document.getElementById('camera-frame-slider');
        if (frameSlider) {
            frameSlider.addEventListener('input', (e) => {
                const zVal = parseFloat(e.target.value);
                camera.position.z = zVal;
                // Automatically adjust Y to keep the avatar framed nicely as we zoom out
                // We reduce the multiplier from 0.15 to 0.10 so the camera doesn't dip down as far
                camera.position.y = 1.4 - ((zVal - 1.5) * 0.10);
            });
            // Trigger once to set initial position from the slider's default value
            frameSlider.dispatchEvent(new Event('input'));
        }
        
        const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
        renderer.setSize(container.clientWidth, container.clientHeight);
        
        // Force minimum 2x pixel ratio (Supersampling) to eliminate jagged edges and "8-bit" look
        renderer.setPixelRatio(Math.max(window.devicePixelRatio, 2.0)); 
        
        // CRITICAL: VRM/GLTF models require sRGB encoding for proper texture colors and lighting
        renderer.outputEncoding = THREE.sRGBEncoding;
        
        container.appendChild(renderer.domElement);
        
        // --- 3-Point Lighting Setup ---
        // Main Key Light
        const mainLight = new THREE.DirectionalLight(0xffffff, 0.4);
        mainLight.position.set(1.0, 1.0, 1.0).normalize();
        scene.add(mainLight);
        
        // Fill Light (softens shadows on the opposite side)
        const fillLight = new THREE.DirectionalLight(0xffffff, 0.1);
        fillLight.position.set(-1.0, 0.5, 1.0).normalize(); 
        scene.add(fillLight);
        
        // Rim / Backlight (separates character from background)
        const rimLight = new THREE.DirectionalLight(0xffffff, 0.15);
        rimLight.position.set(0.0, 1.0, -2.0).normalize(); 
        scene.add(rimLight);

        // Global Ambient Fill
        const ambient = new THREE.AmbientLight(0xffffff, 0.3);
        scene.add(ambient);

        // --- Dynamic Environment Lighting ---
        window.setVTuberLighting = function(bgClass) {
            if (bgClass === 'bg-pastel-bedroom') {
                // Soft, warm morning sunlight, very low contrast
                ambient.color.setHex(0xfff0f5); // lavender blush
                ambient.intensity = 0.4;
                mainLight.color.setHex(0xfffae6); // soft warm sunlight
                mainLight.intensity = 0.3;
                fillLight.color.setHex(0xe6e6fa); // light violet bounce
                fillLight.intensity = 0.15;
                rimLight.color.setHex(0xffffff); // soft white rim
                rimLight.intensity = 0.1;
            } else if (bgClass === 'bg-magical-library') {
                // Warm, dim, magical gold & purple lighting, medium contrast
                ambient.color.setHex(0x4a3b5c); // dark purple shadow fill
                ambient.intensity = 0.5;
                mainLight.color.setHex(0xffd700); // golden chandelier/magic light
                mainLight.intensity = 0.4;
                fillLight.color.setHex(0x8a2be2); // purple magical fill
                fillLight.intensity = 0.2;
                rimLight.color.setHex(0xffb6c1); // pink magical rim
                rimLight.intensity = 0.2;
            } else if (bgClass === 'bg-cozy-gaming') {
                // Neon cyber lighting, high contrast
                ambient.color.setHex(0x1a0f2e); // very dark purple ambient
                ambient.intensity = 0.6;
                mainLight.color.setHex(0x00ffff); // cyan monitor glow (front)
                mainLight.intensity = 0.3;
                fillLight.color.setHex(0xff1493); // deep pink neon (side)
                fillLight.intensity = 0.3;
                rimLight.color.setHex(0x8a2be2); // purple neon (back)
                rimLight.intensity = 0.4;
            } else if (bgClass === 'bg-fantasy-sky') {
                // Ethereal, heavenly, bright outdoor sky
                ambient.color.setHex(0xf0f8ff); // alice blue sky ambient
                ambient.intensity = 0.45;
                mainLight.color.setHex(0xffffff); // bright sun
                mainLight.intensity = 0.35;
                fillLight.color.setHex(0xadd8e6); // light blue sky bounce
                fillLight.intensity = 0.2;
                rimLight.color.setHex(0xfffacd); // lemon chiffon sun rim
                rimLight.intensity = 0.25;
            }
        };
        
        // Init default
        window.setVTuberLighting('bg-pastel-bedroom');

        // Robust Resize Handler (prevents CSS stretching pixelation)
        const resizeObserver = new ResizeObserver(entries => {
            for (let entry of entries) {
                const width = entry.contentRect.width;
                const height = entry.contentRect.height;
                
                if (width === 0 || height === 0) return; // Ignore if hidden
                
                camera.aspect = width / height;
                camera.updateProjectionMatrix();
                renderer.setSize(width, height);
            }
        });
        resizeObserver.observe(container);

        // --- Interactive Cursor (Raycaster) ---
        const raycaster = new THREE.Raycaster();
        const mouse = new THREE.Vector2();
        let isMouseDown = false;
        let isPetting = false;
        let isDraggingHand = false;
        let draggedHand = null; // 'left' or 'right'
        let mouseWorldPos = new THREE.Vector3();
        let cursorHoverWorldPos = new THREE.Vector3();
        let isMouseInContainer = false;
        let petTimer = 0;
        let wasPetting = false;
        let dragPlaneZ = 0;
        
        container.addEventListener('mousedown', (event) => {
            isMouseDown = true;
            updateMousePos(event);
            checkIntersections();
        });
        
        container.addEventListener('mouseenter', () => isMouseInContainer = true);
        
        container.addEventListener('mousemove', (event) => {
            isMouseInContainer = true;
            updateMousePos(event);
            
            // Calculate hover pos in 3D for wind effect
            raycaster.setFromCamera(mouse, camera);
            const planeZ = new THREE.Plane(new THREE.Vector3(0, 0, 1), 0);
            raycaster.ray.intersectPlane(planeZ, cursorHoverWorldPos);
            
            // Mouse collider removed - using hand colliders instead
            
            if (isMouseDown) {
                if (isPetting) {
                    petTimer = 1.0; // Keep petting reaction active while moving mouse
                }
                
                // Update 3D world pos for hand dragging
                if (isDraggingHand) {
                    raycaster.setFromCamera(mouse, camera);
                    // Create an invisible plane at the character's depth to drag along
                    const planeZ = new THREE.Plane(new THREE.Vector3(0, 0, 1), dragPlaneZ);
                    raycaster.ray.intersectPlane(planeZ, mouseWorldPos);
                }
            } else {
                // Hover detection for cursor change
                if (currentVrm && currentVrm.scene) {
                    raycaster.setFromCamera(mouse, camera);
                    const intersects = raycaster.intersectObjects(currentVrm.scene.children, true);
                    if (intersects.length > 0) {
                        const hitPart = getHitPart(intersects[0].point);
                        if (hitPart === 'head' || hitPart === 'leftArm' || hitPart === 'rightArm') {
                            container.style.cursor = 'pointer'; // Grab/Pet indicator
                        } else {
                            container.style.cursor = 'default';
                        }
                    } else {
                        container.style.cursor = 'default';
                    }
                }
            }
        });
        
        container.addEventListener('mouseup', () => {
            isMouseDown = false;
            isPetting = false;
            isDraggingHand = false;
            draggedHand = null;
        });
        
        container.addEventListener('mouseleave', () => {
            isMouseDown = false;
            isPetting = false;
            isDraggingHand = false;
            draggedHand = null;
            isMouseInContainer = false;
        });

        function updateMousePos(event) {
            const rect = container.getBoundingClientRect();
            mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
            mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
        }

        function getHitPart(point) {
            if (!currentVrm || !currentVrm.humanoid) return 'body';
            const h = currentVrm.humanoid;
            
            const head = h.getNormalizedBoneNode('head');
            const leftArm = h.getNormalizedBoneNode('leftLowerArm'); // Forearm/Hand region
            const rightArm = h.getNormalizedBoneNode('rightLowerArm');
            const spine = h.getNormalizedBoneNode('spine');
            
            const parts = [];
            if (head) {
                const p = new THREE.Vector3();
                head.getWorldPosition(p);
                parts.push({ name: 'head', dist: point.distanceTo(p) });
            }
            if (leftArm) {
                const p = new THREE.Vector3();
                leftArm.getWorldPosition(p);
                parts.push({ name: 'leftArm', dist: point.distanceTo(p) });
            }
            if (rightArm) {
                const p = new THREE.Vector3();
                rightArm.getWorldPosition(p);
                parts.push({ name: 'rightArm', dist: point.distanceTo(p) });
            }
            if (spine) {
                const p = new THREE.Vector3();
                spine.getWorldPosition(p);
                // Bias the spine distance slightly so arms are easier to grab
                parts.push({ name: 'body', dist: point.distanceTo(p) * 1.5 });
            }
            
            if (parts.length === 0) return 'body';
            
            parts.sort((a, b) => a.dist - b.dist);
            return parts[0].name;
        }

        function checkIntersections() {
            if (!currentVrm || !currentVrm.scene) return;
            raycaster.setFromCamera(mouse, camera);
            const intersects = raycaster.intersectObjects(currentVrm.scene.children, true);
            
            if (intersects.length > 0) {
                // Determine what part of the body was clicked based on distance to bones
                // instead of mesh names (since VRM meshes are often combined into one 'Body' mesh)
                const hitPart = getHitPart(intersects[0].point);
                
                if (hitPart === 'head') {
                    isPetting = true;
                    petTimer = 1.0;
                } else if (hitPart === 'leftArm' || hitPart === 'rightArm') {
                    isDraggingHand = true;
                    draggedHand = hitPart === 'leftArm' ? 'left' : 'right';
                    
                    // Init drag plane depth based on where the user clicked, pulling it slightly forward 
                    // so the hand hovers in front of the body, preventing clipping
                    dragPlaneZ = -(intersects[0].point.z + 0.15);
                    const planeZ = new THREE.Plane(new THREE.Vector3(0, 0, 1), dragPlaneZ);
                    raycaster.ray.intersectPlane(planeZ, mouseWorldPos);
                } else {
                    // Poke body reaction
                    if (window.setVTuberEmotion) {
                        window.setVTuberEmotion('surprised');
                        setTimeout(() => window.setVTuberEmotion('neutral'), 1500);
                    }
                }
            }
        }

        // Missing blink and expression functions that were causing a ReferenceError
        let isBlinking = false;
        function scheduleNextBlink() {
            if (!currentVrm || !currentVrm.expressionManager) return;
            const timeToNextBlink = Math.random() * 3000 + 2000; // 2 to 5 seconds
            setTimeout(() => {
                if (!isBlinking && !isSleeping) {
                    targetExpressions['blink'] = 1.0;
                    isBlinking = true;
                    setTimeout(() => {
                        targetExpressions['blink'] = 0.0;
                        isBlinking = false;
                        scheduleNextBlink();
                    }, 150);
                } else {
                    scheduleNextBlink();
                }
            }, timeToNextBlink);
        }

        function scheduleMicroExpression() {
            const timeToNextExpr = Math.random() * 8000 + 4000;
            setTimeout(() => {
                if (!isTalking && !isSleeping && !window.isVibing && !isYawning && !isDraggingHand && !isPetting) {
                    // Small chance to briefly switch to a subtle expression to look alive
                    if (Math.random() > 0.5) {
                        const subtleExprs = ['relaxed', 'neutral'];
                        const expr = subtleExprs[Math.floor(Math.random() * subtleExprs.length)];
                        if (window.setVTuberEmotion) window.setVTuberEmotion(expr);
                        setTimeout(() => {
                            if (window.setVTuberEmotion) window.setVTuberEmotion('neutral');
                        }, 2000);
                    }
                }
                scheduleMicroExpression();
            }, timeToNextExpr);
        }

        // Load VRM Model (three-vrm v1.x API)
        const loader = new THREE.GLTFLoader();
        loader.crossOrigin = 'anonymous';
        
        loader.register((parser) => {
            return new THREE_VRM.VRMLoaderPlugin(parser);
        });

        // Smart Browser Caching: Load from hard drive on subsequent visits
        async function loadModelWithCache(url) {
            try {
                const cacheName = 'vrm-cache-v1';
                const cache = await caches.open(cacheName);
                let response = await cache.match(url);
                
                if (!response) {
                    console.log("Model not in cache, downloading...");
                    response = await fetch(url);
                    if (response.ok) {
                        cache.put(url, response.clone());
                    }
                } else {
                    console.log("Model loaded from local cache instantly!");
                }
                
                const blob = await response.blob();
                return URL.createObjectURL(blob);
            } catch (err) {
                console.warn("Caching failed or unsupported, falling back to network load:", err);
                return url;
            }
        }

        loadModelWithCache('/assets/model.vrm').then((modelUrl) => {
            loader.load(
                modelUrl,
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
                    
                    // --- HAND PHYSICS COLLIDER SETUP ---
                    if (vrm.humanoid && vrm.springBoneManager) {
                        const leftHand = vrm.humanoid.getNormalizedBoneNode('leftHand');
                        const rightHand = vrm.humanoid.getNormalizedBoneNode('rightHand');
                        
                        const handColliderGroup = new THREE_VRM.VRMSpringBoneColliderGroup();
                        
                        if (leftHand) {
                            const leftColliderShape = new THREE_VRM.VRMSpringBoneColliderShapeSphere({ offset: new THREE.Vector3(0, 0, 0), radius: 0.1 });
                            const leftCollider = new THREE_VRM.VRMSpringBoneCollider(leftColliderShape);
                            leftHand.add(leftCollider);
                            handColliderGroup.addCollider(leftCollider);
                        }
                        
                        if (rightHand) {
                            const rightColliderShape = new THREE_VRM.VRMSpringBoneColliderShapeSphere({ offset: new THREE.Vector3(0, 0, 0), radius: 0.1 });
                            const rightCollider = new THREE_VRM.VRMSpringBoneCollider(rightColliderShape);
                            rightHand.add(rightCollider);
                            handColliderGroup.addCollider(rightCollider);
                        }
                        
                        // Inject our hand colliders into EVERY spring bone on the model
                        vrm.springBoneManager.springBones.forEach(springBone => {
                            if (!springBone.colliderGroups) {
                                springBone.colliderGroups = [];
                            }
                            springBone.colliderGroups.push(handColliderGroup);
                        });
                        console.log('Successfully injected interactive HAND physics colliders!');
                    }
                    // ------------------------------------
                    
                    // Start automatic blinking and idle micro-expressions
                    scheduleNextBlink();
                    scheduleMicroExpression();

                    // Loading screen removed.

                    // Play Welcome Animation & Message (Silent Wave)
                    setTimeout(async () => {
                        const welcomeText = "Hi! I'm Clio, your Local Autonomous Responsive Agent! I'm fully loaded and ready whenever you are!";
                        if (window.appendMessage) window.appendMessage('clio', welcomeText + " 💖");

                        // Trigger the wave animation instead of playing audio
                        setVTuberEmotion('wave');
                        if (window.setLiveEmotion) window.setLiveEmotion('happy');
                        
                        setTimeout(() => {
                            setVTuberEmotion('neutral');
                            if (window.setLiveEmotion) window.setLiveEmotion('neutral');
                        }, 3000);
                    }, 5000);
                    
                    // Clean up blob URL memory
                    if (modelUrl.startsWith('blob:')) {
                        URL.revokeObjectURL(modelUrl);
                    }
                }
            },
            (progress) => {
                const percentage = Math.round((progress.loaded / progress.total) * 100);
                console.log(`Loading Avatar Assets: ${percentage}%`);
            },
            (error) => {
                console.error('Failed to load VRM:', error);
            }
        );
    });

    // Eye Movement Variables
        let targetEyeX = 0;
        let targetEyeY = 0;
        let currentEyeX = 0;
        let currentEyeY = 0;
        let nextEyeMoveTime = 0;

        // Animation Loop
        const clock = new THREE.Clock();
        function animate() {
            requestAnimationFrame(animate);
            const delta = clock.getDelta();
            
            // Update VRM
            if (currentVrm) {
                const time = clock.elapsedTime;
                
                // Sleep Tracker (prevent sleep if she is actively vibing to music)
                if (window.isVibing && (isSleeping || isYawning)) {
                    resetActivityTimer(); // Wake up immediately if she starts vibing
                }
                
                let idleTime = Date.now() - lastActivityTime;
                
                // Yawn after 4 minutes idle, sleep after 5 minutes
                if (!isTalking && !window.isVibing && idleTime > 240000 && idleTime < 300000 && !isYawning) {
                    if (Math.random() < 0.005) {
                        isYawning = true;
                        setVTuberEmotion('yawn');
                        targetExpressions['aa'] = 0.8;
                        targetExpressions['blink'] = 0.7;
                    }
                }

                if (!isTalking && !window.isVibing && idleTime > 300000 && !isSleeping) {
                    isSleeping = true;
                    isYawning = false;
                    setVTuberEmotion('sleep');
                    if (currentVrm.expressionManager) {
                        targetExpressions['aa'] = 0.0;
                        targetExpressions['blink'] = 1.0;
                        isBlinking = true;
                    }
                }
                
                // Enforce Pose Targets via Lerp (fixes T-pose snap)
                if (currentVrm.humanoid && typeof targetPose !== 'undefined') {
                    const h = currentVrm.humanoid;
                    // Properly time-corrected lerp to prevent overshoot on low framerates
                    const lerpSpeed = 1.0 - Math.exp(-3.5 * delta);
                    
                    const bonesMap = {
                        'head': { target: targetPose.head, current: currentPose.head },
                        'neck': { target: targetPose.neck, current: currentPose.neck },
                        'spine': { target: targetPose.spine, current: currentPose.spine },
                        'leftUpperArm': { target: targetPose.leftArm, current: currentPose.leftArm },
                        'rightUpperArm': { target: targetPose.rightArm, current: currentPose.rightArm },
                        'leftLowerArm': { target: targetPose.leftLowerArm, current: currentPose.leftLowerArm },
                        'rightLowerArm': { target: targetPose.rightLowerArm, current: currentPose.rightLowerArm },
                        'leftHand': { target: targetPose.leftHand, current: currentPose.leftHand },
                        'rightHand': { target: targetPose.rightHand, current: currentPose.rightHand },
                        'leftUpperLeg': { target: targetPose.leftUpperLeg, current: currentPose.leftUpperLeg },
                        'rightUpperLeg': { target: targetPose.rightUpperLeg, current: currentPose.rightUpperLeg },
                        'leftLowerLeg': { target: targetPose.leftLowerLeg, current: currentPose.leftLowerLeg },
                        'rightLowerLeg': { target: targetPose.rightLowerLeg, current: currentPose.rightLowerLeg },
                        'leftFoot': { target: targetPose.leftFoot, current: currentPose.leftFoot },
                        'rightFoot': { target: targetPose.rightFoot, current: currentPose.rightFoot },
                        'leftToes': { target: targetPose.leftToes, current: currentPose.leftToes },
                        'rightToes': { target: targetPose.rightToes, current: currentPose.rightToes }
                    };
                    
                    for (const [boneName, state] of Object.entries(bonesMap)) {
                        // Lerp the base pose state
                        state.current.x = THREE.MathUtils.lerp(state.current.x, state.target.x, lerpSpeed);
                        state.current.y = THREE.MathUtils.lerp(state.current.y, state.target.y, lerpSpeed);
                        state.current.z = THREE.MathUtils.lerp(state.current.z, state.target.z, lerpSpeed);
                        
                        // Apply the base pose to the bones (this resets any procedural += from the previous frame!)
                        const bone = h.getNormalizedBoneNode(boneName);
                        if (bone) {
                            bone.rotation.set(state.current.x, state.current.y, state.current.z);
                        }
                    }
                    
                    // --- Interactive Cursor Overrides ---
                    if (petTimer > 0) {
                        petTimer -= delta;
                        wasPetting = true;
                        if (currentVrm.expressionManager) {
                            targetExpressions['happy'] = 1.0;
                            
                            // Make her tilt head into the pet
                            const head = h.getNormalizedBoneNode('head');
                            if (head) {
                                head.rotation.x += -0.1; // look up slightly
                                head.rotation.z += Math.sin(time * 8) * 0.05; // wiggle with the petting
                            }
                        }
                    } else if (wasPetting) {
                        wasPetting = false;
                        targetExpressions['happy'] = 0.0;
                        if (window.setVTuberEmotion) {
                            window.setVTuberEmotion('neutral');
                        }
                    }

                    if (isDraggingHand && draggedHand) {
                        // Simple FK to point arm toward mouseWorldPos
                        const armBoneName = draggedHand === 'left' ? 'leftUpperArm' : 'rightUpperArm';
                        const lowerArmBoneName = draggedHand === 'left' ? 'leftLowerArm' : 'rightLowerArm';
                        
                        const arm = h.getNormalizedBoneNode(armBoneName);
                        const lowerArm = h.getNormalizedBoneNode(lowerArmBoneName);
                        
                        if (arm && lowerArm) {
                            // 1. Fix ReferenceError: Calculate exact shoulder position in 3D space
                            const shoulderPos = new THREE.Vector3();
                            arm.getWorldPosition(shoulderPos);
                            
                            // --- Kinematic Torso Collision Cylinder ---
                            // Get the spine position to use as the center of our collision cylinder
                            const spine = h.getNormalizedBoneNode('spine');
                            const spinePos = new THREE.Vector3();
                            if (spine) {
                                spine.getWorldPosition(spinePos);
                            } else {
                                spinePos.set(0, 1.0, 0); // fallback
                            }
                            
                            const torsoRadius = 0.24; // Approximate width/depth of the chest
                            
                            // Calculate screen-space (XY plane) distance from spine center to the mouse
                            const dx = mouseWorldPos.x - spinePos.x;
                            const dy = mouseWorldPos.y - spinePos.y;
                            const distFromSpine = Math.sqrt(dx * dx + dy * dy);
                            
                            // If the mouse is pulled *inside* the 2D boundary, push it out to the surface edge!
                            if (distFromSpine < torsoRadius && distFromSpine > 0.001) {
                                // Normalize the direction vector
                                const nx = dx / distFromSpine;
                                const ny = dy / distFromSpine;
                                
                                // Push the mouseWorldPos exactly to the edge of the radius in 2D
                                mouseWorldPos.x = spinePos.x + (nx * torsoRadius);
                                mouseWorldPos.y = spinePos.y + (ny * torsoRadius);
                            }
                            
                            // Additionally, prevent arms from crossing too far past the center chest
                            // to prevent unnatural shoulder twisting
                            if (draggedHand === 'left' && mouseWorldPos.x < 0.05) mouseWorldPos.x = 0.05;
                            if (draggedHand === 'right' && mouseWorldPos.x > -0.05) mouseWorldPos.x = -0.05;
                            // --- 2D Trigonometric Tracking ---
                            // Calculate the 2D angle from the shoulder to the mouse cursor on the screen
                            // Math.atan2 takes (y, x). ThreeJS Y is up, X is right.
                            const dxAngle = mouseWorldPos.x - shoulderPos.x;
                            const dyAngle = mouseWorldPos.y - shoulderPos.y;
                            let angle = Math.atan2(dyAngle, dxAngle);
                            
                            // Reset any 3D twist that might have been applied before
                            arm.rotation.set(0, 0, 0);
                            
                            // Apply pure 2D rotation around the local Z axis
                            // The left arm points +X in T-pose, right arm points -X.
                            if (draggedHand === 'left') {
                                // For left arm (screen right), angle 0 is straight out right.
                                arm.rotation.z = angle;
                            } else {
                                // For right arm (screen left), the arm naturally points left (-X).
                                // Math.PI flips it to align correctly with atan2 logic.
                                arm.rotation.z = angle + Math.PI;
                            }
                            
                            // 3. Natural Elbow Bending (Pure 2D)
                            // Calculate how far the mouse is from the shoulder (2D distance)
                            const dist = Math.sqrt(dxAngle * dxAngle + dyAngle * dyAngle);
                            const maxDist = 0.40; // Approximate fully extended arm length (2D projection)
                            const bendRatio = Math.max(0, 1.0 - (dist / maxDist));
                            let elbowBend = bendRatio * 2.2; // Max bend when hand is pulled close to body
                            
                            // Apply natural elbow bend purely on local Z axis
                            lowerArm.rotation.set(0, 0, draggedHand === 'left' ? -elbowBend : elbowBend);
                            
                            // Keep wrist totally stiff and neutral to prevent ANY mesh tearing
                            const handBoneName = draggedHand === 'left' ? 'leftHand' : 'rightHand';
                            const hand = h.getNormalizedBoneNode(handBoneName);
                            if (hand) hand.rotation.set(0, 0, 0);
                        }
                    }

                    // Procedural Waving Animation
                    if (window.isWaving) {
                        const elapsed = (Date.now() - window.waveStartTime) / 1000;
                        if (elapsed < 2.5) { // Wave for 2.5 seconds
                            const rightLowerArm = h.getNormalizedBoneNode('rightLowerArm');
                            const rightHandBone = h.getNormalizedBoneNode('rightHand');
                            if (rightLowerArm) {
                                // Natural human wave: pivot from the elbow (windshield wiper motion)
                                rightLowerArm.rotation.x += Math.sin(elapsed * 12) * 0.4;
                            }
                            if (rightHandBone) {
                                // Slight wrist sway following the forearm
                                rightHandBone.rotation.z += Math.sin(elapsed * 12 - 0.5) * 0.2;
                            }
                        } else {
                            window.isWaving = false;
                            setVTuberEmotion('neutral');
                        }
                    }
                    
                    // Lerp Finger Curls
                    const fingers = ['Thumb', 'Index', 'Middle', 'Ring', 'Little'];
                    const joints = ['Proximal', 'Intermediate', 'Distal'];
                    
                    ['left', 'right'].forEach(side => {
                        const prefix = side === 'left' ? 'left' : 'right';
                        const targetCurls = side === 'left' ? targetPose.leftFingerCurls : targetPose.rightFingerCurls;
                        
                        fingers.forEach(finger => {
                            // Add slight procedural finger wiggle based on time to keep hands looking alive
                            const wiggle = Math.sin(time * 2.0 + (finger === 'Index' ? 1 : (finger === 'Thumb' ? 2 : 0))) * 0.05;
                            const targetCurl = (targetCurls[finger] || 0) + wiggle;
                            
                            currentFingerCurls[side][finger] = THREE.MathUtils.lerp(currentFingerCurls[side][finger] || 0, targetCurl, lerpSpeed);
                            const curlAmount = currentFingerCurls[side][finger];
                            
                            joints.forEach(joint => {
                                const bone = h.getNormalizedBoneNode(`${prefix}${finger}${joint}`);
                                if (bone) {
                                    if (finger === 'Thumb') {
                                        bone.rotation.set(0, side === 'left' ? curlAmount : -curlAmount, 0);
                                    } else {
                                        bone.rotation.set(0, 0, side === 'left' ? curlAmount : -curlAmount);
                                    }
                                }
                            });
                        });
                    });
                    
                    // --- Audio Analyser Lip Sync (FFT) ---
                    if (isTalking && audioAnalyser && audioDataArray) {
                        audioAnalyser.getByteFrequencyData(audioDataArray);
                        // Calculate average volume in the speech frequency range
                        let sum = 0;
                        for (let i = 0; i < audioDataArray.length; i++) {
                            sum += audioDataArray[i];
                        }
                        let average = sum / audioDataArray.length;
                        
                        // Map average (0-255) to a 0.0 - 1.0 range, with a threshold and multiplier
                        let mouthOpenness = Math.max(0, (average - 15) / 100.0);
                        mouthOpenness = Math.min(1.0, mouthOpenness * 1.6); // Boost
                        
                        // Occasionally swap phonemes based on time so it's not just 'aa'
                        const phonemes = ['aa', 'oh', 'ih'];
                        // Swap phoneme roughly every 0.125s (8 times a sec) based on time
                        const activePhoneme = phonemes[Math.floor(time * 8) % phonemes.length]; 
                        
                        // Clear others
                        ['aa', 'ih', 'ou', 'ee', 'oh'].forEach(shape => targetExpressions[shape] = 0.0);
                        
                        // Set the active one smoothly
                        if (mouthOpenness > 0.05) {
                            targetExpressions[activePhoneme] = mouthOpenness;
                        } else if (targetExpressions['happy'] > 0.5) {
                            targetExpressions['aa'] = 0.25; // Maintain base smile during pauses in speech
                        }
                    }
                    
                    // Lerp Expressions (Facial Animations)
                    if (currentVrm.expressionManager) {
                        for (const [expr, targetVal] of Object.entries(targetExpressions)) {
                            // Blinking and lipsync are fast, emotions are slower
                            const speed = (expr === 'blink' || ['aa', 'ih', 'ou', 'ee', 'oh'].includes(expr)) ? 25.0 : 5.0;
                            const exprLerpSpeed = 1.0 - Math.exp(-speed * delta);
                            currentExpressions[expr] = THREE.MathUtils.lerp(currentExpressions[expr] || 0, targetVal, exprLerpSpeed);
                            currentVrm.expressionManager.setValue(expr, currentExpressions[expr]);
                        }
                        currentVrm.expressionManager.update();
                    }
                }

                // Human-like Eye Movement & Head Tracking (Saccades + Drift)
                if (currentVrm.humanoid) {
                    const h = currentVrm.humanoid;
                    if (!isSleeping) {
                        // If mouse hasn't moved recently, look away and wander
                        if (Date.now() > nextMouseCheckTime) {
                            isTrackingMouse = false;
                        }
                    } else {
                        isTrackingMouse = false;
                    }

                    if (time > nextEyeMoveTime && !isSleeping) {
                        if (isTrackingMouse) {
                            // Follow the mouse cursor smoothly (negative multiplier so she looks AT it)
                            targetEyeX = mousePos.y * -0.15; // pitch up/down
                            targetEyeY = mousePos.x * -0.3;  // yaw left/right
                            
                            // Tiny micro-saccades while tracking (so it doesn't look robotic)
                            targetEyeX += (Math.random() - 0.5) * 0.01;
                            targetEyeY += (Math.random() - 0.5) * 0.015;
                            
                            nextEyeMoveTime = time + 0.15 + Math.random() * 0.2; // update frequently
                        } else {
                            // Standard wandering saccades (90% chance to look at the user / center)
                            const roll = Math.random();
                            
                            if (roll > 0.90) {
                                // Macro-saccade: looking away at something (10%)
                                targetEyeX = (Math.random() - 0.5) * 0.12;
                                targetEyeY = (Math.random() - 0.5) * 0.35;
                                // Gaze-shift blink (humans do this involuntarily)
                                if (currentVrm.expressionManager) {
                                    targetExpressions['blink'] = 1.0;
                                    setTimeout(() => targetExpressions['blink'] = 0.0, 120);
                                }
                                nextEyeMoveTime = time + 2.0 + Math.random() * 3.0;
                            } else {
                                // 90% chance to look straight ahead (at the user)
                                // Tiny micro-saccades centered on 0 so it looks alive but focused
                                targetEyeX = (Math.random() - 0.5) * 0.02;
                                targetEyeY = (Math.random() - 0.5) * 0.02;
                                nextEyeMoveTime = time + 0.5 + Math.random() * 1.5;
                            }
                            
                            // When talking, bias eyes toward center (looking at the user)
                            if (isTalking) {
                                targetEyeX *= 0.4;
                                targetEyeY *= 0.4;
                            }
                        }
                    } else if (isSleeping) {
                        // Slow dream drift under closed lids
                        targetEyeX = Math.sin(time * 0.3) * 0.02;
                        targetEyeY = Math.cos(time * 0.2) * 0.02;
                    }
                    
                    // Slow drift overlay (eyes are never perfectly still, even when staring)
                    const driftX = Math.sin(time * 0.7) * 0.005;
                    const driftY = Math.cos(time * 0.5) * 0.008;
                    
                    // Framerate-independent lerp to prevent head twisting/overshooting when swinging the mouse
                    const eyeLerpSpeed = 1.0 - Math.exp(-18.0 * delta);
                    currentEyeX = THREE.MathUtils.lerp(currentEyeX, targetEyeX + driftX, eyeLerpSpeed);
                    currentEyeY = THREE.MathUtils.lerp(currentEyeY, targetEyeY + driftY, eyeLerpSpeed);
                    
                    const leftEye = h.getNormalizedBoneNode('leftEye');
                    const rightEye = h.getNormalizedBoneNode('rightEye');
                    const headBone = h.getNormalizedBoneNode('head');
                    const neckBone = h.getNormalizedBoneNode('neck');
                    
                    if (leftEye) {
                        leftEye.rotation.x = currentEyeX;
                        leftEye.rotation.y = currentEyeY;
                    }
                    if (rightEye) {
                        rightEye.rotation.x = currentEyeX;
                        rightEye.rotation.y = currentEyeY;
                    }
                    
                    // Head subtly follows the eyes (eye-head coupling, delayed)
                    if (headBone && !isSleeping) {
                        headBone.rotation.x += currentEyeX * 0.25;
                        headBone.rotation.y += currentEyeY * 0.35;
                    }
                    if (neckBone && !isSleeping) {
                        neckBone.rotation.x += currentEyeX * 0.08;
                        neckBone.rotation.y += currentEyeY * 0.12;
                    }
                }

                if (window.isVibing && currentVrm.humanoid) {
                    // Slow, chill lofi vibe (approx 60-70 BPM)
                    const slowTime = time * Math.PI * 1.2;
                    const bounce = Math.abs(Math.sin(slowTime)); 
                    const sway = Math.sin(slowTime * 0.5); 
                    const deepSway = Math.sin(slowTime * 0.25);
                    
                    const spine = currentVrm.humanoid.getNormalizedBoneNode('spine');
                    const head = currentVrm.humanoid.getNormalizedBoneNode('head');
                    const neck = currentVrm.humanoid.getNormalizedBoneNode('neck');
                    
                    if (spine) {
                        spine.rotation.x = targetPose.spine.x + (bounce * 0.05);
                        spine.rotation.z = targetPose.spine.z + (deepSway * 0.03);
                    }
                    if (neck) neck.rotation.x = targetPose.neck.x - (bounce * 0.02);
                    if (head) {
                        head.rotation.x = targetPose.head.x + (bounce * 0.03); 
                        head.rotation.y = targetPose.head.y + (deepSway * 0.05);
                        head.rotation.z = targetPose.head.z - (sway * 0.08);
                    }
                } else if (currentVrm.humanoid && isSleeping) {
                    // === SLEEPING: Full body relaxed with deep breathing ===
                    const sleepBreath = Math.sin(time * 1.2); // ~11 breaths/min
                    const h = currentVrm.humanoid;
                    
                    const spine = h.getNormalizedBoneNode('spine');
                    const head = h.getNormalizedBoneNode('head');
                    const leftArm = h.getNormalizedBoneNode('leftUpperArm');
                    const rightArm = h.getNormalizedBoneNode('rightUpperArm');
                    const leftLeg = h.getNormalizedBoneNode('leftUpperLeg');
                    const rightLeg = h.getNormalizedBoneNode('rightUpperLeg');
                    const leftKnee = h.getNormalizedBoneNode('leftLowerLeg');
                    const rightKnee = h.getNormalizedBoneNode('rightLowerLeg');
                    
                    // Deep belly breathing
                    if (spine) spine.rotation.x += (sleepBreath * 0.025);
                    
                    // Shoulders rise gently
                    if (leftArm) leftArm.rotation.z += -(sleepBreath * 0.008);
                    if (rightArm) rightArm.rotation.z += (sleepBreath * 0.008);
                    
                    // Legs slightly relaxed/bent (like standing asleep)
                    if (leftKnee) leftKnee.rotation.x += 0.03;
                    if (rightKnee) rightKnee.rotation.x += 0.05; // asymmetric = natural
                    
                    // Dream twitch (tiny head jerk)
                    if (head && Math.sin(time * 0.4) > 0.99) {
                        head.rotation.z += (Math.random() - 0.5) * 0.04;
                    }
                    // Rare leg twitch in sleep
                    if (leftLeg && Math.sin(time * 0.17) > 0.995) {
                        leftLeg.rotation.x += (Math.random() - 0.5) * 0.02;
                    }
                } else if (currentVrm.humanoid) {
                    // ============================================================
                    // FULL BODY IDLE ANIMATION — Every VRM bone, lively and cute
                    // This is NOT sleep. She looks awake, alert, and fidgety.
                    // ============================================================
                    
                    // --- Organic Procedural Noise (Human Biomechanics) ---
                    // By passing distinct prime multipliers into the noise() function, we avoid repeating metronome loops
                    const breath       = noise(time * 1.5);
                    const breathUp     = noise(time * 1.5 + 0.3) * 0.5 + 0.5; // positive only
                    const sway1        = noise(time * 0.35);
                    const sway2        = noise(time * 0.61);
                    
                    // Contrapposto (Weight Shift): humans stand on one leg at a time.
                    // This creates asymmetric hip/spine alignment.
                    const weightShift  = noise(time * 0.2); 
                    
                    const headDrift    = noise(time * 0.4);
                    const legShift     = noise(time * 0.3);
                    const fidget       = noise(time * 0.8);
                    const wiggle       = noise(time * 1.2);
                    
                    const h = currentVrm.humanoid;
                    
                    // --- Get ALL bones ---
                    // Core
                    const hips       = h.getNormalizedBoneNode('hips');
                    const spine      = h.getNormalizedBoneNode('spine');
                    const chest      = h.getNormalizedBoneNode('chest');
                    const upperChest = h.getNormalizedBoneNode('upperChest');
                    const neckBone   = h.getNormalizedBoneNode('neck');
                    const headBone   = h.getNormalizedBoneNode('head');
                    const jaw        = h.getNormalizedBoneNode('jaw');
                    // Shoulders & Arms
                    const leftShoulder  = h.getNormalizedBoneNode('leftShoulder');
                    const rightShoulder = h.getNormalizedBoneNode('rightShoulder');
                    const leftArm       = h.getNormalizedBoneNode('leftUpperArm');
                    const rightArm      = h.getNormalizedBoneNode('rightUpperArm');
                    const leftLower     = h.getNormalizedBoneNode('leftLowerArm');
                    const rightLower    = h.getNormalizedBoneNode('rightLowerArm');
                    const leftHand      = h.getNormalizedBoneNode('leftHand');
                    const rightHand     = h.getNormalizedBoneNode('rightHand');
                    // Legs
                    const leftUpperLeg  = h.getNormalizedBoneNode('leftUpperLeg');
                    const rightUpperLeg = h.getNormalizedBoneNode('rightUpperLeg');
                    const leftLowerLeg  = h.getNormalizedBoneNode('leftLowerLeg');
                    const rightLowerLeg = h.getNormalizedBoneNode('rightLowerLeg');
                    const leftFoot      = h.getNormalizedBoneNode('leftFoot');
                    const rightFoot     = h.getNormalizedBoneNode('rightFoot');
                    const leftToes      = h.getNormalizedBoneNode('leftToes');
                    const rightToes     = h.getNormalizedBoneNode('rightToes');
                    
                    // === HIPS: Center of mass sway ===
                    if (hips) {
                        hips.rotation.y = (sway1 * 0.025) + (sway2 * 0.012);
                        hips.rotation.z = weightShift * 0.018;
                        hips.rotation.x = breath * 0.004;
                    }
                    
                    // === SPINE: Breathing + counter-sway ===
                    if (spine) {
                        spine.rotation.x += (breath * 0.014);
                        spine.rotation.y += -(sway1 * 0.022);
                        spine.rotation.z += -(weightShift * 0.016);
                    }
                    
                    // === CHEST: Secondary breath wave ===
                    if (chest) {
                        chest.rotation.x = breath * 0.009;
                        chest.rotation.z = sway2 * 0.005;
                    }
                    
                    // === UPPER CHEST: Tertiary subtle breath ===
                    if (upperChest) {
                        upperChest.rotation.x = breath * 0.005;
                    }
                    
                    // === NECK: Slight bobble ===
                    if (neckBone) {
                        neckBone.rotation.y += sway2 * 0.012;
                        neckBone.rotation.x += fidget * 0.005;
                    }
                    
                    // === HEAD: Lively drift + cute tilts ===
                    if (headBone) {
                        headBone.rotation.z += headDrift * 0.018; // cute head tilts
                        headBone.rotation.x += noise(time * 0.41) * 0.008; // tiny nods
                    }
                    
                    // (Jaw bone manual rotation has been completely removed to prevent creepy mesh deformation. 
                    // VTuber mouths should strictly use ExpressionManager BlendShapes for lip sync and idle.)
                    
                    // === SHOULDERS: Rise on inhale + slight roll ===
                    if (leftShoulder) {
                        leftShoulder.rotation.z = -(breathUp * 0.014);
                        leftShoulder.rotation.y = sway1 * 0.005;
                    }
                    if (rightShoulder) {
                        rightShoulder.rotation.z = (breathUp * 0.014);
                        rightShoulder.rotation.y = -sway1 * 0.005;
                    }
                    
                    // === UPPER ARMS: Gentle pendulum + breath flare ===
                    if (leftArm) {
                        leftArm.rotation.x += (sway1 * 0.018) + 0.02;
                        leftArm.rotation.z += (breath * 0.01);
                        leftArm.rotation.y += fidget * 0.008;
                    }
                    if (rightArm) {
                        rightArm.rotation.x += -(sway1 * 0.018) + 0.02;
                        rightArm.rotation.z += -(breath * 0.01);
                        rightArm.rotation.y += -fidget * 0.008;
                    }
                    
                    // === FOREARMS: Sway + fidget ===
                    if (leftLower) {
                        leftLower.rotation.x += -(breath * 0.012);
                        leftLower.rotation.y += fidget * 0.006;
                    }
                    if (rightLower) {
                        rightLower.rotation.x += -(breath * 0.012);
                        rightLower.rotation.y += -fidget * 0.006;
                    }
                    
                    // === HANDS: Wrist roll + wiggle (alive, not stiff) ===
                    if (leftHand) {
                        leftHand.rotation.x += (wiggle * 0.015);
                        leftHand.rotation.z += noise(time * 0.83) * 0.01;
                    }
                    if (rightHand) {
                        rightHand.rotation.x += (wiggle * 0.015);
                        rightHand.rotation.z += -noise(time * 0.83) * 0.01;
                    }
                    
                    // === UPPER LEGS: Weight shifting ===
                    if (leftUpperLeg) {
                        leftUpperLeg.rotation.x += legShift * 0.012;
                        leftUpperLeg.rotation.z += weightShift * 0.01;
                    }
                    if (rightUpperLeg) {
                        rightUpperLeg.rotation.x += -legShift * 0.012;
                        rightUpperLeg.rotation.z += -weightShift * 0.01;
                    }
                    
                    // === KNEES: Alternating micro-bend (weight shift) ===
                    if (leftLowerLeg) {
                        leftLowerLeg.rotation.x += Math.max(0, weightShift) * 0.018;
                    }
                    if (rightLowerLeg) {
                        rightLowerLeg.rotation.x += Math.max(0, -weightShift) * 0.018;
                    }
                    
                    // === FEET: Ankle tilt + subtle toe curl ===
                    if (leftFoot) {
                        leftFoot.rotation.x += -weightShift * 0.006;
                        leftFoot.rotation.z += sway1 * 0.004;
                    }
                    if (rightFoot) {
                        rightFoot.rotation.x += weightShift * 0.006;
                        rightFoot.rotation.z += -sway1 * 0.004;
                    }
                    
                    // === TOES: Grip/release with weight ===
                    if (leftToes) {
                        leftToes.rotation.x += Math.max(0, weightShift) * 0.01;
                    }
                    if (rightToes) {
                        rightToes.rotation.x += Math.max(0, -weightShift) * 0.01;
                    }
                }
                
                // --- Gentle Air/Wind Effect for Hair and Clothes (Optimized) ---
                if (currentVrm.springBoneManager) {
                    const cursorForce = new THREE.Vector3();
                    let globalStrength = 0;
                    let applyWind = false;
                    
                    if (isMouseInContainer && currentVrm.humanoid) {
                        const spine = currentVrm.humanoid.getNormalizedBoneNode('spine');
                        if (spine) {
                            const spinePos = new THREE.Vector3();
                            spine.getWorldPosition(spinePos);
                            
                            const dx = spinePos.x - cursorHoverWorldPos.x;
                            const dy = spinePos.y - cursorHoverWorldPos.y;
                            const distSq = dx*dx + dy*dy;
                            
                            // Check if cursor is anywhere near the character's upper body
                            if (distSq < 0.49 && distSq > 0.0001) {
                                applyWind = true;
                                const dist = Math.sqrt(distSq);
                                globalStrength = (1.0 - (dist / 0.7)) * 0.4;
                                cursorForce.set(dx / dist, (dy / dist) + 0.5, 0).normalize().multiplyScalar(globalStrength);
                            }
                        }
                    }
                    
                    const baseGravity = new THREE.Vector3(0, -1, 0);
                    const blendedForce = applyWind ? baseGravity.clone().add(cursorForce).normalize() : baseGravity;
                    
                    currentVrm.springBoneManager.springBones.forEach(springBone => {
                        const name = (springBone.bone.name || '').toLowerCase();
                        
                        // Never apply air effect to skirt (only standard gravity / body animation)
                        if (name.includes('skirt') || name.includes('dress') || name.includes('leg') || name.includes('foot')) {
                            return; 
                        }
                        
                        let target = springBone;
                        if (target.settings && target.settings.gravityDir !== undefined) {
                            target = target.settings;
                        }
                        
                        if (target.gravityDir && target.gravityPower !== undefined) {
                            if (applyWind) {
                                target.gravityDir.lerp(blendedForce, 0.15);
                                target.gravityPower = THREE.MathUtils.lerp(target.gravityPower, 1.2, 0.15);
                            } else {
                                target.gravityDir.lerp(baseGravity, 0.05);
                                target.gravityPower = THREE.MathUtils.lerp(target.gravityPower, 1.0, 0.05);
                            }
                        }
                    });
                }
                
                // Update VRM Physics LAST, after all manual bone overrides! 
                // This fixes the "spring/rubber-band" effect on hair and clothes.
                currentVrm.update(delta);
            }

            renderer.render(scene, camera);
        }
        animate();
        
        vrmSceneInitialized = true;
        console.log("VTuber Three.js Engine Initialized");
    }
