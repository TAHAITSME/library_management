/**
 * BiblioNUM — app.js
 * Modern vanilla JS — no jQuery dependency
 * Modules: Theme, Navbar, Toast, Dropdown, Mobile menu,
 *          Cart, Search, Animations, Form validation
 */

'use strict';

/* ================================================================
   0. CSRF HELPER — Django CSRF token management
   ================================================================ */
function getCsrfToken() {
  const name = 'csrftoken';
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

// Automatically add CSRF token to fetch requests
function secureFetch(url, options = {}) {
  const csrfToken = getCsrfToken();
  const headers = {
    'X-CSRFToken': csrfToken,
    ...(options.headers || {})
  };
  return fetch(url, { ...options, headers });
}

/* ================================================================
   1. THEME TOGGLE — dark / light
   ================================================================ */
const ThemeManager = (() => {
  const ROOT   = document.documentElement;
  const TOGGLE = document.querySelector('[data-theme-toggle]');
  const KEY    = 'lib-theme';

  const icons = {
    dark:  `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>`,
    light: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>`,
  };

  let current = (() => {
    try { return localStorage.getItem(KEY); } catch { return null; }
  })() || (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');

  function apply(theme) {
    ROOT.setAttribute('data-theme', theme);
    if (TOGGLE) {
      TOGGLE.innerHTML = icons[theme === 'dark' ? 'light' : 'dark'];
      TOGGLE.setAttribute('aria-label', `Passer en mode ${theme === 'dark' ? 'clair' : 'sombre'}`);
    }
    try { localStorage.setItem(KEY, theme); } catch {}
    current = theme;
  }

  function toggle() { apply(current === 'dark' ? 'light' : 'dark'); }

  if (TOGGLE) TOGGLE.addEventListener('click', toggle);
  apply(current);

  return { toggle, get current() { return current; } };
})();


/* ================================================================
   2. NAVBAR — scroll shadow + active link detection
   ================================================================ */
const NavbarManager = (() => {
  const navbar = document.querySelector('.lib-navbar');
  if (!navbar) return;

  // Scroll shadow
  const observer = new IntersectionObserver(
    ([entry]) => navbar.classList.toggle('scrolled', !entry.isIntersecting),
    { threshold: 0 }
  );
  const sentinel = document.createElement('div');
  sentinel.style.cssText = 'position:absolute;top:0;left:0;height:1px;width:1px;pointer-events:none;';
  document.body.prepend(sentinel);
  observer.observe(sentinel);

  // Auto-active nav links
  const path = window.location.pathname;
  document.querySelectorAll('.lib-nav-link[href]').forEach(link => {
    const href = link.getAttribute('href');
    if (href && href !== '/' && path.startsWith(href)) link.classList.add('active');
    else if (href === '/' && path === '/') link.classList.add('active');
  });
})();


/* ================================================================
   3. MOBILE MENU TOGGLE
   ================================================================ */
const MobileMenu = (() => {
  const toggle = document.getElementById('mobileToggle');
  const menu   = document.getElementById('mobileMenu');
  if (!toggle || !menu) return;

  const iconOpen  = `<i class="fas fa-bars"></i>`;
  const iconClose = `<i class="fas fa-times"></i>`;
  let open = false;

  toggle.addEventListener('click', () => {
    open = !open;
    menu.classList.toggle('is-open', open);
    toggle.innerHTML = open ? iconClose : iconOpen;
    toggle.setAttribute('aria-expanded', String(open));
  });

  // Close on outside click
  document.addEventListener('click', e => {
    if (open && !toggle.contains(e.target) && !menu.contains(e.target)) {
      open = false;
      menu.classList.remove('is-open');
      toggle.innerHTML = iconOpen;
      toggle.setAttribute('aria-expanded', 'false');
    }
  });
})();


/* ================================================================
   4. TOAST NOTIFICATIONS
   ================================================================ */
const Toast = (() => {
  let container = document.querySelector('.toast-container');

  function getOrCreateContainer() {
    if (!container) {
      container = document.createElement('div');
      container.className = 'toast-container';
      document.body.appendChild(container);
    }
    return container;
  }

  const CONFIG = {
    success: { icon: 'fa-circle-check',    label: 'Succès'      },
    danger:  { icon: 'fa-circle-xmark',    label: 'Erreur'      },
    error:   { icon: 'fa-circle-xmark',    label: 'Erreur'      },
    warning: { icon: 'fa-triangle-exclamation', label: 'Attention' },
    info:    { icon: 'fa-circle-info',     label: 'Information' },
  };

  function show(message, type = 'info', duration = 4200) {
    const cfg  = CONFIG[type] || CONFIG.info;
    const el   = document.createElement('div');
    el.className = `toast toast--${type}`;
    el.setAttribute('role', 'alert');
    el.innerHTML = `
      <div class="toast__stripe"></div>
      <i class="toast__icon fas ${cfg.icon}"></i>
      <div class="toast__body">
        <div class="toast__title">${cfg.label}</div>
        <div class="toast__msg">${message}</div>
      </div>
      <button class="toast__close" aria-label="Fermer">
        <i class="fas fa-xmark fa-xs"></i>
      </button>`;

    const c = getOrCreateContainer();
    c.appendChild(el);

    el.querySelector('.toast__close').addEventListener('click', () => dismiss(el));

    const timer = setTimeout(() => dismiss(el), duration);
    el._timer = timer;

    el.addEventListener('mouseenter', () => clearTimeout(el._timer));
    el.addEventListener('mouseleave', () => { el._timer = setTimeout(() => dismiss(el), 1500); });

    return el;
  }

  function dismiss(el) {
    el.style.animation = `toastOut 250ms cubic-bezier(0.4,0,1,1) both`;
    el.addEventListener('animationend', () => el.remove(), { once: true });
  }

  // Mount Django messages as toasts
  function mountDjangoMessages() {
    document.querySelectorAll('[data-toast]').forEach(el => {
      show(el.dataset.message, el.dataset.type || 'info');
      el.remove();
    });
  }

  document.addEventListener('DOMContentLoaded', mountDjangoMessages);

  return { show, dismiss };
})();


/* ================================================================
   5. CART INTERACTIONS
   ================================================================ */
const Cart = (() => {
  // Quantity steppers
  function initQuantitySteppers() {
    document.querySelectorAll('[data-qty-stepper]').forEach(wrapper => {
      const input = wrapper.querySelector('input[type="number"]');
      const dec   = wrapper.querySelector('[data-dec]');
      const inc   = wrapper.querySelector('[data-inc]');
      if (!input || !dec || !inc) return;

      const min = parseInt(input.min) || 1;
      const max = parseInt(input.max) || 999;

      function update(val) {
        const clamped = Math.min(max, Math.max(min, val));
        input.value = clamped;
        dec.disabled = clamped <= min;
        inc.disabled = clamped >= max;
        input.dispatchEvent(new Event('change', { bubbles: true }));
      }

      dec.addEventListener('click', () => update(parseInt(input.value) - 1));
      inc.addEventListener('click', () => update(parseInt(input.value) + 1));
      input.addEventListener('input', () => update(parseInt(input.value) || min));
      update(parseInt(input.value) || min);
    });
  }

  // Cart badge live update
  function updateBadge(count) {
    const badge = document.querySelector('.lib-cart-badge');
    if (!badge) return;
    badge.textContent = count;
    badge.style.display = count > 0 ? 'flex' : 'none';
    badge.animate([
      { transform: 'scale(1.4)', background: '#f59e0b' },
      { transform: 'scale(1)',   background: '' }
    ], { duration: 300, easing: 'cubic-bezier(0.16,1,0.3,1)' });
  }

  // Confirm remove
  document.addEventListener('click', e => {
    const btn = e.target.closest('[data-confirm-remove]');
    if (!btn) return;
    const label = btn.dataset.confirmRemove || 'cet article';
    if (!confirm(`Supprimer "${label}" du panier ?`)) e.preventDefault();
  });

  document.addEventListener('DOMContentLoaded', initQuantitySteppers);

  return { updateBadge };
})();


/* ================================================================
   6. SEARCH — autocomplete / live filter
   ================================================================ */
const Search = (() => {
  const bar  = document.querySelector('[data-search-input]');
  const list = document.querySelector('[data-search-results]');
  if (!bar || !list) return;

  let debounceTimer;

  function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  async function fetchResults(query) {
    if (!query || query.length < 2) { list.hidden = true; return; }
    try {
      const res = await fetch(`/catalog/search/?q=${encodeURIComponent(query)}&ajax=1`);
      if (!res.ok) return;
      const data = await res.json();
      renderResults(data.results || [], query);
    } catch (err) {
      console.error('Search error:', err);
    }
  }

  function renderResults(results, query) {
    if (!results.length) {
      list.innerHTML = `<div class="search-no-result">
        <i class="fas fa-magnifying-glass"></i> Aucun résultat pour "<strong>${escapeHtml(query)}</strong>"
      </div>`;
      list.hidden = false;
      return;
    }
    list.innerHTML = results.slice(0, 8).map(book => `
      <a href="${book.url}" class="search-result-item">
        <div class="search-result-cover">
          ${book.cover ? `<img src="${book.cover}" alt="${escapeHtml(book.title)}" loading="lazy">` : '<i class="fas fa-book"></i>'}
        </div>
        <div class="search-result-info">
          <strong>${highlight(book.title, query)}</strong>
          <small>${escapeHtml(book.author || '')}</small>
        </div>
        <span class="search-result-price">${book.price || ''} MAD</span>
      </a>`
    ).join('');
    list.hidden = false;
  }

  function highlight(text, query) {
    const escaped = query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    return escapeHtml(text).replace(new RegExp(`(${escaped})`, 'gi'), '<mark>$1</mark>');
  }

  bar.addEventListener('input', e => {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => fetchResults(e.target.value), 200);
  });

  document.addEventListener('click', e => {
    if (!bar.contains(e.target) && !list.contains(e.target)) list.hidden = true;
  });

  return {};
})();


/* ================================================================
   7. SMOOTH SCROLL ANCHOR LINKS
   ================================================================ */
document.addEventListener('click', e => {
  const link = e.target.closest('a[href^="#"]');
  if (!link) return;
  const id = link.getAttribute('href').slice(1);
  const target = document.getElementById(id);
  if (!target) return;
  e.preventDefault();
  target.scrollIntoView({ behavior: 'smooth' });
});


/* ================================================================
   8. FORM VALIDATION
   ================================================================ */
const FormValidator = (() => {
  function validateEmail(email) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  }

  function validateForm(form) {
    const inputs = form.querySelectorAll('input[required], textarea[required], select[required]');
    let valid = true;

    inputs.forEach(input => {
      if (!input.value.trim()) {
        input.classList.add('error');
        valid = false;
      } else if (input.type === 'email' && !validateEmail(input.value)) {
        input.classList.add('error');
        valid = false;
      } else {
        input.classList.remove('error');
      }
    });

    return valid;
  }

  document.addEventListener('submit', e => {
    if (!validateForm(e.target)) e.preventDefault();
  });

  return { validateEmail, validateForm };
})();


/* ================================================================
   9. INTERSECTION OBSERVER — Lazy animations
   ================================================================ */
const LazyAnimations = (() => {
  if (!window.IntersectionObserver) return;

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.style.animation = 'slideUp 600ms ease-out forwards';
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.1 });

  document.querySelectorAll('[data-animate]').forEach(el => observer.observe(el));
})();


/* ================================================================
   10. DROPDOWN MENUS
   ================================================================ */
const Dropdown = (() => {
  document.addEventListener('click', e => {
    const toggle = e.target.closest('[data-dropdown-toggle]');
    if (!toggle) {
      document.querySelectorAll('[data-dropdown].open').forEach(menu => menu.classList.remove('open'));
      return;
    }

    const menuId = toggle.dataset.dropdownToggle;
    const menu = document.getElementById(menuId);
    if (!menu) return;

    menu.classList.toggle('open');
    e.stopPropagation();
  });
})();


/* ================================================================
   11. AUTO-INITIALIZE ON DOM READY
   ================================================================ */
document.addEventListener('DOMContentLoaded', () => {
  // Remove loading states
  document.querySelectorAll('[data-loading]').forEach(el => el.removeAttribute('data-loading'));
  
  // Log initialization
  console.log('BiblioNUM — App initialized ✓');
});



/* ================================================================
   9. GLOBAL CART FUNCTIONS (for inline onclick handlers)
   ================================================================ */
function addToCart(bookId) {
  fetch(`/cart/add/${bookId}/`, {
    method: 'POST',
    headers: {
      'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || '',
      'Content-Type': 'application/json'
    }
  })
  .then(r => r.json())
  .then(data => {
    if (data.success) {
      Toast.show(`"${data.book_title}" ajouté au panier`, 'success');
      Cart.updateBadge(data.cart_count || 0);
    } else {
      Toast.show(data.message || 'Erreur lors de l\'ajout', 'danger');
    }
  })
  .catch(err => {
    console.error('Cart error:', err);
    Toast.show('Erreur serveur', 'danger');
  });
}

function borrowBook(bookId) {
  if (!confirm('Emprunter ce livre?')) return;
  
  fetch(`/borrowing/borrow/${bookId}/`, {
    method: 'POST',
    headers: {
      'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || '',
      'Content-Type': 'application/json'
    }
  })
  .then(r => r.json())
  .then(data => {
    if (data.success) {
      Toast.show(data.message || 'Livre emprunté avec succès', 'success');
      setTimeout(() => window.location.href = '/borrowing/', 1500);
    } else {
      Toast.show(data.message || 'Erreur lors de l\'emprunt', 'danger');
    }
  })
  .catch(err => {
    console.error('Borrow error:', err);
    Toast.show('Erreur serveur', 'danger');
  });
}

function reserveBook(bookId) {
  window.location.href = `/reservations/create/${bookId}/`;
}

function deleteAccount() {
  if (!confirm('Êtes-vous certain? Cette action est irréversible.')) return;
  
  fetch('/accounts/delete/', {
    method: 'POST',
    headers: {
      'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || '',
    }
  })
  .then(r => r.json())
  .then(data => {
    if (data.success) {
      Toast.show('Compte supprimé', 'warning');
      setTimeout(() => window.location.href = '/', 2000);
    } else {
      Toast.show(data.message || 'Erreur', 'danger');
    }
  })
  .catch(err => {
    console.error('Delete account error:', err);
    Toast.show('Erreur serveur', 'danger');
  });
}
