/* Offline catalogue UI. No customer data is stored or sent to a server. */
(() => {
  'use strict';
  const root = document.querySelector('.cr-root');
  if (!root || !window.CRO_DATA) return;
  const data = window.CRO_DATA, base = root.dataset.root, kind = root.dataset.kind;
  const $ = (selector, parent = root) => parent.querySelector(selector);
  const $$ = (selector, parent = root) => [...parent.querySelectorAll(selector)];
  const escape = value => String(value ?? '').replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
  const money = value => value === null ? 'Уточнить цену' : new Intl.NumberFormat('ru-RU').format(value) + ' ₽';
  const read = key => { try { return JSON.parse(sessionStorage.getItem('cro:' + key)); } catch { return null; } };
  const save = (key, value) => { try { sessionStorage.setItem('cro:' + key, JSON.stringify(value)); } catch {} };
  const params = new URLSearchParams(location.search);
  const defaults = {glass:'windshield',year:'',side:'any',door:'any',movement:'any',hud:'any',camera:'any',rain:'any',heating:'any',athermal:'any',brand:'',stock:false,sort:'recommended',limit:6};
  const cached = read('filters') || {};
  const state = {...defaults, ...cached};
  for (const key of Object.keys(defaults)) if (params.has(key)) state[key] = params.get(key);
  state.stock = state.stock === true || state.stock === 'true';
  state.limit = Math.max(6, Math.min(36, Number(state.limit) || 6));
  const enumValues = {glass:['windshield','rear','side'],side:['any','left','right'],door:['any','front','back'],movement:['any','moving','fixed'],sort:['recommended','price','price-desc','brand']};
  for (const key of ['hud','camera','rain','heating','athermal']) enumValues[key] = ['any','yes','no','unknown'];
  for (const [key, values] of Object.entries(enumValues)) if (!values.includes(state[key])) state[key] = defaults[key];
  if (!data.products.some(p => p.brand === state.brand)) state.brand = '';
  if (state.year && !/^(201[89]|202[0-6])$/.test(state.year)) state.year = '';
  let mode = (params.get('mode') || read('mode')) === 'glass' ? 'glass' : 'install';
  let center = params.get('center') || read('center') || '';
  const centers = {val:'Городской Вал, 2',gromova:'Громова, 1Ж'};
  if (!(center in centers)) center = '';
  const candidates = params.has('compare') ? params.get('compare').split(',') : read('compare') || [];
  let compared = [...new Set(candidates)].filter(id => data.products.some(p => p.id === id)).slice(0,3);
  const get = id => data.products.find(p => p.id === String(id));
  const current = get('92644');
  const labels = {hud:'HUD',camera:'Камера',rain:'Датчик дождя',heating:'Обогрев',athermal:'Атермальность'};
  const optionText = value => value === true ? 'Есть по каталогу' : value === false ? 'Нет по каталогу' : 'Не подтверждено';
  const glassName = () => ({windshield:'Лобовое',rear:'Заднее',side:'Боковое'}[state.glass]);
  const total = p => p.price === null ? null : p.price + (mode === 'install' ? p.service : 0);
  const emit = (event, product) => document.dispatchEvent(new CustomEvent('catalog:interaction', {detail:{event, ...(product ? {productId:product.id} : {}), mode, city:'Ярославль'}}));
  let toastTimer;
  function toast(message) {
    const el = $('#cr-toast'); el.textContent = message; el.hidden = false;
    clearTimeout(toastTimer); toastTimer = setTimeout(() => { el.hidden = true; }, 4200);
  }
  function persist() {
    save('filters',state); save('mode',mode); save('center',center); save('compare',compared);
    const query = new URLSearchParams(location.search);
    for (const key of Object.keys(defaults)) {
      if (state[key] !== defaults[key]) query.set(key,String(state[key])); else query.delete(key);
    }
    mode === 'glass' ? query.set('mode','glass') : query.delete('mode');
    center ? query.set('center',center) : query.delete('center');
    compared.length ? query.set('compare',compared.join(',')) : query.delete('compare');
    try { history.replaceState(null,'',location.pathname + (query.size ? '?' + query : '') + location.hash); } catch {}
  }
  function link(path) {
    const url = new URL(base + path, location.href);
    for (const [key,value] of Object.entries(state)) if (value !== defaults[key]) url.searchParams.set(key,String(value));
    if (mode === 'glass') url.searchParams.set('mode','glass');
    if (center) url.searchParams.set('center',center);
    if (compared.length) url.searchParams.set('compare',compared.join(','));
    return url.href;
  }
  function estimate(p) {
    return `<dl><div><dt>Стекло</dt><dd>${money(p.price)}</dd></div>${mode === 'install' ? `<div><dt>Замена</dt><dd>${money(p.service)}</dd></div>` : ''}<div class="cr-total"><dt>${mode === 'install' ? 'Подытог' : 'Только стекло'}</dt><dd>${money(total(p))}</dd></div></dl>`;
  }
  function actionLabel(p) { return p.price === null ? 'Уточнить цену и срок' : mode === 'install' ? 'Заявка на установку' : 'Заявка на стекло'; }
  function card(p) {
    const selected = compared.includes(p.id);
    const tags = Object.entries(labels).filter(([key]) => p.options[key] === true).map(([,label]) => `<span>${label}</span>`).join('');
    return `<article class="cr-glass-card" data-product="${p.id}"><div class="cr-glass-info"><img class="cr-brand-logo" src="${base + escape(p.brandImage)}" alt="${escape(p.brand)}" width="120" height="50" loading="lazy"><h3>${p.path.endsWith('/' + data.productPage.split('/')[1] + '/') ? `<a href="${link(data.productPage)}">` : ''}Лобовое стекло Audi Q8 · ${escape(p.brand)}${p.id === '92644' ? '</a>' : ''}</h3><div class="cr-tags">${tags}</div><p class="cr-small cr-muted">${p.options.hud === null ? 'HUD не подтверждён. ' : ''}${p.options.heating === null ? 'Обогрев не подтверждён.' : ''}</p><p class="cr-small cr-code">Eurocode: ${escape(p.eurocode)}<br>OEM: ${escape(p.oem)}</p><p class="cr-small cr-stock">${p.stock ? 'Было в наличии в снимке' : 'Под заказ в снимке'} · ${data.date}<br>Срок и наличие в центре уточняются.</p><details class="cr-card-details"><summary>Все параметры</summary><p>${escape(p.title)}</p><p>Точную применимость проверяют по VIN.</p>${p.id !== '92644' ? `<a href="https://autosteklo.pro${escape(p.path)}" target="_blank" rel="noopener">Карточка на сайте онлайн</a>` : ''}</details></div><div class="cr-glass-buy"><div class="cr-estimate">${estimate(p)}</div><button type="button" class="cr-btn cr-full" data-order="${p.id}">${actionLabel(p)}</button><button type="button" class="cr-compare-toggle" data-compare="${p.id}" aria-pressed="${selected}">${selected ? 'Убрать из сравнения' : 'Добавить в сравнение'}</button></div></article>`;
  }
  function matching() {
    if (state.glass !== 'windshield') return [];
    const list = data.products.filter(p => (!state.brand || p.brand === state.brand) && (!state.stock || (p.stock && p.price !== null)) && Object.keys(labels).every(key => state[key] === 'yes' ? p.options[key] === true : state[key] === 'no' ? p.options[key] === false : true));
    return list.sort((a,b) => {
      if (state.sort === 'brand') return a.brand.localeCompare(b.brand,'ru') || Number(a.id)-Number(b.id);
      if (a.price === null && b.price !== null) return 1;
      if (b.price === null && a.price !== null) return -1;
      if (state.sort === 'price' || state.sort === 'price-desc') return ((a.price ?? 0)-(b.price ?? 0)) * (state.sort === 'price' ? 1 : -1) || Number(a.id)-Number(b.id);
      return Number(b.stock)-Number(a.stock) || Number(a.id)-Number(b.id);
    });
  }
  function syncFilters() {
    const form = $('#cr-filter-form'); if (!form) return;
    for (const el of form.elements) if (el.name in state) {
      if (el.type === 'checkbox') el.checked = state[el.name]; else el.value = state[el.name];
    }
    $('#cr-sort').value = state.sort;
    $('#cr-side-options').hidden = state.glass !== 'side';
    if ($('#cr-glass')) $('#cr-glass').value=state.glass;
    if ($('#cr-year')) $('#cr-year').value=state.year;
  }
  function renderProducts() {
    if (!$('#cr-products')) return;
    const records = matching();
    $('#cr-count').textContent = `${records.length} ${records.length === 1 ? 'вариант' : 'вариантов'} по вашему подбору`;
    $('#cr-products').innerHTML = records.length ? records.slice(0,state.limit).map(card).join('') : `<div class="cr-empty"><h3>${state.glass !== 'windshield' ? 'Этот тип стекла не сохранён в офлайн-каталоге' : 'Стёкла по этим условиям не найдены'}</h3><p>${state.glass !== 'windshield' ? 'Здесь доступны 33 лобовых стекла Audi Q8. Боковое или заднее стекло можно подобрать по VIN / фото.' : 'Попробуйте убрать один фильтр. «Нет» исключает товары, у которых отсутствие опции не подтверждено.'}</p><button type="button" class="cr-btn cr-outline" data-reset>Сбросить фильтры</button> <button type="button" class="cr-btn" data-help>Помочь с подбором</button></div>`;
    $('#cr-more').hidden = records.length <= state.limit;
    $('#cr-shown').textContent = records.length ? `Показано ${Math.min(records.length,state.limit)} из ${records.length}` : 'Выбранные условия сохранены.';
    const chips = [];
    for (const key of Object.keys(defaults)) {
      if (['sort','limit','side','door','movement'].includes(key) || state[key] === defaults[key]) continue;
      const label = key === 'glass' ? glassName() : key === 'brand' ? state.brand : key === 'stock' ? 'С наличием в снимке' : key === 'year' ? state.year : `${labels[key]}: ${{yes:'есть',no:'нет',unknown:'не знаю'}[state[key]]}`;
      chips.push(`<button type="button" class="cr-chip" data-remove-filter="${key}" aria-label="Убрать фильтр ${escape(label)}">${escape(label)} <span aria-hidden="true">×</span></button>`);
    }
    $('#cr-filter-chips').innerHTML = chips.join('');
    syncFilters();
  }
  function renderProduct() {
    if (kind !== 'product') return;
    $('#cr-product-estimate').innerHTML = estimate(current);
    $('[data-order="92644"]', $('.cr-buy')).textContent = actionLabel(current);
    const alternatives = data.products.filter(p => p.id !== current.id && p.eurocode === current.eurocode && p.oem === current.oem).sort((a,b) => (a.price ?? Infinity)-(b.price ?? Infinity));
    $('#cr-alternatives').innerHTML = alternatives.slice(0,3).map(card).join('');
  }
  function syncModes() {
    $$('[data-mode]').forEach(el => { const active = el.dataset.mode === mode; el.setAttribute('aria-pressed',String(active)); el.classList.toggle('cr-outline',!active); });
  }
  function syncCompare() {
    $$('[data-compare]').forEach(el => { const on = compared.includes(el.dataset.compare); el.setAttribute('aria-pressed',String(on)); el.textContent = on ? 'Убрать из сравнения' : 'Добавить в сравнение'; });
    const bottom = $('#cr-bottom');
    if (compared.length) {
      bottom.hidden = false; bottom.classList.remove('cr-product-bar');
      bottom.innerHTML = `<div><strong>В сравнении: ${compared.length} из 3</strong><span class="cr-small">${compared.map(id => escape(get(id).brand)).join(' · ')}</span></div><button type="button" class="cr-btn" data-open-compare ${compared.length < 2 ? 'disabled' : ''}>Сравнить${compared.length < 2 ? ' · выберите ещё' : ''}</button><button type="button" class="cr-clear-compare" data-clear-compare aria-label="Очистить сравнение">×</button>`;
    } else if (kind === 'product') {
      bottom.hidden = false; bottom.classList.add('cr-product-bar');
      bottom.innerHTML = `<div><span class="cr-small">${mode === 'install' ? 'Стекло + замена' : 'Только стекло'}</span><strong>${money(total(current))}</strong></div><button type="button" class="cr-btn" data-order="92644">${mode === 'install' ? 'Заявка на установку' : 'Заявка на стекло'}</button>`;
    } else bottom.hidden = true;
    document.body.classList.toggle('cr-has-bottom',!bottom.hidden);
  }
  function compareTable() {
    const list = compared.map(get);
    const row = (title, fn, cls='') => `<tr class="${cls}"><th scope="row">${title}</th>${list.map(p => `<td>${fn(p)}</td>`).join('')}</tr>`;
    $('#cr-compare-content').innerHTML = `<table class="cr-compare-table"><thead><tr><th scope="col">Параметр</th>${list.map(p => `<th scope="col">${escape(p.brand)}<br><span class="cr-small">Арт. ${p.id}</span><button type="button" class="cr-text-button" data-remove-compare="${p.id}">Убрать</button></th>`).join('')}</tr></thead><tbody>${row('Eurocode',p => escape(p.eurocode))}${row('OEM',p => escape(p.oem))}${Object.entries(labels).map(([key,label]) => row(label,p => optionText(p.options[key]))).join('')}${row('Стекло',p => money(p.price))}${row('Замена',p => mode === 'install' ? money(p.service) : 'Не выбрана')}${row('Подытог',p => money(total(p)),'cr-total')}${row('Гарантия на стекло',p => p.brand === 'AGC' ? 'Условия программы AGC уточняются для заказа' : 'Условия производителя уточняются для заказа')}${row('Срок / центр',() => 'Нужно подтвердить для выбранного центра')}${row('Выбрать',p => `<button type="button" class="cr-btn" data-order="${p.id}">${actionLabel(p)}</button>`)}</tbody></table><p class="cr-small">Подытог включает только выбранные позиции. Дополнительные работы согласуются после проверки. Совпадение кодов не заменяет проверку по VIN.</p>`;
  }
  function updateCenter() {
    $$('[data-center-label]').forEach(el => { el.textContent = centers[center] || 'выбрать центр'; });
    $$('[data-center]').forEach(el => { const on = el.dataset.center === center; el.textContent = on ? 'Центр выбран' : 'Выбрать центр'; el.setAttribute('aria-pressed',String(on)); });
    $('#cr-center-status').textContent = center ? `Выбран центр: ${centers[center]}. Наличие и время установки нужно подтвердить.` : 'Наличие на складе поставщика не означает наличие в центре.';
  }
  function refresh() { syncModes(); renderProducts(); renderProduct(); syncCompare(); updateCenter(); persist(); }

  // Directory search supports common Russian names and Latin spellings.
  const aliases = {AUDI:'ауди',ACURA:'акура',BMW:'бмв',MERCEDES:'мерседес',VOLKSWAGEN:'фольксваген',TOYOTA:'тойота',KIA:'киа',HYUNDAI:'хендай хёндай',SKODA:'шкода',FORD:'форд',RENAULT:'рено',NISSAN:'ниссан',CHERY:'чери',GEELY:'джили',HAVAL:'хавал',LADA:'лада ваз',VOLVO:'вольво',Q8:'ку8 кью8'};
  function transliterate(text) {
    const map={а:'a',б:'b',в:'v',г:'g',д:'d',е:'e',ё:'e',ж:'zh',з:'z',и:'i',й:'i',к:'k',л:'l',м:'m',н:'n',о:'o',п:'p',р:'r',с:'s',т:'t',у:'u',ф:'f',х:'h',ц:'ts',ч:'ch',ш:'sh',щ:'sh',ъ:'',ы:'y',ь:'',э:'e',ю:'yu',я:'ya'};
    return text.toLowerCase().split('').map(ch => map[ch] ?? ch).join('');
  }
  const directorySearch = $('#cr-directory-search');
  function searchDirectory() {
    if (!directorySearch) return;
    const q = directorySearch.value.trim().toLowerCase().replace(/\s/g,''); let visible=0;
    $$('[data-directory-name]').forEach(el => {
      const name = el.dataset.directoryName;
      const text = (name + ' ' + (aliases[name] || '')).toLowerCase().replace(/\s/g,'');
      el.hidden = q && !text.includes(q) && !transliterate(text).includes(transliterate(q));
      if (!el.hidden) visible++;
    });
    $('#cr-directory-count').textContent = `Найдено: ${visible}`;
    $('#cr-directory-empty').hidden = visible > 0;
    save('search:'+kind,directorySearch.value);
  }
  if (directorySearch) {
    directorySearch.value = params.get('q') || read('search:'+kind) || '';
    directorySearch.addEventListener('input',searchDirectory); searchDirectory();
  }
  const picker = $('#cr-picker');
  function fillModels(selected='') {
    if (!picker) return;
    const brand = $('#cr-brand').value;
    const model = $('#cr-model');
    model.innerHTML = brand === 'AUDI' ? '<option value="">Выберите модель</option>'+data.models.map(m => `<option value="${escape(m.name)}">${escape(m.name)}</option>`).join('') : '<option value="">Модели доступны онлайн</option>';
    model.disabled = brand !== 'AUDI'; model.value = selected;
    $('#cr-picker-note').textContent = brand && brand !== 'AUDI' ? 'Для этой марки каталог доступен на основном сайте. Кнопка откроет его онлайн.' : 'Для Audi Q8 сохранён полный список из 33 лобовых стёкол. Другие модели доступны на сайте онлайн.';
    $('#cr-year').disabled = brand !== 'AUDI' || model.value !== 'Q8';
  }
  if (picker) {
    if (kind === 'model' || kind === 'generation') { $('#cr-brand').value='AUDI'; fillModels('Q8'); }
    else {
      const storedPicker=read('picker');
      if(kind==='catalog'&&storedPicker&&data.brands.some(b=>b.name===storedPicker.brand))$('#cr-brand').value=storedPicker.brand;
      fillModels(storedPicker&&$('#cr-brand').value==='AUDI'?storedPicker.model:'');
    }
    $('#cr-year').value = state.year; $('#cr-glass').value=state.glass;
    $('#cr-brand').addEventListener('change',() => fillModels());
    $('#cr-model').addEventListener('change',() => { $('#cr-year').disabled = $('#cr-model').value !== 'Q8'; });
    picker.addEventListener('submit',event => {
      event.preventDefault(); event.stopPropagation();
      const brand = $('#cr-brand').value, model = $('#cr-model').value;
      if (!brand) { $('#cr-brand').focus(); toast('Выберите марку автомобиля.'); return; }
      state.year=$('#cr-year').disabled ? '' : $('#cr-year').value; state.glass=$('#cr-glass').value; state.limit=6; persist();
      save('picker',{brand,model});
      if (brand === 'AUDI' && model === 'Q8') location.href=link('catalog/audi/q8/index.html');
      else if (brand === 'AUDI' && !model) location.href=link('catalog/audi/index.html');
      else {
        const record = brand === 'AUDI' ? data.models.find(m=>m.name===model) : data.brands.find(b=>b.name===brand);
        if (record) location.href=record.url;
      }
    });
  }
  const filterForm = $('#cr-filter-form');
  if (filterForm) {
    filterForm.addEventListener('change',event => {
      const el=event.target; if (!(el.name in state)) return;
      state[el.name] = el.type === 'checkbox' ? el.checked : el.value; state.limit=6;
      if (el.name === 'glass') $('#cr-glass').value=state.glass;
      if (el.name === 'year') $('#cr-year').value=state.year;
      renderProducts(); persist(); emit('filter_change');
    });
    filterForm.addEventListener('reset',event => { event.preventDefault(); Object.assign(state,defaults); renderProducts(); persist(); });
    $('#cr-sort').addEventListener('change',event => { state.sort=event.target.value; state.limit=6; renderProducts(); persist(); });
    $('#cr-more').addEventListener('click',() => { const previous=state.limit; state.limit+=6; renderProducts(); persist(); const added=$$('.cr-glass-card')[previous]; if(added) { added.tabIndex=-1;added.focus({preventScroll:true}); } });
    if (matchMedia('(max-width: 760px)').matches) $('#cr-filters').open=false;
  }

  const orderDialog=$('#cr-order-dialog'), compareDialog=$('#cr-compare-dialog'), orderForm=$('#cr-order-form');
  let ordered=null, previousFocus=null, objectUrls=[], assistance={glass:'Лобовое',year:'',details:[]};
  function openDialog(dialog) {
    if (compareDialog.open) compareDialog.close();
    previousFocus=document.activeElement; dialog.showModal(); document.body.classList.add('cr-dialog-open');
  }
  [orderDialog,compareDialog].forEach(dialog => {
    dialog.addEventListener('close',() => {
      if (!$('dialog[open]')) document.body.classList.remove('cr-dialog-open');
      if (previousFocus?.isConnected) previousFocus.focus({preventScroll:true});
    });
    dialog.addEventListener('click',event => { if(event.target===dialog) { const rect=dialog.getBoundingClientRect();if(event.clientX<rect.left||event.clientX>rect.right||event.clientY<rect.top||event.clientY>rect.bottom)dialog.close(); } });
  });
  function orderSummary() {
    const car=ordered ? `Audi Q8 · ${ordered.brand} · арт. ${ordered.id}` : (orderForm.elements.car.value || 'Подбор по VIN / фото');
    const options=ordered ? Object.entries(labels).filter(([key])=>ordered.options[key]===true).map(([,label])=>label).join(' · ') : `${assistance.glass} стекло · ${assistance.year || 'год уточняется'}${assistance.details.length ? ' · '+assistance.details.join(' · ') : ''}`;
    $('#cr-order-summary').innerHTML=`<strong>${escape(car)}</strong><p>${escape(options)}</p><p>Ярославль · ${escape(centers[center] || 'центр выберем с менеджером')}</p><p>${mode === 'install' ? 'Стекло с установкой' : 'Только стекло'}</p>${ordered ? '<div class="cr-estimate">'+estimate(ordered)+'</div><p class="cr-small">Калибровка, молдинги и другие работы согласуются после проверки.</p>' : '<p class="cr-small">Стоимость рассчитают после подбора стекла.</p>'}`;
  }
  function openOrder(p=null) {
    ordered=p;
    $('#cr-order-title').textContent=p ? actionLabel(p) : 'Подбор по VIN или фото';
    const selectedBrand=$('#cr-brand')?.value || (kind==='product'?'Audi':''), selectedModel=$('#cr-model')?.value || (kind==='product'?'Q8':'');
    assistance={glass:({windshield:'Лобовое',rear:'Заднее',side:'Боковое'}[$('#cr-glass')?.value || state.glass]),year:$('#cr-year')?.value || state.year,details:[]};
    if(filterForm) {
      for(const [key,label] of Object.entries(labels))if(state[key]!=='any')assistance.details.push(`${label}: ${{yes:'есть',no:'нет',unknown:'не знаю'}[state[key]]}`);
      if(state.glass==='side') {
        if(state.side!=='any')assistance.details.push(state.side==='right'?'правая сторона':'левая сторона');
        if(state.door!=='any')assistance.details.push(state.door==='front'?'передняя дверь':'задняя дверь');
        if(state.movement!=='any')assistance.details.push(state.movement==='moving'?'опускное':'неподвижное');
      }
    }
    orderForm.elements.car.value=p ? `Audi Q8, ${state.year || '2018–'}, лобовое стекло` : [selectedBrand,selectedModel,assistance.year,assistance.glass.toLowerCase()+' стекло'].filter(Boolean).join(' ');
    orderForm.elements.center.value=center;
    $('#cr-form-status').textContent=''; orderSummary(); openDialog(orderDialog);
    emit(p?'order_open':'vin_help_open',p);
  }
  orderForm.addEventListener('input',event => {
    event.target.setCustomValidity?.(''); event.target.removeAttribute('aria-invalid');
    $('#cr-form-status').textContent='';
    if(event.target.name==='car'&&!ordered)orderSummary();
  });
  orderForm.elements.center.addEventListener('change',event => { center=event.target.value;updateCenter();persist();orderSummary(); });
  orderForm.elements.photos.addEventListener('change',event => {
    objectUrls.forEach(URL.revokeObjectURL);objectUrls=[];$('#cr-photo-preview').replaceChildren();
    const files=[...event.target.files];
    if(files.length>3||files.some(f=>f.size>10*1024*1024||!['image/jpeg','image/png','image/webp'].includes(f.type))) {
      event.target.value='';$('#cr-form-status').textContent='Выберите до 3 фото JPG, PNG или WebP, каждое до 10 МБ.';return;
    }
    files.forEach(file => { const url=URL.createObjectURL(file);objectUrls.push(url);const img=document.createElement('img');img.src=url;img.alt=file.name;$('#cr-photo-preview').append(img); });
  });
  orderForm.addEventListener('submit',event => {
    event.preventDefault();event.stopImmediatePropagation();
    const phone=orderForm.elements.phone,vin=orderForm.elements.vin;
    phone.setCustomValidity('');vin.setCustomValidity('');
    if(!/^[78]\d{10}$/.test(phone.value.replace(/\D/g,''))) {phone.setCustomValidity('Введите полный номер: 11 цифр, начиная с 7 или 8.');phone.setAttribute('aria-invalid','true');}
    if(vin.value && !/^[A-HJ-NPR-Z0-9]{17}$/i.test(vin.value)) {vin.setCustomValidity('Проверьте VIN: 17 латинских букв и цифр, без I, O, Q.');vin.setAttribute('aria-invalid','true');}
    if(!orderForm.reportValidity())return;
    const submit=$('#cr-form-submit');if(submit.disabled)return;submit.disabled=true;
    $('#cr-form-status').textContent='Форма заполнена. Данные не отправлены: это офлайн-копия. Для реального подбора или заказа позвоните 8 (800) 707-37-72. Введённые поля сохранены в открытой форме.';
    $('#cr-form-status').focus();emit('offline_form_checked',ordered);
    setTimeout(()=>{submit.disabled=false;},400);
  });
  root.addEventListener('click',event => {
    const el=event.target.closest('button,a'); if(!el)return;
    if(el.matches('[data-mode]')) {mode=el.dataset.mode;refresh();emit('purchase_mode_change');}
    else if(el.matches('[data-help]'))openOrder();
    else if(el.matches('[data-order]'))openOrder(get(el.dataset.order));
    else if(el.matches('[data-close]'))el.closest('dialog').close();
    else if(el.matches('[data-center]')) {center=el.dataset.center;updateCenter();persist();toast('Выбран центр: '+centers[center]+'.');emit('center_select');}
    else if(el.matches('[data-reset]')) {Object.assign(state,defaults);renderProducts();persist();}
    else if(el.matches('[data-remove-filter]')) {state[el.dataset.removeFilter]=defaults[el.dataset.removeFilter];state.limit=6;renderProducts();persist();}
    else if(el.matches('[data-compare]')) {
      const id=el.dataset.compare;
      if(compared.includes(id))compared=compared.filter(x=>x!==id);
      else if(compared.length===3) {toast('Можно сравнить до 3 стёкол. Уберите одно из выбранных.');return;}
      else {compared.push(id);emit('compare_add',get(id));}
      syncCompare();persist();
    } else if(el.matches('[data-open-compare]')) {compareTable();openDialog(compareDialog);emit('compare_open');}
    else if(el.matches('[data-clear-compare]')) {compared=[];syncCompare();persist();}
    else if(el.matches('[data-remove-compare]')) {compared=compared.filter(x=>x!==el.dataset.removeCompare);syncCompare();persist();if(compared.length<2)compareDialog.close();else compareTable();}
    if(el.matches('a[href]')) {
      const url=new URL(el.href,location.href);
      if(url.protocol===location.protocol && !el.getAttribute('href').startsWith('#') && url.href.startsWith(new URL(base,location.href).href)) {
        save('scroll:'+location.pathname,scrollY);
        for(const [key,value] of Object.entries(state))if(value!==defaults[key])url.searchParams.set(key,String(value));
        if(mode==='glass')url.searchParams.set('mode','glass');if(center)url.searchParams.set('center',center);if(compared.length)url.searchParams.set('compare',compared.join(','));el.href=url.href;
      }
    }
  });
  // Native legacy forms keep their original offline behavior; these forms own theirs.
  refresh();
  window.addEventListener('pagehide',()=>{save('scroll:'+location.pathname,scrollY);objectUrls.forEach(URL.revokeObjectURL);});
  const navigation=performance.getEntriesByType('navigation')[0];
  if(navigation?.type==='back_forward')requestAnimationFrame(()=>scrollTo(0,read('scroll:'+location.pathname)||0));
})();
