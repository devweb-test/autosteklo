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
  await open(PAGES[0])
  await page.locator('#cr-directory-search').fill('ауди')
  assert await page.locator('.cr-tile:visible').count()==1
  await click('.cr-tile:visible');await page.wait_for_url('**/catalog/audi/index.html*')
  await page.locator('#cr-directory-search').fill('ку8')
  assert await page.locator('.cr-tile:visible').count()==1
  await click('.cr-tile:visible');await page.wait_for_url('**/catalog/audi/q8/index.html*')
  await page.get_by_role('link',name='5D RANGER (2018 - )',exact=True).click()
  await page.wait_for_url('**/5d-ranger-2018/index.html*')
  assert await page.locator('.cr-root').get_attribute('data-kind')=='generation'
  await page.go_back(wait_until='load')
  await page.wait_for_url('**/catalog/audi/q8/index.html*')
  assert await page.locator('.cr-glass-card').count()==6
  await page.locator('[name="hud"]').select_option('yes')
  assert '24 ' in await page.locator('#cr-count').inner_text()
  await page.locator('[name="hud"]').select_option('no')
  assert await page.locator('.cr-glass-card').count()==0
  assert await page.locator('.cr-empty').is_visible()
  await page.locator('[name="hud"]').select_option('unknown')
  assert '33 ' in await page.locator('#cr-count').inner_text()
  await page.locator('[name="heating"]').select_option('yes')
  assert '2 ' in await page.locator('#cr-count').inner_text()
  await click('#cr-filter-form [type="reset"]')
  await page.locator('#cr-sort').select_option('price')
  prices=await page.locator('.cr-glass-card .cr-estimate dd:first-of-type').all_text_contents()
  first=await page.locator('.cr-glass-card').first.get_attribute('data-product')
  assert '11' in prices[0] and '300' in prices[0]
  await click('#cr-more');assert await page.locator('.cr-glass-card').count()==12
  await page.set_viewport_size({'width':390,'height':844})
  assert await page.locator('#cr-sort').input_value()=='price'
  assert await page.locator('.cr-glass-card').first.get_attribute('data-product')==first
  await page.set_viewport_size({'width':1440,'height':1000})
  await page.locator('#cr-filter-form [name="glass"]').select_option('side')
  assert await page.locator('#cr-side-options').is_visible()
  assert 'не сохранён' in await page.locator('.cr-empty').inner_text()
  await page.locator('[name="side"]').select_option('right')
  await click('.cr-empty [data-help]')
  assert 'Боковое' in await page.locator('#cr-order-summary').inner_text()
  await page.keyboard.press('Escape')
  await click('#cr-filter-form [type="reset"]')
  await page.locator('[name="hud"]').select_option('yes')
  await page.locator('[name="stock"]').check()
  cards=page.locator('.cr-glass-card');assert await cards.count()==4
  ids=[await cards.nth(i).get_attribute('data-product') for i in range(4)]
  for product_id in ids[:3]:await click(f'[data-compare="{product_id}"]')
  await click(f'[data-compare="{ids[3]}"]')
  assert '3 из 3' in await page.locator('#cr-bottom').inner_text()
  assert 'до 3' in await page.locator('#cr-toast').inner_text()
  await click('[data-open-compare]')
  assert await page.locator('#cr-compare-dialog').is_visible()
  assert await page.locator('.cr-compare-table thead th').count()==4
  assert 'Не подтверждено' in await page.locator('.cr-compare-table').inner_text()
  chosen=ids[0]
  await click(f'#cr-compare-content [data-order="{chosen}"]')
  assert await page.locator('#cr-order-dialog').is_visible()
  assert f'арт. {chosen}' in await page.locator('#cr-order-summary').inner_text()
  await page.locator('#cr-order-form [name="phone"]',).fill('123')
  await page.locator('#cr-order-form [name="consent"]').check()
  await click('#cr-form-submit')
  assert await page.locator('#cr-order-form [name="phone"]').get_attribute('aria-invalid')=='true'
  await page.locator('#cr-order-form [name="phone"]').fill('+7 (900) 123-45-67')
  await page.locator('#cr-order-form [name="vin"]').fill('BADVIN')
  await click('#cr-form-submit')
  assert await page.locator('#cr-order-form [name="vin"]').get_attribute('aria-invalid')=='true'
  await page.locator('#cr-order-form [name="vin"]').fill('WAUZZZ4M0JD000001')
  await page.locator('#cr-order-form [name="photos"]').set_input_files({'name':'invalid.txt','mimeType':'text/plain','buffer':b'x'})
  assert 'до 3 фото' in await page.locator('#cr-form-status').inner_text()
  png=base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+a6XQAAAAASUVORK5CYII=')
  await page.locator('#cr-order-form [name="photos"]').set_input_files({'name':'mark.png','mimeType':'image/png','buffer':png})
  assert await page.locator('#cr-photo-preview img').count()==1
  await page.locator('#cr-order-form [name="center"]').select_option('gromova')
  assert 'Громова' in await page.locator('#cr-order-summary').inner_text()
  before=len(requests);await click('#cr-form-submit')
  assert 'не отправлены' in await page.locator('#cr-form-status').inner_text()
  assert len(requests)==before
  assert '79001234567' not in await page.evaluate('JSON.stringify(sessionStorage)')
  assert 'WAUZZZ4M0JD000001' not in await page.evaluate('JSON.stringify(sessionStorage)')
  assert 'WAUZZZ4M0JD000001' not in page.url
  await page.keyboard.press('Escape')
  await click('[data-clear-compare]')
  await click('.cr-glass-card[data-product="92644"] h3 a')
  await page.wait_for_url('**/product/**/index.html*')
  assert ''.join(x for x in await page.locator('#cr-product-estimate .cr-total dd').inner_text() if x.isdigit())=='50650'
  await click('.cr-buy [data-mode="glass"]')
  assert ''.join(x for x in await page.locator('#cr-product-estimate .cr-total dd').inner_text() if x.isdigit())=='44650'
  await click('.cr-buy [data-order="92644"]')
  summary=await page.locator('#cr-order-summary').inner_text()
  assert 'Только стекло' in summary and 'Громова' in summary and '6 000' not in summary
  await page.keyboard.press('Escape')
  await page.go_back(wait_until='load')
  assert await page.locator('[name="hud"]').input_value()=='yes'
  assert await page.locator('[name="stock"]').is_checked()
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
     assert await page.locator('.cr-breadcrumbs').evaluate('(el)=>el.getBoundingClientRect().top')>=120
     if route==PRODUCT:
      assert await page.locator('.cr-product-bar').is_visible()
      await click('.cr-product-bar [data-order]')
      assert await page.locator('#cr-order-dialog').is_visible()
      assert await page.locator('.cr-product-bar').is_hidden()
      await page.keyboard.press('Escape')
    layout.append({'page':route,'viewport':width,'overflow':False})
  assert not errors,errors
  print(json.dumps({'passed':True,'offline':True,'products':33,'checks':['Russian search and local navigation','positive, negative and unknown options','stable sorting and load more','side-glass empty state','comparison up to 3 products','context and price calculation','phone/VIN/photo validation','no form requests or PII storage','back navigation state','20 responsive page/viewport checks','mobile price bar and dialog focus'],'layouts':layout,'javascriptErrors':errors},ensure_ascii=False,indent=2))
  await browser.close()

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--browser');args=parser.parse_args()
 asyncio.run(run(args.browser))
