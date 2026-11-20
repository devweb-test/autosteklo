/* Native generation-page markup, connected to the shared offline catalogue state. */
(() => {
  'use strict';
  let panel, api, opener, savedOverflow = '';
  const $ = selector => api.root.querySelector(selector);
  const $$ = selector => [...api.root.querySelectorAll(selector)];
  function closePanel() {
    if (!panel?.classList.contains('active')) return;
    panel.classList.remove('active');panel.removeAttribute('role');panel.removeAttribute('aria-modal');
    document.body.style.overflow = savedOverflow;opener.setAttribute('aria-expanded','false');opener.focus({preventScroll:true});
  }
  function sync(state) {
    if (!api) return;
    $$('[data-native-glass]').forEach(el => {const on=el.dataset.nativeGlass===state.glass;el.classList.toggle('active',on);el.setAttribute('aria-checked',String(on));});
    $$('[data-native-option]').forEach(el => {const on=state[el.dataset.nativeOption]==='yes';el.classList.toggle('active',on);el.setAttribute('aria-checked',String(on));});
    $$('[data-native-sort]').forEach(el => {const on=el.dataset.nativeSort===state.sort;el.classList.toggle('active',on);el.setAttribute('aria-pressed',String(on));});
    $('#optionInput').value=$$('[data-native-option][aria-checked=true]').map(el=>el.dataset.value).join(',');
  }
  function init(context) {
    api=context;panel=$('#catalogFiltersBlock');opener=$('#catalogFiltersOpen');
    opener.addEventListener('click',event=>{
      event.preventDefault();savedOverflow=document.body.style.overflow;
      panel.classList.add('active');panel.setAttribute('role','dialog');panel.setAttribute('aria-modal','true');
      panel.setAttribute('aria-label','Фильтр автостекол');document.body.style.overflow='hidden';opener.setAttribute('aria-expanded','true');$('#catalogFiltersClose').focus();
    });
    panel.addEventListener('click',event=>{
      const el=event.target.closest('[data-native-glass],[data-native-option],#catalogApply,#catalogClear,#catalogFiltersClose,#optionHeader');
      if(!el)return;event.preventDefault();
      if(el.dataset.nativeGlass) {api.state.glass=el.dataset.nativeGlass;api.change();}
      else if(el.dataset.nativeOption) {const key=el.dataset.nativeOption;api.state[key]=api.state[key]==='yes'?'any':'yes';api.change();}
      else if(el.id==='catalogClear')api.reset();
      else if(el.id==='optionHeader') {const open=el.getAttribute('aria-expanded')!=='true';el.setAttribute('aria-expanded',String(open));el.classList.toggle('active',open);$('#optionSelect').classList.toggle('active',open);}
      else {api.change();closePanel();}
    });
    panel.addEventListener('keydown',event=>{
      if(event.key==='Escape') {event.preventDefault();closePanel();return;}
      if(['ArrowDown','ArrowRight','ArrowUp','ArrowLeft'].includes(event.key) && event.target.matches('[data-native-glass]')) {
        event.preventDefault();const items=$$('[data-native-glass]'),index=items.indexOf(event.target),step=['ArrowDown','ArrowRight'].includes(event.key)?1:-1;
        const next=items[(index+step+items.length)%items.length];next.click();next.focus();return;
      }
      if(['Enter',' '].includes(event.key) && event.target.matches('[role=button],[role=checkbox],[role=radio]')) {event.preventDefault();event.target.click();}
      if(event.key==='Tab' && panel.classList.contains('active')) {
        const items=[...panel.querySelectorAll('a[href],button,select,input:not([type=hidden]),summary,[tabindex="0"]')].filter(el=>el.getClientRects().length);
        const index=items.indexOf(document.activeElement);
        if(event.shiftKey && index===0) {event.preventDefault();items.at(-1)?.focus();}
        else if(!event.shiftKey && index===items.length-1) {event.preventDefault();items[0]?.focus();}
      }
    });
    $$('[data-native-sort]').forEach(el=>{
      el.addEventListener('click',event=>{event.preventDefault();api.state.sort=el.dataset.nativeSort;api.change();});
      el.addEventListener('keydown',event=>{if(event.key===' '){event.preventDefault();el.click();}});
    });
    matchMedia('(min-width:1171px)').addEventListener('change',event=>{if(event.matches)closePanel();});
    sync(api.state);
  }
  function card(p,view) {
    const {base,escape,money,link,mode,total,actionLabel,labels,selected,date}=view;
    const original=window.OFFLINE_CATALOG_DATA.products.find(record=>record.key===p.path);
    const holder=document.createElement('div');holder.innerHTML=original.html;
    const node=holder.firstElementChild;node.classList.add('cr-native-card');node.dataset.product=p.id;
    node.querySelectorAll('img').forEach(img=>{
      img.src=base+'assets/'+img.getAttribute('src').split('/').pop();img.removeAttribute('data-src');img.loading='lazy';
    });
    node.querySelectorAll('a[href]').forEach(a=>{a.href=p.id==='92644'?link(window.CRO_DATA.productPage):'https://autosteklo.pro'+p.path;});
    const availability=node.querySelector('.product-card-content-available');
    availability.textContent=p.stock?'В наличии в снимке':'Под заказ в снимке';
    const content=node.querySelector('.product-card-content');
    const tags=Object.entries(labels).filter(([key])=>p.options[key]===true).map(([,name])=>`<span>${escape(name)}</span>`).join('');
    content.insertAdjacentHTML('beforeend',`<div class="cr-tags cr-native-tags">${tags}</div><p class="cr-native-note">Данные на ${escape(date)}. Наличие в центре и срок уточняются.</p><details class="cr-card-details"><summary>Параметры и совместимость</summary><p>${escape(p.title)}</p><p>Неуказанные опции требуют проверки. Точную применимость проверяют по VIN.</p></details>`);
    const order=node.querySelector('.product-card__order');
    const prices=order.querySelector('.product-card__prices').outerHTML;
    const metadata=[...order.querySelectorAll('meta,link')].map(el=>el.outerHTML).join('');
    order.innerHTML=metadata+prices+`<p class="product-card__replace">${mode==='install'?'Услуга по замене: '+money(p.service):'Без установки'}</p><div class="cr-estimate cr-native-estimate"><dl><div class="cr-total"><dt>${mode==='install'?'С установкой':'Только стекло'}</dt><dd>${money(total)}</dd></div></dl></div><button type="button" class="${p.price===null?'product-card__order__callback a-btn a-btn-outline':'product-card__order__main-btn a-btn a-btn-red2'}" data-order="${escape(p.id)}">${escape(actionLabel)}</button><button type="button" class="cr-compare-toggle" data-compare="${escape(p.id)}" aria-pressed="${selected}">${selected?'Убрать из сравнения':'Добавить в сравнение'}</button>`;
    return node.outerHTML;
  }
  window.CRO_GENERATION={init,sync,card};
})();
