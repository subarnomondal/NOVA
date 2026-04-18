import os
import sys

def test_transcribe():
    wav_path = "stream_23051b.wav"
    if not os.path.exists(os.path.join("temp", wav_path)):
        print("WAV file not found!")
        return

    full_path = os.path.join("temp", wav_path)
    
    try:
        from faster_whisper import WhisperModel
        print("Loading model...")
        model = WhisperModel("base.en", device="cpu", compute_type="int8")
        print("Transcribing...")
        segments, info = model.transcribe(full_path, beam_size=1)
        text = " ".join([s.text for s in segments]).strip()
        print(f"Transcript: {text}")
    except Exception as e:
        print(f"Error during transcription: {e}")

if __name__ == "__main__":
    test_transcribe()
