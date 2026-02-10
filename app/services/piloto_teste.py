import hashlib
import json
import os
import secrets
from datetime import datetime, timedelta
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
LEGACY_ARQUIVO = BASE_DIR / "data" / "piloto_teste.json"
DATA_DIR = Path(
    os.getenv("LOKAO_DATA_DIR", str(BASE_DIR / "data"))
).resolve()
ARQUIVO = DATA_DIR / "piloto_teste.json"
ARQUIVO_EVENTOS = DATA_DIR / "piloto_eventos.jsonl"
DURACAO_DIAS = 2


def _agora():
    return datetime.utcnow()


def _iso(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_iso(valor):
    try:
        return datetime.strptime(str(valor), "%Y-%m-%dT%H:%M:%SZ")
    except Exception:
        return None


def _estado_inicial():
    return {
        "window_start": "",
        "window_end": "",
        "cpfs": {},
        "tokens": {},
        "feedback": [],
        "eventos": [],
    }


def _carregar():
    if not ARQUIVO.exists() and LEGACY_ARQUIVO.exists():
        try:
            dados_legado = json.loads(
                LEGACY_ARQUIVO.read_text(encoding="utf-8")
            )
            _salvar(dados_legado)
            return dados_legado
        except Exception:
            pass
    if not ARQUIVO.exists():
        return _estado_inicial()
    try:
        return json.loads(ARQUIVO.read_text(encoding="utf-8"))
    except Exception:
        return _estado_inicial()


def _salvar(dados):
    ARQUIVO.parent.mkdir(parents=True, exist_ok=True)
    tmp = ARQUIVO.with_suffix(".tmp")
    tmp.write_text(
        json.dumps(dados, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    tmp.replace(ARQUIVO)


def _append_evento(evento):
    ARQUIVO_EVENTOS.parent.mkdir(parents=True, exist_ok=True)
    with ARQUIVO_EVENTOS.open("a", encoding="utf-8") as fp:
        fp.write(json.dumps(evento, ensure_ascii=False) + "\n")


def _normalizar_cpf(cpf):
    return "".join(ch for ch in str(cpf or "") if ch.isdigit())


def _validar_cpf(cpf):
    if len(cpf) != 11:
        return False
    if cpf == cpf[0] * 11:
        return False

    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    d1 = (soma * 10) % 11
    d1 = 0 if d1 == 10 else d1
    if d1 != int(cpf[9]):
        return False

    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    d2 = (soma * 10) % 11
    d2 = 0 if d2 == 10 else d2
    return d2 == int(cpf[10])


def _hash_cpf(cpf_limpo):
    salt = os.getenv("LOKAO_CPF_SALT", "lokao-piloto-v1")
    texto = f"{salt}:{cpf_limpo}"
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def _hash_ip(ip):
    txt = str(ip or "").strip()
    if not txt:
        return ""
    return hashlib.sha256(txt.encode("utf-8")).hexdigest()


def _garantir_janela(dados):
    inicio = _parse_iso(dados.get("window_start", ""))
    fim = _parse_iso(dados.get("window_end", ""))
    if inicio and fim:
        return dados

    agora = _agora()
    dados["window_start"] = _iso(agora)
    dados["window_end"] = _iso(agora + timedelta(days=DURACAO_DIAS))
    return dados


def _janela_ativa(dados):
    agora = _agora()
    inicio = _parse_iso(dados.get("window_start", ""))
    fim = _parse_iso(dados.get("window_end", ""))
    if not inicio or not fim:
        return False
    return inicio <= agora <= fim


def _registrar_evento(dados, tipo, cpf_hash="", token="", ip="", ua=""):
    evento = {
        "ts": _iso(_agora()),
        "tipo": tipo,
        "cpf_hash": cpf_hash,
        "token": token,
        "ip_hash": _hash_ip(ip),
        "ua": str(ua or "")[:180],
    }
    dados.setdefault("eventos", []).append(evento)
    _append_evento(evento)


def obter_janela_teste():
    dados = _garantir_janela(_carregar())
    _salvar(dados)
    return {
        "inicio": dados.get("window_start", ""),
        "fim": dados.get("window_end", ""),
        "ativo": _janela_ativa(dados),
    }


def registrar_geracao_unica(cpf, ip="", ua=""):
    dados = _garantir_janela(_carregar())
    if not _janela_ativa(dados):
        _registrar_evento(dados, "janela_encerrada", ip=ip, ua=ua)
        _salvar(dados)
        return {"ok": False, "motivo": "janela_encerrada"}

    cpf_limpo = _normalizar_cpf(cpf)
    if not _validar_cpf(cpf_limpo):
        _registrar_evento(dados, "cpf_invalido", ip=ip, ua=ua)
        _salvar(dados)
        return {"ok": False, "motivo": "cpf_invalido"}

    cpf_hash = _hash_cpf(cpf_limpo)
    registro = dados.setdefault("cpfs", {}).get(cpf_hash)
    if registro and registro.get("report_token"):
        token_existente = registro.get("report_token", "")
        _registrar_evento(
            dados,
            "tentativa_repetida",
            cpf_hash=cpf_hash,
            token=token_existente,
            ip=ip,
            ua=ua,
        )
        _salvar(dados)
        return {
            "ok": False,
            "motivo": "ja_utilizado",
            "token": token_existente,
        }

    token = secrets.token_urlsafe(24)
    dados["cpfs"][cpf_hash] = {
        "report_token": token,
        "criado_em": _iso(_agora()),
        "feedback_enviado_em": "",
    }
    dados.setdefault("tokens", {})[token] = cpf_hash
    _registrar_evento(
        dados,
        "relatorio_gerado",
        cpf_hash=cpf_hash,
        token=token,
        ip=ip,
        ua=ua,
    )
    _salvar(dados)
    return {"ok": True, "token": token}


def token_piloto_valido(token):
    dados = _carregar()
    cpf_hash = dados.get("tokens", {}).get(str(token or ""))
    if not cpf_hash:
        return False
    return cpf_hash in dados.get("cpfs", {})


def feedback_ja_enviado(token):
    dados = _carregar()
    cpf_hash = dados.get("tokens", {}).get(str(token or ""))
    if not cpf_hash:
        return False
    item = dados.get("cpfs", {}).get(cpf_hash, {})
    return bool(item.get("feedback_enviado_em"))


def registrar_feedback(token, respostas, ip="", ua=""):
    dados = _carregar()
    token = str(token or "").strip()
    cpf_hash = dados.get("tokens", {}).get(token)
    if not cpf_hash:
        return {"ok": False, "motivo": "token_invalido"}

    if feedback_ja_enviado(token):
        _registrar_evento(
            dados,
            "feedback_repetido",
            cpf_hash=cpf_hash,
            token=token,
            ip=ip,
            ua=ua,
        )
        _salvar(dados)
        return {"ok": False, "motivo": "feedback_repetido"}

    item = {
        "token": token,
        "cpf_hash": cpf_hash,
        "ts": _iso(_agora()),
        "respostas": respostas,
    }
    dados.setdefault("feedback", []).append(item)
    dados["cpfs"][cpf_hash]["feedback_enviado_em"] = _iso(_agora())
    _registrar_evento(
        dados,
        "feedback_enviado",
        cpf_hash=cpf_hash,
        token=token,
        ip=ip,
        ua=ua,
    )
    _salvar(dados)
    return {"ok": True}


def metricas_piloto():
    dados = _garantir_janela(_carregar())
    cpfs = dados.get("cpfs", {})
    total_gerados = sum(1 for _, v in cpfs.items() if v.get("report_token"))
    total_feedback = sum(
        1 for _, v in cpfs.items() if v.get("feedback_enviado_em")
    )
    taxa = (
        round((total_feedback / total_gerados) * 100, 1)
        if total_gerados > 0 else 0.0
    )
    return {
        "janela": {
            "inicio": dados.get("window_start", ""),
            "fim": dados.get("window_end", ""),
            "ativo": _janela_ativa(dados),
        },
        "total_gerados": total_gerados,
        "total_feedback": total_feedback,
        "taxa_feedback_pct": taxa,
        "eventos_total": len(dados.get("eventos", [])),
    }


def dados_admin_piloto(limite_feedback=30, limite_eventos=60):
    dados = _garantir_janela(_carregar())
    metricas = metricas_piloto()

    feedback = list(dados.get("feedback", []))[-limite_feedback:]
    feedback_view = []
    for item in reversed(feedback):
        feedback_view.append(
            {
                "ts": item.get("ts", ""),
                "token": str(item.get("token", ""))[:8],
                "respostas": item.get("respostas", {}),
            }
        )

    eventos = list(dados.get("eventos", []))[-limite_eventos:]
    eventos_view = []
    for ev in reversed(eventos):
        eventos_view.append(
            {
                "ts": ev.get("ts", ""),
                "tipo": ev.get("tipo", ""),
                "token": str(ev.get("token", ""))[:8],
            }
        )

    return {
        "metricas": metricas,
        "feedback": feedback_view,
        "eventos": eventos_view,
    }


def liberar_cpf_piloto(cpf):
    cpf_limpo = _normalizar_cpf(cpf)
    if not _validar_cpf(cpf_limpo):
        return {"ok": False, "motivo": "cpf_invalido"}

    dados = _carregar()
    cpf_hash = _hash_cpf(cpf_limpo)
    registro = dados.get("cpfs", {}).pop(cpf_hash, None)
    if not registro:
        return {"ok": False, "motivo": "cpf_nao_encontrado"}

    token = registro.get("report_token", "")
    if token:
        dados.get("tokens", {}).pop(token, None)

    # Remove feedback associado ao token para manter consistencia de contagem.
    if token:
        dados["feedback"] = [
            item for item in dados.get("feedback", [])
            if item.get("token") != token
        ]

    _registrar_evento(
        dados,
        "cpf_liberado_admin",
        cpf_hash=cpf_hash,
        token=token,
    )
    _salvar(dados)
    return {"ok": True, "token_removido": token}


def registrar_evento_publico(tipo, token="", ip="", ua=""):
    dados = _carregar()
    _registrar_evento(
        dados,
        tipo=tipo,
        token=str(token or "").strip(),
        ip=ip,
        ua=ua,
    )
    _salvar(dados)


def dados_brutos_piloto():
    return _garantir_janela(_carregar())
