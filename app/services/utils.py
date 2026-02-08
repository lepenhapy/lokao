def normalizar_valor_monetario(valor):
    """
    Converte valores monetários brasileiros para float.
    Ex:
    'R$ 250.000,00' -> 250000.0
    '250.000,00'    -> 250000.0
    '250000'        -> 250000.0
    """

    if valor is None:
        return 0.0

    if isinstance(valor, (int, float)):
        return float(valor)

    try:
        texto = str(valor)
        texto = texto.replace("R$", "")
        texto = texto.replace(" ", "")
        texto = texto.replace(".", "")
        texto = texto.replace(",", ".")
        return float(texto)
    except ValueError:
        return 0.0
