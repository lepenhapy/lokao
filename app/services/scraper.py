# app/services/scraper.py

def obter_valor_m2_bairro(
    bairro: str,
    tipo_imovel: str | None = None
) -> dict:
    """
    Retorna valor médio estimado do m² para o bairro informado,
    considerando (quando possível) o tipo de imóvel.
    """

    # Base mock inicial (substituível por scraping real)
    valores_base = {
        "Alphaville I e II": {
            "Casa nova": 7500,
            "Casa usada": 7000,
            "Terreno": 4200,
        },
        "Jardim Imperial": {
            "Casa nova": 4800,
            "Casa usada": 4400,
            "Terreno": 2800,
        },
        "Centro Norte": {
            "Apartamento": 5200,
            "Casa usada": 5000,
            "Terreno": 3000,
        },
    }

    dados_bairro = valores_base.get(bairro)

    # Caso bairro não esteja na base
    if not dados_bairro:
        return {
            "bairro": bairro,
            "valor_m2": None,
            "fonte": "nao_encontrado",
            "observacao": (
                "Não foi possível identificar valor médio de mercado "
                "para este bairro no momento."
            ),
        }

    # Se tipo de imóvel foi informado e existe na base
    if tipo_imovel and tipo_imovel in dados_bairro:
        valor = dados_bairro[tipo_imovel]
        fonte = "estimativa_por_tipo"
    else:
        # Média simples dos valores disponíveis
        valores = list(dados_bairro.values())
        valor = round(sum(valores) / len(valores), 2)
        fonte = "media_bairro"

    return {
        "bairro": bairro,
        "tipo_imovel": tipo_imovel,
        "valor_m2": valor,
        "fonte": fonte,
        "observacao": (
            "Valor estimado a partir de anúncios públicos e dados de mercado. "
            "Pode variar conforme rua, padrão construtivo, posição solar, "
            "ruído urbano e momento econômico."
        ),
    }
