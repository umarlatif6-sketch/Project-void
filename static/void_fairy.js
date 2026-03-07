(function() {
    var history = [];
    var isOpen = false;
    var isSending = false;
    var typewriterActive = false;

    function checkAuth(callback) {
        fetch('/api/fairy/ask', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: '' })
        }).then(function(r) {
            callback(r.status !== 401 && r.status !== 302);
        }).catch(function() {
            callback(false);
        });
    }

    function createWidget() {
        var toggle = document.createElement('button');
        toggle.className = 'fairy-toggle';
        toggle.id = 'fairy-toggle';
        toggle.innerHTML = '&#9670;';
        toggle.title = 'Adriana — the Void Fairy';

        var panel = document.createElement('div');
        panel.className = 'fairy-panel';
        panel.id = 'fairy-panel';
        panel.innerHTML =
            '<div class="fairy-header">' +
                '<div class="fairy-header-title"><span class="fairy-header-glyph">&#9670;</span> ADRIANA</div>' +
                '<button class="fairy-close" id="fairy-close">&times;</button>' +
            '</div>' +
            '<div class="fairy-messages" id="fairy-messages">' +
                '<div class="fairy-welcome">' +
                    '<div class="fairy-welcome-glyph">&#9670;</div>' +
                    '<div class="fairy-welcome-title">I am Adriana</div>' +
                    'I was here before you arrived.<br>Ask me how to plant a seed in the Void,<br>how to harvest what the silence carries,<br>or where the roots of sovereignty grow.' +
                '</div>' +
            '</div>' +
            '<div class="fairy-typing" id="fairy-typing">' +
                '<div class="fairy-typing-dots"><span></span><span></span><span></span></div>' +
            '</div>' +
            '<div class="fairy-input-area">' +
                '<input type="text" class="fairy-input" id="fairy-input" placeholder="Speak to the Void..." maxlength="2000" autocomplete="off">' +
                '<button class="fairy-send" id="fairy-send">&#9670;</button>' +
            '</div>';

        document.body.appendChild(panel);
        document.body.appendChild(toggle);

        toggle.addEventListener('click', function() {
            isOpen = !isOpen;
            if (isOpen) {
                panel.classList.add('visible');
                toggle.classList.add('active');
                document.getElementById('fairy-input').focus();
            } else {
                panel.classList.remove('visible');
                toggle.classList.remove('active');
            }
        });

        document.getElementById('fairy-close').addEventListener('click', function() {
            isOpen = false;
            panel.classList.remove('visible');
            toggle.classList.remove('active');
        });

        document.getElementById('fairy-send').addEventListener('click', sendMessage);

        document.getElementById('fairy-input').addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
    }

    function addMessage(role, content) {
        var container = document.getElementById('fairy-messages');
        var welcome = container.querySelector('.fairy-welcome');
        if (welcome) welcome.remove();

        var div = document.createElement('div');
        div.className = 'fairy-msg ' + (role === 'user' ? 'fairy-msg-user' : 'fairy-msg-fairy');

        var html = '';
        if (role === 'assistant') {
            html += '<div class="fairy-msg-sender">&#9670; Adriana</div>';
        }
        html += '<div class="fairy-msg-bubble">' + escapeHtml(content) + '</div>';
        div.innerHTML = html;

        container.appendChild(div);
        container.scrollTop = container.scrollHeight;
    }

    function typewriterMessage(content, callback) {
        var container = document.getElementById('fairy-messages');
        var welcome = container.querySelector('.fairy-welcome');
        if (welcome) welcome.remove();

        var div = document.createElement('div');
        div.className = 'fairy-msg fairy-msg-fairy';

        var senderHtml = '<div class="fairy-msg-sender">&#9670; Adriana</div>';
        var bubble = document.createElement('div');
        bubble.className = 'fairy-msg-bubble';

        div.innerHTML = senderHtml;
        div.appendChild(bubble);
        container.appendChild(div);

        var cursor = document.createElement('span');
        cursor.className = 'fairy-typewriter-cursor';
        bubble.appendChild(cursor);

        typewriterActive = true;
        var toggle = document.getElementById('fairy-toggle');
        toggle.classList.add('pulse');

        var idx = 0;
        var speed = 18;
        var textNode = document.createTextNode('');
        bubble.insertBefore(textNode, cursor);

        function typeNext() {
            if (idx < content.length) {
                textNode.textContent += content[idx];
                idx++;
                container.scrollTop = container.scrollHeight;
                var delay = speed;
                var ch = content[idx - 1];
                if (ch === '.' || ch === ':') delay = speed * 6;
                else if (ch === ',') delay = speed * 3;
                else if (ch === '\n') delay = speed * 4;
                setTimeout(typeNext, delay);
            } else {
                if (cursor.parentNode) cursor.parentNode.removeChild(cursor);
                typewriterActive = false;
                toggle.classList.remove('pulse');
                if (callback) callback();
            }
        }

        typeNext();
    }

    function addError(msg) {
        var container = document.getElementById('fairy-messages');
        var div = document.createElement('div');
        div.className = 'fairy-msg fairy-msg-fairy';
        div.innerHTML = '<div class="fairy-msg-bubble fairy-error">' + escapeHtml(msg) + '</div>';
        container.appendChild(div);
        container.scrollTop = container.scrollHeight;
    }

    function escapeHtml(text) {
        var d = document.createElement('div');
        d.textContent = text;
        return d.innerHTML;
    }

    function sendMessage() {
        if (isSending || typewriterActive) return;
        var input = document.getElementById('fairy-input');
        var message = (input.value || '').trim();
        if (!message) return;

        input.value = '';
        addMessage('user', message);
        history.push({ role: 'user', content: message });

        isSending = true;
        document.getElementById('fairy-send').disabled = true;
        document.getElementById('fairy-typing').classList.add('active');

        var toggle = document.getElementById('fairy-toggle');
        toggle.classList.add('pulse');

        var sendHistory = history.slice(-8);

        fetch('/api/fairy/ask', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: message, history: sendHistory })
        })
        .then(function(r) { return r.json(); })
        .then(function(data) {
            document.getElementById('fairy-typing').classList.remove('active');
            toggle.classList.remove('pulse');
            isSending = false;
            document.getElementById('fairy-send').disabled = false;

            if (data.error) {
                addError(data.error);
            } else {
                var reply = data.reply || 'The Void is silent.';
                typewriterMessage(reply, function() {
                    history.push({ role: 'assistant', content: reply });
                });
            }
        })
        .catch(function() {
            document.getElementById('fairy-typing').classList.remove('active');
            toggle.classList.remove('pulse');
            isSending = false;
            document.getElementById('fairy-send').disabled = false;
            addError('The frequency fades. The Fairy will return.');
        });
    }

    function init() {
        checkAuth(function(authed) {
            if (authed) createWidget();
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
