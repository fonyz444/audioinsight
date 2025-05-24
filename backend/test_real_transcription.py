import asyncio
import logging
from services.speech_service import speech_service

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_real_transcription():
    try:
        # Используем тестовый WAV файл
        test_file = "demo_data/real_speech.wav"
        
        logger.info(f"Testing real transcription with file: {test_file}")
        result = await speech_service.transcribe_audio(test_file)
        
        logger.info("\nTranscription result:")
        logger.info(f"Text: {result['text']}")
        logger.info(f"Duration: {result['duration']} seconds")
        logger.info(f"Language: {result['language']}")
        logger.info(f"Participant count: {result['participant_count']}")
        logger.info(f"Confidence: {result['confidence']}")
        
        if result['speaker_info']:
            logger.info("\nSpeaker information:")
            for info in result['speaker_info'][:5]:  # Показываем первые 5 слов
                logger.info(f"Speaker {info['speaker']}: {info['word']} ({info['start_time']:.2f}s - {info['end_time']:.2f}s)")
        
        return True
    except Exception as e:
        logger.error(f"Test failed with error: {str(e)}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_real_transcription())
    if success:
        logger.info("\n✅ Test completed successfully!")
    else:
        logger.error("\n❌ Test failed!") 