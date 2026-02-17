import zlib
import os


def compress_file(file_path: str) -> tuple[bytes, str, str, int]:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    original_size = os.path.getsize(file_path)
    file_name = os.path.basename(file_path)
    name, extension = os.path.splitext(file_name)

    with open(file_path, "rb") as f:
        raw_data = f.read()

    compressed = zlib.compress(raw_data, level=9)

    ratio = (1 - len(compressed) / original_size) * 100 if original_size > 0 else 0
    print(f"  [VOID] Compression complete:")
    print(f"         Original size:   {original_size:,} bytes")
    print(f"         Compressed size: {len(compressed):,} bytes")
    print(f"         Ratio:           {ratio:.1f}% reduction")

    return compressed, name, extension, original_size


def decompress_data(compressed_data: bytes) -> bytes:
    return zlib.decompress(compressed_data)
