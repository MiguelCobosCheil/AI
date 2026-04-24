import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

from main import extraer_info_web

def ejecutar_crawl(base_url, max_pages, opciones):

    visited = set()
    results = []

    base_domain = urlparse(base_url).netloc

    def es_mismo_dominio(url):
        try:
            return urlparse(url).netloc == base_domain
        except:
            return False

    def limpiar_url(url):
        return url.split("#")[0].rstrip("/")

    def recorrer(url):

        url = limpiar_url(url)

        if url in visited or len(visited) >= max_pages:
            return

        visited.add(url)

        try:
            r = requests.get(url, timeout=10)
            if r.status_code != 200:
                return
            html = r.text
        except:
            return

        try:
            info = extraer_info_web(html, opciones)
        except:
            info = {}

        results.append({
            "url": url,
            "data": info,
            "score": info.get("score")
        })

        soup = BeautifulSoup(html, "html.parser")

        for a in soup.find_all("a", href=True):

            href = a["href"].strip()

            if href.startswith("#") or href.startswith("mailto:") or href.startswith("tel:") or "javascript:" in href:
                continue

            full_url = limpiar_url(urljoin(url, href))

            if not es_mismo_dominio(full_url):
                continue

            recorrer(full_url)

    recorrer(base_url)

    return {
        "total": len(results),
        "results": results
    }