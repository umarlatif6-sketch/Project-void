import wave
import struct
import hashlib
import numpy as np


HEADER_SIZE = 24
MAGIC = b"VOID"


def _build_header(file_name: str, extension: str, data_size: int) -> bytes:
    name_ext = (file_name + extension).encode("utf-8")
    if len(name_ext) > 16:
        name_ext = name_ext[:16]
    name_ext = name_ext.ljust(16, b"\x00")
    header = MAGIC + name_ext + struct.pack("<I", data_size)
    assert len(header) == HEADER_SIZE
    return header


def _parse_header(header_bytes: bytes) -> tuple[str, int]:
    if header_bytes[:4] != MAGIC:
        raise ValueError("Invalid VOID header — this audio does not contain encoded data.")
    name_ext_raw = header_bytes[4:20]
    name_ext = name_ext_raw.rstrip(b"\x00").decode("utf-8", errors="replace")
    data_size = struct.unpack("<I", header_bytes[20:24])[0]
    return name_ext, data_size


def _compute_md5(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()


def encode(carrier_path: str, payload: bytes, file_name: str, extension: str,
           output_path: str, lsb_depth: int = 1) -> str:
    if lsb_depth not in (1, 2):
        raise ValueError("lsb_depth must be 1 or 2")

    checksum = _compute_md5(payload)
    checksum_bytes = checksum.encode("utf-8")

    header = _build_header(file_name, extension, len(payload))
    full_payload = header + checksum_bytes + payload

    total_bits = len(full_payload) * 8

    with wave.open(carrier_path, "rb") as wav_in:
        params = wav_in.getparams()
        n_channels = params.nchannels
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
            f"Payload too large: needs {total_bits} bits, "
            f"carrier has capacity for {capacity} bits ({capacity // 8:,} bytes) "
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
    print(f"         MD5:        {checksum}")

    return checksum


def decode(stego_path: str, lsb_depth: int = 1) -> tuple[bytes, str, str]:
    if lsb_depth not in (1, 2):
        raise ValueError("lsb_depth must be 1 or 2")

    with wave.open(stego_path, "rb") as wav_in:
        params = wav_in.getparams()
        n_frames = params.nframes
        sampwidth = params.sampwidth
        raw_frames = wav_in.readframes(n_frames)

    if sampwidth != 2:
        raise ValueError(f"Only 16-bit WAV files are supported (got {sampwidth * 8}-bit).")

    samples = np.frombuffer(raw_frames, dtype=np.int16)

    header_bits_needed = HEADER_SIZE * 8
    md5_hex_len = 32
    header_plus_md5_bytes = HEADER_SIZE + md5_hex_len
    header_plus_md5_bits = header_plus_md5_bytes * 8

    if lsb_depth == 1:
        header_md5_bits = samples[:header_plus_md5_bits] & 1
    else:
        needed_samples = (header_plus_md5_bits + 1) // 2
        raw_bits = []
        for i in range(needed_samples):
            val = int(samples[i]) & 3
            raw_bits.append((val >> 1) & 1)
            raw_bits.append(val & 1)
        header_md5_bits = np.array(raw_bits[:header_plus_md5_bits], dtype=np.uint8)

    header_md5_bytes = np.packbits(header_md5_bits).tobytes()[:header_plus_md5_bytes]

    header_data = header_md5_bytes[:HEADER_SIZE]
    stored_checksum = header_md5_bytes[HEADER_SIZE:HEADER_SIZE + md5_hex_len].decode("utf-8")

    name_ext, data_size = _parse_header(header_data)

    total_payload_bytes = HEADER_SIZE + md5_hex_len + data_size
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

    compressed_data = all_bytes[HEADER_SIZE + md5_hex_len:]

    computed_checksum = _compute_md5(compressed_data)

    if computed_checksum != stored_checksum:
        raise ValueError(
            f"Resonance verification FAILED!\n"
            f"  Expected MD5: {stored_checksum}\n"
            f"  Computed MD5: {computed_checksum}\n"
            f"  The data may be corrupted."
        )

    print(f"  [VOID] Decoding complete:")
    print(f"         File:       {name_ext}")
    print(f"         Data size:  {data_size:,} bytes (compressed)")
    print(f"         MD5 match:  VERIFIED")

    return compressed_data, name_ext, stored_checksum
