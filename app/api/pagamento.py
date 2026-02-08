from flask import Blueprint, jsonify, redirect, render_template, request

from app.services.pagamentos_mp import (
    carregar_pagamentos,
    confirmar_pagamento,
    criar_pagamento,
    status_pagamento,
)


pagamento = Blueprint("pagamento", __name__)


@pagamento.route("/pagar")
def pagar():
    token = request.args.get("token")
    url, token = criar_pagamento(3990, token=token)  # R$ 39,90
    return render_template(
        "pagamento_aguardando.html",
        token=token,
        url_pagamento=url,
        url_retorno=f"/pago?token={token}",
    )


@pagamento.route("/pago")
def pago():
    token = request.args.get("token")
    dados = carregar_pagamentos()
    if token and token in dados:
        confirmar_pagamento(token)
        return redirect(f"/relatorio?token={token}")
    return "Pagamento nao encontrado", 404


@pagamento.route("/pagamento/status")
def pagamento_status():
    token = request.args.get("token")
    return jsonify({
        "token": token,
        "status": status_pagamento(token),
    })
