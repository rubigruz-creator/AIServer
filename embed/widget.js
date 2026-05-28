(function () {
  'use strict';

  var script = document.currentScript;
  var defaults = {
    chatUrl: 'https://agent.remont-gazon.ru/embed/chat.html',
    position: 'bottom-right',
    zIndex: 2147483000,
    title: 'Чат с администратором автосервиса',
  };

  var config = Object.assign({}, defaults, window.AIServerWidget || {});

  if (script) {
    if (script.dataset.chatUrl) config.chatUrl = script.dataset.chatUrl;
    if (script.dataset.zIndex) config.zIndex = parseInt(script.dataset.zIndex, 10);
  }

  if (document.getElementById('aiserver-widget-root')) {
    return;
  }

  var root = document.createElement('div');
  root.id = 'aiserver-widget-root';
  root.className = 'aiserver-widget';

  var backdrop = document.createElement('div');
  backdrop.className = 'aiserver-backdrop';
  backdrop.setAttribute('aria-hidden', 'true');

  var panelWrap = document.createElement('div');
  panelWrap.className = 'aiserver-panel-wrap';
  panelWrap.setAttribute('role', 'dialog');
  panelWrap.setAttribute('aria-label', config.title);
  panelWrap.setAttribute('aria-hidden', 'true');

  var iframe = document.createElement('iframe');
  iframe.className = 'aiserver-panel';
  iframe.src = config.chatUrl;
  iframe.title = config.title;
  iframe.loading = 'lazy';
  iframe.setAttribute('allow', 'microphone');

  var launcher = document.createElement('button');
  launcher.type = 'button';
  launcher.className = 'aiserver-launcher';
  launcher.setAttribute('aria-label', 'Открыть чат с администратором');
  launcher.setAttribute('aria-expanded', 'false');
  launcher.innerHTML =
    '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H5.17L4 17.17V4h16v12z"/></svg>';

  panelWrap.appendChild(iframe);
  root.appendChild(backdrop);
  root.appendChild(panelWrap);
  root.appendChild(launcher);

  root.style.setProperty('--aiserver-z', String(config.zIndex));
  launcher.style.zIndex = String(config.zIndex);
  panelWrap.style.zIndex = String(config.zIndex - 1);
  backdrop.style.zIndex = String(config.zIndex - 2);

  var isOpen = false;

  function setOpen(open) {
    isOpen = open;
    panelWrap.classList.toggle('is-open', open);
    backdrop.classList.toggle('is-open', open);
    launcher.setAttribute('aria-expanded', open ? 'true' : 'false');
    panelWrap.setAttribute('aria-hidden', open ? 'false' : 'true');
    launcher.setAttribute(
      'aria-label',
      open ? 'Закрыть чат' : 'Открыть чат с администратором'
    );
  }

  launcher.addEventListener('click', function () {
    setOpen(!isOpen);
  });

  backdrop.addEventListener('click', function () {
    setOpen(false);
  });

  document.addEventListener('keydown', function (event) {
    if (event.key === 'Escape' && isOpen) {
      setOpen(false);
    }
  });

  window.addEventListener('message', function (event) {
    if (event.data && event.data.type === 'aiserver-widget-close') {
      setOpen(false);
    }
  });

  document.body.appendChild(root);
})();
