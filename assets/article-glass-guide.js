/* Reader activity is stored only in this browser, without server requests. */
(()=>{
 const root=document.querySelector('.glass-guide--meta');if(!root)return;
 const key='autosteklo:windshield-choice';let views=1,rating=0;
 try{const previous=Number(localStorage.getItem(key+':views'));views=(Number.isFinite(previous)&&previous>0?previous:0)+1;localStorage.setItem(key+':views',String(views));rating=Number(localStorage.getItem(key+':rating'))||0;}catch{}
 root.querySelector('[data-article-views]').textContent=String(views);
 const buttons=[...root.querySelectorAll('[data-article-rating]')],status=root.querySelector('[data-article-rating-status]');
 function render(){buttons.forEach(button=>{const value=Number(button.dataset.articleRating);button.classList.toggle('is-selected',value<=rating);button.setAttribute('aria-pressed',String(value===rating));});status.textContent=rating?'Ваша оценка: '+rating+' из 5':'Оцените статью';}
 buttons.forEach(button=>button.addEventListener('click',()=>{rating=Number(button.dataset.articleRating);try{localStorage.setItem(key+':rating',String(rating));}catch{}render();}));render();
})();
