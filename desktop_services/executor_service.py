import pyautogui
import time
import cv2
import numpy as np
import os
import Quartz
from skimage.metrics import structural_similarity as ssim

def get_scale_factor():
    try:
        main_display = Quartz.CGMainDisplayID()
        pixel_width = Quartz.CGDisplayPixelsWide(main_display)
        bounds = Quartz.CGDisplayBounds(main_display)
        logical_width = bounds.size.width

        scale = pixel_width / logical_width

        return scale
    except:
        return 1
DEBUG_DIR = "desktop_assets/debug"

if not os.path.exists(DEBUG_DIR):
    os.makedirs(DEBUG_DIR)

# -------------------------
# 🧠 EJECUTOR PRINCIPAL
# -------------------------
def ejecutar_flow(flow):

    print("🚀 Ejecutando flow...")
    time.sleep(2)  # margen para cambiar de ventana

    for i, step in enumerate(flow):

        print(f"\n➡️ Step {i+1}: {step.get('type')}")

        step_type = step.get("type")

        # -------------------------
        # CLICK POR COORDENADAS
        # -------------------------
        if step_type == "click":

            data = step.get("data", {})
            x = data.get("x")
            y = data.get("y")
            image = data.get("image")

            print(f"➡️ Step {i+1} → Click esperado en {x},{y}")

            # -------------------------
            # 🥇 1. IR A POSICIÓN (SIN CLICK)
            # -------------------------
            mover_mouse_humano(x, y)
            time.sleep(0.2)
            capturar_zona_debug(x, y, nombre="intento_local")
            # -------------------------
            # 🧠 2. CAPTURA LOCAL (MISMO TAMAÑO)
            # -------------------------
            match_local = comparar_zona_actual(x, y, image)

            print(f"🧪 MATCH LOCAL: {round(match_local * 100, 2)}%")

            # -------------------------
            # ✅ 3. SI COINCIDE → CLICK
            # -------------------------
            if match_local >= 0.5:
                print("✅ Coincide → click directo")
                pyautogui.click()
                continue

            # -------------------------
            # 🌍 4. FALLBACK → SCREENSHOT COMPLETO
            # -------------------------
            print("🌍 No coincide → captura global y búsqueda")

            pos = buscar_imagen_en_pantalla(image, threshold=0.7)

            if pos:
                gx, gy = pos

                print(f"🎯 Encontrado en pantalla en {gx},{gy}")

                mover_mouse_humano(gx, gy)
                time.sleep(0.3)
                capturar_zona_debug(gx, gy, nombre="intento_global")
                # -------------------------
                # 🧠 VALIDACIÓN FINAL
                # -------------------------
                match_final = comparar_zona_actual(gx, gy, image)

                print(f"🧪 MATCH FINAL: {round(match_final * 100, 2)}%")

                if match_final >= 0.5:
                    print("✅ Confirmación OK → click")
                    pyautogui.click()
                    continue
                else:
                    print("❌ Encontrado pero no coincide suficiente")
            else:
                print("❌ No encontrado en pantalla")

            # -------------------------
            # 🚨 ERROR
            # -------------------------
            print(f"🚨 ERROR: Step {i+1} no ejecutado")
            return

        # -------------------------
        # TECLADO
        # -------------------------
        elif step_type == "key":

            texto = step["data"]["key"]
            pyautogui.write(texto, interval=0.05)

        # -------------------------
        # meszcla coordenadas con visual
        # -------------------------            
        elif step_type == "smart_step":

            data = step.get("data", {})

            x = data.get("x")
            y = data.get("y")
            image = data.get("image")

            print(f"➡️ Smart step en {x},{y}")

            # 🥇 intento rápido
            mover_mouse_humano(x, y)
            pyautogui.click()
            time.sleep(0.5)

            # 🧠 comprobación ligera (opcional simple)
            print("🔍 Intentando fallback solo si necesario...")

            ok = buscar_y_click(image, threshold=0.9, reintentos=2)

            if ok:
                print("⚠️ Se usó fallback visual")
            else:
                print("✅ Click directo válido")
        # -------------------------
        # CLICK POR IMAGEN (legacy)
        # -------------------------
        elif step_type == "click_image":

            ruta = step["data"]["image"]

            ok = buscar_y_click(ruta)

            if not ok:
                print("⚠️ No se pudo hacer click en imagen")

        # -------------------------
        # 🧠 NUEVO → VISION STEP
        # -------------------------
        elif step_type == "vision_step":

            ruta = step.get("image")
            prompt = step.get("prompt", "")

            print(f"🧠 Prompt: {prompt}")

            ok = buscar_y_click(ruta)

            if not ok:
                print("❌ No encontrado tras reintentos")

        else:
            print("❌ Tipo no soportado:", step_type)

        time.sleep(1)


# -------------------------
# 🔍 BUSCAR IMAGEN + CLICK
# -------------------------
def comparar_zona_actual(x, y, template_path, size=120):

    scale = get_scale_factor()

    x = int(x * scale)
    y = int(y * scale)
    size = int(size * scale)

    screenshot = pyautogui.screenshot()
    screenshot = np.array(screenshot)

    h_screen, w_screen = screenshot.shape[:2]

    left = int(max(x - size//2, 0))
    top = int(max(y - size//2, 0))
    right = int(min(x + size//2, w_screen))
    bottom = int(min(y + size//2, h_screen))

    if left >= right or top >= bottom:
        print("❌ Zona fuera de pantalla")
        return 0

    crop = screenshot[top:bottom, left:right]

    template = cv2.imread(template_path)

    if template is None:
        print("❌ Template no encontrado:", template_path)
        return 0

    # 🔧 ajustar tamaño SOLO manteniendo proporción
    try:
        template = cv2.resize(template, (crop.shape[1], crop.shape[0]))
    except Exception as e:
        print("❌ Error resize:", e)
        return 0

    # 🧠 pasar a gris
    crop_gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)

    # 🔥 SSIM (clave)
    score, _ = ssim(crop_gray, template_gray, full=True)

    porcentaje = round(score * 100, 2)
    print(f"🧠 MATCH LOCAL (SSIM): {porcentaje}%")

    # 🧪 debug visual
    try:
        combined = np.hstack((crop, template))
        debug_path = os.path.join(DEBUG_DIR, f"compare_{int(time.time())}.png")
        cv2.imwrite(debug_path, combined)
        print(f"🧪 Debug comparación: {debug_path}")
    except:
        pass

    return score


def buscar_y_click(ruta_imagen, threshold=0.8, reintentos=3):

    for intento in range(reintentos):

        print(f"🌍 Búsqueda global intento {intento+1}")

        screenshot = pyautogui.screenshot()
        screenshot = np.array(screenshot)

        screenshot_gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)

        template = cv2.imread(ruta_imagen)

        if template is None:
            print("❌ Imagen no encontrada:", ruta_imagen)
            return False

        template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)

        result = cv2.matchTemplate(screenshot_gray, template_gray, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)

        print("📊 MATCH GLOBAL:", round(max_val, 3))

        if max_val >= threshold:

            h, w = template_gray.shape[:2]

            x = max_loc[0] + w // 2
            y = max_loc[1] + h // 2

            mover_mouse_humano(x, y)
            pyautogui.click()

            print(f"✅ Click global en {x},{y}")

            return True

        time.sleep(0.5)

    return False

def buscar_imagen_en_pantalla(ruta_imagen, threshold=0.8):

    screenshot = pyautogui.screenshot()
    screenshot_np = np.array(screenshot)
    screenshot_cv = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)

    template = cv2.imread(ruta_imagen)

    if template is None:
        print("❌ Imagen no encontrada:", ruta_imagen)
        return None

    result = cv2.matchTemplate(screenshot_cv, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)

    print("📊 MATCH GLOBAL:", round(max_val, 3))

    h, w = template.shape[:2]

    # 🎯 dibujar resultado
    debug_img = screenshot_cv.copy()
    cv2.rectangle(debug_img, max_loc, (max_loc[0]+w, max_loc[1]+h), (0,255,0), 2)

    debug_path = os.path.join(DEBUG_DIR, f"global_{int(time.time())}.png")
    cv2.imwrite(debug_path, debug_img)

    print(f"🖼️ DEBUG GLOBAL guardado en: {debug_path}")

    if max_val >= threshold:
        x = max_loc[0] + w // 2
        y = max_loc[1] + h // 2
        return (x, y)

    return None


# -------------------------
# 🖱️ MOVIMIENTO HUMANO
# -------------------------
def mover_mouse_humano(x, y):

    current_x, current_y = pyautogui.position()

    pasos = 20

    for i in range(pasos):
        t = i / pasos

        new_x = current_x + (x - current_x) * t
        new_y = current_y + (y - current_y) * t

        pyautogui.moveTo(new_x, new_y)
        time.sleep(0.01)

def capturar_zona_debug(x, y, size=60, nombre="local"):

    scale = get_scale_factor()

    x = int(x * scale)
    y = int(y * scale)
    size = int(size * scale)

    screenshot = pyautogui.screenshot()

    left = max(x - size//2, 0)
    top = max(y - size//2, 0)
    width, height = screenshot.size

    right = min(left + size, width)
    bottom = min(top + size, height)
    if left >= right or top >= bottom:
        print("❌ DEBUG fuera de pantalla")
        return None
    crop = screenshot.crop((left, top, right, bottom))

    path = os.path.join(DEBUG_DIR, f"{nombre}_{int(time.time())}.png")
    crop.save(path)

    print(f"📸 DEBUG LOCAL guardado en: {path}")

    return path       