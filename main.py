import os
import sys

from void_engine.compressor import compress_file, decompress_data
from void_engine.stega import encode, decode
from void_engine.keep_alive import start_pulse
from void_engine.calculator import analyze_carrier, print_analysis, append_to_log

BANNER = r"""
 ╔══════════════════════════════════════════════════════════╗
 ║               P R O J E C T    V O I D                  ║
 ║         Modular Steganography Engine  v2.0               ║
 ╠══════════════════════════════════════════════════════════╣
 ║  Hide any file inside an audio signal.                   ║
 ║  LSB encoding | zlib+lzma | ChaCha20 header | MD5 hash  ║
 ╠══════════════════════════════════════════════════════════╣
 ║  Modules: Void-Compressor | Stega Engine | Pulse-Wrapper ║
 ║  Planned: Silk Web | Graphene Suit                       ║
 ╚══════════════════════════════════════════════════════════╝
"""

INPUT_DIR = "input_files"
OUTPUT_DIR = "output_audio"


def list_files(directory: str, ext: str | None = None) -> list[str]:
    if not os.path.isdir(directory):
        return []
    files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
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
        if size >= 1_073_741_824:
            size_str = f"{size / 1_073_741_824:.2f} GB"
        elif size >= 1_048_576:
            size_str = f"{size / 1_048_576:.1f} MB"
        elif size >= 1024:
            size_str = f"{size / 1024:.1f} KB"
        else:
            size_str = f"{size:,} bytes"
        print(f"    [{i}] {f}  ({size_str})")

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
    print("\n" + "=" * 60)
    print("  ENCODE — Hide a file inside a high-fidelity audio track")
    print("=" * 60)

    carrier = pick_file(INPUT_DIR, "Select carrier WAV file", ext=".wav")
    if not carrier:
        print("\n  Place a 16-bit .wav file in 'input_files/' and try again.")
        return

    print()
    payload_path = pick_file(INPUT_DIR, "Select file to hide")
    if not payload_path:
        return

    while True:
        depth_str = input("\n  LSB depth (1=stealth, 2=capacity, default=1): ").strip()
        if depth_str == "" or depth_str == "1":
            lsb_depth = 1
            break
        elif depth_str == "2":
            lsb_depth = 2
            break
        print("  Enter 1 or 2.")

    print("\n  [VOID] Compressing payload (zlib+lzma, selecting best)...")
    compressed, name, ext, orig_size = compress_file(payload_path)

    base_name = os.path.splitext(os.path.basename(carrier))[0]
    output_path = os.path.join(OUTPUT_DIR, f"{base_name}_void.wav")

    print("\n  [VOID] Encoding into carrier audio...")
    try:
        hash_key = encode(carrier, compressed, name, ext, output_path, lsb_depth)
    except ValueError as e:
        print(f"\n  [ERROR] {e}")
        return

    out_size = os.path.getsize(output_path)
    print(f"\n  {'=' * 60}")
    print(f"  OUTPUT SAVED: {output_path} ({out_size:,} bytes)")
    print(f"  {'=' * 60}")
    print(f"  HASH KEY (save this — required for decoding):")
    print(f"  >>> {hash_key} <<<")
    print(f"  {'=' * 60}")
    print(f"  Encoding COMPLETE.")


def decode_flow():
    print("\n" + "=" * 60)
    print("  DECODE — Extract a file from audio using your Hash Key")
    print("=" * 60)

    stego = pick_file(OUTPUT_DIR, "Select encoded WAV file", ext=".wav")
    if not stego:
        stego = pick_file(INPUT_DIR, "Select encoded WAV file", ext=".wav")
    if not stego:
        print("\n  No encoded WAV files found.")
        return

    hash_key = input("\n  Enter your Hash Key: ").strip()
    if not hash_key:
        print("  No key provided. Aborting.")
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
        compressed_data, name_ext, checksum = decode(stego, hash_key, lsb_depth)
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
    print(f"  Checksum:      {checksum}")
    print("  Decoding COMPLETE.")


def capacity_flow():
    print("\n" + "=" * 60)
    print("  RESONANCE METER — Check Carrier Capacity")
    print("=" * 60)

    wav_file = pick_file(INPUT_DIR, "Select WAV file to analyze", ext=".wav")
    if not wav_file:
        wav_file = pick_file(OUTPUT_DIR, "Select WAV file to analyze", ext=".wav")
    if not wav_file:
        print("\n  No WAV files found.")
        return

    try:
        info = analyze_carrier(wav_file)
        print_analysis(info)
        append_to_log(info)
    except Exception as e:
        print(f"\n  [ERROR] {e}")


def main():
    os.makedirs(INPUT_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    start_pulse()
    print(BANNER)

    while True:
        print("\n  ┌──────────────────────────────────────┐")
        print("  │  [1]  Encode File to Audio           │")
        print("  │  [2]  Decode Audio to File (Hash Key)│")
        print("  │  [3]  Check Capacity (Resonance)     │")
        print("  │  [q]  Quit                           │")
        print("  └──────────────────────────────────────┘")
        choice = input("\n  Select option: ").strip().lower()

        if choice == "1":
            encode_flow()
        elif choice == "2":
            decode_flow()
        elif choice == "3":
            capacity_flow()
        elif choice == "q":
            print("\n  [VOID] Engine shutting down.\n")
            sys.exit(0)
        else:
            print("  Invalid option.")


if __name__ == "__main__":
    main()
