(function () {
  'use strict';

  var ROOT_ID = 'aiserver-widget-root';
  var STORAGE_HINT = 'aiserver-widget-hint-dismissed';
  var STORAGE_BADGE = 'aiserver-widget-badge-dismissed';
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

  if (document.getElementById(ROOT_ID)) {
    return;
  }

  var iconChat =
    '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H5.17L4 17.17V4h16v12z"/></svg>';
  var iconClose =
    '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/></svg>';

  var root = document.createElement('div');
  root.id = ROOT_ID;
  root.className = 'aiserver-widget';
  root.setAttribute('data-aiserver-widget', '1');

  var backdrop = document.createElement('div');
  backdrop.id = 'aiserver-widget-backdrop';
  backdrop.className = 'aiserver-backdrop';
  backdrop.setAttribute('aria-hidden', 'true');

  var panelWrap = document.createElement('div');
  panelWrap.id = 'aiserver-widget-panel-wrap';
  panelWrap.className = 'aiserver-panel-wrap';
  panelWrap.setAttribute('role', 'dialog');
  panelWrap.setAttribute('aria-modal', 'true');
  panelWrap.setAttribute('aria-label', config.title);
  panelWrap.setAttribute('aria-hidden', 'true');

  function buildChatIframeUrl(baseUrl) {
    var parentPage = window.location.href;
    try {
      var url = new URL(baseUrl, window.location.href);
      url.searchParams.set('parent', parentPage);
      return url.toString();
    } catch (e) {
      var sep = baseUrl.indexOf('?') >= 0 ? '&' : '?';
      return baseUrl + sep + 'parent=' + encodeURIComponent(parentPage);
    }
  }

  var iframe = document.createElement('iframe');
  iframe.id = 'aiserver-widget-iframe';
  iframe.className = 'aiserver-panel';
  iframe.src = buildChatIframeUrl(config.chatUrl);
  iframe.title = config.title;
  iframe.loading = 'lazy';
  iframe.setAttribute('allow', 'microphone');

  var chatPreloaded = false;
  function preloadChat() {
    if (chatPreloaded) {
      return;
    }
    chatPreloaded = true;
    iframe.loading = 'eager';
  }

  var hint = document.createElement('div');
  hint.id = 'aiserver-widget-hint';
  hint.setAttribute('role', 'tooltip');
  hint.innerHTML =
    '<span id="aiserver-widget-hint-text">Нужна помощь? Напишите администратору</span>' +
    '<button type="button" id="aiserver-widget-hint-close" aria-label="Закрыть подсказку">×</button>';

  var launcher = document.createElement('button');
  launcher.id = 'aiserver-widget-launcher';
  launcher.type = 'button';
  launcher.className = 'aiserver-launcher';
  launcher.setAttribute('aria-label', 'Открыть чат с администратором');
  launcher.setAttribute('aria-expanded', 'false');
  launcher.innerHTML = iconChat;

  var badge = document.createElement('span');
  badge.id = 'aiserver-widget-launcher-badge';
  badge.textContent = '1';
  badge.setAttribute('aria-hidden', 'true');
  launcher.appendChild(badge);

  panelWrap.appendChild(iframe);
  root.appendChild(backdrop);
  root.appendChild(panelWrap);
  root.appendChild(hint);
  root.appendChild(launcher);

  root.style.setProperty('--aiserver-z', String(config.zIndex));
  launcher.style.zIndex = String(config.zIndex);
  hint.style.zIndex = String(config.zIndex - 1);
  panelWrap.style.zIndex = String(config.zIndex - 1);
  backdrop.style.zIndex = String(config.zIndex - 2);

  var isOpen = false;
  var hintDismissed = false;
  var badgeDismissed = false;

  function storageGet(key) {
    try {
      return window.localStorage.getItem(key);
    } catch (e) {
      return null;
    }
  }

  function storageSet(key) {
    try {
      window.localStorage.setItem(key, '1');
    } catch (e) {}
  }

  function dismissHint() {
    if (hintDismissed) return;
    hintDismissed = true;
    hint.classList.remove('is-visible');
    hint.classList.add('is-hidden');
    storageSet(STORAGE_HINT);
  }

  function dismissBadge() {
    if (badgeDismissed) return;
    badgeDismissed = true;
    badge.classList.add('is-hidden');
    storageSet(STORAGE_BADGE);
  }

  function revealLauncher() {
    launcher.classList.add('is-revealed');
    preloadChat();
    if (!hintDismissed && !isOpen) {
      hint.classList.add('is-visible');
    }
  }

  if (storageGet(STORAGE_HINT)) {
    hintDismissed = true;
    hint.classList.add('is-hidden');
  }

  if (storageGet(STORAGE_BADGE)) {
    badgeDismissed = true;
    badge.classList.add('is-hidden');
  }

  function setOpen(open) {
    isOpen = open;
    panelWrap.classList.toggle('is-open', open);
    backdrop.classList.toggle('is-open', open);
    launcher.classList.toggle('is-active', open);
    launcher.setAttribute('aria-expanded', open ? 'true' : 'false');
    panelWrap.setAttribute('aria-hidden', open ? 'false' : 'true');
    backdrop.setAttribute('aria-hidden', open ? 'false' : 'true');
    launcher.setAttribute(
      'aria-label',
      open ? 'Закрыть чат' : 'Открыть чат с администратором'
    );
    launcher.innerHTML = open ? iconClose : iconChat;
    launcher.appendChild(badge);

    if (open) {
      dismissHint();
      dismissBadge();
      hint.classList.remove('is-visible');
    } else if (!hintDismissed) {
      hint.classList.add('is-visible');
    }
  }

  launcher.addEventListener('mouseenter', preloadChat, { once: true });
  launcher.addEventListener('click', function () {
    preloadChat();
    setOpen(!isOpen);
  });

  backdrop.addEventListener('click', function () {
    setOpen(false);
  });

  var hintClose = hint.querySelector('#aiserver-widget-hint-close');
  if (hintClose) {
    hintClose.addEventListener('click', function (event) {
      event.stopPropagation();
      dismissHint();
    });
  }

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

  var scrollRevealed = false;
  function onScroll() {
    if (scrollRevealed) return;
    if (window.scrollY > 80) {
      scrollRevealed = true;
      revealLauncher();
    }
  }

  window.addEventListener('scroll', onScroll, { passive: true });

  document.body.appendChild(root);

  window.setTimeout(function () {
    if (!scrollRevealed) {
      scrollRevealed = true;
      revealLauncher();
    }
  }, 1200);
})();
