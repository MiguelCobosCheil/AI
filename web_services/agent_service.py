from playwright.sync_api import sync_playwright
import random
import math
import json
import os

FLOWS_FILE = "flows.json"

def extraer_info_web_wrapper(html, opciones):
    from main import extraer_info_web
    return extraer_info_web(html, opciones)

def guardar_flujo(nombre, flow):

    data = {}

    if os.path.exists(FLOWS_FILE):
        with open(FLOWS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

    data[nombre] = flow

    with open(FLOWS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def cargar_flujos():

    if not os.path.exists(FLOWS_FILE):
        return {}

    with open(FLOWS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def eliminar_flujo(nombre):

    if not os.path.exists(FLOWS_FILE):
        return

    with open(FLOWS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    if nombre in data:
        del data[nombre]

    with open(FLOWS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def mover_mouse_humano(page, locator):

    box = locator.bounding_box()
    if not box:
        return

    # 🎯 destino (NO centrado)
    target_x = box["x"] + random.uniform(0.2, 0.8) * box["width"]
    target_y = box["y"] + random.uniform(0.2, 0.8) * box["height"]

    # 🖱️ punto inicial (arriba-centro pantalla)
    viewport = page.viewport_size or {"width": 1280, "height": 800}
    start_x = viewport["width"] / 2
    start_y = random.uniform(0, 50)

    # 🎯 puntos de control (Bezier imperfecta)
    control_x1 = start_x + random.uniform(-200, 200)
    control_y1 = start_y + random.uniform(100, 300)

    control_x2 = target_x + random.uniform(-200, 200)
    control_y2 = target_y + random.uniform(-100, 100)

    # ⏱️ número de pasos (trayectoria)
    steps = random.randint(20, 40)

    for i in range(steps):
        t = i / steps

        # curva Bezier cúbica
        x = (
            (1 - t) ** 3 * start_x +
            3 * (1 - t) ** 2 * t * control_x1 +
            3 * (1 - t) * t ** 2 * control_x2 +
            t ** 3 * target_x
        )

        y = (
            (1 - t) ** 3 * start_y +
            3 * (1 - t) ** 2 * t * control_y1 +
            3 * (1 - t) * t ** 2 * control_y2 +
            t ** 3 * target_y
        )

        page.mouse.move(x, y)
        page.wait_for_timeout(random.randint(5, 20))

    # ❌ fallo humano (no acierta a la primera)
    if random.random() < 0.3:
        page.mouse.move(target_x + random.randint(-30, 30), target_y + random.randint(-30, 30))
        page.wait_for_timeout(random.randint(100, 300))

        # volver a corregir
        page.mouse.move(target_x, target_y)
        page.wait_for_timeout(random.randint(50, 150))


def ejecutar_agent(url, steps):

    resultados = []

    with sync_playwright() as p:

        page = None
        context = None

        try:
            print("🔌 Intentando conectar a Chrome real...")

            browser = p.chromium.connect_over_cdp("http://localhost:9222")

            context = browser.contexts[0]
            page = context.pages[0]

            print("✅ Conectado a Chrome real")

        except Exception as e:

            print("⚠️ No hay Chrome debug activo, lanzando uno nuevo...")

            context = p.chromium.launch_persistent_context(
                user_data_dir="playwright_profile",
                channel="chrome",
                headless=False,
                args=["--start-maximized"],
                viewport={"width": 1366, "height": 768},
                locale="es-ES"
            )

            page = context.new_page()

            print("✅ Chrome lanzado por Playwright")

        # -------------------------
        # 🕵️ FINGERPRINT
        # -------------------------
        page.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        Object.defineProperty(navigator, 'languages', { get: () => ['es-ES', 'es'] });
        Object.defineProperty(navigator, 'plugins', { get: () => [1,2,3,4,5] });
        """)

        try:
            from playwright_stealth import stealth_sync
            stealth_sync(page)
        except:
            print("⚠️ stealth no activo")
            

        # -------------------------
        # 🔥 CAPTURAR CONSOLE.LOG
        # -------------------------
        logs = []

        def handle_console(msg):
            try:
                logs.append(msg.text)
            except:
                pass

        page.on("console", handle_console)

        # -------------------------
        # 🌐 IR A URL INICIAL
        # -------------------------
        if url:
            try:
                page.goto(url, timeout=60000)
                page.wait_for_load_state("domcontentloaded", timeout=15000)
            except:
                pass

        # -------------------------
        # 🔁 EJECUTAR PASOS
        # -------------------------
        for i, step in enumerate(steps):

            tipo = step.get("type")

            resultado_step = {
                "step": i + 1,
                "type": tipo,
                "ok": True
            }

            try:

                # -------------------------
                # 🌐 GOTO
                # -------------------------
                if tipo == "goto":

                    page.goto(step.get("url"), timeout=60000)

                    try:
                        page.wait_for_load_state("domcontentloaded", timeout=15000)
                    except:
                        pass

                    resultado_step["url"] = step.get("url")

                # -------------------------
                # CLICK
                # -------------------------
                elif tipo == "click":

                    selector = step.get("selector")

                    locator = page.locator(f"{selector}:visible").first

                    locator.wait_for(state="visible", timeout=10000)

                    mover_mouse_humano(page, locator)

                    page.wait_for_timeout(random.randint(100, 400))

                    locator.click(timeout=30000)

                    resultado_step["selector"] = selector

                # -------------------------
                # WAIT
                # -------------------------
                elif tipo == "wait":

                    tiempo = step.get("time", 1000)
                    page.wait_for_timeout(tiempo)

                    resultado_step["time"] = tiempo

                # -------------------------
                # FORMULARIO (🔥 HUMAN TYPING)
                # -------------------------
                elif tipo == "form":

                    print("FORM STEP DEBUG:", step)

                    selector = step.get("form", {}).get("selector")
                    value = step.get("form", {}).get("value")
                    input_type = step.get("form", {}).get("inputType")

                    page.wait_for_selector(selector, timeout=10000)

                    count = page.locator(selector).count()
                    print("ELEMENTS FOUND:", count)

                    locator = page.locator(selector).first

                    if input_type == "input":

                        # 🖱️ movimiento humano hacia el input
                        mover_mouse_humano(page, locator)

                        # ⏱️ pequeña pausa antes de interactuar
                        page.wait_for_timeout(random.randint(100, 300))

                        # ❌ pequeña imprecisión (no siempre acierta perfecto)
                        if random.random() < 0.2:
                            box = locator.bounding_box()
                            if box:
                                page.mouse.click(
                                    box["x"] + random.randint(-20, 20),
                                    box["y"] + random.randint(-20, 20)
                                )
                                page.wait_for_timeout(random.randint(100, 300))

                        # 🎯 click correcto
                        locator.click()

                        # limpiar campo
                        locator.fill("")

                        texto = value or ""

                        # ⌨️ escritura humana
                        for char in texto:
                            delay = random.randint(50, 180)
                            locator.type(char, delay=delay)

                            # pequeñas pausas humanas
                            if random.random() < 0.1:
                                page.wait_for_timeout(random.randint(100, 400))

                        # 🤔 pequeña pausa final (como humano pensando)
                        if random.random() < 0.3:
                            page.wait_for_timeout(random.randint(300, 800))

                    elif input_type == "checkbox":

                        mover_mouse_humano(page, locator)
                        page.wait_for_timeout(random.randint(100, 300))

                        if str(value).lower() == "true":
                            locator.check()
                        else:
                            locator.uncheck()

                    elif input_type == "radio":

                        mover_mouse_humano(page, locator)
                        page.wait_for_timeout(random.randint(100, 300))

                        locator.check()

                    elif input_type == "select":

                        mover_mouse_humano(page, locator)
                        page.wait_for_timeout(random.randint(100, 300))

                        locator.select_option(value)

                    resultado_step["selector"] = selector
                    resultado_step["value"] = value
                    resultado_step["input_type"] = input_type

                # -------------------------
                # EXTRACT
                # -------------------------
                elif tipo == "extract":

                    extract = step.get("extract", {})

                    selector = extract.get("selector")
                    tipo_extract = extract.get("type", "text")
                    attr = extract.get("attr")

                    locator = page.locator(selector).first

                    if tipo_extract == "html":
                        value = locator.inner_html()

                    elif tipo_extract == "attr":
                        attr_name = attr or "href"
                        value = locator.get_attribute(attr_name)

                    else:
                        value = locator.inner_text()

                    resultado_step["selector"] = selector
                    resultado_step["result"] = value

                # -------------------------
                # SCRIPT
                # -------------------------
                elif tipo == "script":

                    script = step.get("script", "")

                    logs.clear()

                    page.evaluate(script)

                    resultado_step["logs"] = logs.copy()
                # -------------------------
                # 🤖 EXTRACT IA
                # -------------------------
                elif tipo == "extract_ai":

                    prompt = step.get("prompt", "")

                    if not prompt:
                        raise Exception("Prompt vacío en extract_ai")

                    text = page.inner_text("body")

                    from ia_services.llm_service import llamar_ia

                    resultado = llamar_ia(f"""
                    Analiza esta página web.

                    TAREA:
                    {prompt}

                    CONTENIDO:
                    {text[:50000]}
                    """)

                    resultado_step["result"] = resultado
                # -------------------------
                # ANALYZE
                # -------------------------
                elif tipo == "analyze":

                    html = page.content()

                    info = extraer_info_web_wrapper(
                        html,
                        step.get("opciones", {})
                    )

                    resultado_step["result"] = info

                else:
                    resultado_step["ok"] = False
                    resultado_step["error"] = f"Tipo no soportado: {tipo}"

            except Exception as e:

                resultado_step["ok"] = False
                resultado_step["error"] = str(e)

                try:
                    screenshot_path = f"debug_step_{i+1}.png"
                    page.screenshot(path=screenshot_path, full_page=True)

                    html = page.content()
                    html_path = f"debug_step_{i+1}.html"

                    with open(html_path, "w", encoding="utf-8") as f:
                        f.write(html)

                    print(f"🧠 DEBUG GUARDADO → {screenshot_path}, {html_path}")

                except Exception as debug_error:
                    print("❌ Error guardando debug:", debug_error)

            # -------------------------
            # 📸 Screenshot por step
            # -------------------------
            try:
                screenshot_path = f"step_{i+1}.png"
                page.screenshot(path=screenshot_path, full_page=True)

                resultado_step["screenshot"] = screenshot_path

            except Exception as e:
                print("Error capturando screenshot:", e)

            resultados.append(resultado_step)

        context.close()

    return resultados

def ejecutar_agent_con_ia(prompt):

    from ia_services.llm_service import planificar_steps

    print("🧠 Generando pasos con IA...")

    steps = planificar_steps(prompt)

    if not steps:
        return {
            "ok": False,
            "error": "La IA no generó pasos válidos"
        }

    print("📋 STEPS:", steps)

    # detectar URL inicial
    url = None
    if steps and steps[0].get("type") == "goto":
        url = steps[0].get("url")

    resultados = ejecutar_agent(url, steps)

    return {
        "ok": True,
        "steps": steps,
        "resultados": resultados
    }