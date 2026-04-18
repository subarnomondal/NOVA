import asyncio
import os
import edge_tts
import pygame
import time

VOICES = [
    ("Michelle (Soft-spoken, gentle)", "en-US-MichelleNeural"),
    ("Emma (Young, clear)", "en-US-EmmaNeural"),
    ("Clara (Canadian, articulate)", "en-CA-ClaraNeural"),
    ("Emily (Irish, energetic)", "en-IE-EmilyNeural"),
    ("Natasha (Australian, natural)", "en-AU-NatashaNeural"),
    ("Libby (British, deeper, professional)", "en-GB-LibbyNeural")
]

async def test_voices():
    pygame.mixer.init()
    
    print("🔊 Playing Voice Samples...\n")
    
    for name, voice_id in VOICES:
        text = f"Hi, I am {name.split(' ')[0]}. This is how my voice sounds. I hope you like it!"
        print(f"Loading {name} ({voice_id})...")
        
        communicate = edge_tts.Communicate(text, voice_id)
        tmp_path = "temp_voice_sample.mp3"
        await communicate.save(tmp_path)
        
        try:
            pygame.mixer.music.load(tmp_path)
            pygame.mixer.music.play()
            
            # Wait for it to finish
            print(f"▶️ Playing {name}")
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
                
            pygame.mixer.music.unload()
            time.sleep(1) # Small pause
        except Exception as e:
            print(f"Error playing {voice_id}: {e}")
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
                
    print("\n✅ Finished playing all samples.")

if __name__ == "__main__":
    asyncio.run(test_voices())
