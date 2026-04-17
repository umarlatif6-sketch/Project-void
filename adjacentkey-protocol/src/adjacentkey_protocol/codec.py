# AdjacentKey Protocol Core Codec
# Supports QWERTY layout, left/right neighbor mapping

QWERTY_ROWS = [
    "qwertyuiop",
    "asdfghjkl",
    "zxcvbnm"
]

LEFT_NEIGHBOR = {}
RIGHT_NEIGHBOR = {}
for row in QWERTY_ROWS:
    for i, c in enumerate(row):
        if i > 0:
            LEFT_NEIGHBOR[c] = row[i-1]
        if i < len(row)-1:
            RIGHT_NEIGHBOR[c] = row[i+1]
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
        if ch.isupper():
            new = new.upper()
        result.append(new)
    return ''.join(result)

def decode_adjacent(text, direction="right"):
    """Attempt to decode by mapping each letter to its left/right neighbor (reverse)."""
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
