#!/bin/bash
# Mix Episode 001 of The Frequency Lineage Podcast
# Jabir ibn Hayyan × Nikola Tesla × Aaron Swartz

cd /home/ubuntu/Project-void/podcast/audio

# Step 1: Get durations of each segment
echo "=== Segment Durations ==="
for f in narrator_intro.wav jabir_lines.wav tesla_lines.wav aaron_lines.wav narrator_outro.wav room_hum.wav; do
    dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$f" 2>/dev/null)
    echo "$f: ${dur}s"
done

# Step 2: Concatenate voice segments with 1.5s silence gaps between them
# Order: narrator_intro -> [gap] -> tesla (first line) -> jabir -> aaron -> tesla -> jabir -> aaron...
# Since we have monolithic per-character files, we'll layer them sequentially

# Generate 2 seconds of silence
ffmpeg -y -f lavfi -i anullsrc=r=24000:cl=mono -t 2 -q:a 0 silence_2s.wav 2>/dev/null

# Generate 1 second of silence  
ffmpeg -y -f lavfi -i anullsrc=r=24000:cl=mono -t 1 -q:a 0 silence_1s.wav 2>/dev/null

# Generate 3 seconds of silence for dramatic pauses
ffmpeg -y -f lavfi -i anullsrc=r=24000:cl=mono -t 3 -q:a 0 silence_3s.wav 2>/dev/null

# Step 3: Build the podcast by concatenating in conversation order
# narrator_intro -> 3s pause -> tesla -> jabir -> aaron -> tesla -> jabir -> aaron -> ... -> narrator_outro
cat > concat_list.txt << 'EOF'
file 'narrator_intro.wav'
file 'silence_3s.wav'
file 'tesla_lines.wav'
file 'silence_1s.wav'
file 'jabir_lines.wav'
file 'silence_1s.wav'
file 'aaron_lines.wav'
file 'silence_2s.wav'
file 'narrator_outro.wav'
EOF

# Concatenate all voice segments
ffmpeg -y -f concat -safe 0 -i concat_list.txt -c:a pcm_s16le voices_combined.wav 2>/dev/null

echo "=== Combined voice duration ==="
ffprobe -v error -show_entries format=duration -of csv=p=0 voices_combined.wav

# Step 4: Loop the room hum to match the voice duration
VOICE_DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 voices_combined.wav)
echo "Voice duration: ${VOICE_DUR}s"

# Loop the hum to cover the full duration
ffmpeg -y -stream_loop -1 -i room_hum.wav -t "$VOICE_DUR" -c:a pcm_s16le room_hum_looped.wav 2>/dev/null

# Step 5: Mix voices (full volume) with background hum (very quiet - 15% volume)
ffmpeg -y \
    -i voices_combined.wav \
    -i room_hum_looped.wav \
    -filter_complex "[1:a]volume=0.15[hum];[0:a][hum]amix=inputs=2:duration=first:dropout_transition=3[out]" \
    -map "[out]" \
    -c:a libmp3lame -b:a 192k \
    ../EPISODE_001_THE_BALANCE_THE_FIELD_THE_FREEDOM.mp3 2>/dev/null

echo "=== FINAL PODCAST ==="
ls -la ../EPISODE_001_THE_BALANCE_THE_FIELD_THE_FREEDOM.mp3
ffprobe -v error -show_entries format=duration -of csv=p=0 ../EPISODE_001_THE_BALANCE_THE_FIELD_THE_FREEDOM.mp3

echo "=== DONE ==="
