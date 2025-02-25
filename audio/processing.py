import wave
import numpy as np
from scipy.signal import resample

def load_wave(file_path):
    with wave.open(file_path, 'rb') as wav_file:
        sample_rate = wav_file.getframerate()
        n_channels = wav_file.getnchannels()
        frames = wav_file.readframes(wav_file.getnframes())
        data = np.frombuffer(frames, dtype=np.int16).copy()
        if n_channels > 1:
            data = data.reshape(-1, n_channels)
    return sample_rate, data

def save_wave(file_path, sample_rate, data):
    n_channels = data.shape[1] if len(data.shape) > 1 else 1
    with wave.open(file_path, 'wb') as wav_file:
        wav_file.setnchannels(n_channels)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(data.astype(np.int16).tobytes())

def resample_audio(audio_data, original_rate, target_rate):
    float_data = audio_data.astype(np.float32) / 32768.0
    num_samples = int(audio_data.shape[0] * (target_rate / original_rate))
    resampled_float = resample(float_data, num_samples, axis=0)
    resampled_int16 = np.clip(resampled_float * 32768, -32768, 32767).astype(np.int16)
    return resampled_int16

async def resample_audio_inplace(file_path, target_sample_rate=44100):
    sample_rate, audio_data = load_wave(file_path)
    if sample_rate == target_sample_rate:
        return
    resampled_data = resample_audio(audio_data, sample_rate, target_sample_rate)
    save_wave(file_path, target_sample_rate, resampled_data)

def loop_audio(audio, target_length):
    repetitions = (target_length + len(audio) - 1) // len(audio)
    looped_audio = np.tile(audio, (repetitions, 1))
    return looped_audio[:target_length]

def is_valid_wav(file_path):
    try:
        with wave.open(file_path, 'rb'):
            return True
    except (wave.Error, EOFError, IOError):
        return False
