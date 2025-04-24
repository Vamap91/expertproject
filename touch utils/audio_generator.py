# utils/audio_generator.py

import pyttsx3
import tempfile

def text_to_audio(text):
    engine = pyttsx3.init()
    engine.setProperty('rate', 160)
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    engine.save_to_file(text, temp_file.name)
    engine.runAndWait()
    return open(temp_file.name, "rb").read()

