import os
import logging
import traceback
from google.cloud import speech_v1p1beta1 as speech
import asyncio

logger = logging.getLogger(__name__)

class GoogleSpeechService:
    """
    Сервис для транскрипции аудио с помощью Google Cloud Speech-to-Text
    """
    
    def __init__(self):
        self.client = None
        self.language_code = "ru-RU"
        self.sample_rate_hertz = 16000
        self.encoding = speech.RecognitionConfig.AudioEncoding.LINEAR16
        self.credentials_path = os.path.abspath("backend/audioinsight-460812-a14416636db4.json")

    def _get_client(self):
        if not self.client:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = self.credentials_path
            self.client = speech.SpeechClient()
        return self.client

    async def transcribe_audio(self, file_path: str) -> dict:
        try:
            client = self._get_client()
            with open(file_path, "rb") as audio_file:
                content = audio_file.read()
            audio = speech.RecognitionAudio(content=content)
            config = speech.RecognitionConfig(
                encoding=self.encoding,
                sample_rate_hertz=self.sample_rate_hertz,
                language_code=self.language_code,
                enable_automatic_punctuation=True,
                audio_channel_count=1,
                enable_speaker_diarization=True,
                diarization_speaker_count=2,
            )
            operation = client.long_running_recognize(config=config, audio=audio)
            logger.info(f"⏳ Waiting for Google Speech-to-Text operation to complete...")
            response = operation.result(timeout=180)
            transcript = ""
            confidence = 0.0
            for result in response.results:
                alternative = result.alternatives[0]
                transcript += alternative.transcript + " "
                confidence = max(confidence, alternative.confidence)
            transcript = transcript.strip()
            logger.info(f"✅ Transcription complete. Confidence: {confidence}")
            return {
                "text": transcript,
                "duration": 0,  # Можно добавить расчет длительности при необходимости
                "language": self.language_code,
                "participant_count": 2,
                "confidence": confidence
            }
        except Exception as e:
            logger.error(f"❌ Ошибка транскрипции: {str(e)}")
            logger.error(traceback.format_exc())
            return {
                "text": "Ошибка транскрипции: " + str(e),
                "duration": 0,
                "language": self.language_code,
                "participant_count": 0,
                "confidence": 0.0
            }

# Глобальный экземпляр сервиса
speech_service = GoogleSpeechService()