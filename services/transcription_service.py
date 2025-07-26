# services/transcription_service.py

from google.cloud import speech
import logging

def transcribe_audio(audio_bytes: bytes) -> str:
    """
    Transcribes the given audio bytes into text.
    It does NOT perform language detection.
    """
    client = speech.SpeechClient()
    audio = speech.RecognitionAudio(content=audio_bytes)

    # Use a simple config with a single, common language code.
    # The actual language will be detected by the LLM later.
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
        sample_rate_hertz=48000,
        language_code="en-US", # Use a base language for transcription
        enable_automatic_punctuation=True,
    )

    logging.info("Sending audio to Google STT API for transcription...")
    response = client.recognize(config=config, audio=audio)
    
    if response.results:
        return response.results[0].alternatives[0].transcript
    else:
        return "" # Return empty string if no speech is detected