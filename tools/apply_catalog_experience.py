"""Apply conversion improvements to the five saved catalogue pages."""
import json, os, re
from pathlib import Path
from html import escape as h
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
PAGE_METADATA = json.loads((ROOT/'tools/native_page_metadata.json').read_text())
raw = (ROOT/'offline-catalog-data.js').read_text()
source = json.loads(raw[raw.index('=')+1:-1])
PRODUCT = 'product/audi-q8-5d-suv-2018-steklo-vetrovoe-datchik-dozhdia-kamera-hud-vin-3/index.html'
ROUTES = {'catalog/index.html':'catalog', 'catalog/audi/index.html':'brand',
 'catalog/audi/q8/index.html':'model', 'catalog/audi/q8/lobovye-stekla/5d-ranger-2018/index.html':'generation', PRODUCT:'product'}

def directory(route):
    nodes = BeautifulSoup(''.join(source['lists'][route]), 'html.parser')
    return [{'name':a.get_text(' ',strip=True), 'url':a['href'],
             'image':'assets/'+Path(a.img['src']).name if a.img else None} for a in nodes.select('a')]

products=[]
for p in source['products']:
    s=BeautifulSoup(p['html'],'html.parser')
    brand=s.select_one('.product-card-content-brand img')['alt']
    title=s.select_one('.product-card__title').get_text(' ',strip=True)
    codes=[x.get_text(' ',strip=True) for x in s.select('.product-card-content-eurocode')]
    order=s.select_one('[data-id]')
    # A missing positive option does not establish that the option is absent.
    opts={k:(True if p['key'] in source['options'][v] else None) for k,v in
          {'rain':'1','hud':'14','camera':'7','heating':'12','vin':'9','athermal':'8'}.items()}
    products.append({'id':order['data-id'], 'path':p['key'], 'brand':brand, 'title':title,
        'price':int(p['price']) if p['price'] is not None else None, 'stock':p['available'],
        'eurocode':codes[0] if codes else '', 'oem':codes[1] if len(codes)>1 else '',
        'options':opts, 'service':6000,
        'brandImage':'assets/'+Path(s.select_one('.product-card-content-brand img')['src']).name})
data={'date':'19.11.2026','products':products,'brands':directory('catalog/'),
      'models':directory('catalog/audi/'),'productPage':PRODUCT}
brand_listing_template=(ROOT/'tools/audi_native_products.html.txt').read_text()
brand_products=[]
for card in BeautifulSoup(brand_listing_template,'html.parser').select('.product-card'):
    def amount(selector):
        node=card.select_one(selector)
        value=re.sub(r'\D','',node.get_text()) if node else ''
        return int(value) if value else None
    title=card.select_one('.product-card__title').get_text(' ',strip=True)
    logo=card.select_one('.product-card-content-brand img')
    brand_products.append({'id':card.select_one('[data-brand-order]')['data-brand-order'],
        'title':title,'car':title,'brand':logo.get('alt','') if logo else '',
        'price':amount('.product-card__prices__main'),'service':amount('.product-card__replace'),
        'options':{},'native':True})
data['brandProducts']=brand_products
(ROOT/'assets/catalog-experience-data.js').write_text('window.CRO_DATA='+json.dumps(data,ensure_ascii=False)+';\n')

def button(text,attrs='',secondary=False):
    return f'<button type="button" class="cr-btn{ " cr-outline" if secondary else ""}" {attrs}>{text}</button>'

def help_block():
    return '<aside class="cr-help"><div><div class="base__title">Не знаете, какое стекло выбрать?</div><p>Подберите по VIN или фото маркировки и зоны камеры.</p></div>'+button('Подобрать по VIN / фото','data-help')+'</aside>'

def picker(kind):
    brand='Audi' if kind!='catalog' else ''
    title='Подберите стекло для своего автомобиля'+(' в Ярославле' if kind=='catalog' else '')
    if kind in ['catalog','brand','model','generation']:
        return (ROOT/'tools/catalog_native_picker.html.txt').read_text().replace('{{PICKER_TITLE}}',h(title))
    return f'''<form id="cr-picker" class="cr-picker"><p class="filter-block-typical1__title">{title}</p><div class="cr-picker-fields">
    <label>Марка<select name="carBrand" id="cr-brand"><option value="">Выберите марку</option>{''.join(f'<option {"selected" if x["name"]=="AUDI" and brand else ""} value="{h(x["name"])}">{h(x["name"])}</option>' for x in data['brands'])}</select></label>
    <label>Модель<select name="carModel" id="cr-model"><option value="">Выберите модель</option></select></label>
    <label>Год выпуска<select name="year" id="cr-year"><option value="">Не знаю</option>{''.join(f'<option>{y}</option>' for y in range(2026,2017,-1))}</select></label>
    <label>Стекло<select name="glass" id="cr-glass"><option value="windshield">Лобовое</option><option value="rear">Заднее</option><option value="side">Боковое</option></select></label>
    <button class="cr-btn" type="submit">Показать варианты</button></div><p class="cr-small cr-muted" id="cr-picker-note">Для Audi Q8 сохранён полный список из 33 лобовых стёкол. Другие автомобили доступны на сайте онлайн.</p></form>'''

def directory_block(kind,rel):
    isbrand=kind=='brand';items=data['models'] if isbrand else data['brands']
    links=[]
    for x in items:
        local=x['name']=='Q8' if isbrand else x['name']=='AUDI'
        url=rel+('catalog/audi/q8/index.html' if isbrand else 'catalog/audi/index.html') if local else x['url']
        image=f'<img class="catalog-mark__img" src="{rel+h(x["image"])}" alt="" loading="lazy">' if not isbrand and x['image'] else ''
        if isbrand:
            links.append(f'<a class="cr-tile catalog-model" href="{h(url)}" data-directory-name="{h(x["name"])}"><p class="catalog-mark__title">{h(x["name"])}</p></a>')
        else:
            links.append(f'<a class="cr-tile catalog-mark" href="{h(url)}" data-directory-name="{h(x["name"])}">{image}<span class="catalog-mark__title">{h(x["name"])}</span></a>')
    tiles_class='catalog-items' if isbrand else 'cr-tiles'
    search_label='Поиск моделей Audi' if isbrand else 'Поиск марки автомобиля'
    search=f'''<label class="catalog-search" for="cr-directory-search"><span class="cr-sr">{search_label}</span><input class="catalog-search__input" id="cr-directory-search" type="search" placeholder="Начните вводить название" autocomplete="off"><span class="catalog-search-btn" aria-hidden="true"><svg class="catalog-search-btn__svg" focusable="false"><use href="#offline-sprite-search"></use></svg></span></label>'''
    header=f'<div class="catalog__description" id="cr-directory-title">Выберите марку вашего автомобиля</div>{search}'
    return f'''<section class="cr-section" aria-labelledby="cr-directory-title">{header}<p id="cr-directory-count" class="cr-small" role="status"></p><div class="{tiles_class}" id="cr-directory">{''.join(links)}</div><div id="cr-directory-empty" class="cr-card" hidden><h3>Ничего не нашли</h3><p>Попробуйте другое название или подберите стекло по VIN / фото.</p>{button('Помочь с подбором','data-help')}</div></section>'''

def generation_block(rel):
    search='''<label class="catalog-search" for="cr-directory-search"><span class="cr-sr">Поиск поколения Audi Q8</span><input class="catalog-search__input" id="cr-directory-search" type="search" placeholder="Начните вводить название" autocomplete="off"><span class="catalog-search-btn" aria-hidden="true"><svg class="catalog-search-btn__svg" focusable="false"><use href="#offline-sprite-search"></use></svg></span></label>'''
    native_products=(ROOT/'tools/q8_native_products.html.txt').read_text().replace('{{ROOT}}',rel)
    return f'''<section class="cr-section cr-native-model-products" aria-labelledby="cr-generation-title"><div class="catalog__description" id="cr-generation-title">Выберите модель вашего автомобиля</div>{search}<div class="catalog-items" id="cr-generations"><a class="catalog-model generation" data-directory-name="5D RANGER (2018 - )" href="{rel}catalog/audi/q8/lobovye-stekla/5d-ranger-2018/index.html"><p class="catalog-mark__title">5D RANGER (2018 - )</p></a>{native_products}</div><div id="cr-directory-empty" class="cr-card" role="status" hidden><h3>Ничего не нашли</h3><p>Попробуйте другое название или подберите стекло по VIN / фото.</p>{button('Помочь с подбором','data-help')}</div></section>'''

def filters():
    return (ROOT/'tools/generation_native_filters.html.txt').read_text()

def listing():
    sort=(ROOT/'tools/generation_native_sort.html.txt').read_text()
    return f'''<section class="catalog-wrapper cr-native-generation" aria-label="Стёкла Audi Q8">{filters()}<div class="catalog-content">{sort}<div class="cr-native-list-controls"><a class="catalog-filters__btn a-btn a-btn-outline --mobile" href="#" id="catalogFiltersOpen" role="button" aria-controls="catalogFiltersBlock" aria-expanded="false">Фильтр</a><label class="cr-native-sort-select">Сортировка<select id="cr-sort"><option value="recommended">Сначала с ценой</option><option value="price">Цена по возрастанию</option><option value="price-desc">Цена по убыванию</option><option value="stock">По наличию</option><option value="brand">Производитель</option></select></label></div><div class="cr-mode" role="group" aria-label="Способ покупки">{button('Стекло с установкой','data-mode="install" aria-pressed="true"')}{button('Только стекло','data-mode="glass" aria-pressed="false"',True)}</div><div id="cr-filter-chips" class="cr-chips"></div><div id="cr-products" class="catalog-items"></div><div class="catalog-pagination"><button class="show-more a-btn a-btn-outline" id="cr-more" type="button">Показать еще</button></div><noscript><p>Для фильтрации включите JavaScript. <a href="../../../../../product/audi-q8-5d-suv-2018-steklo-vetrovoe-datchik-dozhdia-kamera-hud-vin-3/index.html">Стекло AGC</a>.</p></noscript></div></section>'''

def product(rel):
    return f'''<section class="cr-buy" aria-label="Стоимость и способ покупки"><div class="cr-mode" role="group" aria-label="Способ покупки">{button('Стекло с установкой','data-mode="install" aria-pressed="true"')}{button('Только стекло','data-mode="glass" aria-pressed="false"',True)}</div><div id="cr-product-estimate" class="cr-estimate"><dl><div><dt>Стекло</dt><dd>44 650 ₽</dd></div><div><dt>Замена</dt><dd>6 000 ₽</dd></div><div class="cr-total"><dt>Подытог</dt><dd>50 650 ₽</dd></div></dl></div><p class="cr-small">Калибровку, молдинги и дополнительные работы согласуем после проверки автомобиля.</p><div class="cr-actions">{button('Заявка на установку','data-order="92644"')}{button('Подобрать по VIN / фото','data-help',True)}</div></section>'''

def services():
    return f'''<section class="cr-section" id="cr-centers"><div class="cr-row cr-between"><h2>Где установить стекло</h2><span class="cr-badge">Ярославль</span></div><p>Выберите удобный центр. Сначала проверим комплектацию и наличие, затем согласуем стоимость и время.</p><div class="cr-centers"><article class="cr-card"><h3>Городской Вал, 2</h3><p>Ежедневно, 9:00–18:00</p><a href="tel:+78007073772">8 (800) 707-37-72</a><div class="cr-row cr-between">{button('Выбрать центр','data-center="val"',True)}<a href="https://yandex.ru/maps/?text=Ярославль%20Городской%20Вал%202" target="_blank" rel="noopener">Маршрут онлайн</a></div></article><article class="cr-card"><h3>Улица Громова, 1Ж</h3><p>Пн–сб, 9:00–18:00 · вс — выходной</p><a href="tel:+78007073772">8 (800) 707-37-72</a><div class="cr-row cr-between">{button('Выбрать центр','data-center="gromova"',True)}<a href="https://yandex.ru/maps/?text=Ярославль%20Громова%201Ж" target="_blank" rel="noopener">Маршрут онлайн</a></div></article></div><p id="cr-center-status" class="cr-small" role="status">Наличие на складе поставщика не означает наличие в центре.</p></section>{(ROOT/'tools/catalog_native_benefits.html.txt').read_text()}<section class="cr-section cr-process"><div><div class="base__title">Как проходит замена</div><ol><li>Проверяем VIN, опции стекла и комплектацию автомобиля.</li><li>Подтверждаем наличие, работы и смету до заказа.</li><li>Согласуем центр и время, устанавливаем стекло.</li><li>Проверяем результат, выдаём документы и рекомендации.</li></ol></div><img src="PLACEHOLDER_PROCESS" alt="Процесс установки автостекла в сервисном центре" width="1280" height="853" loading="lazy"></section><section class="cr-section cr-faq"><div class="base__title">Частые вопросы</div><details><summary>Что входит в указанную стоимость?</summary><p>Подытог складывается из цены стекла и услуги замены, если она выбрана. Калибровка камеры, молдинги, крепления и другие необходимые работы согласуются отдельно после проверки. Автоматически платные дополнения не выбираются.</p></details><details><summary>Как узнать, нужны ли HUD, камера и обогрев?</summary><p>Посмотрите комплектацию автомобиля или приложите фото зоны камеры и маркировки стекла. VIN помогает проверить применимость; при выборе «Не знаю» варианты не исключаются.</p>{button('Проверить по VIN / фото','data-help',True)}</details><details><summary>Можно купить стекло без установки?</summary><p>Да, выберите «Только стекло». Подытог и состав заявки изменятся. Возможность выдачи, упаковку и срок нужно подтвердить для выбранного товара.</p></details><details><summary>Как оплатить и получить стекло?</summary><p>Способ оплаты, самовывоз или доставку и её стоимость согласуют с центром до заказа.</p></details><details><summary>Можно записаться на точное время?</summary><p>Время подтверждает менеджер после проверки комплектации и наличия.</p></details></section>'''

def dialogs():
    return (ROOT/'tools/catalog_dialogs.html.txt').read_text()

for path,kind in ROUTES.items():
    f=ROOT/path;soup=BeautifulSoup(f.read_text(),'html.parser')
    rel=os.path.relpath(ROOT,f.parent).replace('\\','/')+'/'
    for tag in soup.select('script[src]'):
        if 'offline-catalog' in tag['src'] or re.search(r'/(catalog(?:_\d)?|product)-bundle-',tag['src']):tag.decompose()
    for tag in soup.select('[data-cro-resource]'):tag.decompose()
    asset_version='?v=native-form-style-20261120'
    css=soup.new_tag('link',rel='stylesheet',href=rel+'assets/catalog-experience.css'+asset_version,attrs={'data-cro-resource':'true'});soup.head.append(css)
    if kind=='generation':
        css=soup.new_tag('link',rel='stylesheet',href=rel+'assets/catalog-generation.css'+asset_version,attrs={'data-cro-resource':'true'});soup.head.append(css)
    if kind=='product':
        css=soup.new_tag('link',rel='stylesheet',href=rel+'assets/product-native.css'+asset_version,attrs={'data-cro-resource':'true'});soup.head.append(css)
    if kind!='product':
        css=soup.new_tag('link',rel='stylesheet',href=rel+'assets/catalog-benefits.css'+asset_version,attrs={'data-cro-resource':'true'});soup.head.append(css)
    css=soup.new_tag('link',rel='stylesheet',href=rel+'assets/catalog-forms.css'+asset_version,attrs={'data-cro-resource':'true'});soup.head.append(css)
    script_paths=['assets/catalog-experience-data.js','assets/catalog-experience.js']
    if kind=='generation':script_paths[1:1]=['offline-catalog-data.js','assets/catalog-generation.js']
    if kind=='product':script_paths=['assets/product-bundle-db4a78c8a435.js']+script_paths+['assets/product-native.js']
    for path_to_script in script_paths:
        t=soup.new_tag('script',src=rel+path_to_script+asset_version,attrs={'defer':'','data-cro-resource':'true'});soup.head.append(t)
    if kind in ['model','generation']:
        for tag in soup.select('script[src]'):
            if tag['src'].split('?')[0].endswith('/offline-ui.js'):
                tag['src']=rel+'offline-ui.js?v='+('generation-native-blocks-20261120' if kind=='generation' else 'q8-native-content-20261120')
    title={'catalog':'Каталог автостёкол','brand':'Автостёкла для Audi','model':'Лобовые стёкла Audi Q8','generation':'Лобовые стёкла Audi Q8 · 2018–','product':'Стекло Audi Q8 · AGC'}[kind]
    trail=[('Главная','index.html'),('Каталог автостекол','catalog/index.html')]
    if kind!='catalog':trail.append(('Audi','catalog/audi/index.html'))
    if kind in ['model','generation','product']:trail.append(('Audi Q8','catalog/audi/q8/index.html'))
    if kind=='generation':trail.append(('5D RANGER (2018 - )',path))
    if kind=='product':trail.append(('AGC · 92644',path))
    crumbs=''
    for index,(label,target) in enumerate(trail):
        last=index==len(trail)-1
        item=f'<span class="breadcrumbs-item__text breadcrumbs-item__current" itemprop="name" aria-current="page">{h(label)}</span>' if last else f'<meta itemprop="name" content="{h(label)}"><a itemprop="item" class="breadcrumbs-item__text breadcrumbs-item__link" href="{rel+target}">{h(label)}</a>'
        crumbs+=f'<div class="breadcrumbs-item" itemprop="itemListElement" itemscope itemtype="https://schema.org/ListItem">{item}<meta itemprop="position" content="{index+1}"></div>'
    title_class='product__title base__title' if kind=='product' else 'catalog__title' if kind=='generation' else 'catalog__title base__title'
    heading_title={'catalog':'Каталог автостекол','brand':'Каталог автостекол Audi в Ярославле','model':'Каталог автостекол Audi Q8 в Ярославле','generation':'Лобовые стекла Audi Q8 5D RANGER (2018 - ) в Ярославле'}.get(kind,title)
    heading_subtitle='<p>Ярославль · подбор, покупка и установка автостёкол</p>' if kind=='product' else ''
    content=f'<main id="main" class="cr-root" data-kind="{kind}" data-root="{rel}"><div class="cr-wrap base-container"><a class="cr-skip" href="#cr-content">Перейти к подбору</a><nav class="breadcrumbs cr-breadcrumbs" itemscope itemtype="https://schema.org/BreadcrumbList" aria-label="Хлебные крошки">{crumbs}</nav><div id="cr-content" class="cr-heading"><h1 class="{title_class}">{heading_title}</h1>{heading_subtitle}</div>'
    if kind=='generation':
        content=content.replace(f'<div id="cr-content" class="cr-heading"><h1 class="{title_class}">{heading_title}</h1></div>',f'<div id="cr-content" class="cr-heading catalog-header"><div class="catalog-header-left"><h1 class="catalog__title">{heading_title}</h1><p class="catalog-header__count" id="cr-count" role="status">Найдено 33 товаров</p></div><div class="catalog-header-image --desktop"><img class="catalog-header-image__img" src="{rel}assets/4audi-442769e75a57.png" alt="Audi" style="object-fit:contain;height:100%"></div></div>')
    if kind=='product':content+=product(rel)
    else:
        if kind in ['catalog','brand']:
            content+=picker(kind)+help_block()+directory_block(kind,rel)
            if kind=='brand':content+=brand_listing_template.replace('{{ROOT}}',rel)
        elif kind=='model':
            content+=help_block()+generation_block(rel)
            content+='<div class="filter-block-typical2 base-wrapper" style="margin-top:50px">'+picker(kind)+'</div>'
        else:
            content+=help_block()+listing()
    content+=services().replace('PLACEHOLDER_PROCESS',rel+'assets/typical2banner-665ad213bc04.png')
    if kind=='product':content+=help_block()
    content+=f'</div>{dialogs()}</main>'
    fragment=BeautifulSoup(content,'html.parser')
    if kind in ['model','generation']:fragment.select_one('#cr-centers').decompose()
    if kind in ['catalog','brand']:
        # Catalogue directories reuse the original form, addresses and content.
        selectors=['#cr-directory-count','#cr-centers','#cr-picker-note']
        for selector in selectors:
            element=fragment.select_one(selector)
            if element:element.decompose()
        fragment.select_one('#cr-directory-empty')['role']='status'
    picker_form=fragment.select_one('#cr-picker')
    if picker_form:
        picker_form['class']+=['filter-block-typical1-wrapper','typ2']
    for heading in fragment.select('h2'):
        if heading.find_parent('dialog'):heading['class']=['modal-typical__header']
        elif heading.find_parent('form',id='cr-picker') is None:heading['class']=['base__title']
    for control in fragment.select('button.cr-btn'):
        variant='a-btn-black' if control.find_parent('form',id='cr-picker') else 'a-btn-outline' if 'cr-outline' in control['class'] else 'a-btn-red2'
        control['class']+=['a-btn',variant]
    for control in fragment.select('#cr-order-form input:not([type="file"]):not([type="checkbox"]),#cr-help-form input:not([type="file"]):not([type="checkbox"])'):
        control['class']=['form-group__input']
    if kind=='product':
        native=BeautifulSoup((ROOT/'tools/product_native_page.html.txt').read_text().replace('{{ROOT}}',rel),'html.parser')
        price_root=soup.new_tag('div',attrs={'class':['cr-root','cr-native-price'],'data-kind':'product','data-root':rel})
        price_root.append(fragment.select_one('.cr-buy'))
        for element in fragment.select('dialog,#cr-bottom,#cr-toast'):price_root.append(element)
        native.select_one('.product-content-info-prices').append(price_root)
        soup.select_one('#main').replace_with(native.select_one('#main'))
    elif kind in ['catalog','brand','model','generation']:
        outer=soup.new_tag('main',id='main',attrs={'class':'main catalog-main'})
        enhanced=fragment.select_one('main')
        enhanced.name='div';enhanced.attrs.pop('id',None)
        outer.append(enhanced)
        native=BeautifulSoup((ROOT/'tools/catalog_native_blocks.html.txt').read_text(),'html.parser')
        if kind in ['brand','model','generation']:
            for element in native.select('[src],[data-src],[href]'):
                for attr in ['src','data-src','href']:
                    value=element.get(attr,'')
                    if value.startswith('../'):element[attr]=rel+value[3:]
            if kind=='generation':
                generation_content=BeautifulSoup((ROOT/'tools/generation_native_content.html.txt').read_text().replace('{{ROOT}}',rel),'html.parser')
                native.select_one('.seo').replace_with(generation_content.select_one('.seo'))
                links=BeautifulSoup((ROOT/'tools/generation_native_links.html.txt').read_text(),'html.parser')
                native.select_one('#catalog-original-blocks').append(links)
            else:
                brand_content=BeautifulSoup((ROOT/'tools'/('q8_native_content.html.txt' if kind=='model' else 'audi_native_content.html.txt')).read_text(),'html.parser')
                native.select_one('.seo').replace_with(brand_content.select_one('.seo'))
        outer.append(native)
        soup.select_one('#main').replace_with(outer)
    else:
        soup.select_one('#main').replace_with(fragment)
    soup.body['class']=list(set(soup.body.get('class',[])+['cro-page']))
    # Keep the original chrome, while correcting unusable tel formatting.
    for a in soup.select('a[href]'):
        if a['href'].startswith('tel:') and '707' in a['href']:a['href']='tel:+78007073772'
    # Preserve the source site's metadata when regenerating the saved pages.
    metadata=PAGE_METADATA[path]
    soup.title.string=metadata['title']
    description=soup.find('meta',attrs={'name':'description'})
    if description is None:
        description=soup.new_tag('meta',attrs={'name':'description'})
        soup.head.append(description)
    description['content']=metadata['description']
    f.write_text(str(soup))

print('Updated',len(ROUTES),'pages;',len(products),'products;',len(data['brands']),'brands')

# The compatibility layer must let the new local forms handle their own submit.
runtime=ROOT/'offline-runtime.js'
text=runtime.read_text()
old="document.addEventListener('submit', e => { e.preventDefault();"
new="document.addEventListener('submit', e => { if(e.target.closest('.cr-root'))return; e.preventDefault();"
text=text.replace(old,new)
text=text.replace("const target = window.OFFLINE_ROOT + 'blog/index.html';\n    location.href = target + '?offline-search=' + encodeURIComponent(query);", "const catalogue = Boolean(document.querySelector('.cr-root'));\n    const target = window.OFFLINE_ROOT + (catalogue ? 'catalog/index.html' : 'blog/index.html');\n    location.href = target + (catalogue ? '?q=' : '?offline-search=') + encodeURIComponent(query);")
runtime.write_text(text)
