import speech_recognition as sr
import io

def transcribe_voice():
    """For local/Streamlit use - direct microphone"""
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        audio = recognizer.listen(source)
    try:
        return recognizer.recognize_google(audio)
    except:
        return None

def transcribe_audio_file(audio_bytes: bytes) -> str:
    """For FastAPI use - receives audio bytes from frontend"""
    recognizer = sr.Recognizer()
    audio_file = io.BytesIO(audio_bytes)
    with sr.AudioFile(audio_file) as source:
        audio = recognizer.record(source)
    try:
        return recognizer.recognize_google(audio)
    except:
        return None