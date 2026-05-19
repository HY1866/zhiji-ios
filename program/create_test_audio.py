
import wave
import struct
import os

audio_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Audio")
test_audio_path = os.path.join(audio_folder, "test.wav")

sample_rate = 16000
duration = 2  # 2秒
num_samples = sample_rate * duration

with wave.open(test_audio_path, 'wb') as wf:
    wf.setnchannels(1)
    wf.setsampwidth(2)
    wf.setframerate(sample_rate)
    
    # 生成简单的测试音频 - 1kHz正弦波（振幅较小，避免太响）
    import math
    for i in range(num_samples):
        value = int(1000 * math.sin(2 * math.pi * 1000 * i / sample_rate))
        wf.writeframes(struct.pack('<h', value))

print(f"测试音频已创建: {test_audio_path}")

