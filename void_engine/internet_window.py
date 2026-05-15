"""
Internet Window — PROJECT VOID
Z-Axis Knowledge Capture System

Instead of giving Mesa agents a live internet connection (expensive, transient,
unreliable), we give them a WINDOW — a compressed video file that contains an
entire search session's worth of internet content.

The agents don't browse the internet. They browse the VIDEO.
The video IS their internet.

Architecture:
  1. CAPTURE: Search the internet (via Manus or manual), collect content
  2. ENCODE: Compress all collected content into a Z-axis video file
     - Each frame = one page/paper/article
     - Metadata encoded in first frame (index)
     - Content encoded as pixel data (lossless, decodable)
  3. STORE: The video file IS the agent's knowledge window
  4. DECODE: Agents read the video to access external knowledge
  5. UPDATE: New sessions produce new window files (versioned)

Hash Architecture:
  - Internal (286 hash / Al-Jabr): Repository state, void architecture
  - External (256 hash / SHA-256): Internet content, captured knowledge
  - Bridge (Adriana/OpenClaw): Translation layer between the two hash spaces

The window is like a newspaper for AI:
  - You don't give them a phone line
  - You give them today's edition
  - Compressed. Finite. Sovereign.

Requires: numpy, Pillow (pre-installed in Manus sandbox)
"""

import hashlib
import json
import logging
import os
import struct
import subprocess
import sys
import tarfile
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from io import BytesIO
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)

# --- Constants ---

WINDOW_STORAGE_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "internet_windows")
FRAME_WIDTH = 1920
FRAME_HEIGHT = 1080
PIXELS_PER_FRAME = FRAME_WIDTH * FRAME_HEIGHT
BYTES_PER_FRAME = PIXELS_PER_FRAME * 3  # RGB = 3 bytes per pixel
MAGIC_HEADER = b"VOID_WINDOW_v1"
INDEX_FRAME_MARKER = b"INDEX_FRAME_"

# --- Data Structures ---

@dataclass
class CapturedPage:
    """A single page/paper/article captured from the internet."""
    url: str
    title: str
    content: str  # Full text content
    snippet: str  # Short summary
    source_type: str  # "paper", "article", "wiki", "huggingface", etc.
    field: str  # Academic/knowledge field
    captured_at: str
    sha256: str = ""  # 256 hash of content (external hash space)

    def __post_init__(self):
        if not self.sha256:
            self.sha256 = hashlib.sha256(
                self.content.encode("utf-8")
            ).hexdigest()

    def to_dict(self) -> Dict:
        return {
            "url": self.url,
            "title": self.title,
            "content_length": len(self.content),
            "snippet": self.snippet[:200],
            "source_type": self.source_type,
            "field": self.field,
            "captured_at": self.captured_at,
            "sha256": self.sha256,
        }

    def to_bytes(self) -> bytes:
        """Serialize the full page to bytes for video encoding."""
        data = json.dumps({
            "url": self.url,
            "title": self.title,
            "content": self.content,
            "snippet": self.snippet,
            "source_type": self.source_type,
            "field": self.field,
            "captured_at": self.captured_at,
            "sha256": self.sha256,
        }, ensure_ascii=False).encode("utf-8")
        # Prefix with length for clean decoding
        return struct.pack(">I", len(data)) + data

    @classmethod
    def from_bytes(cls, data: bytes) -> "CapturedPage":
        """Deserialize from bytes."""
        if len(data) > 4:
            possible_len = struct.unpack(">I", data[:4])[0]
            if possible_len < len(data) and possible_len > 0:
                try:
                    json_data = json.loads(data[4:4+possible_len].decode("utf-8"))
                    return cls(**json_data)
                except (json.JSONDecodeError, UnicodeDecodeError):
                    pass
        json_data = json.loads(data.decode("utf-8"))
        return cls(**json_data)


@dataclass
class WindowIndex:
    """
    Index frame — the first frame of every Internet Window video.
    Contains metadata about all pages in the window.
    """
    window_id: str
    created_at: str
    session_name: str
    total_pages: int
    total_bytes: int
    source_concepts: List[str]  # Void concepts that triggered this search
    fields_covered: List[str]
    page_manifest: List[Dict]  # Minimal info per page (title, url, frame_number)
    sha256_composite: str  # Hash of all content hashes combined

    def to_bytes(self) -> bytes:
        data = json.dumps({
            "magic": MAGIC_HEADER.decode(),
            "window_id": self.window_id,
            "created_at": self.created_at,
            "session_name": self.session_name,
            "total_pages": self.total_pages,
            "total_bytes": self.total_bytes,
            "source_concepts": self.source_concepts,
            "fields_covered": self.fields_covered,
            "page_manifest": self.page_manifest,
            "sha256_composite": self.sha256_composite,
        }, ensure_ascii=False).encode("utf-8")
        return struct.pack(">I", len(data)) + data

    @classmethod
    def from_bytes(cls, data: bytes) -> "WindowIndex":
        # data may or may not have length prefix
        if len(data) > 4:
            possible_len = struct.unpack(">I", data[:4])[0]
            if possible_len < len(data) and possible_len > 0:
                try:
                    json_data = json.loads(data[4:4+possible_len].decode("utf-8"))
                    json_data.pop("magic", None)
                    return cls(**json_data)
                except (json.JSONDecodeError, UnicodeDecodeError):
                    pass
        # Try raw (no prefix)
        json_data = json.loads(data.decode("utf-8"))
        json_data.pop("magic", None)
        return cls(**json_data)

    def to_dict(self) -> Dict:
        return {
            "window_id": self.window_id,
            "created_at": self.created_at,
            "session_name": self.session_name,
            "total_pages": self.total_pages,
            "total_bytes": self.total_bytes,
            "source_concepts": self.source_concepts,
            "fields_covered": self.fields_covered,
            "sha256_composite": self.sha256_composite,
            "page_manifest": self.page_manifest,
        }


@dataclass
class InternetWindow:
    """
    A complete Internet Window — a captured moment of external knowledge.
    Can be encoded to video and decoded back.
    """
    index: Optional[WindowIndex] = None
    pages: List[CapturedPage] = field(default_factory=list)

    def add_page(self, page: CapturedPage):
        self.pages.append(page)

    def build_index(self, session_name: str, source_concepts: List[str]) -> WindowIndex:
        """Build the index from current pages."""
        now = datetime.now(timezone.utc).isoformat()
        fields = list(set(p.field for p in self.pages))
        total_bytes = sum(len(p.content.encode("utf-8")) for p in self.pages)

        # Composite hash: hash of all individual hashes
        combined = "".join(p.sha256 for p in self.pages)
        composite_hash = hashlib.sha256(combined.encode()).hexdigest()

        # Window ID from composite hash
        window_id = f"WIN-{composite_hash[:12]}"

        manifest = []
        for i, page in enumerate(self.pages):
            manifest.append({
                "frame": i + 1,  # Frame 0 is the index
                "title": page.title[:100],
                "url": page.url,
                "field": page.field,
                "sha256": page.sha256[:16],
                "size": len(page.content),
            })

        self.index = WindowIndex(
            window_id=window_id,
            created_at=now,
            session_name=session_name,
            total_pages=len(self.pages),
            total_bytes=total_bytes,
            source_concepts=source_concepts,
            fields_covered=fields,
            page_manifest=manifest,
            sha256_composite=composite_hash,
        )
        return self.index


# --- Encoder ---

def _bytes_to_frames(data: bytes) -> List[np.ndarray]:
    """Convert raw bytes into video frames (RGB pixel arrays)."""
    frames = []
    offset = 0
    while offset < len(data):
        chunk = data[offset:offset + BYTES_PER_FRAME]
        # Pad with zeros if last chunk is incomplete
        if len(chunk) < BYTES_PER_FRAME:
            chunk = chunk + b'\x00' * (BYTES_PER_FRAME - len(chunk))
        # Reshape to frame
        frame = np.frombuffer(chunk, dtype=np.uint8).reshape(
            (FRAME_HEIGHT, FRAME_WIDTH, 3)
        )
        frames.append(frame.copy())
        offset += BYTES_PER_FRAME
    return frames


def encode_window(
    window: InternetWindow,
    output_path: str,
    session_name: str = "unnamed",
    source_concepts: List[str] = None,
) -> str:
    """
    Encode an InternetWindow into a lossless video file.

    Frame 0: Index (metadata, manifest)
    Frame 1-N: One page per frame (or multiple frames for large pages)

    Returns the output file path.
    """
    source_concepts = source_concepts or []

    # Build index
    window.build_index(session_name, source_concepts)

    # Serialize all data
    index_bytes = window.index.to_bytes()
    page_bytes_list = [page.to_bytes() for page in window.pages]

    # Combine all data: [index_data][page1_data][page2_data]...
    # With length prefixes so we can split on decode
    all_data = BytesIO()

    # Write header
    all_data.write(MAGIC_HEADER)
    all_data.write(struct.pack(">I", len(window.pages)))

    # Write index
    all_data.write(struct.pack(">I", len(index_bytes)))
    all_data.write(index_bytes)

    # Write each page
    for pb in page_bytes_list:
        all_data.write(struct.pack(">I", len(pb)))
        all_data.write(pb)

    raw_data = all_data.getvalue()
    total_size = len(raw_data)

    logger.info("Encoding Internet Window: %d pages, %d bytes total",
                len(window.pages), total_size)

    # Convert to frames
    frames = _bytes_to_frames(raw_data)
    logger.info("Generated %d frames (%dx%d)", len(frames), FRAME_WIDTH, FRAME_HEIGHT)

    # Write frames as PNGs and encode with ffmpeg (lossless)
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    with tempfile.TemporaryDirectory() as tmpdir:
        for i, frame in enumerate(frames):
            img = Image.fromarray(frame, mode="RGB")
            img.save(os.path.join(tmpdir, f"frame_{i:04d}.png"))

        # Encode with ffmpeg FFV1 (lossless)
        cmd = [
            "ffmpeg", "-y",
            "-framerate", "1",
            "-i", os.path.join(tmpdir, "frame_%04d.png"),
            "-c:v", "ffv1",
            "-level", "3",
            output_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logger.error("ffmpeg encode failed: %s", result.stderr)
            raise RuntimeError(f"ffmpeg encode failed: {result.stderr}")

    file_size = os.path.getsize(output_path)
    logger.info("Internet Window encoded: %s (%d bytes, %d frames)",
                output_path, file_size, len(frames))

    # Save index as sidecar JSON
    index_path = output_path.rsplit(".", 1)[0] + "_index.json"
    with open(index_path, "w") as f:
        json.dump(window.index.to_dict(), f, indent=2)

    return output_path


# --- Decoder ---

def _frames_to_bytes(frames: List[np.ndarray]) -> bytes:
    """Convert video frames back to raw bytes."""
    chunks = []
    for frame in frames:
        chunks.append(frame.tobytes())
    return b"".join(chunks)


def decode_window(video_path: str) -> InternetWindow:
    """
    Decode an Internet Window video back into structured data.
    The agents use this to "browse" the captured internet.
    """
    # Extract frames with ffmpeg
    with tempfile.TemporaryDirectory() as tmpdir:
        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            os.path.join(tmpdir, "frame_%04d.png"),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg decode failed: {result.stderr}")

        # Load frames
        frames = []
        i = 1
        while True:
            frame_path = os.path.join(tmpdir, f"frame_{i:04d}.png")
            if not os.path.exists(frame_path):
                break
            img = Image.open(frame_path)
            frames.append(np.array(img))
            i += 1

    if not frames:
        raise RuntimeError("No frames found in video")

    # Convert frames back to bytes
    raw_data = _frames_to_bytes(frames)

    # Parse header
    offset = 0
    magic = raw_data[offset:offset + len(MAGIC_HEADER)]
    if magic != MAGIC_HEADER:
        raise RuntimeError(f"Invalid magic header: {magic}")
    offset += len(MAGIC_HEADER)

    num_pages = struct.unpack(">I", raw_data[offset:offset+4])[0]
    offset += 4

    # Parse index
    index_len = struct.unpack(">I", raw_data[offset:offset+4])[0]
    offset += 4
    index_data = raw_data[offset:offset+index_len]
    offset += index_len
    # index_data already contains its own length prefix from to_bytes()
    window_index = WindowIndex.from_bytes(index_data)

    # Parse pages
    pages = []
    for _ in range(num_pages):
        page_len = struct.unpack(">I", raw_data[offset:offset+4])[0]
        offset += 4
        page_data = raw_data[offset:offset+page_len]
        offset += page_len
        # page_data already contains its own length prefix from to_bytes()
        page = CapturedPage.from_bytes(page_data)
        pages.append(page)

    window = InternetWindow(index=window_index, pages=pages)
    logger.info("Decoded Internet Window: %s (%d pages)",
                window_index.window_id, len(pages))
    return window


# --- Agent Interface ---

class WindowBrowser:
    """
    The interface agents use to browse an Internet Window.
    Like a web browser, but for captured video-encoded knowledge.
    """

    def __init__(self, window: InternetWindow):
        self.window = window
        self.current_page_idx = 0

    @classmethod
    def from_video(cls, video_path: str) -> "WindowBrowser":
        """Open a window from a video file."""
        window = decode_window(video_path)
        return cls(window)

    @classmethod
    def from_index(cls, index_path: str) -> Optional["WindowBrowser"]:
        """Open a window from a sidecar index (without decoding video)."""
        # This allows quick browsing of metadata without full decode
        if not os.path.exists(index_path):
            return None
        with open(index_path) as f:
            data = json.load(f)
        # Can only browse index, not full content
        return None  # Full decode needed for content

    def list_pages(self) -> List[Dict]:
        """List all pages in the window (like a table of contents)."""
        return [
            {
                "index": i,
                "title": p.title,
                "url": p.url,
                "field": p.field,
                "source_type": p.source_type,
                "content_length": len(p.content),
                "sha256": p.sha256[:16],
            }
            for i, p in enumerate(self.window.pages)
        ]

    def read_page(self, index: int) -> Optional[CapturedPage]:
        """Read a specific page by index."""
        if 0 <= index < len(self.window.pages):
            self.current_page_idx = index
            return self.window.pages[index]
        return None

    def search(self, query: str) -> List[Tuple[int, float, str]]:
        """
        Search within the window for content matching a query.
        Returns list of (page_index, relevance_score, snippet).
        """
        query_words = set(query.lower().split())
        results = []

        for i, page in enumerate(self.window.pages):
            text = (page.title + " " + page.content).lower()
            text_words = set(text.split())

            # Simple relevance: word overlap ratio
            overlap = query_words & text_words
            if overlap:
                score = len(overlap) / len(query_words)
                # Find snippet around first match
                first_word = list(overlap)[0]
                pos = text.find(first_word)
                snippet = text[max(0, pos-50):pos+150]
                results.append((i, score, snippet.strip()))

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:10]

    def get_fields(self) -> Dict[str, int]:
        """Get field distribution in this window."""
        fields = {}
        for p in self.window.pages:
            fields[p.field] = fields.get(p.field, 0) + 1
        return fields

    def get_stats(self) -> Dict:
        """Get window statistics."""
        return {
            "window_id": self.window.index.window_id if self.window.index else "unknown",
            "total_pages": len(self.window.pages),
            "total_content_bytes": sum(len(p.content) for p in self.window.pages),
            "fields": self.get_fields(),
            "source_types": list(set(p.source_type for p in self.window.pages)),
            "concepts": self.window.index.source_concepts if self.window.index else [],
        }


# --- Capture Helpers ---

def capture_from_search_results(
    results: List[Dict[str, str]],
    source_type: str = "search",
    field: str = "general",
) -> List[CapturedPage]:
    """
    Convert raw search results into CapturedPage objects.
    Used when ingesting Manus search tool output.
    """
    pages = []
    now = datetime.now(timezone.utc).isoformat()

    for r in results:
        title = r.get("title", "")
        url = r.get("url", "")
        snippet = r.get("snippet", "")
        content = r.get("content", snippet)  # Use full content if available, else snippet

        if not title or not url:
            continue

        page = CapturedPage(
            url=url,
            title=title,
            content=content,
            snippet=snippet[:200],
            source_type=source_type,
            field=field,
            captured_at=now,
        )
        pages.append(page)

    return pages


def create_window_from_session(
    session_results: Dict[str, List[Dict]],
    session_name: str,
    source_concepts: List[str],
    output_path: Optional[str] = None,
) -> str:
    """
    High-level function: take a session's worth of search results,
    create an Internet Window video file.

    Args:
        session_results: Dict mapping field/topic to list of search results
        session_name: Name for this capture session
        source_concepts: Void concepts that triggered the search
        output_path: Where to save the video (default: data/internet_windows/)

    Returns:
        Path to the encoded video file
    """
    window = InternetWindow()

    for field_name, results in session_results.items():
        pages = capture_from_search_results(results, field=field_name)
        for page in pages:
            window.add_page(page)

    if not window.pages:
        raise ValueError("No pages captured — nothing to encode")

    if output_path is None:
        os.makedirs(WINDOW_STORAGE_PATH, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(
            WINDOW_STORAGE_PATH,
            f"window_{timestamp}.mkv"
        )

    encode_window(window, output_path, session_name, source_concepts)
    return output_path


# --- Bridge Functions (286 ↔ 256 hash spaces) ---

def compute_bridge_hash(
    internal_hash: str,  # 286 / Al-Jabr hash from repo
    external_hash: str,  # 256 / SHA-256 from internet content
) -> str:
    """
    Compute the Adriana bridge hash — the connection point between
    the internal void (286) and the external world (256).

    The bridge hash is what allows agents to verify that a particular
    piece of external knowledge has been properly captured and connected
    to the internal architecture.
    """
    # Combine both hash spaces
    combined = f"{internal_hash}::{external_hash}"
    # The bridge uses a different algorithm (SHA-384) to exist in neither space
    bridge = hashlib.sha384(combined.encode()).hexdigest()
    # Truncate to a middle ground between 256 and 286 bits
    # 271 bits ≈ 68 hex chars (between 64 for SHA-256 and 72 for ~286 bits)
    return bridge[:68]


def verify_window_integrity(
    video_path: str,
    expected_composite_hash: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Verify that an Internet Window video is intact and unmodified.
    """
    window = decode_window(video_path)

    # Recompute composite hash
    combined = "".join(p.sha256 for p in window.pages)
    actual_hash = hashlib.sha256(combined.encode()).hexdigest()

    integrity = {
        "window_id": window.index.window_id if window.index else "unknown",
        "pages_decoded": len(window.pages),
        "composite_hash": actual_hash,
        "hash_match": True,
    }

    if expected_composite_hash:
        integrity["hash_match"] = actual_hash == expected_composite_hash
        integrity["expected_hash"] = expected_composite_hash

    if window.index:
        integrity["hash_match"] = actual_hash == window.index.sha256_composite

    # Verify individual page hashes
    page_integrity = []
    for i, page in enumerate(window.pages):
        expected = page.sha256
        actual = hashlib.sha256(page.content.encode("utf-8")).hexdigest()
        page_integrity.append({
            "page": i,
            "title": page.title[:50],
            "intact": expected == actual,
        })

    integrity["pages"] = page_integrity
    integrity["all_pages_intact"] = all(p["intact"] for p in page_integrity)

    return integrity


# --- CLI ---

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    if len(sys.argv) < 2:
        print("VOID ENGINE — Internet Window System")
        print("=" * 50)
        print()
        print("The video IS the internet. The agents browse the video.")
        print()
        print("Usage:")
        print("  python internet_window.py encode <results.json> <output.mkv>")
        print("    Encode search results into an Internet Window video")
        print()
        print("  python internet_window.py decode <video.mkv>")
        print("    Decode a window and show its contents")
        print()
        print("  python internet_window.py browse <video.mkv> [search_query]")
        print("    Browse/search within a decoded window")
        print()
        print("  python internet_window.py verify <video.mkv>")
        print("    Verify window integrity (all hashes match)")
        print()
        print("  python internet_window.py stats <video.mkv>")
        print("    Show window statistics")
        print()
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd == "encode":
        if len(sys.argv) < 4:
            print("Usage: encode <results.json> <output.mkv>")
            sys.exit(1)

        results_path = sys.argv[2]
        output_path = sys.argv[3]

        with open(results_path) as f:
            data = json.load(f)

        # Detect format: either {field: [results]} or {concept: [results]}
        session_results = {}
        for key, results in data.items():
            session_results[key] = results

        concepts = list(data.keys())
        path = create_window_from_session(
            session_results, "cli_session", concepts, output_path
        )
        print(f"\nInternet Window encoded: {path}")
        print(f"File size: {os.path.getsize(path):,} bytes")

    elif cmd == "decode":
        if len(sys.argv) < 3:
            print("Usage: decode <video.mkv>")
            sys.exit(1)

        video_path = sys.argv[2]
        window = decode_window(video_path)

        print(f"\nWindow ID: {window.index.window_id}")
        print(f"Created: {window.index.created_at}")
        print(f"Pages: {window.index.total_pages}")
        print(f"Total content: {window.index.total_bytes:,} bytes")
        print(f"Concepts: {', '.join(window.index.source_concepts)}")
        print(f"Fields: {', '.join(window.index.fields_covered)}")
        print(f"\nManifest:")
        for entry in window.index.page_manifest:
            print(f"  [{entry['frame']:3d}] {entry['field']:15s} | {entry['title'][:50]}")

    elif cmd == "browse":
        if len(sys.argv) < 3:
            print("Usage: browse <video.mkv> [search_query]")
            sys.exit(1)

        video_path = sys.argv[2]
        browser = WindowBrowser.from_video(video_path)

        if len(sys.argv) > 3:
            query = " ".join(sys.argv[3:])
            print(f"\nSearching window for: '{query}'")
            results = browser.search(query)
            if results:
                for idx, score, snippet in results:
                    page = browser.window.pages[idx]
                    print(f"\n  [{score:.2f}] {page.title}")
                    print(f"         {page.url}")
                    print(f"         ...{snippet}...")
            else:
                print("  No results found.")
        else:
            print("\nPages in window:")
            for entry in browser.list_pages():
                print(f"  [{entry['index']:3d}] {entry['field']:15s} | {entry['title'][:50]}")

    elif cmd == "verify":
        if len(sys.argv) < 3:
            print("Usage: verify <video.mkv>")
            sys.exit(1)

        video_path = sys.argv[2]
        result = verify_window_integrity(video_path)

        print(f"\nWindow: {result['window_id']}")
        print(f"Pages decoded: {result['pages_decoded']}")
        print(f"Composite hash: {result['composite_hash'][:32]}...")
        print(f"Hash match: {'✓' if result['hash_match'] else '✗'}")
        print(f"All pages intact: {'✓' if result['all_pages_intact'] else '✗'}")

        if not result["all_pages_intact"]:
            for p in result["pages"]:
                if not p["intact"]:
                    print(f"  CORRUPTED: page {p['page']} — {p['title']}")

    elif cmd == "stats":
        if len(sys.argv) < 3:
            print("Usage: stats <video.mkv>")
            sys.exit(1)

        video_path = sys.argv[2]
        browser = WindowBrowser.from_video(video_path)
        stats = browser.get_stats()

        print(f"\nWindow: {stats['window_id']}")
        print(f"Pages: {stats['total_pages']}")
        print(f"Content: {stats['total_content_bytes']:,} bytes")
        print(f"Source types: {', '.join(stats['source_types'])}")
        print(f"Concepts: {', '.join(stats['concepts'])}")
        print(f"\nField distribution:")
        for field, count in stats["fields"].items():
            print(f"  {field}: {count} pages")

    else:
        print(f"Unknown command: {cmd}")
        print("Run without arguments for help.")
        sys.exit(1)
