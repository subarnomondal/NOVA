import asyncio
import os
import edge_tts
import pygame
import time

async def test_voice():
    print("🔊 Testing Nova's Neural Voice...")
    
    # 1. Generate audio
    text = "Hi there! I am Nova, Ri-vu's personal AI assistant. This is my premium neural voice. Do I sound better now, Ri-vu?"
    voice = "en-US-AvaNeural"
    
    print(f"Generating speech with {voice}...")
    communicate = edge_tts.Communicate(text, voice)
    
    tmp_path = "voice_test_temp.mp3"
    await communicate.save(tmp_path)
    
    # 2. Play audio
    try:
        print("Initializing playback...")
        pygame.mixer.init()
        pygame.mixer.music.load(tmp_path)
        pygame.mixer.music.play()
        
        print("Playing... Can you hear me?")
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
            
        pygame.mixer.music.unload()
        print("✅ Playback finished.")
    except Exception as e:
        print(f"❌ Playback Error: {e}")
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

async def test_recording():
    print("\n🎤 Testing System Audio Recording (Stereo Mix)...")
    print("Please play some music or make a sound on your PC now.")
    
    import sounddevice as sd
    import numpy as np
    
    # Try to find Stereo Mix
    device_idx = None
    for i, d in enumerate(sd.query_devices()):
        if "Stereo Mix" in d['name'] and d['max_input_channels'] > 0:
            device_idx = i
            break
    
    if device_idx is None:
        print("❌ Could NOT find 'Stereo Mix' device. Nova won't be able to hear the caller.")
        print("   Please enable it in Windows Sound Settings.")
        return

    print(f"✅ Found Stereo Mix at index {device_idx}. Recording for 5 seconds...")
    duration = 5
    fs = 16000
    recording = sd.rec(int(duration * fs), samplerate=fs, channels=1, device=device_idx)
    sd.wait()
    
    rms = np.sqrt(np.mean(recording**2))
    max_val = np.max(np.abs(recording))
    print(f"📊 Recording finished. Room Volume (RMS): {rms:.5f}, Peak: {max_val:.5f}")
    
    if max_val < 0.001:
        print("⚠️ Warning: Extremely low volume detected. Stereo Mix might be muted or not picking up sound.")
    else:
        print("🎉 Success! Stereo Mix is picking up sound.")

async def main():
    await test_voice()
    await test_recording()

if __name__ == "__main__":
    asyncio.run(main())
