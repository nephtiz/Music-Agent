import numpy as np
import secrets
import string
from audio.processing import load_wave, save_wave, loop_audio

def bits_to_array(bits_str, dtype=np.int16):
    return np.array([int(bit) for bit in bits_str], dtype=dtype)

def embed_bits(audio_channel, bits):
    bits_array = bits_to_array(bits)
    audio_channel = audio_channel.copy()
    end = len(bits_array)
    audio_channel[:end] = (audio_channel[:end] & ~1) | bits_array
    return audio_channel

def extract_bits(audio_channel, num_bits):
    return (audio_channel[:num_bits] & 1).astype(np.uint8)

def text_to_binary(text):
    utf8_bytes = text.encode('utf-8')
    bits = [f"{byte:08b}" for byte in utf8_bytes]
    return ''.join(bits)

def binary_to_text(binary):
    bytes_list = [int(binary[i:i+8], 2) for i in range(0, len(binary), 8)]
    return bytes(bytes_list).decode('utf-8', errors='replace')

def generate_random_filename(length=10, extension=".wav"):
    characters = string.ascii_letters + string.digits
    random_string = ''.join(secrets.choice(characters) for _ in range(length))
    return f"{random_string}{extension}"

def text_to_audio(input_text, song_file, output_file, signature, password=None, exceptions=None):
    pass_bin = text_to_binary(password or "") if password else ""
    except_bin = text_to_binary(','.join(exceptions or []))
    text_bin = text_to_binary(input_text)
    
    metadata = (
        signature +
        f"{len(pass_bin):016b}" +
        f"{len(except_bin):016b}" +
        f"{len(text_bin):016b}" +
        pass_bin +
        except_bin +
        text_bin
    )

    sample_rate, audio_data = load_wave(song_file)

    if len(audio_data.shape) == 1:
        audio_data = np.column_stack((audio_data, audio_data))
    elif audio_data.shape[1] == 1:
        audio_data = np.column_stack((audio_data.flatten(), audio_data.flatten()))

    required_length = len(metadata)
    if required_length > len(audio_data):
        audio_data = loop_audio(audio_data, required_length)

    left_channel = audio_data[:, 0].copy()
    audio_data[:, 0] = embed_bits(left_channel, metadata)
    
    save_wave(output_file, sample_rate, audio_data)
    return output_file

def verify_audio_signature(input_file, signature):
    _, audio_data = load_wave(input_file)
    left_channel = audio_data[:, 0] if audio_data.ndim > 1 else audio_data

    if len(signature) > len(left_channel):
        return False
    extracted_sig = ''.join(map(str, extract_bits(left_channel, len(signature))))
    return extracted_sig == signature

def audio_to_text(input_file, signature):
    _, audio_data = load_wave(input_file)
    left_channel = audio_data[:, 0] if audio_data.ndim > 1 else audio_data

    ptr = len(signature)
    pass_len = int(''.join(map(str, extract_bits(left_channel[ptr:ptr+16], 16))), 2)
    ptr += 16
    except_len = int(''.join(map(str, extract_bits(left_channel[ptr:ptr+16], 16))), 2)
    ptr += 16
    text_len = int(''.join(map(str, extract_bits(left_channel[ptr:ptr+16], 16))), 2)
    ptr += 16

    total_expected = ptr + pass_len + except_len + text_len
    if total_expected > len(left_channel):
        return {"error": "Corrupted metadata, length exceeds available data"}

    pass_bits = ''.join(map(str, extract_bits(left_channel[ptr:ptr+pass_len], pass_len)))
    ptr += pass_len
    except_bits = ''.join(map(str, extract_bits(left_channel[ptr:ptr+except_len], except_len)))
    ptr += except_len
    text_bits = ''.join(map(str, extract_bits(left_channel[ptr:ptr+text_len], text_len)))

    password = binary_to_text(pass_bits) if pass_len else None
    exceptions = binary_to_text(except_bits) if except_len else None
    text = binary_to_text(text_bits)

    return {"password": password, "exceptions": exceptions, "text": text}
