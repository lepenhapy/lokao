def moeda_para_float(valor):
    if valor is None:
        return 0.0

    if isinstance(valor, (int, float)):
        return float(valor)

    if isinstance(valor, str):
        try:
            valor = (
                valor.replace("R$", "")
                .replace(".", "")
                .replace(",", ".")
                .strip()
            )
            return float(valor)
        except ValueError:
            return 0.0

    return 0.0


def float_para_moeda(valor):
    try:
        valor = float(valor)
    except (TypeError, ValueError):
        valor = 0.0

    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
