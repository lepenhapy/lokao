# app/services/financeiro.py


def _to_float(valor):
    try:
        return float(valor)
    except (TypeError, ValueError):
        return 0.0


def _safe_div(numerador, denominador):
    if denominador <= 0:
        return 0.0
    return numerador / denominador


def _calcular_cenarios_compra(valor_imovel, financiar):
    if valor_imovel <= 0:
        return []

    cenarios = {
        "Conservador": {
            "itbi": 0.020,
            "cartorio": 0.008,
            "bancario": 2500 if financiar else 800,
            "adequacoes": 0.020,
            "reserva": 0.040,
        },
        "Base": {
            "itbi": 0.025,
            "cartorio": 0.011,
            "bancario": 4500 if financiar else 1200,
            "adequacoes": 0.050,
            "reserva": 0.060,
        },
        "Estressado": {
            "itbi": 0.030,
            "cartorio": 0.015,
            "bancario": 7000 if financiar else 1800,
            "adequacoes": 0.080,
            "reserva": 0.100,
        },
    }

    projecoes = []
    for nome, premissa in cenarios.items():
        itbi = valor_imovel * premissa["itbi"]
        cartorio = valor_imovel * premissa["cartorio"]
        bancario = premissa["bancario"]
        adequacoes = valor_imovel * premissa["adequacoes"]
        reserva = valor_imovel * premissa["reserva"]
        total = (
            valor_imovel + itbi + cartorio
            + bancario + adequacoes + reserva
        )
        projecoes.append(
            {
                "cenario": nome,
                "itbi": itbi,
                "cartorio": cartorio,
                "bancario": bancario,
                "adequacoes": adequacoes,
                "reserva": reserva,
                "total": total,
            }
        )
    return projecoes


def _calcular_cenarios_construcao(custo_obra):
    if custo_obra <= 0:
        return []

    cenarios = {
        "Conservador": {
            "projetos": 0.040,
            "aprovacoes": 0.010,
            "infraestrutura": 0.070,
            "contingencia": 0.080,
        },
        "Base": {
            "projetos": 0.060,
            "aprovacoes": 0.015,
            "infraestrutura": 0.100,
            "contingencia": 0.120,
        },
        "Estressado": {
            "projetos": 0.080,
            "aprovacoes": 0.020,
            "infraestrutura": 0.130,
            "contingencia": 0.180,
        },
    }

    projecoes = []
    for nome, premissa in cenarios.items():
        projetos = custo_obra * premissa["projetos"]
        aprovacoes = custo_obra * premissa["aprovacoes"]
        infraestrutura = custo_obra * premissa["infraestrutura"]
        contingencia = custo_obra * premissa["contingencia"]
        total = (
            custo_obra + projetos + aprovacoes
            + infraestrutura + contingencia
        )
        projecoes.append(
            {
                "cenario": nome,
                "projetos": projetos,
                "aprovacoes": aprovacoes,
                "infraestrutura": infraestrutura,
                "contingencia": contingencia,
                "total": total,
            }
        )
    return projecoes


def analisar_financeiro(**kwargs) -> dict:
    """
    Analise financeira orientativa com cenarios de desembolso final.
    """

    orcamento = _to_float(kwargs.get("orcamento"))
    valor_imovel = _to_float(kwargs.get("valor_imovel"))
    area = _to_float(kwargs.get("area"))
    valor_m2 = _to_float(kwargs.get("valor_m2"))
    renda = _to_float(kwargs.get("renda"))
    financiar = bool(kwargs.get("financiar", False))
    prazo_meses = int(_to_float(kwargs.get("prazo_meses", 360))) or 360

    resultado = {
        "orcamento": orcamento,
        "valor_imovel": valor_imovel,
        "area": area,
        "valor_m2": valor_m2,
        "mensagens": [],
    }

    if valor_m2 > 0 and area > 0:
        resultado["custo_estimado"] = valor_m2 * area

    if valor_imovel > 0:
        percentual_ticket = _safe_div(valor_imovel, orcamento) * 100
        resultado["percentual_ticket_orcamento"] = percentual_ticket

        if percentual_ticket <= 70:
            resultado["mensagens"].append(
                "Ticket de compra em faixa confortavel frente ao orcamento."
            )
        elif percentual_ticket <= 90:
            resultado["mensagens"].append(
                "Ticket em faixa administravel, com necessidade "
                "de controle de custos."
            )
        else:
            resultado["mensagens"].append(
                "Ticket pressionado para o orcamento informado."
            )

    if financiar and valor_imovel > 0:
        entrada_minima = valor_imovel * 0.2
        saldo_financiado = valor_imovel - entrada_minima
        parcela_estimada = saldo_financiado / max(1, prazo_meses)
        comprometimento = _safe_div(parcela_estimada, renda) * 100
        resultado.update(
            {
                "entrada_minima_estimada": entrada_minima,
                "parcela_estimada_360m": parcela_estimada,
                "comprometimento_renda_estimado": comprometimento,
            }
        )
        resultado["mensagens"].append(
            "Simulacao simplificada: use como referencia inicial, "
            "nao como proposta bancaria."
        )

    projecoes_compra = _calcular_cenarios_compra(valor_imovel, financiar)
    for linha in projecoes_compra:
        linha["saldo_vs_orcamento"] = orcamento - linha["total"]
        linha["percentual_orcamento"] = (
            _safe_div(linha["total"], orcamento) * 100
        )
    resultado["projecoes_compra"] = projecoes_compra

    custo_obra = resultado.get("custo_estimado", 0.0)
    projecoes_construcao = _calcular_cenarios_construcao(custo_obra)
    for linha in projecoes_construcao:
        linha["saldo_vs_orcamento"] = orcamento - linha["total"]
        linha["percentual_orcamento"] = (
            _safe_div(linha["total"], orcamento) * 100
        )
    resultado["projecoes_construcao"] = projecoes_construcao

    return resultado


# ======================================================
# ALIAS DE CONTRATO (NAO REMOVER)
# ======================================================
def simular_financeiro(**kwargs) -> dict:
    """
    Alias publico utilizado pelo routes.
    Mantem compatibilidade e permite evolucao interna.
    """
    return analisar_financeiro(**kwargs)
