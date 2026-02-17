import os
import sys

from compressor import compress_file, decompress_data
from steganography import encode, decode
from keep_alive import start_pulse

BANNER = r"""
 ╔══════════════════════════════════════════════════════╗
 ║              T H E   V O I D   E N G I N E          ║
 ║         Modular Steganography System  v1.0           ║
 ╠══════════════════════════════════════════════════════╣
 ║  Hide any file inside an audio signal.               ║
 ║  LSB encoding  |  zlib compression  |  MD5 verified  ║
 ╚══════════════════════════════════════════════════════╝
"""

INPUT_DIR = "input_files"
OUTPUT_DIR = "output_audio"


def list_files(directory: str, ext: str | None = None) -> list[str]:
    if not os.path.isdir(directory):
        return []
    files = os.listdir(directory)
    if ext:
        files = [f for f in files if f.lower().endswith(ext)]
    return sorted(files)


def pick_file(directory: str, prompt: str, ext: str | None = None) -> str | None:
    files = list_files(directory, ext)
    if not files:
        print(f"\n  No files found in '{directory}/'", end="")
        if ext:
            print(f" (filter: *{ext})", end="")
        print()
        return None

    print(f"\n  Files in '{directory}/':")
    for i, f in enumerate(files, 1):
        size = os.path.getsize(os.path.join(directory, f))
        print(f"    [{i}] {f}  ({size:,} bytes)")

    while True:
        choice = input(f"\n  {prompt} (number or 'q' to cancel): ").strip()
        if choice.lower() == "q":
            return None
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(files):
                return os.path.join(directory, files[idx])
        except ValueError:
            pass
        print("  Invalid choice, try again.")


def encode_flow():
    print("\n" + "=" * 56)
    print("  ENCODE — Hide a file inside audio")
    print("=" * 56)

    carrier = pick_file(INPUT_DIR, "Select carrier WAV file", ext=".wav")
    if not carrier:
        print("\n  Place a .wav file in 'input_files/' and try again.")
        return

    print()
    payload_path = pick_file(INPUT_DIR, "Select file to hide")
    if not payload_path:
        return

    while True:
        depth_str = input("\n  LSB depth (1 or 2, default=1): ").strip()
        if depth_str == "" or depth_str == "1":
            lsb_depth = 1
            break
        elif depth_str == "2":
            lsb_depth = 2
            break
        print("  Enter 1 or 2.")

    print("\n  [VOID] Compressing payload...")
    compressed, name, ext, orig_size = compress_file(payload_path)

    base_name = os.path.splitext(os.path.basename(carrier))[0]
    output_path = os.path.join(OUTPUT_DIR, f"{base_name}_void.wav")

    print("\n  [VOID] Encoding into carrier audio...")
    try:
        checksum = encode(carrier, compressed, name, ext, output_path, lsb_depth)
    except ValueError as e:
        print(f"\n  [ERROR] {e}")
        return

    out_size = os.path.getsize(output_path)
    print(f"\n  Output saved: {output_path} ({out_size:,} bytes)")
    print(f"  Resonance ID (MD5): {checksum}")
    print("  Encoding COMPLETE.")


def decode_flow():
    print("\n" + "=" * 56)
    print("  DECODE — Extract a file from audio")
    print("=" * 56)

    stego = pick_file(OUTPUT_DIR, "Select encoded WAV file", ext=".wav")
    if not stego:
        stego = pick_file(INPUT_DIR, "Select encoded WAV file", ext=".wav")
    if not stego:
        print("\n  No encoded WAV files found.")
        return

    while True:
        depth_str = input("\n  LSB depth used during encoding (1 or 2, default=1): ").strip()
        if depth_str == "" or depth_str == "1":
            lsb_depth = 1
            break
        elif depth_str == "2":
            lsb_depth = 2
            break
        print("  Enter 1 or 2.")

    print("\n  [VOID] Extracting data from audio...")
    try:
        compressed_data, name_ext, checksum = decode(stego, lsb_depth)
    except ValueError as e:
        print(f"\n  [ERROR] {e}")
        return

    print("\n  [VOID] Decompressing payload...")
    try:
        original_data = decompress_data(compressed_data)
    except Exception as e:
        print(f"\n  [ERROR] Decompression failed: {e}")
        return

    output_path = os.path.join(OUTPUT_DIR, name_ext)
    with open(output_path, "wb") as f:
        f.write(original_data)

    print(f"\n  File restored: {output_path} ({len(original_data):,} bytes)")
    print(f"  Resonance ID (MD5): {checksum}")
    print("  Decoding COMPLETE.")


def main():
    os.makedirs(INPUT_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    start_pulse()
    print(BANNER)

    while True:
        print("\n  ┌─────────────────────────────┐")
        print("  │  [1]  Encode File to Audio  │")
        print("  │  [2]  Decode Audio to File  │")
        print("  │  [q]  Quit                  │")
        print("  └─────────────────────────────┘")
        choice = input("\n  Select option: ").strip().lower()

        if choice == "1":
            encode_flow()
        elif choice == "2":
            decode_flow()
        elif choice == "q":
            print("\n  [VOID] Engine shutting down.\n")
            sys.exit(0)
        else:
            print("  Invalid option.")


if __name__ == "__main__":
    main()
