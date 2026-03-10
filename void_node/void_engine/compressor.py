import zlib
import lzma
import os

CHUNK_SIZE = 8 * 1024 * 1024
ADAPTIVE_LZMA_THRESHOLD = 100 * 1024 * 1024
PROGRESS_THRESHOLD = 10 * 1024 * 1024


def _get_available_ram() -> int:
    try:
        with open("/proc/meminfo", "r") as f:
            for line in f:
                if line.startswith("MemAvailable:"):
                    return int(line.split()[1]) * 1024
    except Exception:
        pass
    try:
        pages = os.sysconf("SC_AVPHYS_PAGES")
        page_size = os.sysconf("SC_PAGE_SIZE")
        if pages > 0 and page_size > 0:
            return pages * page_size
    except Exception:
        pass
    return 2 * 1024 * 1024 * 1024


def _stream_compress_zlib(file_path: str, file_size: int, show_progress: bool) -> bytes:
    compressor = zlib.compressobj(level=9)
    chunks = []
    processed = 0
    last_pct = 0

    with open(file_path, "rb") as f:
        while True:
            block = f.read(CHUNK_SIZE)
            if not block:
                break
            chunks.append(compressor.compress(block))
            processed += len(block)
            if show_progress:
                pct = int((processed / file_size) * 100)
                if pct >= last_pct + 10:
                    last_pct = pct - (pct % 10)
                    print(f"         [PULSE] zlib compression... {last_pct}%")

    chunks.append(compressor.flush())
    if show_progress and last_pct < 100:
        print(f"         [PULSE] zlib compression... 100%")
    return b"".join(chunks)


def _stream_compress_lzma(file_path: str, file_size: int, show_progress: bool) -> bytes:
    compressor = lzma.LZMACompressor(preset=9)
    chunks = []
    processed = 0
    last_pct = 0

    with open(file_path, "rb") as f:
        while True:
            block = f.read(CHUNK_SIZE)
            if not block:
                break
            chunks.append(compressor.compress(block))
            processed += len(block)
            if show_progress:
                pct = int((processed / file_size) * 100)
                if pct >= last_pct + 10:
                    last_pct = pct - (pct % 10)
                    print(f"         [PULSE] lzma compression... {last_pct}%")

    chunks.append(compressor.flush())
    if show_progress and last_pct < 100:
        print(f"         [PULSE] lzma compression... 100%")
    return b"".join(chunks)


def compress_file(file_path: str, deep: bool = False, low_power: bool = False) -> tuple[bytes, str, str, int]:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    original_size = os.path.getsize(file_path)
    file_name = os.path.basename(file_path)
    name, extension = os.path.splitext(file_name)

    available = _get_available_ram()
    if original_size > available * 0.5:
        print(f"  [RESONANCE WARNING]: System RAM near limit. "
              f"File is {original_size // (1024*1024):,} MB, "
              f"available RAM ~{available // (1024*1024):,} MB. "
              f"Using streaming compression to stay safe.")

    show_progress = original_size > PROGRESS_THRESHOLD

    if original_size > 500 * 1024 * 1024:
        print(f"  [RESONANCE WARNING]: Large Void detected ({original_size / (1024*1024):.0f} MB). "
              f"Ensuring 18-hour Pulse is active...")

    if show_progress:
        print(f"  [VOID] Compressing {original_size:,} bytes...")

    zlib_compressed = _stream_compress_zlib(file_path, original_size, show_progress)

    skip_lzma = (original_size > ADAPTIVE_LZMA_THRESHOLD and not deep) or low_power
    if low_power:
        print(f"  [VOID] Low-Power Resonance active — LZMA disabled.")
    lzma_compressed = None

    if skip_lzma:
        print(f"  [VOID] Skipping LZMA (file > 100 MB). "
              f"Use deep=True to force LZMA compression.")
    else:
        try:
            lzma_compressed = _stream_compress_lzma(file_path, original_size, show_progress)
        except Exception:
            lzma_compressed = None

    if lzma_compressed and len(lzma_compressed) < len(zlib_compressed):
        compressed = b"LZMA" + lzma_compressed
        algo = "lzma"
        del zlib_compressed
    else:
        compressed = b"ZLIB" + zlib_compressed
        algo = "zlib"
        if lzma_compressed is not None:
            del lzma_compressed

    ratio = (1 - (len(compressed) - 4) / original_size) * 100 if original_size > 0 else 0
    print(f"  [VOID] Compression complete ({algo}):")
    print(f"         Original size:   {original_size:,} bytes")
    print(f"         Compressed size: {len(compressed):,} bytes")
    print(f"         Ratio:           {ratio:.1f}% reduction")

    return compressed, name, extension, original_size


def compress_bytes(data: bytes) -> bytes:
    compressed = zlib.compress(data, level=9)
    return b"ZLIB" + compressed


def decompress_data(compressed_data: bytes) -> bytes:
    tag = compressed_data[:4]
    payload = compressed_data[4:]

    if tag == b"LZMA":
        return lzma.decompress(payload)
    elif tag == b"ZLIB":
        return zlib.decompress(payload)
    else:
        return zlib.decompress(compressed_data)
