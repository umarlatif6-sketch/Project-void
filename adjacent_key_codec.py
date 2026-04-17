# Adjacent-Key Encoder/Decoder for Fast-Typing Misspellings
# Supports QWERTY layout, left/right neighbor mapping

QWERTY_ROWS = [
    "qwertyuiop",
    "asdfghjkl",
    "zxcvbnm"
]

# Build neighbor maps
LEFT_NEIGHBOR = {}
RIGHT_NEIGHBOR = {}
for row in QWERTY_ROWS:
    for i, c in enumerate(row):
        if i > 0:
            LEFT_NEIGHBOR[c] = row[i-1]
        if i < len(row)-1:
            RIGHT_NEIGHBOR[c] = row[i+1]

# Add space and common punctuation (no neighbors)
for c in " 1234567890-=[]\\;',./":
    LEFT_NEIGHBOR[c] = c
    RIGHT_NEIGHBOR[c] = c


def encode_adjacent(text, direction="right"):
    """Encode text by replacing each letter with its left or right QWERTY neighbor."""
    result = []
    for ch in text:
        lower = ch.lower()
        if direction == "right" and lower in RIGHT_NEIGHBOR:
            new = RIGHT_NEIGHBOR[lower]
        elif direction == "left" and lower in LEFT_NEIGHBOR:
            new = LEFT_NEIGHBOR[lower]
        else:
            new = ch
        # Preserve case
        if ch.isupper():
            new = new.upper()
        result.append(new)
    return ''.join(result)


def decode_adjacent(text, direction="right"):
    """Attempt to decode by mapping each letter to its left/right neighbor (reverse)."""
    # This is not always invertible, but we can try
    # Build reverse maps
    if direction == "right":
        reverse_map = {v: k for k, v in RIGHT_NEIGHBOR.items()}
    else:
        reverse_map = {v: k for k, v in LEFT_NEIGHBOR.items()}
    result = []
    for ch in text:
        lower = ch.lower()
        if lower in reverse_map:
            new = reverse_map[lower]
        else:
            new = ch
        if ch.isupper():
            new = new.upper()
        result.append(new)
    return ''.join(result)


if __name__ == "__main__":
    sample = "what am i saying how are you nice"
    print("Original:", sample)
    print("Right-adjacent:", encode_adjacent(sample, "right"))
    print("Left-adjacent:", encode_adjacent(sample, "left"))
    # Try decoding
    encoded = encode_adjacent(sample, "right")
    print("Decoded (right):", decode_adjacent(encoded, "right"))
