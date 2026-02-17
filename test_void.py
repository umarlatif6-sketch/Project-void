import wave
import struct
import os
import numpy as np
from compressor import compress_file, decompress_data
from steganography import encode, decode


def generate_test_wav(path: str, duration: float = 10.0, sample_rate: int = 44100):
    n_samples = int(sample_rate * duration)
    t = np.linspace(0, duration, n_samples, endpoint=False)
    freq = 440.0
    signal = (np.sin(2 * np.pi * freq * t) * 16000).astype(np.int16)

    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(signal.tobytes())

    print(f"  Generated test WAV: {path} ({os.path.getsize(path):,} bytes)")


def create_test_file(path: str, content: str = "Hello from THE VOID ENGINE! This is a secret message."):
    with open(path, "w") as f:
        f.write(content)
    print(f"  Created test file:  {path} ({os.path.getsize(path):,} bytes)")


def run_test():
    print("\n  === VOID ENGINE SELF-TEST ===\n")

    wav_path = "input_files/test_carrier.wav"
    secret_path = "input_files/secret.txt"
    output_path = "output_audio/test_carrier_void.wav"

    generate_test_wav(wav_path)
    create_test_file(secret_path)

    print("\n  --- ENCODING ---")
    compressed, name, ext, orig_size = compress_file(secret_path)
    checksum = encode(wav_path, compressed, name, ext, output_path, lsb_depth=1)

    print("\n  --- DECODING ---")
    compressed_out, name_ext, checksum_out = decode(output_path, lsb_depth=1)
    restored = decompress_data(compressed_out)

    with open(secret_path, "rb") as f:
        original = f.read()

    assert restored == original, "DATA MISMATCH!"
    assert checksum == checksum_out, "CHECKSUM MISMATCH!"

    print(f"\n  SELF-TEST PASSED")
    print(f"  Original:  {original.decode('utf-8')[:60]}")
    print(f"  Restored:  {restored.decode('utf-8')[:60]}")
    print(f"  MD5 match: {checksum}")


if __name__ == "__main__":
    run_test()
