import json
import uuid
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
ARQUIVO = BASE_DIR / "data" / "pagamentos_mp.json"
LINK_PAGAMENTO_PIX = "https://mpago.la/1DucMHZ"


def carregar_pagamentos():
    if ARQUIVO.exists():
        return json.loads(ARQUIVO.read_text(encoding="utf-8"))
    return {}


def salvar_pagamentos(dados):
    ARQUIVO.parent.mkdir(exist_ok=True)
    ARQUIVO.write_text(
        json.dumps(dados, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def registrar_pagamento_pendente(token, dados_relatorio):
    dados = carregar_pagamentos()
    atual = dados.get(token, {})
    status = atual.get("status", "pendente")
    dados[token] = {
        "status": status if status == "pago" else "pendente",
        "dados": {**(atual.get("dados", {}) or {}), **(dados_relatorio or {})},
    }
    salvar_pagamentos(dados)
    return token


def confirmar_pagamento(token):
    dados = carregar_pagamentos()
    if token in dados:
        dados[token]["status"] = "pago"
        salvar_pagamentos(dados)


def status_pagamento(token):
    if not token:
        return "inexistente"
    dados = carregar_pagamentos()
    return dados.get(token, {}).get("status", "inexistente")


def criar_pagamento(valor_centavos, token=None, dados_relatorio=None):
    """
    Cria/recupera um token de pagamento e retorna URL de checkout.
    """
    if not token:
        token = uuid.uuid4().hex
    registrar_pagamento_pendente(token, dados_relatorio or {"valor_centavos": valor_centavos})
    return f"{LINK_PAGAMENTO_PIX}?ref={token}", token
