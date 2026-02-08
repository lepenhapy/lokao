import requests
from bs4 import BeautifulSoup
import statistics
import re

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

def limpar_numero(texto):
    texto = texto.replace("R$", "").replace(".", "").replace(",", ".")
    try:
        return float(texto)
    except:
        return None


def extrair_valores(bairro, tipo="casa"):
    """
    tipo = 'casa' ou 'terreno'
    """
    bairro_url = bairro.lower().replace(" ", "-")
    tipo_url = "casas" if tipo == "casa" else "terrenos"

    url = f"https://www.vivareal.com.br/venda/mato-grosso/cuiaba/bairros/{bairro_url}/{tipo_url}/"

    resp = requests.get(url, headers=HEADERS, timeout=10)
    if resp.status_code != 200:
        return None

    soup = BeautifulSoup(resp.text, "html.parser")
    cards = soup.select("div.property-card__content")

    valores_m2 = []

    for card in cards[:15]:
        preco = card.select_one(".property-card__price")
        area = card.select_one(".property-card__detail-value")

        if not preco or not area:
            continue

        preco_val = limpar_numero(preco.text)
        area_val = limpar_numero(area.text)

        if not preco_val or not area_val or area_val <= 20:
            continue

        valor_m2 = preco_val / area_val
        valores_m2.append(valor_m2)

    if len(valores_m2) < 3:
        return None

    return round(statistics.median(valores_m2), 2)
