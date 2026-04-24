from playwright.sync_api import sync_playwright
from main import extraer_info_web

def ejecutar_analyze(urls, opciones):

    resultados = []

    with sync_playwright() as p:

        browser = p.chromium.launch(headless=True)

        for url in urls:

            try:
                page = browser.new_page()

                page.goto(url, timeout=60000)

                try:
                    page.wait_for_load_state("domcontentloaded", timeout=15000)
                except:
                    pass

                page.wait_for_timeout(3000)

                html = page.content()

                info = extraer_info_web(html, opciones)

                resultados.append({
                    "url": url,
                    "data": info,
                    "score": info.get("score")
                })

                page.close()

            except Exception as e:
                resultados.append({
                    "url": url,
                    "data": {},
                    "error": str(e)
                })

        browser.close()

    return resultados