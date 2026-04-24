from bs4 import BeautifulSoup
from ia_services.llm_service import llamar_ia


def extraer_info_web(html, opciones):

    soup = BeautifulSoup(html, "html.parser")

    data = {}

    # -------------------------
    # UTIL: limpiar texto
    # -------------------------
    def get_text_clean():
        return " ".join(soup.get_text().split())[:2000]

    # -------------------------
    # TITLE
    # -------------------------
    if opciones.get("title") or opciones.get("titular"):
        data["title"] = (
            soup.title.string.strip()
            if soup.title and soup.title.string
            else ""
        )

    # -------------------------
    # META
    # -------------------------
    if opciones.get("meta"):
        metas = []
        for m in soup.find_all("meta"):
            metas.append({
                "name": m.get("name"),
                "content": m.get("content")
            })
        data["meta"] = metas

    # -------------------------
    # KEYWORDS (IA)
    # -------------------------
    if opciones.get("keywords"):
        texto = get_text_clean()
        data["keywords"] = llamar_ia(f"Saca palabras clave:\n{texto}")

    # -------------------------
    # RESUMEN IA
    # -------------------------
    if opciones.get("resumen"):
        texto = get_text_clean()
        data["resumen"] = llamar_ia(f"Resume esta página:\n{texto}")

    # -------------------------
    # SCHEMA
    # -------------------------
    if opciones.get("schema"):
        schemas = []
        for s in soup.find_all("script", type="application/ld+json"):
            if s.string:
                schemas.append(s.string)
        data["schema"] = schemas

    # -------------------------
    # IMÁGENES
    # -------------------------
    if opciones.get("imagenes"):
        imgs = []
        for img in soup.find_all("img"):
            src = img.get("src")
            if src:
                imgs.append(src)
        data["imagenes"] = imgs[:10]

    # -------------------------
    # VIDEOS
    # -------------------------
    if opciones.get("videos"):
        videos = []
        for v in soup.find_all("video"):
            src = v.get("src")
            if src:
                videos.append(src)
        data["videos"] = videos

    # -------------------------
    # SEO + SCORING
    # -------------------------
    if opciones.get("seo"):

        score = 100
        errores = []

        title = soup.title.string.strip() if soup.title and soup.title.string else ""

        if not title:
            score -= 20
            errores.append("Falta title")

        if len(title) > 65:
            score -= 5
            errores.append("Title demasiado largo")

        meta_desc = soup.find("meta", attrs={"name": "description"})
        if not meta_desc:
            score -= 20
            errores.append("Falta meta description")

        canonical = soup.find("link", rel="canonical")
        if not canonical:
            score -= 10
            errores.append("Falta canonical")

        robots = soup.find("meta", attrs={"name": "robots"})
        if robots and "noindex" in (robots.get("content") or "").lower():
            score -= 50
            errores.append("Página en noindex")

        og_tags = soup.find_all("meta", property=lambda x: x and "og:" in x)
        if not og_tags:
            score -= 5
            errores.append("Sin Open Graph")

        if not soup.find("h1"):
            score -= 10
            errores.append("Sin H1")

        if len(soup.find_all("h2")) < 1:
            score -= 5
            errores.append("Sin H2")

        texto = soup.get_text()
        if len(texto.strip()) < 500:
            score -= 20
            errores.append("Contenido pobre")

        imagenes = soup.find_all("img")
        sin_alt = [img for img in imagenes if not img.get("alt")]

        if sin_alt:
            score -= 10
            errores.append(f"{len(sin_alt)} imágenes sin ALT")

        hreflang = soup.find_all("link", rel="alternate")
        if not any("hreflang" in str(x) for x in hreflang):
            score -= 5
            errores.append("Sin hreflang")

        enlaces = soup.find_all("a", href=True)
        internos = [a for a in enlaces if "/" in a["href"]]

        if len(internos) < 5:
            score -= 5
            errores.append("Pocos enlaces internos")

        palabras = texto.lower().split()
        data["top_keywords"] = list(set(palabras))[:10]

        data["score"] = max(score, 0)
        data["errores_seo"] = errores

    return data