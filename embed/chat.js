(function () {
  'use strict';

  var API_URL = '/embed/ollama/chat';
  var MODEL = 'truck-service:latest';
  var messagesEl = document.getElementById('messages');
  var inputEl = document.getElementById('input');
  var sendBtn = document.getElementById('send');
  var closeBtn = document.getElementById('close');
  var history = [];
  var busy = false;

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

  async function streamAssistantReply(userText) {
    history.push({ role: 'user', content: userText });

    var assistantEl = appendMessage('assistant', '');
    var typingEl = document.createElement('div');
    typingEl.className = 'typing';
    typingEl.textContent = 'Печатает…';
    messagesEl.appendChild(typingEl);
    messagesEl.scrollTop = messagesEl.scrollHeight;

    var assistantText = '';

    try {
      var response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model: MODEL,
          stream: true,
          messages: history,
        }),
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

      typingEl.remove();

      var reader = response.body.getReader();
      var decoder = new TextDecoder();
      var buffer = '';

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
            assistantText += delta;
            assistantEl.textContent = assistantText;
            messagesEl.scrollTop = messagesEl.scrollHeight;
          }
        }
      }

      if (!assistantText) {
        assistantEl.textContent = 'Извините, не удалось получить ответ. Попробуйте ещё раз.';
      } else {
        history.push({ role: 'assistant', content: assistantText });
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

  appendMessage(
    'system',
    'Здравствуйте! Я помогу записать ваш грузовой автомобиль на обслуживание. Напишите, с чего начнём — марка и модель авто.'
  );
})();
