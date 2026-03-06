(function() {
    var GLYPHS = [
        {g:"\u03b1",f:432.0,c:"#c9a84c"},{g:"\u03b2",f:433.2,c:"#2dd4bf"},{g:"\u03b3",f:434.0,c:"#60a5fa"},
        {g:"\u03b4",f:434.8,c:"#a78bfa"},{g:"\u03b5",f:435.5,c:"#f87171"},{g:"\u03b6",f:429.0,c:"#92400e"},
        {g:"\u03b7",f:430.5,c:"#2dd4bf"},{g:"\u03b8",f:431.0,c:"#fb923c"},{g:"\u03b9",f:432.5,c:"#34d399"},
        {g:"\u03ba",f:433.7,c:"#f472b6"},{g:"\u03bb",f:436.0,c:"#60a5fa"},{g:"\u03bc",f:432.8,c:"#a3e635"},
        {g:"\u03bd",f:431.5,c:"#22d3ee"},{g:"\u03be",f:437.0,c:"#818cf8"},{g:"\u03bf",f:432.2,c:"#fbbf24"},
        {g:"\u03c0",f:432.0,c:"#e879f9"},{g:"\u03c1",f:433.0,c:"#34d399"},{g:"\u03c3",f:435.1,c:"#c9a84c"},
        {g:"\u03c4",f:434.5,c:"#6366f1"},{g:"\u03c5",f:430.0,c:"#475569"},{g:"\u03c6",f:442.0,c:"#818cf8"},
        {g:"\u03c7",f:436.5,c:"#22d3ee"},{g:"\u03c8",f:438.5,c:"#2dd4bf"},{g:"\u03c9",f:428.5,c:"#ef4444"},
        {g:"\u0391",f:432.0,c:"#c9a84c"},{g:"\u0392",f:433.2,c:"#f97316"},{g:"\u0393",f:434.0,c:"#8b5cf6"},
        {g:"\u0394",f:434.8,c:"#a78bfa"},{g:"\u0398",f:431.0,c:"#f472b6"},{g:"\u039b",f:436.0,c:"#60a5fa"},
        {g:"\u039e",f:437.0,c:"#475569"},{g:"\u03a0",f:432.0,c:"#c9a84c"},{g:"\u03a3",f:435.1,c:"#c9a84c"},
        {g:"\u03a6",f:442.2,c:"#e879f9"},{g:"\u03a8",f:438.5,c:"#2dd4bf"},{g:"\u03a9",f:428.0,c:"#ef4444"},
        {g:"\u221e",f:432.0,c:"#fbbf24"},{g:"\u25c6",f:432.0,c:"#c9a84c"},{g:"\u2b21",f:435.0,c:"#22d3ee"},
        {g:"\u27d0",f:433.5,c:"#2dd4bf"},{g:"\u263d",f:429.5,c:"#6366f1"},{g:"\u2600",f:440.0,c:"#60a5fa"},
        {g:"\u26a1",f:441.0,c:"#f97316"},{g:"\ud83c\udf0a",f:430.0,c:"#2dd4bf"},{g:"\ud83d\udd2e",f:432.0,c:"#2dd4bf"}
    ];

    var _glyphsLoaded = false;
    function _loadGlyphsFromAPI() {
        if (_glyphsLoaded) return;
        fetch('/api/resonance/glyphs').then(function(r) { return r.json(); }).then(function(data) {
            if (data.glyphs) {
                GLYPHS = [];
                Object.keys(data.glyphs).forEach(function(g) {
                    var m = data.glyphs[g];
                    GLYPHS.push({ g: g, f: m.frequency, c: m.color || '#c9a84c' });
                });
                _glyphsLoaded = true;
            }
        }).catch(function() {});
    }
    setTimeout(_loadGlyphsFromAPI, 1000);

    function ResonanceField(container, opts) {
        this.el = typeof container === 'string' ? document.getElementById(container) : container;
        if (!this.el) return;
        this.opts = opts || {};
        this.isFounder = this.opts.founder || false;
        this.particles = [];
        this.active = false;
        this.raf = null;
        this.canvas = document.createElement('canvas');
        this.canvas.style.cssText = 'width:100%;height:100%;position:absolute;top:0;left:0;pointer-events:none;z-index:5;';
        this.el.style.position = 'relative';
        this.el.appendChild(this.canvas);
        this.ctx = this.canvas.getContext('2d');
        this._resize();
        var self = this;
        window.addEventListener('resize', function() { self._resize(); });
    }

    ResonanceField.prototype._resize = function() {
        this.canvas.width = this.el.offsetWidth;
        this.canvas.height = this.el.offsetHeight;
    };

    ResonanceField.prototype.activate = function(hashHex, phase) {
        this.active = true;
        this.canvas.style.display = 'block';
        this._spawnFromHash(hashHex || '', phase || 'encoding');
        if (!this.raf) this._loop();
    };

    ResonanceField.prototype.deactivate = function() {
        this.active = false;
        this.particles = [];
        if (this.raf) { cancelAnimationFrame(this.raf); this.raf = null; }
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        this.canvas.style.display = 'none';
    };

    ResonanceField.prototype._spawnFromHash = function(hash, phase) {
        var clean = hash.replace(/[^0-9a-fA-F]/g, '');
        var count = this.isFounder ? 24 : 14;
        var speed = this.isFounder ? 2.5 : 1.2;
        var baseColor = this.isFounder ? '#c9a84c' : '#2dd4bf';

        for (var i = 0; i < count; i++) {
            var idx;
            if (clean.length >= 2) {
                var pos = (i * 2) % Math.max(clean.length - 1, 1);
                idx = parseInt(clean.substr(pos, 2) || '00', 16) % GLYPHS.length;
            } else {
                idx = Math.floor(Math.random() * GLYPHS.length);
            }
            var g = GLYPHS[idx];
            this.particles.push({
                x: Math.random() * this.canvas.width,
                y: Math.random() * this.canvas.height,
                vx: (Math.random() - 0.5) * speed,
                vy: (Math.random() - 0.5) * speed - 0.3,
                glyph: g.g,
                color: this.isFounder ? baseColor : g.c,
                alpha: 0.7 + Math.random() * 0.3,
                size: this.isFounder ? 22 + Math.random() * 10 : 16 + Math.random() * 8,
                life: 120 + Math.floor(Math.random() * 80),
                maxLife: 200,
                freq: g.f,
                phase: phase,
                pulse: Math.random() * Math.PI * 2
            });
        }
    };

    ResonanceField.prototype._loop = function() {
        if (!this.active && this.particles.length === 0) {
            this.raf = null;
            this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
            return;
        }
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        var alive = [];
        for (var i = 0; i < this.particles.length; i++) {
            var p = this.particles[i];
            p.x += p.vx;
            p.y += p.vy;
            p.life--;
            p.pulse += 0.05;
            var fadeIn = Math.min(1, (p.maxLife - p.life) / 20);
            var fadeOut = Math.min(1, p.life / 30);
            var a = p.alpha * fadeIn * fadeOut;
            var pulseFactor = 1 + Math.sin(p.pulse) * 0.15;
            this.ctx.save();
            this.ctx.globalAlpha = a;
            this.ctx.font = Math.round(p.size * pulseFactor) + 'px sans-serif';
            this.ctx.fillStyle = p.color;
            this.ctx.shadowColor = p.color;
            this.ctx.shadowBlur = this.isFounder ? 20 : 10;
            this.ctx.textAlign = 'center';
            this.ctx.fillText(p.glyph, p.x, p.y);
            this.ctx.restore();
            if (p.life > 0) alive.push(p);
        }
        this.particles = alive;
        var self = this;
        this.raf = requestAnimationFrame(function() { self._loop(); });
    };

    ResonanceField.prototype.pulseHash = function(hashHex) {
        this._spawnFromHash(hashHex, 'pulse');
        if (!this.raf) { this.active = true; this._loop(); }
    };

    window.ResonanceField = ResonanceField;

    window.createResonanceOverlay = function(containerId, opts) {
        return new ResonanceField(containerId, opts);
    };
})();
