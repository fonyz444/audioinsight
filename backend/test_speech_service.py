import asyncio
import logging
from services.speech_service import speech_service

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_transcription():
    try:
        # Тестируем fallback транскрипцию
        logger.info("Testing fallback transcription...")
        result = await speech_service.transcribe_audio("demo_data/real_speech.wav")
        
        logger.info("Transcription result:")
        logger.info(f"Text: {result['text'][:200]}...")  # Показываем первые 200 символов
        logger.info(f"Duration: {result['duration']} seconds")
        logger.info(f"Language: {result['language']}")
        logger.info(f"Participant count: {result['participant_count']}")
        logger.info(f"Confidence: {result['confidence']}")
        
        return True
    except Exception as e:
        logger.error(f"Test failed with error: {str(e)}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_transcription())
    if success:
        logger.info("Test completed successfully!")
    else:
        logger.error("Test failed!") 