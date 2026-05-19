#!/bin/bash
set -e

# --- Part 1: Keep Intent Intact v2 (92 BPM, 140s) ---
ffmpeg -y -f lavfi -i "sine=f=40:d=140,lowpass=f=80,volume=1.5" \
-f lavfi -i "sine=f=46:d=140" \
-f lavfi -i "anoisesrc=d=140" \
-f lavfi -i "sine=f=220:d=140,tremolo=f=0.2,volume=0.3" \
-filter_complex \
"[1]volume='if(lt(mod(t,1.304),0.1),1,0)':eval=frame[kick];
 [2]bandpass=f=200:width_type=h:width=100,volume='if(lt(mod(t-0.652,1.304),0.1),0.8,0)':eval=frame[snare];
 [0][kick]amix=inputs=2:weights='1 1.2'[a1];
 [a1][snare]amix=inputs=2:weights='1 0.8'[a2];
 [a2][3]amix=inputs=2:weights='1 0.5',aecho=0.8:0.88:60:0.4" \
project_void_keep_intent_intact_v2_instrumental.wav

ffmpeg -y -i project_void_keep_intent_intact_v2_instrumental.wav -ab 192k project_void_keep_intent_intact_v2_instrumental.mp3

espeak-ng "Keep the intent intact" -w project_void_short_vocal_v2.wav
ffmpeg -y -i project_void_keep_intent_intact_v2_instrumental.wav -i project_void_short_vocal_v2.wav \
-filter_complex "[1]adelay=2000|2000,volume=1.5[v];[0][v]amix=inputs=2:duration=first" \
project_void_keep_intent_intact_v2_demo_song.mp3

# --- Part 2: Clean Arrangement Assets (v2) ---
ffmpeg -y -f lavfi -i "sine=f=46:d=140" -f lavfi -i "anoisesrc=d=140" \
-filter_complex "[0]volume='if(lt(mod(t,1.304),0.1),1,0)':eval=frame[k];[1]bandpass=f=200:width_type=h:width=100,volume='if(lt(mod(t-0.652,1.304),0.1),0.8,0)':eval=frame[s];[k][s]amix=inputs=2" \
project_void_keep_intent_intact_v2_stem_drums.wav

ffmpeg -y -f lavfi -i "sine=f=40:d=140,lowpass=f=80,volume=1.5" project_void_keep_intent_intact_v2_stem_bass.wav
ffmpeg -y -f lavfi -i "sine=f=220:d=140,tremolo=f=0.2,volume=0.3" project_void_keep_intent_intact_v2_stem_pad.wav
ffmpeg -y -f lavfi -i "sine=f=1000:d=140,volume='if(lt(mod(t,0.652),0.05),1,0)':eval=frame" project_void_keep_intent_intact_v2_click.wav

# --- Part 3: Thread Under Pressure (138 BPM, 140s) ---
ffmpeg -y -f lavfi -i "sine=f=35:d=140,volume=1.8" \
-f lavfi -i "sine=f=50:d=140" \
-f lavfi -i "anoisesrc=d=140" \
-f lavfi -i "sine=f=110:d=140,tremolo=f=0.1,volume=0.4" \
-filter_complex \
"[1]volume='if(lt(mod(t,0.869),0.1),1,0)':eval=frame[k];
 [2]bandpass=f=5000:width_type=h:width=2000,volume='if(lt(mod(t,0.217),0.05),0.3,0)':eval=frame[hh];
 [0][k]amix=inputs=2[a1];[a1][hh]amix=inputs=2[a2];[a2][3]amix=inputs=2:weights='1 0.6',aecho=0.8:0.88:40:0.5" \
project_void_thread_under_pressure_instrumental.wav

ffmpeg -y -i project_void_thread_under_pressure_instrumental.wav -ab 192k project_void_thread_under_pressure_instrumental.mp3

espeak-ng "Thread under pressure" -w project_void_thread_under_pressure_vocals.wav

ffmpeg -y -i project_void_thread_under_pressure_instrumental.wav -i project_void_thread_under_pressure_vocals.wav \
-filter_complex "[1]adelay=1000|1000,volume=2[v];[0][v]amix=inputs=2:duration=first" \
project_void_thread_under_pressure_demo_song.mp3

echo "Song pack generation complete."
