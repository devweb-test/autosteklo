"""Compare added blocks against native site CSS at six viewport widths."""
import argparse,asyncio,json
from pathlib import Path
from playwright.async_api import async_playwright
ROOT=Path(__file__).resolve().parents[1]
PAGES=['catalog/index.html','catalog/audi/index.html','catalog/audi/q8/index.html',
       'catalog/audi/q8/lobovye-stekla/5d-ranger-2018/index.html',
       'product/audi-q8-5d-suv-2018-steklo-vetrovoe-datchik-dozhdia-kamera-hud-vin-3/index.html']
REFERENCE='''<aside id="native-style-reference" style="position:fixed;inset:0;visibility:hidden;pointer-events:none;z-index:-1"><div class="base-wrapper"><div class="base-container"><h1 class="catalog__title base__title">Заголовок</h1><h1 id="native-product-title" class="product__title base__title">Заголовок товара</h1><h1 id="native-generation-title" class="catalog__title">Заголовок</h1><h2 class="base__title">Заголовок раздела</h2><div class="breadcrumbs"><div class="breadcrumbs-item"><a class="breadcrumbs-item__text breadcrumbs-item__link">Главная</a></div><div class="breadcrumbs-item"><span class="breadcrumbs-item__text breadcrumbs-item__current">Каталог</span></div></div><div class="content-text"><p>Основной текст</p></div><button class="a-btn a-btn-red2">Действие</button><button class="a-btn a-btn-outline">Другое действие</button><div class="modal-typical"><form class="modal-typical-form"><div class="form-group"><input class="form-group__input"></div></form></div></div></div></aside>'''
COMPARE='''pairs=>pairs.flatMap(([native,current,keys])=>{const a=document.querySelector('#native-style-reference '+native),b=document.querySelector(current);if(!a||!b)return [];const x=getComputedStyle(a),y=getComputedStyle(b);return keys.filter(k=>x[k]!==y[k]).map(k=>({native,current,property:k,expected:x[k],actual:y[k]}))})'''
async def run(executable):
 async with async_playwright() as p:
  browser=await p.chromium.launch(**({'executable_path':executable} if executable else {}),args=['--no-sandbox'])
  context=await browser.new_context();await context.route('https://**/*',lambda r:r.abort());await context.route('http://**/*',lambda r:r.abort());page=await context.new_page();rows=[]
  for width in [1920,1440,1280,768,390,320]:
   await page.set_viewport_size({'width':width,'height':1000 if width>767 else 844})
   for route in PAGES:
    await page.goto((ROOT/route).as_uri());await page.evaluate('document.fonts.ready')
    await page.evaluate('(html)=>document.body.insertAdjacentHTML("beforeend",html)',REFERENCE)
    font=['fontFamily','fontSize','lineHeight','fontWeight','color']
    native_product=route.startswith('product/')
    crumbs='#main .breadcrumbs' if native_product else '.cr-breadcrumbs'
    pairs=[('.breadcrumbs-item__link',crumbs+' .breadcrumbs-item__link',font+['textDecorationLine']),('.breadcrumbs-item__current',crumbs+' .breadcrumbs-item__current',font+['textDecorationLine']),('h2.base__title','#cr-centers h2',font),('.content-text p','.cr-faq details p',font),('.a-btn-red2','.cr-root .a-btn-red2',['color','backgroundColor','borderColor','borderRadius']),('.a-btn-outline','.cr-root .a-btn-outline',['color','backgroundColor','borderColor','borderRadius'])]
    pairs.append(('.breadcrumbs',crumbs,['fontSize','lineHeight','color','margin']))
    pairs.append(('#native-product-title' if route.startswith('product/') else '#native-generation-title' if '/5d-ranger-' in route else 'h1.base__title','.product__title' if native_product else '.cr-heading h1',font+['textAlign']))
    errors=await page.evaluate(COMPARE,pairs)
    dimensions=await page.evaluate('''selector=>{const a=document.querySelector('#native-style-reference .base-container').getBoundingClientRect(),b=document.querySelector(selector).getBoundingClientRect();return {nativeWidth:a.width,actualWidth:b.width,nativeX:a.x,actualX:b.x}}''','.cr-native-product .page' if native_product else '.cr-wrap')
    assert dimensions['nativeWidth']==dimensions['actualWidth'] and dimensions['nativeX']==dimensions['actualX'],(width,route,dimensions)
    assert not errors,(width,route,errors)
    separator=await page.locator(crumbs+' .breadcrumbs-item').nth(1).evaluate("e=>getComputedStyle(e,'::before').content")
    assert separator=='"—"',separator
    assert await page.evaluate('document.documentElement.scrollWidth===innerWidth')
    if route.startswith('product/'):
     await page.locator('.cr-buy [data-order]').click()
     errors=await page.evaluate(COMPARE,[('.form-group__input','#cr-order-form [name="phone"]',font+['borderRadius','borderColor'])])
     assert not errors,(width,route,'form',errors)
     await page.keyboard.press('Escape')
    rows.append({'page':route,'viewport':width,'nativeStylesMatch':True,**dimensions})
  print(json.dumps({'passed':True,'cases':rows,'compared':['native container dimensions','page and section heading typography','body typography','breadcrumb links/current item/separator','primary and secondary button palette','form field typography and border','horizontal overflow']},ensure_ascii=False,indent=2))
  await browser.close()
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--browser');args=parser.parse_args();asyncio.run(run(args.browser))
