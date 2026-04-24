import time
import os
from playwright.sync_api import sync_playwright

from main import analizar_har

def ejecutar_pixels(url):

    import time
    import os
    from playwright.sync_api import sync_playwright
    from main import analizar_har

    har_path = f"temp_{int(time.time())}.har"

    with sync_playwright() as p:

        browser = p.chromium.launch(headless=True)

        context = browser.new_context(
            record_har_path=har_path
        )

        page = context.new_page()

        print("🌐 Capturando HAR:", url)

        try:
            # 🔥 CLAVE: NO esperar "load"
            page.goto(url, timeout=60000, wait_until="domcontentloaded")
        except:
            print("⚠️ Timeout controlado en goto (seguimos)")

        # 🍪 intentar cookies sin romper
        try:
            page.click("button:has-text('Aceptar')", timeout=3000)
            print("🍪 Cookies aceptadas")
        except:
            pass

        # 🔥 esperar tráfico real
        try:
            page.wait_for_load_state("networkidle", timeout=10000)
        except:
            pass

        # 🔥 tiempo de captura
        page.wait_for_timeout(15000)

        context.close()
        browser.close()

    if not os.path.exists(har_path):
        return {"error": "HAR no generado"}

    pixels = analizar_har(har_path)

    return {
        "url": url,
        "pixels": pixels
    }