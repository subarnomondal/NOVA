// Add dynamic welcome message based on time of day
function getGreeting() {
    const hour = new Date().getHours();
    if (hour < 12) return "Good morning";
    if (hour < 17) return "Good afternoon";
    if (hour < 21) return "Good evening";
    return "Good night";
}

// Generate and play welcome sound
function playWelcomeSound() {
    try {
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const now = audioContext.currentTime;

        // Create a pleasant startup chime (C major chord arpeggio)
        const notes = [
            { freq: 523.25, time: 0.0, duration: 0.3 },    // C5
            { freq: 659.25, time: 0.15, duration: 0.3 },   // E5
            { freq: 783.99, time: 0.3, duration: 0.5 }     // G5
        ];

        notes.forEach(note => {
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();

            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);

            oscillator.frequency.value = note.freq;
            oscillator.type = 'sine';

            // Envelope for smooth sound
            gainNode.gain.setValueAtTime(0, now + note.time);
            gainNode.gain.linearRampToValueAtTime(0.15, now + note.time + 0.05);
            gainNode.gain.exponentialRampToValueAtTime(0.01, now + note.time + note.duration);

            oscillator.start(now + note.time);
            oscillator.stop(now + note.time + note.duration);
        });

        console.log("🔔 Welcome sound played!");
    } catch (e) {
        console.log("Could not play welcome sound:", e);
    }
}

// Update welcome message on page load
window.addEventListener('DOMContentLoaded', () => {
    const welcomeScreen = document.getElementById('welcome');
    if (welcomeScreen) {
        const greeting = getGreeting();
        const h1 = welcomeScreen.querySelector('h1');
        const p = welcomeScreen.querySelector('p');

        // Personalized greeting
        h1.textContent = `${greeting}, Rivu! 🙏`;
        p.textContent = "I'm Nova, your AI assistant. Ready to help you today!";
    }

    // Play welcome sound after a short delay
    setTimeout(() => {
        playWelcomeSound();
    }, 500);
});
