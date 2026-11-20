"""Offline UI regression checks. Run: python tests/catalog_smoke.py [--browser PATH]."""
import argparse, asyncio, base64, json
from pathlib import Path
from playwright.async_api import async_playwright

ROOT=Path(__file__).resolve().parents[1]
PRODUCT='product/audi-q8-5d-suv-2018-steklo-vetrovoe-datchik-dozhdia-kamera-hud-vin-3/index.html'
PAGES=['catalog/index.html','catalog/audi/index.html','catalog/audi/q8/index.html',
       'catalog/audi/q8/lobovye-stekla/5d-ranger-2018/index.html',PRODUCT]

async def run(executable):
 async with async_playwright() as playwright:
  browser=await playwright.chromium.launch(**({'executable_path':executable} if executable else {}),args=['--no-sandbox'])
  context=await browser.new_context(viewport={'width':1440,'height':1000})
  await context.route('http://**/*',lambda route:route.abort())
  await context.route('https://**/*',lambda route:route.abort())
  page=await context.new_page();errors=[];requests=[]
  page.on('pageerror',lambda error:errors.append(str(error)))
  page.on('request',lambda request:requests.append(request.url))
  async def open(route):
   await page.goto((ROOT/route).as_uri(),wait_until='load')
  async def click(selector):
   await page.locator(selector).click()
  async def check_order(product_id,purchase='install',brand=False):
   expected=await page.evaluate("([id,brand])=>(brand?CRO_DATA.brandProducts:CRO_DATA.products).find(p=>p.id===id)",[product_id,brand])
   assert await page.locator('#cr-order-dialog').is_visible()
   assert await page.locator('#cr-order-title').evaluate("e=>e.tagName==='DIV'")
   assert await page.locator('#cr-order-title').inner_text()==('Заказать стекло с установкой' if purchase=='install' else 'Заказать стекло без установки')
   assert await page.locator('#cr-form-submit').inner_text()=='Отправить заявку'
   assert ' '.join((await page.locator('#cr-order-summary>strong').inner_text()).split())==' '.join(expected['title'].split())
   summary=await page.locator('#cr-order-summary').inner_text()
   assert 'арт.' not in summary and 'центр' not in summary and 'Калибровка' not in summary
   assert await page.locator('#cr-order-form').evaluate("f=>[...f.elements].filter(e=>e.name).map(e=>e.name).join(',')")=='customerName,phone,consent'
   assert await page.locator('#cr-order-form a[href^="tel:"]').count()==0
   labels=await page.locator('#cr-order-summary dt').all_text_contents()
   assert labels==(['Стекло','Замена','Подытог'] if purchase=='install' else ['Стекло','Только стекло'])
   total=None if expected['price'] is None or (purchase=='install' and expected['service'] is None) else expected['price']+(expected['service'] if purchase=='install' else 0)
   amount=await page.locator('#cr-order-summary .cr-total dd').inner_text()
   assert (''.join(x for x in amount if x.isdigit())==str(total)) if total is not None else amount=='Уточнить цену'
  await open(PAGES[0])
  assert await page.locator('#cr-native-button').get_attribute('aria-disabled')=='true'
  await page.locator('#cr-native-glass-field').focus()
  await page.keyboard.press('ArrowDown');await page.keyboard.press('End');await page.keyboard.press('Enter')
  assert await page.locator('#cr-native-glass').input_value()=='windshield'
  for field,value in [('brand','AUDI'),('model','Q8'),('year','2020'),('body','5d-ranger-2018')]:
   await click(f'[data-native-field="{field}"]')
   await click(f'[data-native-field="{field}"] [data-native-value="{value}"]')
  await click('#cr-native-button');await page.wait_for_url('**/5d-ranger-2018/index.html*')
  assert 'year=2020' in page.url
  await page.goto(page.url.split('?')[0]+'?brand=AGC&stock=true&hud=no&side=right',wait_until='load')
  assert '33 ' in await page.locator('#cr-count').inner_text()
  assert not any(key+'=' in page.url for key in ['brand','stock','hud','side'])
  await page.evaluate('sessionStorage.clear()');await open(PAGES[0])
  await page.locator('#cr-directory-search').fill('ауди')
  assert await page.locator('.cr-tile:visible').count()==1
  await click('.cr-tile:visible');await page.wait_for_url('**/catalog/audi/index.html*')
  assert await page.locator('#cr-native-picker [data-native-field]').count()==5
  assert await page.locator('#cr-directory-title').inner_text()=='Выберите марку вашего автомобиля'
  assert await page.locator('.cr-native-brand-products .product-card').count()==10
  await click('[data-brand-order="103436"]')
  assert await page.locator('#cr-order-dialog').is_visible()
  summary=await page.locator('#cr-order-summary').inner_text()
  assert 'AUDI A3' in summary and 'Audi Q8' not in summary
  await check_order('103436',brand=True)
  await page.keyboard.press('Escape')
  await click('[data-brand-order="105449"]')
  summary=await page.locator('#cr-order-summary').inner_text()
  assert '22' in summary and '850' in summary
  await check_order('105449',brand=True)
  await page.keyboard.press('Escape')
  await page.locator('#cr-directory-search').fill('ку8')
  assert await page.locator('.cr-tile:visible').count()==1
  await click('.cr-tile:visible');await page.wait_for_url('**/catalog/audi/q8/index.html*')
  assert await page.locator('.cr-heading').evaluate("e=>e.nextElementSibling.classList.contains('cr-help')")
  assert await page.locator('.cr-root #cr-centers').count()==0
  assert await page.locator('.cr-native-benefits .product-similar-side-item').count()==3 and await page.locator('.cr-process').count()==1
  assert await page.locator('.cr-native-model-products .product-card').count()==10
  assert await page.locator('#cr-native-picker [data-native-field]').count()==5
  await click('.cr-help [data-help]');assert await page.locator('#cr-help-dialog').is_visible();await page.keyboard.press('Escape')
  await page.goto(page.url.split('?')[0]+'?mode=glass',wait_until='load')
  await click('[data-order="92287"]')
  summary=await page.locator('#cr-order-summary').inner_text()
  assert 'Стекло с установкой' in summary
  await check_order('92287')
  await page.keyboard.press('Escape')
  await page.get_by_role('link',name='5D RANGER (2018 - )',exact=True).click()
  await page.wait_for_url('**/5d-ranger-2018/index.html*')
  assert await page.locator('.cr-root').get_attribute('data-kind')=='generation'
  await page.go_back(wait_until='load')
  await page.wait_for_url('**/catalog/audi/q8/index.html*')
  await page.get_by_role('link',name='5D RANGER (2018 - )',exact=True).click()
  await page.wait_for_url('**/5d-ranger-2018/index.html*')
  assert await page.locator('.cr-native-card').count()==6
  assert await page.locator('.cr-heading').evaluate("e=>e.nextElementSibling.classList.contains('cr-help')")
  assert await page.locator('[data-native-option]').count()==6
  await click('[data-native-option="hud"]');assert '24 ' in await page.locator('#cr-count').inner_text()
  await click('[data-native-option="hud"]');assert '33 ' in await page.locator('#cr-count').inner_text()
  await click('[data-native-option="heating"]')
  assert '2 ' in await page.locator('#cr-count').inner_text()
  await click('#catalogClear')
  await click('[data-native-sort="price"]')
  prices=await page.locator('.cr-native-card .product-card__prices__main').all_text_contents()
  first=await page.locator('.cr-native-card').first.get_attribute('data-product')
  assert '11' in prices[0] and '300' in prices[0]
  await click('#cr-more');assert await page.locator('.cr-native-card').count()==12
  await page.set_viewport_size({'width':390,'height':844})
  assert await page.locator('#cr-sort').input_value()=='price'
  assert await page.locator('.cr-native-card').first.get_attribute('data-product')==first
  await click('#catalogFiltersOpen');assert await page.locator('#catalogFiltersBlock').get_attribute('role')=='dialog'
  await page.keyboard.press('Escape');assert await page.evaluate('document.body.style.overflow')==''
  await page.set_viewport_size({'width':1440,'height':1000})
  await click('[data-native-glass="side"]')
  assert 'не сохранён' in await page.locator('.cr-empty').inner_text()
  await click('.cr-empty [data-help]')
  assert await page.locator('#cr-help-dialog').is_visible()
  assert await page.locator('#cr-help-summary').count()==0
  assert await page.locator('#cr-help-form [name="car"],#cr-help-form [name="center"]').count()==0
  await page.keyboard.press('Escape')
  await click('#catalogClear')
  await click('[data-native-option="hud"]')
  cards=page.locator('.cr-native-card');assert await cards.count()==6
  chosen=await cards.first.get_attribute('data-product')
  await click(f'.cr-native-card[data-product="{chosen}"] [data-order]')
  assert await page.locator('#cr-order-dialog').is_visible()
  await check_order(chosen)
  assert await page.locator('#cr-form-submit').get_attribute('data-ready')=='false'
  await page.locator('#cr-order-form [name="phone"]',).fill('123')
  await page.locator('#cr-order-form [name="consent"]').check()
  await click('#cr-form-submit')
  assert await page.locator('#cr-order-form [name="phone"]').get_attribute('aria-invalid')=='true'
  await page.locator('#cr-order-form [name="phone"]').fill('+7 (900) 123-45-67')
  assert await page.locator('#cr-form-submit').get_attribute('data-ready')=='true'
  before=len(requests);await click('#cr-form-submit')
  assert 'не отправлены' in await page.locator('#cr-form-status').inner_text()
  assert len(requests)==before
  await page.keyboard.press('Escape')
  await click('.cr-help [data-help]')
  assert await page.locator('#cr-help-dialog').is_visible()
  assert await page.locator('#cr-help-title').evaluate("e=>e.tagName==='DIV'")
  await page.locator('#cr-help-form [name="phone"]').fill('+7 (900) 123-45-67')
  await page.locator('#cr-help-form [name="consent"]').check()
  await page.locator('#cr-help-form [name="vin"]').fill('BADVIN')
  await click('#cr-help-submit')
  assert await page.locator('#cr-help-form [name="vin"]').get_attribute('aria-invalid')=='true'
  assert await page.locator('#cr-help-submit').get_attribute('data-ready')=='false'
  await page.locator('#cr-help-form [name="vin"]').fill('WAUZZZ4M0JD000001')
  assert await page.locator('#cr-help-submit').get_attribute('data-ready')=='true'
  await page.locator('#cr-help-form [name="photos"]').set_input_files({'name':'invalid.txt','mimeType':'text/plain','buffer':b'x'})
  assert 'до 3 фото' in await page.locator('#cr-help-status').inner_text()
  png=base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+a6XQAAAAASUVORK5CYII=')
  await page.locator('#cr-help-form [name="photos"]').set_input_files({'name':'mark.png','mimeType':'image/png','buffer':png})
  assert await page.locator('#cr-photo-preview img').count()==1
  assert await page.locator('#cr-help-form a[href^="tel:"]').count()==0
  before=len(requests);await click('#cr-help-submit')
  assert 'не отправлены' in await page.locator('#cr-help-status').inner_text()
  assert len(requests)==before
  assert '79001234567' not in await page.evaluate('JSON.stringify(sessionStorage)')
  assert 'WAUZZZ4M0JD000001' not in await page.evaluate('JSON.stringify(sessionStorage)')
  assert 'WAUZZZ4M0JD000001' not in page.url
  await page.locator('#cr-help-form [name="vin"]').fill('BADVIN')
  await click('#cr-help-submit')
  assert await page.locator('#cr-help-form [name="vin"]').get_attribute('aria-invalid')=='true'
  await page.keyboard.press('Escape')
  await click(f'.cr-native-card[data-product="{chosen}"] [data-order]')
  await check_order(chosen)
  await click('#cr-form-submit')
  assert 'не отправлены' in await page.locator('#cr-form-status').inner_text()
  await page.keyboard.press('Escape')
  await click('.cr-native-card[data-product="92644"] .product-card__title')
  await page.wait_for_url('**/product/**/index.html*')
  assert ''.join(x for x in await page.locator('#cr-product-estimate .cr-total dd').inner_text() if x.isdigit())=='50650'
  await click('.cr-buy [data-mode="glass"]')
  assert ''.join(x for x in await page.locator('#cr-product-estimate .cr-total dd').inner_text() if x.isdigit())=='44650'
  await click('.cr-buy [data-order="92644"]')
  summary=await page.locator('#cr-order-summary').inner_text()
  assert 'Стекло без установки' in summary and 'Громова' not in summary and '6 000' not in summary
  await check_order('92644','glass')
  await page.keyboard.press('Escape')
  await click('.cr-native-product .--product-order[data-id="93869"]')
  await check_order('93869')
  await page.keyboard.press('Escape')
  await click('.cr-native-product .--product-price[data-id="90075"]')
  await check_order('90075')
  await page.keyboard.press('Escape')
  await page.go_back(wait_until='load')
  assert await page.locator('[data-native-option="hud"]').get_attribute('aria-checked')=='true'
  layout=[]
  for width in [1440,768,390,320]:
   await page.set_viewport_size({'width':width,'height':844 if width<760 else 1000})
   for route in PAGES:
    await open(route)
    size=await page.evaluate('({width:innerWidth,scroll:document.documentElement.scrollWidth})')
    assert size['width']==size['scroll'],(route,width,size)
    assert await page.locator('meta[name="robots"][content="noindex, nofollow"]').count()==1
    assert not await page.locator('.cr-root img').evaluate_all('(xs)=>xs.some(x=>x.complete&&!x.naturalWidth)')
    if width<760:
     assert await page.locator('#main .breadcrumbs').evaluate('(el)=>el.getBoundingClientRect().top')>=120
     if route==PRODUCT:
      assert await page.locator('.cr-product-bar').is_visible()
      await click('.cr-product-bar [data-order]')
      assert await page.locator('#cr-order-dialog').is_visible()
      assert await page.locator('.cr-product-bar').is_hidden()
      await page.keyboard.press('Escape')
    layout.append({'page':route,'viewport':width,'overflow':False})
  assert not errors,errors
  print(json.dumps({'passed':True,'offline':True,'products':33,'checks':['native five-field picker, keyboard and local generation navigation','Russian search and local navigation','native option filters and removed-filter migration','stable sorting and load more','side-glass empty state','native product details and price selection','context and price calculation','phone/VIN/photo validation','no form requests or PII storage','back navigation state','20 responsive page/viewport checks','mobile price bar and dialog focus'],'layouts':layout,'javascriptErrors':errors},ensure_ascii=False,indent=2))
  await browser.close()

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--browser');args=parser.parse_args()
 asyncio.run(run(args.browser))
