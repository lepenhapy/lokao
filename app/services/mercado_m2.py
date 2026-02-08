import json
import unicodedata
from datetime import datetime, timedelta
from pathlib import Path

from app.services.scraper_valor_m2 import buscar_valor_m2_viva_real
from app.utils.formatacao import moeda_para_float


CACHE_PATH = (
    Path(__file__).resolve().parents[1] / "data" / "mercado_m2_cache.json"
)


def _normalizar_chave(texto):
    texto = str(texto or "").strip().lower()
    texto = "".join(
        c for c in unicodedata.normalize("NFKD", texto)
        if not unicodedata.combining(c)
    )
    return " ".join(texto.split())


def _carregar_cache():
    if not CACHE_PATH.exists():
        return {}
    try:
        return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _salvar_cache(cache):
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(
        json.dumps(cache, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _cache_valido(registro, max_age_hours):
    coletado_em = str(registro.get("coletado_em", "")).strip()
    if not coletado_em:
        return False
    try:
        coleta = datetime.fromisoformat(coletado_em)
    except ValueError:
        return False
    return datetime.now() - coleta <= timedelta(hours=max_age_hours)


def obter_contexto_m2(
    dados_bairro,
    bairro,
    tipo_imovel,
    usar_coleta_externa=True,
    cache_horas=168,
    cooldown_falha_horas=6,
):
    """
    Resolve valor de m2 com estrategia segura:
    1) cache recente
    2) coleta online (quando habilitado)
    3) base interna da planilha
    """

    valor_planilha = moeda_para_float(dados_bairro.get("valor_m2_medio"))
    origem_planilha = str(dados_bairro.get("origem_valor", "")).strip()
    if not origem_planilha:
        origem_planilha = "base_interna"

    chave = f"{_normalizar_chave(bairro)}|{_normalizar_chave(tipo_imovel)}"
    cache = _carregar_cache()
    registro = cache.get(chave, {})

    if registro:
        if _cache_valido(registro, cache_horas):
            valor_cache = moeda_para_float(registro.get("valor"))
            if valor_cache > 0:
                return {
                    "valor": valor_cache,
                    "fonte": "Base Lokao",
                    "data_referencia": registro.get("coletado_em", ""),
                    "origem": "base_lokao",
                }
        if registro.get("status") == "falha" and _cache_valido(
            registro,
            cooldown_falha_horas,
        ):
            usar_coleta_externa = False

    if usar_coleta_externa and bairro:
        valor_coleta = buscar_valor_m2_viva_real(
            bairro,
            tipo_imovel=tipo_imovel or "casa",
            timeout=4,
        )
        if valor_coleta:
            agora = datetime.now().isoformat(timespec="seconds")
            cache[chave] = {
                "valor": valor_coleta,
                "fonte": "Base Lokao",
                "coletado_em": agora,
            }
            _salvar_cache(cache)
            return {
                "valor": float(valor_coleta),
                "fonte": "Base Lokao",
                "data_referencia": agora,
                "origem": "base_lokao",
            }
        agora = datetime.now().isoformat(timespec="seconds")
        cache[chave] = {
            "status": "falha",
            "fonte": "falha_coleta",
            "coletado_em": agora,
            "cooldown_horas": cooldown_falha_horas,
        }
        _salvar_cache(cache)

    if valor_planilha > 0:
        return {
            "valor": valor_planilha,
            "fonte": "Base Lokao",
            "data_referencia": "",
            "origem": "base_lokao",
        }

    return {
        "valor": 0.0,
        "fonte": "Nao informado",
        "data_referencia": "",
        "origem": "fallback",
    }
