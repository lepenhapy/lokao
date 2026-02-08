def _parse_float(valor):
    """
    Converte qualquer valor monetario ou numerico para float.
    """
    if valor is None:
        return 0.0

    if isinstance(valor, (int, float)):
        return float(valor)

    if isinstance(valor, str):
        try:
            valor = (
                valor.replace("R$", "")
                .replace(".", "")
                .replace(",", ".")
                .strip()
            )
            return float(valor)
        except ValueError:
            return 0.0

    return 0.0


def calcular_score_urbano(dados_bairro: dict, **kwargs) -> dict:
    """
    Calcula o índice de compatibilidade urbana do Lokao.
    """
    orcamento = _parse_float(kwargs.get("orcamento"))
    valor_imovel = _parse_float(kwargs.get("valor_imovel"))
    _ = _parse_float(kwargs.get("area"))
    padrao_desejado = (kwargs.get("padrao_desejado") or "").lower()
    financia = kwargs.get("financia", False)

    score = 20  # base neutra
    explicacoes = []

    padrao_bairro = (dados_bairro.get("padrao_predominante") or "").lower()
    perfil_socio = (dados_bairro.get("perfil_socioeconomico") or "").lower()
    ordem = {"economico": 1, "baixo": 1, "medio": 2, "alto": 3}
    nivel_bairro = ordem.get(padrao_bairro, 0)
    nivel_desejado = ordem.get(padrao_desejado, 0)
    nivel_socio = ordem.get(perfil_socio, 0)

    # 1) Perfil urbano do bairro
    if padrao_bairro == "alto":
        score += 25
        explicacoes.append("Bairro de padrão urbano elevado.")
    elif padrao_bairro == "medio":
        score += 18
        explicacoes.append("Bairro de padrão urbano intermediário.")
    else:
        score += 10
        explicacoes.append("Bairro de padrão urbano mais econômico/popular.")

    # 2) Coerencia de padrao
    if padrao_desejado:
        if nivel_desejado and nivel_bairro:
            diff = abs(nivel_desejado - nivel_bairro)
            if diff == 0:
                score += 20
                explicacoes.append(
                    "Padrão desejado totalmente compatível com o bairro."
                )
            elif diff == 1:
                score -= 8
                explicacoes.append(
                    "Padrão desejado parcialmente desalinhado com a "
                    "predominância do bairro."
                )
            else:
                score -= 16
                explicacoes.append(
                    "Padrão desejado distante da predominância urbana local."
                )
        else:
            explicacoes.append(
                "Padrão do bairro não totalmente identificado "
                "para comparação fina."
            )

    # 3) Capacidade financeira
    if valor_imovel > 0 and orcamento > 0:
        relacao = orcamento / valor_imovel
        if relacao >= 1.8:
            score += 25
            explicacoes.append(
                "Orçamento com folga alta para aquisição e custos acessórios."
            )
        elif relacao >= 1.4:
            score += 22
            explicacoes.append(
                "Orçamento com folga confortável para o ticket analisado."
            )
        elif relacao >= 1.1:
            score += 18
            explicacoes.append(
                "Orçamento compatível com margem moderada de segurança."
            )
        elif relacao >= 1.0:
            score += 14
            explicacoes.append("Orçamento compatível, com folga reduzida.")
        elif relacao >= 0.85:
            score += 6
            explicacoes.append("Orçamento próximo do valor do imóvel.")
        else:
            score -= 20
            explicacoes.append(
                "Orçamento insuficiente para o valor do imóvel."
            )

    # 4) Ajuste por desalinhamento socioeconomico
    bairro_abaixo = (
        (0 < nivel_bairro < nivel_desejado)
        or (0 < nivel_socio < nivel_desejado)
    )
    if (
        valor_imovel > 0
        and orcamento >= valor_imovel * 1.5
        and nivel_desejado >= 3
        and bairro_abaixo
    ):
        score -= 6
        explicacoes.append(
            "Há desalinhamento de posicionamento: capacidade financeira "
            "alta em bairro de predominancia socioeconomica inferior ao "
            "padrão desejado."
        )

    # 5) Impacto do financiamento
    if financia:
        score -= 4
        explicacoes.append(
            "Financiamento reduz a margem de segurança financeira "
            "de longo prazo."
        )

    score = max(0, min(100, int(score)))

    if score >= 80:
        classificacao = "Excelente compatibilidade"
    elif score >= 65:
        classificacao = "Boa compatibilidade"
    elif score >= 45:
        classificacao = "Compatibilidade limitada"
    else:
        classificacao = "Baixa compatibilidade"

    return {
        "valor": score,
        "classificacao": classificacao,
        "explicacoes": explicacoes,
    }
