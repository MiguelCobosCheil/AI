import requests
import base64
import os


def analizar_imagen_llava(ruta_imagen, contexto=""):

    try:
        # 🔥 leer imagen
        with open(ruta_imagen, "rb") as f:
            imagen_base64 = base64.b64encode(f.read()).decode()

        # 🔥 prompt potente (clave)
        prompt = f"""
Describe esta imagen en UNA frase clara.

Contexto:
{contexto}

Reglas:
- Máx 12 palabras
- Sé específico (ej: "palacio histórico", "factura", "gráfico de barras")
- No digas "imagen de"
- Usa el contexto si ayuda

Respuesta:
"""

        r = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llava",
                "prompt": prompt,
                "images": [imagen_base64],
                "stream": False
            }
        )

        respuesta = r.json().get("response", "").strip()

        if not respuesta:
            return "imagen no identificada"

        return respuesta

    except Exception as e:
        return f"error analizando imagen: {str(e)}"