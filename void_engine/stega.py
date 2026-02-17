import wave
import struct
import hashlib
import os
import secrets
import numpy as np
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

HEADER_SIZE = 64
MAGIC = b"PVOD"
VILLAGE_STANDARD_HZ = 432


def _derive_key(passphrase: str) -> bytes:
    return hashlib.sha256(passphrase.encode("utf-8")).digest()


def _generate_hash_key() -> str:
    return secrets.token_hex(16)


def _encrypt_header(header_bytes: bytes, key: bytes) -> bytes:
    nonce = header_bytes[48:64]
    cipher = Cipher(algorithms.ChaCha20(key, nonce), mode=None)
    encryptor = cipher.encryptor()
    encrypted = encryptor.update(header_bytes[:48]) + encryptor.finalize()
    return encrypted + nonce


def _decrypt_header(encrypted_header: bytes, key: bytes) -> bytes:
    nonce = encrypted_header[48:64]
    cipher = Cipher(algorithms.ChaCha20(key, nonce), mode=None)
    decryptor = cipher.decryptor()
    decrypted = decryptor.update(encrypted_header[:48]) + decryptor.finalize()
    return decrypted + nonce


def _build_header(file_name: str, extension: str, data_size: int,
                  checksum: str, key: bytes) -> bytes:
    name_ext = (file_name + extension).encode("utf-8")
    if len(name_ext) > 24:
        name_ext = name_ext[:24]
    name_ext = name_ext.ljust(24, b"\x00")

    checksum_bytes = bytes.fromhex(checksum)

    nonce = secrets.token_bytes(16)

    plaintext = (
        MAGIC
        + name_ext
        + struct.pack("<I", data_size)
        + checksum_bytes
        + nonce
    )

    assert len(plaintext) == HEADER_SIZE, f"Header is {len(plaintext)} bytes, expected {HEADER_SIZE}"

    encrypted = _encrypt_header(plaintext, key)
    return encrypted


def _parse_header(encrypted_header: bytes, key: bytes) -> tuple[str, int, str]:
    decrypted = _decrypt_header(encrypted_header, key)

    magic = decrypted[:4]
    if magic != MAGIC:
        raise ValueError("Invalid hash key or corrupted header — decryption failed.")

    name_ext_raw = decrypted[4:28]
    name_ext = name_ext_raw.rstrip(b"\x00").decode("utf-8", errors="replace")

    data_size = struct.unpack("<I", decrypted[28:32])[0]

    checksum = decrypted[32:48].hex()

    return name_ext, data_size, checksum


def _compute_md5(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()


def encode(carrier_path: str, payload: bytes, file_name: str, extension: str,
           output_path: str, lsb_depth: int = 1, passphrase: str | None = None) -> str:
    if lsb_depth not in (1, 2):
        raise ValueError("lsb_depth must be 1 or 2")

    if passphrase is None:
        passphrase = _generate_hash_key()

    key = _derive_key(passphrase)
    checksum = _compute_md5(payload)
    header = _build_header(file_name, extension, len(payload), checksum, key)

    full_payload = header + payload
    total_bits = len(full_payload) * 8

    with wave.open(carrier_path, "rb") as wav_in:
        params = wav_in.getparams()
        sampwidth = params.sampwidth
        n_frames = params.nframes
        raw_frames = wav_in.readframes(n_frames)

    if sampwidth != 2:
        raise ValueError(f"Only 16-bit WAV files are supported (got {sampwidth * 8}-bit).")

    samples = np.frombuffer(raw_frames, dtype=np.int16).copy()
    total_samples = len(samples)
    bits_per_sample = lsb_depth
    capacity = total_samples * bits_per_sample

    if total_bits > capacity:
        raise ValueError(
            f"Payload too large: needs {total_bits:,} bits, "
            f"carrier has capacity for {capacity:,} bits ({capacity // 8:,} bytes) "
            f"at LSB depth {lsb_depth}."
        )

    bit_array = np.unpackbits(np.frombuffer(full_payload, dtype=np.uint8))

    if lsb_depth == 1:
        mask = np.int16(~1)
        for i in range(len(bit_array)):
            samples[i] = (samples[i] & mask) | np.int16(bit_array[i])
    else:
        mask = np.int16(~3)
        pad_len = (2 - (len(bit_array) % 2)) % 2
        if pad_len:
            bit_array = np.concatenate([bit_array, np.zeros(pad_len, dtype=np.uint8)])
        for i in range(0, len(bit_array), 2):
            two_bits = np.int16((bit_array[i] << 1) | bit_array[i + 1])
            idx = i // 2
            samples[idx] = (samples[idx] & mask) | two_bits

    modified_frames = samples.tobytes()

    with wave.open(output_path, "wb") as wav_out:
        wav_out.setparams(params)
        wav_out.writeframes(modified_frames)

    usage_pct = (total_bits / capacity) * 100
    print(f"  [VOID] Encoding complete:")
    print(f"         Carrier:    {carrier_path}")
    print(f"         Output:     {output_path}")
    print(f"         LSB depth:  {lsb_depth}")
    print(f"         Capacity:   {capacity // 8:,} bytes")
    print(f"         Used:       {len(full_payload):,} bytes ({usage_pct:.1f}%)")
    print(f"         Checksum:   {checksum}")

    return passphrase


def encode_burst(signal_text: str, output_path: str) -> str:
    if len(signal_text) > 10:
        raise ValueError("Signal text must be 10 characters or fewer.")

    sample_rate = 44100
    duration = 5
    t = np.linspace(0, duration, sample_rate * duration, endpoint=False)
    carrier = (16000 * np.sin(2 * np.pi * VILLAGE_STANDARD_HZ * t)).astype(np.int16)

    carrier_path = output_path + ".tmp_carrier.wav"
    try:
        with wave.open(carrier_path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(carrier.tobytes())

        from void_engine.compressor import compress_bytes
        compressed = compress_bytes(signal_text.encode("utf-8"))

        hash_key = encode(carrier_path, compressed, "burst", ".sig", output_path, lsb_depth=1)
    finally:
        if os.path.exists(carrier_path):
            os.remove(carrier_path)

    return hash_key


def decode(stego_path: str, passphrase: str, lsb_depth: int = 1) -> tuple[bytes, str, str]:
    if lsb_depth not in (1, 2):
        raise ValueError("lsb_depth must be 1 or 2")

    key = _derive_key(passphrase)

    with wave.open(stego_path, "rb") as wav_in:
        params = wav_in.getparams()
        n_frames = params.nframes
        sampwidth = params.sampwidth
        raw_frames = wav_in.readframes(n_frames)

    if sampwidth != 2:
        raise ValueError(f"Only 16-bit WAV files are supported (got {sampwidth * 8}-bit).")

    samples = np.frombuffer(raw_frames, dtype=np.int16)

    header_bits_needed = HEADER_SIZE * 8

    if lsb_depth == 1:
        header_bits = samples[:header_bits_needed] & 1
    else:
        needed_samples = (header_bits_needed + 1) // 2
        raw_bits = []
        for i in range(needed_samples):
            val = int(samples[i]) & 3
            raw_bits.append((val >> 1) & 1)
            raw_bits.append(val & 1)
        header_bits = np.array(raw_bits[:header_bits_needed], dtype=np.uint8)

    header_bytes = np.packbits(header_bits).tobytes()[:HEADER_SIZE]
    name_ext, data_size, stored_checksum = _parse_header(header_bytes, key)

    total_payload_bytes = HEADER_SIZE + data_size
    total_bits = total_payload_bytes * 8

    if lsb_depth == 1:
        all_bits = samples[:total_bits] & 1
    else:
        needed_samples = (total_bits + 1) // 2
        raw_bits = []
        for i in range(needed_samples):
            val = int(samples[i]) & 3
            raw_bits.append((val >> 1) & 1)
            raw_bits.append(val & 1)
        all_bits = np.array(raw_bits[:total_bits], dtype=np.uint8)

    all_bytes = np.packbits(all_bits).tobytes()[:total_payload_bytes]
    compressed_data = all_bytes[HEADER_SIZE:]

    computed_checksum = _compute_md5(compressed_data)
    if computed_checksum != stored_checksum:
        raise ValueError(
            f"Resonance verification FAILED!\n"
            f"  Expected: {stored_checksum}\n"
            f"  Computed: {computed_checksum}\n"
            f"  Data may be corrupted."
        )

    print(f"  [VOID] Decoding complete:")
    print(f"         File:       {name_ext}")
    print(f"         Data size:  {data_size:,} bytes (compressed)")
    print(f"         Checksum:   VERIFIED")

    return compressed_data, name_ext, stored_checksum
