from pynput import mouse

def on_click(x, y, button, pressed):
    print("CLICK:", x, y, button, pressed)

print("Escuchando...")

with mouse.Listener(on_click=on_click) as listener:
    listener.join()