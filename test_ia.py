import requests
import json

# -----------------------------
# INPUT (simula un correo real)
# -----------------------------
correo = "Hola, te envío el pedido. Cliente: Juan"

# -----------------------------
# 1. CLASIFICACIÓN (SIN IA)
# -----------------------------
if "pedido" in correo.lower():
    tipo = "pedido"
else:
    tipo = "otro"

# -----------------------------
# 2. LLAMADA A LA IA (SOLO DATOS + RESPUESTA)
# -----------------------------
url = "http://localhost:11434/api/generate"

prompt = f"""
Analiza el siguiente correo.

Tu tarea:
1. Detectar qué datos faltan
2. Generar una respuesta profesional solicitando esos datos

Datos obligatorios:
- numero_pedido (ej: 12345, pedido 001)
- fecha_entrega (ej: mañana, 12/03/2026)

Reglas:
- Si el dato no aparece claramente → falta
- NO inventar datos
- SIEMPRE generar respuesta

Devuelve SOLO JSON válido:

{{
  "faltan_datos": [],
  "respuesta": ""
}}

Correo:
{correo}
"""

response = requests.post(url, json={
    "model": "llama3",
    "prompt": prompt,
    "stream": False
})

texto = response.json()["response"]

# -----------------------------
# 3. LIMPIAR RESPUESTA (IMPORTANTE)
# -----------------------------
# A veces el modelo mete texto extra → limpiamos
inicio = texto.find("{")
fin = texto.rfind("}") + 1
json_limpio = texto[inicio:fin]

try:
    data = json.loads(json_limpio)
except:
    print("❌ Error parseando JSON:")
    print(texto)
    exit()

# -----------------------------
# 4. RESULTADO FINAL
# -----------------------------
resultado = {
    "tipo": tipo,
    "faltan_datos": data["faltan_datos"],
    "respuesta": data["respuesta"]
}

print("\n✅ RESULTADO FINAL:")
print(json.dumps(resultado, indent=2, ensure_ascii=False))

# -----------------------------
# 5. LÓGICA AUTOMÁTICA (SIMULACIÓN)
# -----------------------------
if resultado["faltan_datos"]:
    print("\n📩 ACCIÓN: Enviar email solicitando datos")
else:
    print("\n✅ ACCIÓN: Procesar pedido automáticamente")