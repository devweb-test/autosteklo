"""Apply conversion improvements to the five saved catalogue pages."""
import json, os, re
from pathlib import Path
from html import escape as h
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
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
(ROOT/'assets/catalog-experience-data.js').write_text('window.CRO_DATA='+json.dumps(data,ensure_ascii=False)+';\n')

def button(text,attrs='',secondary=False):
    return f'<button type="button" class="cr-btn{ " cr-outline" if secondary else ""}" {attrs}>{text}</button>'

def help_block():
    return '<aside class="cr-help"><div><h2>Не знаете, какое стекло выбрать?</h2><p>Подберите по VIN или фото маркировки и зоны камеры. Контакты не нужны для просмотра каталога.</p></div>'+button('Подобрать по VIN / фото','data-help')+'</aside>'

def picker(kind):
    brand='Audi' if kind!='catalog' else ''
    title='Подберите стекло для своего автомобиля'+(' в Ярославле' if kind=='catalog' else '')
    return f'''<form id="cr-picker" class="cr-picker"><h2>{title}</h2><div class="cr-picker-fields">
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
        links.append(f'<a class="cr-tile catalog-mark{ " catalog-model" if isbrand else ""}" href="{h(url)}" data-directory-name="{h(x["name"])}">{image}<span class="catalog-mark__title">{h(x["name"])}</span><small>{"Офлайн" if local else "Онлайн"}</small></a>')
    noun='модели' if isbrand else 'марки'
    return f'''<section class="cr-section" aria-labelledby="cr-directory-title"><div class="cr-row cr-between"><h2 id="cr-directory-title">{'Модели Audi' if isbrand else 'Все марки'}</h2><label class="cr-search"><span class="cr-sr">Поиск {noun}</span><input id="cr-directory-search" type="search" placeholder="{'Модель, например Q8' if isbrand else 'Марка, например Ауди или Audi'}" autocomplete="off"></label></div><p class="cr-small cr-muted">Названия с отметкой «Онлайн» открываются на основном сайте и требуют интернета.</p><p id="cr-directory-count" class="cr-small" role="status"></p><div class="cr-tiles" id="cr-directory">{''.join(links)}</div><div id="cr-directory-empty" class="cr-card" hidden><h3>Ничего не нашли</h3><p>Попробуйте другое название или подберите стекло по VIN / фото.</p>{button('Помочь с подбором','data-help')}</div></section>'''

def filters():
    opts=''.join(f'<label>{name}<select name="{key}"><option value="any">Любой вариант</option><option value="yes">Есть</option><option value="no">Нет</option><option value="unknown">Не знаю</option></select></label>' for key,name in [('hud','Проекция HUD'),('camera','Камера'),('rain','Датчик дождя'),('heating','Обогрев'),('athermal','Атермальное стекло')])
    brands=sorted({p['brand'] for p in products})
    return f'''<details class="cr-filters" id="cr-filters" open><summary>Фильтры стекла</summary><form id="cr-filter-form"><label>Тип стекла<select name="glass"><option value="windshield">Лобовое</option><option value="rear">Заднее</option><option value="side">Боковое</option></select></label><label>Год выпуска<select name="year"><option value="">2018 и новее</option>{''.join(f'<option>{y}</option>' for y in range(2026,2017,-1))}</select></label><p class="cr-small">Кузов: 5 дверей, 2018–<br><span class="cr-muted">В каталоге поставщика: 5D RANGER</span></p><div id="cr-side-options" hidden><label>Сторона<select name="side"><option value="any">Не знаю</option><option value="left">Левая</option><option value="right">Правая</option></select></label><label>Дверь<select name="door"><option value="any">Не знаю</option><option value="front">Передняя</option><option value="back">Задняя</option></select></label><label>Исполнение<select name="movement"><option value="any">Не знаю</option><option value="moving">Опускное</option><option value="fixed">Неподвижное</option></select></label></div>{opts}<label>Производитель<select name="brand"><option value="">Все производители</option>{''.join(f'<option>{h(b)}</option>' for b in brands)}</select></label><label class="cr-check"><input type="checkbox" name="stock"> С ценой и наличием в снимке</label><p class="cr-small cr-muted">«Нет» покажет только подтверждённое отсутствие опции. «Не знаю» не исключает варианты: комплектацию нужно проверить.</p><button class="cr-btn cr-outline" type="reset">Сбросить фильтры</button></form></details>'''

def listing():
    return f'''<section class="cr-section" aria-label="Стёкла Audi Q8"><div class="cr-list-layout">{filters()}<div class="cr-results"><div class="cr-row cr-between cr-list-head"><h2 id="cr-count" role="status">33 варианта в каталоге</h2><label>Сортировка<select id="cr-sort"><option value="recommended">Сначала с ценой</option><option value="price">Цена по возрастанию</option><option value="price-desc">Цена по убыванию</option><option value="brand">Производитель</option></select></label></div><div class="cr-mode" role="group" aria-label="Способ покупки">{button('Стекло с установкой','data-mode="install" aria-pressed="true"')}{button('Только стекло','data-mode="glass" aria-pressed="false"',True)}</div><p class="cr-small cr-muted">Подытог включает только указанные позиции. Калибровку, молдинги и другие работы согласуем после проверки автомобиля.</p><div id="cr-filter-chips" class="cr-chips"></div><div id="cr-products" class="cr-products"></div><p class="cr-small" id="cr-shown"></p><button class="cr-btn cr-outline" id="cr-more" type="button">Показать ещё</button><noscript><p>Для фильтрации включите JavaScript. Карточка AGC доступна по ссылке в навигации.</p></noscript></div></div></section>'''

def product(rel):
    return f'''<section class="cr-product-top" aria-label="Стекло и стоимость"><figure class="cr-product-image"><img src="{rel}assets/ph-05c7eb3402ec.png" width="720" height="505" alt="Схематичное изображение лобового стекла"><figcaption>Схема стекла · не фотография артикула</figcaption></figure><div class="cr-buy"><div class="cr-row cr-between"><span class="cr-badge">AGC · арт. 92644</span><a href="#cr-specs">Характеристики</a></div><h2>Лобовое стекло с HUD и камерой</h2><p>Датчик дождя · окно VIN · Audi Q8, 2018–</p><div class="cr-mode" role="group" aria-label="Способ покупки">{button('Стекло с установкой','data-mode="install" aria-pressed="true"')}{button('Только стекло','data-mode="glass" aria-pressed="false"',True)}</div><div id="cr-product-estimate" class="cr-estimate"><dl><div><dt>Стекло</dt><dd>44 650 ₽</dd></div><div><dt>Замена</dt><dd>6 000 ₽</dd></div><div class="cr-total"><dt>Подытог</dt><dd>50 650 ₽</dd></div></dl></div><p class="cr-small">Калибровку, молдинги и дополнительные работы согласуем после проверки автомобиля.</p><p class="cr-stock">Цена и наличие — снимок от 19.11.2026. Наличие в выбранном центре и срок подтвердит менеджер.</p><div class="cr-actions">{button('Заявка на установку','data-order="92644"')}{button('Подобрать по VIN / фото','data-help',True)}</div><div class="cr-row cr-between"><a href="#cr-centers">Ярославль · <span data-center-label>выбрать центр</span></a>{button('В сравнение','data-compare="92644" aria-pressed="false"',True)}</div></div></section><section class="cr-section" id="cr-specs"><h2>Характеристики и совместимость</h2><p>Опции указаны в каталоге. Точную применимость проверяют по комплектации автомобиля.</p><dl class="cr-specs"><div><dt>Автомобиль</dt><dd>Audi Q8 · 5 дверей · 2018–</dd></div><div><dt>Производитель</dt><dd>AGC</dd></div><div><dt>Eurocode</dt><dd>8645AGACMUVZ1B</dd></div><div><dt>Номер OEM</dt><dd>4M8845099PNVB</dd></div><div><dt>Опции по каталогу</dt><dd>HUD, камера, датчик дождя, окно VIN</dd></div><div><dt>Обогрев / атермальность</dt><dd>Не подтверждены · уточните по VIN</dd></div></dl></section><section class="cr-section"><h2>Варианты с теми же кодами в каталоге</h2><p>Совпадают Eurocode и OEM. Это кандидаты для проверки по VIN; дополнительные опции и применимость нужно подтвердить.</p><div id="cr-alternatives" class="cr-products"></div><a class="cr-text-link" href="{rel}catalog/audi/q8/index.html">Все стёкла Audi Q8</a></section>'''

def services():
    return f'''<section class="cr-section" id="cr-centers"><div class="cr-row cr-between"><h2>Где установить стекло</h2><span class="cr-badge">Ярославль</span></div><p>Выберите удобный центр. Сначала проверим комплектацию и наличие, затем согласуем стоимость и время.</p><div class="cr-centers"><article class="cr-card"><h3>Городской Вал, 2</h3><p>Ежедневно, 9:00–18:00</p><a href="tel:+78007073772">8 (800) 707-37-72</a><div class="cr-row cr-between">{button('Выбрать центр','data-center="val"',True)}<a href="https://yandex.ru/maps/?text=Ярославль%20Городской%20Вал%202" target="_blank" rel="noopener">Маршрут онлайн</a></div></article><article class="cr-card"><h3>Улица Громова, 1Ж</h3><p>Пн–сб, 9:00–18:00 · вс — выходной</p><a href="tel:+78007073772">8 (800) 707-37-72</a><div class="cr-row cr-between">{button('Выбрать центр','data-center="gromova"',True)}<a href="https://yandex.ru/maps/?text=Ярославль%20Громова%201Ж" target="_blank" rel="noopener">Маршрут онлайн</a></div></article></div><p id="cr-center-status" class="cr-small" role="status">Наличие на складе поставщика не означает наличие в центре.</p></section><section class="cr-section cr-assurances" aria-label="Условия покупки"><article class="cr-card"><h3>Гарантия на стекло</h3><p>Зависит от производителя и выбранного товара. Условия программы AGC проверяют при заказе.</p><a href="https://autosteklo.pro/zamena-avtostekol/rasshirennaya-garantiya-na-avtostekla-agc/" target="_blank" rel="noopener">Условия AGC онлайн</a></article><article class="cr-card"><h3>Гарантия на работу</h3><p>Срок, покрытие и порядок обращения фиксируются в документах на установку.</p><a href="https://autosteklo.pro/garantiya/" target="_blank" rel="noopener">Условия гарантии онлайн</a></article><article class="cr-card"><h3>Отзывы клиентов</h3><p>Посмотрите опыт клиентов перед выбором сервисного центра.</p><a href="https://autosteklo.pro/reviews/" target="_blank" rel="noopener">Читать отзывы онлайн</a></article></section><section class="cr-section cr-process"><div><h2>Как проходит замена</h2><ol><li>Проверяем VIN, опции стекла и комплектацию автомобиля.</li><li>Подтверждаем наличие, работы и смету до заказа.</li><li>Согласуем центр и время, устанавливаем стекло.</li><li>Проверяем результат, выдаём документы и рекомендации.</li></ol></div><img src="PLACEHOLDER_PROCESS" alt="Процесс установки автостекла в сервисном центре" width="1280" height="853" loading="lazy"></section><section class="cr-section cr-faq"><h2>Частые вопросы</h2><details><summary>Что входит в указанную стоимость?</summary><p>Подытог складывается из цены стекла и услуги замены, если она выбрана. Калибровка камеры, молдинги, крепления и другие необходимые работы согласуются отдельно после проверки. Автоматически платные дополнения не выбираются.</p></details><details><summary>Как узнать, нужны ли HUD, камера и обогрев?</summary><p>Посмотрите комплектацию автомобиля или приложите фото зоны камеры и маркировки стекла. VIN помогает проверить применимость; при выборе «Не знаю» варианты не исключаются.</p>{button('Проверить по VIN / фото','data-help',True)}</details><details><summary>Можно купить стекло без установки?</summary><p>Да, выберите «Только стекло». Подытог и состав заявки изменятся. Возможность выдачи, упаковку и срок нужно подтвердить для выбранного товара.</p></details><details><summary>Как оплатить и получить стекло?</summary><p>Способ оплаты, самовывоз или доставку и её стоимость согласуют с центром до заказа. В офлайн-копии оплата и бронирование не выполняются.</p></details><details><summary>Можно записаться на точное время?</summary><p>Время подтверждает менеджер после проверки комплектации и наличия. Форма создаёт обращение, а не бронь свободного слота.</p></details></section>'''

def dialogs():
    return '''<dialog id="cr-order-dialog" class="cr-dialog" aria-labelledby="cr-order-title"><div class="cr-dialog-head"><h2 id="cr-order-title">Заявка на установку</h2><button type="button" class="cr-close" data-close aria-label="Закрыть форму">×</button></div><form id="cr-order-form"><div id="cr-order-summary" class="cr-summary"></div><p class="cr-demo">Офлайн-копия: данные не отправляются. Здесь можно проверить форму и состав обращения.</p><div class="cr-two-fields"><label>Телефон для ответа<input name="phone" type="tel" inputmode="tel" autocomplete="tel" placeholder="+7 (___) ___-__-__" required maxlength="24"></label><label>Имя — необязательно<input name="customerName" autocomplete="given-name" maxlength="80"></label></div><label>Автомобиль и нужное стекло<input name="car" maxlength="180" placeholder="Например, Audi Q8 2020, лобовое"></label><label>VIN — необязательно<input name="vin" autocomplete="off" maxlength="17" placeholder="17 символов VIN" aria-describedby="cr-vin-hint"></label><p class="cr-small cr-muted" id="cr-vin-hint">VIN указан в документах автомобиля. Если VIN нет под рукой, приложите фото.</p><label class="cr-upload">Фото маркировки или зоны камеры<input name="photos" type="file" accept="image/jpeg,image/png,image/webp" multiple aria-describedby="cr-photo-hint"></label><p class="cr-small cr-muted" id="cr-photo-hint">До 3 фото JPG, PNG или WebP, каждое до 10 МБ. Снимите маркировку в углу и крепление камеры из салона. Файлы остаются в этой вкладке.</p><div id="cr-photo-preview" class="cr-photo-preview"></div><label>Удобный центр<select name="center"><option value="">Выберу с менеджером</option><option value="val">Ярославль · Городской Вал, 2</option><option value="gromova">Ярославль · Громова, 1Ж</option></select></label><label class="cr-check"><input name="consent" type="checkbox" required> <span>Согласен(на) на обработку персональных данных. <a href="https://autosteklo.pro/personal-data/" target="_blank" rel="noopener">Условия онлайн</a></span></label><p id="cr-form-status" class="cr-form-status" role="status" tabindex="-1"></p><button type="submit" class="cr-btn cr-full" id="cr-form-submit">Проверить заявку</button><p class="cr-small cr-muted">Для реального обращения: <a href="tel:+78007073772">8 (800) 707-37-72</a>. Время установки согласуют отдельно.</p></form></dialog><dialog id="cr-compare-dialog" class="cr-dialog cr-wide" aria-labelledby="cr-compare-title"><div class="cr-dialog-head"><h2 id="cr-compare-title">Сравнение стёкол</h2><button type="button" class="cr-close" data-close aria-label="Закрыть сравнение">×</button></div><p>Сравните опции и стоимость. Применимость и срок нужно подтвердить по VIN.</p><div id="cr-compare-content" class="cr-table-scroll" tabindex="0" role="region" aria-label="Таблица сравнения стёкол"></div></dialog><div id="cr-bottom" class="cr-bottom" hidden></div><div id="cr-toast" class="cr-toast" role="status" hidden></div>'''

for path,kind in ROUTES.items():
    f=ROOT/path;soup=BeautifulSoup(f.read_text(),'html.parser')
    rel=os.path.relpath(ROOT,f.parent).replace('\\','/')+'/'
    for tag in soup.select('script[src]'):
        if 'offline-catalog' in tag['src'] or re.search(r'/(catalog(?:_\d)?|product)-bundle-',tag['src']):tag.decompose()
    for tag in soup.select('[data-cro-resource]'):tag.decompose()
    asset_version='?v=catalog-landing-20261119' if kind=='catalog' else ''
    css=soup.new_tag('link',rel='stylesheet',href=rel+'assets/catalog-experience.css'+asset_version,attrs={'data-cro-resource':'true'});soup.head.append(css)
    for name in ['catalog-experience-data.js','catalog-experience.js']:
        t=soup.new_tag('script',src=rel+'assets/'+name+asset_version,attrs={'defer':'','data-cro-resource':'true'});soup.head.append(t)
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
    content=f'<main id="main" class="cr-root" data-kind="{kind}" data-root="{rel}"><div class="cr-wrap base-container"><a class="cr-skip" href="#cr-content">Перейти к подбору</a><nav class="breadcrumbs cr-breadcrumbs" itemscope itemtype="https://schema.org/BreadcrumbList" aria-label="Хлебные крошки">{crumbs}</nav><div id="cr-content" class="cr-heading"><h1 class="{title_class}">{title}</h1><p>Ярославль · подбор, покупка и установка автостёкол</p></div>'
    if kind=='product':content+=product(rel)
    else:
        if kind in ['catalog','brand']:content+=picker(kind)+help_block()+directory_block(kind,rel)
        else:content+=picker(kind)+'<p class="cr-inline-help"><button type="button" class="cr-text-button" data-help>Не уверены в комплектации? Подберём по VIN / фото</button></p>'+listing()
    content+=services().replace('PLACEHOLDER_PROCESS',rel+'assets/typical2banner-665ad213bc04.png')
    if kind=='product':content+=help_block()
    content+=f'<p class="cr-snapshot">Офлайн-копия · каталог от 19.11.2026. Актуальные цены, наличие и условия подтвердит менеджер. <a href="https://autosteklo.pro/{path.removesuffix("index.html")}" target="_blank" rel="noopener">Страница на сайте онлайн</a></p></div>{dialogs()}</main>'
    fragment=BeautifulSoup(content,'html.parser')
    if kind=='catalog':
        # The catalogue landing page uses the original site's three lower blocks.
        for selector in ['.cr-heading>p','#cr-picker-note','#cr-directory-count','#cr-centers']:
            element=fragment.select_one(selector)
            if element:element.decompose()
        fragment.select_one('#cr-directory-empty')['role']='status'
    picker_form=fragment.select_one('#cr-picker')
    if picker_form:
        picker_form['class']+=['filter-block-typical1-wrapper','typ2']
        picker_form.h2['class']=['filter-block-typical1__title']
    for heading in fragment.select('h2'):
        if heading.find_parent('dialog'):heading['class']=['modal-typical__header']
        elif heading.find_parent('form',id='cr-picker') is None:heading['class']=['base__title']
    for control in fragment.select('button.cr-btn'):
        variant='a-btn-black' if control.find_parent('form',id='cr-picker') else 'a-btn-outline' if 'cr-outline' in control['class'] else 'a-btn-red2'
        control['class']+=['a-btn',variant]
    for control in fragment.select('#cr-order-form input:not([type="file"]):not([type="checkbox"])'):
        control['class']=['form-group__input']
    if kind=='catalog':
        outer=soup.new_tag('main',id='main',attrs={'class':'main catalog-main'})
        enhanced=fragment.select_one('main')
        enhanced.name='div';enhanced.attrs.pop('id',None)
        outer.append(enhanced)
        native=BeautifulSoup((ROOT/'tools/catalog_native_blocks.html.txt').read_text(),'html.parser')
        outer.append(native)
        soup.select_one('#main').replace_with(outer)
    else:
        soup.select_one('#main').replace_with(fragment)
    soup.body['class']=list(set(soup.body.get('class',[])+['cro-page']))
    # Keep the original chrome, while correcting unusable tel formatting.
    for a in soup.select('a[href]'):
        if a['href'].startswith('tel:') and '707' in a['href']:a['href']='tel:+78007073772'
    soup.title.string=title+' — Автостёкла, Ярославль (офлайн)'
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
