# app/services/scraping.py

import random
import time


def obter_valor_m2(bairro: str, tipo_imovel: str) -> float:
    """
    Retorna o valor médio do m² para o bairro informado.

    Estratégia:
    1) Base interna de referência (segura e rápida)
    2) Simulação de scraping (stub controlado)
    3) Fallback conservador (nunca quebra o sistema)

    Nunca retorna None.
    """

    bairro = bairro.strip()

    # =====================================================
    # 1️⃣ BASE DE REFERÊNCIA (manual + confiável)
    # =====================================================
    referencia_m2 = {
        # ALTO PADRÃO
        "Alphaville I e II": 7500,
        "Florais do Parque": 7200,
        "Florais Cuiabá": 7000,
        "Florais dos Lagos": 7300,
        "Jardim das Américas": 6500,

        # MÉDIO
        "Jardim Imperial": 4200,
        "Jardim Itália": 4300,
        "Jardim Leblon": 4100,
        "Jardim Kennedy": 3900,
        "Bosque da Saúde": 4500,

        # CENTRAL
        "Centro Norte": 3800,
        "Centro Sul": 4000,
        "Araés": 3600,

        # POPULAR / EXPANSÃO
        "CPA I, II, III e IV": 3000,
        "Pedra 90 (Setores I a IV)": 2700,
        "Tijucal (Sectores I a IV)": 2800,
    }

    if bairro in referencia_m2:
        return float(referencia_m2[bairro])

    # =====================================================
    # 2️⃣ SCRAPING SIMULADO (CONTROLADO)
    # =====================================================
    # ⚠️ Aqui futuramente entra Zap / VivaReal / ImovelWeb
    # Agora mantemos previsível e estável

    valor_scraping = _scraping_simulado(bairro, tipo_imovel)

    if valor_scraping > 0:
        return float(valor_scraping)

    # =====================================================
    # 3️⃣ FALLBACK CONSERVADOR (NUNCA QUEBRA)
    # =====================================================
    return 3500.0


# =====================================================
# FUNÇÃO INTERNA – SIMULAÇÃO DE SCRAPING
# =====================================================
def _scraping_simulado(bairro: str, tipo_imovel: str) -> float:
    """
    Simula uma busca externa.
    Retorna 0 se não encontrar.
    """

    # Delay artificial (evita comportamento agressivo futuramente)
    time.sleep(0.2)

    # Faixas médias por tipo
    faixa = {
        "casa": (3200, 5500),
        "apartamento": (3500, 6000),
        "terreno": (2500, 4800),
    }

    tipo = tipo_imovel.lower()
    minimo, maximo = faixa.get(tipo, (3000, 5000))

    # Simula chance de não encontrar dados
    chance = random.random()

    if chance < 0.35:
        return 0  # não achou nada

    return round(random.uniform(minimo, maximo), 2)
