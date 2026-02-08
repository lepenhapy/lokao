import pandas as pd
from pathlib import Path


# ==============================
# MAPA DE INFERÊNCIAS POR REGIÃO
# ==============================
INFERENCIAS_REGIAO = {
    "Central": {
        "perfil_urbano": "Área urbana consolidada, com uso misto e grande circulação.",
        "uso_solo": "Predominância de uso misto (residencial e comercial).",
        "infraestrutura": "Infraestrutura urbana considerada alta.",
        "mobilidade": "Alta oferta de vias estruturantes e transporte.",
        "nivel_ruido": "Nível de ruído médio a alto, típico de áreas centrais."
    },
    "Norte": {
        "perfil_urbano": "Área predominantemente residencial, com expansão urbana.",
        "uso_solo": "Predominância residencial.",
        "infraestrutura": "Infraestrutura urbana de nível médio.",
        "mobilidade": "Mobilidade urbana considerada média.",
        "nivel_ruido": "Nível de ruído urbano médio."
    },
    "Sul": {
        "perfil_urbano": "Área residencial consolidada com ocupação popular.",
        "uso_solo": "Predominância residencial com pontos comerciais.",
        "infraestrutura": "Infraestrutura urbana de nível médio.",
        "mobilidade": "Mobilidade urbana média.",
        "nivel_ruido": "Nível de ruído urbano médio."
    },
    "Leste": {
        "perfil_urbano": "Área residencial planejada, com presença de empreendimentos de médio e alto padrão.",
        "uso_solo": "Predominância residencial planejada.",
        "infraestrutura": "Infraestrutura urbana considerada alta.",
        "mobilidade": "Boa mobilidade e acesso a vias principais.",
        "nivel_ruido": "Nível de ruído baixo a médio."
    },
    "Oeste": {
        "perfil_urbano": "Área residencial consolidada, com bairros tradicionais e áreas nobres.",
        "uso_solo": "Predominância residencial consolidada.",
        "infraestrutura": "Infraestrutura urbana considerada alta.",
        "mobilidade": "Boa mobilidade urbana.",
        "nivel_ruido": "Nível de ruído baixo a médio."
    }
}


# ==============================
# FUNÇÃO PRINCIPAL
# ==============================
def obter_dados_urbanos(bairro: str) -> dict:
    """
    Retorna dados urbanos SEMPRE preenchidos,
    aplicando inferência regional quando necessário.
    """

    base_dir = Path(__file__).resolve().parents[2]
    caminho = base_dir / "data" / "bairros_cuiaba.csv"

    df = pd.read_csv(caminho)

    linha = df[df["bairro"].str.lower() == bairro.lower()].iloc[0]

    regiao = linha.get("regiao", "").strip()

    inferencia = INFERENCIAS_REGIAO.get(regiao, {})

    def resolver(campo, texto_padrao):
        valor = linha.get(campo)
        if pd.isna(valor) or str(valor).strip() == "":
            return inferencia.get(campo, texto_padrao)
        return str(valor)

    return {
        "bairro": bairro,
        "regiao": regiao if regiao else "Não informada",
        "perfil_urbano": resolver(
            "perfil_urbano",
            "Perfil urbano estimado para a região."
        ),
        "uso_solo": resolver(
            "uso_solo",
            "Uso do solo estimado conforme padrão regional."
        ),
        "infraestrutura": resolver(
            "infraestrutura",
            "Infraestrutura urbana considerada adequada para a região."
        ),
        "mobilidade": resolver(
            "mobilidade",
            "Mobilidade urbana compatível com a região."
        ),
        "nivel_ruido": resolver(
            "nivel_ruido",
            "Nível de ruído urbano compatível com a região."
        ),
        "observacoes_entorno": "Análise baseada em dados urbanos públicos e inferências técnicas regionais."
    }
