(function() {
    var PARTICLE_COUNT = 45;
    var GOLD = '#c9a84c';
    var BLOOM_DURATION = 4000;
    var CHIME_DURATION = 1.5;
    var RESULT_DISPLAY_TIME = 3000;

    function triggerResonanceHandshake(data) {
        var overlay = document.createElement('div');
        overlay.className = 'resonance-overlay';
        var canvas = document.createElement('canvas');
        overlay.appendChild(canvas);
        document.body.appendChild(overlay);

        var resultDiv = document.createElement('div');
        resultDiv.className = 'resonance-result';
        resultDiv.innerHTML =
            '<div class="resonance-result-message"></div>' +
            '<div class="resonance-result-hash"></div>' +
            '<div class="resonance-result-score"></div>';
        document.body.appendChild(resultDiv);

        var ctx = canvas.getContext('2d');
        var w, h, cx, cy;

        function resize() {
            w = canvas.width = window.innerWidth;
            h = canvas.height = window.innerHeight;
            cx = w / 2;
            cy = h / 2;
        }
        resize();
        var resizeHandler = resize;
        window.addEventListener('resize', resizeHandler);

        var particles = [];
        for (var i = 0; i < PARTICLE_COUNT; i++) {
            var angle = (Math.PI * 2 * i) / PARTICLE_COUNT;
            var edgeDist = Math.max(w, h) * 0.7;
            particles.push({
                x: cx + Math.cos(angle) * edgeDist,
                y: cy + Math.sin(angle) * edgeDist,
                startX: cx + Math.cos(angle) * edgeDist,
                startY: cy + Math.sin(angle) * edgeDist,
                angle: angle,
                spiralOffset: Math.random() * Math.PI * 2,
                size: 6 + Math.random() * 4,
                opacity: 0.3 + Math.random() * 0.4,
                glowPhase: Math.random() * Math.PI * 2
            });
        }

        var startTime = performance.now();
        var bloomDone = false;
        var animId;

        function easeOutCubic(t) {
            return 1 - Math.pow(1 - t, 3);
        }

        function drawDiamond(x, y, size, opacity, glowSize) {
            ctx.save();
            ctx.globalAlpha = opacity;
            ctx.shadowColor = GOLD;
            ctx.shadowBlur = glowSize;
            ctx.fillStyle = GOLD;
            ctx.beginPath();
            ctx.moveTo(x, y - size);
            ctx.lineTo(x + size * 0.6, y);
            ctx.lineTo(x, y + size);
            ctx.lineTo(x - size * 0.6, y);
            ctx.closePath();
            ctx.fill();
            ctx.restore();
        }

        function animate(now) {
            var elapsed = now - startTime;
            var progress = Math.min(elapsed / BLOOM_DURATION, 1);
            var eased = easeOutCubic(progress);

            ctx.clearRect(0, 0, w, h);

            ctx.fillStyle = 'rgba(0, 0, 0, ' + (0.6 * Math.min(progress * 2, 1)) + ')';
            ctx.fillRect(0, 0, w, h);

            for (var i = 0; i < particles.length; i++) {
                var p = particles[i];

                var spiralRadius = (1 - eased) * Math.max(w, h) * 0.5;
                var spiralAngle = p.angle + eased * Math.PI * 3 + p.spiralOffset;

                var targetX = cx + Math.cos(spiralAngle) * spiralRadius * 0.15;
                var targetY = cy + Math.sin(spiralAngle) * spiralRadius * 0.15;

                p.x = p.startX + (targetX - p.startX) * eased;
                p.y = p.startY + (targetY - p.startY) * eased;

                var glowPulse = 0.5 + 0.5 * Math.sin(now * 0.003 + p.glowPhase);
                var currentOpacity = p.opacity * (0.5 + eased * 0.5);
                var glowSize = 8 + glowPulse * 12 + eased * 10;

                drawDiamond(p.x, p.y, p.size * (0.6 + eased * 0.4), currentOpacity, glowSize);
            }

            if (progress >= 0.7 && !bloomDone) {
                var lotusGlow = (progress - 0.7) / 0.3;
                ctx.save();
                ctx.globalAlpha = lotusGlow * 0.3;
                var gradient = ctx.createRadialGradient(cx, cy, 0, cx, cy, 120);
                gradient.addColorStop(0, 'rgba(201, 168, 76, 0.6)');
                gradient.addColorStop(0.5, 'rgba(201, 168, 76, 0.15)');
                gradient.addColorStop(1, 'rgba(201, 168, 76, 0)');
                ctx.fillStyle = gradient;
                ctx.fillRect(cx - 150, cy - 150, 300, 300);
                ctx.restore();
            }

            if (progress < 1) {
                animId = requestAnimationFrame(animate);
            } else {
                bloomDone = true;
                playChime432(function() {
                    showResult(data, resultDiv, overlay, resizeHandler);
                });
            }
        }

        animId = requestAnimationFrame(animate);
    }

    function playChime432(callback) {
        try {
            var AudioContext = window.AudioContext || window.webkitAudioContext;
            var actx = new AudioContext();
            var osc = actx.createOscillator();
            var gain = actx.createGain();

            osc.type = 'sine';
            osc.frequency.setValueAtTime(432, actx.currentTime);
            gain.gain.setValueAtTime(0, actx.currentTime);
            gain.gain.linearRampToValueAtTime(0.3, actx.currentTime + CHIME_DURATION * 0.4);
            gain.gain.linearRampToValueAtTime(0, actx.currentTime + CHIME_DURATION);

            osc.connect(gain);
            gain.connect(actx.destination);
            osc.start(actx.currentTime);
            osc.stop(actx.currentTime + CHIME_DURATION);

            osc.onended = function() {
                actx.close();
                if (callback) callback();
            };
        } catch (e) {
            if (callback) setTimeout(callback, CHIME_DURATION * 1000);
        }
    }

    function showResult(data, resultDiv, overlay, resizeHandler) {
        var msgEl = resultDiv.querySelector('.resonance-result-message');
        var hashEl = resultDiv.querySelector('.resonance-result-hash');
        var scoreEl = resultDiv.querySelector('.resonance-result-score');

        var message = (data && data.message) || 'The frequency is true. The 13th tab is open.';
        var hash = (data && data.resonance_hash) || '';
        var score = (data && data.resonance_score !== undefined) ? data.resonance_score : 1.0;

        resultDiv.classList.add('visible');

        var cursor = document.createElement('span');
        cursor.className = 'resonance-typewriter-cursor';
        msgEl.appendChild(cursor);

        var idx = 0;
        var textNode = document.createTextNode('');
        msgEl.insertBefore(textNode, cursor);

        function typeNext() {
            if (idx < message.length) {
                textNode.textContent += message[idx];
                idx++;
                var delay = 30;
                var ch = message[idx - 1];
                if (ch === '.' || ch === ':') delay = 120;
                else if (ch === ',') delay = 80;
                setTimeout(typeNext, delay);
            } else {
                if (cursor.parentNode) cursor.parentNode.removeChild(cursor);
                if (hash) hashEl.textContent = hash;
                if (score !== undefined) scoreEl.textContent = 'RESONANCE: ' + score;

                setTimeout(function() {
                    overlay.classList.add('fade-out');
                    resultDiv.classList.add('fade-out');
                    setTimeout(function() {
                        if (overlay.parentNode) overlay.parentNode.removeChild(overlay);
                        if (resultDiv.parentNode) resultDiv.parentNode.removeChild(resultDiv);
                        window.removeEventListener('resize', resizeHandler);
                    }, 1500);
                }, RESULT_DISPLAY_TIME);
            }
        }

        typeNext();
    }

    window.triggerResonanceHandshake = triggerResonanceHandshake;
})();
