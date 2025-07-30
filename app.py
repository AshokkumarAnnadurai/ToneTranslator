import streamlit as st
import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wavfile
import speech_recognition as sr
import pyttsx3
import tempfile
import os
import io
from deep_translator import GoogleTranslator
from typing import Optional

# Streamlit page config
st.set_page_config(page_title="AI Voice Tone Converter", page_icon="🎤", layout="wide")

# Session state
for key in ['recording', 'audio_data', 'transcribed_text', 'generated_responses', 'input_language']:
    if key not in st.session_state:
        st.session_state[key] = None if key not in ['recording', 'input_language'] else (False if key == 'recording' else 'ta')


class VoiceRecorder:
    def __init__(self):
        self.rate = 44100
        self.duration = 30  # seconds
        self.channels = 1
        self.silence_threshold = 100
        self.silence_duration = 2  # seconds

    def record_audio(self) -> Optional[bytes]:
        st.info("🎤 Recording... Speak now!")
        recording = sd.rec(int(self.rate * self.duration), samplerate=self.rate, channels=self.channels, dtype='int16')
        sd.wait()

        audio_array = np.abs(recording).flatten()
        silent_frames = np.where(audio_array < self.silence_threshold)[0]
        if len(silent_frames) > self.rate * self.silence_duration:
            st.info("🔇 Silence detected. Stopping early...")

        buf = io.BytesIO()
        wavfile.write(buf, self.rate, recording)
        return buf.getvalue()


class SpeechProcessor:
    def __init__(self):
        self.recognizer = sr.Recognizer()

    def transcribe_audio(self, audio_data: bytes, lang_code: str = "ta-IN") -> str:
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_file_path = temp_file.name
            with sr.AudioFile(temp_file_path) as source:
                audio = self.recognizer.record(source)
                text = self.recognizer.recognize_google(audio, language=lang_code)
            os.remove(temp_file_path)
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

    # Language options
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

    col1, col2 = st.columns([1, 2])
    with col1:
        if st.button("🎙️ Start Recording", disabled=st.session_state.recording):
            st.session_state.recording = True
            recorder = VoiceRecorder()
            audio_data = recorder.record_audio()

            if audio_data:
                st.success("✅ Recording completed!")
                st.session_state.audio_data = audio_data

                with st.spinner("Transcribing..."):
                    processor = SpeechProcessor()
                    raw_text = processor.transcribe_audio(audio_data, lang_code=f"{st.session_state.input_language}-IN")

                with st.spinner("Translating to English..."):
                    translator = TranslatorHelper(source_lang=st.session_state.input_language)
                    translated = translator.translate_to_english(raw_text)

                st.session_state.transcribed_text = translated

                with st.spinner("Generating tones..."):
                    converter = FreeToneConverter()
                    st.session_state.generated_responses = converter.generate_with_simple_prompts(translated)
            else:
                st.error("Recording failed.")
            st.session_state.recording = False

        if st.session_state.transcribed_text:
            st.subheader("📝 Transcribed & Translated Text")
            st.info(st.session_state.transcribed_text)

    with col2:
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
            st.info("Start recording to generate tone responses.")

    st.markdown("---")
    st.markdown("""
        <div style='text-align: center; color: #888;'>
            <p>🎉 Supports Tamil • Malayalam • Kannada • Telugu — Auto-translates to English!</p>
            <p><small>Built with ❤️ using Streamlit</small></p>
        </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
