import requests

def llamar_ia(prompt, temperature=0):

    try:
        print("🧠 PROMPT:", prompt[:300])

        r = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3",
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature
                }
            },
            timeout=60
        )

        if r.status_code != 200:
            print("❌ ERROR HTTP:", r.status_code, r.text)
            return ""

        data = r.json()

        if "response" not in data:
            print("❌ RESPUESTA IA INVÁLIDA:", data)
            return ""

        return data["response"].strip()

    except Exception as e:
        print(f"❌ ERROR IA: {e}")
        return ""
    
import json

def llamar_ia_json(prompt, temperature=0):

    texto = llamar_ia(prompt, temperature)

    try:
        return json.loads(texto)
    except:
        print("❌ JSON inválido:", texto[:500])
        return {}
   
def llamar_ia_json_safe(prompt, temperature=0):

    texto = llamar_ia(prompt, temperature)

    if not texto:
        return {}

    # intento normal
    try:
        return json.loads(texto)
    except:
        pass

    # limpiar markdown típico
    try:
        limpio = texto.replace("```json", "").replace("```", "").strip()
        return json.loads(limpio)
    except:
        pass

    # extraer bloque JSON
    try:
        import re

        match = re.search(r"\{.*\}|\[.*\]", texto, re.DOTALL)

        if match:
            return json.loads(match.group(0))

    except Exception as e:
        print("❌ ERROR parsing avanzado:", e)

    print("⚠️ JSON inválido (safe):", texto[:500])
    return {}   


def planificar_steps(prompt):

    instrucciones = f"""
Eres un agente que automatiza navegación web.

Convierte la tarea en pasos JSON.

TIPOS:
- goto
- click
- form
- extract_ai

REGLAS:
- Usa selectores CSS válidos
- Para Google usa textarea[name="q"]
- Para resultados usa #search
- NO expliques nada
- SOLO JSON válido
- NO inventes tipos nuevos

FORMATO:
[
  {{ "type": "goto", "url": "..." }},
  ...
]

TAREA:
{prompt}
"""

    steps = llamar_ia_json_safe(instrucciones)

    # 🔥 VALIDACIÓN CLAVE
    if not isinstance(steps, list):
        print("❌ IA no devolvió lista")
        return []

    steps_validos = []

    tipos_validos = ["goto", "click", "form", "extract_ai"]

    for s in steps:

        if not isinstance(s, dict):
            continue

        if s.get("type") not in tipos_validos:
            continue

        steps_validos.append(s)

    return steps_validos