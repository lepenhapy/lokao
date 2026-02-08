import pandas as pd
from pathlib import Path


def carregar_bairros():
    """
    Carrega a base de bairros de Cuiaba com contrato unico.
    """
    raiz = Path(__file__).resolve().parents[2]

    caminhos_possiveis = [
        raiz / "data" / "bairros_cuiaba.csv",
        raiz / "data" / "bairros.csv",
        raiz / "bairros_cuiaba.csv",
        raiz / "bairros.csv",
    ]

    caminho = next((c for c in caminhos_possiveis if c.exists()), None)
    if caminho is None:
        raise FileNotFoundError(
            "Arquivo de bairros nao encontrado. "
            "Coloque 'bairros_cuiaba.csv' dentro de /data."
        )

    df = pd.read_csv(caminho)
    df.columns = [c.strip().lower() for c in df.columns]

    # Compatibilidade entre schemas antigos/novos
    if "padrao_predominante" not in df.columns and "padrao_urbano" in df.columns:
        df["padrao_predominante"] = df["padrao_urbano"]
    if "uso_predominante" not in df.columns and "uso_solo" in df.columns:
        df["uso_predominante"] = df["uso_solo"]
    if "nivel_ruido" not in df.columns and "sensibilidade_ruido" in df.columns:
        df["nivel_ruido"] = df["sensibilidade_ruido"]

    colunas_minimas = [
        "bairro",
        "regiao",
        "perfil_urbano",
        "uso_predominante",
        "infraestrutura",
        "nivel_ruido",
        "padrao_predominante",
        "valor_m2_medio",
        "perfil_socioeconomico",
    ]
    for col in colunas_minimas:
        if col not in df.columns:
            df[col] = ""

    df["bairro"] = df["bairro"].astype(str).str.strip()
    df["regiao"] = df["regiao"].astype(str).str.strip()
    df["padrao_predominante"] = (
        df["padrao_predominante"].astype(str).str.strip().str.lower()
    )
    df["perfil_socioeconomico"] = (
        df["perfil_socioeconomico"].astype(str).str.strip().str.lower()
    )

    # Alias legado para consumidores que esperam 'padrao'
    if "padrao" not in df.columns:
        df["padrao"] = df["padrao_predominante"]

    return df
