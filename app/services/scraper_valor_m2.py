import requests
from bs4 import BeautifulSoup
import re
import statistics


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0 Safari/537.36"
    )
}


def extrair_valores(texto):
    """
    Extrai valores monetários do tipo R$ 7.200/m²
    """
    valores = []
    padrao = re.findall(r"R\$\s?([\d\.]+)", texto)
    for v in padrao:
        try:
            valores.append(float(v.replace(".", "")))
        except ValueError:
            continue
    return valores


def buscar_valor_m2_viva_real(
    bairro,
    tipo_imovel="casa",
    cidade="cuiaba",
    timeout=10,
):
    """
    Retorna valor médio de mercado por m² ou None
    """
    tipo = "casas" if "casa" in tipo_imovel.lower() else "apartamentos"

    url = (
        f"https://www.vivareal.com.br/venda/"
        f"{cidade}-{cidade}/{tipo}/"
        f"?q={bairro}"
    )

    try:
        resposta = requests.get(url, headers=HEADERS, timeout=timeout)
        if resposta.status_code != 200:
            return None

        soup = BeautifulSoup(resposta.text, "html.parser")

        textos = soup.get_text(separator=" ")
        valores = extrair_valores(textos)

        # Remove valores absurdos
        valores = [v for v in valores if 500 < v < 50000]

        if len(valores) < 3:
            return None

        return round(statistics.median(valores), 2)

    except Exception:
        return None


def obter_valor_m2(
    bairro,
    tipo_imovel,
    valor_planilha=None,
    cidade="cuiaba"
):
    """
    Estratégia completa:
    1. scraping
    2. planilha
    3. fallback regional
    """

    # 1️⃣ scraping
    valor_scraping = buscar_valor_m2_viva_real(bairro, tipo_imovel)
    if valor_scraping:
        return {
            "valor": valor_scraping,
            "fonte": "Viva Real (scraping)"
        }

    # 2️⃣ planilha
    if valor_planilha and valor_planilha > 0:
        return {
            "valor": valor_planilha,
            "fonte": "Base interna Lokao"
        }

    # 3️⃣ fallback por região
    fallback = {
        "Leste": 5500,
        "Oeste": 6000,
        "Norte": 4500,
        "Sul": 4000,
        "Central": 6500
    }

    return {
        "valor": fallback.get("Leste", 5000),
        "fonte": "Estimativa regional"
    }
