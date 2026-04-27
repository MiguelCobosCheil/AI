import pyautogui
import time
import cv2
import numpy as np
import os
import Quartz
from skimage.metrics import structural_similarity as ssim


DEBUG_DIR = "desktop_assets/debug"

if not os.path.exists(DEBUG_DIR):
    os.makedirs(DEBUG_DIR)



def to_pixels(x, y):
    scale = get_scale_factor()
    return int(x * scale), int(y * scale)

def to_logical(x, y):
    scale = get_scale_factor()
    return int(x / scale), int(y / scale)

def get_scale_factor():
    try:
        screenshot_w, screenshot_h = pyautogui.screenshot().size
        screen_w, screen_h = pyautogui.size()

        scale_x = screenshot_w / screen_w
        scale_y = screenshot_h / screen_h

        scale = (scale_x + scale_y) / 2

        print(f"🧠 SCALE DINÁMICO: {scale}")

        return scale

    except Exception as e:
        print("❌ ERROR SCALE:", e)
        return 1

def get_real_size(base_size):
    scale = get_scale_factor()
    return int(base_size * scale)

# -------------------------
# 🧠 EJECUTOR PRINCIPAL
# -------------------------
def ejecutar_flow(flow):

    print("🚀 Ejecutando flow...")
    print("⏳ Esperando interacción real del sistema...")

    esperar_raton_estable()

    print("✅ Sistema listo")

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

            # 🧠 esperar a que el ratón termine realmente
            esperar_raton_estable()
            print("📸 CAPTURA TRAS MOVIMIENTO COMPLETO (LOCAL)",x, y)
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

                esperar_raton_estable()
                print("📸 CAPTURA TRAS MOVIMIENTO COMPLETO (GLOBAL)",gx, gy)
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
            esperar_raton_estable()

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

    screenshot = pyautogui.screenshot()
    screenshot = np.array(screenshot)

    h_screen, w_screen = screenshot.shape[:2]

    # 🔥 posición ya escalada correctamente
    x_px, y_px = to_pixels(x, y)

    template = cv2.imread(template_path)

    if template is None:
        print("❌ Template no encontrado:", template_path)
        return 0

    # 🔥 IMPORTANTE: usar tamaño ORIGINAL (NO escalar)
    th, tw = template.shape[:2]
    print(f"🧠 TEMPLATE REAL: {tw}x{th}")

    # 🔥 usar tamaño real del template (80x80 normalmente)
    left = int(max(x_px - tw // 2, 0))
    top = int(max(y_px - th // 2, 0))
    right = int(min(x_px + tw // 2, w_screen))
    bottom = int(min(y_px + th // 2, h_screen))

    if left >= right or top >= bottom:
        print("❌ Zona fuera de pantalla")
        return 0

    crop = screenshot[top:bottom, left:right]

    ch, cw = crop.shape[:2]

    print(f"🧠 CROP SIZE: {cw}x{ch}")

    # 🔥 ajustar template SOLO si hace falta
    if (ch, cw) != (th, tw):
        template = cv2.resize(template, (cw, ch))

    # 🧠 gris
    crop_gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)

    # 🔥 SSIM
    try:
        score, _ = ssim(crop_gray, template_gray, full=True)
    except Exception as e:
        print("❌ ERROR SSIM:", e)
        return 0

    porcentaje = round(score * 100, 2)
    print(f"🧠 MATCH LOCAL (SSIM): {porcentaje}%")

    # 🧪 debug
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

            scale = get_scale_factor()

            x = int((max_loc[0] + w // 2) / scale)
            y = int((max_loc[1] + h // 2) / scale)

            mover_mouse_humano(x, y)
            pyautogui.click()

            print(f"✅ Click global en {x},{y}")

            return True

        esperar_raton_estable()

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
        x_px = max_loc[0] + w // 2
        y_px = max_loc[1] + h // 2

        x, y = to_logical(x_px, y_px)

        return (x, y)

    return None


# -------------------------
# 🖱️ MOVIMIENTO HUMANO
# -------------------------
def mover_mouse_humano(x, y):

    start_x, start_y = pyautogui.position()

    print("\n🟢 INICIO MOVIMIENTO RATÓN")
    print(f"📍 Desde: {start_x}, {start_y}")
    print(f"🎯 Hacia: {x}, {y}")

    pasos = 20

    for i in range(pasos):
        t = i / pasos

        new_x = start_x + (x - start_x) * t
        new_y = start_y + (y - start_y) * t

        pyautogui.moveTo(int(new_x), int(new_y))
        time.sleep(0.01)

    # 🔥 mover EXACTO al destino (clave)
    pyautogui.moveTo(int(x), int(y))

    # 🔥 forzar precisión (por si el sistema se queda corto)
    real_x, real_y = pyautogui.position()

    if abs(real_x - x) > 2 or abs(real_y - y) > 2:
        print("⚠️ Ajuste final necesario")
        pyautogui.moveTo(int(x), int(y))

    final_x, final_y = pyautogui.position()

    print(f"🏁 FIN MOVIMIENTO RATÓN en: {final_x}, {final_y}")
    print("🟢 FIN MOVIMIENTO\n")


def esperar_raton_estable(max_checks=10, delay=0.01):

    print("⏳ Esperando estabilidad del ratón...")

    estable_count = 0
    prev_x, prev_y = pyautogui.position()

    for i in range(50):

        time.sleep(delay)
        x, y = pyautogui.position()

        print(f"🔍 Check {i}: {x},{y}")

        if abs(x - prev_x) < 1 and abs(y - prev_y) < 1:
            estable_count += 1
        else:
            estable_count = 0

        if estable_count >= max_checks:
            print(f"✅ Ratón estable en: {x},{y}")
            return True

        prev_x, prev_y = x, y

    print("⚠️ No se detectó estabilidad")
    return False

def capturar_zona_debug(x, y, size=60, nombre="local"):

    print("\n================ DEBUG CAPTURA ================")

    # 🧠 escala detectada
    scale = get_scale_factor()
    print(f"🧠 SCALE FACTOR: {scale}")

    # 🖱️ posición real del ratón
    mouse_x, mouse_y = pyautogui.position()
    print(f"🖱️ RATÓN REAL: {mouse_x}, {mouse_y}")

    # 📍 coordenadas del step
    print(f"📍 STEP (x,y): {x}, {y}")

    # 🔄 usar SIEMPRE la posición real del ratón
    x_px, y_px = to_pixels(mouse_x, mouse_y)
    print(f"🎯 USANDO RATÓN REAL en píxeles: {x_px}, {y_px}")

    # ⏳ CLAVE → esperar a que el frame de pantalla se actualice
    time.sleep(0.2)

    # 📸 screenshot
    screenshot = pyautogui.screenshot()
    width, height = screenshot.size
    print(f"🖥️ SCREENSHOT SIZE: {width}x{height}")

    size_px = get_real_size(80)
    print(f"📐 SIZE px: {size_px}")

    # 📦 bounding box
    left = max(x_px - size_px // 2, 0)
    top = max(y_px - size_px // 2, 0)
    right = min(x_px + size_px // 2, width)
    bottom = min(y_px + size_px // 2, height)

    print(f"📦 BOX: left={left}, top={top}, right={right}, bottom={bottom}")

    # 🚨 validación
    if left >= right or top >= bottom:
        print("❌ ERROR: bounding box inválido")
        return None

    # ✂️ recorte
    crop = screenshot.crop((left, top, right, bottom))

    # 📊 info
    crop_w, crop_h = crop.size
    print(f"✂️ CROP SIZE: {crop_w}x{crop_h}")

    # 🧪 contenido real
    crop_np = np.array(crop)
    mean_pixel = crop_np.mean()
    print(f"🧪 MEDIA PIXEL: {round(mean_pixel, 2)}")

    if mean_pixel > 240:
        print("⚠️ POSIBLE CAPTURA BLANCA")
    elif mean_pixel < 10:
        print("⚠️ POSIBLE CAPTURA NEGRA")
    else:
        print("✅ CAPTURA CON CONTENIDO")

    # 💾 guardar
    path = os.path.join(DEBUG_DIR, f"{nombre}_{int(time.time())}.png")
    crop.save(path)

    print(f"💾 GUARDADO EN: {path}")
    print("==============================================\n")

    return path