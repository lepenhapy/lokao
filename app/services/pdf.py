from io import BytesIO
import re
from pathlib import Path

from flask import Response
from xhtml2pdf import pisa


def _sanitizar_html_para_pdf(html_content: str) -> str:
    """
    xhtml2pdf nao suporta bem CSS moderno (como var()).
    Faz substituicoes simples para manter compatibilidade.
    """
    if not html_content:
        return ""

    substituicoes = {
        "var(--primaria)": "#1f3c88",
        "var(--secundaria)": "#4f6bed",
        "var(--texto)": "#1f2937",
        "var(--suave)": "#6b7280",
        "var(--bg)": "#f4f6f8",
        "var(--papel)": "#ffffff",
        "var(--borda)": "#e5e7eb",
        "backdrop-filter: blur(6px);": "",
        "filter: blur(6px);": "",
    }

    html = html_content
    for origem, destino in substituicoes.items():
        html = html.replace(origem, destino)
    # Fallback para qualquer outra var(...) residual no CSS
    html = re.sub(r"var\(--[a-zA-Z0-9_-]+\)", "#000000", html)
    return html


def gerar_pdf(html_content: str, nome_arquivo: str):
    def _link_callback(uri, _rel):
        if uri.startswith("/static/"):
            base = Path(__file__).resolve().parents[1] / "static"
            return str((base / uri.replace("/static/", "")).resolve())
        return uri

    pdf_buffer = BytesIO()
    html_processado = _sanitizar_html_para_pdf(html_content)

    pisa_status = pisa.CreatePDF(
        html_processado,
        dest=pdf_buffer,
        encoding="UTF-8",
        link_callback=_link_callback,
    )

    if pisa_status.err:
        return None

    pdf_buffer.seek(0)
    return Response(
        pdf_buffer.read(),
        mimetype="application/pdf",
        headers={"Content-Disposition": f"inline; filename={nome_arquivo}"},
    )
