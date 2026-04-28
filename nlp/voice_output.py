from gtts import gTTS
import re
import io

def clean_text(text):
    text = re.sub(r'[^\x00-\x7F]+', '', text)
    text = text.replace("%", " percent")
    text = text.replace("$", " dollars")
    return text

def speak(text):
    text = clean_text(text)

    # tld="co.uk" selects the UK English female voice on gTTS —
    # noticeably more natural and professional than the default US voice
    tts = gTTS(text=text, lang='en', tld='co.uk', slow=False)

    audio_bytes = io.BytesIO()
    tts.write_to_fp(audio_bytes)
    audio_bytes.seek(0)

    return audio_bytes
