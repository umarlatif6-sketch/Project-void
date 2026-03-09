function escHtml(str) {
    var d = document.createElement('div');
    d.appendChild(document.createTextNode(str));
    return d.innerHTML;
}

function buildSelectOptions(files, emptyLabel, suffixFn) {
    const frag = document.createDocumentFragment();
    if (!files.length) {
        const opt = document.createElement('option');
        opt.value = '';
        opt.textContent = emptyLabel;
        frag.appendChild(opt);
    } else {
        files.forEach(function(f) {
            const opt = document.createElement('option');
            opt.value = f.name;
            opt.textContent = f.name + ' (' + formatSize(f.size) + ')' + (suffixFn ? suffixFn(f) : '');
            frag.appendChild(opt);
        });
    }
    return frag;
}

document.addEventListener("DOMContentLoaded", () => {
    const isDemo = document.body.getAttribute("data-demo") === "true";
    const tabs = document.querySelectorAll(".tab");
    const panels = document.querySelectorAll(".panel");

    if (isDemo) {
        var restrictedTabs = ["harness", "mesh", "transceiver", "silk"];
        tabs.forEach(function(tab) {
            if (restrictedTabs.indexOf(tab.dataset.tab) !== -1) {
                tab.style.opacity = "0.35";
                tab.style.pointerEvents = "none";
                tab.title = "Full Version Only";
            }
        });
        var journalismTab = null;
        tabs.forEach(function(t) { if (t.dataset.tab === "journalism") journalismTab = t; });
        if (journalismTab) {
            tabs.forEach(function(t) { t.classList.remove("active"); });
            panels.forEach(function(p) { p.classList.remove("active"); });
            journalismTab.classList.add("active");
            var jp = document.getElementById("journalism");
            if (jp) jp.classList.add("active");
        }
    }

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
            if (tab.dataset.tab === "transceiver") refreshTransceiverStatus();
            if (tab.dataset.tab === "journalism") loadSiltDrops();
        });
    });

    function formatSize(bytes) {
        if (bytes >= 1073741824) return (bytes / 1073741824).toFixed(2) + " GB";
        if (bytes >= 1048576) return (bytes / 1048576).toFixed(1) + " MB";
        if (bytes >= 1024) return (bytes / 1024).toFixed(1) + " KB";
        return bytes.toLocaleString() + " B";
    }

    var _isFounder = document.body.dataset.founderVibe === "true";
    var _resonanceFields = {};

    function _getResonanceField(panelId) {
        if (typeof ResonanceField === 'undefined') return null;
        if (_resonanceFields[panelId]) return _resonanceFields[panelId];
        var el = document.getElementById(panelId);
        if (!el) return null;
        var rf = new ResonanceField(el, { founder: _isFounder });
        _resonanceFields[panelId] = rf;
        return rf;
    }

    function _activateResonance(panelId, hash, phase) {
        var rf = _getResonanceField(panelId);
        if (rf) rf.activate(hash || '', phase || 'encoding');
    }

    function _pulseResonance(panelId, hash) {
        var rf = _getResonanceField(panelId);
        if (rf) rf.pulseHash(hash || '');
    }

    function _deactivateResonance(panelId, delay) {
        var rf = _resonanceFields[panelId];
        if (!rf) return;
        if (delay) {
            setTimeout(function() { rf.deactivate(); }, delay);
        } else {
            rf.deactivate();
        }
    }

    function _renderResonanceBadge(badgeId, hashKey) {
        var badge = document.getElementById(badgeId);
        if (!badge || !hashKey) return;
        fetch('/api/resonance/field?hash=' + encodeURIComponent(hashKey))
            .then(function(r) { return r.json(); })
            .then(function(data) {
                if (!data.glyph) return;
                var glyphSpan = document.createElement('span');
                glyphSpan.className = 'resonance-badge-glyph';
                glyphSpan.style.color = data.color || '#2dd4bf';
                glyphSpan.textContent = data.glyph;

                var domainDiv = document.createElement('div');
                domainDiv.className = 'resonance-badge-domain';
                domainDiv.textContent = data.domain || 'unknown';

                var freqDiv = document.createElement('div');
                freqDiv.className = 'resonance-badge-freq';
                freqDiv.textContent = (data.frequency || 432).toFixed(1) + ' Hz';

                var strengthFill = document.createElement('div');
                strengthFill.className = 'resonance-badge-strength-fill';
                strengthFill.style.width = Math.round((data.field_strength || 0) * 100) + '%';

                var strengthDiv = document.createElement('div');
                strengthDiv.className = 'resonance-badge-strength';
                strengthDiv.appendChild(strengthFill);

                var infoDiv = document.createElement('div');
                infoDiv.className = 'resonance-badge-info';
                infoDiv.appendChild(domainDiv);
                infoDiv.appendChild(freqDiv);
                infoDiv.appendChild(strengthDiv);

                badge.textContent = '';
                badge.appendChild(glyphSpan);
                badge.appendChild(infoDiv);
                badge.classList.add('active');
            })
            .catch(function() {});
    }

    function showToast(msg, type, duration) {
        const toast = document.getElementById("toast");
        toast.textContent = msg;
        toast.className = "toast show " + (type || "");
        clearTimeout(toast._timeout);
        const dur = duration || (type === "error" ? 8000 : 4000);
        toast._timeout = setTimeout(() => toast.className = "toast", dur);
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
        carrier.replaceChildren(buildSelectOptions(wavFiles, 'No WAV files in input_files/'));

        payload.replaceChildren(buildSelectOptions(data.input, 'No files in input_files/', function(f) {
            return f.name.toLowerCase().endsWith(".wav") ? " [WAV AUDIO]" : "";
        }));

        updateStegoSelect(data);
        updateCapSelect(data);
        updateVizSelect(data);
        checkEncodeFit(data);
    }

    let _lastFileData = null;
    function checkEncodeFit(fileData) {
        if (fileData) _lastFileData = fileData;
        if (!_lastFileData) return;
        const fitEl = document.getElementById("encode-fit-check");
        const carrier = document.getElementById("carrier-select").value;
        const payloadName = document.getElementById("payload-select").value;
        const lsb = parseInt(document.querySelector('input[name="lsb-encode"]:checked').value);

        if (!carrier || !payloadName) { fitEl.style.display = "none"; return; }

        const carrierFile = _lastFileData.input.find(f => f.name === carrier);
        const payloadFile = _lastFileData.input.find(f => f.name === payloadName);
        if (!carrierFile || !payloadFile) { fitEl.style.display = "none"; return; }

        const carrierSamples = Math.floor((carrierFile.size - 44) / 2);
        const ghostOffset = Math.floor(carrierSamples * 0.02);
        const usableSamples = carrierSamples - ghostOffset;
        const capacityBits = usableSamples * lsb;
        const headerBytes = 64;
        const capacityBytes = Math.max(0, Math.floor(capacityBits / 8) - headerBytes);
        const payloadBytes = payloadFile.size;

        function _setFitMessage(el, iconChar, message) {
            const icon = document.createElement('span');
            icon.className = 'fit-icon';
            icon.textContent = iconChar;
            el.replaceChildren(icon, document.createTextNode(' ' + message));
        }
        if (capacityBytes === 0) {
            fitEl.className = "fit-check fit-fail";
            _setFitMessage(fitEl, '\u2716', 'Carrier too small \u2014 no usable capacity for data embedding.');
        } else if (payloadBytes <= capacityBytes * 0.5) {
            fitEl.className = "fit-check fit-ok";
            _setFitMessage(fitEl, '\u25cf', 'Payload fits comfortably \u2014 ' + formatSize(payloadBytes) + ' payload vs ' + formatSize(capacityBytes) + ' capacity at LSB ' + lsb + ' (compression will reduce further)');
        } else if (payloadBytes <= capacityBytes) {
            fitEl.className = "fit-check fit-warn";
            _setFitMessage(fitEl, '\u26a0', 'Tight fit \u2014 ' + formatSize(payloadBytes) + ' payload vs ' + formatSize(capacityBytes) + ' capacity at LSB ' + lsb + '. May work if compression is effective.');
        } else {
            fitEl.className = "fit-check fit-fail";
            _setFitMessage(fitEl, '\u2716', 'Payload too large \u2014 ' + formatSize(payloadBytes) + ' payload exceeds ' + formatSize(capacityBytes) + ' capacity at LSB ' + lsb + '. Use a longer carrier WAV or switch to LSB Depth 2.');
        }
        fitEl.style.display = "block";
    }

    const genToggle = document.getElementById("gen-carrier-toggle");
    const genBody = document.getElementById("gen-carrier-body");
    if (genToggle && genBody) {
        genToggle.addEventListener("click", () => {
            const open = genBody.style.display !== "none";
            genBody.style.display = open ? "none" : "block";
            genToggle.querySelector(".toggle-icon").textContent = open ? "\u25B6" : "\u25BC";
            if (!open) updateEstimate();
        });
    }

    document.querySelectorAll(".preset-btn[data-dur]").forEach(btn => {
        btn.addEventListener("click", () => {
            document.querySelectorAll(".preset-btn[data-dur]").forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            document.getElementById("gen-duration").value = btn.dataset.dur;
            updateEstimate();
        });
    });

    const genDuration = document.getElementById("gen-duration");
    const genStyle = document.getElementById("gen-style");
    if (genDuration) genDuration.addEventListener("change", updateEstimate);
    if (genStyle) genStyle.addEventListener("change", updateEstimate);

    async function updateEstimate() {
        const dur = parseFloat(document.getElementById("gen-duration").value) || 1;
        const style = document.getElementById("gen-style").value;
        const panel = document.getElementById("gen-estimate");
        try {
            const res = await fetch(`/api/carrier-estimate?duration=${encodeURIComponent(dur)}&style=${encodeURIComponent(style)}`);
            const d = await res.json();
            if (!d.success) return;
            panel.style.display = "block";
            var existingErr = document.getElementById("est-error");
            if (existingErr) existingErr.style.display = "none";
            document.getElementById("est-wav-size").textContent = formatSize(d.wav_size);
            document.getElementById("est-lsb1").textContent = formatSize(d.raw_lsb1);
            document.getElementById("est-lsb2").textContent = formatSize(d.raw_lsb2);
            document.getElementById("est-effective").textContent = formatSize(d.effective_lsb2);

            const badge = document.getElementById("est-density-badge");
            if (d.density_multiplier > 1) {
                badge.textContent = d.density_multiplier + "x DENSITY";
                badge.style.display = "inline-block";
            } else {
                badge.style.display = "none";
            }

            const shelfEl = document.getElementById("est-shelf-info");
            if (d.shelf_breakdown) {
                const sb = d.shelf_breakdown;
                shelfEl.innerHTML = '<strong>Shelf Breakdown:</strong><br>' +
                    'Whales: heavy data blocks | Birds: parity headers | Insects: compressed silt';
                shelfEl.style.display = "block";
            } else {
                shelfEl.style.display = "none";
            }
        } catch(e) {
            var errMsg = document.getElementById("est-error");
            if (!errMsg) {
                errMsg = document.createElement("div");
                errMsg.id = "est-error";
                errMsg.style.color = "var(--error, #ff6b6b)";
                errMsg.style.marginTop = "0.5rem";
                panel.appendChild(errMsg);
            }
            errMsg.textContent = "Failed to load carrier estimate.";
            errMsg.style.display = "block";
        }
    }

    const genBtn = document.getElementById("gen-carrier-btn");
    if (genBtn) {
        genBtn.addEventListener("click", async () => {
            const dur = parseFloat(document.getElementById("gen-duration").value) || 1;
            const style = document.getElementById("gen-style").value;
            const statusEl = document.getElementById("gen-carrier-status");

            genBtn.disabled = true;
            genBtn.innerHTML = '<span class="spinner"></span>Generating...';
            statusEl.style.display = "block";
            statusEl.className = "gen-status";
            statusEl.textContent = "Synthesizing " + style + " carrier (" + dur + " min)...";

            try {
                const res = await fetch("/api/generate-carrier", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ duration_minutes: dur, style }),
                });
                const data = await res.json();
                if (data.success) {
                    statusEl.className = "gen-status gen-success";
                    statusEl.textContent = '';
                    const _genPrefix = document.createTextNode('Generated: ');
                    const _genStrong = document.createElement('strong');
                    _genStrong.textContent = data.filename;
                    const _genSuffix = document.createTextNode(
                        ' (' + formatSize(data.file_size) + ')' +
                        (data.chirp_count ? ' | ' + data.chirp_count.toLocaleString() + ' chirp peaks' : '')
                    );
                    statusEl.appendChild(_genPrefix);
                    statusEl.appendChild(_genStrong);
                    statusEl.appendChild(_genSuffix);
                    showToast("Carrier generated: " + data.filename, "success");
                    await loadSelects();
                    const carrierSel = document.getElementById("carrier-select");
                    for (let i = 0; i < carrierSel.options.length; i++) {
                        if (carrierSel.options[i].value === data.filename) {
                            carrierSel.selectedIndex = i;
                            break;
                        }
                    }
                } else {
                    statusEl.className = "gen-status gen-error";
                    statusEl.textContent = data.error || "Generation failed";
                    showToast(data.error || "Generation failed", "error");
                }
            } catch(e) {
                statusEl.className = "gen-status gen-error";
                statusEl.textContent = "Request failed: " + e.message;
            } finally {
                genBtn.disabled = false;
                genBtn.innerHTML = "Generate Carrier";
            }
        });
    }

    function updateStegoSelect(data) {
        const stego = document.getElementById("stego-select");
        const source = document.querySelector('input[name="decode-source"]:checked').value;
        const files = source === "output" ? data.output : data.input;
        const wavFiles = files.filter(f => f.name.toLowerCase().endsWith(".wav"));
        stego.replaceChildren(buildSelectOptions(wavFiles, 'No WAV files found'));
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
        sel.replaceChildren(buildSelectOptions(wavFiles, 'No WAV files found'));
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
        el.innerHTML = '';
        files.forEach(f => {
            const row = document.createElement('div');
            row.className = 'file-row';
            const info = document.createElement('div');
            info.className = 'file-info';
            const nameSpan = document.createElement('span');
            nameSpan.className = 'file-name';
            nameSpan.textContent = f.name;
            const sizeSpan = document.createElement('span');
            sizeSpan.className = 'file-size';
            sizeSpan.textContent = formatSize(f.size);
            info.appendChild(nameSpan);
            info.appendChild(sizeSpan);
            const actions = document.createElement('div');
            actions.className = 'file-actions';
            const dlBtn = document.createElement('button');
            dlBtn.className = 'btn-sm';
            dlBtn.textContent = 'Download';
            dlBtn.addEventListener('click', () => downloadFile(folder, f.name));
            const delBtn = document.createElement('button');
            delBtn.className = 'btn-sm delete';
            delBtn.textContent = 'Delete';
            delBtn.addEventListener('click', () => deleteFile(folder, f.name));
            actions.appendChild(dlBtn);
            actions.appendChild(delBtn);
            row.appendChild(info);
            row.appendChild(actions);
            el.appendChild(row);
        });
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

    function setUploadItemSpans(item, nameText, statusText, statusColor) {
        item.textContent = "";
        const nameSpan = document.createElement("span");
        nameSpan.textContent = nameText;
        const statusSpan = document.createElement("span");
        statusSpan.textContent = statusText;
        if (statusColor) statusSpan.style.color = statusColor;
        item.appendChild(nameSpan);
        item.appendChild(statusSpan);
    }

    async function uploadFiles(fileList, statusEl, dest) {
        statusEl.textContent = "";
        for (const file of fileList) {
            const item = document.createElement("div");
            item.className = "upload-item";
            setUploadItemSpans(item, file.name, "Uploading...");
            statusEl.appendChild(item);

            const fd = new FormData();
            fd.append("file", file);
            fd.append("dest", dest);

            try {
                const res = await fetch("/api/upload", { method: "POST", body: fd });
                const data = await res.json();
                if (data.success) {
                    setUploadItemSpans(item, data.filename, formatSize(data.size), "var(--success)");
                    showToast(`Uploaded ${escHtml(data.filename)}`, "success");
                } else {
                    setUploadItemSpans(item, file.name, data.error, "var(--error)");
                }
            } catch {
                setUploadItemSpans(item, file.name, "Upload failed", "var(--error)");
            }
        }
        loadSelects();
    }

    setupUpload("upload-zone-encode", "file-upload-encode", "upload-status-encode", "input");
    setupUpload("upload-zone-decode", "file-upload-decode", "upload-status-decode", "output");

    let lastEncodedFile = null;
    let lastDecodedFile = null;

    document.getElementById("carrier-select").addEventListener("change", () => checkEncodeFit());
    document.getElementById("payload-select").addEventListener("change", () => checkEncodeFit());
    document.querySelectorAll('input[name="lsb-encode"]').forEach(r => r.addEventListener("change", () => checkEncodeFit()));

    function showInlineError(elementId, message) {
        const el = document.getElementById(elementId);
        el.innerHTML = '';
        const title = document.createElement('div');
        title.className = 'error-title';
        title.textContent = 'Error';
        el.appendChild(title);
        el.appendChild(document.createTextNode(message));
        el.style.display = "block";
    }

    document.getElementById("encode-btn").addEventListener("click", async () => {
        const carrier = document.getElementById("carrier-select").value;
        const payload = document.getElementById("payload-select").value;
        const lsb = document.querySelector('input[name="lsb-encode"]:checked').value;
        const scatterMode = document.querySelector('input[name="scatter-mode"]:checked').value;
        const jitter = scatterMode === "jitter";
        const vortex = scatterMode === "vortex";
        const chirp_sync = scatterMode === "chirp_sync";
        const btn = document.getElementById("encode-btn");

        if (!carrier || !payload) {
            showToast("Select both a carrier WAV and a file to hide", "error");
            return;
        }

        btn.disabled = true;
        btn.innerHTML = '<span class="spinner"></span>Encoding...';
        document.getElementById("encode-result").style.display = "none";
        document.getElementById("encode-error").style.display = "none";
        _activateResonance('encode', '', 'encoding');

        try {
            const res = await fetch("/api/encode", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ carrier, payload, lsb_depth: parseInt(lsb), jitter, vortex, chirp_sync }),
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
                _pulseResonance('encode', data.hash_key);
                _renderResonanceBadge('encode-resonance-badge', data.hash_key);
                _deactivateResonance('encode', 2500);
                loadSelects();
            } else {
                showInlineError("encode-error", data.error || "Unknown encoding error");
                showToast("Encoding failed — see details below", "error");
                _deactivateResonance('encode');
            }
        } catch (e) {
            showInlineError("encode-error", "Encoding failed: " + e.message);
            showToast("Encoding failed — see details below", "error");
            _deactivateResonance('encode');
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
        document.getElementById("decode-error").style.display = "none";
        _activateResonance('decode', hashKey, 'decoding');

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
                _pulseResonance('decode', hashKey);
                _deactivateResonance('decode', 2500);
                loadSelects();
            } else {
                showInlineError("decode-error", data.error || "Unknown decoding error");
                showToast("Decoding failed — see details below", "error");
                _deactivateResonance('decode');
            }
        } catch (e) {
            showInlineError("decode-error", "Decoding failed: " + e.message);
            showToast("Decoding failed — see details below", "error");
            _deactivateResonance('decode');
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
        sel.replaceChildren(buildSelectOptions(wavFiles, 'No WAV files found'));
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
        _activateResonance('burst', '', 'encoding');

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
                _pulseResonance('burst', data.hash_key);
                _renderResonanceBadge('burst-resonance-badge', data.hash_key);
                _deactivateResonance('burst', 2500);
                loadSelects();
            } else {
                showToast(data.error, "error");
                _deactivateResonance('burst');
            }
        } catch (e) {
            showToast("Burst encoding failed: " + e.message, "error");
            _deactivateResonance('burst');
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
    let vizResonanceMode = false;
    let spectrogramImageData = null;
    let pocketPhase = 0;
    var vizResonanceParticles = [];

    function updateVizLegends() {
        const legendNormal = document.getElementById("viz-legend");
        const legendSpec = document.getElementById("viz-legend-spectrogram");
        const legendPocket = document.getElementById("viz-legend-pocket");
        const legendResonance = document.getElementById("viz-legend-resonance");
        legendNormal.style.display = "none";
        legendSpec.style.display = "none";
        legendPocket.style.display = "none";
        if (legendResonance) legendResonance.style.display = "none";
        if (vizResonanceMode) {
            if (legendResonance) legendResonance.style.display = "flex";
        } else if (vizPocketMode) {
            legendPocket.style.display = "flex";
        } else if (vizSpectrogramMode) {
            legendSpec.style.display = "flex";
        } else {
            legendNormal.style.display = "flex";
        }
    }

    function _clearVizModes(except) {
        if (except !== 'spectrogram') { vizSpectrogramMode = false; document.getElementById("viz-spectrogram-toggle").checked = false; }
        if (except !== 'pocket') { vizPocketMode = false; document.getElementById("viz-pocket-toggle").checked = false; }
        if (except !== 'resonance') { vizResonanceMode = false; var rt = document.getElementById("viz-resonance-toggle"); if (rt) rt.checked = false; }
    }

    document.getElementById("viz-spectrogram-toggle").addEventListener("change", (e) => {
        vizSpectrogramMode = e.target.checked;
        spectrogramImageData = null;
        if (vizSpectrogramMode) _clearVizModes('spectrogram');
        updateVizLegends();
    });

    document.getElementById("viz-pocket-toggle").addEventListener("change", (e) => {
        vizPocketMode = e.target.checked;
        pocketPhase = 0;
        if (vizPocketMode) _clearVizModes('pocket');
        updateVizLegends();
    });

    var vizResToggle = document.getElementById("viz-resonance-toggle");
    if (vizResToggle) {
        vizResToggle.addEventListener("change", function(e) {
            vizResonanceMode = e.target.checked;
            vizResonanceParticles = [];
            if (vizResonanceMode) _clearVizModes('resonance');
            updateVizLegends();
        });
    }

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

            if (vizResonanceMode) {
                drawResonanceViz(ctx, cw, ch, dataArr, maxBin, bin432, binWidth);
            } else if (vizPocketMode) {
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

        function drawResonanceViz(ctx, w, h, dataArr, maxBin, bin432, binWidth) {
            ctx.fillStyle = "rgba(10, 10, 15, 0.15)";
            ctx.fillRect(0, 0, w, h);

            var peakVal = 0, peakBin = 0;
            for (var i = 0; i < maxBin; i++) {
                if (dataArr[i] > peakVal) { peakVal = dataArr[i]; peakBin = i; }
            }
            var peakFreq = peakBin * binWidth;
            var energy = peakVal / 255;

            var vizGlyphs = [
                {g:"\u03b1",f:432.0,c:"#c9a84c"},{g:"\u03b2",f:433.2,c:"#2dd4bf"},{g:"\u03b3",f:434.0,c:"#60a5fa"},
                {g:"\u03b4",f:434.8,c:"#a78bfa"},{g:"\u03b5",f:435.5,c:"#f87171"},{g:"\u03b6",f:429.0,c:"#92400e"},
                {g:"\u03b7",f:430.5,c:"#2dd4bf"},{g:"\u03b8",f:431.0,c:"#fb923c"},{g:"\u03b9",f:432.5,c:"#34d399"},
                {g:"\u03ba",f:433.7,c:"#f472b6"},{g:"\u03bb",f:436.0,c:"#60a5fa"},{g:"\u03bc",f:432.8,c:"#a3e635"},
                {g:"\u03c0",f:432.0,c:"#e879f9"},{g:"\u03c3",f:435.1,c:"#c9a84c"},{g:"\u03c9",f:428.5,c:"#ef4444"},
                {g:"\u0394",f:434.8,c:"#a78bfa"},{g:"\u03a3",f:435.1,c:"#c9a84c"},{g:"\u03a9",f:428.0,c:"#ef4444"},
                {g:"\u221e",f:432.0,c:"#fbbf24"},{g:"\u25c6",f:432.0,c:"#c9a84c"}
            ];

            if (energy > 0.05) {
                var bestGlyph = vizGlyphs[0];
                var bestDist = 9999;
                for (var gi = 0; gi < vizGlyphs.length; gi++) {
                    var dist = Math.abs(vizGlyphs[gi].f - peakFreq);
                    if (dist < bestDist) { bestDist = dist; bestGlyph = vizGlyphs[gi]; }
                }
                var count = Math.floor(energy * (_isFounder ? 6 : 3));
                for (var ci = 0; ci < count; ci++) {
                    vizResonanceParticles.push({
                        x: Math.random() * w,
                        y: h + 10,
                        vx: (Math.random() - 0.5) * 2,
                        vy: -(1 + Math.random() * 2 * energy),
                        glyph: bestGlyph.g,
                        color: _isFounder ? '#c9a84c' : bestGlyph.c,
                        alpha: 0.5 + energy * 0.5,
                        size: 14 + energy * 16,
                        life: 80 + Math.floor(Math.random() * 60),
                        pulse: Math.random() * Math.PI * 2
                    });
                }
            }

            var alive = [];
            for (var pi = 0; pi < vizResonanceParticles.length; pi++) {
                var p = vizResonanceParticles[pi];
                p.x += p.vx;
                p.y += p.vy;
                p.life--;
                p.pulse += 0.06;
                var fade = Math.min(1, p.life / 20);
                var pf = 1 + Math.sin(p.pulse) * 0.12;
                ctx.save();
                ctx.globalAlpha = p.alpha * fade;
                ctx.font = Math.round(p.size * pf) + 'px sans-serif';
                ctx.fillStyle = p.color;
                ctx.shadowColor = p.color;
                ctx.shadowBlur = _isFounder ? 18 : 8;
                ctx.textAlign = 'center';
                ctx.fillText(p.glyph, p.x, p.y);
                ctx.restore();
                if (p.life > 0 && p.y > -20) alive.push(p);
            }
            vizResonanceParticles = alive;

            ctx.fillStyle = _isFounder ? '#c9a84c' : '#2dd4bf';
            ctx.font = '11px monospace';
            ctx.textAlign = 'left';
            ctx.fillText('Resonance: ' + peakFreq.toFixed(0) + ' Hz  |  ' + vizResonanceParticles.length + ' glyphs', 10, 18);

            document.getElementById("viz-peak-freq").textContent = 'Dominant: ' + peakFreq.toFixed(0) + ' Hz';
            document.getElementById("viz-432-level").textContent = '432 Hz: ' + (dataArr[bin432] || 0) + '/255';
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
                var capHash = (d.filename || '') + d.capacity_1bit + d.capacity_2bit;
                var capHashHex = '';
                for (var ci = 0; ci < capHash.length; ci++) capHashHex += capHash.charCodeAt(ci).toString(16);
                _renderResonanceBadge('cap-resonance-badge', capHashHex.substring(0, 64));
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
        _activateResonance('silk', '', 'encoding');

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

                _pulseResonance('silk', data.hash_key);
                _renderResonanceBadge('silk-resonance-badge', data.hash_key);
                _deactivateResonance('silk', 2500);
                loadSilkFeed();
                loadSelects();
            } else {
                showToast(data.error, "error");
                _deactivateResonance('silk');
            }
        } catch (e) {
            showToast("Signal failed: " + e.message, "error");
            _deactivateResonance('silk');
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

            feed.innerHTML = "";
            data.signals.forEach(s => {
                const entry = document.createElement("div");
                entry.className = "silk-entry";

                const left = document.createElement("div");
                left.className = "silk-entry-left";

                const signalText = document.createElement("span");
                signalText.className = "silk-signal-text";
                signalText.textContent = s.signal;

                const meta = document.createElement("span");
                meta.className = "silk-entry-meta";
                meta.textContent = `${s.timestamp} \u00b7 ${s.output_file}`;

                left.appendChild(signalText);
                left.appendChild(meta);

                const right = document.createElement("div");
                right.className = "silk-entry-right";

                const status = document.createElement("span");
                status.className = "silk-status";
                status.textContent = s.status;

                const hashTail = document.createElement("span");
                hashTail.className = "silk-hash-tail";
                hashTail.textContent = s.hash_tail;

                right.appendChild(status);
                right.appendChild(hashTail);

                entry.appendChild(left);
                entry.appendChild(right);
                feed.appendChild(entry);
            });
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
            const labelSpan = document.createElement("span");
            labelSpan.className = "sensor-label";
            labelSpan.textContent = label;
            const valueSpan = document.createElement("span");
            valueSpan.className = "sensor-value";
            valueSpan.textContent = String(val);
            item.appendChild(labelSpan);
            item.appendChild(valueSpan);
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
            const icon = document.createElement("div");
            icon.className = "harness-check-icon " + check.verdict.toLowerCase().replace(/[^a-z0-9_-]/g, "");
            icon.textContent = icons[check.verdict] || "?";
            const msg = document.createElement("span");
            msg.className = "harness-check-msg";
            msg.textContent = check.message;
            row.appendChild(icon);
            row.appendChild(msg);
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
                const makeStatSpan = (val) => {
                    const span = document.createElement("span");
                    span.className = "harness-loop-stat";
                    span.textContent = String(Number(val));
                    return span;
                };
                loopStats.textContent = "";
                loopStats.append(
                    "Detections: ", makeStatSpan(ls.total_detections),
                    " | Active: ", makeStatSpan(ls.active_alerts),
                    " | Tracked: ", makeStatSpan(ls.tracked_signatures)
                );
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

                const spanId = document.createElement("span");
                spanId.className = "alert-id";
                spanId.textContent = a.alert_id;

                const divMsg = document.createElement("div");
                divMsg.className = "alert-msg";
                divMsg.textContent = a.message;

                const divDiag = document.createElement("div");
                divDiag.className = "alert-diag";
                a.diagnostic_suggestions.slice(0, 3).forEach((d, i) => {
                    if (i > 0) divDiag.appendChild(document.createElement("br"));
                    divDiag.appendChild(document.createTextNode("\u2022 " + d));
                });

                div.appendChild(spanId);
                div.appendChild(divMsg);
                div.appendChild(divDiag);
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
        _activateResonance('harness', '', 'transpiling');
        try {
            const res = await fetch("/api/harness/adriana/transpile", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ expression: expr }),
            });
            const data = await res.json();
            if (data.result) {
                renderAdrianaResult(data.result, data.dry_runs);
                var txHash = '';
                for (var ti = 0; ti < expr.length; ti++) txHash += expr.charCodeAt(ti).toString(16);
                _pulseResonance('harness', txHash.substring(0, 64));
            }
            else showToast(data.error || "Transpile failed", "error");
            _deactivateResonance('harness', 2000);
        } catch(e) { showToast("Error: " + e.message, "error"); _deactivateResonance('harness'); }
    });

    document.getElementById("adriana-execute-btn")?.addEventListener("click", async () => {
        const expr = document.getElementById("adriana-input").value.trim();
        if (!expr) return showToast("Enter an Adriana expression", "error");
        _activateResonance('harness', '', 'executing');
        try {
            const res = await fetch("/api/harness/adriana/execute", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ expression: expr }),
            });
            const data = await res.json();
            if (data.result) {
                renderAdrianaResult(data.result, null, data.execution);
                var exHash = '';
                for (var ei = 0; ei < expr.length; ei++) exHash += expr.charCodeAt(ei).toString(16);
                _pulseResonance('harness', exHash.substring(0, 64));
            }
            if (data.success) {
                showToast("Adriana: All commands executed", "success");
            } else if (data.partial) {
                showToast("Adriana: Partial execution (some blocked)", "error");
            } else if (data.errors && data.errors.length) {
                showToast("Adriana: " + data.errors[0], "error");
            } else {
                showToast("Adriana: Execution blocked by safety pipeline", "error");
            }
            _deactivateResonance('harness', 2000);
            loadHarnessStatus();
        } catch(e) { showToast("Error: " + e.message, "error"); _deactivateResonance('harness'); }
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
        const compRatio = Number(comp.ratio) || 0;
        const compAcChars = Number(comp.adriana_chars) || 0;
        const compPyChars = Number(comp.python_chars) || 0;
        const compAcGlyphs = Number(comp.adriana_glyphs) || 0;
        const compPyTokens = Number(comp.python_tokens) || 0;
        const compDensity = Number(comp.density) || 0;
        document.getElementById("adriana-compression").innerHTML =
            `<div class="ratio-value">${compRatio}x</div>` +
            `<div class="ratio-label">COMPRESSION RATIO</div>` +
            `<div style="margin-top:6px; font-size:10px; color:#888;">` +
            `${compAcChars} chars → ${compPyChars} chars<br>` +
            `${compAcGlyphs} glyphs → ${compPyTokens} tokens<br>` +
            `Density: ${compDensity}%</div>`;

        const cmdsEl = document.getElementById("adriana-commands");
        cmdsEl.innerHTML = (result.commands || []).map(c =>
            `<div class="adriana-cmd">${escHtml(c.action_type)} → ${escHtml(c.narrative)}</div>`
        ).join("") || '<div style="color:#666;">No commands generated</div>';

        const pyEl = document.getElementById("adriana-python");
        pyEl.innerHTML = `<div class="py-label">Python Equivalent</div>${escHtml(comp.python_equivalent || "# no equivalent")}`;

        const drEl = document.getElementById("adriana-dry-runs");
        if (dryRuns) {
            drEl.innerHTML = "<div style='color:#888;font-size:10px;margin-bottom:4px;'>SAFETY DRY-RUN</div>" +
                dryRuns.map(dr => {
                    const ok = dr.boundary_allowed && dr.checklist_verdict === "PASS";
                    return `<div class="adriana-dry-run">` +
                        `<span class="dr-verdict ${ok ? 'dr-pass' : 'dr-fail'}">${ok ? 'SAFE' : 'BLOCKED'}</span>` +
                        `<span>${escHtml(dr.action.type)}</span>` +
                        `<span style="color:#666;">${escHtml(dr.checklist_verdict)}</span>` +
                        `</div>`;
                }).join("");
        } else if (execResults) {
            drEl.innerHTML = "<div style='color:#888;font-size:10px;margin-bottom:4px;'>EXECUTION RESULTS</div>" +
                execResults.map(er => {
                    return `<div class="adriana-dry-run">` +
                        `<span class="dr-verdict ${er.executed ? 'dr-pass' : 'dr-fail'}">${er.executed ? 'DONE' : 'BLOCKED'}</span>` +
                        `<span>${escHtml(er.action.type)}</span>` +
                        `<span style="color:#888;font-size:10px;">${escHtml(er.narrative)}</span>` +
                        (er.blocked_by ? `<span style="color:#f87171;font-size:10px;">[${escHtml(er.blocked_by)}]</span>` : '') +
                        `</div>`;
                }).join("");
        } else {
            drEl.innerHTML = "";
        }
    }

    function renderAdrianaLexicon(lex) {
        const renderGroup = (containerId, title, entries) => {
            const el = document.getElementById(containerId);
            el.innerHTML = `<h4>${escHtml(title)}</h4>` +
                entries.map(e =>
                    `<span class="lex-entry" title="${escHtml(e.description)} → ${escHtml(e.python_equivalent)}">` +
                    `<span class="lex-glyph">${escHtml(e.glyph)}</span>` +
                    `<span class="lex-key">${escHtml(e.key)}</span>` +
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
            `<div class="ratio-value">${Number(comp.ratio) || 0}x</div>` +
            `<div class="ratio-label">COMPRESSION RATIO</div>` +
            `<div style="margin-top:6px; font-size:10px; color:#888;">` +
            `${Number(comp.aljabr_chars) || 0} chars \u2192 ${Number(comp.python_chars) || 0} chars<br>` +
            `${Number(comp.root_count) || 0} roots, ${Number(comp.pattern_count) || 0} patterns \u2192 ${Number(comp.action_count) || 0} actions</div>`;

        const cmdsEl = document.getElementById("aljabr-commands");
        cmdsEl.innerHTML = (result.commands || []).map(c =>
            `<div class="aljabr-cmd"><span class="cmd-root">${escHtml(c.root)}</span><span class="cmd-pat">.${escHtml(c.pattern)}</span> ${escHtml(c.action_type)} \u2192 ${escHtml(c.narrative)}</div>`
        ).join("") || '<div style="color:#666;">No commands generated</div>';

        const pyEl = document.getElementById("aljabr-python");
        pyEl.innerHTML = `<div class="py-label">Python Equivalent</div><pre>${escHtml(comp.python_equivalent || "# no equivalent")}</pre>`;

        const drEl = document.getElementById("aljabr-dry-runs");
        if (dryRuns) {
            drEl.innerHTML = "<div style='color:#888;font-size:10px;margin-bottom:4px;'>SAFETY DRY-RUN</div>" +
                dryRuns.map(dr => {
                    const ok = dr.boundary_allowed && dr.checklist_verdict === "PASS";
                    return `<div class="aljabr-dry-run">` +
                        `<span class="dr-verdict ${ok ? 'dr-pass' : 'dr-fail'}">${ok ? 'SAFE' : 'BLOCKED'}</span>` +
                        `<span class="dr-root">${escHtml(dr.root)}.${escHtml(dr.pattern)}</span>` +
                        `<span>${escHtml(dr.action.type)}</span>` +
                        `<span style="color:#666;">${escHtml(dr.checklist_verdict)}</span>` +
                        `</div>`;
                }).join("");
        } else if (execResults) {
            drEl.innerHTML = "<div style='color:#888;font-size:10px;margin-bottom:4px;'>EXECUTION RESULTS</div>" +
                execResults.map(er => {
                    return `<div class="aljabr-dry-run">` +
                        `<span class="dr-verdict ${er.executed ? 'dr-pass' : 'dr-fail'}">${er.executed ? 'DONE' : 'BLOCKED'}</span>` +
                        `<span class="dr-root">${escHtml(er.root)}.${escHtml(er.pattern)}</span>` +
                        `<span>${escHtml(er.action.type)}</span>` +
                        `<span style="color:#888;font-size:10px;">${escHtml(er.narrative)}</span>` +
                        (er.blocked_by ? `<span style="color:#f87171;font-size:10px;">[${escHtml(er.blocked_by)}]</span>` : '') +
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
            html += `<span class="pat-tag" title="${escHtml(info.verb)}">${escHtml(code)} ${escHtml(info.name)}</span>`;
        }
        html += '</div>';

        const domainLabels = {aqua:"Aquaponics",flywheel:"Flywheel",silk:"Silk Wiring",pressure:"Pressure",system:"System"};
        for (const [domain, roots] of Object.entries(manifest)) {
            if (!roots.length) continue;
            html += `<div class="aljabr-domain-group"><div class="aljabr-domain-label">${escHtml(domainLabels[domain] || domain)}</div>`;
            for (const r of roots) {
                html += `<div class="aljabr-root-entry">` +
                    `<span class="root-code">${escHtml(r.root)}</span>` +
                    `<span class="root-essence">${escHtml(r.essence)}</span>` +
                    `<span class="root-desc">${escHtml(r.description)}</span>` +
                    `<span class="root-patterns">${escHtml((r.available_patterns||[]).join(" "))}</span>` +
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
                    `<span class="wallet-tx-type ${escHtml(tx.tx_type)}">${escHtml(tx.tx_type)}</span>` +
                    `<span class="wallet-tx-amount ${amtClass}">${amtStr}</span>` +
                    `<span class="wallet-tx-desc">${escHtml(tx.description)}</span>` +
                    `<span class="wallet-tx-balance">${tx.balance_after.toFixed(2)} CC</span>` +
                    (tx.root_command ? `<span style="color:#eab308;font-size:9px;">${escHtml(tx.root_command)}</span>` : '') +
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

    function escapeHtml(str) {
        if (str == null) return '';
        return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
    }

    function renderConsensusResult(data) {
        const wrap = document.getElementById("consensus-result");
        wrap.style.display = "block";

        const outcomeEl = document.getElementById("consensus-outcome");
        outcomeEl.innerHTML = `<span class="consensus-verdict ${data.success ? 'pass' : 'fail'}">${escapeHtml(data.outcome)}</span>` +
            `<span class="consensus-cmd">${escapeHtml(data.consensus_command)}</span>`;

        const statsEl = document.getElementById("consensus-stats");
        statsEl.innerHTML = [
            { label: "Energy", value: escapeHtml(data.energy_pct) + "%" },
            { label: "Turns", value: escapeHtml(data.total_turns) },
            { label: "Total Chars", value: escapeHtml(data.total_chars) },
            { label: "Intent", value: escapeHtml(data.consensus_intent) },
        ].map(s => `<div class="cs-stat"><span class="cs-label">${s.label}</span> <span class="cs-value">${s.value}</span></div>`).join("");

        const traceEl = document.getElementById("consensus-trace");
        traceEl.innerHTML = '<div class="trace-header"><span>#</span><span>Agent</span><span>Command</span><span>Intent</span></div>' +
            (data.trace || []).map(t =>
                `<div class="trace-row ${t.agent === 'Agent A' ? 'agent-a' : 'agent-b'}">` +
                `<span>${escapeHtml(t.turn)}</span>` +
                `<span><strong>${escapeHtml(t.agent)}</strong><br><span class="trace-role">${escapeHtml(t.agent_role)}</span></span>` +
                `<span class="trace-cmd">${escapeHtml(t.command)}</span>` +
                `<span class="trace-intent">${escapeHtml(t.intent)}</span>` +
                `</div>`
            ).join("");

        const finalEl = document.getElementById("consensus-final");
        finalEl.innerHTML = `<div class="consensus-final-label">CONSENSUS COMMAND</div>` +
            `<div class="consensus-final-cmd">${escapeHtml(data.consensus_command)}</div>` +
            `<div class="consensus-final-intent">${escapeHtml(data.consensus_intent)}</div>`;

        const execEl = document.getElementById("consensus-execution");
        if (data.execution_results && data.execution_results.length) {
            execEl.innerHTML = '<div style="color:#888;font-size:10px;margin-bottom:4px;">EXECUTION TRACE</div>' +
                data.execution_results.map(er =>
                    `<div class="consensus-exec-row">` +
                    `<span class="dr-verdict ${er.executed ? 'dr-pass' : 'dr-fail'}">${er.executed ? 'DONE' : 'BLOCKED'}</span>` +
                    `<span class="dr-root">${escapeHtml(er.root)}.${escapeHtml(er.pattern)}</span>` +
                    `<span>${escapeHtml(er.narrative)}</span>` +
                    (er.blocked_by ? `<span style="color:#f87171;font-size:10px;">[${escapeHtml(er.blocked_by)}]</span>` : '') +
                    (er.wallet_result ? `<span style="color:#eab308;font-size:10px;">[${er.wallet_result.balance != null ? er.wallet_result.balance + ' CC' : ''}]</span>` : '') +
                    `</div>`
                ).join("");
        } else {
            execEl.innerHTML = "";
        }

        if (data.wallet) {
            const walletLine = document.createElement("div");
            walletLine.style.cssText = "margin-top:8px;padding:6px 10px;background:rgba(234,179,8,0.06);border:1px solid rgba(234,179,8,0.2);border-radius:4px;font-size:11px;font-family:monospace;color:#eab308;";
            walletLine.textContent = `WALLET: ${data.wallet.balance.toFixed(2)} CC | Earned: ${data.wallet.total_earned.toFixed(2)} | Spent: ${data.wallet.total_spent.toFixed(2)}`;
            if (data.wallet.frozen) {
                const frozenSpan = document.createElement("span");
                frozenSpan.style.color = "#f87171";
                frozenSpan.textContent = " | FROZEN";
                walletLine.appendChild(frozenSpan);
            }
            execEl.appendChild(walletLine);
        }
    }

    function updateDividedSelects(fileData) {
        const carrierSel = document.getElementById("divided-carrier");
        const payloadSel = document.getElementById("divided-payload");
        if (!carrierSel || !payloadSel) return;
        const wavFiles = fileData.input.filter(f => f.name.toLowerCase().endsWith(".wav"));
        carrierSel.replaceChildren(buildSelectOptions(wavFiles, 'No WAV files'));
        payloadSel.replaceChildren(buildSelectOptions(fileData.input, 'No files', function(f) {
            return f.name.toLowerCase().endsWith(".wav") ? " [WAV]" : "";
        }));
    }

    (async function loadDividedReadiness() {
        try {
            const res = await fetch("/api/harness/divided/status");
            const data = await res.json();
            const el = document.getElementById("divided-readiness");
            if (!el) return;
            const ready = data.ready;
            el.className = "divided-readiness " + (ready ? "ready" : "not-ready");
            const checks = data.checks || {};
            el.innerHTML = ready
                ? `System Ready — ${checks.system_status || "NOMINAL"} | RPM: ${checks.flywheel_rpm || 0} | Chronicle: ${checks.chronicle_available ? "ON" : "OFF"} | Wallet: ${checks.wallet_available ? "ON" : "OFF"}`
                : `System Not Ready — ${checks.critical_issues || 0} critical issue(s) detected. Run SLM.V scan first.`;

            const files = await fetchFiles();
            updateDividedSelects(files);
        } catch(e) {}
    })();

    document.getElementById("divided-execute-btn")?.addEventListener("click", async () => {
        const carrier = document.getElementById("divided-carrier").value;
        const payload = document.getElementById("divided-payload").value;
        const lsb = document.getElementById("divided-lsb").value;
        const btn = document.getElementById("divided-execute-btn");

        if (!carrier || !payload) {
            showToast("Select carrier and payload files", "error");
            return;
        }

        btn.disabled = true;
        btn.innerHTML = '<span class="spinner"></span>Executing...';
        document.getElementById("divided-result").style.display = "none";

        document.querySelectorAll(".divided-step").forEach(el => {
            el.setAttribute("data-status", "");
            el.querySelector(".divided-step-status").textContent = "—";
        });

        for (let i = 1; i <= 5; i++) {
            const stepEl = document.querySelector(`.divided-step[data-step="${i}"]`);
            if (stepEl) {
                stepEl.setAttribute("data-status", "running");
                stepEl.querySelector(".divided-step-status").textContent = "running...";
            }
            await new Promise(r => setTimeout(r, 200));
            if (i < 5) {
                stepEl.setAttribute("data-status", "pass");
                stepEl.querySelector(".divided-step-status").textContent = "PASS";
            }
        }

        try {
            const res = await fetch("/api/harness/divided/execute", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ carrier, payload, lsb_depth: parseInt(lsb) }),
            });
            const data = await res.json();

            if (data.error && !data.steps) {
                showToast("Protocol error: " + data.error, "error");
                document.querySelectorAll(".divided-step").forEach(el => {
                    el.setAttribute("data-status", "fail");
                    el.querySelector(".divided-step-status").textContent = "ERROR";
                });
                btn.disabled = false;
                btn.textContent = "Execute Protocol";
                return;
            }

            (data.steps || []).forEach(step => {
                const stepEl = document.querySelector(`.divided-step[data-step="${step.index}"]`);
                if (stepEl) {
                    stepEl.setAttribute("data-status", step.status);
                    const ms = step.duration_ms > 0 ? ` (${step.duration_ms.toFixed(0)}ms)` : "";
                    stepEl.querySelector(".divided-step-status").textContent = step.status.toUpperCase() + ms;
                }
            });

            const headerEl = document.getElementById("divided-result-header");
            headerEl.className = "divided-result-header " + (data.success ? "success" : "failure");
            headerEl.textContent = data.success
                ? "Protocol Complete — All steps passed"
                : "Protocol Failed — Check step details below";

            const detailsEl = document.getElementById("divided-step-details");
            detailsEl.innerHTML = (data.steps || []).map(step => {
                let info = "";
                if (step.result) {
                    if (step.index === 1) info = step.result.summary || "";
                    if (step.index === 2) info = `SNR: ${step.result.carrier_snr_db || 0} dB | Resonance: ${step.result.resonance_score || 0}`;
                    if (step.index === 3) info = `Axiom: ${step.result.axiom_result || ""} | RPM: ${step.result.motion_rpm || 0}`;
                    if (step.index === 4) info = `${formatSize(step.result.original_size || 0)} → ${formatSize(step.result.compressed_size || 0)} (vortex)`;
                    if (step.index === 5) info = step.result.committed ? `Chronicle #${step.result.chronicle_id} | ${step.result.wallet_charged} CC` : "Not committed";
                }
                if (step.error) info = step.error;
                return `<div class="divided-detail-row">` +
                    `<div class="divided-detail-code">${step.root_code}</div>` +
                    `<div class="divided-detail-name">${step.name}</div>` +
                    `<div class="divided-detail-info">${info}</div>` +
                    `<div class="divided-detail-badge ${step.status}">${step.status.toUpperCase()}</div>` +
                    `</div>`;
            }).join("");

            const finalEl = document.getElementById("divided-final");
            if (data.success && data.hash_key) {
                finalEl.innerHTML = `<div style="color:#888;font-size:10px;margin-bottom:4px;">HASH KEY (save this!)</div>` +
                    `<div class="hash-display">${data.hash_key}</div>` +
                    `<div style="margin-top:8px;font-size:11px;color:var(--text-muted);">` +
                    `Output: ${data.output_file} | Scatter: ${data.scatter_mode} | Chain: ${data.chain} | Duration: ${data.total_duration_ms.toFixed(0)}ms</div>`;
            } else {
                finalEl.innerHTML = `<div style="color:#ff4444;font-size:12px;">Protocol terminated at failed step. Duration: ${(data.total_duration_ms || 0).toFixed(0)}ms</div>`;
            }

            document.getElementById("divided-result").style.display = "block";
            showToast(data.success ? "Divided Protocol — all 5 steps passed" : "Protocol failed — see results", data.success ? "success" : "error");
            loadSelects();
        } catch(e) {
            showToast("Protocol execution error: " + e.message, "error");
            document.querySelectorAll(".divided-step").forEach(el => {
                el.setAttribute("data-status", "fail");
                el.querySelector(".divided-step-status").textContent = "ERROR";
            });
        }

        btn.disabled = false;
        btn.textContent = "Execute Protocol";
    });

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
            renderWarrantyMachineId(data);
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

    function renderWarrantyMachineId(data) {
        if (data.machine_id) {
            let html = `<div class="warranty-machine-id">Machine ID: ${data.machine_id}</div>`;
            html += `<div class="warranty-title">${data.title}</div>`;
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
            document.getElementById("warranty-content").innerHTML = html;
        }
    }

    fetch("/api/harness/machine-id").then(r => r.json()).then(data => {
        document.getElementById("ritual-machine-id").textContent = data.machine_id;
    }).catch(() => {});

    document.querySelectorAll(".btn-ritual").forEach(btn => {
        btn.addEventListener("click", async () => {
            const ritualType = btn.dataset.ritual;
            const color = btn.dataset.color;
            btn.disabled = true;

            try {
                const res = await fetch("/api/harness/rituals/perform", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ ritual_type: ritualType }),
                });
                const data = await res.json();
                if (data.error) {
                    showToast("Ritual failed: " + data.error);
                    btn.disabled = false;
                    return;
                }

                showRitualFlash(color, data.ritual);
                renderRitualResult(data);
                loadRitualHistory();
            } catch (e) {
                showToast("Ritual failed");
            }
            btn.disabled = false;
        });
    });

    function showRitualFlash(color, ritual) {
        const flash = document.getElementById("ritual-flash");
        flash.style.display = "block";
        flash.style.background = `radial-gradient(circle, ${color}40, transparent 70%)`;
        flash.style.boxShadow = `0 0 60px ${color}60, inset 0 0 40px ${color}30`;
        flash.innerHTML = `<div class="ritual-flash-glyph" style="color:${color}">${ritual.visual}</div>` +
            `<div class="ritual-flash-name" style="color:${color}">${ritual.name}</div>` +
            `<div class="ritual-flash-root">${ritual.root}</div>`;

        setTimeout(() => {
            flash.style.display = "none";
        }, 3000);
    }

    function renderRitualResult(data) {
        const el = document.getElementById("ritual-last-result");
        el.style.display = "block";
        const r = data.ritual;
        el.innerHTML = `<div class="ritual-result-card" style="border-color:${r.color}">` +
            `<div class="ritual-result-header">` +
            `<span class="ritual-result-name" style="color:${r.color}">${r.name}</span>` +
            `<span class="ritual-result-root">${r.root}</span>` +
            `</div>` +
            `<div class="ritual-result-intent">${r.intent}</div>` +
            `<div class="ritual-result-desc">${r.description}</div>` +
            `<div class="ritual-result-snap">Before: ${r.scan_before} | After: ${r.scan_after}</div>` +
            `</div>`;
    }

    async function loadRitualHistory() {
        try {
            const res = await fetch("/api/harness/rituals/history?limit=30");
            const data = await res.json();
            document.getElementById("ritual-count").textContent = data.history.length + " rituals";
            renderRitualTimeline(data.history);
        } catch (e) {}
    }

    function renderRitualTimeline(history) {
        const el = document.getElementById("ritual-timeline");
        if (!history.length) {
            el.innerHTML = `<div class="ritual-empty">No rituals performed yet. The machine awaits its first Ritual.</div>`;
            return;
        }
        el.innerHTML = history.slice().reverse().map(r => {
            const dt = new Date(r.timestamp * 1000);
            const timeStr = dt.toLocaleString();
            return `<div class="ritual-entry" style="border-left-color:${r.color}">` +
                `<div class="ritual-entry-header">` +
                `<span class="ritual-entry-name" style="color:${r.color}">${r.name}</span>` +
                `<span class="ritual-entry-root">${r.root}</span>` +
                `<span class="ritual-entry-visual">${r.visual}</span>` +
                `</div>` +
                `<div class="ritual-entry-intent">${r.intent}</div>` +
                `<div class="ritual-entry-time">${timeStr}</div>` +
                `</div>`;
        }).join("");
    }

    loadRitualHistory();

    document.getElementById("autoheal-scan-btn").addEventListener("click", async () => {
        const label = document.getElementById("autoheal-status-label");
        label.textContent = "Scanning + Healing...";
        try {
            const res = await fetch("/api/harness/autoheal/scan", { method: "POST" });
            const data = await res.json();
            if (data.error) { label.textContent = "Error: " + data.error; return; }
            renderAutoHealResult(data);
            updateAutoHealStats(data.stats);
            label.textContent = "";
        } catch (e) {
            label.textContent = "Scan failed";
        }
    });

    document.getElementById("autoheal-toggle-btn").addEventListener("click", async () => {
        try {
            const res = await fetch("/api/harness/autoheal/toggle", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ interval: 300 }),
            });
            const data = await res.json();
            const btn = document.getElementById("autoheal-toggle-btn");
            if (data.status === "started") {
                btn.textContent = "Daemon: ON";
                btn.classList.add("active");
                document.getElementById("ah-daemon-status").textContent = "ON";
                document.getElementById("ah-daemon-status").style.color = "#00FF88";
            } else {
                btn.textContent = "Daemon: OFF";
                btn.classList.remove("active");
                document.getElementById("ah-daemon-status").textContent = "OFF";
                document.getElementById("ah-daemon-status").style.color = "#ff4444";
            }
        } catch (e) {
            showToast("Failed to toggle daemon");
        }
    });

    function renderAutoHealResult(data) {
        const wrap = document.getElementById("autoheal-result");
        wrap.style.display = "block";

        const healedEl = document.getElementById("autoheal-healed");
        if (data.healed && data.healed.length > 0) {
            healedEl.innerHTML = `<div class="ah-section-title">Auto-Healed</div>` +
                data.healed.map(h =>
                    `<div class="ah-heal-card">` +
                    `<span class="ah-heal-root">${h.root}</span>` +
                    `<span class="ah-heal-domain">${h.domain}</span>` +
                    `<span class="ah-heal-desc">${h.description}</span>` +
                    `</div>`
                ).join("");
        } else {
            healedEl.innerHTML = `<div class="ah-section-title">Auto-Healed</div><div class="ah-none">No auto-repairs needed</div>`;
        }

        const alertsEl = document.getElementById("autoheal-alerts");
        if (data.alerts && data.alerts.length > 0) {
            alertsEl.innerHTML = `<div class="ah-section-title ah-alert-title">Ritual Requests</div>` +
                data.alerts.map(a =>
                    `<div class="ah-alert-card">` +
                    `<div class="ah-alert-header">` +
                    `<span class="ah-alert-severity sev-${a.severity}">${a.severity}</span>` +
                    `<span class="ah-alert-root">${a.root_code}</span>` +
                    `</div>` +
                    `<div class="ah-alert-msg">${a.message}</div>` +
                    (a.ritual_name ? `<div class="ah-alert-ritual">Required Ritual: <strong>${a.ritual_name}</strong></div>` : '') +
                    `<div class="ah-alert-fix">Fix: <code>${a.fix_command}</code></div>` +
                    `</div>`
                ).join("");
        } else {
            alertsEl.innerHTML = `<div class="ah-section-title ah-alert-title">Ritual Requests</div><div class="ah-none">No alerts — The Village is at peace</div>`;
        }
    }

    function updateAutoHealStats(stats) {
        document.getElementById("ah-scans").textContent = stats.total_scans;
        document.getElementById("ah-heals").textContent = stats.total_heals;
        document.getElementById("ah-alerts-count").textContent = stats.total_alerts;
        const daemonEl = document.getElementById("ah-daemon-status");
        if (stats.daemon_active) {
            daemonEl.textContent = "ON";
            daemonEl.style.color = "#00FF88";
            document.getElementById("autoheal-toggle-btn").textContent = "Daemon: ON";
        } else {
            daemonEl.textContent = "OFF";
            daemonEl.style.color = "#ff4444";
        }
    }

    fetch("/api/harness/autoheal/status").then(r => r.json()).then(data => {
        updateAutoHealStats(data);
    }).catch(() => {});

    function loadChronicleStats() {
        fetch("/api/harness/chronicle/stats").then(r => r.json()).then(data => {
            document.getElementById("ch-total").textContent = data.total_entries;
            document.getElementById("ch-rate").textContent = data.success_rate + "%";
            document.getElementById("ch-machine").textContent = data.machine_id ? data.machine_id.replace("VOID-4000-", "V4K-") : "—";
            if (data.most_proven_root) {
                document.getElementById("ch-proven").textContent = data.most_proven_root.command;
                document.getElementById("ch-proven").title = "Used " + data.most_proven_root.count + " times";
            }
        }).catch(() => {});

        fetch("/api/harness/chronicle/wisdom").then(r => r.json()).then(data => {
            if (data.memory_layers) {
                const stMatch = data.memory_layers.short_term || "";
                const epMatch = data.memory_layers.episodic || "";
                const anMatch = data.memory_layers.ancestral || "";
                document.getElementById("chronicle-layer-st").textContent = stMatch.split("—")[1] || "Current scan";
                document.getElementById("chronicle-layer-ep").textContent = epMatch.split("—")[1] || "0 readings";
                document.getElementById("chronicle-layer-an").textContent = anMatch.split("—")[1] || "0 outcomes";
            }
        }).catch(() => {});
    }

    function loadChronicleTimeline() {
        fetch("/api/harness/chronicle/entries?limit=30").then(r => r.json()).then(data => {
            const timeline = document.getElementById("chronicle-timeline");
            if (!data.entries || data.entries.length === 0) {
                timeline.innerHTML = '<div class="chronicle-empty">No entries yet. Run Consensus to build the Chronicle.</div>';
                return;
            }
            timeline.innerHTML = data.entries.map(e => {
                const t = new Date(e.timestamp * 1000);
                const time = t.toLocaleTimeString([], {hour: "2-digit", minute: "2-digit"});
                const cls = e.success ? "success" : "partial";
                return '<div class="chronicle-entry ' + cls + '">' +
                    '<span class="ce-time">' + time + '</span>' +
                    '<span class="ce-cmd" title="' + (e.consensus_intent || "") + '">' + e.consensus_command + '</span>' +
                    '<span class="ce-energy">' + e.energy_pct + '%</span>' +
                    '<span class="ce-outcome">' + e.outcome + '</span>' +
                    '</div>';
            }).join("");
        }).catch(() => {});
    }

    loadChronicleStats();
    loadChronicleTimeline();

    document.getElementById("chronicle-query-btn").addEventListener("click", function() {
        this.disabled = true;
        this.textContent = "Querying...";
        fetch("/api/harness/chronicle/query", {method: "POST"}).then(r => r.json()).then(data => {
            const resultEl = document.getElementById("chronicle-result");
            const matchesEl = document.getElementById("chronicle-matches");
            resultEl.style.display = "block";

            if (!data.matches || data.matches.length === 0) {
                matchesEl.innerHTML = '<div class="chronicle-empty">No ancestral matches found for current sensor state.</div>';
            } else {
                matchesEl.innerHTML = '<div style="font-size:0.8em;color:var(--text-muted);margin-bottom:8px;">ANCESTRAL MATCHES</div>' +
                    data.matches.map(m =>
                        '<div class="ancestor-card">' +
                        '<div class="ancestor-similarity">Match: ' + (m.similarity * 100).toFixed(1) + '%</div>' +
                        '<div class="ancestor-command">' + m.proven_command + '</div>' +
                        '<div class="ancestor-intent">' + m.proven_intent + '</div>' +
                        '<div class="ancestor-domains">' + m.matched_domains.map(d => '<span class="ancestor-domain-tag">' + d + '</span>').join("") + '</div>' +
                        '</div>'
                    ).join("");
            }
            showToast("Ancestors queried", "success");
        }).catch(() => {
            showToast("Query failed", "error");
        }).finally(() => {
            this.disabled = false;
            this.textContent = "Query Ancestors";
        });
    });

    document.getElementById("chronicle-prophecy-btn").addEventListener("click", function() {
        this.disabled = true;
        this.textContent = "Prophesying...";
        fetch("/api/harness/chronicle/prophecy", {method: "POST"}).then(r => r.json()).then(data => {
            const resultEl = document.getElementById("chronicle-result");
            const prophEl = document.getElementById("chronicle-prophecies");
            resultEl.style.display = "block";

            if (!data.prophecies || data.prophecies.length === 0) {
                prophEl.innerHTML = '<div class="chronicle-empty">No prophecies — the V2 Pastor sees no imminent crisis patterns.</div>';
            } else {
                prophEl.innerHTML = '<div style="font-size:0.8em;color:#FFD700;margin-bottom:8px;">V2 PASTOR PROPHECIES</div>' +
                    data.prophecies.map(p =>
                        '<div class="prophecy-card">' +
                        '<div class="prophecy-name">' + p.pattern_name.replace(/_/g, " ") + '</div>' +
                        '<div class="prophecy-command">' + p.prophecy_command + '</div>' +
                        '<div class="prophecy-intent">' + p.prophecy_intent + '</div>' +
                        '<div class="prophecy-confidence">Confidence: ' + (p.confidence * 100).toFixed(0) + '% | Supporting: ' + p.supporting_entries + ' entries | ' + p.trigger_domain + ' → ' + p.consequence_domain + '</div>' +
                        '</div>'
                    ).join("");
            }
            showToast("Prophecy complete", "success");
        }).catch(() => {
            showToast("Prophecy failed", "error");
        }).finally(() => {
            this.disabled = false;
            this.textContent = "V2 Pastor Prophecy";
        });
    });

    document.getElementById("chronicle-export-btn").addEventListener("click", function() {
        fetch("/api/harness/chronicle/export").then(r => r.json()).then(data => {
            const blob = new Blob([JSON.stringify(data, null, 2)], {type: "application/json"});
            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = "genesis_seed_" + (data.source_machine_id || "void") + ".json";
            a.click();
            URL.revokeObjectURL(url);
            showToast("Genesis Seed exported — " + data.total_entries + " entries", "success");
        }).catch(() => {
            showToast("Export failed", "error");
        });
    });

    document.getElementById("chronicle-import-input").addEventListener("change", function(e) {
        const file = e.target.files[0];
        if (!file) return;
        const reader = new FileReader();
        reader.onload = function(ev) {
            try {
                const seedData = JSON.parse(ev.target.result);
                fetch("/api/harness/chronicle/import", {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify(seedData)
                }).then(r => r.json()).then(data => {
                    if (data.success) {
                        showToast("Genesis Seed imported: " + data.imported_chronicle + " chronicle + " + data.imported_episodic + " episodic from " + data.source_machine, "success");
                        loadChronicleStats();
                        loadChronicleTimeline();
                    } else {
                        showToast("Import failed: " + (data.error || "Unknown error"), "error");
                    }
                }).catch(() => showToast("Import failed", "error"));
            } catch (err) {
                showToast("Invalid JSON file", "error");
            }
        };
        reader.readAsText(file);
        e.target.value = "";
    });

    const origConsensusBtn = document.getElementById("consensus-run-btn");
    if (origConsensusBtn) {
        const origClick = origConsensusBtn.onclick;
        origConsensusBtn.addEventListener("click", function() {
            setTimeout(function() {
                loadChronicleStats();
                loadChronicleTimeline();
                loadFounderStatus();
            }, 1500);
        });
    }

    function loadFounderStatus() {
        fetch("/api/harness/founder/status").then(r => r.json()).then(data => {
            var statusEl = document.getElementById("founder-status-val");
            var countEl = document.getElementById("founder-count-val");
            var hashEl = document.getElementById("founder-hash-val");
            var machineEl = document.getElementById("founder-machine-val");
            var banner = document.getElementById("founder-greeting-banner");

            countEl.textContent = data.founder_count || 0;
            machineEl.textContent = data.machine_id ? data.machine_id.replace("VOID-4000-", "V4K-") : "—";

            if (data.is_founder) {
                statusEl.textContent = "FIRST GENERATION";
                statusEl.style.color = "#D4AF37";
                hashEl.textContent = data.founder_root_hash;
                hashEl.style.color = "#D4AF37";
                banner.style.display = "flex";
                document.getElementById("founder-greeting-msg").textContent = data.greeting || "First Generation Status: ACTIVE";
                document.getElementById("founder-greeting-hash").textContent = data.founder_root_hash;
                document.body.classList.add("founder-vibe");
            } else {
                statusEl.textContent = "NOT ACTIVATED";
                statusEl.style.color = "var(--text-muted)";
                hashEl.textContent = "—";
                banner.style.display = "none";
                document.body.classList.remove("founder-vibe");
            }
        }).catch(function() {});
    }

    loadFounderStatus();

    document.getElementById("founder-mark-btn").addEventListener("click", function() {
        var btn = this;
        btn.disabled = true;
        btn.textContent = "Marking...";
        fetch("/api/harness/founder/mark", {method: "POST"}).then(r => r.json()).then(function(data) {
            if (data.success) {
                showToast("Founder Wisdom marked: " + data.marked_count + " entries flagged as Original Lineage", "success");
                loadFounderStatus();
                loadChronicleStats();
            } else {
                showToast("Failed to mark founder wisdom", "error");
            }
        }).catch(function() {
            showToast("Mark failed", "error");
        }).finally(function() {
            btn.disabled = false;
            btn.textContent = "Mark as Founder Wisdom";
        });
    });

    document.getElementById("founder-cert-btn").addEventListener("click", function() {
        var btn = this;
        btn.disabled = true;
        btn.textContent = "Generating...";
        fetch("/api/harness/founder/cert", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({customer_id: 1})
        }).then(r => r.json()).then(function(data) {
            if (data.success) {
                var resultEl = document.getElementById("founder-result");
                var contentEl = document.getElementById("founder-result-content");
                resultEl.style.display = "block";
                contentEl.innerHTML = '<div class="founder-cert-result">' +
                    '<div class="cert-icon">CERT</div>' +
                    '<div class="cert-details">' +
                    '<div class="cert-filename">' + data.filename + '</div>' +
                    '<div class="cert-seal">Seal: ' + data.seal + '</div>' +
                    '<a href="/api/download/output_audio/' + data.filename + '" class="btn-founder-secondary" style="text-decoration:none;display:inline-block;margin-top:8px;">Download Certificate</a>' +
                    '</div></div>';
                showToast("Founder Certificate generated: " + data.filename, "success");
            }
        }).catch(function() {
            showToast("Generation failed", "error");
        }).finally(function() {
            btn.disabled = false;
            btn.textContent = "Generate Single Cert";
        });
    });

    document.getElementById("founder-batch-btn").addEventListener("click", function() {
        var btn = this;
        btn.disabled = true;
        btn.textContent = "Generating 100...";
        fetch("/api/harness/founder/batch", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({count: 100})
        }).then(r => r.json()).then(function(data) {
            if (data.success) {
                var resultEl = document.getElementById("founder-result");
                var contentEl = document.getElementById("founder-result-content");
                resultEl.style.display = "block";
                contentEl.innerHTML = '<div class="founder-batch-result">' +
                    '<div class="batch-count">' + data.generated + ' Certificates Generated</div>' +
                    '<div class="batch-list">' + data.filenames.slice(0, 5).join(", ") + (data.generated > 5 ? ", ..." : "") + '</div>' +
                    '</div>';
                showToast(data.generated + " Founder Certificates generated", "success");
            }
        }).catch(function() {
            showToast("Batch generation failed", "error");
        }).finally(function() {
            btn.disabled = false;
            btn.textContent = "Generate 100 Certs";
        });
    });

    document.getElementById("founder-kit-btn").addEventListener("click", function() {
        var btn = this;
        btn.disabled = true;
        btn.textContent = "Packaging...";
        fetch("/api/harness/founder/genesis-kit", {method: "POST"}).then(r => r.json()).then(function(data) {
            if (data.success) {
                var blob = new Blob([JSON.stringify(data.genesis_seed, null, 2)], {type: "application/json"});
                var url = URL.createObjectURL(blob);
                var a = document.createElement("a");
                a.href = url;
                a.download = "genesis_kit_founder_seed.json";
                a.click();
                URL.revokeObjectURL(url);

                var resultEl = document.getElementById("founder-result");
                var contentEl = document.getElementById("founder-result-content");
                resultEl.style.display = "block";
                contentEl.innerHTML = '<div class="founder-kit-result">' +
                    '<div class="kit-title">Genesis Kit Packaged</div>' +
                    '<div class="kit-hash">Root Hash: ' + data.founder_root_hash + '</div>' +
                    '<div class="kit-entries">Chronicle: ' + data.genesis_seed.total_entries + ' entries | Episodic: ' + data.genesis_seed.total_episodic + '</div>' +
                    '<div class="kit-instructions">' + data.instructions + '</div>' +
                    '</div>';

                showToast("Genesis Kit exported with Founder Wisdom", "success");
                loadFounderStatus();
            }
        }).catch(function() {
            showToast("Kit packaging failed", "error");
        }).finally(function() {
            btn.disabled = false;
            btn.textContent = "Package Genesis Kit";
        });
    });

    var meshActive = false;
    var meshRefreshInterval = null;

    function addMeshLog(event, detail) {
        var log = document.getElementById("mesh-activity-log");
        var empty = log.querySelector(".mesh-log-empty");
        if (empty) empty.remove();
        var now = new Date();
        var timeStr = now.toLocaleTimeString([], {hour:'2-digit', minute:'2-digit', second:'2-digit'});
        var entry = document.createElement("div");
        entry.className = "mesh-log-entry";
        entry.innerHTML = '<span class="mesh-log-time">' + timeStr + '</span><span class="mesh-log-event">' + event + '</span><span class="mesh-log-detail">' + detail + '</span>';
        log.prepend(entry);
    }

    function updateMeshStateBadge(state) {
        var badge = document.getElementById("mesh-state-badge");
        var s = (state || "dark").toLowerCase();
        badge.textContent = s.toUpperCase();
        badge.className = "mesh-state-badge state-" + s;
    }

    function refreshMeshStatus() {
        fetch("/api/mesh/status").then(function(r) { return r.json(); }).then(function(data) {
            if (!data.success) return;
            document.getElementById("mesh-node-id").textContent = data.node_id || "—";
            document.getElementById("mesh-state-val").textContent = (data.state || "DARK").toUpperCase();
            document.getElementById("mesh-neighbor-count").textContent = data.neighbor_count || 0;
            var stats = data.stats || {};
            document.getElementById("mesh-packets-sent").textContent = stats.packets_sent || 0;
            document.getElementById("mesh-packets-recv").textContent = stats.packets_received || 0;
            document.getElementById("mesh-packets-relay").textContent = stats.packets_relayed || 0;
            document.getElementById("mesh-cc-spent").textContent = (stats.cc_spent || 0).toFixed(1);
            updateMeshStateBadge(data.state || "dark");

            var grid = document.getElementById("mesh-neighbors-grid");
            if (data.neighbors && data.neighbors.length > 0) {
                grid.innerHTML = data.neighbors.map(function(n) {
                    var signalClass = "mesh-signal-strong";
                    if (n.signal < 0.5) signalClass = "mesh-signal-weak";
                    else if (n.signal < 0.8) signalClass = "mesh-signal-medium";
                    var cardClass = n.state === "dark" ? "mesh-neighbor-card dark" : "mesh-neighbor-card active";
                    return '<div class="' + cardClass + '">' +
                        '<div class="mesh-neighbor-id">' + (n.node_id || "unknown") + '</div>' +
                        '<div class="mesh-neighbor-stat">State: ' + (n.state || "unknown") + '</div>' +
                        '<div class="mesh-neighbor-stat">Hops: ' + (n.hops || 0) + '</div>' +
                        '<div class="mesh-signal-bar ' + signalClass + '"></div>' +
                        '</div>';
                }).join("");
            } else {
                grid.innerHTML = '<div class="mesh-empty">No neighbors detected.</div>';
            }
        }).catch(function() {});
    }

    var meshToggleBtn = document.getElementById("mesh-toggle-btn");
    if (meshToggleBtn) {
        meshToggleBtn.addEventListener("click", function() {
            if (!meshActive) {
                meshToggleBtn.disabled = true;
                meshToggleBtn.textContent = "Connecting...";
                fetch("/api/mesh/connect", { method: "POST", headers: {"Content-Type": "application/json"}, body: "{}" }).then(function(r) { return r.json(); }).then(function(data) {
                    if (data.success) {
                        meshActive = true;
                        meshToggleBtn.textContent = "Leave Sovereign Mesh Mode";
                        meshToggleBtn.classList.add("active");
                        document.body.classList.add("beehive-active");
                        document.getElementById("mesh-send-btn").disabled = false;
                        addMeshLog("CONNECTED", "Node joined the mesh network");
                        refreshMeshStatus();
                        meshRefreshInterval = setInterval(refreshMeshStatus, 5000);
                        showToast("Sovereign Mesh Mode activated", "success");
                    } else {
                        showToast(data.error || "Failed to connect", "error");
                    }
                }).catch(function(e) {
                    showToast("Connection failed: " + e.message, "error");
                }).finally(function() {
                    meshToggleBtn.disabled = false;
                });
            } else {
                meshToggleBtn.disabled = true;
                meshToggleBtn.textContent = "Disconnecting...";
                fetch("/api/mesh/disconnect", { method: "POST", headers: {"Content-Type": "application/json"}, body: "{}" }).then(function(r) { return r.json(); }).then(function(data) {
                    meshActive = false;
                    meshToggleBtn.textContent = "Enter Sovereign Mesh Mode";
                    meshToggleBtn.classList.remove("active");
                    document.body.classList.remove("beehive-active");
                    document.getElementById("mesh-send-btn").disabled = true;
                    if (meshRefreshInterval) { clearInterval(meshRefreshInterval); meshRefreshInterval = null; }
                    updateMeshStateBadge("dark");
                    addMeshLog("DISCONNECTED", "Node left the mesh network");
                    showToast("Sovereign Mesh Mode deactivated", "success");
                }).catch(function(e) {
                    showToast("Disconnect failed: " + e.message, "error");
                }).finally(function() {
                    meshToggleBtn.disabled = false;
                });
            }
        });
    }

    var meshSendBtn = document.getElementById("mesh-send-btn");
    if (meshSendBtn) {
        meshSendBtn.addEventListener("click", function() {
            var input = document.getElementById("mesh-send-input");
            var msg = input.value.trim();
            if (!msg) { showToast("Enter a message to transmit", "error"); return; }
            meshSendBtn.disabled = true;
            _activateResonance('mesh', '', 'transmitting');
            fetch("/api/mesh/send", { method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({message: msg}) }).then(function(r) { return r.json(); }).then(function(data) {
                if (data.success) {
                    addMeshLog("TRANSMITTED", msg);
                    showToast("Message transmitted via mesh", "success");
                    var meshHash = '';
                    for (var mi = 0; mi < msg.length; mi++) meshHash += msg.charCodeAt(mi).toString(16);
                    _pulseResonance('mesh', meshHash.substring(0, 64));
                    _deactivateResonance('mesh', 2000);
                    input.value = "";
                    refreshMeshStatus();
                } else {
                    showToast(data.error || "Transmit failed", "error");
                    _deactivateResonance('mesh');
                }
            }).catch(function(e) {
                showToast("Transmit failed: " + e.message, "error");
                _deactivateResonance('mesh');
            }).finally(function() {
                meshSendBtn.disabled = !meshActive;
            });
        });
    }

    var meshHandshakeBtn = document.getElementById("mesh-handshake-btn");
    if (meshHandshakeBtn) {
        meshHandshakeBtn.addEventListener("click", function() {
            meshHandshakeBtn.disabled = true;
            _activateResonance('mesh', '', 'handshake');
            fetch("/api/mesh/handshake", { method: "POST", headers: {"Content-Type": "application/json"}, body: "{}" }).then(function(r) { return r.json(); }).then(function(data) {
                if (data.success) {
                    addMeshLog("HANDSHAKE", data.message || "432 Hz pulse sent");
                    showToast(data.message || "Handshake pulse sent", "success");
                    var hsHash = data.node_id || data.message || '432';
                    var hsHex = '';
                    for (var hi = 0; hi < hsHash.length; hi++) hsHex += hsHash.charCodeAt(hi).toString(16);
                    _pulseResonance('mesh', hsHex.substring(0, 64));
                    _deactivateResonance('mesh', 2000);
                    refreshMeshStatus();
                } else {
                    showToast(data.error || "Handshake failed", "error");
                    _deactivateResonance('mesh');
                }
            }).catch(function(e) {
                showToast("Handshake failed: " + e.message, "error");
                _deactivateResonance('mesh');
            }).finally(function() {
                meshHandshakeBtn.disabled = false;
            });
        });
    }

    var meshSimulateBtn = document.getElementById("mesh-simulate-btn");
    if (meshSimulateBtn) {
        meshSimulateBtn.addEventListener("click", function() {
            meshSimulateBtn.disabled = true;
            meshSimulateBtn.textContent = "Simulating...";
            var simResult = document.getElementById("mesh-sim-result");
            var simContent = document.getElementById("mesh-sim-content");
            fetch("/api/mesh/simulate", { method: "POST", headers: {"Content-Type": "application/json"}, body: "{}" }).then(function(r) { return r.json(); }).then(function(data) {
                simResult.style.display = "block";
                if (data.success) {
                    var html = '<div><strong>Two-Node Simulation</strong></div>';
                    if (data.steps && data.steps.length) {
                        data.steps.forEach(function(step) {
                            var cls = step.pass ? "sim-pass" : "sim-fail";
                            html += '<div class="' + cls + '">' + (step.pass ? "✓" : "✗") + ' ' + step.description + '</div>';
                        });
                    }
                    if (data.summary) html += '<div style="margin-top:8px;"><strong>' + data.summary + '</strong></div>';
                    simContent.innerHTML = html;
                    addMeshLog("SIMULATION", data.summary || "Two-node sim complete");
                    showToast("Simulation complete", "success");
                } else {
                    simContent.innerHTML = '<div class="sim-fail">' + (data.error || "Simulation failed") + '</div>';
                    showToast(data.error || "Simulation failed", "error");
                }
            }).catch(function(e) {
                simResult.style.display = "block";
                simContent.innerHTML = '<div class="sim-fail">Simulation error: ' + e.message + '</div>';
            }).finally(function() {
                meshSimulateBtn.disabled = false;
                meshSimulateBtn.textContent = "Run Two-Node Simulation";
            });
        });
    }

    if (document.getElementById("kinetic-log-btn")) {
        document.getElementById("kinetic-log-btn").addEventListener("click", async function() {
            var btn = this;
            var exercise = document.getElementById("kinetic-exercise").value;
            var reps = parseInt(document.getElementById("kinetic-reps").value) || 0;
            var duration_sec = parseFloat(document.getElementById("kinetic-duration").value) || 30;
            var heart_rate = parseInt(document.getElementById("kinetic-hr").value) || 0;

            if (reps <= 0) { showToast("Enter reps > 0", "error"); return; }

            btn.disabled = true;
            btn.textContent = "Logging...";

            try {
                var res = await fetch("/api/kinetic/log-set", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ exercise: exercise, reps: reps, duration_sec: duration_sec, heart_rate: heart_rate })
                });
                var data = await res.json();
                if (data.error) {
                    showToast("Kinetic: " + data.error, "error");
                } else {
                    showToast("Set logged! +" + (data.cc_earned || 0).toFixed(2) + " CC", "success");
                    refreshTransceiverStatus();
                }
            } catch(e) {
                showToast("Kinetic error: " + e.message, "error");
            }
            btn.disabled = false;
            btn.textContent = "Log Set";
        });
    }

    var bioSliders = ["bio-water", "bio-temp", "bio-ph", "bio-do"];
    var bioValIds = ["bio-water-val", "bio-temp-val", "bio-ph-val", "bio-do-val"];
    bioSliders.forEach(function(id, i) {
        var slider = document.getElementById(id);
        if (slider) {
            slider.addEventListener("input", function() {
                document.getElementById(bioValIds[i]).textContent = parseFloat(this.value).toFixed(id === "bio-water" ? 2 : 1);
            });
        }
    });

    if (document.getElementById("bio-update-btn")) {
        document.getElementById("bio-update-btn").addEventListener("click", async function() {
            var btn = this;
            btn.disabled = true;
            btn.textContent = "Updating...";
            try {
                var res = await fetch("/api/biological/update-sensors", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        water_level: parseFloat(document.getElementById("bio-water").value),
                        temperature: parseFloat(document.getElementById("bio-temp").value),
                        ph: parseFloat(document.getElementById("bio-ph").value),
                        dissolved_oxygen: parseFloat(document.getElementById("bio-do").value)
                    })
                });
                var data = await res.json();
                if (data.error) {
                    showToast("Biological: " + data.error, "error");
                } else {
                    showToast("Sensors updated", "success");
                    refreshTransceiverStatus();
                }
            } catch(e) {
                showToast("Biological error: " + e.message, "error");
            }
            btn.disabled = false;
            btn.textContent = "Update Sensors";
        });
    }

    if (document.getElementById("bio-govern-btn")) {
        document.getElementById("bio-govern-btn").addEventListener("click", async function() {
            var btn = this;
            btn.disabled = true;
            btn.textContent = "Triggering...";
            try {
                var res = await fetch("/api/biological/govern", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ intervention: "water_refill", reason: "Manual governance trigger" })
                });
                var data = await res.json();
                if (data.error) {
                    showToast("Governance: " + data.error, "error");
                } else {
                    showToast("Governance vote triggered", "success");
                    refreshTransceiverStatus();
                }
            } catch(e) {
                showToast("Governance error: " + e.message, "error");
            }
            btn.disabled = false;
            btn.textContent = "Trigger Governance Vote";
        });
    }

    async function refreshTransceiverStatus() {
        try {
            var [kinStatus, kinHistory, bioImp, bioHealth, ledgerStatus, ledgerChain, ledgerVotes] = await Promise.all([
                fetch("/api/kinetic/status").then(function(r) { return r.json(); }),
                fetch("/api/kinetic/history").then(function(r) { return r.json(); }),
                fetch("/api/biological/impedance").then(function(r) { return r.json(); }),
                fetch("/api/biological/health").then(function(r) { return r.json(); }),
                fetch("/api/ledger/status").then(function(r) { return r.json(); }),
                fetch("/api/ledger/chain?limit=20").then(function(r) { return r.json(); }),
                fetch("/api/ledger/votes").then(function(r) { return r.json(); })
            ]);

            var shimmer = (kinStatus.shimmer_alignment || 0) * 100;
            document.getElementById("kinetic-shimmer-bar").style.width = shimmer + "%";
            document.getElementById("kinetic-shimmer-val").textContent = shimmer.toFixed(0) + "%";
            document.getElementById("kinetic-cc-earned").textContent = (kinStatus.total_cc || 0).toFixed(2);
            document.getElementById("kinetic-stability-val").textContent = (kinStatus.stability_score || 0).toFixed(2);

            var glowEl = document.getElementById("kinetic-maxglow-indicator");
            if (kinStatus.max_glow) {
                glowEl.classList.add("active");
            } else {
                glowEl.classList.remove("active");
            }

            var sets = kinHistory.sets || kinHistory.history || [];
            var tbody = document.getElementById("kinetic-sets-body");
            if (sets.length === 0) {
                tbody.innerHTML = '<tr><td colspan="5" class="kinetic-empty">No sets logged yet</td></tr>';
            } else {
                tbody.innerHTML = sets.slice(-10).reverse().map(function(s) {
                    return '<tr>' +
                        '<td>' + (s.exercise || "—") + '</td>' +
                        '<td>' + (s.reps || 0) + '</td>' +
                        '<td>' + (s.cc_earned || 0).toFixed(2) + '</td>' +
                        '<td class="' + (s.harmonic_bonus && s.harmonic_bonus > 1 ? 'harmonic-yes' : 'harmonic-no') + '">' + (s.harmonic_bonus && s.harmonic_bonus > 1 ? s.harmonic_bonus.toFixed(1) + 'x' : '—') + '</td>' +
                        '<td class="' + (s.max_glow ? 'glow-yes' : 'glow-no') + '">' + (s.max_glow ? 'GLOW' : '—') + '</td>' +
                        '</tr>';
                }).join("");
            }

            var whaleVal = bioImp.whale_shelf != null ? bioImp.whale_shelf : 1;
            var birdVal = bioImp.bird_shelf != null ? bioImp.bird_shelf : 1;
            var insectVal = bioImp.insect_shelf != null ? bioImp.insect_shelf : 1;

            function setImpBar(barId, valId, val) {
                var bar = document.getElementById(barId);
                var valEl = document.getElementById(valId);
                bar.style.width = (val * 100) + "%";
                valEl.textContent = val.toFixed(2);
                bar.className = "bio-imp-bar" + (val < 0.3 ? " critical" : val < 0.6 ? " warning" : "");
                valEl.style.color = val < 0.3 ? "#f87171" : val < 0.6 ? "#fbbf24" : "#4ade80";
            }
            setImpBar("bio-imp-whale", "bio-imp-whale-val", whaleVal);
            setImpBar("bio-imp-bird", "bio-imp-bird-val", birdVal);
            setImpBar("bio-imp-insect", "bio-imp-insect-val", insectVal);

            var healthVal = bioHealth.composite_score != null ? bioHealth.composite_score : 1;
            var healthEl = document.getElementById("bio-health-val");
            healthEl.textContent = healthVal.toFixed(2);
            healthEl.style.color = healthVal < 0.3 ? "#f87171" : healthVal < 0.6 ? "#fbbf24" : "#4ade80";

            var alertsEl = document.getElementById("bio-alerts");
            var alerts = bioImp.alerts || [];
            alertsEl.innerHTML = alerts.length ? alerts.map(function(a) { return '<div style="color:' + (a.level === "CRITICAL" ? "#f87171" : "#fbbf24") + '">[' + (a.level || "WARN") + '] ' + (a.message || a) + '</div>'; }).join("") : "";

            document.getElementById("ledger-height").textContent = ledgerStatus.chain_height || 0;

            var integrityEl = document.getElementById("ledger-integrity");
            if (ledgerStatus.integrity_valid) {
                integrityEl.textContent = "VALID";
                integrityEl.style.color = "#4ade80";
            } else if (ledgerStatus.integrity_valid === false) {
                integrityEl.textContent = "BROKEN";
                integrityEl.style.color = "#f87171";
            } else {
                integrityEl.textContent = "—";
                integrityEl.style.color = "#4a9eff";
            }

            var honorScores = ledgerStatus.relay_honor || {};
            var honorKeys = Object.keys(honorScores);
            var honorText = honorKeys.length > 0 ? honorKeys.map(function(k) { return honorScores[k].toFixed(2); }).join(", ") : "—";
            document.getElementById("ledger-relay-honor").textContent = honorText;

            var vw = ledgerStatus.voting_weight || {};
            var totalWeight = (vw.total || 0);
            document.getElementById("ledger-vote-weight").textContent = totalWeight.toFixed(2);
            document.getElementById("ledger-weight-detail").textContent = "(K:" + (vw.kinetic || 0).toFixed(1) + " + B:" + (vw.biological || 0).toFixed(1) + " + R:" + (vw.relay || 0).toFixed(1) + ")";

            var blocks = ledgerChain.blocks || ledgerChain.chain || [];
            var blocksEl = document.getElementById("ledger-blocks-list");
            if (blocks.length === 0) {
                blocksEl.innerHTML = '<div class="ledger-empty">No blocks yet</div>';
            } else {
                blocksEl.innerHTML = blocks.slice(-15).reverse().map(function(b) {
                    var hashTail = b.block_hash ? "..." + b.block_hash.slice(-8) : "";
                    var payloadStr = "";
                    try {
                        payloadStr = typeof b.payload === "string" ? b.payload : JSON.stringify(b.payload).slice(0, 60);
                    } catch(e) { payloadStr = "—"; }
                    return '<div class="ledger-block-row">' +
                        '<span class="ledger-block-idx">#' + (b.block_index != null ? b.block_index : "?") + '</span>' +
                        '<span class="ledger-block-hash">' + hashTail + '</span>' +
                        '<span class="ledger-block-payload">' + payloadStr + '</span>' +
                        '<span class="ledger-block-node">' + (b.node_id ? b.node_id.slice(0, 12) : "") + '</span>' +
                        '</div>';
                }).join("");
            }

            var proposals = ledgerVotes.proposals || ledgerVotes.votes || [];
            var proposalsEl = document.getElementById("ledger-proposals-list");
            if (proposals.length === 0) {
                proposalsEl.innerHTML = '<div class="ledger-empty">No active proposals</div>';
            } else {
                proposalsEl.innerHTML = proposals.map(function(p) {
                    var statusClass = p.status === "passed" ? "passed" : "active";
                    return '<div class="ledger-proposal-row">' +
                        '<span class="ledger-proposal-text">' + (p.proposal || p.description || "—") + '</span>' +
                        '<span class="ledger-proposal-votes">' + (p.vote_count || 0) + ' votes (' + (p.weighted_score || 0).toFixed(2) + ')</span>' +
                        '<span class="ledger-proposal-status ' + statusClass + '">' + (p.status || "active") + '</span>' +
                        (p.status !== "passed" ? '<button class="btn-vote" onclick="voteOnProposal(\'' + (p.id || p.proposal_id || "") + '\')">Vote</button>' : '') +
                        '</div>';
                }).join("");
            }

            refreshResonanceContract();

        } catch(e) {}
    }

    async function refreshResonanceContract() {
        try {
            var data = await fetch("/api/resonance/evaluate").then(function(r) { return r.json(); });

            var freqEl = document.getElementById("resonance-freq-hz");
            var statusEl = document.getElementById("resonance-status");
            var circleEl = document.querySelector(".resonance-freq-circle");
            var freq = data.body_frequency || 0;
            freqEl.textContent = freq.toFixed(1);

            circleEl.classList.remove("full-resonance", "fading");
            if (data.contract_status === "FULL_RESONANCE") {
                circleEl.classList.add("full-resonance");
                statusEl.textContent = "FULL RESONANCE";
                statusEl.style.color = "#4ade80";
            } else if (data.contract_status === "FADING") {
                circleEl.classList.add("fading");
                statusEl.textContent = "FADING";
                statusEl.style.color = "#f87171";
            } else {
                statusEl.textContent = "PARTIAL RESONANCE";
                statusEl.style.color = "#fbbf24";
            }

            var scorePct = (data.resonance_score || 0) * 100;
            document.getElementById("resonance-score-fill").style.width = scorePct + "%";
            document.getElementById("resonance-score-pct").textContent = scorePct.toFixed(0) + "%";

            function updateAxiom(prefix, axiom) {
                document.getElementById("axiom-" + prefix + "-score").textContent = (axiom.score || 0).toFixed(2);
                document.getElementById("axiom-" + prefix + "-freq").textContent = (axiom.frequency_contribution || 0).toFixed(0) + " Hz";
                var statusEl = document.getElementById("axiom-" + prefix + "-status");
                statusEl.textContent = axiom.status || "—";
                if (axiom.status === "LOCKED" || axiom.status === "BLOOMING" || axiom.status === "CONNECTED" || axiom.status === "MAX_GLOW") {
                    statusEl.style.color = "#4ade80";
                } else if (axiom.status === "FADING" || axiom.status === "DARK" || axiom.status === "DORMANT" || axiom.status === "OFFLINE") {
                    statusEl.style.color = "#f87171";
                } else {
                    statusEl.style.color = "#fbbf24";
                }
                var detail = axiom.detail || {};
                var detailParts = [];
                Object.keys(detail).forEach(function(k) {
                    var v = detail[k];
                    if (typeof v === "number") v = v.toFixed(2);
                    detailParts.push(k.replace(/_/g, " ") + ": " + v);
                });
                document.getElementById("axiom-" + prefix + "-detail").textContent = detailParts.slice(0, 3).join(" | ") || "—";
            }

            if (data.kinetic_axiom) updateAxiom("kinetic", data.kinetic_axiom);
            if (data.biological_axiom) updateAxiom("bio", data.biological_axiom);
            if (data.relay_axiom) updateAxiom("relay", data.relay_axiom);

            document.getElementById("resonance-cc-rate").textContent = (data.total_cc_rate || 0).toFixed(2);
            document.getElementById("resonance-stability-tier").textContent = data.stability_tier || "Seedling";
            document.getElementById("resonance-stability-hours").textContent = (data.stability_hours || 0).toFixed(1) + "h";
            document.getElementById("resonance-contract-hash").textContent = data.contract_hash || "—";

            var statusRes = await fetch("/api/resonance/status").then(function(r) { return r.json(); });
            if (statusRes.bloom) {
                document.getElementById("resonance-bloom-cc").textContent = (statusRes.bloom.total_bloom_cc || 0).toFixed(2);
            }
            if (statusRes.relay) {
                document.getElementById("resonance-relay-cc").textContent = (statusRes.relay.total_relay_cc || 0).toFixed(2);
            }

        } catch(e) {}
    }

    window.harvestBloom = async function() {
        try {
            var res = await fetch("/api/resonance/harvest-bloom", {
                method: "POST",
                headers: { "Content-Type": "application/json" }
            });
            var data = await res.json();
            if (data.harvested) {
                showToast("Bloom harvested: " + (data.bloom.amount || 0).toFixed(4) + " CC (" + data.bloom.tier + ")", "success");
                refreshTransceiverStatus();
            } else {
                showToast("Bloom: " + (data.reason || "Not ready"), "error");
            }
        } catch(e) {
            showToast("Bloom error: " + e.message, "error");
        }
    };

    window.refreshResonance = async function() {
        await refreshResonanceContract();
        showToast("Resonance evaluated", "success");
    };

    window.voteOnProposal = async function(proposalId) {
        try {
            var res = await fetch("/api/ledger/vote", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ proposal_id: proposalId })
            });
            var data = await res.json();
            if (data.error) {
                showToast("Vote: " + data.error, "error");
            } else {
                showToast("Vote cast!", "success");
                refreshTransceiverStatus();
            }
        } catch(e) {
            showToast("Vote error: " + e.message, "error");
        }
    };

    document.getElementById("founder-export-seed-btn").addEventListener("click", function() {
        fetch("/api/harness/chronicle/export?mark_founder=true").then(r => r.json()).then(function(data) {
            var blob = new Blob([JSON.stringify(data, null, 2)], {type: "application/json"});
            var url = URL.createObjectURL(blob);
            var a = document.createElement("a");
            a.href = url;
            a.download = "founder_seed_" + (data.source_machine_id || "void") + ".json";
            a.click();
            URL.revokeObjectURL(url);
            showToast("Founder Seed exported — " + data.total_entries + " entries (Founder: " + data.founder_wisdom_count + ")", "success");
            loadFounderStatus();
        }).catch(function() {
            showToast("Export failed", "error");
        });
    });

    var lightbox = document.getElementById("blueprint-lightbox");
    var lightboxImg = document.getElementById("lightbox-img");
    document.querySelectorAll(".blueprint-schematic[data-lightbox]").forEach(function(el) {
        el.addEventListener("click", function() {
            lightboxImg.src = el.getAttribute("data-lightbox");
            lightbox.style.display = "flex";
        });
    });
    if (lightbox) {
        lightbox.addEventListener("click", function() {
            lightbox.style.display = "none";
            lightboxImg.src = "";
        });
        document.addEventListener("keydown", function(e) {
            if (e.key === "Escape" && lightbox.style.display === "flex") {
                lightbox.style.display = "none";
                lightboxImg.src = "";
            }
        });
    }

    var journalismFile = null;
    var journalismDropzone = document.getElementById("journalism-dropzone");
    var journalismFileInput = document.getElementById("journalism-file-input");
    var journalismFileName = document.getElementById("journalism-file-name");
    var journalismEncodeBtn = document.getElementById("journalism-encode-btn");

    if (journalismDropzone) {
        journalismDropzone.addEventListener("click", function() {
            journalismFileInput.click();
        });
        journalismDropzone.addEventListener("dragover", function(e) {
            e.preventDefault();
            journalismDropzone.classList.add("drag-over");
        });
        journalismDropzone.addEventListener("dragleave", function() {
            journalismDropzone.classList.remove("drag-over");
        });
        journalismDropzone.addEventListener("drop", function(e) {
            e.preventDefault();
            journalismDropzone.classList.remove("drag-over");
            if (e.dataTransfer.files.length > 0) {
                journalismFile = e.dataTransfer.files[0];
                journalismFileName.textContent = journalismFile.name + " (" + formatSize(journalismFile.size) + ")";
                journalismEncodeBtn.disabled = false;
            }
        });
        journalismFileInput.addEventListener("change", function() {
            if (journalismFileInput.files.length > 0) {
                journalismFile = journalismFileInput.files[0];
                journalismFileName.textContent = journalismFile.name + " (" + formatSize(journalismFile.size) + ")";
                journalismEncodeBtn.disabled = false;
            }
        });
    }

    if (journalismEncodeBtn) {
        journalismEncodeBtn.addEventListener("click", function() {
            if (!journalismFile) return;
            if (isDemo && journalismFile.size > 1048576) {
                showToast("Demo mode: file limit is 1 MB. Get full access for up to 50 MB.", "error");
                return;
            }
            var style = document.getElementById("journalism-style-select").value;
            var formData = new FormData();
            formData.append("file", journalismFile);
            formData.append("style", style);

            journalismEncodeBtn.disabled = true;
            journalismEncodeBtn.textContent = "Sinking into Silt...";
            document.getElementById("journalism-result").style.display = "none";
            _activateResonance('journalism', '', 'encoding');

            fetch("/api/journalism/encode", { method: "POST", body: formData })
                .then(function(r) { return r.json(); })
                .then(function(data) {
                    journalismEncodeBtn.disabled = false;
                    journalismEncodeBtn.textContent = "Sink into Silt";
                    if (data.error) {
                        showToast(data.error, "error");
                        _deactivateResonance('journalism');
                        return;
                    }
                    document.getElementById("journalism-result").style.display = "block";
                    document.getElementById("journalism-out-file").textContent = data.output_file;
                    document.getElementById("journalism-hash-key").textContent = data.hash_key;
                    document.getElementById("journalism-orig-size").textContent = formatSize(data.original_size);
                    document.getElementById("journalism-comp-size").textContent = formatSize(data.compressed_size);
                    document.getElementById("journalism-wav-size").textContent = formatSize(data.output_size);
                    document.getElementById("journalism-carrier-style").textContent = data.carrier_style;
                    document.getElementById("journalism-scatter").textContent = data.scatter_mode;
                    document.getElementById("journalism-duration").textContent = data.carrier_duration_min + " min";
                    _pulseResonance('journalism', data.hash_key);
                    _renderResonanceBadge('journalism-resonance-badge', data.hash_key);
                    _deactivateResonance('journalism', 2500);

                    document.getElementById("journalism-download-btn").onclick = function() {
                        window.location.href = "/api/journalism/download/" + encodeURIComponent(data.output_file);
                    };
                    document.getElementById("journalism-broadcast-btn").onclick = function() {
                        fetch("/api/mesh/broadcast", {
                            method: "POST",
                            headers: { "Content-Type": "application/json" },
                            body: JSON.stringify({ filename: data.output_file, source: "silt_drops" })
                        }).then(function(r) { return r.json(); })
                          .then(function(d) { showToast(d.success ? "Broadcast queued to mesh" : (d.error || "Broadcast failed"), d.success ? "success" : "error"); })
                          .catch(function() { showToast("Mesh broadcast failed", "error"); });
                    };

                    showToast("Silt drop ready — " + data.output_file, "success");
                    if (isDemo) {
                        showToast("Your file is hidden in nature sounds. Get full access for mesh broadcast, 50MB uploads, and all modules.", "success", 10000);
                    }
                    loadSiltDrops();
                    journalismFile = null;
                    journalismFileName.textContent = "";
                    journalismFileInput.value = "";
                })
                .catch(function() {
                    journalismEncodeBtn.disabled = false;
                    journalismEncodeBtn.textContent = "Sink into Silt";
                    showToast("Silt encoding failed", "error");
                    _deactivateResonance('journalism');
                });
        });
    }

    var journalismHashEl = document.getElementById("journalism-hash-key");
    if (journalismHashEl) {
        journalismHashEl.addEventListener("click", function() {
            var key = journalismHashEl.textContent;
            if (key && key !== "—") {
                navigator.clipboard.writeText(key).then(function() {
                    showToast("286-bit key copied", "success");
                }).catch(function() {
                    showToast("Copy failed", "error");
                });
            }
        });
    }

    function loadSiltDrops() {
        var list = document.getElementById("journalism-drops-list");
        if (!list) return;
        fetch("/api/journalism/drops")
            .then(function(r) { return r.json(); })
            .then(function(data) {
                if (!data.drops || data.drops.length === 0) {
                    list.innerHTML = '<p class="loading">No drops yet.</p>';
                    return;
                }
                var html = "";
                data.drops.forEach(function(d) {
                    html += '<div class="journalism-drop-row">';
                    html += '<span class="journalism-drop-name" title="' + d.name + '">' + d.name + '</span>';
                    html += '<span class="journalism-drop-meta">' + formatSize(d.size) + ' &middot; ' + d.modified + '</span>';
                    html += '<div class="journalism-drop-actions">';
                    html += '<button onclick="window._downloadSiltDrop(\'' + d.name + '\')">Download</button>';
                    html += '<button onclick="window._deleteSiltDrop(\'' + d.name + '\')">Delete</button>';
                    html += '</div></div>';
                });
                list.innerHTML = html;
            })
            .catch(function() {
                list.innerHTML = '<p class="loading">Failed to load drops.</p>';
            });
    }

    window._downloadSiltDrop = function(name) {
        window.location.href = "/api/journalism/download/" + encodeURIComponent(name);
    };

    window._deleteSiltDrop = function(name) {
        if (!confirm("Delete silt drop: " + name + "?")) return;
        fetch("/api/journalism/delete/" + encodeURIComponent(name), { method: "DELETE" })
            .then(function(r) { return r.json(); })
            .then(function(data) {
                showToast(data.success ? "Deleted " + name : (data.error || "Delete failed"), data.success ? "success" : "error");
                loadSiltDrops();
            })
            .catch(function() { showToast("Delete failed", "error"); });
    };

    var journalismRefreshBtn = document.getElementById("journalism-refresh-btn");
    if (journalismRefreshBtn) {
        journalismRefreshBtn.addEventListener("click", loadSiltDrops);
    }

    var journalismPurgeBtn = document.getElementById("journalism-purge-btn");
    if (journalismPurgeBtn) {
        journalismPurgeBtn.addEventListener("click", function() {
            if (!confirm("Purge ALL silt drops? This cannot be undone.")) return;
            fetch("/api/journalism/purge", { method: "DELETE" })
                .then(function(r) { return r.json(); })
                .then(function(data) {
                    showToast(data.success ? "Purged " + data.purged + " drops" : "Purge failed", data.success ? "success" : "error");
                    loadSiltDrops();
                })
                .catch(function() { showToast("Purge failed", "error"); });
        });
    }

    var journalismDecodeBtn = document.getElementById("journalism-decode-btn");
    if (journalismDecodeBtn) {
        journalismDecodeBtn.addEventListener("click", function() {
            var filename = document.getElementById("journalism-decode-file").value.trim();
            var hashKey = document.getElementById("journalism-decode-key").value.trim();
            if (!filename || !hashKey) {
                showToast("Provide both filename and hash key", "error");
                return;
            }
            fetch("/api/journalism/decode", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ filename: filename, hash_key: hashKey })
            })
                .then(function(r) { return r.json(); })
                .then(function(data) {
                    var result = document.getElementById("journalism-decode-result");
                    if (data.error) {
                        result.style.display = "block";
                        result.innerHTML = '<span style="color:#ef4444;">Error: ' + data.error + '</span>';
                        return;
                    }
                    result.style.display = "block";
                    result.innerHTML = 'Extracted: <strong>' + data.filename + '</strong> (' + formatSize(data.size) + ') — <a href="' + data.download_url + '" style="color:#2dd4bf;">Download</a>';
                    showToast("File extracted from silt", "success");
                })
                .catch(function() { showToast("Decode failed", "error"); });
        });
    }

    var proofRunBtn = document.getElementById("proof-run-btn");
    var proofLastFile = null;

    function setProofStepState(stepNum, state) {
        var el = document.getElementById("proof-step-" + stepNum);
        if (!el) return;
        el.className = "proof-step" + (state ? " proof-step-" + state : "");
    }

    function resetProofSteps() {
        for (var i = 1; i <= 5; i++) setProofStepState(i, "");
    }

    function animateProofSteps(stepIndex) {
        if (stepIndex > 5) return;
        for (var i = 1; i <= 5; i++) {
            if (i < stepIndex) setProofStepState(i, "done");
            else if (i === stepIndex) setProofStepState(i, "active");
            else setProofStepState(i, "");
        }
    }

    if (proofRunBtn) {
        proofRunBtn.addEventListener("click", async function() {
            var btn = proofRunBtn;
            var progressEl = document.getElementById("proof-progress");
            var progressFill = document.getElementById("proof-progress-fill");
            var progressText = document.getElementById("proof-progress-text");
            var resultEl = document.getElementById("proof-result");
            var errorEl = document.getElementById("proof-error");

            btn.disabled = true;
            btn.innerHTML = '<span class="spinner"></span>Running Proof...';
            resultEl.style.display = "none";
            errorEl.style.display = "none";
            progressEl.style.display = "block";
            progressFill.style.width = "0%";
            progressText.textContent = "Initializing proof workflow...";
            _activateResonance('proof', '', 'encoding');
            resetProofSteps();

            var stepTimers = [
                { step: 1, pct: 10, text: "Generating Midnight Pond carrier...", delay: 500 },
                { step: 2, pct: 25, text: "Creating sample payload...", delay: 2000 },
                { step: 3, pct: 50, text: "Encoding with Vortex scatter at LSB-2...", delay: 4000 },
                { step: 4, pct: 70, text: "Analyzing capacity...", delay: 6000 },
                { step: 5, pct: 85, text: "Decoding and verifying integrity...", delay: 8000 }
            ];

            var stepIntervals = [];
            stepTimers.forEach(function(s) {
                var tid = setTimeout(function() {
                    animateProofSteps(s.step);
                    progressFill.style.width = s.pct + "%";
                    progressText.textContent = s.text;
                }, s.delay);
                stepIntervals.push(tid);
            });

            try {
                var res = await fetch("/api/demo/proof", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({})
                });
                var data = await res.json();

                stepIntervals.forEach(function(tid) { clearTimeout(tid); });

                if (data.success) {
                    for (var i = 1; i <= 5; i++) setProofStepState(i, "done");
                    progressFill.style.width = "100%";
                    progressText.textContent = "Proof complete!";

                    document.getElementById("proof-res-id").textContent = data.proof_id;
                    document.getElementById("proof-res-carrier-size").textContent = formatSize(data.carrier_size);
                    document.getElementById("proof-res-payload-size").textContent = formatSize(data.payload_size);
                    document.getElementById("proof-res-compressed").textContent = formatSize(data.compressed_size);
                    document.getElementById("proof-res-ratio").textContent = data.compression_ratio + "%";
                    document.getElementById("proof-res-scatter").textContent = "Vortex (432 Hz spiral)";
                    document.getElementById("proof-res-lsb").textContent = "LSB-" + data.lsb_depth;
                    document.getElementById("proof-res-capacity-used").textContent = formatSize(data.capacity_used) + " (" + data.capacity_used_pct + "%)";
                    document.getElementById("proof-res-capacity-remain").textContent = formatSize(data.capacity_remaining);

                    var integrityEl = document.getElementById("proof-res-integrity");
                    integrityEl.textContent = data.integrity_check;
                    integrityEl.className = data.integrity_check === "PASS" ? "value verified" : "value" ;

                    document.getElementById("proof-res-hash").textContent = data.hash_key;

                    var capBarFill = document.getElementById("proof-capacity-bar-fill");
                    capBarFill.style.width = Math.min(data.capacity_used_pct, 100) + "%";
                    document.getElementById("proof-capacity-bar-text").textContent = data.capacity_used_pct + "% used";

                    proofLastFile = data.output_file;
                    resultEl.style.display = "block";
                    showToast("Live Proof complete — integrity " + data.integrity_check, "success");
                    _pulseResonance('proof', data.hash_key);
                    _renderResonanceBadge('proof-resonance-badge', data.hash_key);
                    _deactivateResonance('proof', 2500);
                } else {
                    resetProofSteps();
                    errorEl.innerHTML = '<div class="error-title">Error</div>' + (data.error || "Unknown error");
                    errorEl.style.display = "block";
                    showToast("Proof failed", "error");
                    _deactivateResonance('proof');
                }
            } catch(e) {
                stepIntervals.forEach(function(tid) { clearTimeout(tid); });
                resetProofSteps();
                errorEl.innerHTML = '<div class="error-title">Error</div>Request failed: ' + e.message;
                errorEl.style.display = "block";
                showToast("Proof failed", "error");
                _deactivateResonance('proof');
            }

            setTimeout(function() { progressEl.style.display = "none"; }, 2000);
            btn.disabled = false;
            btn.textContent = "Run Live Proof";
        });
    }

    var copyProofHashBtn = document.getElementById("copy-proof-hash-btn");
    if (copyProofHashBtn) {
        copyProofHashBtn.addEventListener("click", function() {
            var key = document.getElementById("proof-res-hash").textContent;
            navigator.clipboard.writeText(key).then(function() {
                showToast("Hash Key copied!", "success");
            }).catch(function() {
                var ta = document.createElement("textarea");
                ta.value = key;
                document.body.appendChild(ta);
                ta.select();
                document.execCommand("copy");
                document.body.removeChild(ta);
                showToast("Hash Key copied!", "success");
            });
        });
    }

    var downloadProofBtn = document.getElementById("download-proof-btn");
    if (downloadProofBtn) {
        downloadProofBtn.addEventListener("click", function() {
            if (proofLastFile) window.open("/api/download/output_audio/" + proofLastFile, "_blank");
        });
    }

    var demoInquiryForm = document.getElementById("demo-inquiry-form");
    var demoInquiryClose = document.getElementById("demo-inquiry-close");
    var demoInquiryBanner = document.getElementById("demo-inquiry-banner");

    if (demoInquiryClose && demoInquiryBanner) {
        demoInquiryClose.addEventListener("click", function() {
            demoInquiryBanner.classList.add("hidden");
        });
    }

    if (demoInquiryForm) {
        demoInquiryForm.addEventListener("submit", async function(e) {
            e.preventDefault();
            var submitBtn = demoInquiryForm.querySelector(".demo-inquiry-submit");
            submitBtn.disabled = true;
            submitBtn.textContent = "Sending...";

            var payload = {
                name: document.getElementById("demo-inq-name").value.trim(),
                email: document.getElementById("demo-inq-email").value.trim(),
                message: document.getElementById("demo-inq-message").value.trim(),
                organisation: document.getElementById("demo-inq-org").value.trim(),
                interest: document.getElementById("demo-inq-interest").value,
                type: "demo",
                source_page: "demo",
                consent: document.getElementById("demo-inq-consent").checked
            };

            try {
                var res = await fetch("/api/inquiry", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload)
                });
                var data = await res.json();
                if (data.success) {
                    demoInquiryForm.style.display = "none";
                    document.getElementById("demo-inquiry-success").style.display = "block";
                    showToast("Inquiry submitted!", "success");
                } else {
                    showToast(data.error || "Submission failed", "error");
                    submitBtn.disabled = false;
                    submitBtn.textContent = "Send Inquiry";
                }
            } catch (err) {
                showToast("Submission failed: " + err.message, "error");
                submitBtn.disabled = false;
                submitBtn.textContent = "Send Inquiry";
            }
        });
    }

    // ── Vigilance Board ──
    var vigSubmitBtn = document.getElementById("vig-submit-btn");
    if (vigSubmitBtn) {
        vigSubmitBtn.addEventListener("click", async function() {
            var title = document.getElementById("vig-title").value.trim();
            var severity = document.getElementById("vig-severity").value;
            var category = document.getElementById("vig-category").value;
            var description = document.getElementById("vig-description").value.trim();
            var steps = document.getElementById("vig-steps").value.trim();
            var statusEl = document.getElementById("vig-submit-status");

            if (!title || title.length < 5) { showToast("Title must be at least 5 characters", "error"); return; }
            if (!description || description.length < 20) { showToast("Description must be at least 20 characters", "error"); return; }

            vigSubmitBtn.disabled = true;
            vigSubmitBtn.textContent = "Submitting...";
            try {
                var res = await fetch("/api/vigilance/report", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ title: title, severity: severity, category: category, description: description, steps_to_reproduce: steps })
                });
                var data = await res.json();
                if (data.error) {
                    showToast(data.error, "error");
                } else {
                    showToast("Report #" + data.id + " submitted — potential bounty: " + data.bounty_potential + " VTX", "success");
                    document.getElementById("vig-title").value = "";
                    document.getElementById("vig-description").value = "";
                    document.getElementById("vig-steps").value = "";
                    _activateResonance('vigilance', title, 'vigilance');
                    _pulseResonance('vigilance', title);
                    _deactivateResonance('vigilance', 2500);
                    loadVigMyReports();
                    loadVigStats();
                }
            } catch(e) { showToast("Error: " + e.message, "error"); }
            vigSubmitBtn.disabled = false;
            vigSubmitBtn.textContent = "Submit Report";
        });
    }

    async function loadVigMyReports() {
        var el = document.getElementById("vig-my-reports");
        if (!el) return;
        try {
            var res = await fetch("/api/vigilance/my-reports");
            var data = await res.json();
            if (!data.reports || data.reports.length === 0) {
                el.innerHTML = '<p class="text-dim">No reports submitted yet. Be the first vigilant.</p>';
                return;
            }
            el.innerHTML = '<table class="vig-table"><thead><tr><th>#</th><th>Title</th><th>Severity</th><th>Status</th><th>Reward</th><th>Date</th></tr></thead><tbody>' +
                data.reports.map(function(r) {
                    var rewarded = r.status === 'rewarded';
                    return '<tr>' +
                        '<td>' + r.id + '</td>' +
                        '<td class="vig-report-title">' + _escHtml(r.title) + '</td>' +
                        '<td><span class="vig-sev vig-sev-' + r.severity + '">' + r.severity + '</span></td>' +
                        '<td><span class="vig-status vig-status-' + r.status + '">' + r.status + '</span></td>' +
                        '<td>' + (rewarded ? '<span class="vig-vtx-reward">' + r.vtx_reward + ' VTX</span>' : '—') + '</td>' +
                        '<td class="text-dim">' + (r.created_at ? r.created_at.substring(0,10) : '') + '</td>' +
                    '</tr>';
                }).join("") + '</tbody></table>';
        } catch(e) { el.innerHTML = '<p class="text-dim">Failed to load reports.</p>'; }
    }

    async function loadVigLeaderboard() {
        var el = document.getElementById("vig-leaderboard");
        if (!el) return;
        try {
            var res = await fetch("/api/vigilance/leaderboard");
            var data = await res.json();
            if (!data.leaderboard || data.leaderboard.length === 0) {
                el.innerHTML = '<p class="text-dim">No bug hunters yet.</p>';
                return;
            }
            el.innerHTML = data.leaderboard.map(function(e) {
                var medal = e.rank <= 3 ? ['', '\u2B50', '\u26A1', '\u2B55'][e.rank] : '';
                return '<div class="vig-lb-row">' +
                    '<span class="vig-lb-rank">' + medal + ' #' + e.rank + '</span>' +
                    '<span class="vig-lb-name">' + _escHtml(e.username) + '</span>' +
                    '<span class="vig-lb-stats">' + e.rewarded_count + '/' + e.report_count + ' verified</span>' +
                    '<span class="vig-lb-vtx">' + e.total_vtx.toFixed(1) + ' VTX</span>' +
                '</div>';
            }).join("");
        } catch(e) { el.innerHTML = '<p class="text-dim">Failed to load leaderboard.</p>'; }
    }

    async function loadVigStats() {
        var el = document.getElementById("vig-stats");
        if (!el) return;
        try {
            var res = await fetch("/api/vigilance/stats");
            var data = await res.json();
            el.innerHTML =
                '<div class="vig-stat"><span class="vig-stat-val">' + data.total_reports + '</span><span class="vig-stat-lbl">Reports</span></div>' +
                '<div class="vig-stat"><span class="vig-stat-val">' + (data.by_status.rewarded || 0) + '</span><span class="vig-stat-lbl">Verified</span></div>' +
                '<div class="vig-stat"><span class="vig-stat-val">' + (data.by_status.pending || 0) + '</span><span class="vig-stat-lbl">Pending</span></div>' +
                '<div class="vig-stat"><span class="vig-stat-val">' + data.total_vtx_paid.toFixed(1) + '</span><span class="vig-stat-lbl">VTX Paid</span></div>';
        } catch(e) { el.innerHTML = '<p class="text-dim">Failed to load stats.</p>'; }
    }

    function _escHtml(s) { var d = document.createElement('div'); d.textContent = s; return d.innerHTML; }

    var vigTab = document.querySelector('[data-tab="vigilance"]');
    if (vigTab) {
        vigTab.addEventListener("click", function() {
            loadVigMyReports();
            loadVigLeaderboard();
            loadVigStats();
        });
    }

    var userTier = document.body.getAttribute('data-tier') || 'ghost';
    var origFetch = window.fetch;
    window.fetch = function() {
        return origFetch.apply(this, arguments).then(function(resp) {
            if (resp.status === 403 || resp.status === 413) {
                var clone = resp.clone();
                clone.json().then(function(data) {
                    if (data.upgrade) {
                        showToast(data.error + ' <a href="/pricing" style="color:#c9a84c;text-decoration:underline;">Upgrade</a>', 'error');
                    }
                }).catch(function() {});
            }
            return resp;
        });
    };

    window.VoidState = {
        vtxBalance: null,
        userTier: userTier,
        engineOnline: true,
        meshConnected: false,
        _pollTimer: null,
        _visHandler: null,

        async refreshBalance() {
            try {
                var balEl = document.getElementById('vcb-vtx-balance');
                if (balEl) balEl.classList.add('updating');
                var res = await origFetch('/api/wallet/balance');
                if (res.ok) {
                    var data = await res.json();
                    this.vtxBalance = data.balance;
                    this.userTier = data.tier || this.userTier;
                    if (balEl) {
                        balEl.textContent = (typeof data.balance === 'number') ? data.balance.toFixed(1) : data.balance;
                        setTimeout(function() { balEl.classList.remove('updating'); }, 400);
                    }
                    var tierEl = document.getElementById('vcb-tier-badge');
                    if (tierEl) tierEl.textContent = (data.tier || this.userTier).toUpperCase();
                } else {
                    if (balEl) balEl.classList.remove('updating');
                }
            } catch(e) {
                var balEl2 = document.getElementById('vcb-vtx-balance');
                if (balEl2) balEl2.classList.remove('updating');
            }
        },

        async refreshMeshStatus() {
            var meshDot = document.getElementById('vcb-mesh-status');
            if (!meshDot) return;
            try {
                var res = await origFetch('/api/mesh/status');
                if (res.ok) {
                    var data = await res.json();
                    this.meshConnected = !!(data.connected || data.is_connected);
                    var dot = meshDot.querySelector('.vcb-mesh-dot');
                    if (dot) {
                        if (this.meshConnected) dot.classList.add('connected');
                        else dot.classList.remove('connected');
                    }
                }
            } catch(e) {}
        },

        async refreshEngineStatus() {
            try {
                var res = await origFetch('/api/status');
                if (res.ok) {
                    this.engineOnline = true;
                    var dot = document.getElementById('vcb-engine-status');
                    var lbl = document.getElementById('vcb-engine-label');
                    if (dot) dot.classList.remove('offline');
                    if (lbl) lbl.textContent = 'Engine Active';
                } else {
                    this.engineOnline = false;
                    var dot2 = document.getElementById('vcb-engine-status');
                    var lbl2 = document.getElementById('vcb-engine-label');
                    if (dot2) dot2.classList.add('offline');
                    if (lbl2) lbl2.textContent = 'Engine Offline';
                }
            } catch(e) {
                this.engineOnline = false;
                var dot3 = document.getElementById('vcb-engine-status');
                var lbl3 = document.getElementById('vcb-engine-label');
                if (dot3) dot3.classList.add('offline');
                if (lbl3) lbl3.textContent = 'Engine Offline';
            }
        },

        async refreshAll() {
            await Promise.all([
                this.refreshBalance(),
                this.refreshMeshStatus(),
                this.refreshEngineStatus()
            ]);
        },

        startPolling() {
            var self = this;
            self.refreshAll();
            self._pollTimer = setInterval(function() { self.refreshAll(); }, 60000);
            self._visHandler = function() {
                if (!document.hidden) self.refreshAll();
            };
            document.addEventListener('visibilitychange', self._visHandler);
        }
    };

    if (!isDemo) {
        window.VoidState.startPolling();
    }

    tabs.forEach(function(tab) {
        tab.addEventListener('click', function() {
            if (!isDemo && window.VoidState) window.VoidState.refreshBalance();
        });
    });

    var _cmdActions = [
        { id: 'encode', icon: '\u25C6', name: 'Encode', desc: 'Hide a file inside audio', tab: 'encode' },
        { id: 'decode', icon: '\u25C7', name: 'Decode', desc: 'Extract a file from audio', tab: 'decode' },
        { id: 'burst', icon: '\u26A1', name: 'Burst Signal', desc: 'Quick short signal encoding', tab: 'burst' },
        { id: 'visualizer', icon: '\u223F', name: 'Visualizer', desc: '432 Hz frequency spectrum', tab: 'visualizer' },
        { id: 'capacity', icon: '\u2261', name: 'Capacity', desc: 'Carrier capacity analysis', tab: 'capacity' },
        { id: 'silk', icon: '\u2042', name: 'Silk Web', desc: 'Signal relay network', tab: 'silk' },
        { id: 'mesh', icon: '\u2A2F', name: 'Mesh', desc: 'Ghost Internet mesh network', tab: 'mesh' },
        { id: 'transceiver', icon: '\u2B21', name: 'Transceiver', desc: 'Signal transceiver control', tab: 'transceiver' },
        { id: 'blueprint', icon: '\u2B22', name: 'Blueprint', desc: 'Hardware schematics', tab: 'blueprint' },
        { id: 'journalism', icon: '\u270E', name: 'Journalism', desc: 'Silt journalism drops', tab: 'journalism' },
        { id: 'proof', icon: '\u2713', name: 'Live Proof', desc: 'Live proof panel', tab: 'proof' },
        { id: 'files', icon: '\u2191', name: 'Files', desc: 'File manager', tab: 'files' },
        { id: 'harness', icon: '\u2699', name: 'Harness', desc: 'Plankton-Orin harness', tab: 'harness' },
        { id: 'vigilance', icon: '\u2691', name: 'Vigilance', desc: 'Bug bounty board', tab: 'vigilance' },
        { id: 'wallet', icon: '\u25C6', name: 'Wallet', desc: 'VTX wallet & balance', url: '/pricing' },
        { id: 'gift', icon: '\u2661', name: 'Gift VTX', desc: 'Send VTX to another user', url: '/messenger' },
        { id: 'messenger', icon: '\u2709', name: 'Messenger', desc: 'Encrypted messaging', url: '/messenger' },
        { id: 'sovereign', icon: '\u2B50', name: 'Sovereign', desc: 'Sovereign hardware page', url: '/sovereign' },
        { id: 'pricing', icon: '\u2B50', name: 'Pricing', desc: 'Tier pricing page', url: '/pricing' },
        { id: 'grants', icon: '\u2606', name: 'Grants', desc: 'Grant applications', url: '/grants' },
        { id: 'guide', icon: '\u2139', name: 'Guide', desc: 'User guide', url: '/guide' }
    ];

    var _cmdOverlay = document.getElementById('void-cmd-overlay');
    var _cmdInput = document.getElementById('void-cmd-input');
    var _cmdResults = document.getElementById('void-cmd-results');
    var _cmdSelectedIdx = -1;

    function _cmdFuzzyMatch(query, text) {
        query = query.toLowerCase();
        text = text.toLowerCase();
        if (text.indexOf(query) !== -1) return true;
        var qi = 0;
        for (var ti = 0; ti < text.length && qi < query.length; ti++) {
            if (text[ti] === query[qi]) qi++;
        }
        return qi === query.length;
    }

    function _cmdRender(query) {
        var filtered = _cmdActions;
        if (query) {
            filtered = _cmdActions.filter(function(a) {
                return _cmdFuzzyMatch(query, a.name) || _cmdFuzzyMatch(query, a.desc) || _cmdFuzzyMatch(query, a.id);
            });
        }
        _cmdSelectedIdx = filtered.length > 0 ? 0 : -1;
        _cmdResults.innerHTML = filtered.map(function(a, i) {
            return '<div class="void-cmd-item' + (i === 0 ? ' selected' : '') + '" data-idx="' + i + '" data-action-id="' + a.id + '">' +
                '<span class="void-cmd-item-icon">' + a.icon + '</span>' +
                '<div class="void-cmd-item-text">' +
                    '<div class="void-cmd-item-name">' + a.name + '</div>' +
                    '<div class="void-cmd-item-desc">' + a.desc + '</div>' +
                '</div>' +
                (a.tab ? '<span class="void-cmd-item-shortcut">TAB</span>' : '<span class="void-cmd-item-shortcut">NAV</span>') +
            '</div>';
        }).join('');
        _cmdResults.querySelectorAll('.void-cmd-item').forEach(function(el) {
            el.addEventListener('click', function() {
                var aid = el.dataset.actionId;
                _cmdExecuteAction(aid);
            });
        });
    }

    function _cmdExecuteAction(actionId) {
        var action = _cmdActions.find(function(a) { return a.id === actionId; });
        if (!action) return;
        _cmdClose();
        if (action.tab) {
            var tabBtn = document.querySelector('.tab[data-tab="' + action.tab + '"]');
            if (tabBtn) tabBtn.click();
        } else if (action.url) {
            window.location.href = action.url;
        }
    }

    function _cmdOpen() {
        if (!_cmdOverlay) return;
        _cmdOverlay.style.display = 'flex';
        _cmdInput.value = '';
        _cmdRender('');
        setTimeout(function() { _cmdInput.focus(); }, 50);
    }

    function _cmdClose() {
        if (!_cmdOverlay) return;
        _cmdOverlay.style.display = 'none';
        _cmdInput.value = '';
    }

    if (_cmdInput) {
        _cmdInput.addEventListener('input', function() {
            _cmdRender(_cmdInput.value.trim());
        });

        _cmdInput.addEventListener('keydown', function(e) {
            var items = _cmdResults.querySelectorAll('.void-cmd-item');
            if (e.key === 'ArrowDown') {
                e.preventDefault();
                if (_cmdSelectedIdx < items.length - 1) _cmdSelectedIdx++;
                items.forEach(function(el, i) { el.classList.toggle('selected', i === _cmdSelectedIdx); });
                if (items[_cmdSelectedIdx]) items[_cmdSelectedIdx].scrollIntoView({ block: 'nearest' });
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                if (_cmdSelectedIdx > 0) _cmdSelectedIdx--;
                items.forEach(function(el, i) { el.classList.toggle('selected', i === _cmdSelectedIdx); });
                if (items[_cmdSelectedIdx]) items[_cmdSelectedIdx].scrollIntoView({ block: 'nearest' });
            } else if (e.key === 'Enter') {
                e.preventDefault();
                if (_cmdSelectedIdx >= 0 && items[_cmdSelectedIdx]) {
                    var aid = items[_cmdSelectedIdx].dataset.actionId;
                    _cmdExecuteAction(aid);
                }
            } else if (e.key === 'Escape') {
                _cmdClose();
            }
        });
    }

    if (_cmdOverlay) {
        _cmdOverlay.addEventListener('click', function(e) {
            if (e.target === _cmdOverlay) _cmdClose();
        });
    }

    document.addEventListener('keydown', function(e) {
        if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
            e.preventDefault();
            if (_cmdOverlay && _cmdOverlay.style.display !== 'none') {
                _cmdClose();
            } else {
                _cmdOpen();
            }
        }
        if (e.key === 'Escape' && _cmdOverlay && _cmdOverlay.style.display !== 'none') {
            _cmdClose();
        }
    });

    var cmdKBtn = document.getElementById('vcb-cmd-k-btn');
    if (cmdKBtn) {
        cmdKBtn.addEventListener('click', function() { _cmdOpen(); });
    }

    var _sovOnboardingSteps = [
        {
            text: "Welcome home, Sovereign. Let me show you what your tier unlocks.",
            highlight: '#void-command-bar'
        },
        {
            text: "The Mesh is yours to command. Host a node and join the Ghost Internet.",
            highlight: '.tab[data-tab="mesh"]'
        },
        {
            text: "Your Adriana learns your language. Speak naturally \u2014 she will mirror your resonance.",
            highlight: '#resonance-handshake-btn'
        },
        {
            text: "The Handshake proves your machine\u2019s identity. Try it now.",
            highlight: '#resonance-handshake-btn'
        }
    ];

    var _sovCurrentStep = 0;
    var _sovTypingTimer = null;
    var _sovHighlightedEl = null;

    function _sovGetStorageKey() {
        var username = document.body.getAttribute('data-username') || '';
        return 'void_sovereign_onboarded' + (username ? '_' + username : '');
    }

    function _sovShouldShow() {
        var tier = document.body.getAttribute('data-tier');
        if (tier !== 'sovereign') return false;
        if (isDemo) return false;
        try {
            return !localStorage.getItem(_sovGetStorageKey());
        } catch(e) {
            return false;
        }
    }

    function _sovTypeText(el, text, cb) {
        el.innerHTML = '';
        var idx = 0;
        var cursor = document.createElement('span');
        cursor.className = 'sov-cursor';
        el.appendChild(cursor);

        function typeNext() {
            if (idx < text.length) {
                var charNode = document.createTextNode(text[idx]);
                el.insertBefore(charNode, cursor);
                idx++;
                _sovTypingTimer = setTimeout(typeNext, 35);
            } else {
                setTimeout(function() {
                    if (cursor.parentNode) cursor.parentNode.removeChild(cursor);
                    if (cb) cb();
                }, 400);
            }
        }
        typeNext();
    }

    function _sovHighlight(selector) {
        _sovClearHighlight();
        if (!selector) return;
        var el = document.querySelector(selector);
        if (el) {
            el.classList.add('sov-onboarding-highlight');
            _sovHighlightedEl = el;
        }
    }

    function _sovClearHighlight() {
        if (_sovHighlightedEl) {
            _sovHighlightedEl.classList.remove('sov-onboarding-highlight');
            _sovHighlightedEl = null;
        }
    }

    function _sovUpdateDots(step) {
        var dots = document.querySelectorAll('.sov-step-dot');
        dots.forEach(function(dot, i) {
            dot.classList.remove('active', 'completed');
            if (i === step) dot.classList.add('active');
            else if (i < step) dot.classList.add('completed');
        });
    }

    function _sovShowStep(step) {
        if (_sovTypingTimer) { clearTimeout(_sovTypingTimer); _sovTypingTimer = null; }
        _sovCurrentStep = step;
        var textEl = document.getElementById('sov-onboarding-text');
        var nextBtn = document.getElementById('sov-onboarding-next');
        if (!textEl || !nextBtn) return;

        if (step >= _sovOnboardingSteps.length) {
            _sovComplete();
            return;
        }

        var s = _sovOnboardingSteps[step];
        _sovUpdateDots(step);
        _sovHighlight(s.highlight);
        nextBtn.textContent = (step === _sovOnboardingSteps.length - 1) ? 'FINISH' : 'NEXT';
        nextBtn.disabled = true;

        _sovTypeText(textEl, s.text, function() {
            nextBtn.disabled = false;
        });
    }

    function _sovComplete() {
        if (_sovTypingTimer) { clearTimeout(_sovTypingTimer); _sovTypingTimer = null; }
        _sovClearHighlight();
        var overlay = document.getElementById('sovereign-onboarding-overlay');
        if (overlay) overlay.style.display = 'none';
        try {
            localStorage.setItem(_sovGetStorageKey(), 'true');
        } catch(e) {}
    }

    function _sovStart() {
        var overlay = document.getElementById('sovereign-onboarding-overlay');
        if (!overlay) return;
        overlay.style.display = 'flex';
        _sovShowStep(0);
    }

    var sovNextBtn = document.getElementById('sov-onboarding-next');
    var sovSkipBtn = document.getElementById('sov-onboarding-skip');

    if (sovNextBtn) {
        sovNextBtn.addEventListener('click', function() {
            _sovShowStep(_sovCurrentStep + 1);
        });
    }

    if (sovSkipBtn) {
        sovSkipBtn.addEventListener('click', function() {
            _sovComplete();
        });
    }

    if (_sovShouldShow()) {
        setTimeout(function() { _sovStart(); }, 1500);
    }
});
