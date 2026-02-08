import os
import secrets

from flask import Flask

from app.api.pagamento import pagamento
from app.api.routes import router
from app.api.webhook_mp import webhook_mp


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.getenv(
        "LOKAO_SECRET_KEY",
        secrets.token_hex(32),
    )
    app.config["MAX_CONTENT_LENGTH"] = 1024 * 1024
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["SESSION_COOKIE_SECURE"] = bool(
        os.getenv("LOKAO_SESSION_SECURE", "")
    )

    app.register_blueprint(router)
    app.register_blueprint(pagamento)
    app.register_blueprint(webhook_mp)

    @app.after_request
    def _set_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "connect-src 'self'; "
            "object-src 'none'; "
            "base-uri 'self'; "
            "frame-ancestors 'none'; "
            "form-action 'self'"
        )
        return response

    return app


if __name__ == "__main__":
    app = create_app()
    host = os.getenv("LOKAO_HOST", "127.0.0.1")
    port = int(os.getenv("LOKAO_PORT", "5000"))
    debug = os.getenv("LOKAO_DEBUG", "1") == "1"
    app.run(host=host, port=port, debug=debug)
