import os
import json
from datetime import datetime

REGLAS_FILE = "ia_rules/reglas.json"

# -----------------------------
# CARGAR / GUARDAR
# -----------------------------
def cargar_reglas():
    if not os.path.exists(REGLAS_FILE):
        return []

    with open(REGLAS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def guardar_reglas(data):
    with open(REGLAS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# -----------------------------
# CREAR REGLA
# -----------------------------
def crear_regla(nombre, prompt_base, documentos=[], imagenes=[]):

    reglas = cargar_reglas()

    regla = {
        "id": str(datetime.now().timestamp()),
        "nombre": nombre,
        "prompt_base": prompt_base,
        "documentos": documentos,
        "imagenes": imagenes
    }

    reglas.append(regla)
    guardar_reglas(reglas)

    return regla


# -----------------------------
# OBTENER REGLA
# -----------------------------
def obtener_regla(regla_id):
    reglas = cargar_reglas()
    return next((r for r in reglas if r["id"] == regla_id), None)


# -----------------------------
# GENERAR CONTEXTO
# -----------------------------
def generar_contexto_regla(regla):

    if not regla:
        return ""

    contexto = ""

    # -------------------------
    # 🧠 INSTRUCCIONES BASE
    # -------------------------
    if regla.get("prompt_base"):
        contexto += f"""
INSTRUCCIONES:
{regla['prompt_base']}
"""

    # -------------------------
    # 📄 EJEMPLOS DE DOCUMENTOS
    # -------------------------
    if regla.get("documentos"):
        contexto += "\nEJEMPLOS DE DOCUMENTOS CORRECTOS:\n"

        for doc in regla["documentos"][:3]:
            contexto += f"\n---\n{doc[:1000]}\n"

    # -------------------------
    # 🖼️ EJEMPLOS DE IMÁGENES
    # -------------------------
    if regla.get("imagenes"):
        contexto += "\nEJEMPLOS VISUALES (DESCRIPCIONES):\n"

        for img in regla["imagenes"][:3]:
            contexto += f"\n- {img}\n"

    # -------------------------
    # 🔥 FEEDBACK (APRENDIZAJE REAL)
    # -------------------------
    if regla.get("feedback"):

        contexto += "\nAPRENDIZAJE PREVIO:\n"

        for f in regla["feedback"][-5:]:

            if f.get("correcto"):
                contexto += f"""
✔ CASO CORRECTO:
Entrada:
{f.get("input")[:500]}

"""
            else:
                contexto += f"""
❌ CASO INCORRECTO:
Entrada:
{f.get("input")[:500]}

Motivo del error:
{f.get("comentario")}

"""

    # -------------------------
    # 🎯 INSTRUCCIÓN FINAL CLAVE
    # -------------------------
    contexto += """

REGLA FINAL:
Debes evaluar si el contenido cumple las instrucciones.
Responde siempre en formato JSON válido.
"""

    return contexto

def evaluar_con_regla(regla, contenido):

    contexto = generar_contexto_regla(regla)

    prompt = f"""
{contexto}

TAREA:
Evalúa si el siguiente contenido cumple las reglas.

CONTENIDO:
{contenido}

Responde en JSON:
{{
  "ok": true/false,
  "motivo": "explicación clara"
}}
"""

    return prompt