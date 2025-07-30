import streamlit as st
from audiorecorder import audiorecorder
import speech_recognition as sr
import pyttsx3
import tempfile
import os
from deep_translator import GoogleTranslator
from typing import Optional
from io import BytesIO

# Streamlit page config
st.set_page_config(page_title="AI Voice Tone Converter", page_icon="🎤", layout="wide")

# Session state
for key in ['audio_data', 'transcribed_text', 'generated_responses', 'input_language']:
    if key not in st.session_state:
        st.session_state[key] = None if key != 'input_language' else 'ta'


class SpeechProcessor:
    def __init__(self):
        self.recognizer = sr.Recognizer()

    def transcribe_audio(self, audio_path: str, lang_code: str = "ta-IN") -> str:
        try:
            with sr.AudioFile(audio_path) as source:
                audio = self.recognizer.record(source)
                text = self.recognizer.recognize_google(audio, language=lang_code)
            return text
        except sr.UnknownValueError:
            return "Could not understand audio"
        except Exception as e:
            return f"Error processing audio: {e}"


class TranslatorHelper:
    def __init__(self, source_lang):
        self.translator = GoogleTranslator(source=source_lang, target='en')

    def translate_to_english(self, text: str) -> str:
        try:
            return self.translator.translate(text)
        except Exception as e:
            return f"Translation error: {e}"


class FreeToneConverter:
    def generate_with_simple_prompts(self, text: str) -> dict:
        return {
            "Professional": self._make_professional(text),
            "Formal": self._make_formal(text),
            "Friendly": self._make_friendly(text)
        }

    def _make_professional(self, text: str) -> str:
        replacements = {"i'm": "I am", "don't": "do not", "can't": "cannot", "yeah": "yes"}
        result = text.lower()
        for k, v in replacements.items():
            result = result.replace(k, v)
        result = result.capitalize()
        if not result.endswith('.'):
            result += '.'
        return f"I would like to inform you that {result}" if len(result) > 20 else result

    def _make_formal(self, text: str) -> str:
        replacements = {"i'm": "I am", "don't": "do not", "can't": "cannot", "yeah": "yes"}
        result = text.lower()
        for k, v in replacements.items():
            result = result.replace(k, v)
        result = result.capitalize()
        if not result.endswith('.'):
            result += '.'
        return f"It is my understanding that {result}" if len(result) > 15 else result

    def _make_friendly(self, text: str) -> str:
        from random import choice
        starters = ["Hey there! ", "Hi! ", "Hello friend! "]
        enders = [" 😊", " Hope that helps!", " Have a great day!"]
        return choice(starters) + text + choice(enders)


class TextToSpeech:
    def __init__(self):
        self.engine = pyttsx3.init()

    def speak(self, text: str):
        try:
            self.engine.say(text)
            self.engine.runAndWait()
        except Exception as e:
            st.error(f"Text-to-speech error: {e}")


def main():
    st.title("🎤 AI Voice Tone Converter")
    st.markdown("Speak in Tamil, Malayalam, Kannada, or Telugu – get responses in English with tone adjustments!")

    lang_map = {
        "Tamil": "ta",
        "Malayalam": "ml",
        "Kannada": "kn",
        "Telugu": "te"
    }

    with st.sidebar:
        st.header("🌐 Language Selection")
        selected_lang = st.selectbox("Choose your input voice language", list(lang_map.keys()))
        st.session_state.input_language = lang_map[selected_lang]

    audio = audiorecorder("🎤 Click to record", "⏹ Stop recording")

    if len(audio) > 0:
        buffer = BytesIO()
        audio.export(buffer, format="wav")
        audio_bytes = buffer.getvalue()

        st.audio(audio_bytes, format="audio/wav")

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(audio_bytes)
            temp_path = f.name

        with st.spinner("Transcribing..."):
            processor = SpeechProcessor()
            raw_text = processor.transcribe_audio(temp_path, lang_code=f"{st.session_state.input_language}-IN")

        with st.spinner("Translating to English..."):
            translator = TranslatorHelper(source_lang=st.session_state.input_language)
            translated = translator.translate_to_english(raw_text)

        st.session_state.transcribed_text = translated

        with st.spinner("Generating tones..."):
            converter = FreeToneConverter()
            st.session_state.generated_responses = converter.generate_with_simple_prompts(translated)

        os.remove(temp_path)

    if st.session_state.transcribed_text:
        st.subheader("📝 Transcribed & Translated Text")
        st.info(st.session_state.transcribed_text)

    st.subheader("🎭 Tone Variations")
    if st.session_state.generated_responses:
        tone_icons = {
            "Professional": "💼",
            "Formal": "🎩",
            "Friendly": "😊"
        }
        tone_colors = {
            "Professional": "#e3f2fd",
            "Formal": "#f3e5f5",
            "Friendly": "#fff8e1"
        }

        for tone, response in st.session_state.generated_responses.items():
            st.markdown(
                f"""
                <div style="background-color:{tone_colors[tone]}; padding:15px; border-radius:10px; margin-bottom:10px;">
                    <h5>{tone_icons[tone]} {tone}</h5>
                    <p style="font-size: 16px;">{response}</p>
                </div>
                """, unsafe_allow_html=True
            )
            if st.button(f"🔊 Play {tone}", key=f"speak_{tone}"):
                TextToSpeech().speak(response)
    else:
        st.info("Record your voice to generate tone responses.")

    st.markdown("---")
    st.markdown("""
        <div style='text-align: center; color: #888;'>
            <p>🎉 Supports Tamil • Malayalam • Kannada • Telugu — Auto-translates to English!</p>
            <p><small>Built with ❤️ using Streamlit</small></p>
        </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
