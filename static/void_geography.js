(function() {
    'use strict';

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

    function _hexByte(clean, pos) {
        if (!clean || clean.length < 2) return 0;
        var p = pos % Math.max(clean.length - 1, 1);
        return parseInt(clean.substr(p, 2) || '00', 16);
    }

    function spawnFromHash(hash, phase, count) {
        var clean = (hash || '').replace(/[^0-9a-fA-F]/g, '');
        var n = count || 14;
        var particles = [];
        for (var i = 0; i < n; i++) {
            var idx;
            if (clean.length >= 2) {
                var pos = (i * 2) % Math.max(clean.length - 1, 1);
                idx = parseInt(clean.substr(pos, 2) || '00', 16) % GLYPHS.length;
            } else {
                idx = i % GLYPHS.length;
            }
            var g = GLYPHS[idx];
            var b0 = _hexByte(clean, i * 3);
            var b1 = _hexByte(clean, i * 5 + 1);
            var b2 = _hexByte(clean, i * 7 + 2);
            var b3 = _hexByte(clean, i * 11 + 3);
            particles.push({
                glyph: g.g,
                color: g.c,
                freq: g.f,
                phase: phase || 'resonance',
                xFrac: b0 / 255,
                yFrac: b1 / 255,
                size: 13 + (b2 / 255) * 12,
                alpha: 0.5 + (b3 / 255) * 0.4,
            });
        }
        return particles;
    }

    function render(canvas, hash, phase) {
        var ctx = canvas.getContext('2d');
        var w = canvas.width || canvas.offsetWidth || 120;
        var h = canvas.height || canvas.offsetHeight || 80;
        if (!canvas.width || canvas.width !== w) canvas.width = w;
        if (!canvas.height || canvas.height !== h) canvas.height = h;
        ctx.clearRect(0, 0, w, h);
        var particles = spawnFromHash(hash, phase, 14);
        for (var i = 0; i < particles.length; i++) {
            var p = particles[i];
            ctx.save();
            ctx.globalAlpha = p.alpha;
            ctx.font = Math.round(p.size) + 'px sans-serif';
            ctx.fillStyle = p.color;
            ctx.shadowColor = p.color;
            ctx.shadowBlur = 8;
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText(p.glyph, p.xFrac * (w * 0.8) + w * 0.1, p.yFrac * (h * 0.8) + h * 0.1);
            ctx.restore();
        }
        return particles;
    }

    function score(particles) {
        if (!particles || !particles.length) {
            return {score: 0, tier: 'Common', tierColor: '#6b7280'};
        }

        var glyphMap = {};
        var freqs = [];
        var total = particles.length;

        for (var i = 0; i < particles.length; i++) {
            var p = particles[i];
            glyphMap[p.glyph] = (glyphMap[p.glyph] || 0) + 1;
            if (freqs.indexOf(p.freq) === -1) freqs.push(p.freq);
        }

        var entropy = 0;
        var glyphKeys = Object.keys(glyphMap);
        for (var j = 0; j < glyphKeys.length; j++) {
            var prob = glyphMap[glyphKeys[j]] / total;
            if (prob > 0) entropy -= prob * Math.log2(prob);
        }

        var uniqueGlyphs = glyphKeys.length;

        var maxFreq = Math.max.apply(null, freqs);
        var minFreq = Math.min.apply(null, freqs);
        var freqSpread = maxFreq - minFreq;
        var freqRange = 442.2 - 428.0;
        var normFreqSpread = freqSpread / freqRange;

        var maxEntropy = Math.log2(total);
        var normEntropy = maxEntropy > 0 ? entropy / maxEntropy : 0;
        var normUnique = uniqueGlyphs / total;

        var s = Math.round(normEntropy * normUnique * normFreqSpread * 100) / 10;

        var tier, tierColor;
        if (s > 7.5) {
            tier = 'Singular'; tierColor = '#c9a84c';
        } else if (s >= 5.5) {
            tier = 'Legendary'; tierColor = '#e879f9';
        } else if (s >= 3.0) {
            tier = 'Rare'; tierColor = '#2dd4bf';
        } else {
            tier = 'Common'; tierColor = '#6b7280';
        }

        return {score: s, tier: tier, tierColor: tierColor};
    }

    window.VoidGeography = {
        spawnFromHash: spawnFromHash,
        render: render,
        score: score,
    };
})();
