import pandas as pd
from datetime import datetime, timedelta
from app.services.scraping.fontes.vivareal import extrair_valores

CAMINHO = "data/bairros_cuiaba.csv"


def precisa_atualizar(data):
    if pd.isna(data) or not data:
        return True
    try:
        ultima = datetime.strptime(data, "%Y-%m-%d")
        return datetime.now() - ultima > timedelta(days=15)
    except:
        return True


def atualizar_base():
    df = pd.read_csv(CAMINHO)

    for idx, row in df.iterrows():
        bairro = row["bairro"]

        if precisa_atualizar(row["data_atualizacao"]):
            print(f"🔍 Atualizando {bairro}")

            valor_casa = extrair_valores(bairro, "casa")
            valor_terreno = extrair_valores(bairro, "terreno")

            if valor_casa:
                df.at[idx, "valor_m2_casa"] = valor_casa
            if valor_terreno:
                df.at[idx, "valor_m2_terreno"] = valor_terreno

            df.at[idx, "fonte_valor"] = "VivaReal"
            df.at[idx, "data_atualizacao"] = datetime.now().strftime("%Y-%m-%d")

    df.to_csv(CAMINHO, index=False)
    print("✅ Base atualizada com sucesso.")
