from app.services.loader import carregar_bairros


df = carregar_bairros()
print("linhas:", len(df))
print("colunas:", list(df.columns))

centro = df[df["bairro"].str.lower() == "centro"]
if not centro.empty:
    print("centro:", centro.iloc[0].to_dict())
else:
    print("centro: nao encontrado")
