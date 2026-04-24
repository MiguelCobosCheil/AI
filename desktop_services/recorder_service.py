from pynput import mouse
from pynput.mouse import Button
import time
import pyautogui
import os

print("🔥 recorder_service cargado")

listener_global = None
last_click_time = 0

ASSETS_DIR = "desktop_assets"

recording = []
start_time = None

mouse_down = False
start_pos = None


# -------------------------
# 🎥 INICIAR GRABACIÓN
# -------------------------
def start_recording():
    print("🚀 START RECORDING")

    global recording, start_time, mouse_down, start_pos, listener_global

    recording.clear()
    start_time = time.time()
    mouse_down = False
    start_pos = None

    def on_click(x, y, button, pressed):

        print("🖱️ CLICK:", x, y, button, pressed)

        global mouse_down, start_pos

        if button == Button.left:
            button_type = "left"
        elif button == Button.right:
            button_type = "right"
        else:
            button_type = "middle"

        # ❌ ELIMINADO FILTRO PANEL (MUY IMPORTANTE)

        if pressed:
            mouse_down = True
            start_pos = (x, y)

        else:
            mouse_down = False
            end_pos = (x, y)

            if start_pos and distancia(start_pos, end_pos) < 5:
                guardar_click(x, y, button_type)
            else:
                guardar_drag(start_pos, end_pos)

    def on_scroll(x, y, dx, dy):
        global recording

        step = {
            "time": time.time() - start_time,
            "type": "scroll",
            "data": {
                "x": x,
                "y": y,
                "dx": dx,
                "dy": dy,
                "prompt": ""
            }
        }

        recording.append(step)

    from pynput import keyboard

    def on_press(key):
        global recording

        try:
            k = key.char
        except:
            k = str(key)

        step = {
            "time": time.time() - start_time,
            "type": "key",
            "data": {
                "key": k,
                "prompt": ""
            }
        }

        recording.append(step)

    mouse_listener = mouse.Listener(
        on_click=on_click,
        on_scroll=on_scroll
    )

    keyboard_listener = keyboard.Listener(
        on_press=on_press
    )

    mouse_listener.start()
    keyboard_listener.start()

    listener_global = (mouse_listener, keyboard_listener)

    return listener_global


# -------------------------
# ⏹️ PARAR
# -------------------------
def stop_recording(listener):

    mouse_listener, keyboard_listener = listener

    mouse_listener.stop()
    keyboard_listener.stop()

    print("⏹️ Grabación terminada")

    return recording


# -------------------------
# 🖱️ CLICK
# -------------------------
def guardar_click(x, y, button_type="left"):

    global last_click_time, recording

    now = time.time()
    is_double = (now - last_click_time) < 0.3
    last_click_time = now

    tipo = "double_click" if is_double else "click"

    img = capturar_region(x, y)

    print(f"🎯 CLICK ORIGINAL: {x},{y}")

    step = {
        "time": time.time() - start_time,
        "type": tipo,
        "data": {
            "x": x,
            "y": y,
            "button": button_type,
            "image": img,
            "prompt": ""
        }
    }

    recording.append(step)

    print(f"📌 {tipo.upper()}:", step)


# -------------------------
# 🖱️ DRAG
# -------------------------
def guardar_drag(start, end):

    global recording

    img = capturar_region(end[0], end[1])

    step = {
        "time": time.time() - start_time,
        "type": "drag",
        "data": {
            "start": start,
            "end": end,
            "image": img,
            "prompt": ""
        }
    }

    recording.append(step)


# -------------------------
# 📸 CAPTURA CORRECTA (RETINA FIX)
# -------------------------
def capturar_region(x, y, size=80):

    if not os.path.exists(ASSETS_DIR):
        os.makedirs(ASSETS_DIR)

    screenshot = pyautogui.screenshot()

    screen_width, screen_height = pyautogui.size()
    img_width, img_height = screenshot.size

    scale_x = img_width / screen_width
    scale_y = img_height / screen_height

    print(f"🧠 SCREEN: {screen_width}x{screen_height}")
    print(f"🧠 IMG: {img_width}x{img_height}")
    print(f"🧠 SCALE: {scale_x}, {scale_y}")

    x_scaled = int(x * scale_x)
    y_scaled = int(y * scale_y)

    print(f"🎯 ESCALADO: {x_scaled},{y_scaled}")

    # -------------------------
    # recorte seguro con transparencia
    # -------------------------
    from PIL import Image

    left = x_scaled - size // 2
    top = y_scaled - size // 2
    right = x_scaled + size // 2
    bottom = y_scaled + size // 2

    crop = Image.new("RGBA", (size, size), (0, 0, 0, 0))

    valid_left = max(left, 0)
    valid_top = max(top, 0)
    valid_right = min(right, img_width)
    valid_bottom = min(bottom, img_height)

    if valid_right > valid_left and valid_bottom > valid_top:

        region = screenshot.crop((valid_left, valid_top, valid_right, valid_bottom))

        paste_x = valid_left - left
        paste_y = valid_top - top

        crop.paste(region, (paste_x, paste_y))

    filename = f"step_{int(time.time())}.png"
    path = os.path.join(ASSETS_DIR, filename)

    crop.save(path)

    print(f"📸 CAPTURA FINAL en: {x_scaled},{y_scaled}")

    return path


# -------------------------
# 🧮 DISTANCIA
# -------------------------
def distancia(a, b):
    return ((a[0]-b[0])**2 + (a[1]-b[1])**2) ** 0.5