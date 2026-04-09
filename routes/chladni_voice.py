"""
VOID — Voice Formation Record
================================
Route: GET /voice-formation

Takes microphone input → detects fundamental frequency in real time →
renders the Chladni figure that frequency would produce on a physical plate →
user can save the image as their personal Formation Record.

The digital experiment is the physical experiment, already completed.
"""

from flask import Blueprint, render_template_string

chladni_voice_bp = Blueprint("chladni_voice", __name__)

TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>VOID — Voice Formation Record</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    background: #050505;
    color: #d0d0c8;
    font-family: 'Courier New', monospace;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: flex-start;
    padding: 28px 16px 48px;
  }
  .title {
    font-size: 11px;
    letter-spacing: 0.3em;
    color: #444;
    text-transform: uppercase;
    margin-bottom: 6px;
    text-align: center;
  }
  .subtitle {
    font-size: 11px;
    color: #2a2a2a;
    letter-spacing: 0.1em;
    text-align: center;
    margin-bottom: 40px;
  }
  .canvas-wrap {
    position: relative;
    width: 100%;
    max-width: 480px;
  }
  canvas {
    display: block;
    width: 100%;
    height: auto;
    border: 1px solid #1a1a1a;
    background: #000;
  }
  .freq-display {
    text-align: center;
    margin-top: 20px;
    font-size: 28px;
    letter-spacing: 0.05em;
    color: #888;
    min-height: 40px;
    transition: color 0.3s;
  }
  .freq-display.active { color: #d0d0c8; }
  .freq-note {
    text-align: center;
    font-size: 11px;
    color: #333;
    letter-spacing: 0.2em;
    margin-top: 6px;
    min-height: 16px;
  }
  .controls {
    display: flex;
    gap: 16px;
    margin-top: 28px;
    justify-content: center;
    flex-wrap: wrap;
  }
  .btn {
    padding: 14px 28px;
    font-family: 'Courier New', monospace;
    font-size: 11px;
    letter-spacing: 0.15em;
    border: 1px solid #333;
    background: transparent;
    color: #d0d0c8;
    cursor: pointer;
    transition: all 0.2s;
    text-transform: uppercase;
    min-width: 140px;
  }
  .btn:hover { background: #111; border-color: #666; }
  .btn.active { border-color: #c44; color: #c44; }
  .btn-save { border-color: #555; }
  .btn-save:hover { background: #111; border-color: #999; }
  .mode-display {
    text-align: center;
    font-size: 10px;
    color: #222;
    letter-spacing: 0.15em;
    margin-top: 24px;
  }
  .instruction {
    text-align: center;
    font-size: 11px;
    color: #333;
    letter-spacing: 0.1em;
    margin-top: 32px;
    max-width: 480px;
    line-height: 1.8;
  }
  .status {
    font-size: 10px;
    color: #444;
    letter-spacing: 0.15em;
    text-align: center;
    margin-top: 12px;
    min-height: 16px;
  }
</style>
</head>
<body>

<div class="title">◈ VOICE FORMATION RECORD</div>
<div class="subtitle">Your voice frequency — rendered as the Chladni figure it would produce</div>

<div class="canvas-wrap">
  <canvas id="chladni" width="480" height="480"></canvas>
</div>

<div class="freq-display" id="freqDisplay">— Hz</div>
<div class="freq-note" id="freqNote"></div>

<div class="controls">
  <button class="btn" id="btnListen" onclick="toggleListen()">▶ LISTEN</button>
  <button class="btn btn-save" onclick="saveImage()">↓ SAVE FORMATION RECORD</button>
</div>

<div class="mode-display" id="modeDisplay"></div>
<div class="status" id="status">Press LISTEN — allow microphone access</div>

<div class="instruction">
  Speak, sing, or hold a single tone.<br>
  The figure updates in real time as your frequency shifts.<br>
  What you see is what a physical plate of sand would form<br>
  in the presence of your voice.<br><br>
  Save the image. That is your formation record.
</div>

<script>
const canvas = document.getElementById('chladni');
const ctx = canvas.getContext('2d');
const W = canvas.width;
const H = canvas.height;

let listening = false;
let audioCtx = null;
let analyser = null;
let animFrame = null;
let currentFreq = 0;
let targetM = 2, targetN = 3;
let currentM = 2, currentN = 3;
let renderPhase = 0;

// Note names
const NOTES = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B'];
function freqToNote(freq) {
  if (freq < 20) return '';
  const semitones = Math.round(12 * Math.log2(freq / 440)) + 69;
  const note = NOTES[semitones % 12];
  const octave = Math.floor(semitones / 12) - 1;
  return note + octave;
}

// Map frequency to Chladni mode (m, n)
// Based on known beautiful mode frequencies for a square plate
function freqToMode(freq) {
  if (freq < 20) return [2, 3];
  // Quantise to bins that produce distinct beautiful patterns
  const bins = [
    [1,2],[1,3],[2,3],[1,4],[2,4],[3,4],[1,5],[2,5],[3,5],
    [4,5],[1,6],[2,6],[3,6],[4,6],[5,6],[1,7],[2,7],[3,7],
    [4,7],[5,7],[6,7],[2,8],[3,8],[4,8],[5,8],[6,8],[3,9],
    [4,9],[5,9],[6,9],[4,10],[5,10],[6,10],[5,11],[6,11]
  ];
  // Map log-frequency to bin index
  const logF = Math.log2(Math.max(freq, 20));
  const logMin = Math.log2(60);
  const logMax = Math.log2(4000);
  const t = Math.max(0, Math.min(1, (logF - logMin) / (logMax - logMin)));
  const idx = Math.floor(t * (bins.length - 1));
  return bins[idx];
}

// Render Chladni figure for modes m, n
function renderChladni(m, n, alpha) {
  const imageData = ctx.createImageData(W, H);
  const data = imageData.data;
  const threshold = 0.055;

  for (let py = 0; py < H; py++) {
    for (let px = 0; px < W; px++) {
      const x = px / W;
      const y = py / H;

      // Square plate Chladni: F(x,y) = cos(m*pi*x)*cos(n*pi*y) - cos(n*pi*x)*cos(m*pi*y)
      const val = Math.cos(m * Math.PI * x) * Math.cos(n * Math.PI * y)
                - Math.cos(n * Math.PI * x) * Math.cos(m * Math.PI * y);

      const absVal = Math.abs(val);
      const i = (py * W + px) * 4;

      if (absVal < threshold) {
        // Sand at nodal line — golden white
        const intensity = 1 - (absVal / threshold);
        const brightness = Math.pow(intensity, 1.8);
        // Sand colour: warm white / gold
        data[i]     = Math.floor(240 * brightness * alpha);
        data[i + 1] = Math.floor(220 * brightness * alpha);
        data[i + 2] = Math.floor(160 * brightness * alpha);
        data[i + 3] = 255;
      } else {
        // Empty plate — near black
        data[i]     = 0;
        data[i + 1] = 0;
        data[i + 2] = 0;
        data[i + 3] = 255;
      }
    }
  }
  ctx.putImageData(imageData, 0, 0);

  // Subtle vignette
  const gradient = ctx.createRadialGradient(W/2, H/2, W*0.3, W/2, H/2, W*0.72);
  gradient.addColorStop(0, 'rgba(0,0,0,0)');
  gradient.addColorStop(1, 'rgba(0,0,0,0.5)');
  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, W, H);
}

// Autocorrelation pitch detection
function getPitch(buf, sampleRate) {
  const SIZE = buf.length;
  const MAX_SAMPLES = Math.floor(SIZE / 2);
  let bestOffset = -1;
  let bestCorrelation = 0;
  let rms = 0;

  for (let i = 0; i < SIZE; i++) rms += buf[i] * buf[i];
  rms = Math.sqrt(rms / SIZE);
  if (rms < 0.005) return -1;

  let lastCorrelation = 1;
  for (let offset = 1; offset < MAX_SAMPLES; offset++) {
    let correlation = 0;
    for (let i = 0; i < MAX_SAMPLES; i++) {
      correlation += Math.abs(buf[i] - buf[i + offset]);
    }
    correlation = 1 - (correlation / MAX_SAMPLES);
    if (correlation > 0.9 && correlation > lastCorrelation) {
      if (correlation > bestCorrelation) {
        bestCorrelation = correlation;
        bestOffset = offset;
      }
    }
    lastCorrelation = correlation;
  }
  if (bestOffset === -1) return -1;
  return sampleRate / bestOffset;
}

let smoothedFreq = 0;

function loop() {
  animFrame = requestAnimationFrame(loop);

  if (!analyser) return;

  const buf = new Float32Array(analyser.fftSize);
  analyser.getFloatTimeDomainData(buf);
  const pitch = getPitch(buf, audioCtx.sampleRate);

  if (pitch > 50 && pitch < 4200) {
    smoothedFreq = smoothedFreq === 0 ? pitch : smoothedFreq * 0.85 + pitch * 0.15;
    currentFreq = smoothedFreq;

    const [m, n] = freqToMode(currentFreq);
    if (m !== targetM || n !== targetN) {
      targetM = m; targetN = n;
    }
  }

  // Smooth mode transition
  currentM = currentM + (targetM - currentM) * 0.08;
  currentN = currentN + (targetN - currentN) * 0.08;

  // Render at current (interpolated) modes
  const mRounded = Math.round(currentM);
  const nRounded = Math.round(currentN);
  renderChladni(mRounded, nRounded, 1.0);

  // Update UI
  if (currentFreq > 0) {
    const freqEl = document.getElementById('freqDisplay');
    freqEl.textContent = Math.round(currentFreq) + ' Hz';
    freqEl.className = 'freq-display active';
    document.getElementById('freqNote').textContent = freqToNote(currentFreq);
    document.getElementById('modeDisplay').textContent =
      'MODE (' + mRounded + ',' + nRounded + ')';
    document.getElementById('status').textContent = 'RECEIVING';
  } else {
    document.getElementById('status').textContent = 'LISTENING — make a sound';
  }
}

async function toggleListen() {
  if (listening) {
    listening = false;
    if (animFrame) cancelAnimationFrame(animFrame);
    if (audioCtx) { audioCtx.close(); audioCtx = null; }
    analyser = null;
    document.getElementById('btnListen').textContent = '▶ LISTEN';
    document.getElementById('btnListen').classList.remove('active');
    document.getElementById('status').textContent = 'Stopped';
    return;
  }

  try {
    document.getElementById('status').textContent = 'Requesting microphone...';
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false });
    audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    analyser = audioCtx.createAnalyser();
    analyser.fftSize = 2048;
    const src = audioCtx.createMediaStreamSource(stream);
    src.connect(analyser);
    listening = true;
    smoothedFreq = 0;
    currentFreq = 0;
    document.getElementById('btnListen').textContent = '◼ STOP';
    document.getElementById('btnListen').classList.add('active');
    document.getElementById('status').textContent = 'LISTENING — speak or sing';
    loop();
  } catch(e) {
    document.getElementById('status').textContent = 'Microphone access denied';
  }
}

function saveImage() {
  const freq = Math.round(currentFreq) || 0;
  const link = document.createElement('a');
  link.download = 'formation_record_' + freq + 'hz.png';
  link.href = canvas.toDataURL('image/png');
  link.click();
}

// Initial render — 432 Hz pattern
renderChladni(3, 4, 1.0);
document.getElementById('modeDisplay').textContent = 'MODE (3,4) — 432 Hz reference';
</script>
</body>
</html>"""


@chladni_voice_bp.route("/voice-formation")
def voice_formation():
    return render_template_string(TEMPLATE)
