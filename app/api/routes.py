import os
from flask import Blueprint, abort, jsonify, render_template, request
import re
import unicodedata
from datetime import datetime

from app.services.financeiro import analisar_financeiro
from app.services.cub import obter_cub_cuiaba
from app.services.graficos import gerar_grafico_financeiro, gerar_grafico_score
from app.services.loader import carregar_bairros
from app.services.mercado_m2 import obter_contexto_m2
from app.services.pagamentos_mp import (
    carregar_pagamentos,
    confirmar_pagamento,
    criar_pagamento,
    registrar_pagamento_pendente,
    status_pagamento,
)
from app.services.piloto_teste import (
    dados_admin_piloto,
    feedback_ja_enviado,
    metricas_piloto,
    obter_janela_teste,
    registrar_feedback,
    registrar_geracao_unica,
    token_piloto_valido,
)
from app.services.pdf import gerar_pdf
from app.services.score_urbano import calcular_score_urbano
from app.services.sugestoes import gerar_sugestoes
from app.services.textos_dinamicos import (
    texto_compatibilidade,
    texto_financeiro,
    texto_urbano,
)
from app.utils.formatacao import float_para_moeda, moeda_para_float


router = Blueprint("router", __name__)


def _corrigir_mojibake(texto):
    if not isinstance(texto, str):
        return texto
    try:
        return texto.encode("latin1").decode("utf-8")
    except Exception:
        return texto


def _normalizar_nome_bairro(texto):
    texto = _corrigir_mojibake(str(texto or "")).strip().lower()
    texto = "".join(
        c for c in unicodedata.normalize("NFKD", texto)
        if not unicodedata.combining(c)
    )
    return " ".join(texto.split())


def _obter_dados_bairro(df, nome_bairro):
    if not nome_bairro:
        return {}

    alvo = _normalizar_nome_bairro(nome_bairro)
    serie_normalizada = df["bairro"].astype(str).map(_normalizar_nome_bairro)
    filtro = serie_normalizada == alvo
    if filtro.any():
        return df[filtro].iloc[0].to_dict()
    return {}


def _parse_financiar(valor):
    return str(valor).lower() in {"1", "true", "on", "sim"}


def _parse_prazo_meses(valor):
    txt = str(valor or "").lower()
    digitos = "".join(ch for ch in txt if ch.isdigit())
    try:
        return int(digitos) if digitos else 360
    except Exception:
        return 360


def _formatar_data_iso_br(valor):
    txt = str(valor or "").strip()
    if not txt:
        return ""
    try:
        return datetime.fromisoformat(txt).strftime("%d/%m/%Y %H:%M")
    except ValueError:
        return txt


def _formatar_competencia_curta(competencia):
    txt = str(competencia or "").strip()
    if len(txt) != 7 or "-" not in txt:
        return ""
    ano, mes = txt.split("-", 1)
    meses = {
        "01": "jan",
        "02": "fev",
        "03": "mar",
        "04": "abr",
        "05": "mai",
        "06": "jun",
        "07": "jul",
        "08": "ago",
        "09": "set",
        "10": "out",
        "11": "nov",
        "12": "dez",
    }
    return f"{meses.get(mes, mes)}/{ano[-2:]}"


def _insight_score(valor):
    if valor >= 70:
        return (
            "Leitura executiva: o score esta em faixa saudavel. "
            "A decisao tende a ser sustentavel se a vistoria tecnica "
            "confirmar os pontos de conforto e documentacao."
        )
    if valor >= 45:
        return (
            "Leitura executiva: o score indica zona de atencao. "
            "Ha viabilidade, mas com necessidade de ajustes em padrao, "
            "area ou estrategia financeira."
        )
    return (
        "Leitura executiva: o score esta em faixa critica para o cenario "
        "atual. A compra pode ocorrer, porem com maior chance de concessoes "
        "relevantes em conforto, liquidez ou custo total."
    )


def _insight_financeiro(orcamento, valor_imovel):
    if orcamento <= 0 or valor_imovel <= 0:
        return (
            "Leitura executiva: faltam valores completos para avaliar "
            "pressao financeira com precisao."
        )
    rel = valor_imovel / orcamento
    if rel <= 0.7:
        return (
            "Leitura executiva: relacao de preco confortavel frente ao "
            "orcamento, com margem para custos acessorios e ajustes "
            "pos-compra."
        )
    if rel <= 0.9:
        return (
            "Leitura executiva: relacao de preco administravel, porem "
            "exige disciplina no planejamento para nao reduzir a "
            "reserva de seguranca."
        )
    return (
        "Leitura executiva: relacao de preco pressionada para o orcamento "
        "informado; recomenda-se reduzir exposicao financeira antes de fechar."
    )


def _resumo_decisao(score_valor):
    if score_valor >= 70:
        return {
            "classe": "Seguir",
            "mensagem": (
                "Cenario favoravel para avancar na negociacao, mantendo "
                "validacao documental e vistoria tecnica final."
            ),
            "acao": (
                "Acione corretor e engenheiro para fechamento com checklist "
                "de risco e validacao cartorial."
            ),
        }
    if score_valor >= 45:
        return {
            "classe": "Seguir com ajustes",
            "mensagem": (
                "Ha viabilidade, mas com necessidade de calibrar "
                "padrao, area, "
                "ticket ou estrutura de financiamento."
            ),
            "acao": (
                "Negocie alternativas de bairro/tipo de imovel e rode nova "
                "simulacao financeira antes da proposta final."
            ),
        }
    return {
        "classe": "Reavaliar",
        "mensagem": (
            "Risco elevado de desalinhamento entre objetivo, bairro e custo "
            "total do ciclo imobiliario."
        ),
        "acao": (
            "Priorize bairros sugeridos, ajuste estrategia e somente retome "
            "fechamento apos nova rodada de analise."
        ),
    }


def _mes_pt(numero):
    meses = [
        "Janeiro",
        "Fevereiro",
        "Marco",
        "Abril",
        "Maio",
        "Junho",
        "Julho",
        "Agosto",
        "Setembro",
        "Outubro",
        "Novembro",
        "Dezembro",
    ]
    return meses[(numero - 1) % 12]


def _somar_meses(ano, mes, delta):
    total = (ano * 12 + (mes - 1)) + delta
    novo_ano = total // 12
    novo_mes = (total % 12) + 1
    return novo_ano, novo_mes


def _custo_m2_metodologia(cub, padrao):
    padrao_txt = str(padrao or "").strip().lower()
    steel_ref = {
        "economico": 2951.0,
        "medio": 4368.0,
        "alto": 5904.0,
    }
    steel_padrao = steel_ref.get(padrao_txt, 4368.0)

    convencional = cub if cub > 0 else 3000.0
    estrutural = convencional * 0.92
    steel = max(convencional * 1.18, steel_padrao)
    eps = convencional * 1.06

    return [
        {
            "metodologia": "Alvenaria convencional",
            "m2": convencional,
            "faixa_prazo": "8 a 14 meses",
            "fonte_preco": "Base Lokáo (referencia CUB/SINAPI)",
        },
        {
            "metodologia": "Alvenaria estrutural",
            "m2": estrutural,
            "faixa_prazo": "7 a 12 meses",
            "fonte_preco": "Base Lokáo (ganho de racionalizacao)",
        },
        {
            "metodologia": "Steel Frame",
            "m2": steel,
            "faixa_prazo": "5 a 9 meses",
            "fonte_preco": "Benchmark setorial (Centro-Oeste)",
        },
        {
            "metodologia": "Painel EPS (isopor) + concreto",
            "m2": eps,
            "faixa_prazo": "6 a 10 meses",
            "fonte_preco": "Base Lokáo (mercado regional)",
        },
    ]


def _montar_contexto_relatorio(token_forcado="", liberar_sem_pagamento=False):
    token = token_forcado or request.values.get("token", "")
    dados_salvos = {}
    if token:
        dados_salvos = (
            carregar_pagamentos().get(token, {}).get("dados", {}) or {}
        )

    nome = request.values.get("nome", dados_salvos.get("nome", ""))
    bairro = request.values.get("bairro", dados_salvos.get("bairro", ""))
    tipo_imovel = request.values.get(
        "tipo_imovel",
        dados_salvos.get("tipo_imovel", ""),
    )
    tipo_imovel_txt = str(tipo_imovel or "").strip().lower()
    is_apartamento = "apartamento" in tipo_imovel_txt
    padrao = request.values.get("padrao", dados_salvos.get("padrao", ""))

    orcamento_raw = request.values.get(
        "orcamento",
        dados_salvos.get("orcamento", ""),
    )
    valor_imovel_raw = request.values.get(
        "valor_imovel",
        dados_salvos.get("valor_imovel", ""),
    )
    area_raw = request.values.get("area", dados_salvos.get("area", ""))
    financiar_raw = request.values.get(
        "financiar",
        dados_salvos.get("financiar", ""),
    )
    tipo_financiamento = request.values.get(
        "tipo_financiamento",
        dados_salvos.get("tipo_financiamento", ""),
    )
    prazo = request.values.get("prazo", dados_salvos.get("prazo", ""))
    renda_raw = request.values.get("renda", dados_salvos.get("renda", ""))

    orcamento = moeda_para_float(orcamento_raw)
    valor_imovel = moeda_para_float(valor_imovel_raw)
    area = moeda_para_float(area_raw)
    renda = moeda_para_float(renda_raw)
    financiar = _parse_financiar(financiar_raw)

    df = carregar_bairros()
    dados_bairro = _obter_dados_bairro(df, bairro) or {
        "bairro": bairro,
        "padrao_predominante": padrao,
        "valor_m2_medio": 0,
    }

    score = calcular_score_urbano(
        dados_bairro=dados_bairro,
        orcamento=orcamento,
        valor_imovel=valor_imovel,
        area=area,
        padrao_desejado=padrao,
        financia=financiar,
    )

    sugestoes = gerar_sugestoes(
        df=df,
        dados_bairro=dados_bairro,
        score=score,
        orcamento=orcamento,
        area=area,
        padrao=padrao,
        limite=5,
    )

    contexto_m2 = obter_contexto_m2(
        dados_bairro=dados_bairro,
        bairro=bairro,
        tipo_imovel=tipo_imovel,
        usar_coleta_externa=True,
        cache_horas=168,
    )
    valor_m2_compra = contexto_m2.get("valor", 0)
    if is_apartamento:
        contexto_cub = {
            "valor": 0.0,
            "competencia_br": "",
            "padrao": "nao aplicavel",
            "cidade": "Cuiaba-MT",
            "fonte": "Nao aplicavel para apartamento",
        }
        cub = 0.0
        custo_estimado = 0.0
    else:
        contexto_cub = obter_cub_cuiaba(padrao=padrao)
        cub = contexto_cub.get("valor", 0)
        custo_estimado = cub * area if cub > 0 and area > 0 else 0
    entrada_estimada = (
        valor_imovel * 0.2 if financiar and valor_imovel > 0 else 0
    )
    parcela_estimada = (
        (valor_imovel * 0.8) / 360 if financiar and valor_imovel > 0 else 0
    )

    financeiro = analisar_financeiro(
        orcamento=orcamento,
        valor_imovel=valor_imovel,
        area=area,
        valor_m2=cub if cub > 0 else 0,
        renda=renda,
        financiar=financiar,
        prazo_meses=_parse_prazo_meses(prazo),
    )

    grafico_score_url = gerar_grafico_score(
        bairro=bairro or "bairro",
        score=score.get("valor", 0),
        media_cidade=55,
    )
    grafico_financeiro_url = gerar_grafico_financeiro(
        bairro=bairro or "bairro",
        orcamento=orcamento,
        valor_imovel=valor_imovel,
    )

    dados_relatorio = {
        "nome": nome,
        "bairro": bairro,
        "tipo_imovel": tipo_imovel,
        "padrao": padrao,
        "orcamento": orcamento_raw,
        "valor_imovel": valor_imovel_raw,
        "area": area_raw,
        "financiar": financiar_raw,
        "tipo_financiamento": tipo_financiamento,
        "prazo": prazo,
        "renda": renda_raw,
    }

    if liberar_sem_pagamento:
        if token:
            registrar_pagamento_pendente(
                token,
                dados_relatorio=dados_relatorio,
            )
            confirmar_pagamento(token)
        else:
            _, token = criar_pagamento(
                0,
                dados_relatorio=dados_relatorio,
            )
            confirmar_pagamento(token)
    else:
        if token:
            registrar_pagamento_pendente(
                token,
                dados_relatorio=dados_relatorio,
            )
        else:
            _, token = criar_pagamento(3990, dados_relatorio=dados_relatorio)

    pago = True if liberar_sem_pagamento else status_pagamento(token) == "pago"
    link_pagamento = f"/pagar?token={token}"
    score_valor = score.get("valor", 0)
    resumo_decisao = _resumo_decisao(score_valor)

    tabela_indices = [
        {
            "indice": "TR",
            "leitura": (
                "Taxa de Referencia historicamente baixa em "
                "varios ciclos."
            ),
            "impacto": (
                "Parcela tende a oscilar menos, mas depende "
                "da taxa do banco."
            ),
        },
        {
            "indice": "IPCA",
            "leitura": "Indice de inflacao oficial.",
            "impacto": (
                "Parcela inicial menor, com risco de subir "
                "em cenarios inflacionarios."
            ),
        },
        {
            "indice": "CDI / Selic",
            "leitura": "Indexadores de custo de dinheiro na economia.",
            "impacto": "Afetam custo de credito e condicoes de renegociacao.",
        },
    ]

    tabela_bancos = [
        {
            "instituicao": "Caixa",
            "sistemas": "SAC / PRICE",
            "observacao": "Maior capilaridade e linhas habitacionais amplas.",
        },
        {
            "instituicao": "Banco do Brasil",
            "sistemas": "SAC / PRICE",
            "observacao": "Boas opcoes para correntista com relacionamento.",
        },
        {
            "instituicao": "Itaú / Bradesco / Santander",
            "sistemas": "SAC / PRICE",
            "observacao": (
                "Competicao de taxa via relacionamento e "
                "perfil de renda."
            ),
        },
    ]

    tabela_compra_taxas = [
        {
            "item": "ITBI",
            "faixa": "2% a 3%",
            "observacao": "Variacao por municipio.",
        },
        {
            "item": "Escritura e registro",
            "faixa": "0,8% a 1,5%",
            "observacao": "Custos cartoriais e registro final.",
        },
        {
            "item": "Avaliacao e taxas bancarias",
            "faixa": "R$ 2 mil a R$ 6 mil",
            "observacao": "Depende do banco e ticket do imovel.",
        },
    ]

    tabela_urbanismo = [
        {
            "tema": "Zoneamento de uso",
            "o_que_ver": "Se uso residencial/comercial e permitido na zona.",
            "risco": "Uso nao compativel pode travar projeto ou licenca.",
        },
        {
            "tema": "Taxa de ocupacao e recuos",
            "o_que_ver": "Limite de area ocupada e afastamentos obrigatorios.",
            "risco": "Projeto fora da regra gera retrabalho e custo extra.",
        },
        {
            "tema": "Permeabilidade do lote",
            "o_que_ver": "Percentual minimo de solo permeavel.",
            "risco": "Nao atendimento impede aprovacao e habite-se.",
        },
        {
            "tema": "Gabarito / altura",
            "o_que_ver": "Limite de pavimentos permitido para a zona.",
            "risco": "Restricao afeta viabilidade economica do projeto.",
        },
    ]

    tabela_construcao_taxas = [
        {
            "item": "Projeto + ART/RRT",
            "faixa": "3% a 8% da obra",
            "observacao": (
                "Arquitetura, engenharia e "
                "responsabilidade tecnica."
            ),
        },
        {
            "item": "Alvara e aprovacoes",
            "faixa": "R$ 1 mil a R$ 8 mil",
            "observacao": "Prefeitura e eventuais taxas urbanisticas.",
        },
        {
            "item": "Ligacoes e regularizacao final",
            "faixa": "R$ 3 mil a R$ 15 mil",
            "observacao": "Agua, energia, cartorio e habite-se.",
        },
    ]

    roteiro_profissionais = [
        {
            "profissional": "Corretor",
            "perguntas": [
                "Qual o historico real de liquidez desta micro-regiao?",
                "Quais imoveis comparaveis venderam nos ultimos 6 meses?",
                "Qual o principal risco oculto percebido pelos compradores?",
            ],
        },
        {
            "profissional": "Engenheiro/Arquiteto",
            "perguntas": [
                "Quais patologias mais provaveis neste tipo de imovel/solo?",
                (
                    "Ha sinais de recalque, umidade, fissura "
                    "ou reforma mal executada?"
                ),
                (
                    "O projeto proposto respeita recuos, "
                    "ocupacao e permeabilidade?"
                ),
            ],
        },
        {
            "profissional": "Correspondente bancario",
            "perguntas": [
                "Qual CET final da operacao e nao apenas taxa nominal?",
                "Como ficam parcelas em cenario de inflacao mais alta?",
                "Quais seguros/tarifas obrigatorios entram no custo total?",
            ],
        },
    ]

    checklist_bolso = [
        "Confirmar matricula atualizada e cadeia de propriedade.",
        "Checar certidoes negativas e pendencias urbanisticas.",
        "Validar zoneamento e parametros de ocupacao do lote.",
        "Conferir custo total (imovel + taxas + adequacoes + reserva).",
        "Avaliar ruido, mobilidade e seguranca em dois horarios.",
        "Comparar pelo menos 3 alternativas de bairro/ticket.",
        "Fechar proposta apenas com simulacao financeira completa.",
    ]

    area_ref = area if area > 0 else 180.0
    metodologias = _custo_m2_metodologia(cub, padrao)
    tabela_metodologias = []
    for linha in metodologias:
        custo_total = linha["m2"] * area_ref
        percentual = (custo_total / orcamento * 100) if orcamento > 0 else 0
        area_max = (orcamento / linha["m2"]) if linha["m2"] > 0 else 0
        tabela_metodologias.append(
            {
                "metodologia": linha["metodologia"],
                "custo_m2": float_para_moeda(linha["m2"]),
                "custo_total": float_para_moeda(custo_total),
                "percentual_orcamento": percentual,
                "area_max_orcamento": round(area_max, 1),
                "faixa_prazo": linha["faixa_prazo"],
                "fonte_preco": linha["fonte_preco"],
            }
        )

    tabela_spt = [
        {
            "faixa": "SPT < 8 golpes",
            "leitura": (
                "Solo pouco resistente para fundacoes rasas "
                "economicas."
            ),
            "fundacao_tendencia": "Estacas escavadas ou helice continua.",
            "impacto": "Aumenta custo de fundacao e prazo.",
        },
        {
            "faixa": "SPT 8 a 15 golpes",
            "leitura": "Faixa intermediaria com boa relacao tecnica x custo.",
            "fundacao_tendencia": "Sapata/radier bem dimensionados.",
            "impacto": "Faixa geralmente mais economica para casas.",
        },
        {
            "faixa": "SPT 15 a 25 golpes",
            "leitura": "Boa capacidade de suporte com seguranca estrutural.",
            "fundacao_tendencia": "Sapata isolada, vigas baldrame, radier.",
            "impacto": "Cenario favoravel para custo de fundacao.",
        },
        {
            "faixa": "SPT > 30 golpes",
            "leitura": "Solo muito compacto/duro.",
            "fundacao_tendencia": "Fundacao rasa robusta ou estaca curta.",
            "impacto": (
                "Pode reduzir volume estrutural, mas encarecer "
                "escavacao."
            ),
        },
    ]

    tabela_fundacoes = [
        {
            "tipo": "Sapata isolada + baldrame",
            "uso": (
                "Casas terreas/sobrados com solo de media "
                "a boa capacidade."
            ),
            "vantagem": "Boa economicidade quando SPT e favoravel.",
        },
        {
            "tipo": "Radier",
            "uso": "Lotes planos e cargas distribuidas.",
            "vantagem": "Rapidez executiva e controle de recalques.",
        },
        {
            "tipo": "Estaca escavada",
            "uso": "Solo com baixa capacidade superficial.",
            "vantagem": "Maior seguranca em cenarios de SPT baixo.",
        },
        {
            "tipo": "Helice continua monitorada",
            "uso": "Cargas maiores e controle tecnico elevado.",
            "vantagem": "Produtividade com bom desempenho geotecnico.",
        },
    ]

    quadro_clima = [
        {
            "tema": "Temperatura media anual (Cuiaba)",
            "dado": "Aproximadamente 27 C a 28 C",
            "impacto": "Planejar conforto termico e produtividade da equipe.",
        },
        {
            "tema": "Periodo mais quente",
            "dado": "Agosto a Outubro",
            "impacto": "Reforcar estrategia de sombra, hidratacao e jornada.",
        },
        {
            "tema": "Maior incidencia pluviometrica",
            "dado": "Outubro a Abril (pico entre Dezembro e Marco)",
            "impacto": "Eleva risco de atraso em terraplenagem e estrutura.",
        },
        {
            "tema": "Periodo mais seco",
            "dado": "Maio a Setembro",
            "impacto": "Melhor janela para inicio e ritmo de obra.",
        },
    ]

    tabela_prazo_faixa = [
        {
            "cenario": "Ate 120 m2 - acabamento economico/medio",
            "convencional": "7 a 10 meses",
            "estrutural": "6 a 9 meses",
            "steel_frame": "5 a 8 meses",
            "eps": "5 a 8 meses",
        },
        {
            "cenario": "120 a 220 m2 - acabamento medio",
            "convencional": "9 a 13 meses",
            "estrutural": "8 a 11 meses",
            "steel_frame": "6 a 9 meses",
            "eps": "7 a 10 meses",
        },
        {
            "cenario": "Acima de 220 m2 - medio/alto padrao",
            "convencional": "12 a 18 meses",
            "estrutural": "10 a 15 meses",
            "steel_frame": "8 a 12 meses",
            "eps": "9 a 13 meses",
        },
    ]

    hoje = datetime.now()
    ano_inicio = hoje.year if hoje.month <= 8 else hoje.year + 1
    mes_inicio = 5  # maio
    calendario_exec = []
    for linha in metodologias:
        faixa = linha["faixa_prazo"]
        try:
            partes = [int(v) for v in re.findall(r"\d+", faixa)]
            prazo_medio = int((partes[0] + partes[1]) / 2)
        except Exception:
            prazo_medio = 10
        ano_fim, mes_fim = _somar_meses(ano_inicio, mes_inicio, prazo_medio)
        calendario_exec.append(
            {
                "metodologia": linha["metodologia"],
                "inicio_sugerido": f"{_mes_pt(mes_inicio)}/{ano_inicio}",
                "entrega_estimativa": f"{_mes_pt(mes_fim)}/{ano_fim}",
                "prazo_medio_meses": prazo_medio,
            }
        )

    ressalva_bloco_tecnico = (
        "Quadros tecnicos orientativos: podem variar por projeto, solo, "
        "logistica, licencas, mao de obra, contratos e condicoes de mercado. "
        "Nao substituem sondagem, projeto estrutural e parecer profissional."
    )

    tabela_apartamento_custos = [
        {
            "item": "Condominio mensal",
            "faixa": "R$ 5 a R$ 14 por m2 de area privativa",
            "impacto": "Pressiona custo fixo mensal de ocupacao.",
            "fonte": "Base Lokáo e praticas de mercado local",
        },
        {
            "item": "Fundo de reserva/obras",
            "faixa": "5% a 15% sobre a cota condominial",
            "impacto": "Pode elevar despesa em periodos de modernizacao.",
            "fonte": "Convencao condominial + jurisprudencia setorial",
        },
        {
            "item": "IPTU + taxa de lixo",
            "faixa": "Variavel por metragem e localizacao",
            "impacto": "Encargo anual recorrente no custo total.",
            "fonte": "Prefeitura de Cuiaba (tributos imobiliarios)",
        },
        {
            "item": "Reforma interna pos-compra",
            "faixa": "2% a 10% do valor de aquisicao",
            "impacto": "Ajuste de layout, acabamentos e personalizacao.",
            "fonte": "SINAPI/IBGE + historico de obras residenciais",
        },
    ]

    fontes_publicas = [
        {
            "tema": "Custo da construcao (SINAPI)",
            "url": (
                "https://agenciadenoticias.ibge.gov.br/agencia-noticias/"
                "2012-agencia-de-noticias/noticias/42469-sinapi-custo-"
                "nacional-da-construcao-civil-sobe-0-30-em-outubro"
            ),
        },
        {
            "tema": "CUB e referencia setorial",
            "url": "https://www.cbicdados.com.br/menu/cub",
        },
        {
            "tema": "Clima e monitoramento (INMET)",
            "url": (
                "https://portal.inmet.gov.br/noticias/boletim-"
                "agrometeorologico-dezembro-2025"
            ),
        },
        {
            "tema": "Benchmark Steel Frame (mercado)",
            "url": (
                "https://casaeconstrucao.org/construcao/steel-frame/"
                "preco-m2/"
            ),
        },
    ]

    projecoes_compra = []
    for linha in financeiro.get("projecoes_compra", []):
        projecoes_compra.append(
            {
                "cenario": linha.get("cenario", ""),
                "itbi": float_para_moeda(linha.get("itbi", 0)),
                "cartorio": float_para_moeda(linha.get("cartorio", 0)),
                "bancario": float_para_moeda(linha.get("bancario", 0)),
                "adequacoes": float_para_moeda(linha.get("adequacoes", 0)),
                "reserva": float_para_moeda(linha.get("reserva", 0)),
                "total": float_para_moeda(linha.get("total", 0)),
                "percentual_orcamento": linha.get("percentual_orcamento", 0),
                "saldo_vs_orcamento": float_para_moeda(
                    linha.get("saldo_vs_orcamento", 0)
                ),
            }
        )

    projecoes_construcao = []
    for linha in financeiro.get("projecoes_construcao", []):
        projecoes_construcao.append(
            {
                "cenario": linha.get("cenario", ""),
                "projetos": float_para_moeda(linha.get("projetos", 0)),
                "aprovacoes": float_para_moeda(linha.get("aprovacoes", 0)),
                "infraestrutura": float_para_moeda(
                    linha.get("infraestrutura", 0)
                ),
                "contingencia": float_para_moeda(linha.get("contingencia", 0)),
                "total": float_para_moeda(linha.get("total", 0)),
                "percentual_orcamento": linha.get("percentual_orcamento", 0),
                "saldo_vs_orcamento": float_para_moeda(
                    linha.get("saldo_vs_orcamento", 0)
                ),
            }
        )

    return {
        "nome": nome,
        "bairro": bairro,
        "tipo_imovel": tipo_imovel,
        "padrao": padrao,
        "orcamento": orcamento_raw,
        "valor_imovel": valor_imovel_raw,
        "orcamento_formatado": orcamento_raw,
        "valor_imovel_formatado": valor_imovel_raw,
        "entrada_estimada": (
            float_para_moeda(entrada_estimada) if entrada_estimada else None
        ),
        "parcela_estimada": (
            float_para_moeda(parcela_estimada) if parcela_estimada else None
        ),
        "cub": float_para_moeda(cub) if cub else "Nao informado",
        "cub_competencia": contexto_cub.get("competencia_br", ""),
        "cub_competencia_curta": _formatar_competencia_curta(
            contexto_cub.get("competencia", "")
        ),
        "cub_cidade": contexto_cub.get("cidade", "Cuiaba-MT"),
        "cub_padrao_aplicado": contexto_cub.get("padrao", ""),
        "fonte_cub": contexto_cub.get("fonte", "Nao informado"),
        "valor_m2_compra": (
            float_para_moeda(valor_m2_compra)
            if valor_m2_compra else "Nao informado"
        ),
        "custo_estimado": (
            float_para_moeda(custo_estimado)
            if custo_estimado else "Nao informado"
        ),
        "fonte_valor_m2_compra": contexto_m2.get("fonte", "Nao informado"),
        "data_valor_m2_compra": _formatar_data_iso_br(
            contexto_m2.get("data_referencia", "")
        ),
        "score": score,
        "texto_compatibilidade": texto_compatibilidade(score.get("valor", 0)),
        "texto_financeiro": texto_financeiro(score.get("valor", 0), orcamento),
        "texto_urbano": texto_urbano(score.get("valor", 0)),
        "financeiro_mensagens": financeiro.get("mensagens", []),
        "percentual_ticket_orcamento": financeiro.get(
            "percentual_ticket_orcamento", 0
        ),
        "comprometimento_renda_estimado": financeiro.get(
            "comprometimento_renda_estimado", 0
        ),
        "projecoes_compra": projecoes_compra,
        "projecoes_construcao": projecoes_construcao,
        "grafico_score_url": grafico_score_url,
        "grafico_financeiro_url": grafico_financeiro_url,
        "insight_score_grafico": _insight_score(score.get("valor", 0)),
        "insight_financeiro_grafico": _insight_financeiro(
            orcamento,
            valor_imovel,
        ),
        "resumo_decisao": resumo_decisao,
        "tabela_indices": tabela_indices,
        "tabela_bancos": tabela_bancos,
        "tabela_compra_taxas": tabela_compra_taxas,
        "tabela_urbanismo": tabela_urbanismo,
        "tabela_construcao_taxas": tabela_construcao_taxas,
        "tabela_spt": tabela_spt,
        "tabela_fundacoes": tabela_fundacoes,
        "tabela_metodologias": tabela_metodologias,
        "quadro_clima": quadro_clima,
        "tabela_prazo_faixa": tabela_prazo_faixa,
        "calendario_exec": calendario_exec,
        "area_ref_metodologias": round(area_ref, 1),
        "ressalva_bloco_tecnico": ressalva_bloco_tecnico,
        "is_apartamento": is_apartamento,
        "financiar": financiar,
        "tabela_apartamento_custos": tabela_apartamento_custos,
        "fontes_publicas": fontes_publicas,
        "roteiro_profissionais": roteiro_profissionais,
        "checklist_bolso": checklist_bolso,
        "tipo_financiamento": tipo_financiamento,
        "prazo": prazo,
        "renda_formatada": (
            float_para_moeda(renda) if renda > 0 else "Nao informado"
        ),
        "sugestoes": sugestoes,
        "modo_teste": liberar_sem_pagamento,
        "piloto_feedback_url": (
            f"/piloto/feedback?token={token}" if liberar_sem_pagamento else ""
        ),
        "pago": pago,
        "liberado": pago,
        "token": token,
        "link_pagamento": link_pagamento,
        "is_pdf": False,
        "report_version": "Lokáo 1.0.1",
        "generated_at": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "fontes_metodologia": [
            "Base urbana municipal e dados internos Lokáo",
            (
                "Referencia de valor m2: "
                f"{contexto_m2.get('fonte', 'Nao informado')}"
            ),
            (
                "Referencia de CUB: "
                f"{contexto_cub.get('cidade', 'Cuiaba-MT')} "
                f"({contexto_cub.get('competencia_br', 'n/d')})"
            ),
            (
                "Clima de Cuiaba-MT: padrao sazonal quente com periodo "
                "chuvoso concentrado entre outubro e abril"
            ),
            (
                "Benchmarks setoriais para metodologia construtiva "
                "(faixas orientativas de mercado)"
            ),
            "Leitura de compatibilidade entre perfil, bairro "
            "e capacidade financeira",
            "Premissas de custo por m2 e simulacoes orientativas de mercado",
        ],
    }


@router.route("/")
def index():
    df = carregar_bairros()
    lista_bairros = sorted(
        df["bairro"].dropna().astype(str).str.strip().unique().tolist()
    )
    return render_template(
        "index.html",
        bairros=lista_bairros,
        modo_teste=False,
        janela=None,
    )


def _ip_cliente():
    xff = request.headers.get("X-Forwarded-For", "").strip()
    if xff:
        return xff.split(",")[0].strip()
    return request.remote_addr or ""


def _texto_limpo(texto, limite=1000):
    return str(texto or "").strip().replace("\x00", "")[:limite]


@router.route("/piloto")
def piloto():
    df = carregar_bairros()
    lista_bairros = sorted(
        df["bairro"].dropna().astype(str).str.strip().unique().tolist()
    )
    janela = obter_janela_teste()
    return render_template(
        "index.html",
        bairros=lista_bairros,
        modo_teste=True,
        janela=janela,
    )


@router.route("/piloto/feedback", methods=["GET", "POST"])
def piloto_feedback():
    token = _texto_limpo(request.values.get("token", ""), 120)
    if not token or not token_piloto_valido(token):
        abort(404)

    enviado = feedback_ja_enviado(token)
    salvo = False
    if request.method == "POST" and not enviado:
        respostas = {
            "clareza": _texto_limpo(request.form.get("clareza", ""), 30),
            "utilidade": _texto_limpo(request.form.get("utilidade", ""), 30),
            "confianca": _texto_limpo(request.form.get("confianca", ""), 30),
            "nps": _texto_limpo(request.form.get("nps", ""), 4),
            "tempo_form": _texto_limpo(request.form.get("tempo_form", ""), 30),
            "uso_relatorio": _texto_limpo(
                request.form.get("uso_relatorio", ""),
                30,
            ),
            "etapa_mais_util": _texto_limpo(
                request.form.get("etapa_mais_util", ""),
                50,
            ),
            "info_faltante": _texto_limpo(
                request.form.get("info_faltante", ""),
                220,
            ),
            "valor_percebido": _texto_limpo(
                request.form.get("valor_percebido", ""),
                400,
            ),
            "faltou_algo": _texto_limpo(
                request.form.get("faltou_algo", ""),
                600,
            ),
            "recomendaria": _texto_limpo(
                request.form.get("recomendaria", ""),
                20,
            ),
        }
        resultado = registrar_feedback(
            token=token,
            respostas=respostas,
            ip=_ip_cliente(),
            ua=request.headers.get("User-Agent", ""),
        )
        salvo = bool(resultado.get("ok"))
        enviado = enviado or salvo

    return render_template(
        "piloto_feedback.html",
        token=token,
        enviado=enviado,
        salvo=salvo,
    )


@router.route("/piloto/metricas")
def piloto_metricas():
    chave = _texto_limpo(request.args.get("chave", ""), 160)
    chave_esperada = os.getenv("LOKAO_METRICAS_KEY", "").strip()
    if not chave_esperada or chave != chave_esperada:
        abort(404)
    return jsonify(metricas_piloto())


@router.route("/piloto/admin")
def piloto_admin():
    chave = _texto_limpo(request.args.get("chave", ""), 160)
    chave_esperada = os.getenv("LOKAO_METRICAS_KEY", "").strip()
    if not chave_esperada or chave != chave_esperada:
        abort(404)
    painel = dados_admin_piloto()
    return render_template(
        "piloto_admin.html",
        painel=painel,
    )


@router.route("/relatorio", methods=["GET", "POST"])
def relatorio():
    token = _texto_limpo(request.values.get("token", ""), 120)
    piloto_ativo = str(request.values.get("piloto", "")).strip() == "1"

    if token and token_piloto_valido(token):
        contexto = _montar_contexto_relatorio(
            token_forcado=token,
            liberar_sem_pagamento=True,
        )
        return render_template("relatorio.html", **contexto)

    if piloto_ativo:
        cpf = _texto_limpo(request.values.get("cpf", ""), 20)
        resultado = registrar_geracao_unica(
            cpf=cpf,
            ip=_ip_cliente(),
            ua=request.headers.get("User-Agent", ""),
        )
        if not resultado.get("ok"):
            return render_template(
                "piloto_bloqueado.html",
                motivo=resultado.get("motivo", "erro"),
                token_existente=resultado.get("token", ""),
            )
        contexto = _montar_contexto_relatorio(
            token_forcado=resultado.get("token", ""),
            liberar_sem_pagamento=True,
        )
        return render_template("relatorio.html", **contexto)

    contexto = _montar_contexto_relatorio()
    if not contexto["liberado"]:
        return render_template("paywall.html", **contexto)
    return render_template("relatorio.html", **contexto)


@router.route("/relatorio/pdf")
def relatorio_pdf():
    contexto = _montar_contexto_relatorio()
    if not contexto["liberado"]:
        abort(403, description="Pagamento necessario para gerar PDF.")

    html = render_template(
        "relatorio.html",
        **{**contexto, "liberado": True, "is_pdf": True},
    )
    resposta = gerar_pdf(html, "relatorio_lokao.pdf")
    if resposta is None:
        abort(500, description="Falha ao gerar PDF.")
    return resposta
