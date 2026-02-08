from flask import Blueprint, request

from app.services.pagamentos_mp import confirmar_pagamento


webhook_mp = Blueprint("webhook_mp", __name__)


@webhook_mp.route("/webhook/mercadopago", methods=["POST"])
def mercadopago_webhook():
    payload = request.json or {}
    if not payload:
        return "no payload", 400

    if payload.get("type") == "payment":
        # Alguns formatos enviam reference na raiz, outros em data
        external_reference = payload.get("external_reference")
        if not external_reference:
            data = payload.get("data", {}) or {}
            external_reference = data.get("external_reference")

        if external_reference:
            confirmar_pagamento(external_reference)

    return "ok", 200
