#!/usr/bin/env bash
set -euo pipefail

DUR=140
BASE="project_void_keep_intent_intact"

# Instrumental (simple synth + bass layer)
ffmpeg -y \
  -f lavfi -i "sine=frequency=440:duration=${DUR}" \
  -f lavfi -i "sine=frequency=110:duration=${DUR}" \
  -f lavfi -i "anullsrc=duration=${DUR}" \
  -filter_complex "[0:a]volume=0.30[sine];[1:a]volume=0.50[bass];[2:a]volume=0.10[silence];[sine][bass][silence]amix=inputs=3[out]" \
  -map "[out]" "${BASE}_instrumental.wav"

ffmpeg -y -i "${BASE}_instrumental.wav" -codec:a libmp3lame -qscale:a 2 "${BASE}_instrumental.mp3"

# Vocal demo via espeak-ng
espeak-ng "Keep intent intact. In the noise and in the lapse, we still find the path back. The bottleneck is coherence." \
  -w "${BASE}_vocals.wav"

# Mixed demo
ffmpeg -y \
  -i "${BASE}_instrumental.wav" \
  -i "${BASE}_vocals.wav" \
  -filter_complex "[0:a]volume=0.30[a1];[1:a]volume=1.50[a2];[a1][a2]amix=inputs=2:duration=longest" \
  -b:a 192k "${BASE}_demo_song.mp3"

echo "Built:"
ls -lh "${BASE}_instrumental.wav" "${BASE}_instrumental.mp3" "${BASE}_vocals.wav" "${BASE}_demo_song.mp3"
