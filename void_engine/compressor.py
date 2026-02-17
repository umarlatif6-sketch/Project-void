import zlib
import lzma
import os

CHUNK_SIZE = 64 * 1024 * 1024


def compress_file(file_path: str) -> tuple[bytes, str, str, int]:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    original_size = os.path.getsize(file_path)
    file_name = os.path.basename(file_path)
    name, extension = os.path.splitext(file_name)

    with open(file_path, "rb") as f:
        raw_data = f.read()

    zlib_compressed = zlib.compress(raw_data, level=9)

    try:
        lzma_compressed = lzma.compress(raw_data, preset=9)
    except Exception:
        lzma_compressed = None

    if lzma_compressed and len(lzma_compressed) < len(zlib_compressed):
        compressed = b"LZMA" + lzma_compressed
        algo = "lzma"
    else:
        compressed = b"ZLIB" + zlib_compressed
        algo = "zlib"

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
