from bs4 import BeautifulSoup

def analizar_seo(soup):

    data = {}
    score = 100
    errores = []

    # -------------------------
    # TITLE
    # -------------------------
    title = soup.title.string.strip() if soup.title and soup.title.string else ""

    if not title:
        score -= 20
        errores.append("Falta title")

    if len(title) > 65:
        score -= 5
        errores.append("Title demasiado largo")

    # -------------------------
    # META DESCRIPTION
    # -------------------------
    meta_desc = soup.find("meta", attrs={"name": "description"})
    if not meta_desc:
        score -= 20
        errores.append("Falta meta description")

    # -------------------------
    # CANONICAL
    # -------------------------
    if not soup.find("link", rel="canonical"):
        score -= 10
        errores.append("Falta canonical")

    # -------------------------
    # ROBOTS
    # -------------------------
    robots = soup.find("meta", attrs={"name": "robots"})
    if robots and "noindex" in (robots.get("content") or "").lower():
        score -= 50
        errores.append("Página en noindex")

    # -------------------------
    # OG TAGS
    # -------------------------
    og_tags = soup.find_all("meta", property=lambda x: x and "og:" in x)
    if not og_tags:
        score -= 5
        errores.append("Sin Open Graph")

    # -------------------------
    # 🏗️ ESTRUCTURA HTML
    # -------------------------
    h1 = soup.find_all("h1")
    h2 = soup.find_all("h2")
    h3 = soup.find_all("h3")

    if len(h1) == 0:
        score -= 15
        errores.append("Sin H1")

    if len(h1) > 1:
        score -= 10
        errores.append("Múltiples H1")

    if len(h2) == 0:
        score -= 5
        errores.append("Sin H2")

    if h3 and not h2:
        score -= 5
        errores.append("H3 sin H2 (mala jerarquía)")

    # -------------------------
    # 🧠 SEMÁNTICA HTML
    # -------------------------
    if not soup.find("main"):
        score -= 5
        errores.append("Falta <main>")

    if not soup.find("header"):
        score -= 3
        errores.append("Falta <header>")

    if not soup.find("footer"):
        score -= 3
        errores.append("Falta <footer>")

    # -------------------------
    # CONTENIDO
    # -------------------------
    texto = soup.get_text()
    if len(texto.strip()) < 500:
        score -= 20
        errores.append("Contenido pobre")

    # -------------------------
    # IMÁGENES ALT
    # -------------------------
    imgs = soup.find_all("img")
    sin_alt = [i for i in imgs if not i.get("alt")]

    if sin_alt:
        score -= 10
        errores.append(f"{len(sin_alt)} imágenes sin ALT")

    # -------------------------
    # HREFLANG
    # -------------------------
    hreflang = soup.find_all("link", rel="alternate")
    if not any("hreflang" in str(x) for x in hreflang):
        score -= 5
        errores.append("Sin hreflang")

    # -------------------------
    # ENLACES INTERNOS
    # -------------------------
    enlaces = soup.find_all("a", href=True)
    internos = [a for a in enlaces if "/" in a["href"]]

    if len(internos) < 5:
        score -= 5
        errores.append("Pocos enlaces internos")

    data["score"] = max(score, 0)
    data["errores_seo"] = errores

    return data