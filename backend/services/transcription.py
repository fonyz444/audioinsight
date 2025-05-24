import os
import subprocess
from google.cloud import speech_v1p1beta1 as speech


class TranscriptionWorker:
    """Воркер для транскрипции аудиофайлов с использованием Google Speech-to-Text"""
    
    def __init__(self):
        # Укажите путь к вашему credentials-файлу
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "google-credentials.json"
        self.client = speech.SpeechClient()
        print("✅ TranscriptionWorker инициализирован")
    
    def convert_to_wav(self, input_path: str, output_path: str):
        """Конвертирует аудиофайл в WAV 16kHz 1 канал с помощью ffmpeg"""
        try:
            subprocess.run([
                "ffmpeg", "-y", "-i", input_path, "-ar", "16000", "-ac", "1", output_path
            ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except subprocess.CalledProcessError as e:
            raise Exception(f"Ошибка конвертации аудио: {e.stderr.decode()}")

    def transcribe_audio(self, audio_file_path: str) -> str:
        """
        Транскрибирует аудиофайл в текст
        
        Args:
            audio_file_path: Путь к аудиофайлу
            
        Returns:
            Транскрипция в виде текста
            
        Raises:
            FileNotFoundError: Если файл не найден
            Exception: При ошибках API
        """
        print(f"🎵 Начинаю транскрипцию файла: {audio_file_path}")
        
        try:
            # Проверяем существование файла
            if not os.path.exists(audio_file_path):
                raise FileNotFoundError(f"Аудиофайл не найден: {audio_file_path}")
            
            # Получаем размер файла для логирования
            file_size = os.path.getsize(audio_file_path) / (1024 * 1024)  # в МБ
            print(f"📊 Размер файла: {file_size:.2f} МБ")
            
            # Конвертируем в WAV
            wav_path = audio_file_path + ".google.wav"
            self.convert_to_wav(audio_file_path, wav_path)
            
            with open(wav_path, "rb") as audio_file:
                content = audio_file.read()

            audio = speech.RecognitionAudio(content=content)
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=16000,
                language_code="ru-RU",
                enable_automatic_punctuation=True,
            )

            response = self.client.recognize(config=config, audio=audio)
            transcript = " ".join([result.alternatives[0].transcript for result in response.results])
            
            print(f"✅ Транскрипция завершена. Длина текста: {len(transcript)} символов")
            print(f"📝 Превью транскрипции: {transcript[:200]}...")
            
            # Удаляем временный файл
            if os.path.exists(wav_path):
                os.remove(wav_path)
            
            return transcript
            
        except FileNotFoundError as e:
            print(f"❌ Ошибка: файл не найден - {e}")
            raise
        except Exception as e:
            print(f"❌ Ошибка транскрипции: {e}")
            raise Exception(f"Не удалось транскрибировать аудиофайл: {str(e)}")
    
    def get_supported_formats(self) -> list:
        """
        Возвращает список поддерживаемых форматов файлов
        
        Returns:
            Список поддерживаемых расширений
        """
        return [
            'mp3', 'mp4', 'mpeg', 'mpga', 'm4a', 'wav', 'webm', 
            'flac', 'ogg', 'avi', 'mov', 'wmv', '3gp'
        ]
    
    def validate_file(self, file_path: str) -> bool:
        """
        Проверяет, поддерживается ли формат файла
        
        Args:
            file_path: Путь к файлу
            
        Returns:
            True если формат поддерживается
        """
        if not os.path.exists(file_path):
            return False
            
        file_extension = os.path.splitext(file_path)[1].lower().replace('.', '')
        return file_extension in self.get_supported_formats()