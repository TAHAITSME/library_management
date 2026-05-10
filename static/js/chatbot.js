(function () {
  'use strict';

  const widget = document.querySelector('[data-chatbot]');
  if (!widget) return;

  const endpoint = widget.dataset.endpoint;
  const toggle = widget.querySelector('[data-chatbot-toggle]');
  const closeButtons = widget.querySelectorAll('[data-chatbot-close]');
  const clear = widget.querySelector('[data-chatbot-clear]');
  const panel = widget.querySelector('[data-chatbot-panel]');
  const form = widget.querySelector('[data-chatbot-form]');
  const input = widget.querySelector('[data-chatbot-input]');
  const messages = widget.querySelector('[data-chatbot-messages]');
  const suggestions = widget.querySelector('[data-chatbot-suggestions]');
  const status = widget.querySelector('[data-chatbot-status]');

  const STORAGE_KEY = 'biblionum.chatbot.history.v3';
  const MAX_HISTORY = 30;
  const DEFAULT_SUGGESTIONS = [
    'Catalogue',
    'Chercher un livre',
    'Reserver un livre',
    'Emprunter un livre',
    'Retourner un livre',
    'Mes commandes',
    'Mes emprunts',
    'Mes reservations',
    'Paiement',
    'Reclamation',
    'Aide generale'
  ];

  let history = [];
  let sending = false;
  let isOpen = false;

  function csrfToken() {
    const cookie = document.cookie
      .split(';')
      .map(item => item.trim())
      .find(item => item.startsWith('csrftoken='));
    if (cookie) return decodeURIComponent(cookie.split('=').slice(1).join('='));
    return widget.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
  }

  function escapeHtml(value) {
    const div = document.createElement('div');
    div.textContent = value || '';
    return div.innerHTML;
  }

  function scrollToBottom() {
    requestAnimationFrame(() => {
      messages.scrollTop = messages.scrollHeight;
    });
  }

  function saveHistory() {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(history.slice(-MAX_HISTORY)));
    } catch (error) {
      // localStorage can be unavailable in private contexts.
    }
  }

  function loadHistory() {
    try {
      const stored = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
      history = Array.isArray(stored) ? stored.slice(-MAX_HISTORY) : [];
    } catch (error) {
      history = [];
    }
  }

  function remember(entry) {
    history.push(entry);
    history = history.slice(-MAX_HISTORY);
    saveHistory();
  }

  function openPanel() {
    isOpen = true;
    panel.hidden = false;
    widget.classList.add('is-open');
    toggle.setAttribute('aria-expanded', 'true');
    toggle.setAttribute('aria-label', "Fermer l'assistant");
    setTimeout(() => input.focus(), 120);
    scrollToBottom();
  }

  function closePanel() {
    isOpen = false;
    widget.classList.add('is-closing');
    panel.hidden = true;
    widget.classList.remove('is-open');
    window.setTimeout(() => widget.classList.remove('is-closing'), 180);
    toggle.setAttribute('aria-expanded', 'false');
    toggle.setAttribute('aria-label', "Ouvrir l'assistant");
    toggle.focus();
  }

  function setSending(isSending) {
    sending = isSending;
    form.classList.toggle('is-sending', isSending);
    input.disabled = isSending;
    form.querySelector('button').disabled = isSending;
    if (status) {
      status.textContent = isSending ? "Assistant en train d'ecrire..." : 'Disponible pour vous aider';
    }
  }

  function addPlainMessage(text, type, shouldRemember = true) {
    const bubble = document.createElement('div');
    bubble.className = `chatbot-message chatbot-message--${type}`;
    bubble.setAttribute('role', type === 'user' ? 'status' : 'article');
    bubble.innerHTML = formatText(text);
    messages.appendChild(bubble);
    scrollToBottom();

    if (shouldRemember) {
      remember({ type, text: text || '' });
    }
    return bubble;
  }

  function formatText(text) {
    const paragraphs = String(text || '')
      .split(/\n+/)
      .map(part => part.trim())
      .filter(Boolean);
    if (!paragraphs.length) return '';
    return paragraphs.map(part => `<p>${escapeHtml(part)}</p>`).join('');
  }

  function normalizeList(items) {
    return Array.isArray(items) ? items.filter(Boolean).slice(0, 8) : [];
  }

  function renderRichMessage(data, shouldRemember = true) {
    const safeData = {
      answer: data?.answer || "Je peux vous aider avec la recherche d'un livre, une reservation, un emprunt, une commande ou un paiement.",
      results: normalizeList(data?.results),
      actions: normalizeList(data?.actions),
      suggestions: normalizeList(data?.suggestions)
    };

    const wrapper = document.createElement('div');
    wrapper.className = 'chatbot-message chatbot-message--bot chatbot-message--rich';

    const results = safeData.results.map(item => `
      <a class="chatbot-result" href="${escapeHtml(item.url || '#')}">
        <span class="chatbot-result__cover">
          ${item.cover ? `<img src="${escapeHtml(item.cover)}" alt="">` : '<i class="fas fa-book"></i>'}
        </span>
        <span class="chatbot-result__body">
          <strong>${escapeHtml(item.title || 'Resultat')}</strong>
          ${item.meta ? `<small>${escapeHtml(item.meta)}</small>` : ''}
          ${item.detail ? `<em>${escapeHtml(item.detail)}</em>` : ''}
        </span>
      </a>
    `).join('');

    const actions = safeData.actions.map(action => `
      <a class="chatbot-action" href="${escapeHtml(action.url || '#')}"><span>${escapeHtml(action.label || 'Ouvrir')}</span><i class="fas fa-arrow-right"></i></a>
    `).join('');

    wrapper.innerHTML = `
      ${formatText(safeData.answer)}
      ${results ? `<div class="chatbot-results">${results}</div>` : ''}
      ${actions ? `<div class="chatbot-actions">${actions}</div>` : ''}
    `;

    messages.appendChild(wrapper);
    renderSuggestions(safeData.suggestions.length ? safeData.suggestions : DEFAULT_SUGGESTIONS);
    scrollToBottom();

    if (shouldRemember) {
      remember({ type: 'bot', data: safeData });
    }
  }

  function renderSuggestions(items) {
    const prompts = normalizeList(items).slice(0, 6);
    suggestions.innerHTML = prompts.map(prompt => `
      <button type="button" data-chatbot-prompt="${escapeHtml(prompt)}">${escapeHtml(shortLabel(prompt))}</button>
    `).join('');
  }

  function shortLabel(prompt) {
    if (prompt.length <= 34) return prompt;
    return `${prompt.slice(0, 31).trim()}...`;
  }

  function showTyping() {
    const loading = document.createElement('div');
    loading.className = 'chatbot-message chatbot-message--bot chatbot-typing';
    loading.setAttribute('aria-label', "Assistant en train d'ecrire");
    loading.innerHTML = "<em>Assistant en train d'ecrire</em><span></span><span></span><span></span>";
    messages.appendChild(loading);
    scrollToBottom();
    return loading;
  }

  async function parseResponse(response) {
    const contentType = response.headers.get('content-type') || '';
    if (contentType.includes('application/json')) {
      return response.json();
    }
    return {
      answer: "Le serveur a retourne une reponse inattendue. Reessayez dans un moment.",
      results: [],
      actions: [],
      suggestions: DEFAULT_SUGGESTIONS
    };
  }

  async function ask(message) {
    const cleaned = String(message || '').trim();
    if (!cleaned || sending) return;

    addPlainMessage(cleaned, 'user');
    input.value = '';
    setSending(true);
    const loading = showTyping();

    try {
      const response = await fetch(endpoint, {
        method: 'POST',
        credentials: 'same-origin',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken()
        },
        body: JSON.stringify({ message: cleaned })
      });

      const data = await parseResponse(response);
      loading.remove();

      if (!response.ok) {
        renderRichMessage({
          answer: data.answer || "Je n'ai pas pu traiter cette demande.",
          results: [],
          actions: data.actions || [],
          suggestions: data.suggestions || DEFAULT_SUGGESTIONS
        });
        return;
      }

      renderRichMessage(data);
    } catch (error) {
      loading.remove();
      renderRichMessage({
        answer: "Impossible de joindre l'assistant pour le moment. Verifiez que le serveur Django est lance, puis reessayez.",
        results: [],
        actions: [],
        suggestions: DEFAULT_SUGGESTIONS
      });
    } finally {
      setSending(false);
      input.focus();
    }
  }

  function restoreHistory() {
    loadHistory();
    if (!history.length) {
      renderSuggestions(DEFAULT_SUGGESTIONS);
      return;
    }

    messages.innerHTML = '';
    history.forEach(entry => {
      if (entry.type === 'bot' && entry.data) {
        renderRichMessage(entry.data, false);
      } else {
        addPlainMessage(entry.text || '', entry.type || 'bot', false);
      }
    });
    scrollToBottom();
  }

  function clearConversation() {
    history = [];
    saveHistory();
    messages.innerHTML = '';
    addPlainMessage(
      'Conversation videe. Je peux vous aider avec le catalogue, les reservations, les emprunts, le panier, les commandes ou le paiement.',
      'bot',
      false
    );
    renderSuggestions(DEFAULT_SUGGESTIONS);
    input.focus();
  }

  toggle.addEventListener('click', () => {
    if (isOpen) closePanel();
    else openPanel();
  });

  closeButtons.forEach(button => {
    button.addEventListener('click', event => {
      event.preventDefault();
      event.stopPropagation();
      closePanel();
    });
  });
  clear.addEventListener('click', clearConversation);

  form.addEventListener('submit', event => {
    event.preventDefault();
    ask(input.value);
  });

  input.addEventListener('keydown', event => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      form.requestSubmit();
    }
  });

  suggestions.addEventListener('click', event => {
    const button = event.target.closest('[data-chatbot-prompt]');
    if (!button) return;
    openPanel();
    ask(button.dataset.chatbotPrompt);
  });

  restoreHistory();
})();
