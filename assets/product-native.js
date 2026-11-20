/* Local order bridge and review pagination for the original product layout. */
(() => {
  'use strict';
  const page=document.querySelector('.cr-native-product'),root=page?.querySelector('.cr-native-price');
  if (!root) return;
  const controls=page.querySelectorAll('.--product-order,.--product-price');
  controls.forEach(el=>{el.setAttribute('role','button');el.tabIndex=0;});
  document.addEventListener('click',event=>{
    const button=event.target.closest('.cr-native-product .--product-order,.cr-native-product .--product-price,.cr-native-product .reviews-product__show-more');
    if (!button) return;
    event.preventDefault();event.stopImmediatePropagation();
    if (button.matches('.reviews-product__show-more')) {
      let notice=page.querySelector('#product-reviews-offline-notice');
      if (!notice) {
        notice=document.createElement('p');notice.id='product-reviews-offline-notice';notice.className='offline-form-notice';notice.setAttribute('role','status');notice.tabIndex=-1;
        notice.append('В копии сохранены пять отзывов. Другие отзывы доступны на сайте: ');
        const link=document.createElement('a');link.href='https://autosteklo.pro/product/audi-q8-5d-suv-2018-steklo-vetrovoe-datchik-dozhdia-kamera-hud-vin-3/#reviews-container';link.textContent='Открыть отзывы';link.target='_blank';link.rel='noopener';notice.append(link);button.after(notice);
      }
      notice.focus({preventScroll:true});return;
    }
    button.focus({preventScroll:true});
    root.dispatchEvent(new CustomEvent('catalog:product-order',{detail:{productId:button.dataset.id,mode:'install'}}));
  },true);
  page.addEventListener('keydown',event=>{
    if (['Enter',' '].includes(event.key) && event.target.matches('.--product-order,.--product-price')) {event.preventDefault();event.target.click();}
  });
  page.querySelectorAll('a[href]').forEach(link=>{
    if (link.getAttribute('href').startsWith('#') || !link.href.startsWith(new URL(root.dataset.root,location.href).href)) return;
    link.addEventListener('click',()=>{
      const current=new URL(location.href),next=new URL(link.href);
      for (const key of ['glass','year','hud','camera','rain','heating','athermal','vin','sort','mode','center']) if(current.searchParams.has(key))next.searchParams.set(key,current.searchParams.get(key));
      link.href=next.href;
    });
  });
  window.offlineInitDepartments?.();
})();
