from pathlib import Path
import unicodedata


def _plt():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    return plt


def _slug(texto):
    texto = str(texto or "grafico").strip().lower()
    texto = "".join(
        c for c in unicodedata.normalize("NFKD", texto)
        if not unicodedata.combining(c)
    )
    texto = "_".join(texto.split())
    return "".join(c for c in texto if c.isalnum() or c == "_") or "grafico"


def _patch():
    from matplotlib.patches import Patch
    return Patch


def _static_dir():
    app_dir = Path(__file__).resolve().parents[1]
    static_dir = app_dir / "static"
    static_dir.mkdir(exist_ok=True)
    return static_dir


def gerar_grafico_score(**kwargs) -> str:
    plt = _plt()
    Patch = _patch()
    bairro = kwargs.get("bairro", "bairro")
    score_bairro = kwargs.get("score") or kwargs.get("score_bairro") or 0
    media_cidade = kwargs.get("media_cidade", 55)

    try:
        score_bairro = int(score_bairro)
    except (TypeError, ValueError):
        score_bairro = 0

    try:
        media_cidade = int(media_cidade)
    except (TypeError, ValueError):
        media_cidade = 55

    nome_arquivo = f"grafico_score_{_slug(bairro)}.png"
    caminho_completo = _static_dir() / nome_arquivo

    labels = ["Bairro analisado", "Media da cidade"]
    valores = [score_bairro, media_cidade]
    cores = ["#1f3c88", "#94a3b8"]

    fig, ax = plt.subplots(figsize=(7.2, 2.9))
    ax.set_facecolor("#f8fafc")
    barras = ax.barh(labels, valores, color=cores, edgecolor="#dbeafe")
    ax.set_xlim(0, 100)
    ax.set_xlabel("Indice de Compatibilidade Urbana")
    ax.grid(axis="x", linestyle="--", alpha=0.25)
    ax.set_title("Comparativo de score", fontsize=11, pad=8)

    # Faixas de leitura
    ax.axvspan(0, 44, color="#fee2e2", alpha=0.25)
    ax.axvspan(45, 69, color="#fef3c7", alpha=0.25)
    ax.axvspan(70, 100, color="#dcfce7", alpha=0.25)
    ax.legend(
        handles=[
            Patch(
                facecolor="#fee2e2",
                edgecolor="none",
                label="Baixa (0-44)",
            ),
            Patch(
                facecolor="#fef3c7",
                edgecolor="none",
                label="Limitada (45-69)",
            ),
            Patch(
                facecolor="#dcfce7",
                edgecolor="none",
                label="Boa (70-100)",
            ),
        ],
        loc="center left",
        bbox_to_anchor=(1.01, 0.5),
        frameon=False,
        fontsize=8,
    )

    for barra in barras:
        largura = barra.get_width()
        ax.text(
            largura + 1,
            barra.get_y() + barra.get_height() / 2,
            f"{int(largura)}",
            va="center",
            fontsize=9,
            color="#0f172a",
            fontweight="bold",
        )

    fig.tight_layout(rect=[0, 0, 0.86, 1])
    fig.savefig(caminho_completo, dpi=140)
    plt.close(fig)
    return f"/static/{nome_arquivo}"


def gerar_grafico_financeiro(**kwargs) -> str:
    plt = _plt()
    bairro = kwargs.get("bairro", "bairro")
    orcamento = kwargs.get("orcamento", 0) or 0
    valor_imovel = kwargs.get("valor_imovel", 0) or 0

    try:
        orcamento = float(orcamento)
    except (TypeError, ValueError):
        orcamento = 0

    try:
        valor_imovel = float(valor_imovel)
    except (TypeError, ValueError):
        valor_imovel = 0

    nome_arquivo = f"grafico_financeiro_{_slug(bairro)}.png"
    caminho_completo = _static_dir() / nome_arquivo

    labels = ["Orcamento", "Valor do imovel"]
    valores = [orcamento, valor_imovel]
    cores = ["#0ea5e9", "#f59e0b"]
    teto = max(valores) if max(valores) > 0 else 1

    fig, ax = plt.subplots(figsize=(7.2, 2.9))
    ax.set_facecolor("#f8fafc")
    barras = ax.barh(labels, valores, color=cores, edgecolor="#e2e8f0")
    ax.set_xlim(0, teto * 1.2)
    ax.set_xlabel("Comparativo financeiro (R$)")
    ax.grid(axis="x", linestyle="--", alpha=0.25)
    ax.set_title(
        "Capacidade financeira x ticket do imovel",
        fontsize=11,
        pad=8,
    )
    if orcamento > 0:
        ax.axvline(orcamento, color="#334155", linestyle=":", linewidth=1.2)

    for barra in barras:
        largura = barra.get_width()
        texto = f"R$ {largura:,.0f}".replace(",", ".")
        ax.text(
            largura + (teto * 0.01),
            barra.get_y() + barra.get_height() / 2,
            texto,
            va="center",
            fontsize=9,
            color="#0f172a",
            fontweight="bold",
        )

    fig.tight_layout()
    fig.savefig(caminho_completo, dpi=140)
    plt.close(fig)
    return f"/static/{nome_arquivo}"
