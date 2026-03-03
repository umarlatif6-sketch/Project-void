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
PILOT_TONE_DURATION = 0.5
PILOT_TONE_SAMPLE_RATE = 44100
JITTER_FLAG_BIT = 1 << 31
VORTEX_FLAG_BIT = 1 << 30
CHIRP_SYNC_FLAG_BIT = 1 << 29

_carrier_cache = {}


def _get_cached_carrier(cache_key: str, generator_fn):
    if cache_key not in _carrier_cache:
        _carrier_cache[cache_key] = generator_fn()
    return _carrier_cache[cache_key].copy()


def _generate_pilot_tone(sample_rate: int = PILOT_TONE_SAMPLE_RATE) -> np.ndarray:
    n_samples = int(PILOT_TONE_DURATION * sample_rate)
    t = np.linspace(0, PILOT_TONE_DURATION, n_samples, endpoint=False)
    tone_432 = np.sin(2 * np.pi * VILLAGE_STANDARD_HZ * t)
    tone_864 = np.sin(2 * np.pi * (VILLAGE_STANDARD_HZ * 2) * t)
    combined = 0.6 * tone_432 + 0.3 * tone_864
    fade_len = int(0.01 * sample_rate)
    fade_in = np.linspace(0, 1, fade_len)
    fade_out = np.linspace(1, 0, fade_len)
    combined[:fade_len] *= fade_in
    combined[-fade_len:] *= fade_out
    return np.clip(combined * 16000, -32768, 32767).astype(np.int16)


def _generate_burst_carrier(duration: float = 5.0, sample_rate: int = PILOT_TONE_SAMPLE_RATE) -> np.ndarray:
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    shimmer_lfo_rate = 0.25
    shimmer_depth = 2.0
    shimmer_mod = shimmer_depth * np.sin(2 * np.pi * shimmer_lfo_rate * t)
    base_freq = VILLAGE_STANDARD_HZ + shimmer_mod
    phase = np.cumsum(2 * np.pi * base_freq / sample_rate)
    signal = (
        16000 * np.sin(phase)
        + 16000 * 0.10 * np.sin(2 * phase)
        + 16000 * 0.05 * np.sin(3 * phase)
    )
    return np.clip(signal, -32768, 32767).astype(np.int16)


def _derive_key(passphrase: str) -> bytes:
    return hashlib.sha256(passphrase.encode("utf-8")).digest()


def _compute_ghost_offset(passphrase: str, total_samples: int) -> int:
    seed = int(hashlib.sha256(("ghost:" + passphrase).encode()).hexdigest()[:8], 16)
    max_offset = total_samples // 4
    if max_offset <= 0:
        return 0
    return seed % max_offset


def _generate_jitter_map(passphrase: str, n_data_samples: int,
                         available_start: int, available_end: int) -> list[tuple[int, int]]:
    seed = int(hashlib.sha256(("jitter:" + passphrase).encode()).hexdigest()[:8], 16)
    rng = np.random.RandomState(seed)

    total_available = available_end - available_start

    if n_data_samples <= 0:
        return []

    if n_data_samples >= int(total_available * 0.8):
        return [(available_start, n_data_samples)]

    n_chunks = min(max(7, n_data_samples // 500), 20)
    if n_data_samples < n_chunks:
        n_chunks = max(1, n_data_samples)

    alpha = rng.uniform(0.5, 2.0, size=n_chunks)
    proportions = rng.dirichlet(alpha)
    chunk_sizes = np.maximum(1, np.round(proportions * n_data_samples).astype(int))

    diff = n_data_samples - int(chunk_sizes.sum())
    chunk_sizes[-1] += diff
    if chunk_sizes[-1] <= 0:
        chunk_sizes[-1] = 1
        overshoot = int(chunk_sizes.sum()) - n_data_samples
        for i in range(len(chunk_sizes) - 2, -1, -1):
            take = min(overshoot, int(chunk_sizes[i]) - 1)
            chunk_sizes[i] -= take
            overshoot -= take
            if overshoot <= 0:
                break

    total_gap = total_available - n_data_samples
    n_gaps = n_chunks + 1
    gap_alpha = rng.uniform(0.3, 3.0, size=n_gaps)
    gap_proportions = rng.dirichlet(gap_alpha)
    gaps = np.maximum(0, np.round(gap_proportions * total_gap).astype(int))

    gap_diff = total_gap - int(gaps.sum())
    gaps[-1] += gap_diff

    positions = []
    pos = available_start
    for i in range(n_chunks):
        pos += int(gaps[i])
        csize = int(chunk_sizes[i])
        if pos + csize > available_end:
            csize = available_end - pos
        if csize > 0:
            positions.append((pos, csize))
        pos += csize

    return positions


def _generate_vortex_map(passphrase: str, n_data_samples: int,
                         available_start: int, available_end: int) -> list[tuple[int, int]]:
    seed = int(hashlib.sha256(("vortex:" + passphrase).encode()).hexdigest()[:8], 16)
    total_available = available_end - available_start

    if n_data_samples <= 0:
        return []

    if n_data_samples >= int(total_available * 0.8):
        return [(available_start, n_data_samples)]

    harmonics = [VILLAGE_STANDARD_HZ, VILLAGE_STANDARD_HZ * 2, VILLAGE_STANDARD_HZ * 3,
                 VILLAGE_STANDARD_HZ * 0.5, VILLAGE_STANDARD_HZ * 1.5]
    n_arms = len(harmonics)
    n_chunks = min(max(n_arms * 3, n_data_samples // 300), 40)
    if n_data_samples < n_chunks:
        n_chunks = max(1, n_data_samples)

    golden_angle = 2.399963
    spiral_positions = []
    for i in range(n_chunks):
        harmonic_idx = i % n_arms
        harmonic_weight = harmonics[harmonic_idx] / VILLAGE_STANDARD_HZ
        angle = i * golden_angle * harmonic_weight
        radius = (i / n_chunks)
        normalized_pos = (np.sin(angle) * radius + 1.0) / 2.0
        spiral_positions.append(normalized_pos)

    spiral_positions.sort()

    rng = np.random.RandomState(seed)
    alpha = np.array([harmonics[i % n_arms] / VILLAGE_STANDARD_HZ + 0.5 for i in range(n_chunks)])
    proportions = rng.dirichlet(alpha)
    chunk_sizes = np.maximum(1, np.round(proportions * n_data_samples).astype(int))

    diff = n_data_samples - int(chunk_sizes.sum())
    chunk_sizes[-1] += diff
    if chunk_sizes[-1] <= 0:
        chunk_sizes[-1] = 1
        overshoot = int(chunk_sizes.sum()) - n_data_samples
        for i in range(len(chunk_sizes) - 2, -1, -1):
            take = min(overshoot, int(chunk_sizes[i]) - 1)
            chunk_sizes[i] -= take
            overshoot -= take
            if overshoot <= 0:
                break

    positions = []
    for i in range(n_chunks):
        csize = int(chunk_sizes[i])
        raw_pos = available_start + int(spiral_positions[i] * (total_available - csize))
        raw_pos = max(available_start, min(raw_pos, available_end - csize))
        positions.append((raw_pos, csize))

    positions.sort(key=lambda x: x[0])

    resolved = []
    current_end = available_start
    for (pos, csize) in positions:
        actual_pos = max(pos, current_end)
        if actual_pos + csize > available_end:
            csize = available_end - actual_pos
        if csize > 0:
            resolved.append((actual_pos, csize))
            current_end = actual_pos + csize

    return resolved


def _auto_detect_chirp_peaks(samples: np.ndarray, percentile: int = 70) -> np.ndarray:
    abs_samples = np.abs(samples.astype(np.float64))
    window = min(512, len(abs_samples) // 10)
    if window < 4:
        return np.array([], dtype=np.int64)
    kernel = np.ones(window) / window
    envelope = np.convolve(abs_samples, kernel, mode='same')
    threshold = np.percentile(envelope, percentile)
    above = envelope > threshold
    rising = np.zeros(len(above), dtype=bool)
    rising[1:] = above[1:] & ~above[:-1]
    peak_indices = np.where(rising)[0]
    if len(peak_indices) == 0:
        peak_indices = np.where(above)[0]
        if len(peak_indices) > 0:
            step = max(1, len(peak_indices) // (len(samples) // 1260 + 1))
            peak_indices = peak_indices[::step]
    return peak_indices.astype(np.int64)


def _load_or_detect_chirp_peaks(carrier_path: str, samples: np.ndarray) -> np.ndarray:
    chirpmap_path = carrier_path.replace(".wav", ".chirpmap.npy")
    if os.path.exists(chirpmap_path):
        peaks = np.load(chirpmap_path)
        return peaks.astype(np.int64)
    return _auto_detect_chirp_peaks(samples)


def _copy_chirpmap_sidecar(carrier_path: str, output_path: str):
    import shutil
    src_map = carrier_path.replace(".wav", ".chirpmap.npy")
    if os.path.exists(src_map):
        dst_map = output_path.replace(".wav", ".chirpmap.npy")
        shutil.copy2(src_map, dst_map)


def _generate_chirp_map(samples: np.ndarray, n_data_samples: int,
                        chirp_peaks: np.ndarray, passphrase: str,
                        lsb_depth: int, available_start: int,
                        available_end: int) -> list[tuple[int, int]]:
    if n_data_samples <= 0:
        return []

    valid_peaks = chirp_peaks[(chirp_peaks >= available_start) & (chirp_peaks < available_end)]

    if len(valid_peaks) == 0:
        return [(available_start, n_data_samples)]

    total_available = available_end - available_start
    if n_data_samples >= int(total_available * 0.8):
        return [(available_start, n_data_samples)]

    n_chunks = min(len(valid_peaks), max(7, n_data_samples // 300))
    if n_data_samples < n_chunks:
        n_chunks = max(1, n_data_samples)

    if len(valid_peaks) > n_chunks:
        step = len(valid_peaks) / n_chunks
        selected_peaks = np.array([valid_peaks[int(i * step)] for i in range(n_chunks)])
    else:
        selected_peaks = valid_peaks[:n_chunks]

    seed = int(hashlib.sha256(("chirpsync:" + passphrase).encode()).hexdigest()[:8], 16)
    rng = np.random.RandomState(seed)

    alpha = np.ones(n_chunks) + rng.uniform(0.2, 1.0, size=n_chunks)
    proportions = rng.dirichlet(alpha)
    chunk_sizes = np.maximum(1, np.round(proportions * n_data_samples).astype(int))

    diff = n_data_samples - int(chunk_sizes.sum())
    chunk_sizes[-1] += diff
    if chunk_sizes[-1] <= 0:
        chunk_sizes[-1] = 1
        overshoot = int(chunk_sizes.sum()) - n_data_samples
        for i in range(len(chunk_sizes) - 2, -1, -1):
            take = min(overshoot, int(chunk_sizes[i]) - 1)
            chunk_sizes[i] -= take
            overshoot -= take
            if overshoot <= 0:
                break

    positions = []
    for i in range(n_chunks):
        csize = int(chunk_sizes[i])
        pos = int(selected_peaks[i])
        pos = max(available_start, min(pos, available_end - csize))
        positions.append((pos, csize))

    positions.sort(key=lambda x: x[0])

    resolved = []
    current_end = available_start
    for (pos, csize) in positions:
        actual_pos = max(pos, current_end)
        if actual_pos + csize > available_end:
            csize = available_end - actual_pos
        if csize > 0:
            resolved.append((actual_pos, csize))
            current_end = actual_pos + csize

    return resolved


def apply_dither_mask(samples: np.ndarray, seed: int = 42) -> np.ndarray:
    rng = np.random.RandomState(seed)
    white = rng.randn(len(samples))
    b = [0.049922035, -0.095993537, 0.050612699, -0.004709510,
         0.000045049, -0.000023574, 0.000011570]
    pink = np.zeros(len(white))
    state = np.zeros(len(b))
    for i in range(len(white)):
        x = white[i]
        y = 0.0
        for j in range(len(b)):
            y += b[j] * state[j]
            state[j] = x if j == 0 else state[j - 1]
        pink[i] = x - y
    amplitude = 1.5
    pink = pink / (np.max(np.abs(pink)) + 1e-10) * amplitude
    dithered = samples.astype(np.float64) + pink
    return np.clip(dithered, -32768, 32767).astype(np.int16)


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
                  checksum: str, key: bytes, jitter: bool = False,
                  vortex: bool = False, chirp_sync: bool = False) -> bytes:
    name_ext = (file_name + extension).encode("utf-8")
    if len(name_ext) > 24:
        name_ext = name_ext[:24]
    name_ext = name_ext.ljust(24, b"\x00")

    checksum_bytes = bytes.fromhex(checksum)

    nonce = secrets.token_bytes(16)

    stored_size = data_size
    if jitter:
        stored_size |= JITTER_FLAG_BIT
    if vortex:
        stored_size |= VORTEX_FLAG_BIT
    if chirp_sync:
        stored_size |= CHIRP_SYNC_FLAG_BIT

    plaintext = (
        MAGIC
        + name_ext
        + struct.pack("<I", stored_size)
        + checksum_bytes
        + nonce
    )

    assert len(plaintext) == HEADER_SIZE, f"Header is {len(plaintext)} bytes, expected {HEADER_SIZE}"

    encrypted = _encrypt_header(plaintext, key)
    return encrypted


def _parse_header(encrypted_header: bytes, key: bytes) -> tuple[str, int, str, bool, bool, bool]:
    decrypted = _decrypt_header(encrypted_header, key)

    magic = decrypted[:4]
    if magic != MAGIC:
        raise ValueError("Invalid hash key or corrupted header — decryption failed.")

    name_ext_raw = decrypted[4:28]
    name_ext = name_ext_raw.rstrip(b"\x00").decode("utf-8", errors="replace")

    raw_size = struct.unpack("<I", decrypted[28:32])[0]
    jitter = bool(raw_size & JITTER_FLAG_BIT)
    vortex = bool(raw_size & VORTEX_FLAG_BIT)
    chirp_sync = bool(raw_size & CHIRP_SYNC_FLAG_BIT)
    data_size = raw_size & ~JITTER_FLAG_BIT & ~VORTEX_FLAG_BIT & ~CHIRP_SYNC_FLAG_BIT

    checksum = decrypted[32:48].hex()

    return name_ext, data_size, checksum, jitter, vortex, chirp_sync


def _compute_md5(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()


def _embed_bits_at(samples: np.ndarray, bit_array: np.ndarray,
                   start: int, n_samples: int, lsb_depth: int) -> None:
    if lsb_depth == 1:
        seg = samples[start:start + n_samples]
        samples[start:start + n_samples] = (seg & np.int16(~1)) | bit_array[:n_samples].astype(np.int16)
    else:
        seg = samples[start:start + n_samples]
        bits = bit_array[:n_samples * 2]
        high_bits = bits[0::2].astype(np.int16)
        low_bits = bits[1::2].astype(np.int16)
        two_bit_values = (high_bits << 1) | low_bits
        samples[start:start + n_samples] = (seg & np.int16(~3)) | two_bit_values


def _extract_bits_at(samples: np.ndarray, start: int,
                     n_samples: int, lsb_depth: int) -> np.ndarray:
    if lsb_depth == 1:
        return (samples[start:start + n_samples] & 1).astype(np.uint8)
    else:
        seg = samples[start:start + n_samples]
        two_bit_vals = seg.astype(np.int16) & 3
        high_bits = (two_bit_vals >> 1).astype(np.uint8)
        low_bits = (two_bit_vals & 1).astype(np.uint8)
        interleaved = np.empty(n_samples * 2, dtype=np.uint8)
        interleaved[0::2] = high_bits
        interleaved[1::2] = low_bits
        return interleaved


def encode(carrier_path: str, payload: bytes, file_name: str, extension: str,
           output_path: str, lsb_depth: int = 1, passphrase: str | None = None,
           jitter: bool = False, vortex: bool = False,
           chirp_sync: bool = False) -> str:
    if lsb_depth not in (1, 2):
        raise ValueError("lsb_depth must be 1 or 2")

    active_modes = sum([jitter, vortex, chirp_sync])
    if active_modes > 1:
        raise ValueError("Cannot use multiple scatter modes simultaneously (jitter, vortex, chirp_sync are mutually exclusive)")

    if len(payload) > 500 * 1024 * 1024:
        print(f"  [RESONANCE WARNING]: Large Void detected ({len(payload) / (1024*1024):.0f} MB). Ensuring 18-hour Pulse is active...")

    if passphrase is None:
        passphrase = _generate_hash_key()

    key = _derive_key(passphrase)
    checksum = _compute_md5(payload)
    header = _build_header(file_name, extension, len(payload), checksum, key,
                           jitter=jitter, vortex=vortex, chirp_sync=chirp_sync)

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

    ghost_offset = _compute_ghost_offset(passphrase, total_samples)
    effective_capacity = (total_samples - ghost_offset) * bits_per_sample
    total_bits = (HEADER_SIZE + len(payload)) * 8

    if total_bits > effective_capacity:
        raise ValueError(
            f"Payload too large: needs {total_bits:,} bits, "
            f"carrier has capacity for {effective_capacity:,} bits ({effective_capacity // 8:,} bytes) "
            f"at LSB depth {lsb_depth} (Ghost Offset: {ghost_offset:,} samples)."
        )

    dither_seed = int(hashlib.sha256(("dither:" + passphrase).encode()).hexdigest()[:8], 16)
    samples = apply_dither_mask(samples, seed=dither_seed)

    header_bits = np.unpackbits(np.frombuffer(header, dtype=np.uint8))
    header_samples = HEADER_SIZE * 8 // bits_per_sample
    if lsb_depth == 2:
        pad_len = (2 - (len(header_bits) % 2)) % 2
        if pad_len:
            header_bits = np.concatenate([header_bits, np.zeros(pad_len, dtype=np.uint8)])
    _embed_bits_at(samples, header_bits, ghost_offset, header_samples, lsb_depth)

    data_bits = np.unpackbits(np.frombuffer(payload, dtype=np.uint8))
    if lsb_depth == 2:
        pad_len = (2 - (len(data_bits) % 2)) % 2
        if pad_len:
            data_bits = np.concatenate([data_bits, np.zeros(pad_len, dtype=np.uint8)])
    data_samples_needed = len(data_bits) // bits_per_sample

    scatter_info = ""
    if chirp_sync and data_samples_needed > 0:
        data_start = ghost_offset + header_samples
        chirp_peaks = _load_or_detect_chirp_peaks(carrier_path, samples)
        chirp_map = _generate_chirp_map(samples, data_samples_needed, chirp_peaks,
                                        passphrase, lsb_depth, data_start, total_samples)
        bit_offset = 0
        for (pos, chunk_len) in chirp_map:
            chunk_bits = data_bits[bit_offset * bits_per_sample:(bit_offset + chunk_len) * bits_per_sample]
            _embed_bits_at(samples, chunk_bits, pos, chunk_len, lsb_depth)
            bit_offset += chunk_len
        scatter_info = f"\n         Chirp Sync: Active ({len(chirp_map)} chunks synced to {len(chirp_peaks)} chirp peaks)"
    elif vortex and data_samples_needed > 0:
        data_start = ghost_offset + header_samples
        vortex_map = _generate_vortex_map(passphrase, data_samples_needed,
                                          data_start, total_samples)

        bit_offset = 0
        for (pos, chunk_len) in vortex_map:
            chunk_bits = data_bits[bit_offset * bits_per_sample:(bit_offset + chunk_len) * bits_per_sample]
            _embed_bits_at(samples, chunk_bits, pos, chunk_len, lsb_depth)
            bit_offset += chunk_len

        scatter_info = f"\n         Vortex Scatter: Active ({len(vortex_map)} spiral arms, 432 Hz harmonic distribution)"
    elif jitter and data_samples_needed > 0:
        data_start = ghost_offset + header_samples
        jitter_map = _generate_jitter_map(passphrase, data_samples_needed,
                                          data_start, total_samples)

        bit_offset = 0
        for (pos, chunk_len) in jitter_map:
            chunk_bits = data_bits[bit_offset * bits_per_sample:(bit_offset + chunk_len) * bits_per_sample]
            _embed_bits_at(samples, chunk_bits, pos, chunk_len, lsb_depth)
            bit_offset += chunk_len

        scatter_info = f"\n         Fly Jitter: Active ({len(jitter_map)} chunks scattered)"
    else:
        data_start = ghost_offset + header_samples
        _embed_bits_at(samples, data_bits, data_start, data_samples_needed, lsb_depth)

    modified_frames = samples.tobytes()

    with wave.open(output_path, "wb") as wav_out:
        wav_out.setparams(params)
        wav_out.writeframes(modified_frames)

    if chirp_sync:
        _copy_chirpmap_sidecar(carrier_path, output_path)

    full_payload_size = HEADER_SIZE + len(payload)
    usage_pct = (total_bits / capacity) * 100
    print(f"  [VOID] Encoding complete:")
    print(f"         Carrier:    {carrier_path}")
    print(f"         Output:     {output_path}")
    print(f"         LSB depth:  {lsb_depth}")
    print(f"         Capacity:   {capacity // 8:,} bytes")
    print(f"         Used:       {full_payload_size:,} bytes ({usage_pct:.1f}%)")
    print(f"         Checksum:   {checksum}")
    print(f"         Ghost Offset: {ghost_offset:,} samples")
    print(f"         Dither Mask: Applied (seed {dither_seed}){scatter_info}")

    return passphrase


def encode_burst(signal_text: str, output_path: str) -> str:
    if len(signal_text) > 10:
        raise ValueError("Signal text must be 10 characters or fewer.")

    sample_rate = PILOT_TONE_SAMPLE_RATE

    pilot = _get_cached_carrier("pilot_44100", lambda: _generate_pilot_tone(sample_rate))
    body = _get_cached_carrier("burst_5s_44100", lambda: _generate_burst_carrier(5.0, sample_rate))
    carrier = np.concatenate([pilot, body])

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


def check_resonance_purity(audio_path: str) -> dict:
    with wave.open(audio_path, "rb") as wf:
        sample_rate = wf.getframerate()
        n_frames = wf.getnframes()
        n_channels = wf.getnchannels()
        raw = wf.readframes(n_frames)

    samples = np.frombuffer(raw, dtype=np.int16).astype(np.float64)
    if n_channels > 1:
        samples = samples[::n_channels]

    window_size = min(len(samples), 4096 * 4)
    segment = samples[:window_size]
    windowed = segment * np.hanning(len(segment))

    spectrum = np.abs(np.fft.rfft(windowed))
    freqs = np.fft.rfftfreq(len(segment), 1.0 / sample_rate)

    target_hz = VILLAGE_STANDARD_HZ
    band_width = 20
    band_mask = (freqs >= target_hz - band_width) & (freqs <= target_hz + band_width)
    noise_mask = ~band_mask & (freqs > 50)

    signal_power = np.mean(spectrum[band_mask] ** 2) if np.any(band_mask) else 0
    noise_power = np.mean(spectrum[noise_mask] ** 2) if np.any(noise_mask) else 1e-10

    snr_db = 10 * np.log10(signal_power / noise_power) if noise_power > 0 else 0

    harmonic_2_mask = (freqs >= 864 - band_width) & (freqs <= 864 + band_width)
    harmonic_2_power = np.mean(spectrum[harmonic_2_mask] ** 2) if np.any(harmonic_2_mask) else 0

    if snr_db >= 15:
        quality = "Clear"
        warning = None
    elif snr_db >= 8:
        quality = "Acceptable"
        warning = None
    else:
        quality = "Muddled"
        warning = "[INTERFERENCE]: Signal Muddled. Check Mac 2012 Volume or Room Acoustics."

    return {
        "snr_db": round(snr_db, 1),
        "signal_power": round(float(signal_power), 1),
        "noise_power": round(float(noise_power), 1),
        "harmonic_864_power": round(float(harmonic_2_power), 1),
        "quality": quality,
        "warning": warning,
    }


def find_harmonic_pockets(audio_path: str, fft_size: int = 8192) -> dict:
    with wave.open(audio_path, "rb") as wf:
        sample_rate = wf.getframerate()
        n_frames = wf.getnframes()
        n_channels = wf.getnchannels()
        raw = wf.readframes(n_frames)

    samples = np.frombuffer(raw, dtype=np.int16).astype(np.float64)
    if n_channels > 1:
        samples = samples[1::n_channels]

    window_size = min(len(samples), fft_size * 4)
    segment = samples[:window_size]
    windowed = segment * np.hanning(len(segment))

    spectrum = np.abs(np.fft.rfft(windowed))
    freqs = np.fft.rfftfreq(len(segment), 1.0 / sample_rate)

    spectrum_db = 20 * np.log10(spectrum + 1e-10)
    max_db = np.max(spectrum_db)

    base = VILLAGE_STANDARD_HZ
    harmonic_freqs = [base, base * 2, base * 3, base * 0.5]
    harmonic_width = 15

    harmonic_mask = np.zeros(len(freqs), dtype=bool)
    for hf in harmonic_freqs:
        harmonic_mask |= (np.abs(freqs - hf) <= harmonic_width)

    pocket_mask = ~harmonic_mask & (freqs > 30) & (freqs < sample_rate / 2)

    pockets = []
    in_pocket = False
    pocket_start = 0
    threshold_db = max_db - 40

    for i in range(len(freqs)):
        if pocket_mask[i] and spectrum_db[i] < threshold_db:
            if not in_pocket:
                in_pocket = True
                pocket_start = i
        else:
            if in_pocket:
                in_pocket = False
                pocket_end = i
                if pocket_end - pocket_start >= 3:
                    center_freq = freqs[(pocket_start + pocket_end) // 2]
                    width_hz = freqs[pocket_end - 1] - freqs[pocket_start]
                    depth = max_db - np.mean(spectrum_db[pocket_start:pocket_end])
                    pockets.append({
                        "center_hz": round(float(center_freq), 1),
                        "width_hz": round(float(width_hz), 1),
                        "depth_db": round(float(depth), 1),
                        "bin_start": int(pocket_start),
                        "bin_end": int(pocket_end),
                    })

    if in_pocket:
        pocket_end = len(freqs)
        if pocket_end - pocket_start >= 3:
            center_freq = freqs[(pocket_start + pocket_end) // 2]
            width_hz = freqs[pocket_end - 1] - freqs[pocket_start]
            depth = max_db - np.mean(spectrum_db[pocket_start:pocket_end])
            pockets.append({
                "center_hz": round(float(center_freq), 1),
                "width_hz": round(float(width_hz), 1),
                "depth_db": round(float(depth), 1),
                "bin_start": int(pocket_start),
                "bin_end": int(pocket_end),
            })

    pockets.sort(key=lambda p: p["depth_db"], reverse=True)

    total_pocket_bins = sum(p["bin_end"] - p["bin_start"] for p in pockets)
    total_bins = len(freqs)
    pocket_ratio = total_pocket_bins / total_bins if total_bins > 0 else 0

    return {
        "pockets": pockets[:20],
        "total_pockets": len(pockets),
        "deepest_pocket_db": pockets[0]["depth_db"] if pockets else 0,
        "pocket_coverage": round(pocket_ratio * 100, 1),
        "is_stereo": n_channels > 1,
        "sample_rate": sample_rate,
        "fft_size": fft_size,
    }


def _generate_pn_sequence(passphrase: str, length: int) -> np.ndarray:
    seed = int(hashlib.sha256(("dsss:" + passphrase).encode()).hexdigest()[:8], 16)
    rng = np.random.RandomState(seed)
    return rng.choice([-1, 1], size=length).astype(np.int16)


def encode_stereo(carrier_path: str, payload: bytes, file_name: str, extension: str,
                  output_path: str, lsb_depth: int = 1, passphrase: str | None = None,
                  jitter: bool = False, vortex: bool = False,
                  chirp_sync: bool = False) -> str:
    if lsb_depth not in (1, 2):
        raise ValueError("lsb_depth must be 1 or 2")

    active_modes = sum([jitter, vortex, chirp_sync])
    if active_modes > 1:
        raise ValueError("Cannot use multiple scatter modes simultaneously (jitter, vortex, chirp_sync are mutually exclusive)")

    with wave.open(carrier_path, "rb") as wav_in:
        params = wav_in.getparams()
        n_channels = params.nchannels
        sampwidth = params.sampwidth
        n_frames = params.nframes
        raw_frames = wav_in.readframes(n_frames)

    if sampwidth != 2:
        raise ValueError(f"Only 16-bit WAV files are supported (got {sampwidth * 8}-bit).")
    if n_channels != 2:
        raise ValueError("Stereo encode requires a 2-channel WAV carrier. Use --stereo to generate one.")

    all_samples = np.frombuffer(raw_frames, dtype=np.int16).copy()
    left = all_samples[0::2]
    right = all_samples[1::2]
    total_samples = len(right)

    if passphrase is None:
        passphrase = _generate_hash_key()

    key = _derive_key(passphrase)
    checksum = _compute_md5(payload)
    header = _build_header(file_name, extension, len(payload), checksum, key,
                           jitter=jitter, vortex=vortex, chirp_sync=chirp_sync)

    bits_per_sample = lsb_depth
    ghost_offset = _compute_ghost_offset(passphrase, total_samples)
    effective_capacity = (total_samples - ghost_offset) * bits_per_sample
    total_bits = (HEADER_SIZE + len(payload)) * 8

    if total_bits > effective_capacity:
        raise ValueError(
            f"Payload too large: needs {total_bits:,} bits, "
            f"pocket channel has capacity for {effective_capacity:,} bits ({effective_capacity // 8:,} bytes) "
            f"at LSB depth {lsb_depth} (Ghost Offset: {ghost_offset:,} samples)."
        )

    dither_seed = int(hashlib.sha256(("dither:" + passphrase).encode()).hexdigest()[:8], 16)
    right = apply_dither_mask(right, seed=dither_seed)

    pn_chip_len = min(8, total_samples // (HEADER_SIZE * 8 // bits_per_sample + len(payload) * 8 // bits_per_sample + 1))
    pn_chip_len = max(1, pn_chip_len)

    header_bits = np.unpackbits(np.frombuffer(header, dtype=np.uint8))
    header_samples = HEADER_SIZE * 8 // bits_per_sample
    if lsb_depth == 2:
        pad_len = (2 - (len(header_bits) % 2)) % 2
        if pad_len:
            header_bits = np.concatenate([header_bits, np.zeros(pad_len, dtype=np.uint8)])
    _embed_bits_at(right, header_bits, ghost_offset, header_samples, lsb_depth)

    data_bits = np.unpackbits(np.frombuffer(payload, dtype=np.uint8))
    if lsb_depth == 2:
        pad_len = (2 - (len(data_bits) % 2)) % 2
        if pad_len:
            data_bits = np.concatenate([data_bits, np.zeros(pad_len, dtype=np.uint8)])
    data_samples_needed = len(data_bits) // bits_per_sample

    scatter_info = ""
    if chirp_sync and data_samples_needed > 0:
        data_start = ghost_offset + header_samples
        chirp_peaks = _load_or_detect_chirp_peaks(carrier_path, right)
        chirp_map = _generate_chirp_map(right, data_samples_needed, chirp_peaks,
                                        passphrase, lsb_depth, data_start, total_samples)
        bit_offset = 0
        for (pos, chunk_len) in chirp_map:
            chunk_bits = data_bits[bit_offset * bits_per_sample:(bit_offset + chunk_len) * bits_per_sample]
            _embed_bits_at(right, chunk_bits, pos, chunk_len, lsb_depth)
            bit_offset += chunk_len
        scatter_info = f"\n         Chirp Sync: Active ({len(chirp_map)} chunks synced to {len(chirp_peaks)} chirp peaks)"
    elif vortex and data_samples_needed > 0:
        data_start = ghost_offset + header_samples
        vortex_map = _generate_vortex_map(passphrase, data_samples_needed,
                                          data_start, total_samples)
        bit_offset = 0
        for (pos, chunk_len) in vortex_map:
            chunk_bits = data_bits[bit_offset * bits_per_sample:(bit_offset + chunk_len) * bits_per_sample]
            _embed_bits_at(right, chunk_bits, pos, chunk_len, lsb_depth)
            bit_offset += chunk_len
        scatter_info = f"\n         Vortex Scatter: Active ({len(vortex_map)} spiral arms, 432 Hz harmonic distribution)"
    elif jitter and data_samples_needed > 0:
        data_start = ghost_offset + header_samples
        jitter_map = _generate_jitter_map(passphrase, data_samples_needed,
                                          data_start, total_samples)
        bit_offset = 0
        for (pos, chunk_len) in jitter_map:
            chunk_bits = data_bits[bit_offset * bits_per_sample:(bit_offset + chunk_len) * bits_per_sample]
            _embed_bits_at(right, chunk_bits, pos, chunk_len, lsb_depth)
            bit_offset += chunk_len
        scatter_info = f"\n         Fly Jitter: Active ({len(jitter_map)} chunks scattered)"
    else:
        data_start = ghost_offset + header_samples
        _embed_bits_at(right, data_bits, data_start, data_samples_needed, lsb_depth)

    all_samples[1::2] = right

    with wave.open(output_path, "wb") as wav_out:
        wav_out.setparams(params)
        wav_out.writeframes(all_samples.tobytes())

    if chirp_sync:
        _copy_chirpmap_sidecar(carrier_path, output_path)

    full_payload_size = HEADER_SIZE + len(payload)
    capacity = total_samples * bits_per_sample
    usage_pct = (total_bits / capacity) * 100
    print(f"  [VOID] Stereo Pocket encoding complete:")
    print(f"         Carrier:    {carrier_path} (STEREO)")
    print(f"         Output:     {output_path}")
    print(f"         Channel:    RIGHT (Adriana Pocket)")
    print(f"         LSB depth:  {lsb_depth}")
    print(f"         Capacity:   {capacity // 8:,} bytes")
    print(f"         Used:       {full_payload_size:,} bytes ({usage_pct:.1f}%)")
    print(f"         Checksum:   {checksum}")
    print(f"         Ghost Offset: {ghost_offset:,} samples")
    print(f"         Dither Mask: Applied (seed {dither_seed}){scatter_info}")

    return passphrase


def decode_stereo(stego_path: str, passphrase: str, lsb_depth: int = 1) -> tuple[bytes, str, str]:
    if lsb_depth not in (1, 2):
        raise ValueError("lsb_depth must be 1 or 2")

    key = _derive_key(passphrase)

    with wave.open(stego_path, "rb") as wav_in:
        params = wav_in.getparams()
        n_channels = params.nchannels
        n_frames = params.nframes
        sampwidth = params.sampwidth
        raw_frames = wav_in.readframes(n_frames)

    if sampwidth != 2:
        raise ValueError(f"Only 16-bit WAV files are supported (got {sampwidth * 8}-bit).")
    if n_channels != 2:
        raise ValueError("Stereo decode requires a 2-channel WAV file.")

    all_samples = np.frombuffer(raw_frames, dtype=np.int16)
    right = all_samples[1::2]
    total_samples = len(right)
    bits_per_sample = lsb_depth

    ghost_offset = _compute_ghost_offset(passphrase, total_samples)
    header_samples = HEADER_SIZE * 8 // bits_per_sample

    header_raw_bits = _extract_bits_at(right, ghost_offset, header_samples, lsb_depth)
    header_bits = header_raw_bits[:HEADER_SIZE * 8]
    header_bytes = np.packbits(header_bits).tobytes()[:HEADER_SIZE]
    name_ext, data_size, stored_checksum, has_jitter, has_vortex, has_chirp_sync = _parse_header(header_bytes, key)

    data_samples_needed = (data_size * 8 + bits_per_sample - 1) // bits_per_sample

    if has_chirp_sync and data_samples_needed > 0:
        data_start = ghost_offset + header_samples
        chirp_peaks = _load_or_detect_chirp_peaks(stego_path, right)
        chirp_map = _generate_chirp_map(right, data_samples_needed, chirp_peaks,
                                        passphrase, lsb_depth, data_start, total_samples)
        collected_bits = []
        for (pos, chunk_len) in chirp_map:
            chunk_raw = _extract_bits_at(right, pos, chunk_len, lsb_depth)
            collected_bits.append(chunk_raw)
        all_data_bits = np.concatenate(collected_bits)[:data_size * 8]
        jitter_info = f" (Chirp Sync: {len(chirp_map)} chunks)"
    elif has_vortex and data_samples_needed > 0:
        data_start = ghost_offset + header_samples
        vortex_map = _generate_vortex_map(passphrase, data_samples_needed,
                                          data_start, total_samples)
        collected_bits = []
        for (pos, chunk_len) in vortex_map:
            chunk_raw = _extract_bits_at(right, pos, chunk_len, lsb_depth)
            collected_bits.append(chunk_raw)
        all_data_bits = np.concatenate(collected_bits)[:data_size * 8]
        jitter_info = f" (Vortex Scatter: {len(vortex_map)} spiral arms)"
    elif has_jitter and data_samples_needed > 0:
        data_start = ghost_offset + header_samples
        jitter_map = _generate_jitter_map(passphrase, data_samples_needed,
                                          data_start, total_samples)
        collected_bits = []
        for (pos, chunk_len) in jitter_map:
            chunk_raw = _extract_bits_at(right, pos, chunk_len, lsb_depth)
            collected_bits.append(chunk_raw)
        all_data_bits = np.concatenate(collected_bits)[:data_size * 8]
        jitter_info = f" (Fly Jitter: {len(jitter_map)} chunks)"
    else:
        data_start = ghost_offset + header_samples
        all_data_bits_raw = _extract_bits_at(right, data_start, data_samples_needed, lsb_depth)
        all_data_bits = all_data_bits_raw[:data_size * 8]
        jitter_info = ""

    compressed_data = np.packbits(all_data_bits).tobytes()[:data_size]

    computed_checksum = _compute_md5(compressed_data)
    if computed_checksum != stored_checksum:
        raise ValueError(
            f"Resonance verification FAILED!\n"
            f"  Expected: {stored_checksum}\n"
            f"  Computed: {computed_checksum}\n"
            f"  Data may be corrupted."
        )

    print(f"  [VOID] Stereo Pocket decoding complete:")
    print(f"         Channel:    RIGHT (Adriana Pocket)")
    print(f"         File:       {name_ext}")
    print(f"         Data size:  {data_size:,} bytes (compressed)")
    print(f"         Checksum:   VERIFIED{jitter_info}")

    return compressed_data, name_ext, stored_checksum


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
    total_samples = len(samples)
    bits_per_sample = lsb_depth

    ghost_offset = _compute_ghost_offset(passphrase, total_samples)
    header_samples = HEADER_SIZE * 8 // bits_per_sample

    header_raw_bits = _extract_bits_at(samples, ghost_offset, header_samples, lsb_depth)
    header_bits = header_raw_bits[:HEADER_SIZE * 8]
    header_bytes = np.packbits(header_bits).tobytes()[:HEADER_SIZE]
    name_ext, data_size, stored_checksum, has_jitter, has_vortex, has_chirp_sync = _parse_header(header_bytes, key)

    data_samples_needed = (data_size * 8 + bits_per_sample - 1) // bits_per_sample

    if has_chirp_sync and data_samples_needed > 0:
        data_start = ghost_offset + header_samples
        chirp_peaks = _load_or_detect_chirp_peaks(stego_path, samples)
        chirp_map = _generate_chirp_map(samples, data_samples_needed, chirp_peaks,
                                        passphrase, lsb_depth, data_start, total_samples)
        collected_bits = []
        for (pos, chunk_len) in chirp_map:
            chunk_raw = _extract_bits_at(samples, pos, chunk_len, lsb_depth)
            collected_bits.append(chunk_raw)
        all_data_bits = np.concatenate(collected_bits)[:data_size * 8]
        jitter_info = f" (Chirp Sync: {len(chirp_map)} chunks)"
    elif has_vortex and data_samples_needed > 0:
        data_start = ghost_offset + header_samples
        vortex_map = _generate_vortex_map(passphrase, data_samples_needed,
                                          data_start, total_samples)

        collected_bits = []
        for (pos, chunk_len) in vortex_map:
            chunk_raw = _extract_bits_at(samples, pos, chunk_len, lsb_depth)
            collected_bits.append(chunk_raw)

        all_data_bits = np.concatenate(collected_bits)[:data_size * 8]
        jitter_info = f" (Vortex Scatter: {len(vortex_map)} spiral arms)"
    elif has_jitter and data_samples_needed > 0:
        data_start = ghost_offset + header_samples
        jitter_map = _generate_jitter_map(passphrase, data_samples_needed,
                                          data_start, total_samples)

        collected_bits = []
        for (pos, chunk_len) in jitter_map:
            chunk_raw = _extract_bits_at(samples, pos, chunk_len, lsb_depth)
            collected_bits.append(chunk_raw)

        all_data_bits = np.concatenate(collected_bits)[:data_size * 8]
        jitter_info = f" (Fly Jitter: {len(jitter_map)} chunks)"
    else:
        data_start = ghost_offset + header_samples
        all_data_bits_raw = _extract_bits_at(samples, data_start, data_samples_needed, lsb_depth)
        all_data_bits = all_data_bits_raw[:data_size * 8]
        jitter_info = ""

    compressed_data = np.packbits(all_data_bits).tobytes()[:data_size]

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
    print(f"         Checksum:   VERIFIED{jitter_info}")

    return compressed_data, name_ext, stored_checksum
