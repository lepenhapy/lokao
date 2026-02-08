def _parse_float(valor):
    if valor is None:
        return 0.0
    if isinstance(valor, (int, float)):
        return float(valor)
    if isinstance(valor, str):
        try:
            return float(
                valor.replace("R$", "")
                .replace(".", "")
                .replace(",", ".")
                .strip()
            )
        except ValueError:
            return 0.0
    return 0.0


def _fmt_moeda(valor):
    return f"R$ {valor:,.0f}".replace(",", ".")


def gerar_sugestoes(
    df,
    dados_bairro,
    score,
    orcamento,
    area,
    padrao,
    limite=5,
):
    """
    Sugestoes com foco em poder financeiro e margem de seguranca.
    """
    score_valor = (score or {}).get("valor", 0)
    if score_valor >= 75:
        return []

    orcamento = _parse_float(orcamento)
    area = _parse_float(area)
    if orcamento <= 0:
        return []

    bairro_atual = dados_bairro.get("bairro")
    padrao_desejado = str(padrao or "").lower()
    ordem = {"economico": 1, "baixo": 1, "medio": 2, "alto": 3}
    nivel_desejado = ordem.get(padrao_desejado, 0)

    candidatos = []
    for _, row in df.iterrows():
        bairro = row.get("bairro")
        if bairro == bairro_atual:
            continue

        padrao_bairro = str(row.get("padrao_predominante") or "").lower()
        nivel_bairro = ordem.get(padrao_bairro, 0)

        # Mantem proximidade de padrao, mas sem forcar bairro muito abaixo.
        if (
            nivel_desejado
            and nivel_bairro
            and abs(nivel_bairro - nivel_desejado) > 1
        ):
            continue

        valor_m2 = _parse_float(row.get("valor_m2_medio"))
        if valor_m2 <= 0:
            continue

        area_ref = area if area > 0 else 180.0
        custo_estimado = valor_m2 * area_ref
        comprometimento = custo_estimado / orcamento
        folga = 1 - comprometimento

        # Evita bairros inviaveis e bairros com ticket muito distante.
        if comprometimento > 0.95:
            continue
        if comprometimento < 0.30:
            continue

        # Alvo de encaixe:
        # usar ate ~70% do orcamento para manter folga tecnica.
        distancia_alvo = abs(0.70 - comprometimento)
        candidatos.append(
            {
                "bairro": bairro,
                "padrao": padrao_bairro or "nao informado",
                "custo": custo_estimado,
                "comp": comprometimento,
                "folga": folga,
                "dist": distancia_alvo,
            }
        )

    candidatos.sort(key=lambda c: (c["dist"], -c["comp"]))

    sugestoes = []
    for c in candidatos[:limite]:
        sugestoes.append(
            (
                f"{c['bairro']} - Custo estimado de {_fmt_moeda(c['custo'])} "
                f"para a area informada, comprometendo {c['comp']*100:.1f}% "
                f"do orçamento e mantendo folga de {c['folga']*100:.1f}%."
            )
        )

    return sugestoes
