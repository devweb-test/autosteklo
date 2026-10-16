/* Local compatibility boundary. Loaded before the original deferred scripts. */
(() => {
  const nativeFetch = window.fetch.bind(window);
  window.fetch = (input, options = {}) => {
    const url = typeof input === 'string' ? input : input.url;
    if (/^https?:/.test(url) && /(^|\.)((yandex\.(ru|net))|(yastatic\.net))$/.test(new URL(url).hostname)) return nativeFetch(input, options);
    return Promise.reject(new Error('Эта функция требует сервера оригинального сайта.'));
  };
  function notice(form, message) {
    let box = form.querySelector('.offline-form-notice');
    if (!box) { box = document.createElement('p'); box.className = 'offline-form-notice'; box.setAttribute('role', 'status'); form.append(box); }
    box.textContent = message;
  }
  function handleForm(form) {
    if (!form) return;
    const phone = form.querySelector('[name="phone"]');
    if (phone && phone.value.replace(/\D/g, '').length < 11) {
      phone.setAttribute('aria-invalid', 'true'); phone.focus(); notice(form, 'Введите полный номер телефона. Заявки из локальной копии не отправляются.'); return;
    }
    if (phone) phone.removeAttribute('aria-invalid');
    if (!form.reportValidity()) return;
    notice(form, 'Это локальная копия сайта. Данные не отправлены. Для записи позвоните по телефону 8 (800) 707-37-72 или откройте оригинальный сайт.');
  }
  document.addEventListener('submit', e => { e.preventDefault(); e.stopImmediatePropagation(); handleForm(e.target); }, true);
  document.addEventListener('click', e => {
    const filterItem=e.target.closest('#FBGlass .--filter-children-item');
    if(filterItem){
      e.preventDefault();e.stopImmediatePropagation();
      const field=filterItem.closest('#FBGlass');field.querySelector('input').value=filterItem.dataset.value;field.querySelector('p').textContent=filterItem.textContent.trim();field.classList.remove('active');
      notice(field.closest('form'),'Подбор марки, модели и стоимости требует каталога на сервере. Откройте autosteklo.pro или позвоните по телефону 8 (800) 707-37-72.');return;
    }
    const button = e.target.closest('.modal-typical__send, .--cb-form__btn, .question-form__btn, .departments-map-interface-form__btn, .text-form-btn');
    if (button) {
      e.preventDefault(); e.stopImmediatePropagation();
      const form = button.closest('form') || button.closest('.modal-base, .--cb-form-block')?.querySelector('form');
      handleForm(form);
    }
    const search = e.target.closest('#desktopSearchBtn');
    if (search) {e.preventDefault(); e.stopImmediatePropagation(); localSearch(document.querySelector('#desktopSearch')?.value || '');}
  }, true);
  document.addEventListener('keydown', e => {
    if (e.target.id === 'desktopSearch' && e.key === 'Enter') { e.preventDefault(); e.stopImmediatePropagation(); localSearch(e.target.value); }
    if (e.key === 'Escape') { try { window.modalsStream?.close(); } catch {} }
  }, true);
  function localSearch(query) {
    const target = window.OFFLINE_ROOT + 'blog/index.html';
    location.href = target + '?offline-search=' + encodeURIComponent(query);
  }
})();
