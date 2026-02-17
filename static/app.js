document.addEventListener("DOMContentLoaded", () => {
    const tabs = document.querySelectorAll(".tab");
    const panels = document.querySelectorAll(".panel");

    tabs.forEach(tab => {
        tab.addEventListener("click", () => {
            tabs.forEach(t => t.classList.remove("active"));
            panels.forEach(p => p.classList.remove("active"));
            tab.classList.add("active");
            document.getElementById(tab.dataset.tab).classList.add("active");
            if (tab.dataset.tab === "files") refreshFiles();
            if (tab.dataset.tab === "capacity") loadSelects();
            if (tab.dataset.tab === "visualizer") loadSelects();
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
                body: JSON.stringify({ carrier, payload, lsb_depth: parseInt(lsb) }),
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
                showToast("Encoding complete!", "success");
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

        function draw() {
            vizAnimFrame = requestAnimationFrame(draw);
            vizAnalyser.getByteFrequencyData(dataArr);

            canvas.width = canvas.clientWidth * (window.devicePixelRatio || 1);
            canvas.height = canvas.clientHeight * (window.devicePixelRatio || 1);
            ctx.scale(window.devicePixelRatio || 1, window.devicePixelRatio || 1);

            const w = canvas.clientWidth;
            const h = canvas.clientHeight;

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
                document.getElementById("cap-safe-1").textContent = formatSize(d.resonance_limit_1bit);
                document.getElementById("cap-est-1").textContent = "~" + formatSize(d.resonance_limit_1bit * 3) + " - " + formatSize(d.resonance_limit_1bit * 5);
                document.getElementById("cap-bar-1-max").style.width = (d.capacity_1bit / maxRef * 100) + "%";
                document.getElementById("cap-bar-1-safe").style.width = (d.resonance_limit_1bit / maxRef * 100) + "%";
                document.getElementById("cap-bar-1-est").style.width = (d.resonance_limit_1bit * 4 / maxRef * 100) + "%";

                document.getElementById("cap-max-2").textContent = formatSize(d.capacity_2bit);
                document.getElementById("cap-safe-2").textContent = formatSize(d.resonance_limit_2bit);
                document.getElementById("cap-est-2").textContent = "~" + formatSize(d.resonance_limit_2bit * 3) + " - " + formatSize(d.resonance_limit_2bit * 5);
                document.getElementById("cap-bar-2-max").style.width = "100%";
                document.getElementById("cap-bar-2-safe").style.width = (d.resonance_limit_2bit / maxRef * 100) + "%";
                document.getElementById("cap-bar-2-est").style.width = (d.resonance_limit_2bit * 4 / maxRef * 100) + "%";

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

    loadSelects();
});
