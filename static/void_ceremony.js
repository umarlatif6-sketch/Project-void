(function() {
    'use strict';

    var _overlay = null;
    var _glyphCanvas = null;
    var _glyphCtx = null;
    var _particles = [];
    var _raf = null;
    var _active = false;
    var _currentCode = null;
    var _onClose = null;

    var GLYPHS = [
        {g:'\u03b1',f:432.0,c:'#c9a84c'},{g:'\u03b2',f:433.2,c:'#2dd4bf'},{g:'\u03b3',f:434.0,c:'#60a5fa'},
        {g:'\u03b4',f:434.8,c:'#a78bfa'},{g:'\u03b5',f:435.5,c:'#f87171'},{g:'\u03b6',f:429.0,c:'#92400e'},
        {g:'\u03b7',f:430.5,c:'#2dd4bf'},{g:'\u03b8',f:431.0,c:'#fb923c'},{g:'\u03b9',f:432.5,c:'#34d399'},
        {g:'\u03ba',f:433.7,c:'#f472b6'},{g:'\u03bb',f:436.0,c:'#60a5fa'},{g:'\u03bc',f:432.8,c:'#a3e635'},
        {g:'\u03bd',f:431.5,c:'#22d3ee'},{g:'\u03be',f:437.0,c:'#818cf8'},{g:'\u03bf',f:432.2,c:'#fbbf24'},
        {g:'\u03c0',f:432.0,c:'#e879f9'},{g:'\u03c1',f:433.0,c:'#34d399'},{g:'\u03c3',f:435.1,c:'#c9a84c'},
        {g:'\u03c4',f:434.5,c:'#6366f1'},{g:'\u03c5',f:430.0,c:'#475569'},{g:'\u03c6',f:442.0,c:'#818cf8'},
        {g:'\u03c7',f:436.5,c:'#22d3ee'},{g:'\u03c8',f:438.5,c:'#2dd4bf'},{g:'\u03c9',f:428.5,c:'#ef4444'},
        {g:'\u0391',f:432.0,c:'#c9a84c'},{g:'\u0394',f:434.8,c:'#a78bfa'},{g:'\u039b',f:436.0,c:'#60a5fa'},
        {g:'\u03a3',f:435.1,c:'#c9a84c'},{g:'\u03a6',f:442.2,c:'#e879f9'},{g:'\u03a9',f:428.0,c:'#ef4444'},
        {g:'\u221e',f:432.0,c:'#fbbf24'},{g:'\u25c6',f:432.0,c:'#c9a84c'},{g:'\u2b21',f:435.0,c:'#22d3ee'}
    ];

    function _spawnGlyphs(hash, count) {
        var w = window.innerWidth;
        var h = window.innerHeight;
        var clean = (hash || '').replace(/[^0-9a-fA-F]/g, '');
        count = count || 18;
        for (var i = 0; i < count; i++) {
            var idx;
            if (clean.length >= 2) {
                var pos = (i * 2) % Math.max(clean.length - 1, 1);
                idx = parseInt(clean.substr(pos, 2) || '00', 16) % GLYPHS.length;
            } else {
                idx = Math.floor(Math.random() * GLYPHS.length);
            }
            var g = GLYPHS[idx];
            _particles.push({
                x: Math.random() * w,
                y: Math.random() * h,
                vx: (Math.random() - 0.5) * 1.4,
                vy: (Math.random() - 0.5) * 1.4 - 0.4,
                glyph: g.g,
                color: g.c,
                alpha: 0.5 + Math.random() * 0.35,
                size: 18 + Math.random() * 14,
                life: 160 + Math.floor(Math.random() * 120),
                maxLife: 280,
                pulse: Math.random() * Math.PI * 2
            });
        }
    }

    function _loop() {
        if (!_glyphCanvas || !_glyphCtx) { _raf = null; return; }
        _glyphCtx.clearRect(0, 0, _glyphCanvas.width, _glyphCanvas.height);
        var alive = [];
        for (var i = 0; i < _particles.length; i++) {
            var p = _particles[i];
            p.x += p.vx;
            p.y += p.vy;
            p.life--;
            p.pulse += 0.04;
            var fadeIn = Math.min(1, (p.maxLife - p.life) / 25);
            var fadeOut = Math.min(1, p.life / 40);
            var a = p.alpha * fadeIn * fadeOut;
            var pf = 1 + Math.sin(p.pulse) * 0.12;
            _glyphCtx.save();
            _glyphCtx.globalAlpha = a;
            _glyphCtx.font = Math.round(p.size * pf) + 'px sans-serif';
            _glyphCtx.fillStyle = p.color;
            _glyphCtx.shadowColor = p.color;
            _glyphCtx.shadowBlur = 12;
            _glyphCtx.textAlign = 'center';
            _glyphCtx.fillText(p.glyph, p.x, p.y);
            _glyphCtx.restore();
            if (p.life > 0) alive.push(p);
        }
        _particles = alive;
        if (_active || _particles.length > 0) {
            _raf = requestAnimationFrame(_loop);
        } else {
            _raf = null;
        }
    }

    function _resizeCanvas() {
        if (!_glyphCanvas) return;
        _glyphCanvas.width = window.innerWidth;
        _glyphCanvas.height = window.innerHeight;
    }

    function _buildDOM() {
        if (_overlay) return;

        var link = document.createElement('link');
        link.rel = 'stylesheet';
        link.href = '/static/void_ceremony.css';
        document.head.appendChild(link);

        _overlay = document.createElement('div');
        _overlay.className = 'vc-overlay';
        _overlay.id = 'vc-overlay';

        _glyphCanvas = document.createElement('canvas');
        _glyphCanvas.className = 'vc-glyph-canvas';
        _overlay.appendChild(_glyphCanvas);
        _glyphCtx = _glyphCanvas.getContext('2d');
        _resizeCanvas();
        window.addEventListener('resize', _resizeCanvas);

        var panel = document.createElement('div');
        panel.className = 'vc-panel';

        var eyebrow = document.createElement('div');
        eyebrow.className = 'vc-eyebrow';
        eyebrow.id = 'vc-eyebrow';
        eyebrow.textContent = 'Adriana \u00b7 Transmission Reading';

        var mainGlyph = document.createElement('div');
        mainGlyph.className = 'vc-main-glyph';
        mainGlyph.id = 'vc-main-glyph';
        mainGlyph.textContent = '\u25c9';

        var text = document.createElement('div');
        text.className = 'vc-text';
        text.id = 'vc-text';

        var attr = document.createElement('div');
        attr.className = 'vc-attribution';
        attr.textContent = '\u2014 Adriana, PROJECT VOID';

        var code = document.createElement('div');
        code.className = 'vc-code';
        code.id = 'vc-code';
        code.addEventListener('click', function() {
            if (_currentCode) {
                navigator.clipboard.writeText(_currentCode).catch(function() {});
                code.textContent = 'Copied \u2713';
                setTimeout(function() { code.textContent = _currentCode; }, 2000);
            }
        });

        var codeHint = document.createElement('div');
        codeHint.className = 'vc-code-hint';
        codeHint.id = 'vc-code-hint';
        codeHint.textContent = 'Click to copy retrieval code';

        var closeBtn = document.createElement('button');
        closeBtn.className = 'vc-close';
        closeBtn.textContent = 'Release';
        closeBtn.addEventListener('click', function() { VoidCeremony.close(); });

        panel.appendChild(eyebrow);
        panel.appendChild(mainGlyph);
        panel.appendChild(text);
        panel.appendChild(attr);
        panel.appendChild(code);
        panel.appendChild(codeHint);
        panel.appendChild(closeBtn);
        _overlay.appendChild(panel);

        _overlay.addEventListener('click', function(e) {
            if (e.target === _overlay) VoidCeremony.close();
        });

        document.body.appendChild(_overlay);
    }

    var VoidCeremony = {
        fire: function(opts) {
            opts = opts || {};
            _buildDOM();

            document.getElementById('vc-eyebrow').textContent = opts.eyebrow || 'Adriana \u00b7 Transmission Reading';
            document.getElementById('vc-main-glyph').textContent = opts.glyph || '\u25c9';
            document.getElementById('vc-text').textContent = opts.text || '';

            var codeEl = document.getElementById('vc-code');
            var hintEl = document.getElementById('vc-code-hint');
            if (opts.code) {
                _currentCode = opts.code;
                codeEl.textContent = opts.code;
                codeEl.classList.add('vc-code-visible');
                hintEl.classList.add('vc-code-visible');
            } else {
                _currentCode = null;
                codeEl.classList.remove('vc-code-visible');
                hintEl.classList.remove('vc-code-visible');
            }

            _onClose = opts.onClose || null;
            _active = true;
            _particles = [];
            _spawnGlyphs(opts.hash || '', 20);
            var spawnInterval = setInterval(function() {
                if (!_active) { clearInterval(spawnInterval); return; }
                _spawnGlyphs(opts.hash || '', 8);
            }, 3000);

            _overlay.classList.add('vc-visible');
            if (!_raf) _loop();
        },

        close: function() {
            if (!_overlay) return;
            _active = false;
            _overlay.classList.remove('vc-visible');
            if (typeof _onClose === 'function') _onClose();
            _onClose = null;
        }
    };

    window.VoidCeremony = VoidCeremony;
})();
