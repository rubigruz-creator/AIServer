(function () {
  'use strict';

  // RAG + Ollama через intake-api (см. .docs/KNOWLEDGE-PIPELINE.md)
  var API_URL = '/intake/api/chat';
  var INTAKE_API = '/intake/api';
  var SESSION_KEY = 'aiserver_session_id';
  var MODEL = 'truck-service:latest';
  var KEEP_ALIVE = '30m';
  var messagesEl = document.getElementById('messages');
  var inputEl = document.getElementById('input');
  var sendBtn = document.getElementById('send');
  var closeBtn = document.getElementById('close');
  var history = [];
  var busy = false;
  var warmupStarted = false;

  function getSessionId() {
    var id = localStorage.getItem(SESSION_KEY);
    if (!id) {
      id =
        'sess_' +
        Date.now().toString(36) +
        '_' +
        Math.random().toString(36).slice(2, 12);
      localStorage.setItem(SESSION_KEY, id);
    }
    return id;
  }

  function logMessage(role, content) {
    fetch(INTAKE_API + '/messages', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: getSessionId(),
        role: role,
        content: content,
      }),
    }).catch(function (err) {
      console.warn('[AIServer intake] message', err);
    });
  }

  function getSourceUrl() {
    try {
      var parent = new URLSearchParams(window.location.search).get('parent');
      if (parent) {
        return parent;
      }
    } catch (e) {
      /* ignore */
    }
    return document.referrer || '';
  }

  async function ensureSession() {
    try {
      await fetch(INTAKE_API + '/session', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: getSessionId(),
          source_url: getSourceUrl(),
          user_agent: navigator.userAgent || '',
        }),
      });
    } catch (err) {
      console.warn('[AIServer intake] session', err);
    }
  }

  /** Фоновый прогрев: модель остаётся в RAM до первого сообщения пользователя */
  function warmupModel() {
    if (warmupStarted) {
      return;
    }
    warmupStarted = true;
    fetch(API_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: MODEL,
        stream: false,
        keep_alive: KEEP_ALIVE,
        messages: [{ role: 'user', content: '.' }],
        options: { num_predict: 1 },
      }),
    }).catch(function (err) {
      console.warn('[AIServer chat] warmup', err);
      warmupStarted = false;
    });
  }

  function appendMessage(role, text) {
    var el = document.createElement('div');
    el.className = 'message ' + role;
    el.textContent = text;
    messagesEl.appendChild(el);
    messagesEl.scrollTop = messagesEl.scrollHeight;
    return el;
  }

  function setBusy(state) {
    busy = state;
    sendBtn.disabled = state;
    inputEl.disabled = state;
  }

  function parseJsonLine(raw) {
    if (!raw) {
      return null;
    }
    try {
      return JSON.parse(raw);
    } catch (err) {
      return null;
    }
  }

  function chatRequestBody(messages) {
    return {
      model: MODEL,
      stream: true,
      keep_alive: KEEP_ALIVE,
      messages: messages,
    };
  }

  async function streamAssistantReply(userText) {
    history.push({ role: 'user', content: userText });

    var assistantEl = appendMessage('assistant', '');
    var typingEl = document.createElement('div');
    typingEl.className = 'typing';
    typingEl.textContent = 'Секунду, готовлю ответ…';
    messagesEl.appendChild(typingEl);
    messagesEl.scrollTop = messagesEl.scrollHeight;

    var assistantText = '';

    try {
      var response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(chatRequestBody(history)),
      });

      if (!response.ok) {
        var errBody = '';
        try {
          errBody = await response.text();
        } catch (e) {
          errBody = response.statusText;
        }
        throw new Error('HTTP ' + response.status + ': ' + errBody);
      }

      if (!response.body) {
        throw new Error('Streaming не поддерживается браузером');
      }

      var reader = response.body.getReader();
      var decoder = new TextDecoder();
      var buffer = '';
      var firstToken = false;

      while (true) {
        var readResult = await reader.read();
        if (readResult.done) {
          break;
        }

        buffer += decoder.decode(readResult.value, { stream: true });
        var parts = buffer.split('\n');
        buffer = parts.pop() || '';

        for (var i = 0; i < parts.length; i++) {
          var line = parts[i].trim();
          var chunk = parseJsonLine(line);
          if (!chunk) {
            continue;
          }
          var delta = '';
          if (chunk.message && typeof chunk.message.content === 'string') {
            delta = chunk.message.content;
          }
          if (delta) {
            if (!firstToken) {
              firstToken = true;
              if (typingEl.parentNode) {
                typingEl.remove();
              }
            }
            assistantText += delta;
            assistantEl.textContent = assistantText;
            messagesEl.scrollTop = messagesEl.scrollHeight;
          }
        }
      }

      if (typingEl.parentNode) {
        typingEl.remove();
      }

      if (!assistantText) {
        assistantEl.textContent =
          'Извините, не удалось получить ответ. Попробуйте ещё раз.';
      } else {
        history.push({ role: 'assistant', content: assistantText });
        logMessage('assistant', assistantText);
      }
    } catch (err) {
      if (typingEl.parentNode) {
        typingEl.remove();
      }
      assistantEl.remove();
      appendMessage(
        'error',
        'Ошибка связи с сервером. Попробуйте позже или позвоните в автосервис.'
      );
      console.error('[AIServer chat]', err);
    }
  }

  async function handleSend() {
    var text = inputEl.value.trim();
    if (!text || busy) {
      return;
    }

    inputEl.value = '';
    appendMessage('user', text);
    logMessage('user', text);
    setBusy(true);
    await streamAssistantReply(text);
    setBusy(false);
    inputEl.focus();
  }

  sendBtn.addEventListener('click', handleSend);

  inputEl.addEventListener('keydown', function (event) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSend();
    }
  });

  if (closeBtn) {
    closeBtn.addEventListener('click', function () {
      if (window.parent && window.parent !== window) {
        window.parent.postMessage({ type: 'aiserver-widget-close' }, '*');
      }
    });
  }

  var welcomeText =
    'Здравствуйте! Я помогу записать ваш грузовой автомобиль на обслуживание. Напишите, с чего начнём — марка и модель авто.';

  ensureSession().then(function () {
    appendMessage('system', welcomeText);
    logMessage('system', welcomeText);
    warmupModel();
  });
})();
