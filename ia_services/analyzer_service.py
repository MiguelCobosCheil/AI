import os
from PIL import Image

from ia_services.image_service import analizar_imagen_llava

# -----------------------------
# EXTENSIONES
# -----------------------------
EXTENSIONES_IMAGEN = [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".tiff"]
EXTENSIONES_DOC = [".pdf", ".docx", ".xlsx", ".csv", ".pptx", ".txt"]


# -----------------------------
# ANALIZADOR PRINCIPAL
# -----------------------------
def analizar_archivos(ruta_base, opciones, procesar_doc, resumir_doc):

    resultado = {
        "total_archivos": 0,
        "imagenes": [],
        "documentos": [],
        "busqueda": [],
        "comparacion": ""
    }

    include_sub = opciones.get("include_subfolders", True)

    for root, dirs, files in os.walk(ruta_base):

        if not include_sub:
            dirs.clear()

        for file in files:

            ruta = os.path.join(root, file)
            resultado["total_archivos"] += 1

            # -------------------------
            # IMÁGENES
            # -------------------------
            if any(file.lower().endswith(ext) for ext in EXTENSIONES_IMAGEN):

                info = {"nombre": file, "ruta": ruta}

                if opciones.get("peso"):
                    info["peso_kb"] = round(os.path.getsize(ruta) / 1024, 2)

                if opciones.get("dimensiones"):
                    try:
                        img = Image.open(ruta)
                        info["dimensiones"] = f"{img.size[0]}x{img.size[1]}"
                    except:
                        pass

                if opciones.get("descripcion"):
                    desc = analizar_imagen_llava(ruta, contexto=file)
                    info["descripcion"] = desc

                    # 🔍 búsqueda imagen
                    if opciones.get("buscar_imagen"):
                        if opciones["buscar_imagen"].lower() in desc.lower():
                            resultado["busqueda"].append(info)

                resultado["imagenes"].append(info)

            # -------------------------
            # DOCUMENTOS
            # -------------------------
            elif any(file.lower().endswith(ext) for ext in EXTENSIONES_DOC):

                texto = procesar_doc(ruta)
                resumen = resumir_doc(texto)

                doc = {
                    "nombre": file,
                    "ruta": ruta,
                    "resumen": resumen
                }

                # 🔍 búsqueda texto
                if opciones.get("buscar_texto"):
                    if opciones["buscar_texto"].lower() in texto.lower():
                        resultado["busqueda"].append(doc)

                resultado["documentos"].append(doc)

    return resultado