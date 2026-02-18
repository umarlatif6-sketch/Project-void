document.addEventListener("DOMContentLoaded", () => {
    const tabs = document.querySelectorAll(".tab");
    const panels = document.querySelectorAll(".panel");

    tabs.forEach(tab => {
        tab.addEventListener("click", () => {
            tabs.forEach(t => t.classList.remove("active"));
            panels.forEach(p => p.classList.remove("active"));
            tab.classList.add("active");
            document.getElementById(tab.dataset.tab).classList.add("active");
            if (tab.dataset.tab !== "visualizer") { stopViz(); stopMic(); }
            if (tab.dataset.tab !== "silk") { stopListener(); }
            if (tab.dataset.tab === "files") refreshFiles();
            if (tab.dataset.tab === "capacity") loadSelects();
            if (tab.dataset.tab === "visualizer") loadSelects();
            if (tab.dataset.tab === "silk") loadSilkFeed();
        });
    });

    function formatSize(bytes) {
        if (bytes >= 1073741824) return (bytes / 1073741824).toFixed(2) + " GB";
        if (bytes >= 1048576) return (bytes / 1048576).toFixed(1) + " MB";
        if (bytes >= 1024) return (bytes / 1024).toFixed(1) + " KB";
        return bytes.toLocaleString() + " B";
    }

    function showToast(msg, type) {
        const toast = document.getElementById("toast");
        toast.textContent = msg;
        toast.className = "toast show " + (type || "");
        clearTimeout(toast._timeout);
        toast._timeout = setTimeout(() => toast.className = "toast", 4000);
    }

    async function fetchFiles() {
        const res = await fetch("/api/files");
        return res.json();
    }

    async function loadSelects() {
        const data = await fetchFiles();
        const carrier = document.getElementById("carrier-select");
        const payload = document.getElementById("payload-select");
        const stego = document.getElementById("stego-select");

        const wavFiles = data.input.filter(f => f.name.toLowerCase().endsWith(".wav"));
        carrier.innerHTML = wavFiles.length
            ? wavFiles.map(f => `<option value="${f.name}">${f.name} (${formatSize(f.size)})</option>`).join("")
            : '<option value="">No WAV files in input_files/</option>';

        payload.innerHTML = data.input.length
            ? data.input.map(f => `<option value="${f.name}">${f.name} (${formatSize(f.size)})</option>`).join("")
            : '<option value="">No files in input_files/</option>';

        updateStegoSelect(data);
        updateCapSelect(data);
        updateVizSelect(data);
    }

    function updateStegoSelect(data) {
        const stego = document.getElementById("stego-select");
        const source = document.querySelector('input[name="decode-source"]:checked').value;
        const files = source === "output" ? data.output : data.input;
        const wavFiles = files.filter(f => f.name.toLowerCase().endsWith(".wav"));
        stego.innerHTML = wavFiles.length
            ? wavFiles.map(f => `<option value="${f.name}">${f.name} (${formatSize(f.size)})</option>`).join("")
            : '<option value="">No WAV files found</option>';
    }

    document.querySelectorAll('input[name="decode-source"]').forEach(r => {
        r.addEventListener("change", async () => {
            const data = await fetchFiles();
            updateStegoSelect(data);
        });
    });

    function updateCapSelect(data) {
        const sel = document.getElementById("cap-file-select");
        const source = document.querySelector('input[name="cap-source"]:checked').value;
        const files = source === "output" ? data.output : data.input;
        const wavFiles = files.filter(f => f.name.toLowerCase().endsWith(".wav"));
        sel.innerHTML = wavFiles.length
            ? wavFiles.map(f => `<option value="${f.name}">${f.name} (${formatSize(f.size)})</option>`).join("")
            : '<option value="">No WAV files found</option>';
    }

    document.querySelectorAll('input[name="cap-source"]').forEach(r => {
        r.addEventListener("change", async () => {
            const data = await fetchFiles();
            updateCapSelect(data);
        });
    });

    async function refreshFiles() {
        const data = await fetchFiles();
        renderFileList("input-file-list", data.input, "input_files");
        renderFileList("output-file-list", data.output, "output_audio");
    }

    function renderFileList(containerId, files, folder) {
        const el = document.getElementById(containerId);
        if (!files.length) {
            el.innerHTML = '<p class="empty-msg">No files</p>';
            return;
        }
        el.innerHTML = files.map(f => `
            <div class="file-row">
                <div class="file-info">
                    <span class="file-name">${f.name}</span>
                    <span class="file-size">${formatSize(f.size)}</span>
                </div>
                <div class="file-actions">
                    <button class="btn-sm" onclick="downloadFile('${folder}', '${f.name}')">Download</button>
                    <button class="btn-sm delete" onclick="deleteFile('${folder}', '${f.name}')">Delete</button>
                </div>
            </div>
        `).join("");
    }

    window.downloadFile = (folder, name) => {
        window.open(`/api/download/${folder}/${name}`, "_blank");
    };

    window.deleteFile = async (folder, name) => {
        if (!confirm(`Delete ${name}?`)) return;
        const res = await fetch(`/api/delete/${folder}/${name}`, { method: "DELETE" });
        if (res.ok) {
            showToast(`Deleted ${name}`, "success");
            refreshFiles();
            loadSelects();
        } else {
            showToast("Delete failed", "error");
        }
    };

    function setupUpload(zoneId, inputId, statusId, dest) {
        const zone = document.getElementById(zoneId);
        const input = document.getElementById(inputId);
        const status = document.getElementById(statusId);

        zone.addEventListener("click", () => input.click());

        zone.addEventListener("dragover", e => {
            e.preventDefault();
            zone.classList.add("dragover");
        });

        zone.addEventListener("dragleave", () => zone.classList.remove("dragover"));

        zone.addEventListener("drop", e => {
            e.preventDefault();
            zone.classList.remove("dragover");
            uploadFiles(e.dataTransfer.files, status, dest);
        });

        input.addEventListener("change", () => {
            uploadFiles(input.files, status, dest);
            input.value = "";
        });
    }

    async function uploadFiles(fileList, statusEl, dest) {
        statusEl.innerHTML = "";
        for (const file of fileList) {
            const item = document.createElement("div");
            item.className = "upload-item";
            item.innerHTML = `<span>${file.name}</span><span>Uploading...</span>`;
            statusEl.appendChild(item);

            const fd = new FormData();
            fd.append("file", file);
            fd.append("dest", dest);

            try {
                const res = await fetch("/api/upload", { method: "POST", body: fd });
                const data = await res.json();
                if (data.success) {
                    item.innerHTML = `<span>${data.filename}</span><span style="color:var(--success)">${formatSize(data.size)}</span>`;
                    showToast(`Uploaded ${data.filename}`, "success");
                } else {
                    item.innerHTML = `<span>${file.name}</span><span style="color:var(--error)">${data.error}</span>`;
                }
            } catch {
                item.innerHTML = `<span>${file.name}</span><span style="color:var(--error)">Upload failed</span>`;
            }
        }
        loadSelects();
    }

    setupUpload("upload-zone-encode", "file-upload-encode", "upload-status-encode", "input");
    setupUpload("upload-zone-decode", "file-upload-decode", "upload-status-decode", "output");

    let lastEncodedFile = null;
    let lastDecodedFile = null;

    document.getElementById("encode-btn").addEventListener("click", async () => {
        const carrier = document.getElementById("carrier-select").value;
        const payload = document.getElementById("payload-select").value;
        const lsb = document.querySelector('input[name="lsb-encode"]:checked').value;
        const jitter = document.getElementById("jitter-toggle").checked;
        const btn = document.getElementById("encode-btn");

        if (!carrier || !payload) {
            showToast("Select both a carrier WAV and a file to hide", "error");
            return;
        }

        btn.disabled = true;
        btn.innerHTML = '<span class="spinner"></span>Encoding...';
        document.getElementById("encode-result").style.display = "none";

        try {
            const res = await fetch("/api/encode", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ carrier, payload, lsb_depth: parseInt(lsb), jitter }),
            });
            const data = await res.json();

            if (data.success) {
                document.getElementById("res-output").textContent = data.output_file;
                document.getElementById("res-orig-size").textContent = formatSize(data.original_size);
                document.getElementById("res-comp-size").textContent = formatSize(data.compressed_size);
                document.getElementById("res-out-size").textContent = formatSize(data.output_size);
                document.getElementById("res-hash-key").textContent = data.hash_key;
                document.getElementById("encode-result").style.display = "block";
                lastEncodedFile = data.output_file;

                const bubbleEl = document.getElementById("bubble-status-msg");
                if (bubbleEl) {
                    if (data.bubble_warning) {
                        bubbleEl.textContent = data.bubble_warning;
                        bubbleEl.className = data.bubble_status === "burst" ? "bubble-burst-warning" : "bubble-stretch";
                        bubbleEl.style.display = "block";
                    } else {
                        bubbleEl.textContent = "Bubble intact — clean encode";
                        bubbleEl.className = "bubble-safe";
                        bubbleEl.style.display = "block";
                    }
                }

                const toastMsg = data.bubble_status === "burst" ? "BUBBLE BURST — encoded with distortion risk!" : "Sapphire Bubble sealed!";
                showToast(toastMsg, data.bubble_status === "burst" ? "error" : "success");
                loadSelects();
            } else {
                showToast(data.error, "error");
            }
        } catch (e) {
            showToast("Encoding failed: " + e.message, "error");
        }

        btn.disabled = false;
        btn.textContent = "Encode File";
    });

    document.getElementById("copy-hash-btn").addEventListener("click", () => {
        const key = document.getElementById("res-hash-key").textContent;
        navigator.clipboard.writeText(key).then(() => {
            showToast("Hash Key copied!", "success");
        }).catch(() => {
            const ta = document.createElement("textarea");
            ta.value = key;
            document.body.appendChild(ta);
            ta.select();
            document.execCommand("copy");
            document.body.removeChild(ta);
            showToast("Hash Key copied!", "success");
        });
    });

    document.getElementById("download-encoded-btn").addEventListener("click", () => {
        if (lastEncodedFile) window.open(`/api/download/output_audio/${lastEncodedFile}`, "_blank");
    });

    document.getElementById("decode-btn").addEventListener("click", async () => {
        const stego = document.getElementById("stego-select").value;
        const hashKey = document.getElementById("hash-key-input").value.trim();
        const lsb = document.querySelector('input[name="lsb-decode"]:checked').value;
        const source = document.querySelector('input[name="decode-source"]:checked').value;
        const btn = document.getElementById("decode-btn");

        if (!stego) {
            showToast("Select an encoded WAV file", "error");
            return;
        }
        if (!hashKey) {
            showToast("Enter the Hash Key", "error");
            return;
        }

        btn.disabled = true;
        btn.innerHTML = '<span class="spinner"></span>Decoding...';
        document.getElementById("decode-result").style.display = "none";

        try {
            const res = await fetch("/api/decode", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ stego_file: stego, hash_key: hashKey, lsb_depth: parseInt(lsb), source }),
            });
            const data = await res.json();

            if (data.success) {
                document.getElementById("dec-filename").textContent = data.filename;
                document.getElementById("dec-size").textContent = formatSize(data.size);
                document.getElementById("dec-checksum").textContent = data.checksum;
                document.getElementById("decode-result").style.display = "block";
                lastDecodedFile = data.filename;
                showToast("Decoding complete!", "success");
                loadSelects();
            } else {
                showToast(data.error, "error");
            }
        } catch (e) {
            showToast("Decoding failed: " + e.message, "error");
        }

        btn.disabled = false;
        btn.textContent = "Decode File";
    });

    document.getElementById("download-decoded-btn").addEventListener("click", () => {
        if (lastDecodedFile) window.open(`/api/download/output_audio/${lastDecodedFile}`, "_blank");
    });

    function updateVizSelect(data) {
        const sel = document.getElementById("viz-file-select");
        if (!sel) return;
        const source = document.querySelector('input[name="viz-source"]:checked').value;
        const files = source === "output" ? data.output : data.input;
        const wavFiles = files.filter(f => f.name.toLowerCase().endsWith(".wav"));
        sel.innerHTML = wavFiles.length
            ? wavFiles.map(f => `<option value="${f.name}">${f.name} (${formatSize(f.size)})</option>`).join("")
            : '<option value="">No WAV files found</option>';
    }

    document.querySelectorAll('input[name="viz-source"]').forEach(r => {
        r.addEventListener("change", async () => {
            const data = await fetchFiles();
            updateVizSelect(data);
        });
    });

    document.getElementById("burst-signal").addEventListener("input", (e) => {
        document.getElementById("burst-char-count").textContent = e.target.value.length;
    });

    document.getElementById("burst-btn").addEventListener("click", async () => {
        const signal = document.getElementById("burst-signal").value.trim();
        const btn = document.getElementById("burst-btn");

        if (!signal) {
            showToast("Enter a signal string", "error");
            return;
        }
        if (signal.length > 10) {
            showToast("Signal must be 10 characters or less", "error");
            return;
        }

        btn.disabled = true;
        btn.innerHTML = '<span class="spinner"></span>Encoding Burst...';
        document.getElementById("burst-result").style.display = "none";

        try {
            const res = await fetch("/api/burst", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ signal }),
            });
            const data = await res.json();

            if (data.success) {
                document.getElementById("burst-res-signal").textContent = signal;
                document.getElementById("burst-res-file").textContent = data.output_file;
                document.getElementById("burst-res-size").textContent = formatSize(data.output_size);
                document.getElementById("burst-res-hash").textContent = data.hash_key;
                document.getElementById("burst-result").style.display = "block";
                window._lastBurstFile = data.output_file;
                showToast("Burst signal encoded!", "success");
                loadSelects();
            } else {
                showToast(data.error, "error");
            }
        } catch (e) {
            showToast("Burst encoding failed: " + e.message, "error");
        }

        btn.disabled = false;
        btn.textContent = "Encode Burst Signal";
    });

    document.getElementById("copy-burst-hash-btn").addEventListener("click", () => {
        const key = document.getElementById("burst-res-hash").textContent;
        navigator.clipboard.writeText(key).then(() => {
            showToast("Hash Key copied!", "success");
        }).catch(() => {
            const ta = document.createElement("textarea");
            ta.value = key;
            document.body.appendChild(ta);
            ta.select();
            document.execCommand("copy");
            document.body.removeChild(ta);
            showToast("Hash Key copied!", "success");
        });
    });

    document.getElementById("download-burst-btn").addEventListener("click", () => {
        if (window._lastBurstFile) window.open(`/api/download/output_audio/${window._lastBurstFile}`, "_blank");
    });

    let vizSpectrogramMode = false;
    let vizPocketMode = false;
    let spectrogramImageData = null;
    let pocketPhase = 0;

    function updateVizLegends() {
        const legendNormal = document.getElementById("viz-legend");
        const legendSpec = document.getElementById("viz-legend-spectrogram");
        const legendPocket = document.getElementById("viz-legend-pocket");
        legendNormal.style.display = "none";
        legendSpec.style.display = "none";
        legendPocket.style.display = "none";
        if (vizPocketMode) {
            legendPocket.style.display = "flex";
        } else if (vizSpectrogramMode) {
            legendSpec.style.display = "flex";
        } else {
            legendNormal.style.display = "flex";
        }
    }

    document.getElementById("viz-spectrogram-toggle").addEventListener("change", (e) => {
        vizSpectrogramMode = e.target.checked;
        spectrogramImageData = null;
        if (vizSpectrogramMode) {
            vizPocketMode = false;
            document.getElementById("viz-pocket-toggle").checked = false;
        }
        updateVizLegends();
    });

    document.getElementById("viz-pocket-toggle").addEventListener("change", (e) => {
        vizPocketMode = e.target.checked;
        pocketPhase = 0;
        if (vizPocketMode) {
            vizSpectrogramMode = false;
            document.getElementById("viz-spectrogram-toggle").checked = false;
        }
        updateVizLegends();
    });

    let vizAudioCtx = null;
    let vizSource = null;
    let vizAnalyser = null;
    let vizAnimFrame = null;
    let vizAudio = null;

    document.getElementById("viz-play-btn").addEventListener("click", async () => {
        const filename = document.getElementById("viz-file-select").value;
        const source = document.querySelector('input[name="viz-source"]:checked').value;

        if (!filename) {
            showToast("Select a WAV file to visualize", "error");
            return;
        }

        if (vizAudio) {
            vizAudio.pause();
            vizAudio = null;
        }
        if (vizAnimFrame) cancelAnimationFrame(vizAnimFrame);

        const folder = source === "output" ? "output_audio" : "input_files";
        const url = `/api/download/${folder}/${filename}`;

        try {
            vizAudioCtx = new (window.AudioContext || window.webkitAudioContext)();
            vizAnalyser = vizAudioCtx.createAnalyser();
            vizAnalyser.fftSize = 4096;

            vizAudio = new Audio(url);
            vizAudio.crossOrigin = "anonymous";

            await new Promise((resolve, reject) => {
                vizAudio.addEventListener("canplay", resolve, { once: true });
                vizAudio.addEventListener("error", reject, { once: true });
                vizAudio.load();
            });

            vizSource = vizAudioCtx.createMediaElementSource(vizAudio);
            vizSource.connect(vizAnalyser);
            vizAnalyser.connect(vizAudioCtx.destination);

            vizAudio.play();

            document.getElementById("viz-container").style.display = "block";
            document.getElementById("viz-stop-btn").style.display = "inline-block";
            document.getElementById("viz-play-btn").textContent = "Playing...";
            document.getElementById("viz-play-btn").disabled = true;

            drawSpectrum();

            vizAudio.addEventListener("ended", () => stopViz());

        } catch (e) {
            showToast("Could not play audio: " + e.message, "error");
        }
    });

    document.getElementById("viz-stop-btn").addEventListener("click", stopViz);

    function stopViz() {
        if (vizAudio) { vizAudio.pause(); vizAudio = null; }
        if (vizAnimFrame) cancelAnimationFrame(vizAnimFrame);
        if (vizAudioCtx) { vizAudioCtx.close(); vizAudioCtx = null; }
        vizSource = null;
        vizAnalyser = null;
        document.getElementById("viz-stop-btn").style.display = "none";
        document.getElementById("viz-play-btn").textContent = "Play & Visualize";
        document.getElementById("viz-play-btn").disabled = false;
    }

    let micStream = null;
    let micAudioCtx = null;
    let micAnalyser = null;
    let micAnimFrame = null;
    const SIGNAL_THRESHOLD = 120;
    const PILOT_432_THRESHOLD = 100;
    const PILOT_864_THRESHOLD = 50;
    const PILOT_SUSTAIN_MS = 400;
    let pilotLockStart = 0;
    let sapphireBubbleActive = false;

    document.getElementById("viz-mic-btn").addEventListener("click", async () => {
        if (micStream) { stopMic(); return; }
        stopViz();

        try {
            micStream = await navigator.mediaDevices.getUserMedia({ audio: true });
            micAudioCtx = new (window.AudioContext || window.webkitAudioContext)();
            micAnalyser = micAudioCtx.createAnalyser();
            micAnalyser.fftSize = 4096;

            const source = micAudioCtx.createMediaStreamSource(micStream);
            source.connect(micAnalyser);

            document.getElementById("viz-container").style.display = "block";
            document.getElementById("viz-mic-btn").style.display = "none";
            document.getElementById("viz-mic-stop-btn").style.display = "inline-block";
            document.getElementById("viz-play-btn").disabled = true;

            drawMicSpectrum();
            showToast("Mic Listener active — scanning for 432 Hz", "success");
        } catch (e) {
            showToast("Microphone access denied or unavailable", "error");
        }
    });

    document.getElementById("viz-mic-stop-btn").addEventListener("click", stopMic);

    function stopMic() {
        if (micStream) {
            micStream.getTracks().forEach(t => t.stop());
            micStream = null;
        }
        if (micAnimFrame) cancelAnimationFrame(micAnimFrame);
        if (micAudioCtx) { micAudioCtx.close(); micAudioCtx = null; }
        micAnalyser = null;
        pilotLockStart = 0;
        sapphireBubbleActive = false;
        document.getElementById("viz-mic-stop-btn").style.display = "none";
        document.getElementById("viz-mic-btn").style.display = "inline-block";
        document.getElementById("viz-play-btn").disabled = false;

        const vizContainer = document.getElementById("viz-container");
        vizContainer.classList.remove("gold-glow-border");
        vizContainer.classList.remove("sapphire-bubble-border");
        document.body.classList.remove("sapphire-bubble-mode");
        vizContainer.style.border = "";
        document.getElementById("viz-signal-status").textContent = "Signal: Scanning...";
        document.getElementById("viz-signal-status").style.color = "";
    }

    function drawMicSpectrum() {
        if (!micAnalyser) return;

        const canvas = document.getElementById("viz-canvas");
        const ctx = canvas.getContext("2d");
        const bufLen = micAnalyser.frequencyBinCount;
        const dataArr = new Uint8Array(bufLen);

        const sampleRate = micAudioCtx.sampleRate;
        const binWidth = sampleRate / micAnalyser.fftSize;
        const bin432 = Math.round(432 / binWidth);
        const bin864 = Math.round(864 / binWidth);
        const maxFreq = 2000;
        const maxBin = Math.min(Math.round(maxFreq / binWidth), bufLen);

        let glowActive = false;
        let micSpecCol = 0;
        let micSpecImageData = null;

        function draw() {
            micAnimFrame = requestAnimationFrame(draw);
            micAnalyser.getByteFrequencyData(dataArr);

            const dpr = window.devicePixelRatio || 1;
            const cw = canvas.clientWidth;
            const ch = canvas.clientHeight;
            const pw = Math.round(cw * dpr);
            const ph = Math.round(ch * dpr);

            if (canvas.width !== pw || canvas.height !== ph) {
                canvas.width = pw;
                canvas.height = ph;
                micSpecImageData = null;
                micSpecCol = 0;
            }

            ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

            const w = cw;
            const h = ch;

            if (vizSpectrogramMode) {
                if (!micSpecImageData) {
                    ctx.fillStyle = "#0a0a0f";
                    ctx.fillRect(0, 0, w, h);
                    micSpecImageData = ctx.getImageData(0, 0, w, h);
                    micSpecCol = 0;
                }

                const imgData = micSpecImageData;
                const iw = imgData.width;
                const ih = imgData.height;
                const pixels = imgData.data;

                if (micSpecCol >= iw) {
                    for (let y = 0; y < ih; y++) {
                        const rowStart = y * iw * 4;
                        for (let x = 0; x < iw - 1; x++) {
                            const dst = rowStart + x * 4;
                            const src = rowStart + (x + 1) * 4;
                            pixels[dst] = pixels[src];
                            pixels[dst + 1] = pixels[src + 1];
                            pixels[dst + 2] = pixels[src + 2];
                            pixels[dst + 3] = pixels[src + 3];
                        }
                    }
                    micSpecCol = iw - 1;
                }

                const x = micSpecCol;
                for (let i = 0; i < maxBin && i < ih; i++) {
                    const y = ih - 1 - Math.round((i / maxBin) * (ih - 1));
                    const val = dataArr[i] / 255;
                    const idx = (y * iw + x) * 4;
                    const isSapphire = Math.abs(i - bin432) <= 1;
                    if (isSapphire && val > 0.05) {
                        const glow = Math.min(val * 2.5, 1.0);
                        pixels[idx] = Math.round(40 + 37 * glow);
                        pixels[idx + 1] = Math.round(130 + 126 * glow);
                        pixels[idx + 2] = Math.round(220 + 35 * glow);
                        pixels[idx + 3] = 255;
                    } else {
                        pixels[idx] = Math.round(val * val * 200 + val * 55);
                        pixels[idx + 1] = Math.round(val * val * 40 + val * 20);
                        pixels[idx + 2] = Math.round(val * 180 + 20);
                        pixels[idx + 3] = 255;
                    }
                }
                micSpecCol++;
                ctx.putImageData(imgData, 0, 0);

                const sapphireY = ih - 1 - Math.round((bin432 / maxBin) * (ih - 1));
                const screenY = (sapphireY / ih) * h;
                ctx.strokeStyle = "rgba(77, 166, 255, 0.6)";
                ctx.lineWidth = 1;
                ctx.shadowColor = "#4da6ff";
                ctx.shadowBlur = 6;
                ctx.beginPath();
                ctx.moveTo(0, screenY);
                ctx.lineTo(w, screenY);
                ctx.stroke();
                ctx.shadowBlur = 0;
                ctx.fillStyle = "#4da6ff";
                ctx.font = "10px monospace";
                ctx.fillText("432 Hz", 4, screenY - 4);
            } else {
                ctx.fillStyle = "#0a0a0f";
                ctx.fillRect(0, 0, w, h);

                const barW = w / maxBin;
                let peakVal = 0, peakBin = 0;

                for (let i = 0; i < maxBin; i++) {
                    const val = dataArr[i];
                    const barH = (val / 255) * h * 0.9;
                    if (val > peakVal) { peakVal = val; peakBin = i; }
                    const inGoldZone = Math.abs(i - bin432) <= 2;
                    if (inGoldZone) {
                        ctx.fillStyle = "#ffd700";
                        ctx.shadowColor = "#ffd700";
                        ctx.shadowBlur = 8;
                    } else {
                        ctx.fillStyle = "rgba(124, 92, 255, 0.7)";
                        ctx.shadowBlur = 0;
                    }
                    ctx.fillRect(i * barW, h - barH, Math.max(barW - 1, 1), barH);
                    ctx.shadowBlur = 0;
                }

                const goldX = bin432 * barW;
                ctx.strokeStyle = "rgba(255, 215, 0, 0.4)";
                ctx.lineWidth = 1;
                ctx.setLineDash([4, 4]);
                ctx.beginPath();
                ctx.moveTo(goldX, 0);
                ctx.lineTo(goldX, h);
                ctx.stroke();
                ctx.setLineDash([]);
                ctx.fillStyle = "#ffd700";
                ctx.font = "10px monospace";
                ctx.fillText("432", goldX - 8, 12);
            }

            const peakFreq = (Array.from(dataArr.slice(0, maxBin)).reduce((best, v, i) => v > best.v ? {v, i} : best, {v:0,i:0}).i * binWidth).toFixed(0);
            document.getElementById("viz-peak-freq").textContent = `Peak: ${peakFreq} Hz`;

            const level432 = dataArr[bin432] || 0;
            const level864 = dataArr[bin864] || 0;
            document.getElementById("viz-432-level").textContent = `432 Hz: ${level432}/255`;

            const vizContainer = document.getElementById("viz-container");
            const sigStatus = document.getElementById("viz-signal-status");

            const isPilotTone = level432 >= PILOT_432_THRESHOLD && level864 >= PILOT_864_THRESHOLD;

            if (isPilotTone) {
                if (pilotLockStart === 0) pilotLockStart = performance.now();
                const elapsed = performance.now() - pilotLockStart;

                if (elapsed >= PILOT_SUSTAIN_MS && !sapphireBubbleActive) {
                    sapphireBubbleActive = true;
                    document.body.classList.add("sapphire-bubble-mode");
                    vizContainer.classList.remove("gold-glow-border");
                    vizContainer.classList.add("sapphire-bubble-border");
                    sigStatus.textContent = "FLY CAUGHT — Sapphire Bubble Active";
                    sigStatus.style.color = "#4da6ff";
                    showToast("Wing-Beat detected — Fly caught!", "success");
                } else if (!sapphireBubbleActive) {
                    if (!glowActive) {
                        glowActive = true;
                        vizContainer.classList.add("gold-glow-border");
                        sigStatus.textContent = "PILOT TONE — Locking...";
                        sigStatus.style.color = "#ffd700";
                    }
                }
            } else if (level432 >= SIGNAL_THRESHOLD) {
                pilotLockStart = 0;
                if (!glowActive) {
                    glowActive = true;
                    vizContainer.classList.add("gold-glow-border");
                    sigStatus.textContent = "SIGNAL DETECTED";
                    sigStatus.style.color = "#ffd700";
                }
                if (sapphireBubbleActive) {
                    sapphireBubbleActive = false;
                    document.body.classList.remove("sapphire-bubble-mode");
                    vizContainer.classList.remove("sapphire-bubble-border");
                }
            } else {
                pilotLockStart = 0;
                if (glowActive || sapphireBubbleActive) {
                    glowActive = false;
                    sapphireBubbleActive = false;
                    vizContainer.classList.remove("gold-glow-border");
                    vizContainer.classList.remove("sapphire-bubble-border");
                    document.body.classList.remove("sapphire-bubble-mode");
                    sigStatus.textContent = "Signal: Scanning...";
                    sigStatus.style.color = "";
                }
            }
        }

        draw();
    }

    function drawSpectrum() {
        if (!vizAnalyser) return;

        const canvas = document.getElementById("viz-canvas");
        const ctx = canvas.getContext("2d");
        const bufLen = vizAnalyser.frequencyBinCount;
        const dataArr = new Uint8Array(bufLen);

        const sampleRate = vizAudioCtx.sampleRate;
        const binWidth = sampleRate / vizAnalyser.fftSize;
        const bin432 = Math.round(432 / binWidth);
        const maxFreq = 2000;
        const maxBin = Math.min(Math.round(maxFreq / binWidth), bufLen);

        let specCol = 0;

        function draw() {
            vizAnimFrame = requestAnimationFrame(draw);
            vizAnalyser.getByteFrequencyData(dataArr);

            const dpr = window.devicePixelRatio || 1;
            const cw = canvas.clientWidth;
            const ch = canvas.clientHeight;
            const pw = Math.round(cw * dpr);
            const ph = Math.round(ch * dpr);

            if (canvas.width !== pw || canvas.height !== ph) {
                canvas.width = pw;
                canvas.height = ph;
                spectrogramImageData = null;
                specCol = 0;
            }

            ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

            if (vizPocketMode) {
                drawVocalPocket(ctx, cw, ch, dataArr, maxBin, bin432, binWidth);
            } else if (vizSpectrogramMode) {
                drawSpectrogram(ctx, cw, ch, dataArr, maxBin, bin432, binWidth);
            } else {
                drawBarSpectrum(ctx, cw, ch, dataArr, maxBin, bin432, binWidth);
            }
        }

        function drawBarSpectrum(ctx, w, h, dataArr, maxBin, bin432, binWidth) {
            ctx.fillStyle = "#0a0a0f";
            ctx.fillRect(0, 0, w, h);

            const barW = w / maxBin;
            let peakVal = 0, peakBin = 0;

            for (let i = 0; i < maxBin; i++) {
                const val = dataArr[i];
                const barH = (val / 255) * h * 0.9;

                if (val > peakVal) { peakVal = val; peakBin = i; }

                const inGoldZone = Math.abs(i - bin432) <= 2;
                if (inGoldZone) {
                    ctx.fillStyle = "#ffd700";
                    ctx.shadowColor = "#ffd700";
                    ctx.shadowBlur = 8;
                } else {
                    ctx.fillStyle = "rgba(124, 92, 255, 0.7)";
                    ctx.shadowBlur = 0;
                }

                ctx.fillRect(i * barW, h - barH, Math.max(barW - 1, 1), barH);
                ctx.shadowBlur = 0;
            }

            const goldX = bin432 * barW;
            ctx.strokeStyle = "rgba(255, 215, 0, 0.4)";
            ctx.lineWidth = 1;
            ctx.setLineDash([4, 4]);
            ctx.beginPath();
            ctx.moveTo(goldX, 0);
            ctx.lineTo(goldX, h);
            ctx.stroke();
            ctx.setLineDash([]);

            ctx.fillStyle = "#ffd700";
            ctx.font = "10px monospace";
            ctx.fillText("432", goldX - 8, 12);

            const peakFreq = (peakBin * binWidth).toFixed(0);
            document.getElementById("viz-peak-freq").textContent = `Peak: ${peakFreq} Hz`;
            document.getElementById("viz-432-level").textContent = `432 Hz: ${dataArr[bin432] || 0}/255`;
        }

        function drawVocalPocket(ctx, w, h, dataArr, maxBin, bin432, binWidth) {
            ctx.fillStyle = "#0a0a0f";
            ctx.fillRect(0, 0, w, h);

            pocketPhase += 0.02;
            const breathCycle = Math.sin(pocketPhase);
            const breathScale = 0.6 + 0.4 * breathCycle;

            const level432 = (dataArr[bin432] || 0) / 255;
            const cx = w / 2;
            const cy = h / 2;
            const baseRadius = Math.min(w, h) * 0.35;
            const pulseRadius = baseRadius * breathScale;

            const outerGrad = ctx.createRadialGradient(cx, cy, pulseRadius * 0.1, cx, cy, pulseRadius);
            outerGrad.addColorStop(0, `rgba(255, 215, 0, ${0.15 + level432 * 0.3})`);
            outerGrad.addColorStop(0.5, `rgba(255, 215, 0, ${0.05 + level432 * 0.1})`);
            outerGrad.addColorStop(1, "rgba(255, 215, 0, 0)");
            ctx.fillStyle = outerGrad;
            ctx.beginPath();
            ctx.arc(cx, cy, pulseRadius, 0, Math.PI * 2);
            ctx.fill();

            const numPockets = 8;
            const pocketDepthBase = 0.35;
            for (let i = 0; i < numPockets; i++) {
                const angle = (i / numPockets) * Math.PI * 2 + pocketPhase * 0.5;
                const freqIdx = Math.min(Math.floor((i / numPockets) * maxBin), maxBin - 1);
                const freqLevel = (dataArr[freqIdx] || 0) / 255;

                const pocketOpen = breathCycle > 0 ? breathCycle : 0;
                const pocketDepth = pocketDepthBase * pocketOpen * (1 - freqLevel * 0.5);
                const pocketR = pulseRadius * (0.4 + pocketDepth * 0.3);

                const px = cx + Math.cos(angle) * pulseRadius * 0.7;
                const py = cy + Math.sin(angle) * pulseRadius * 0.7;

                const pocketGrad = ctx.createRadialGradient(px, py, 2, px, py, pocketR);
                const sapAlpha = 0.15 + pocketOpen * 0.4;
                pocketGrad.addColorStop(0, `rgba(40, 120, 220, ${sapAlpha})`);
                pocketGrad.addColorStop(0.6, `rgba(20, 80, 180, ${sapAlpha * 0.5})`);
                pocketGrad.addColorStop(1, "rgba(10, 40, 100, 0)");
                ctx.fillStyle = pocketGrad;
                ctx.beginPath();
                ctx.arc(px, py, pocketR, 0, Math.PI * 2);
                ctx.fill();

                if (pocketOpen > 0.3) {
                    ctx.strokeStyle = `rgba(60, 160, 255, ${pocketOpen * 0.5})`;
                    ctx.lineWidth = 1;
                    ctx.beginPath();
                    ctx.arc(px, py, pocketR * 0.6, 0, Math.PI * 2);
                    ctx.stroke();
                }
            }

            ctx.strokeStyle = `rgba(255, 215, 0, ${0.3 + level432 * 0.5})`;
            ctx.lineWidth = 2;
            ctx.shadowColor = "#ffd700";
            ctx.shadowBlur = level432 * 15;
            ctx.beginPath();
            ctx.arc(cx, cy, pulseRadius * 0.25, 0, Math.PI * 2);
            ctx.stroke();
            ctx.shadowBlur = 0;

            ctx.fillStyle = `rgba(255, 215, 0, ${0.5 + level432 * 0.5})`;
            ctx.font = "bold 12px monospace";
            ctx.textAlign = "center";
            ctx.fillText("432 Hz", cx, cy + 4);
            ctx.textAlign = "start";

            const stateText = breathCycle > 0.2 ? "POCKET OPEN" : breathCycle < -0.2 ? "POCKET SEALED" : "TRANSITIONING";
            const stateColor = breathCycle > 0.2 ? "#3ca0ff" : breathCycle < -0.2 ? "#ffd700" : "#666";
            ctx.fillStyle = stateColor;
            ctx.font = "10px monospace";
            ctx.fillText(stateText, 10, h - 10);

            ctx.fillStyle = "#888";
            ctx.fillText(`Breath: ${(breathCycle * 100).toFixed(0)}%`, w - 120, h - 10);

            document.getElementById("viz-peak-freq").textContent = `Pocket: ${stateText}`;
            document.getElementById("viz-432-level").textContent = `432 Hz: ${dataArr[bin432] || 0}/255`;
        }

        function drawSpectrogram(ctx, w, h, dataArr, maxBin, bin432, binWidth) {
            if (!spectrogramImageData) {
                ctx.fillStyle = "#0a0a0f";
                ctx.fillRect(0, 0, w, h);
                spectrogramImageData = ctx.getImageData(0, 0, w, h);
                specCol = 0;
            }

            const imgData = spectrogramImageData;
            const iw = imgData.width;
            const ih = imgData.height;
            const pixels = imgData.data;

            if (specCol >= iw) {
                const rowBytes = 4;
                for (let y = 0; y < ih; y++) {
                    const rowStart = y * iw * rowBytes;
                    for (let x = 0; x < iw - 1; x++) {
                        const dst = rowStart + x * rowBytes;
                        const src = rowStart + (x + 1) * rowBytes;
                        pixels[dst] = pixels[src];
                        pixels[dst + 1] = pixels[src + 1];
                        pixels[dst + 2] = pixels[src + 2];
                        pixels[dst + 3] = pixels[src + 3];
                    }
                }
                specCol = iw - 1;
            }

            const x = specCol;
            for (let i = 0; i < maxBin && i < ih; i++) {
                const y = ih - 1 - Math.round((i / maxBin) * (ih - 1));
                const val = dataArr[i] / 255;
                const idx = (y * iw + x) * 4;

                const isSapphire = Math.abs(i - bin432) <= 1;
                if (isSapphire && val > 0.05) {
                    const glow = Math.min(val * 2.5, 1.0);
                    pixels[idx] = Math.round(40 + 37 * glow);
                    pixels[idx + 1] = Math.round(130 + 126 * glow);
                    pixels[idx + 2] = Math.round(220 + 35 * glow);
                    pixels[idx + 3] = 255;
                } else {
                    const r = Math.round(val * val * 200 + val * 55);
                    const g = Math.round(val * val * 40 + val * 20);
                    const b = Math.round(val * 180 + 20);
                    pixels[idx] = r;
                    pixels[idx + 1] = g;
                    pixels[idx + 2] = b;
                    pixels[idx + 3] = 255;
                }
            }

            specCol++;
            ctx.putImageData(imgData, 0, 0);

            const sapphireY = ih - 1 - Math.round((bin432 / maxBin) * (ih - 1));
            const screenY = (sapphireY / ih) * h;
            ctx.strokeStyle = "rgba(77, 166, 255, 0.6)";
            ctx.lineWidth = 1;
            ctx.shadowColor = "#4da6ff";
            ctx.shadowBlur = 6;
            ctx.beginPath();
            ctx.moveTo(0, screenY);
            ctx.lineTo(w, screenY);
            ctx.stroke();
            ctx.shadowBlur = 0;

            ctx.fillStyle = "#4da6ff";
            ctx.font = "10px monospace";
            ctx.fillText("432 Hz", 4, screenY - 4);

            let peakVal = 0, peakBin = 0;
            for (let i = 0; i < maxBin; i++) {
                if (dataArr[i] > peakVal) { peakVal = dataArr[i]; peakBin = i; }
            }
            const peakFreq = (peakBin * binWidth).toFixed(0);
            document.getElementById("viz-peak-freq").textContent = `Peak: ${peakFreq} Hz`;
            document.getElementById("viz-432-level").textContent = `432 Hz: ${dataArr[bin432] || 0}/255`;
        }

        draw();
    }

    document.getElementById("cap-btn").addEventListener("click", async () => {
        const filename = document.getElementById("cap-file-select").value;
        const source = document.querySelector('input[name="cap-source"]:checked').value;
        const btn = document.getElementById("cap-btn");

        if (!filename) {
            showToast("Select a WAV file to analyze", "error");
            return;
        }

        btn.disabled = true;
        btn.innerHTML = '<span class="spinner"></span>Analyzing...';
        document.getElementById("cap-result").style.display = "none";

        try {
            const res = await fetch("/api/capacity", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ filename, source }),
            });
            const d = await res.json();

            if (d.success) {
                document.getElementById("cap-filename").textContent = d.filename;
                document.getElementById("cap-duration").textContent = d.duration.toFixed(1) + "s";
                document.getElementById("cap-samplerate").textContent = d.sample_rate.toLocaleString() + " Hz";
                document.getElementById("cap-samples").textContent = d.total_samples.toLocaleString();

                const maxRef = d.capacity_2bit || 1;

                document.getElementById("cap-max-1").textContent = formatSize(d.capacity_1bit);
                document.getElementById("cap-safe-1").textContent = formatSize(d.surface_tension_1bit);
                document.getElementById("cap-burst-1").textContent = formatSize(d.bubble_burst_1bit) + " (90% membrane)";
                document.getElementById("cap-est-1").textContent = "~" + formatSize(d.surface_tension_1bit * 3) + " - " + formatSize(d.surface_tension_1bit * 5);
                document.getElementById("cap-bar-1-max").style.width = (d.capacity_1bit / maxRef * 100) + "%";
                document.getElementById("cap-bar-1-safe").style.width = (d.surface_tension_1bit / maxRef * 100) + "%";
                document.getElementById("cap-bar-1-burst").style.width = (d.bubble_burst_1bit / maxRef * 100) + "%";
                document.getElementById("cap-bar-1-est").style.width = (d.surface_tension_1bit * 4 / maxRef * 100) + "%";

                document.getElementById("cap-max-2").textContent = formatSize(d.capacity_2bit);
                document.getElementById("cap-safe-2").textContent = formatSize(d.surface_tension_2bit);
                document.getElementById("cap-burst-2").textContent = formatSize(d.bubble_burst_2bit) + " (90% membrane)";
                document.getElementById("cap-est-2").textContent = "~" + formatSize(d.surface_tension_2bit * 3) + " - " + formatSize(d.surface_tension_2bit * 5);
                document.getElementById("cap-bar-2-max").style.width = "100%";
                document.getElementById("cap-bar-2-safe").style.width = (d.surface_tension_2bit / maxRef * 100) + "%";
                document.getElementById("cap-bar-2-burst").style.width = (d.bubble_burst_2bit / maxRef * 100) + "%";
                document.getElementById("cap-bar-2-est").style.width = (d.surface_tension_2bit * 4 / maxRef * 100) + "%";

                document.getElementById("cap-result").style.display = "block";
                showToast("Analysis complete!", "success");
            } else {
                showToast(d.error, "error");
            }
        } catch (e) {
            showToast("Analysis failed: " + e.message, "error");
        }

        btn.disabled = false;
        btn.textContent = "Analyze Capacity";
    });

    document.getElementById("silk-signal").addEventListener("input", (e) => {
        document.getElementById("silk-char-count").textContent = e.target.value.length;
    });

    document.getElementById("silk-send-btn").addEventListener("click", async () => {
        const signal = document.getElementById("silk-signal").value.trim();
        const btn = document.getElementById("silk-send-btn");

        if (!signal) {
            showToast("Enter a signal to send", "error");
            return;
        }

        btn.disabled = true;
        btn.innerHTML = '<span class="spinner"></span>Sending Signal...';
        document.getElementById("silk-send-result").style.display = "none";

        try {
            const res = await fetch("/api/silk/send", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ signal }),
            });
            const data = await res.json();

            if (data.success) {
                document.getElementById("silk-res-signal").textContent = data.signal;
                document.getElementById("silk-res-file").textContent = data.output_file;
                document.getElementById("silk-res-size").textContent = formatSize(data.output_size);
                document.getElementById("silk-res-time").textContent = data.timestamp;
                document.getElementById("silk-res-hash").textContent = data.hash_key;
                document.getElementById("silk-send-result").style.display = "block";
                showToast("Sapphire Bubble blown!", "success");
                document.getElementById("silk-signal").value = "";
                document.getElementById("silk-char-count").textContent = "0";

                const silkPanel = document.getElementById("silk");
                silkPanel.classList.remove("sapphire-glow");
                void silkPanel.offsetWidth;
                silkPanel.classList.add("sapphire-glow");
                setTimeout(() => silkPanel.classList.remove("sapphire-glow"), 2100);

                loadSilkFeed();
                loadSelects();
            } else {
                showToast(data.error, "error");
            }
        } catch (e) {
            showToast("Signal failed: " + e.message, "error");
        }

        btn.disabled = false;
        btn.textContent = "Send Signal";
    });

    document.getElementById("copy-silk-hash-btn").addEventListener("click", () => {
        const key = document.getElementById("silk-res-hash").textContent;
        navigator.clipboard.writeText(key).then(() => {
            showToast("Hash Key copied!", "success");
        }).catch(() => {
            const ta = document.createElement("textarea");
            ta.value = key;
            document.body.appendChild(ta);
            ta.select();
            document.execCommand("copy");
            document.body.removeChild(ta);
            showToast("Hash Key copied!", "success");
        });
    });

    async function loadSilkFeed() {
        const feed = document.getElementById("silk-feed");
        try {
            const res = await fetch("/api/silk/signals?limit=20");
            const data = await res.json();

            if (!data.success || !data.signals.length) {
                feed.innerHTML = '<p class="loading">No signals yet</p>';
                return;
            }

            feed.innerHTML = data.signals.map(s => `
                <div class="silk-entry">
                    <div class="silk-entry-left">
                        <span class="silk-signal-text">${s.signal}</span>
                        <span class="silk-entry-meta">${s.timestamp} &middot; ${s.output_file}</span>
                    </div>
                    <div class="silk-entry-right">
                        <span class="silk-status">${s.status}</span>
                        <span class="silk-hash-tail">${s.hash_tail}</span>
                    </div>
                </div>
            `).join("");
        } catch {
            feed.innerHTML = '<p class="loading">Failed to load signals</p>';
        }
    }

    document.getElementById("purge-btn").addEventListener("click", async () => {
        const btn = document.getElementById("purge-btn");
        const status = document.getElementById("purge-status");

        if (!confirm("This will permanently delete all files in output_audio/ older than 24 hours. Continue?")) return;

        btn.disabled = true;
        btn.textContent = "Purging...";
        status.textContent = "";

        try {
            const res = await fetch("/api/purge", { method: "POST" });
            const data = await res.json();

            if (data.success) {
                if (data.purged_count === 0) {
                    status.textContent = "No files older than 24h found.";
                    showToast("Nothing to purge", "success");
                } else {
                    status.textContent = `Purged ${data.purged_count} file(s), freed ${formatSize(data.freed_bytes)}`;
                    showToast(`Purged ${data.purged_count} file(s)!`, "success");
                    refreshFiles();
                }
            } else {
                showToast(data.error || "Purge failed", "error");
            }
        } catch (e) {
            showToast("Purge failed: " + e.message, "error");
        }

        btn.disabled = false;
        btn.textContent = "Purge Files Older Than 24h";
    });

    let listenerStream = null;
    let listenerCtx = null;
    let listenerAnalyser = null;
    let listenerAnimFrame = null;
    let listenerRecorder = null;
    let listenerRecording = false;
    let lockOnStartTime = 0;
    const LOCK_THRESHOLD_432 = 100;
    const LOCK_THRESHOLD_864 = 40;
    const LOCK_SUSTAIN_MS = 500;
    const RECORD_DURATION = 6000;
    const LISTENER_FFT_SIZE = 8192;

    document.getElementById("silk-listen-btn").addEventListener("click", async () => {
        const sonar = document.getElementById("sonar-ring");
        const status = document.getElementById("sonar-status");

        try {
            listenerStream = await navigator.mediaDevices.getUserMedia({ audio: true });
            listenerCtx = new (window.AudioContext || window.webkitAudioContext)();
            listenerAnalyser = listenerCtx.createAnalyser();
            listenerAnalyser.fftSize = LISTENER_FFT_SIZE;

            const source = listenerCtx.createMediaStreamSource(listenerStream);
            source.connect(listenerAnalyser);

            document.getElementById("silk-listen-btn").style.display = "none";
            document.getElementById("silk-listen-stop-btn").style.display = "inline-block";

            sonar.classList.add("active");
            status.textContent = "Scanning for 432 Hz...";
            document.getElementById("listener-decode-result").style.display = "none";

            runListenerLoop();
            showToast("Listener active — scanning for 432 Hz signature", "success");
        } catch (e) {
            showToast("Microphone access denied", "error");
        }
    });

    document.getElementById("silk-listen-stop-btn").addEventListener("click", stopListener);

    function stopListener() {
        if (listenerStream) {
            listenerStream.getTracks().forEach(t => t.stop());
            listenerStream = null;
        }
        if (listenerAnimFrame) cancelAnimationFrame(listenerAnimFrame);
        if (listenerCtx) { listenerCtx.close(); listenerCtx = null; }
        listenerAnalyser = null;
        listenerRecording = false;

        document.getElementById("silk-listen-btn").style.display = "inline-block";
        document.getElementById("silk-listen-stop-btn").style.display = "none";
        document.getElementById("sonar-ring").classList.remove("active", "locked");
        document.getElementById("sonar-status").textContent = "Sonar Idle";
    }

    function runListenerLoop() {
        if (!listenerAnalyser) return;

        const bufLen = listenerAnalyser.frequencyBinCount;
        const dataArr = new Uint8Array(bufLen);
        const sampleRate = listenerCtx.sampleRate;
        const bin432 = Math.round(432 * (LISTENER_FFT_SIZE / sampleRate));
        const bin864 = Math.round(864 * (LISTENER_FFT_SIZE / sampleRate));
        const sonar = document.getElementById("sonar-ring");
        const status = document.getElementById("sonar-status");
        lockOnStartTime = 0;

        function scan() {
            if (!listenerAnalyser) return;
            listenerAnimFrame = requestAnimationFrame(scan);
            listenerAnalyser.getByteFrequencyData(dataArr);

            const level432 = dataArr[bin432] || 0;
            const level864 = dataArr[bin864] || 0;

            if (level432 >= LOCK_THRESHOLD_432 && level864 >= LOCK_THRESHOLD_864) {
                if (lockOnStartTime === 0) {
                    lockOnStartTime = performance.now();
                    status.textContent = "Locking on...";
                }

                const elapsed = performance.now() - lockOnStartTime;

                if (elapsed >= LOCK_SUSTAIN_MS && !listenerRecording) {
                    sonar.classList.remove("active");
                    sonar.classList.add("locked");
                    status.textContent = "BUBBLE CAUGHT — Recording 6s...";
                    listenerRecording = true;
                    captureAndDecode();
                }
            } else {
                if (lockOnStartTime !== 0 && !listenerRecording) {
                    lockOnStartTime = 0;
                    status.textContent = "Scanning for 432 Hz...";
                }
            }
        }

        scan();
    }

    async function captureAndDecode() {
        const sonar = document.getElementById("sonar-ring");
        const status = document.getElementById("sonar-status");

        try {
            const captureStream = await navigator.mediaDevices.getUserMedia({ audio: true });
            const recorder = new MediaRecorder(captureStream, { mimeType: "audio/webm" });
            const chunks = [];

            recorder.ondataavailable = (e) => { if (e.data.size > 0) chunks.push(e.data); };

            recorder.onstop = async () => {
                captureStream.getTracks().forEach(t => t.stop());
                const blob = new Blob(chunks, { type: "audio/webm" });

                status.textContent = "Decoding captured audio...";

                const formData = new FormData();
                formData.append("audio", blob, "capture.webm");

                const keyInput = document.getElementById("default-key-input").value.trim();
                if (keyInput) formData.append("hash_key", keyInput);

                try {
                    const res = await fetch("/api/decode/audio", {
                        method: "POST",
                        body: formData,
                    });
                    const data = await res.json();

                    if (data.success) {
                        document.getElementById("listener-signal").textContent = data.signal_text;
                        document.getElementById("listener-snr").textContent = data.purity.snr_db + " dB";
                        document.getElementById("listener-quality").textContent = data.purity.quality;

                        const warn = document.getElementById("listener-warning");
                        if (data.purity.warning) {
                            warn.textContent = data.purity.warning;
                            warn.style.display = "block";
                        } else {
                            warn.style.display = "none";
                        }

                        document.getElementById("listener-decode-result").style.display = "block";
                        showToast(`Bubble caught: ${data.signal_text}`, "success");

                        sonar.classList.remove("locked");
                        sonar.classList.add("bubble-caught");
                        setTimeout(() => sonar.classList.remove("bubble-caught"), 1200);

                        const silkPanel = document.getElementById("silk");
                        silkPanel.classList.remove("sapphire-glow");
                        void silkPanel.offsetWidth;
                        silkPanel.classList.add("sapphire-glow");
                        setTimeout(() => silkPanel.classList.remove("sapphire-glow"), 2100);

                        loadSilkFeed();
                    } else {
                        showToast(data.error || "Decode failed", "error");
                    }
                } catch (e) {
                    showToast("Decode error: " + e.message, "error");
                }

                listenerRecording = false;
                sonar.classList.remove("locked");
                if (listenerStream) {
                    sonar.classList.add("active");
                    status.textContent = "Scanning for 432 Hz...";
                } else {
                    status.textContent = "Sonar Idle";
                }
            };

            recorder.start();
            setTimeout(() => {
                if (recorder.state === "recording") recorder.stop();
            }, RECORD_DURATION);

        } catch (e) {
            showToast("Recording failed: " + e.message, "error");
            listenerRecording = false;
            sonar.classList.remove("locked");
            sonar.classList.add("active");
            status.textContent = "Scanning for 432 Hz...";
        }
    }

    document.getElementById("set-default-key-btn").addEventListener("click", async () => {
        const key = document.getElementById("default-key-input").value.trim();
        if (!key) { showToast("Enter a hash key first", "error"); return; }

        const res = await fetch("/api/settings/default-key", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ key }),
        });
        const data = await res.json();
        document.getElementById("default-key-status").textContent = data.message;
        showToast("Village Default Key set!", "success");
    });

    document.getElementById("clear-default-key-btn").addEventListener("click", async () => {
        await fetch("/api/settings/default-key", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ key: "" }),
        });
        document.getElementById("default-key-input").value = "";
        document.getElementById("default-key-status").textContent = "Key cleared";
        showToast("Village Default Key cleared", "success");
    });

    document.getElementById("low-power-toggle").addEventListener("change", async (e) => {
        const enabled = e.target.checked;
        await fetch("/api/low-power", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ enabled }),
        });
        const statusText = document.getElementById("engine-status-text");
        statusText.textContent = enabled ? "Low-Power Resonance" : "Engine Active";
        showToast(enabled ? "Low-Power mode active" : "Full power restored", "success");
    });

    fetch("/api/low-power").then(r => r.json()).then(d => {
        document.getElementById("low-power-toggle").checked = d.low_power;
        if (d.low_power) document.getElementById("engine-status-text").textContent = "Low-Power Resonance";
    });

    loadSelects();

    function renderSensorGrid(containerId, sensors) {
        const el = document.getElementById(containerId);
        if (!el) return;
        el.innerHTML = "";
        for (const [key, val] of Object.entries(sensors)) {
            const item = document.createElement("div");
            item.className = "sensor-item";
            const label = key.replace(/_/g, " ");
            item.innerHTML = `<span class="sensor-label">${label}</span><span class="sensor-value">${val}</span>`;
            el.appendChild(item);
        }
    }

    function renderChecklist(data) {
        const verdictEl = document.getElementById("harness-checklist-verdict");
        const checksEl = document.getElementById("harness-checklist-results");
        if (!verdictEl || !checksEl) return;

        const v = data.overall_verdict;
        verdictEl.className = "harness-verdict " + v.toLowerCase();
        verdictEl.textContent = v + " (" + data.passed + "/" + data.total_checks + " passed)";

        checksEl.innerHTML = "";
        for (const check of data.checks) {
            const icons = { PASS: "\u2713", FAIL: "\u2717", RECONSIDER: "?" };
            const row = document.createElement("div");
            row.className = "harness-check-item";
            row.innerHTML =
                `<div class="harness-check-icon ${check.verdict.toLowerCase()}">${icons[check.verdict] || "?"}</div>` +
                `<span class="harness-check-msg">${check.message}</span>`;
            checksEl.appendChild(row);
        }
    }

    function loadHarnessStatus() {
        fetch("/api/harness/status").then(r => r.json()).then(data => {
            if (!data.success) return;
            const state = data.environment_state;

            renderSensorGrid("harness-aqua-sensors", {
                "pH": state.aquaponics.ph,
                "Temp": state.aquaponics.temperature_c + "\u00b0C",
                "O\u2082": state.aquaponics.dissolved_oxygen_ppm + " ppm",
                "NH\u2083": state.aquaponics.ammonia_ppm + " ppm",
                "Pumps/hr": state.aquaponics.pump_cycles_this_hour,
                "Water": state.aquaponics.water_level_pct + "%",
            });

            renderSensorGrid("harness-flywheel-sensors", {
                "RPM": state.flywheel.rpm,
                "Energy": state.flywheel.energy_reserve_wh + " Wh",
                "Temp": state.flywheel.temperature_c + "\u00b0C",
                "Vibration": state.flywheel.vibration_g + " g",
            });

            const silkData = {};
            silkData["Total R"] = state.silk_wiring.total_resistance_ohm + " \u03a9";
            silkData["Delta"] = state.silk_wiring.resistance_delta_ohm + " \u03a9";
            const strands = state.silk_wiring.strands || [];
            for (let i = 0; i < strands.length; i++) {
                silkData["S" + i] = strands[i].resistance_ohm + "\u03a9 " + (strands[i].continuity ? "\u2713" : "\u2717");
            }
            renderSensorGrid("harness-silk-sensors", silkData);

            const pressure = state.pressure || {};
            renderSensorGrid("harness-pressure-sensors", {
                "Int P": (pressure.internal_pressure_atm || 1.0).toFixed(3) + " atm",
                "Ext P": (pressure.external_pressure_atm || 1.0).toFixed(3) + " atm",
                "Diff": ((pressure.internal_pressure_atm || 1.0) - (pressure.external_pressure_atm || 1.0)).toFixed(3) + " atm",
                "AC Vel": (pressure.air_curtain_velocity_ms || 0).toFixed(1) + " m/s",
                "N2 Boil": (pressure.nitrogen_boil_rate || 0).toFixed(3),
                "Seal": (pressure.seal_integrity_pct || 100).toFixed(1) + "%",
            });

            const pBar = document.getElementById("pressure-bar-fill");
            if (pBar) {
                const pAtm = pressure.internal_pressure_atm || 1.0;
                const pPct = Math.min(100, Math.max(0, (pAtm / 1.8) * 100));
                pBar.style.width = pPct + "%";
                if (pAtm >= 1.5) pBar.style.background = "linear-gradient(90deg, #4ade80, #fbbf24, #f87171, #ff00ff)";
                else if (pAtm >= 1.3) pBar.style.background = "linear-gradient(90deg, #4ade80, #fbbf24, #f87171)";
                else pBar.style.background = "linear-gradient(90deg, #4ade80, #fbbf24)";
            }

            const acLabel = document.getElementById("ac-status-label");
            if (acLabel) {
                if (pressure.air_curtain_active) {
                    acLabel.textContent = "ACTIVE " + (pressure.air_curtain_velocity_ms || 0).toFixed(1) + " m/s";
                    acLabel.className = "ac-status-label active";
                } else {
                    acLabel.textContent = "OFF";
                    acLabel.className = "ac-status-label";
                }
            }

            renderChecklist(data.checklist);

            const loopStats = document.getElementById("harness-loop-stats");
            if (loopStats) {
                const ls = data.loop_detector;
                loopStats.innerHTML =
                    `Detections: <span class="harness-loop-stat">${ls.total_detections}</span> | ` +
                    `Active: <span class="harness-loop-stat">${ls.active_alerts}</span> | ` +
                    `Tracked: <span class="harness-loop-stat">${ls.tracked_signatures}</span>`;
            }
        });

        fetch("/api/harness/loops").then(r => r.json()).then(data => {
            const alertsEl = document.getElementById("harness-loop-alerts");
            if (!alertsEl || !data.success) return;
            if (data.active_alerts.length === 0) {
                alertsEl.innerHTML = '<p style="color:#666;font-size:12px;">No active doom loops.</p>';
                return;
            }
            alertsEl.innerHTML = "";
            for (const a of data.active_alerts) {
                const div = document.createElement("div");
                div.className = "harness-loop-alert";
                div.innerHTML =
                    `<span class="alert-id">${a.alert_id}</span>` +
                    `<div class="alert-msg">${a.message}</div>` +
                    `<div class="alert-diag">${a.diagnostic_suggestions.slice(0, 3).map(d => "\u2022 " + d).join("<br>")}</div>`;
                alertsEl.appendChild(div);
            }
        });
    }

    const harnessTab = document.querySelector('[data-tab="harness"]');
    if (harnessTab) {
        harnessTab.addEventListener("click", () => {
            setTimeout(loadHarnessStatus, 100);
        });
    }

    document.getElementById("harness-simulate-btn")?.addEventListener("click", async () => {
        const actionType = document.getElementById("harness-action-type").value;
        const actionValue = parseInt(document.getElementById("harness-action-value").value) || 1;
        const action = { type: actionType };

        if (actionType === "pump_cycle") action.count = actionValue;
        else if (actionType === "flywheel_boost") action.rpm_delta = actionValue * 100;
        else if (actionType === "sensor_calibrate") action.sensor = "Sensor_A";
        else if (actionType === "nutrient_dose") action.dose_ml = actionValue;
        else if (actionType === "silk_test") action.strand_id = actionValue;
        else if (actionType === "air_curtain_activate") action.velocity_ms = actionValue;
        else if (actionType === "air_curtain_deactivate") { /* no extra params */ }
        else if (actionType === "nitrogen_vent") action.vent_rate = actionValue * 0.1;

        const res = await fetch("/api/harness/check", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ action }),
        });
        const data = await res.json();
        const outEl = document.getElementById("harness-sim-result");
        if (outEl) {
            const sim = data.simulation;
            const verdict = sim.checklist.overall_verdict;
            const color = verdict === "PASS" ? "#00c853" : verdict === "FAIL" ? "#ff4444" : "#ffd700";
            let text = `VERDICT: ${verdict}\n`;
            text += `Safe to execute: ${sim.safe_to_execute}\n`;
            text += `Effects: ${sim.effects.join(", ") || "none"}\n`;
            text += `Loop risk: ${data.loop_risk.risk_level} (${data.loop_risk.recent_attempts}/${data.loop_risk.max_attempts})\n`;
            if (!data.boundary_check.allowed) {
                text += `BOUNDARY BLOCKED: ${data.boundary_check.violations.length} violation(s)\n`;
                for (const v of data.boundary_check.violations) {
                    text += `  - ${v.rule_name}: ${v.message}\n`;
                }
            }
            for (const c of sim.checklist.checks) {
                if (c.verdict !== "PASS") {
                    text += `  [${c.verdict}] ${c.message}\n`;
                }
            }
            outEl.style.color = color;
            outEl.textContent = text;
        }
    });

    document.getElementById("harness-execute-btn")?.addEventListener("click", async () => {
        const actionType = document.getElementById("harness-action-type").value;
        const actionValue = parseInt(document.getElementById("harness-action-value").value) || 1;
        const action = { type: actionType };

        if (actionType === "pump_cycle") action.count = actionValue;
        else if (actionType === "flywheel_boost") action.rpm_delta = actionValue * 100;
        else if (actionType === "sensor_calibrate") action.sensor = "Sensor_A";
        else if (actionType === "nutrient_dose") action.dose_ml = actionValue;
        else if (actionType === "silk_test") action.strand_id = actionValue;
        else if (actionType === "air_curtain_activate") action.velocity_ms = actionValue;
        else if (actionType === "air_curtain_deactivate") { /* no extra params */ }
        else if (actionType === "nitrogen_vent") action.vent_rate = actionValue * 0.1;

        const res = await fetch("/api/harness/execute", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ action }),
        });
        const data = await res.json();
        if (data.success) {
            showToast("Action executed successfully", "success");
            if (data.loop_alert) {
                showToast("DOOM LOOP: " + data.loop_alert.message, "error");
            }
        } else {
            showToast("Blocked: " + (data.blocked_by || "checklist failed"), "error");
        }
        loadHarnessStatus();
    });

    document.getElementById("harness-context-btn")?.addEventListener("click", async () => {
        const res = await fetch("/api/harness/context", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ prompt: "You are a Plankton EA agent operating on the Orin 4000-series." }),
        });
        const data = await res.json();
        const pre = document.getElementById("harness-context-output");
        if (pre && data.success) {
            pre.textContent = data.injected_prompt;
        }
    });

    document.getElementById("ac-activate-btn")?.addEventListener("click", async () => {
        const vel = parseFloat(document.getElementById("ac-velocity-input").value) || 15;
        const res = await fetch("/api/harness/air-curtain", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ action: "activate", velocity_ms: vel }),
        });
        const data = await res.json();
        if (data.success) showToast("Air Curtain activated at " + vel + " m/s", "success");
        else showToast("AC activation failed", "error");
        loadHarnessStatus();
    });

    document.getElementById("ac-deactivate-btn")?.addEventListener("click", async () => {
        const res = await fetch("/api/harness/air-curtain", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ action: "deactivate" }),
        });
        const data = await res.json();
        if (data.success) showToast("Air Curtain deactivated", "success");
        loadHarnessStatus();
    });

    document.getElementById("pressure-reset-btn")?.addEventListener("click", async () => {
        await fetch("/api/harness/pressure/reset", { method: "POST" });
        showToast("Pressure system reset to nominal", "success");
        loadHarnessStatus();
    });

    document.getElementById("chaos-run-btn")?.addEventListener("click", async () => {
        const btn = document.getElementById("chaos-run-btn");
        btn.disabled = true;
        btn.textContent = "Running...";

        const steps = parseInt(document.getElementById("chaos-steps").value) || 10;
        const rate = parseFloat(document.getElementById("chaos-rate").value) || 0.05;
        const esc = parseFloat(document.getElementById("chaos-escalation").value) || 1.5;
        const autoResp = document.getElementById("chaos-auto-respond").checked;

        try {
            const res = await fetch("/api/harness/chaos-test", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    steps: steps,
                    initial_boil_rate: rate,
                    escalation_factor: esc,
                    auto_respond: autoResp,
                }),
            });
            const data = await res.json();
            if (data.success && data.report) {
                renderChaosReport(data.report);
                showToast("Chaos test complete: " + data.report.outcome, data.report.seal_survived ? "success" : "error");
            } else {
                showToast(data.error || "Chaos test failed", "error");
            }
        } catch(e) {
            showToast("Chaos test error: " + e.message, "error");
        }
        btn.disabled = false;
        btn.textContent = "Run Chaos Test";
        loadHarnessStatus();
    });

    document.getElementById("adriana-transpile-btn")?.addEventListener("click", async () => {
        const expr = document.getElementById("adriana-input").value.trim();
        if (!expr) return showToast("Enter an Adriana expression", "error");
        try {
            const res = await fetch("/api/harness/adriana/transpile", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ expression: expr }),
            });
            const data = await res.json();
            if (data.result) renderAdrianaResult(data.result, data.dry_runs);
            else showToast(data.error || "Transpile failed", "error");
        } catch(e) { showToast("Error: " + e.message, "error"); }
    });

    document.getElementById("adriana-execute-btn")?.addEventListener("click", async () => {
        const expr = document.getElementById("adriana-input").value.trim();
        if (!expr) return showToast("Enter an Adriana expression", "error");
        try {
            const res = await fetch("/api/harness/adriana/execute", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ expression: expr }),
            });
            const data = await res.json();
            if (data.result) renderAdrianaResult(data.result, null, data.execution);
            if (data.success) {
                showToast("Adriana: All commands executed", "success");
            } else if (data.partial) {
                showToast("Adriana: Partial execution (some blocked)", "error");
            } else if (data.errors && data.errors.length) {
                showToast("Adriana: " + data.errors[0], "error");
            } else {
                showToast("Adriana: Execution blocked by safety pipeline", "error");
            }
            loadHarnessStatus();
        } catch(e) { showToast("Error: " + e.message, "error"); }
    });

    document.getElementById("adriana-lexicon-btn")?.addEventListener("click", async () => {
        const panel = document.getElementById("adriana-lexicon-panel");
        if (panel.style.display !== "none") {
            panel.style.display = "none";
            return;
        }
        try {
            const res = await fetch("/api/harness/adriana/lexicon");
            const data = await res.json();
            if (data.success) renderAdrianaLexicon(data.lexicon);
            panel.style.display = "block";
        } catch(e) { showToast("Error loading lexicon", "error"); }
    });

    function renderAdrianaResult(result, dryRuns, execResults) {
        const narrativeEl = document.getElementById("adriana-narrative");
        if (narrativeEl && result.narrative) {
            narrativeEl.textContent = result.narrative;
            narrativeEl.style.display = "block";
        }

        const resultEl = document.getElementById("adriana-result");
        resultEl.style.display = "block";

        const comp = result.compression || {};
        document.getElementById("adriana-compression").innerHTML =
            `<div class="ratio-value">${comp.ratio || 0}x</div>` +
            `<div class="ratio-label">COMPRESSION RATIO</div>` +
            `<div style="margin-top:6px; font-size:10px; color:#888;">` +
            `${comp.adriana_chars || 0} chars → ${comp.python_chars || 0} chars<br>` +
            `${comp.adriana_glyphs || 0} glyphs → ${comp.python_tokens || 0} tokens<br>` +
            `Density: ${comp.density || 0}%</div>`;

        const cmdsEl = document.getElementById("adriana-commands");
        cmdsEl.innerHTML = (result.commands || []).map(c =>
            `<div class="adriana-cmd">${c.action_type} → ${c.narrative}</div>`
        ).join("") || '<div style="color:#666;">No commands generated</div>';

        const pyEl = document.getElementById("adriana-python");
        pyEl.innerHTML = `<div class="py-label">Python Equivalent</div>${comp.python_equivalent || "# no equivalent"}`;

        const drEl = document.getElementById("adriana-dry-runs");
        if (dryRuns) {
            drEl.innerHTML = "<div style='color:#888;font-size:10px;margin-bottom:4px;'>SAFETY DRY-RUN</div>" +
                dryRuns.map(dr => {
                    const ok = dr.boundary_allowed && dr.checklist_verdict === "PASS";
                    return `<div class="adriana-dry-run">` +
                        `<span class="dr-verdict ${ok ? 'dr-pass' : 'dr-fail'}">${ok ? 'SAFE' : 'BLOCKED'}</span>` +
                        `<span>${dr.action.type}</span>` +
                        `<span style="color:#666;">${dr.checklist_verdict}</span>` +
                        `</div>`;
                }).join("");
        } else if (execResults) {
            drEl.innerHTML = "<div style='color:#888;font-size:10px;margin-bottom:4px;'>EXECUTION RESULTS</div>" +
                execResults.map(er => {
                    return `<div class="adriana-dry-run">` +
                        `<span class="dr-verdict ${er.executed ? 'dr-pass' : 'dr-fail'}">${er.executed ? 'DONE' : 'BLOCKED'}</span>` +
                        `<span>${er.action.type}</span>` +
                        `<span style="color:#888;font-size:10px;">${er.narrative}</span>` +
                        (er.blocked_by ? `<span style="color:#f87171;font-size:10px;">[${er.blocked_by}]</span>` : '') +
                        `</div>`;
                }).join("");
        } else {
            drEl.innerHTML = "";
        }
    }

    function renderAdrianaLexicon(lex) {
        const renderGroup = (containerId, title, entries) => {
            const el = document.getElementById(containerId);
            el.innerHTML = `<h4>${title}</h4>` +
                entries.map(e =>
                    `<span class="lex-entry" title="${e.description} → ${e.python_equivalent}">` +
                    `<span class="lex-glyph">${e.glyph}</span>` +
                    `<span class="lex-key">${e.key}</span>` +
                    `</span>`
                ).join("");
        };
        renderGroup("adriana-lex-entities", "Entities (Subjects)", lex.entity || []);
        renderGroup("adriana-lex-conditions", "Conditions (Qualifiers)", lex.condition || []);
        renderGroup("adriana-lex-actions", "Actions (Operations)", lex.action || []);
    }

    document.getElementById("aljabr-transpile-btn")?.addEventListener("click", async () => {
        const expr = document.getElementById("aljabr-input").value.trim();
        if (!expr) return showToast("Enter a root expression (e.g. HFZ)", "error");
        try {
            const res = await fetch("/api/harness/aljabr/transpile", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ expression: expr }),
            });
            const data = await res.json();
            if (data.result) renderAlJabrResult(data.result, data.dry_runs);
            else showToast(data.error || "Transpile failed", "error");
        } catch(e) { showToast("Error: " + e.message, "error"); }
    });

    document.getElementById("aljabr-execute-btn")?.addEventListener("click", async () => {
        const expr = document.getElementById("aljabr-input").value.trim();
        if (!expr) return showToast("Enter a root expression (e.g. HFZ)", "error");
        try {
            const res = await fetch("/api/harness/aljabr/execute", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ expression: expr }),
            });
            const data = await res.json();
            if (data.result) renderAlJabrResult(data.result, null, data.execution);
            if (data.success) {
                showToast("Al-Jabr: All commands executed", "success");
            } else if (data.partial) {
                showToast("Al-Jabr: Partial execution (some blocked)", "error");
            } else if (data.errors && data.errors.length) {
                showToast("Al-Jabr: " + data.errors[0], "error");
            } else {
                showToast("Al-Jabr: Execution blocked by safety pipeline", "error");
            }
            loadHarnessStatus();
        } catch(e) { showToast("Error: " + e.message, "error"); }
    });

    document.getElementById("aljabr-roots-btn")?.addEventListener("click", async () => {
        const panel = document.getElementById("aljabr-roots-panel");
        if (panel.style.display !== "none") {
            panel.style.display = "none";
            return;
        }
        try {
            const res = await fetch("/api/harness/aljabr/roots");
            const data = await res.json();
            renderAlJabrRoots(data);
            panel.style.display = "block";
        } catch(e) { showToast("Error loading roots", "error"); }
    });

    function renderAlJabrResult(result, dryRuns, execResults) {
        const narrativeEl = document.getElementById("aljabr-narrative");
        if (narrativeEl && result.narrative) {
            narrativeEl.textContent = result.narrative;
            narrativeEl.style.display = "block";
        }

        const resultEl = document.getElementById("aljabr-result");
        resultEl.style.display = "block";

        const comp = result.compression || {};
        document.getElementById("aljabr-compression").innerHTML =
            `<div class="ratio-value">${comp.ratio || 0}x</div>` +
            `<div class="ratio-label">COMPRESSION RATIO</div>` +
            `<div style="margin-top:6px; font-size:10px; color:#888;">` +
            `${comp.aljabr_chars || 0} chars \u2192 ${comp.python_chars || 0} chars<br>` +
            `${comp.root_count || 0} roots, ${comp.pattern_count || 0} patterns \u2192 ${comp.action_count || 0} actions</div>`;

        const cmdsEl = document.getElementById("aljabr-commands");
        cmdsEl.innerHTML = (result.commands || []).map(c =>
            `<div class="aljabr-cmd"><span class="cmd-root">${c.root}</span><span class="cmd-pat">.${c.pattern}</span> ${c.action_type} \u2192 ${c.narrative}</div>`
        ).join("") || '<div style="color:#666;">No commands generated</div>';

        const pyEl = document.getElementById("aljabr-python");
        pyEl.innerHTML = `<div class="py-label">Python Equivalent</div><pre>${comp.python_equivalent || "# no equivalent"}</pre>`;

        const drEl = document.getElementById("aljabr-dry-runs");
        if (dryRuns) {
            drEl.innerHTML = "<div style='color:#888;font-size:10px;margin-bottom:4px;'>SAFETY DRY-RUN</div>" +
                dryRuns.map(dr => {
                    const ok = dr.boundary_allowed && dr.checklist_verdict === "PASS";
                    return `<div class="aljabr-dry-run">` +
                        `<span class="dr-verdict ${ok ? 'dr-pass' : 'dr-fail'}">${ok ? 'SAFE' : 'BLOCKED'}</span>` +
                        `<span class="dr-root">${dr.root}.${dr.pattern}</span>` +
                        `<span>${dr.action.type}</span>` +
                        `<span style="color:#666;">${dr.checklist_verdict}</span>` +
                        `</div>`;
                }).join("");
        } else if (execResults) {
            drEl.innerHTML = "<div style='color:#888;font-size:10px;margin-bottom:4px;'>EXECUTION RESULTS</div>" +
                execResults.map(er => {
                    return `<div class="aljabr-dry-run">` +
                        `<span class="dr-verdict ${er.executed ? 'dr-pass' : 'dr-fail'}">${er.executed ? 'DONE' : 'BLOCKED'}</span>` +
                        `<span class="dr-root">${er.root}.${er.pattern}</span>` +
                        `<span>${er.action.type}</span>` +
                        `<span style="color:#888;font-size:10px;">${er.narrative}</span>` +
                        (er.blocked_by ? `<span style="color:#f87171;font-size:10px;">[${er.blocked_by}]</span>` : '') +
                        `</div>`;
                }).join("");
        } else {
            drEl.innerHTML = "";
        }
    }

    function renderAlJabrRoots(data) {
        const panel = document.getElementById("aljabr-roots-panel");
        const manifest = data.manifest || {};
        const patterns = data.patterns || {};

        let html = '<div class="aljabr-roots-header">ROOT MANIFEST</div>';
        html += '<div class="aljabr-patterns-row">';
        for (const [code, info] of Object.entries(patterns)) {
            html += `<span class="pat-tag" title="${info.verb}">${code} ${info.name}</span>`;
        }
        html += '</div>';

        const domainLabels = {aqua:"Aquaponics",flywheel:"Flywheel",silk:"Silk Wiring",pressure:"Pressure",system:"System"};
        for (const [domain, roots] of Object.entries(manifest)) {
            if (!roots.length) continue;
            html += `<div class="aljabr-domain-group"><div class="aljabr-domain-label">${domainLabels[domain] || domain}</div>`;
            for (const r of roots) {
                html += `<div class="aljabr-root-entry">` +
                    `<span class="root-code">${r.root}</span>` +
                    `<span class="root-essence">${r.essence}</span>` +
                    `<span class="root-desc">${r.description}</span>` +
                    `<span class="root-patterns">${(r.available_patterns||[]).join(" ")}</span>` +
                    `</div>`;
            }
            html += '</div>';
        }
        panel.innerHTML = html;
    }

    async function loadWalletStatus() {
        try {
            const res = await fetch("/api/harness/wallet/audit");
            const data = await res.json();
            document.getElementById("wallet-balance").textContent = data.balance.toFixed(2) + " CC";
            document.getElementById("wallet-earned").textContent = data.total_earned.toFixed(2);
            document.getElementById("wallet-spent").textContent = data.total_spent.toFixed(2);
            const net = data.net_flow;
            const netEl = document.getElementById("wallet-net");
            netEl.textContent = (net >= 0 ? "+" : "") + net.toFixed(2);
            netEl.className = "wallet-stat-value " + (net >= 0 ? "credit" : "debit");
            document.getElementById("wallet-denials").textContent = data.budget_denials;
            const frozenBadge = document.getElementById("wallet-frozen-badge");
            frozenBadge.style.display = data.frozen ? "block" : "none";
            const freezeBtn = document.getElementById("wallet-freeze-btn");
            freezeBtn.textContent = data.frozen ? "QSB.R Unfreeze" : "QSB.I Freeze";
            if (data.frozen) freezeBtn.classList.add("btn-active"); else freezeBtn.classList.remove("btn-active");
        } catch(e) {}
    }

    async function loadWalletLedger() {
        try {
            const res = await fetch("/api/harness/wallet/ledger?limit=15");
            const data = await res.json();
            const el = document.getElementById("wallet-ledger");
            if (!data.ledger || data.ledger.length === 0) {
                el.innerHTML = '<div style="color:#888;font-size:10px;padding:8px;">No transactions yet.</div>';
                return;
            }
            el.innerHTML = data.ledger.reverse().map(tx => {
                const isCredit = tx.tx_type === "credit" || tx.tx_type === "genesis";
                const amtClass = isCredit ? "positive" : (tx.amount > 0 ? "negative" : "");
                const amtStr = tx.amount > 0 ? (isCredit ? "+" : "-") + tx.amount.toFixed(2) : "---";
                return `<div class="wallet-tx-row">` +
                    `<span class="wallet-tx-type ${tx.tx_type}">${tx.tx_type}</span>` +
                    `<span class="wallet-tx-amount ${amtClass}">${amtStr}</span>` +
                    `<span class="wallet-tx-desc">${tx.description}</span>` +
                    `<span class="wallet-tx-balance">${tx.balance_after.toFixed(2)} CC</span>` +
                    (tx.root_command ? `<span style="color:#eab308;font-size:9px;">${tx.root_command}</span>` : '') +
                    `</div>`;
            }).join("");
        } catch(e) {}
    }

    loadWalletStatus();
    loadWalletLedger();

    document.getElementById("wallet-earn-btn")?.addEventListener("click", async () => {
        try {
            const res = await fetch("/api/harness/wallet/earn", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ source: "flywheel_excess", amount: 10.0 }),
            });
            const data = await res.json();
            if (data.earned) {
                showToast(`QSB.A Earned ${data.amount} CC from ${data.source}`, "success");
            } else {
                showToast(`QSB.A: ${data.reason}`, "error");
            }
            loadWalletStatus();
            loadWalletLedger();
        } catch(e) { showToast("Error: " + e.message, "error"); }
    });

    document.getElementById("wallet-spend-btn")?.addEventListener("click", async () => {
        try {
            const res = await fetch("/api/harness/wallet/spend", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ target: "ln2_refill" }),
            });
            const data = await res.json();
            if (data.spent) {
                showToast(`QSB.D Purchased ${data.target} for ${data.cost} CC`, "success");
            } else {
                showToast(`QSB.D: ${data.reason}`, "error");
            }
            loadWalletStatus();
            loadWalletLedger();
        } catch(e) { showToast("Error: " + e.message, "error"); }
    });

    document.getElementById("wallet-audit-btn")?.addEventListener("click", async () => {
        try {
            const res = await fetch("/api/harness/wallet/audit");
            const data = await res.json();
            showToast(`QSB.V Audit: ${data.balance} CC | Earned: ${data.total_earned} | Spent: ${data.total_spent} | Denials: ${data.budget_denials}`, "success");
            loadWalletStatus();
        } catch(e) { showToast("Error: " + e.message, "error"); }
    });

    document.getElementById("wallet-freeze-btn")?.addEventListener("click", async () => {
        try {
            const res = await fetch("/api/harness/wallet/freeze", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ action: "toggle" }),
            });
            const data = await res.json();
            showToast(data.frozen ? "QSB.I Wallet FROZEN — spending blocked" : "QSB.R Wallet UNFROZEN — spending resumed", data.frozen ? "error" : "success");
            loadWalletStatus();
            loadWalletLedger();
        } catch(e) { showToast("Error: " + e.message, "error"); }
    });

    document.getElementById("consensus-run-btn")?.addEventListener("click", async () => {
        const btn = document.getElementById("consensus-run-btn");
        btn.disabled = true;
        btn.textContent = "Negotiating...";
        try {
            const res = await fetch("/api/harness/consensus/run", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
            });
            const data = await res.json();
            if (data.error) {
                showToast("Consensus error: " + data.error, "error");
            } else {
                renderConsensusResult(data);
                showToast("Consensus: " + data.outcome, data.success ? "success" : "error");
            }
            loadHarnessStatus();
            loadWalletStatus();
            loadWalletLedger();
        } catch(e) { showToast("Error: " + e.message, "error"); }
        btn.disabled = false;
        btn.textContent = "Run Consensus";
    });

    document.getElementById("consensus-night-btn")?.addEventListener("click", async () => {
        try {
            const res = await fetch("/api/harness/consensus/night-cycle", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ action: "toggle", interval: 300 }),
            });
            const data = await res.json();
            const btn = document.getElementById("consensus-night-btn");
            if (data.status === "started") {
                btn.textContent = "Night Cycle: ON";
                btn.classList.add("btn-active");
                showToast("Night Cycle daemon started (5 min interval)", "success");
            } else {
                btn.textContent = "Night Cycle: OFF";
                btn.classList.remove("btn-active");
                showToast("Night Cycle daemon stopped", "success");
            }
        } catch(e) { showToast("Error: " + e.message, "error"); }
    });

    (async function loadConsensusStatus() {
        try {
            const res = await fetch("/api/harness/consensus/status");
            const data = await res.json();
            const nightBtn = document.getElementById("consensus-night-btn");
            if (data.night_cycle && data.night_cycle.active) {
                nightBtn.textContent = "Night Cycle: ON";
                nightBtn.classList.add("btn-active");
            }
            const label = document.getElementById("consensus-status-label");
            if (data.night_cycle) {
                label.textContent = `${data.night_cycle.total_consensus_runs} runs`;
            }
            if (data.history && data.history.length > 0) {
                renderConsensusResult(data.history[data.history.length - 1]);
            }
        } catch(e) {}
    })();

    function renderConsensusResult(data) {
        const wrap = document.getElementById("consensus-result");
        wrap.style.display = "block";

        const outcomeEl = document.getElementById("consensus-outcome");
        outcomeEl.innerHTML = `<span class="consensus-verdict ${data.success ? 'pass' : 'fail'}">${data.outcome}</span>` +
            `<span class="consensus-cmd">${data.consensus_command}</span>`;

        const statsEl = document.getElementById("consensus-stats");
        statsEl.innerHTML = [
            { label: "Energy", value: data.energy_pct + "%" },
            { label: "Turns", value: data.total_turns },
            { label: "Total Chars", value: data.total_chars },
            { label: "Intent", value: data.consensus_intent },
        ].map(s => `<div class="cs-stat"><span class="cs-label">${s.label}</span> <span class="cs-value">${s.value}</span></div>`).join("");

        const traceEl = document.getElementById("consensus-trace");
        traceEl.innerHTML = '<div class="trace-header"><span>#</span><span>Agent</span><span>Command</span><span>Intent</span></div>' +
            (data.trace || []).map(t =>
                `<div class="trace-row ${t.agent === 'Agent A' ? 'agent-a' : 'agent-b'}">` +
                `<span>${t.turn}</span>` +
                `<span><strong>${t.agent}</strong><br><span class="trace-role">${t.agent_role}</span></span>` +
                `<span class="trace-cmd">${t.command}</span>` +
                `<span class="trace-intent">${t.intent}</span>` +
                `</div>`
            ).join("");

        const finalEl = document.getElementById("consensus-final");
        finalEl.innerHTML = `<div class="consensus-final-label">CONSENSUS COMMAND</div>` +
            `<div class="consensus-final-cmd">${data.consensus_command}</div>` +
            `<div class="consensus-final-intent">${data.consensus_intent}</div>`;

        const execEl = document.getElementById("consensus-execution");
        if (data.execution_results && data.execution_results.length) {
            execEl.innerHTML = '<div style="color:#888;font-size:10px;margin-bottom:4px;">EXECUTION TRACE</div>' +
                data.execution_results.map(er =>
                    `<div class="consensus-exec-row">` +
                    `<span class="dr-verdict ${er.executed ? 'dr-pass' : 'dr-fail'}">${er.executed ? 'DONE' : 'BLOCKED'}</span>` +
                    `<span class="dr-root">${er.root || ''}.${er.pattern || ''}</span>` +
                    `<span>${er.narrative || ''}</span>` +
                    (er.blocked_by ? `<span style="color:#f87171;font-size:10px;">[${er.blocked_by}]</span>` : '') +
                    (er.wallet_result ? `<span style="color:#eab308;font-size:10px;">[${er.wallet_result.balance != null ? er.wallet_result.balance + ' CC' : ''}]</span>` : '') +
                    `</div>`
                ).join("");
        } else {
            execEl.innerHTML = "";
        }

        if (data.wallet) {
            const walletLine = document.createElement("div");
            walletLine.style.cssText = "margin-top:8px;padding:6px 10px;background:rgba(234,179,8,0.06);border:1px solid rgba(234,179,8,0.2);border-radius:4px;font-size:11px;font-family:monospace;color:#eab308;";
            walletLine.innerHTML = `WALLET: ${data.wallet.balance.toFixed(2)} CC | Earned: ${data.wallet.total_earned.toFixed(2)} | Spent: ${data.wallet.total_spent.toFixed(2)}${data.wallet.frozen ? ' | <span style="color:#f87171;">FROZEN</span>' : ''}`;
            execEl.appendChild(walletLine);
        }
    }

    function renderChaosReport(report) {
        const wrap = document.getElementById("chaos-test-result");
        if (!wrap) return;
        wrap.style.display = "block";

        const outcomeEl = document.getElementById("chaos-outcome");
        outcomeEl.textContent = report.outcome;
        outcomeEl.className = "harness-chaos-outcome " + (report.seal_survived ? "pass" : "fail");

        const statsEl = document.getElementById("chaos-stats");
        statsEl.innerHTML = [
            { label: "Test ID", value: report.test_id },
            { label: "Steps", value: report.completed_steps + "/" + report.total_steps },
            { label: "Max Pressure", value: report.max_pressure_reached + " atm" },
            { label: "Min Seal", value: report.min_seal_integrity + "%" },
            { label: "AC Activated Step", value: report.air_curtain_activated_at_step || "N/A" },
            { label: "Duration", value: (report.duration_seconds || 0) + "s" },
        ].map(s => `<div class="chaos-stat"><span class="stat-label">${s.label}</span><br><span class="stat-value">${s.value}</span></div>`).join("");

        const stepsEl = document.getElementById("chaos-steps-log");
        let html = '<div class="chaos-step-row header"><span>#</span><span>Boil</span><span>Press</span><span>Seal</span><span>AC</span><span>Chk</span><span>Response</span></div>';
        for (const s of report.steps) {
            const pClass = s.internal_pressure_atm >= 1.5 ? "step-danger" : s.internal_pressure_atm >= 1.3 ? "step-warn" : "step-ok";
            const sealClass = s.seal_integrity_pct <= 50 ? "step-danger" : s.seal_integrity_pct <= 80 ? "step-warn" : "step-ok";
            html += `<div class="chaos-step-row">` +
                `<span>${s.step}</span>` +
                `<span>${s.boil_rate.toFixed(3)}</span>` +
                `<span class="${pClass}">${s.internal_pressure_atm.toFixed(3)}</span>` +
                `<span class="${sealClass}">${s.seal_integrity_pct.toFixed(1)}%</span>` +
                `<span>${s.air_curtain_active ? s.air_curtain_velocity_ms.toFixed(0) + "m/s" : "OFF"}</span>` +
                `<span>${s.checklist_verdict}</span>` +
                `<span style="font-size:10px;">${s.auto_response}</span>` +
                `</div>`;
        }
        stepsEl.innerHTML = html;
    }

    document.getElementById("diagnostics-scan-btn").addEventListener("click", async () => {
        const label = document.getElementById("diagnostics-status-label");
        label.textContent = "Scanning...";
        try {
            const res = await fetch("/api/harness/diagnostics/scan", { method: "POST" });
            const data = await res.json();
            if (data.error) { label.textContent = "Error: " + data.error; return; }
            renderDiagnosticReport(data);
            label.textContent = "";
            document.getElementById("warranty-panel").style.display = "none";
        } catch (e) {
            label.textContent = "Scan failed";
        }
    });

    function renderDiagnosticReport(data) {
        const wrap = document.getElementById("diagnostics-result");
        wrap.style.display = "block";

        const overallEl = document.getElementById("diagnostics-overall");
        overallEl.className = "diagnostics-overall status-" + data.overall_status;
        overallEl.textContent = data.overall_status;

        document.getElementById("diagnostics-summary").textContent = data.summary;

        const countsEl = document.getElementById("diagnostics-counts");
        countsEl.innerHTML =
            `<span class="dc-crit">${data.critical_count} CRITICAL</span>` +
            `<span class="dc-warn">${data.warning_count} WARNING</span>` +
            `<span class="dc-nom">${data.nominal_count} NOMINAL</span>`;

        const findingsEl = document.getElementById("diagnostics-findings");
        const sortOrder = { "CRITICAL": 0, "WARNING": 1, "NOMINAL": 2 };
        const sorted = [...data.findings].sort((a, b) => sortOrder[a.severity] - sortOrder[b.severity]);

        findingsEl.innerHTML = sorted.map(f => {
            const meterPct = f.threshold > 0 ? Math.min((f.value / f.threshold) * 100, 100) : (f.severity === "NOMINAL" ? 30 : 80);
            return `<div class="diag-card sev-${f.severity}">` +
                `<div class="diag-card-header">` +
                `<div class="diag-glyph">${f.glyph}</div>` +
                `<span class="diag-root-code">${f.root_code}</span>` +
                `<span class="diag-severity">${f.severity}</span>` +
                `</div>` +
                `<div class="diag-semantic">${f.semantic_error}</div>` +
                `<div class="diag-physical">${f.physical_reality}</div>` +
                (f.solution_command ? `<div class="diag-solution"><span class="diag-solution-cmd">${f.solution_command}</span>${f.solution_text}</div>` : `<div class="diag-solution">${f.solution_text}</div>`) +
                (f.threshold > 0 ? `<div class="diag-meter"><div class="diag-meter-fill" style="width:${meterPct}%"></div></div>` : '') +
                `</div>`;
        }).join("");
    }

    document.getElementById("warranty-btn").addEventListener("click", async () => {
        const panel = document.getElementById("warranty-panel");
        if (panel.style.display !== "none") {
            panel.style.display = "none";
            return;
        }
        document.getElementById("diagnostics-result").style.display = "none";
        try {
            const res = await fetch("/api/harness/warranty");
            const data = await res.json();
            renderWarranty(data);
            panel.style.display = "block";
        } catch (e) {
            document.getElementById("diagnostics-status-label").textContent = "Failed to load warranty";
        }
    });

    function renderWarranty(data) {
        const el = document.getElementById("warranty-content");
        let html = `<div class="warranty-title">${data.title}</div>`;
        html += `<div class="warranty-subtitle">${data.subtitle}</div>`;
        html += `<div class="warranty-preamble">${data.preamble}</div>`;

        for (const article of data.articles) {
            html += `<div class="warranty-article">` +
                `<div class="warranty-article-header">` +
                `<div class="warranty-article-num">${article.number}</div>` +
                `<div class="warranty-article-title">${article.title}</div>` +
                `</div>` +
                `<div class="warranty-article-text">${article.text}</div>` +
                `</div>`;
        }

        html += `<div class="warranty-closing">` +
            `<div class="warranty-closing-text">${data.closing}</div>` +
            `<div class="warranty-seal">${data.seal}</div>` +
            `</div>`;

        el.innerHTML = html;
    }
});
