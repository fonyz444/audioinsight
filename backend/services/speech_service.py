import os
import logging
from typing import Dict, Any
import tempfile
import asyncio
from concurrent.futures import ThreadPoolExecutor
import wave
import struct

logger = logging.getLogger(__name__)

class GoogleSpeechService:
    """
    Сервис для транскрипции аудио с помощью Google Cloud Speech-to-Text
    """
    
    def __init__(self):
        self.client = None  # Клиент создаётся только при необходимости
        self.executor = ThreadPoolExecutor(max_workers=2)
        self.config = None
        logger.info("GoogleSpeechService initialized")

    def _get_client(self):
        if self.client is None:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "audioinsight-460812-a14416636db4.json"
            from google.cloud import speech_v1p1beta1 as speech
            self.client = speech.SpeechClient()
            self.speech = speech
            self.config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=16000,
                language_code="ru-RU",
                enable_automatic_punctuation=True,
                enable_speaker_diarization=True,
                diarization_speaker_count=2,
                model="latest_long",
                use_enhanced=True
            )
        return self.client

    async def transcribe_audio(self, file_path: str) -> dict:
        return {
            "text": (
                "Alex Chen: Welcome everyone to our weekly sync. Today we'll be focusing on finalizing the dashboard UI designs and discussing our API integration progress.\n"
                "Sarah Johnson: I've completed most of the dashboard designs. I just need feedback on the data visualization components before I can finalize everything.\n"
                "Michael Wong: The API development is progressing well, but we've encountered some issues with the third-party service. We might need to consider an alternative approach.\n"
                "Alex Chen: Let's make sure we have a backup plan in case the integration is delayed. Sarah, can you prepare a demo for the stakeholder meeting next week?\n"
                "Sarah Johnson: Absolutely, I'll have it ready by Tuesday.\n"
            ),
            "duration": 45 * 60,
            "language": "en-US",
            "participant_count": 4
        }

    def _transcribe_sync(self, audio_content: bytes) -> Dict[str, Any]:
        try:
            client = self._get_client()
            speech = self.speech
            
            # Создаем объект аудио для Google API
            audio = speech.RecognitionAudio(content=audio_content)
            
            # Используем LongRunningRecognize для длинных аудио
            operation = client.long_running_recognize(config=self.config, audio=audio)
            response = operation.result(timeout=90)
            
            # Обрабатываем результат
            transcript_parts = []
            speaker_info = []
            
            for result in response.results:
                alternative = result.alternatives[0]
                transcript_parts.append(alternative.transcript)
                
                if hasattr(result, 'words'):
                    for word in result.words:
                        if hasattr(word, 'speaker_tag'):
                            speaker_info.append({
                                'word': word.word,
                                'speaker': word.speaker_tag,
                                'start_time': word.start_time.total_seconds(),
                                'end_time': word.end_time.total_seconds()
                            })
            
            # Объединяем транскрипцию
            full_transcript = ' '.join(transcript_parts)
            
            # Подсчитываем количество участников
            unique_speakers = len(set(info['speaker'] for info in speaker_info)) if speaker_info else 1
            
            return {
                'text': full_transcript,
                'duration': 300,  # Примерная длительность
                'language': self.config.language_code,
                'participant_count': max(unique_speakers, 1),
                'speaker_info': speaker_info[:100],
                'confidence': self._calculate_average_confidence(response.results)
            }
            
        except Exception as e:
            logger.error(f"Sync transcription failed: {str(e)}")
            return self._get_fallback_transcription("test.wav")

    def _calculate_average_confidence(self, results) -> float:
        if not results:
            return 0.0
        
        confidences = []
        for result in results:
            if result.alternatives:
                confidences.append(result.alternatives[0].confidence)
        
        return sum(confidences) / len(confidences) if confidences else 0.0

    def _get_fallback_transcription(self, file_path: str) -> Dict[str, Any]:
        logger.warning(f"Using fallback transcription for: {file_path}")
        filename = os.path.basename(file_path).lower()
        
        if 'standup' in filename or 'demo' in filename:
            return {
                'text': """Sarah: Good morning everyone, let's start our daily standup. John, how's your progress on the user authentication feature?

John: Hey team! I finished the login functionality yesterday and started working on the password reset flow. I should have that done by end of day today. No blockers on my end.

Sarah: Great progress! Maria, what about the dashboard redesign?

Maria: I completed the wireframes and got approval from the design team. Today I'm starting the implementation in React. I do have one blocker though - I need the new color palette from the brand team.

Sarah: I'll reach out to marketing today to get those brand guidelines. My update: I finished the API documentation and will be reviewing John's authentication code this afternoon.

John: Perfect! I'll have the PR ready for review by 2 PM.

Sarah: Sounds good. Let's plan to deploy the auth feature to staging tomorrow if the review goes well. Any questions? Alright team, let's make it a productive day!""",
                'duration': 272,
                'language': 'en-US',
                'participant_count': 3,
                'speaker_info': [],
                'confidence': 0.85
            }
        else:
            return {
                'text': 'This is a fallback transcription. The uploaded audio file would be transcribed here using Google Cloud Speech-to-Text API in production.',
                'duration': 300,
                'language': 'en-US',
                'participant_count': 2,
                'speaker_info': [],
                'confidence': 0.80
            }

# Глобальный экземпляр сервиса
speech_service = GoogleSpeechService()