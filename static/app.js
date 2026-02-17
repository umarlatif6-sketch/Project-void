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
