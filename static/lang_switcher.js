(function() {
    'use strict';

    var LANG_CODE_MAP = {
        'en': 'EN', 'ur': 'UR', 'ar': 'AR', 'es': 'ES',
        'fr': 'FR', 'zh': 'ZH', 'ru': 'RU', 'ja': 'JA', 'void': 'VOID',
    };

    var LANG_FULL_NAMES = {
        'en': 'English', 'ur': 'Urdu', 'ar': 'Arabic', 'es': 'Spanish',
        'fr': 'French', 'zh': 'Mandarin', 'ru': 'Russian', 'ja': 'Japanese', 'void': 'VOID',
    };

    var _currentLang = 'en';
    var _currentDir = 'ltr';
    var _originalContent = null;
    var _originalNav = null;
    var _initialized = false;
    var _pageAudio = null;

    function _getOrCreateOverlay() {
        var el = document.getElementById('lang-translating-overlay');
        if (!el) {
            el = document.createElement('div');
            el.id = 'lang-translating-overlay';
            el.className = 'lang-translating-overlay';
            el.innerHTML = '<span class="void-lang-spinner" style="width:16px;height:16px;border-width:2px;margin:0;"></span>' +
                           '<span id="lang-overlay-msg">Translating\u2026</span>';
            document.body.appendChild(el);
        }
        return el;
    }

    function _showOverlay(msg) {
        var el = _getOrCreateOverlay();
        var msgEl = el.querySelector('#lang-overlay-msg');
        if (msgEl) msgEl.textContent = msg || 'Translating\u2026';
        el.classList.add('visible');
    }

    function _hideOverlay() {
        var el = document.getElementById('lang-translating-overlay');
        if (el) el.classList.remove('visible');
    }

    function _getTranslatableContent() {
        return document.querySelector('main') ||
               document.querySelector('.void-lang-main') ||
               document.querySelector('.landing-hero') ||
               document.getElementById('void-lang-main') ||
               document.querySelector('article') ||
               document.querySelector('.content') ||
               document.querySelector('section');
    }

    function _getTranslatableRegions() {
        var regions = [];
        var main = _getTranslatableContent();
        if (main) regions.push(main);
        var nav = document.querySelector('nav') || document.querySelector('header');
        if (nav && !regions.includes(nav)) regions.push(nav);
        return regions;
    }

    function _setDirection(dir) {
        document.body.setAttribute('dir', dir || 'ltr');
        var main = _getTranslatableContent();
        if (main) main.setAttribute('dir', dir || 'ltr');
        _currentDir = dir || 'ltr';
    }

    function _updateSwitcherUI(langCode) {
        var labelEl = document.getElementById('lang-switcher-label');
        if (labelEl) labelEl.textContent = LANG_CODE_MAP[langCode] || langCode.toUpperCase();

        document.querySelectorAll('.lang-option').forEach(function(btn) {
            btn.classList.toggle('active', btn.getAttribute('data-lang') === langCode);
        });

        var speakBtn = document.getElementById('lang-page-speak-btn');
        if (speakBtn) {
            speakBtn.style.display = (langCode !== 'en' && langCode !== 'void') ? 'inline-flex' : 'none';
        }
    }

    function _injectSpeakButton() {
        var footer = document.querySelector('.lang-switcher-footer');
        if (!footer || document.getElementById('lang-page-speak-btn')) return;

        var btn = document.createElement('button');
        btn.id = 'lang-page-speak-btn';
        btn.title = 'Read page aloud in current language';
        btn.style.cssText = 'display:none;align-items:center;gap:4px;background:rgba(124,92,255,0.15);border:1px solid rgba(124,92,255,0.4);color:#a78bfa;font-size:10px;padding:4px 8px;border-radius:4px;cursor:pointer;margin-top:6px;width:100%;justify-content:center;';
        btn.innerHTML = '&#9654; Read Page';
        btn.addEventListener('click', function() {
            _readPageAloud();
        });
        footer.appendChild(btn);
    }

    function _readPageAloud() {
        var main = _getTranslatableContent();
        if (!main) return;

        var text = main.innerText || main.textContent || '';
        text = text.slice(0, 3000).trim();
        if (!text) return;

        var langName = LANG_FULL_NAMES[_currentLang] || _currentLang;
        var speakBtn = document.getElementById('lang-page-speak-btn');

        if (_pageAudio) {
            _pageAudio.pause();
            _pageAudio = null;
            if (speakBtn) speakBtn.innerHTML = '&#9654; Read Page';
            return;
        }

        if (speakBtn) speakBtn.innerHTML = '\u23F3 Loading\u2026';

        fetch('/speak', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: text, language: langName })
        })
        .then(function(r) {
            if (!r.ok) throw new Error('TTS failed');
            return r.blob();
        })
        .then(function(blob) {
            var url = URL.createObjectURL(blob);
            _pageAudio = new Audio(url);
            _pageAudio.play();
            if (speakBtn) speakBtn.innerHTML = '\u23F9 Stop Reading';
            _pageAudio.onended = function() {
                _pageAudio = null;
                URL.revokeObjectURL(url);
                if (speakBtn) speakBtn.innerHTML = '&#9654; Read Page';
            };
        })
        .catch(function() {
            if (speakBtn) speakBtn.innerHTML = '&#9654; Read Page';
        });
    }

    function _translateRegion(el, langName, langCode, slugSuffix, onDone, applyFn) {
        var sourceEl = typeof applyFn === 'undefined' ? el : el;
        var textToTranslate = sourceEl.innerHTML;
        fetch('/translate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                text: textToTranslate,
                language: langName,
                lang_code: langCode,
                slug: window.location.pathname + (slugSuffix || '')
            })
        })
        .then(function(r) { return r.json(); })
        .then(function(data) {
            if (data.success && data.translated) {
                if (applyFn) {
                    applyFn(el, data.translated);
                } else {
                    el.innerHTML = data.translated;
                }
            }
            if (onDone) onDone(data);
        })
        .catch(function() { if (onDone) onDone(null); });
    }

    function _getNavEl() {
        var nav = document.querySelector('nav') || document.querySelector('header');
        return nav || null;
    }

    function _extractNavTextLinks(navEl) {
        if (!navEl) return null;
        var switcherEl = navEl.querySelector('#lang-switcher');
        if (!switcherEl) return navEl;
        var clone = navEl.cloneNode(true);
        var clonedSwitcher = clone.querySelector('#lang-switcher');
        if (clonedSwitcher) clonedSwitcher.parentNode.removeChild(clonedSwitcher);
        return clone;
    }

    function _applyTranslatedNavHTML(navEl, translatedHTML) {
        if (!navEl) return;
        var switcherEl = navEl.querySelector('#lang-switcher');
        if (!switcherEl) {
            navEl.innerHTML = translatedHTML;
            return;
        }
        var switcherClone = switcherEl.cloneNode(true);
        navEl.innerHTML = translatedHTML;
        navEl.appendChild(switcherClone);
        _bindSwitcherAgain();
        var newToggle = navEl.querySelector('#lang-switcher-toggle');
        var newDropdown = navEl.querySelector('#lang-switcher-dropdown');
        if (newToggle && newDropdown) {
            newToggle.addEventListener('click', function(e) {
                e.stopPropagation();
                newDropdown.style.display = newDropdown.style.display === 'none' ? 'block' : 'none';
            });
        }
    }

    function _applyLanguage(langCode, langName, dir) {
        if (_pageAudio) { _pageAudio.pause(); _pageAudio = null; }
        _currentLang = langCode;
        _setDirection(dir || 'ltr');
        _updateSwitcherUI(langCode);

        var statusEl = document.getElementById('lang-translate-status');

        if (langCode === 'en') {
            if (_originalContent) {
                var main = _getTranslatableContent();
                if (main) main.innerHTML = _originalContent;
            }
            if (_originalNav) {
                var nav = _getNavEl();
                if (nav) nav.innerHTML = _originalNav;
                _bindSwitcherAgain();
            }
            if (statusEl) { statusEl.textContent = ''; statusEl.classList.remove('active'); }
            _hideOverlay();
            return;
        }

        if (langCode === 'void') {
            window.location.href = '/void-language';
            return;
        }

        var main = _getTranslatableContent();
        var navEl = _getNavEl();

        if (!main) { _hideOverlay(); return; }

        if (!_originalContent) _originalContent = main.innerHTML;
        if (navEl && !_originalNav) _originalNav = navEl.innerHTML;

        _showOverlay('Translating to ' + langName + '\u2026');
        if (statusEl) { statusEl.textContent = 'Translating\u2026'; statusEl.classList.add('active'); }

        var pending = navEl ? 2 : 1;
        var successCount = 0;

        function _onPartDone(data) {
            pending--;
            if (data && data.success) successCount++;
            if (pending === 0) {
                _hideOverlay();
                if (successCount > 0) {
                    if (statusEl) {
                        statusEl.textContent = 'Showing in ' + langName;
                        statusEl.classList.add('active');
                    }
                } else {
                    if (statusEl) { statusEl.textContent = 'Translation unavailable'; statusEl.classList.remove('active'); }
                }
                _bindSwitcherAgain();
            }
        }

        _translateRegion(main, langName, langCode, '', _onPartDone);
        if (navEl) {
            var navForTranslation = _extractNavTextLinks(navEl);
            _translateRegion(navForTranslation, langName, langCode, '__nav', _onPartDone, function(originalNavEl, translatedHTML) {
                _applyTranslatedNavHTML(originalNavEl, translatedHTML);
            }.bind(null, navEl));
        }
    }

    function _bindSwitcherAgain() {
        document.querySelectorAll('.lang-option[data-lang]').forEach(function(btn) {
            if (btn._langBound) return;
            btn._langBound = true;
            btn.addEventListener('click', function(e) {
                e.preventDefault();
                var dd = document.getElementById('lang-switcher-dropdown');
                if (dd) dd.style.display = 'none';
                var lc = btn.getAttribute('data-lang');
                var ln = btn.getAttribute('data-name') || LANG_FULL_NAMES[lc] || lc;
                var d = btn.getAttribute('data-dir') || 'ltr';
                _setLangOnServer(lc);
                _applyLanguage(lc, ln, d);
            });
        });
    }

    function _setLangOnServer(langCode) {
        fetch('/api/set-language', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ lang: langCode })
        }).catch(function() {});
    }

    function _bootstrapFromServer() {
        fetch('/api/languages')
            .then(function(r) { return r.json(); })
            .then(function(data) {
                var serverLang = data.current || 'en';
                _currentLang = serverLang;
                _updateSwitcherUI(serverLang);

                if (serverLang !== 'en' && serverLang !== 'void') {
                    var langName = LANG_FULL_NAMES[serverLang] || serverLang;
                    var langInfo = (data.languages || []).find(function(l) { return l.code === serverLang; });
                    var dir = langInfo ? langInfo.dir : 'ltr';
                    _applyLanguage(serverLang, langName, dir);
                } else if (serverLang === 'en') {
                    _setDirection('ltr');
                }
            })
            .catch(function() {});
    }

    function _init() {
        var toggle = document.getElementById('lang-switcher-toggle');
        var dropdown = document.getElementById('lang-switcher-dropdown');
        if (!toggle || !dropdown) return;
        if (_initialized) return;
        _initialized = true;

        _injectSpeakButton();

        toggle.addEventListener('click', function(e) {
            e.stopPropagation();
            var isOpen = dropdown.style.display !== 'none';
            dropdown.style.display = isOpen ? 'none' : 'block';
        });

        document.addEventListener('click', function(e) {
            var switcher = document.getElementById('lang-switcher');
            if (switcher && !switcher.contains(e.target)) {
                dropdown.style.display = 'none';
            }
        });

        document.querySelectorAll('.lang-option[data-lang]').forEach(function(btn) {
            btn.addEventListener('click', function(e) {
                e.preventDefault();
                dropdown.style.display = 'none';
                var langCode = btn.getAttribute('data-lang');
                var langName = btn.getAttribute('data-name') || LANG_FULL_NAMES[langCode] || langCode;
                var dir = btn.getAttribute('data-dir') || 'ltr';
                _setLangOnServer(langCode);
                _applyLanguage(langCode, langName, dir);
            });
        });

        _bootstrapFromServer();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', _init);
    } else {
        _init();
    }

    window.VoidLangSwitcher = {
        apply: _applyLanguage,
        current: function() { return _currentLang; },
    };
})();
