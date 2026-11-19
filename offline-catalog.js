/* Catalogue snapshots: original markup, local search/filter state, no order delivery. */
(() => {
  const data = window.OFFLINE_CATALOG_DATA;
  const previousFetch = window.fetch.bind(window);
  // The native brand/model search and infinite scroll keep their original handlers.
  window.fetch = (input, options={}) => {
    const raw = typeof input === 'string' ? input : input.url;
    const url = new URL(raw, location.href);
    const route = document.body?.dataset.offlineCatalogRoute;
    if (data.lists[route] && url.searchParams.get('ajax') === 'on' && (!options.method || options.method === 'GET')) {
      const holder = document.createElement('div');
      holder.innerHTML = data.lists[route].join('');
      const query = (url.searchParams.get('q') || '').trim().toLocaleLowerCase('ru');
      const items = [...holder.children].filter(el => el.textContent.toLocaleLowerCase('ru').includes(query));
      const page = Math.max(1, Number(url.searchParams.get('page')) || 1);
      const perPage = 25;
      const result = {items:items.slice((page-1)*perPage,page*perPage).map(el=>el.outerHTML).join(''),page,next:page*perPage<items.length};
      return Promise.resolve(new Response(JSON.stringify(result),{headers:{'Content-Type':'application/json'}}));
    }
    return previousFetch(input,options);
  };
  document.addEventListener('DOMContentLoaded', () => {
    const items = document.querySelector('#catalogItems');
    if (!items) return;
    window.offlineInitDepartments?.();
    const root = window.OFFLINE_ROOT;
    const listRoute='catalog/audi/q8/lobovye-stekla/5d-ranger-2018/';
    const state={page:1,sort:'count_showing',options:new Set()};
    const paginationStyle=document.querySelector('#catalogPagination style')?.outerHTML||'';
    const initial = new URLSearchParams(location.search);
    state.sort=initial.get('sort')||state.sort;
    state.page=Math.max(1,Number(initial.get('page'))||1);
    (initial.get('options')||'').split(',').filter(x=>data.options[x]).forEach(x=>state.options.add(x));
    function setUrl() {
      const query=new URLSearchParams();
      if(state.page>1)query.set('page',state.page);
      if(state.sort!=='count_showing')query.set('sort',state.sort);
      if(state.options.size)query.set('options',[...state.options].join(','));
      try {history.replaceState(null,'',location.pathname+(query.size?'?'+query:''));}catch{}
    }
    function matching() {
      let records=data.products.filter(p=>[...state.options].every(option=>data.options[option].includes(p.key)));
      if(state.sort==='price'||state.sort==='-price')records.sort((a,b)=>a.price===null?1:b.price===null?-1:(a.price-b.price)*(state.sort==='price'?1:-1));
      if(state.sort==='-count')records.sort((a,b)=>Number(b.available)-Number(a.available));
      return records;
    }
    function render(append=false) {
      const records=matching(),pages=Math.max(1,Math.ceil(records.length/5));state.page=Math.min(state.page,pages);
      const visible=records.slice(append?0:(state.page-1)*5,state.page*5);
      items.innerHTML=visible.map(p=>p.html).join('');
      document.querySelector('#catalogCount').textContent='Найдено '+records.length+' товаров';
      const pagination=document.querySelector('#catalogPagination');
      pagination.innerHTML=paginationStyle+(state.page<pages?'<div class="show-more a-btn a-btn-outline" id="showMore">Показать еще</div>':'')+'<nav><div class="pagination">'+Array.from({length:pages},(_,i)=>'<div class="catalog-pagination-item '+(i+1===state.page?'active':'')+'" data-page="'+(i+1)+'">'+(i+1)+'</div>').join('')+'</div></nav>';
      document.querySelectorAll('.catalog-sort-item').forEach(el=>el.classList.toggle('active',el.dataset.value===state.sort));
      document.querySelectorAll('.catalog-filters-option__option').forEach(el=>el.classList.toggle('active',state.options.has(el.dataset.value)));
      document.querySelector('#optionInput').value=[...state.options].join(',');
      setUrl();
    }
    document.addEventListener('click',event=>{
      const control=event.target.closest('.catalog-filters-option__option,.catalog-sort-item,#catalogApply,#catalogClear,#showMore,.catalog-pagination-item,#catalogFiltersOpen,#catalogFiltersClose,.catalog-filters-glass,.catalog-filters-generation');
      if(!control)return;
      event.preventDefault();event.stopImmediatePropagation();
      if(control.matches('.catalog-filters-option__option')) {
        state.options.has(control.dataset.value)?state.options.delete(control.dataset.value):state.options.add(control.dataset.value);state.page=1;render();
      } else if(control.matches('.catalog-sort-item')) {state.sort=control.dataset.value;state.page=1;render();}
      else if(control.id==='showMore') {state.page++;render(true);}
      else if(control.matches('.catalog-pagination-item')) {state.page=Number(control.dataset.page);render();document.querySelector('.catalog-header').scrollIntoView();}
      else if(control.id==='catalogClear') {state.options.clear();state.page=1;state.sort='count_showing';render();}
      else if(control.id==='catalogFiltersOpen') {document.querySelector('#catalogFiltersBlock').classList.add('active');document.body.style.overflow='hidden';}
      else if(control.id==='catalogFiltersClose'||control.id==='catalogApply') {document.querySelector('#catalogFiltersBlock').classList.remove('active');document.body.style.overflow='';render();}
      else if(control.matches('.catalog-filters-glass')&&control.dataset.value!=='lobovye-stekla') {
        location.href='https://autosteklo.pro/catalog/audi/q8/'+control.dataset.value+'/5d-ranger-2018/';
      }
    },true);
    let small=false;
    function responsiveSort(){const now=matchMedia('(max-width: 1170px)').matches;if(now&&!small){state.sort='price';state.page=1;render();}small=now;}
    if(initial.size)render();
    responsiveSort();window.addEventListener('resize',responsiveSort);
    // Give the original dropdown/accordion initializer its normal data-toggle markup.
    document.querySelector('#glassInput').value='lobovye-stekla';
  });
})();
