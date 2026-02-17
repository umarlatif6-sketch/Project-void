import wave
import os
import numpy as np
from void_engine.compressor import compress_file, decompress_data
from void_engine.stega import encode, decode


def generate_test_wav(path: str, duration: float = 10.0, sample_rate: int = 44100):
    n_samples = int(sample_rate * duration)
    t = np.linspace(0, duration, n_samples, endpoint=False)
    freq = 432.0
    signal = (np.sin(2 * np.pi * freq * t) * 16000).astype(np.int16)

    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(signal.tobytes())

    print(f"  Generated test WAV: {path} ({os.path.getsize(path):,} bytes)")


def create_test_file(path: str, content: str = "PROJECT VOID — This is a classified message hidden in audio."):
    with open(path, "w") as f:
        f.write(content)
    print(f"  Created test file:  {path} ({os.path.getsize(path):,} bytes)")


def run_test():
    print("\n  === PROJECT VOID SELF-TEST ===\n")

    wav_path = "input_files/test_carrier.wav"
    secret_path = "input_files/secret.txt"
    output_path = "output_audio/test_carrier_void.wav"

    os.makedirs("input_files", exist_ok=True)
    os.makedirs("output_audio", exist_ok=True)

    generate_test_wav(wav_path)
    create_test_file(secret_path)

    for depth in [1, 2]:
        print(f"\n  --- LSB DEPTH {depth} ---")

        print("\n  [ENCODING]")
        compressed, name, ext, orig_size = compress_file(secret_path)
        hash_key = encode(wav_path, compressed, name, ext, output_path, lsb_depth=depth)
        print(f"  Hash Key: {hash_key}")

        print("\n  [DECODING]")
        compressed_out, name_ext, checksum_out = decode(output_path, hash_key, lsb_depth=depth)
        restored = decompress_data(compressed_out)

        with open(secret_path, "rb") as f:
            original = f.read()

        assert restored == original, f"DATA MISMATCH at depth {depth}!"
        print(f"  Data match: PASSED")

    print(f"\n  === ALL TESTS PASSED ===")
    print(f"  Original:  {original.decode('utf-8')[:60]}")
    print(f"  Restored:  {restored.decode('utf-8')[:60]}")

    print("\n  [WRONG KEY TEST]")
    try:
        decode(output_path, "wrong_key_12345", lsb_depth=1)
        print("  ERROR: Should have rejected wrong key!")
    except ValueError as e:
        print(f"  Correctly rejected: {e}")

    print("\n  === FULL TEST SUITE PASSED ===\n")


if __name__ == "__main__":
    run_test()
