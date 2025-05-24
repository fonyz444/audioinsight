import os
from google.cloud import speech_v1p1beta1 as speech
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_credentials():
    try:
        # Проверяем наличие файла credentials
        credentials_path = "audioinsight-460812-a14416636db4.json"
        if not os.path.exists(credentials_path):
            logger.error(f"Credentials file not found: {credentials_path}")
            return False

        # Устанавливаем переменную окружения
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
        
        # Пробуем создать клиент
        client = speech.SpeechClient()
        logger.info("Successfully created Speech-to-Text client!")
        
        # Проверяем доступ к API
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000,
            language_code="ru-RU",
        )
        logger.info("Successfully created recognition config!")
        
        return True
        
    except Exception as e:
        logger.error(f"Error testing credentials: {str(e)}")
        return False

if __name__ == "__main__":
    if test_credentials():
        logger.info("✅ Credentials test passed!")
    else:
        logger.error("❌ Credentials test failed!") 