import json
from datetime import datetime
from pathlib import Path


_CUB_PATH = Path(__file__).resolve().parents[1] / "data" / "cub_cuiaba.json"


def _normalizar_padrao(padrao):
    txt = str(padrao or "").strip().lower()
    if txt in {"alto", "alto padrao", "premium"}:
        return "alto"
    if txt in {"medio", "intermediario"}:
        return "medio"
    return "economico"


def _competencia_referencia():
    """
    CUB divulgado no mes corrente normalmente referencia o mes anterior.
    """
    hoje = datetime.now()
    ano = hoje.year
    mes = hoje.month - 1
    if mes == 0:
        mes = 12
        ano -= 1
    return f"{ano:04d}-{mes:02d}"


def _formatar_competencia_br(competencia):
    texto = str(competencia or "")
    if len(texto) != 7 or "-" not in texto:
        return texto
    ano, mes = texto.split("-", 1)
    return f"{mes}/{ano}"


def _carregar_serie():
    if not _CUB_PATH.exists():
        return {
            "cidade": "Cuiaba-MT",
            "fonte": "Base referencial Lokao",
            "series": [],
        }
    try:
        return json.loads(_CUB_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {
            "cidade": "Cuiaba-MT",
            "fonte": "Base referencial Lokao",
            "series": [],
        }


def obter_cub_cuiaba(padrao, competencia=None):
    """
    Retorna CUB referencia por competencia e padrao.
    Se nao houver a competencia solicitada, usa a ultima disponivel.
    """

    alvo_padrao = _normalizar_padrao(padrao)
    comp = competencia or _competencia_referencia()
    base = _carregar_serie()
    serie = sorted(
        base.get("series", []),
        key=lambda x: x.get("competencia", ""),
    )

    if not serie:
        return {
            "valor": 0.0,
            "padrao": alvo_padrao,
            "competencia": "",
            "competencia_br": "",
            "cidade": base.get("cidade", "Cuiaba-MT"),
            "fonte": base.get("fonte", "Base referencial Lokao"),
            "metodo": "sem_base",
        }

    candidatos = [
        item for item in serie
        if item.get("competencia", "") <= comp
    ]
    registro = candidatos[-1] if candidatos else serie[-1]
    valor = float(registro.get(alvo_padrao, 0) or 0)

    return {
        "valor": valor,
        "padrao": alvo_padrao,
        "competencia": registro.get("competencia", ""),
        "competencia_br": _formatar_competencia_br(
            registro.get("competencia", "")
        ),
        "cidade": base.get("cidade", "Cuiaba-MT"),
        "fonte": base.get("fonte", "Base referencial Lokao"),
        "metodo": "serie_mensal",
    }
