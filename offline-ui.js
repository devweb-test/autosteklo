/* Preserve original UI initializers; add only local behavior and widget fallbacks. */
(() => {
  try {if(localStorage.getItem('offline-cookie-accepted'))document.querySelector('#cookie')?.classList.add('hidden');}catch{}
  document.querySelector('#cookieBtn')?.addEventListener('click',()=>{try{localStorage.setItem('offline-cookie-accepted','1');}catch{}document.querySelector('#cookie')?.classList.add('hidden');});
  const query = new URLSearchParams(location.search).get('offline-search');
  if (query && document.querySelector('#itemsBlock')) {
    const cards = [...document.querySelectorAll('#itemsBlock > a')];
    cards.forEach(card => card.hidden = !card.textContent.toLocaleLowerCase('ru').includes(query.toLocaleLowerCase('ru')));
    const text = document.createElement('p'); text.className = 'offline-form-notice';
    text.textContent = 'Поиск по сохранённой странице блога: «' + query + '». Найдено: ' + cards.filter(e => !e.hidden).length;
    document.querySelector('#itemsBlock').before(text);
  }
  document.addEventListener('click', e => {
    const pager = e.target.closest('.pagination-item:not(.active), .blog-content-types-item');
    if (!pager) return;
    e.preventDefault(); e.stopImmediatePropagation();
    let box = document.querySelector('#offline-blog-notice');
    if (!box) {box = document.createElement('p'); box.id = 'offline-blog-notice'; box.className = 'offline-form-notice'; box.setAttribute('role','status'); document.querySelector('#itemsBlock')?.before(box);}
    box.textContent = 'В копии сохранена первая страница блога. Другие страницы и категории доступны на оригинальном сайте: ';
    const link = document.createElement('a'); const page = pager.dataset.page || '1';
    link.href = 'https://autosteklo.pro/blog/?page=' + encodeURIComponent(page) + (pager.dataset.value ? '&category=' + encodeURIComponent(pager.dataset.value) : '');
    link.textContent = 'Открыть блог онлайн'; box.append(link); box.scrollIntoView({block:'center',behavior:'smooth'});
  }, true);
  // The original close control is only shown on mobile; Escape works on desktop too.
  document.querySelectorAll('.modal-near-close').forEach(button => button.addEventListener('click', () => window.modalsStream?.close()));
  let providerPromise;
  function provider() {
    if (window.ymaps) return new Promise(resolve => window.ymaps.ready(resolve));
    if (!providerPromise) providerPromise = new Promise((resolve,reject) => {
      const script = document.createElement('script'); script.src='https://api-maps.yandex.ru/2.1/?lang=ru_RU';
      script.onload=()=>window.ymaps.ready(resolve);script.onerror=()=>{providerPromise=null;reject(new Error('Map unavailable'));};
      document.head.append(script);
      setTimeout(()=>{if(!window.ymaps){providerPromise=null;reject(new Error('Map timeout'));}},18000);
    });
    return providerPromise;
  }
  function connectedMap(host, source) {
    if (!host || host.dataset.offlineMapReady) return;
    host.dataset.offlineMapReady='true';host.classList.add('offline-map-host');
    const canvas=document.createElement('div');canvas.className='offline-map-canvas';host.append(canvas);
    const fallback=document.createElement('div');fallback.className='offline-map-fallback';
    fallback.innerHTML='<strong>Карта центров «Автостекла»</strong><span>Для интерактивной карты нужен интернет.</span><a href="https://yandex.ru/maps/?ll=39.846072%2C57.662846&z=11&text=Автостекла%20Ярославль" target="_blank" rel="noopener">Открыть Яндекс Карты</a><button type="button">Повторить загрузку</button>';
    host.append(fallback);
    let loading=false,map,check,timer;
    const startedAt=performance.now();
    function tilesReady(){
      if(!map)return false;
      const container=map.layers.get(0)?.get(0)?._tileContainer;let count=0,ready=true;
      container?.tiles?.each(tile=>{count++;if(!tile.isReady()||tile._error)ready=false;});
      return count>0&&ready;
    }
    async function start() {
      if (map) {map.container.fitToViewport();return;}
      if (loading || !host.offsetWidth || !host.offsetHeight) return;
      loading=true;
      try {
        if (source) {
          if (canvas.querySelector('script')) return;
          const script=document.createElement('script');script.src=source;script.async=true;canvas.append(script);
        } else {
          await provider();
          if(map)return;
          const data=window.OFFLINE_SHOPS;
          map=new ymaps.Map(canvas,{center:[Number(data.start_lat),Number(data.start_lon)],zoom:11});
          const manager=new ymaps.ObjectManager();const markers=JSON.parse(JSON.stringify(data.markers));
          markers.features.forEach(marker=>{marker.geometry.coordinates=marker.geometry.coordinates.map(Number);marker.options.iconImageHref=window.OFFLINE_ROOT+window.OFFLINE_MARKER;});
          manager.add(markers);map.geoObjects.add(manager);
          host.offlineMap=map;host.offlineManager=manager;
          manager.objects.events.add('mouseenter',event=>manager.objects.setObjectOptions(event.get('objectId'),{iconImageHref:window.OFFLINE_ROOT+window.OFFLINE_MARKER_ACTIVE}));
          manager.objects.events.add('mouseleave',event=>manager.objects.setObjectOptions(event.get('objectId'),{iconImageHref:window.OFFLINE_ROOT+window.OFFLINE_MARKER}));
          map.container.fitToViewport();
          map.layers.get(0)?.get(0)?._tileContainer?.events.add('ready',()=>{if(tilesReady())fallback.hidden=true;});
        }
        check=setInterval(()=>{
          const tiles=[...canvas.querySelectorAll('img')].filter(img=>img.complete && img.naturalWidth>0 && /tiles|maps|yandex/.test(img.src));
          const renderedCanvas=[...canvas.querySelectorAll('canvas')].some(c=>c.width>0 && c.height>0);
          const constructorTiles=source&&renderedCanvas&&performance.getEntriesByType('resource').some(r=>r.startTime>startedAt&&/tiles[./]/.test(r.name)&&r.responseEnd>0);
          if(tiles.length || tilesReady() || constructorTiles){fallback.hidden=true;clearInterval(check);}
        },500);
        timer=setTimeout(()=>clearInterval(check),20000);
      } catch {fallback.hidden=false;}
      finally {loading=false;}
    }
    function retry() {
      clearInterval(check);clearTimeout(timer);
      if(map){map.destroy();map=null;host.offlineMap=null;host.offlineManager=null;}canvas.replaceChildren();fallback.hidden=false;start();
    }
    fallback.querySelector('button').addEventListener('click',retry);
    window.addEventListener('online',()=>{if(host.offsetWidth)retry();});
    new ResizeObserver(()=>{if(host.offsetWidth && host.offsetHeight)start();}).observe(host);
    host.offlineStart=start;
    start();
  }
  window.offlineInitDepartments=()=>{
    connectedMap(document.querySelector('#departmentsMap'));
    document.querySelectorAll('.--departments-shop').forEach(shop=>{
      shop.addEventListener('click',e=>{
        if(e.target.closest('a,button,.offline-map-host'))return;
        const collapsed=shop.classList.contains('collapsed');
        document.querySelectorAll('.--departments-shop').forEach(el=>el.classList.add('collapsed'));
        shop.classList.toggle('collapsed',!collapsed);
        const host=document.querySelector('#departmentsMap');const manager=host?.offlineManager;const id=Number(shop.dataset.shop);
        if(manager){const marker=manager.objects.getById(id);if(marker)host.offlineMap.panTo(marker.geometry.coordinates.map(Number),{flying:true,duration:300,zoom:14});}
      });
    });
    document.querySelectorAll('.offline-constructor-map').forEach(host=>connectedMap(host,host.dataset.mapSrc));
  };
  // Keep the modal's original responsive map box.
  connectedMap(document.querySelector('#nearMap'));
  document.querySelector('#nearSearch')?.addEventListener('input', e => {
    const value=e.target.value.toLocaleLowerCase('ru');
    document.querySelectorAll('.modal-near-content-select-list-item-subitems__city').forEach(el=>el.classList.toggle('hidden',!el.textContent.toLocaleLowerCase('ru').includes(value)));
  });
})();
