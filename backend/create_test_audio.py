import wave
import struct
import math
import os

def create_test_wav():
    # Создаем директорию если её нет
    os.makedirs("demo_data", exist_ok=True)
    
    # Параметры аудио
    sample_rate = 16000  # 16 kHz
    duration = 3  # 3 секунды
    frequency = 440  # 440 Hz - нота ля первой октавы
    
    # Создаем WAV файл
    output_path = os.path.join("demo_data", "real_speech.wav")
    with wave.open(output_path, 'w') as wav_file:
        # Устанавливаем параметры
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        
        # Генерируем синусоидальный сигнал
        for i in range(int(sample_rate * duration)):
            value = int(32767.0 * math.sin(2 * math.pi * frequency * i / sample_rate))
            data = struct.pack('<h', value)
            wav_file.writeframes(data)
    
    print(f"Created test WAV file: {output_path}")

if __name__ == "__main__":
    create_test_wav() 