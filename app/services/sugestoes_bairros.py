# app/services/sugestoes_bairros.py


def _to_float(valor):
    if valor is None:
        return 0.0
    if isinstance(valor, (int, float)):
        return float(valor)
    if isinstance(valor, str):
        try:
            return float(valor.replace("R$", "").replace(".", "").replace(",", ".").strip())
        except ValueError:
            return 0.0
    return 0.0


def gerar_sugestoes_bairros(**kwargs):
    """
    Gera sugestoes de bairros tecnicamente semelhantes,
    porem com melhor compatibilidade financeira.

    Aceita **kwargs para garantir compatibilidade arquitetural
    e evitar quebras no routes.
    """

    df = kwargs.get("df")
    bairro_atual = kwargs.get("bairro_atual")
    orcamento = _to_float(kwargs.get("orcamento"))
    limite = kwargs.get("limite", 5)

    if df is None or bairro_atual is None:
        return []
    if "bairro" not in df.columns:
        return []
    if bairro_atual not in df["bairro"].values:
        return []

    atual = df[df["bairro"] == bairro_atual].iloc[0]
    regiao_atual = atual.get("regiao")
    perfil_atual = atual.get("perfil_socioeconomico")
    padrao_atual = (atual.get("padrao_predominante") or atual.get("padrao_urbano") or "").lower()
    valor_m2_atual = _to_float(atual.get("valor_m2_medio"))

    padrao_map = {"economico": 1, "baixo": 1, "medio": 2, "alto": 3}
    score_padrao_atual = padrao_map.get(padrao_atual, 0)

    candidatos = []
    for _, row in df.iterrows():
        if row.get("bairro") == bairro_atual:
            continue
        if regiao_atual and row.get("regiao") != regiao_atual:
            continue
        if perfil_atual and row.get("perfil_socioeconomico") != perfil_atual:
            continue

        padrao_linha = (row.get("padrao_predominante") or row.get("padrao_urbano") or "").lower()
        score_padrao_linha = padrao_map.get(padrao_linha, 0)
        if score_padrao_atual and score_padrao_linha > score_padrao_atual:
            continue

        valor_m2_linha = _to_float(row.get("valor_m2_medio"))
        if orcamento > 0 and valor_m2_linha > 0 and valor_m2_linha > orcamento:
            continue

        candidatos.append((row, valor_m2_linha))

    candidatos.sort(key=lambda item: item[1] if item[1] > 0 else 10**9)

    sugestoes = []
    for row, valor_m2 in candidatos:
        if valor_m2_atual > 0 and valor_m2 > 0:
            vantagem = ((valor_m2_atual - valor_m2) / valor_m2_atual) * 100
            complemento = f"aprox. {vantagem:.1f}% mais eficiente no valor medio por m2"
        else:
            complemento = "boa alternativa urbana para o mesmo perfil"

        sugestoes.append(
            f"{row.get('bairro')} - regiao {row.get('regiao')}, perfil semelhante e {complemento}."
        )

        if len(sugestoes) >= limite:
            break

    return sugestoes
