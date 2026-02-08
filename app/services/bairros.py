MAPA_BAIRROS = {
    "Centro": "Urbano Consolidado Central",
    "Araés": "Urbano Consolidado Central",
    "Lixeira": "Urbano Consolidado Central",

    "Goiabeiras": "Residencial de Alto Padrão",
    "Duque de Caxias": "Residencial de Alto Padrão",
    "Bosque da Saúde": "Residencial de Alto Padrão",

    "Popular": "Misto Residencial–Comercial",
    "Jardim das Américas": "Misto Residencial–Comercial",
    "Coxipó": "Misto Residencial–Comercial",

    "Jardim Itália": "Expansão Urbana Planejada",
    "Florais Cuiabá": "Residencial de Alto Padrão",
    "Florais dos Lagos": "Residencial de Alto Padrão",
    "Ribeirão do Lipa": "Expansão Urbana Planejada",

    "CPA I": "Residencial Tradicional Consolidado",
    "CPA II": "Residencial Tradicional Consolidado",
    "CPA III": "Residencial Tradicional Consolidado",

    "Distrito Industrial": "Zona Especial / Industrial / Logística"
}

PERFIL_PADRAO = "Residencial Tradicional Consolidado"

def obter_perfil_lokao(bairro: str) -> str:
    return MAPA_BAIRROS.get(bairro, PERFIL_PADRAO)
