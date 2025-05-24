import wave
import struct
import math
import os

def create_russian_audio():
    # Создаем директорию если её нет
    os.makedirs("demo_data", exist_ok=True)
    
    # Параметры аудио
    sample_rate = 16000  # 16 kHz
    duration = 5  # 5 секунд
    
    # Создаем WAV файл
    output_path = os.path.join("demo_data", "real_speech.wav")
    with wave.open(output_path, 'w') as wav_file:
        # Устанавливаем параметры
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        
        # Генерируем тестовый сигнал (тональный сигнал)
        for i in range(int(sample_rate * duration)):
            # Создаем сложный сигнал из нескольких частот
            value = int(32767.0 * (
                0.5 * math.sin(2 * math.pi * 440 * i / sample_rate) +  # 440 Hz
                0.3 * math.sin(2 * math.pi * 880 * i / sample_rate) +  # 880 Hz
                0.2 * math.sin(2 * math.pi * 1320 * i / sample_rate)   # 1320 Hz
            ))
            data = struct.pack('<h', value)
            wav_file.writeframes(data)
    
    print(f"Created test WAV file: {output_path}")
    print("Note: This is a test tone. For real speech recognition, please record or provide a real audio file with speech.")

if __name__ == "__main__":
    create_russian_audio() 