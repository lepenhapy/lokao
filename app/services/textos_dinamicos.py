# app/services/textos_dinamicos.py

def texto_compatibilidade(score_valor):
    if score_valor >= 80:
        return (
            "A análise indica alta compatibilidade entre o perfil do bairro e sua capacidade "
            "financeira atual. Isso significa que o padrão urbano, o valor de mercado e o tipo "
            "de imóvel desejado estão bem alinhados, reduzindo riscos de frustração futura."
        )
    elif score_valor >= 60:
        return (
            "A compatibilidade observada é moderada. O bairro apresenta potencial de atendimento "
            "às suas expectativas, porém ajustes estratégicos podem ser necessários, seja no padrão "
            "construtivo, na área do imóvel ou na forma de aquisição."
        )
    else:
        return (
            "A análise aponta baixa compatibilidade entre o perfil do bairro e sua capacidade "
            "financeira atual. Isso não invalida a escolha, mas indica risco elevado de frustração "
            "ou necessidade de concessões significativas."
        )


def texto_financeiro(score_valor, orcamento):
    if score_valor >= 80:
        return (
            "O orçamento informado demonstra boa capacidade de absorção dos custos médios praticados "
            "no bairro analisado. Isso permite maior liberdade de escolha quanto a padrão de acabamento, "
            "soluções construtivas e eventuais melhorias."
        )
    elif score_valor >= 60:
        return (
            "O orçamento informado se encontra dentro de uma faixa viável, porém exige atenção especial "
            "à composição dos custos totais. Decisões técnicas bem orientadas serão fundamentais para "
            "evitar extrapolação financeira."
        )
    else:
        return (
            "O orçamento informado apresenta limitações relevantes frente ao padrão do bairro. "
            "Recomenda-se reavaliar expectativas, buscar alternativas urbanas ou revisar o modelo "
            "de aquisição para evitar comprometimento financeiro excessivo."
        )


def texto_urbano(score_valor):
    if score_valor >= 80:
        return (
            "O contexto urbano do bairro é coerente com o perfil esperado para o imóvel analisado. "
            "Aspectos como ocupação do solo, vizinhança e padrão construtivo contribuem para uma "
            "experiência urbana estável e previsível."
        )
    elif score_valor >= 60:
        return (
            "O bairro apresenta características urbanas compatíveis em parte com o perfil desejado. "
            "Alguns fatores, como dinâmica local ou padrão predominante, devem ser observados com mais "
            "atenção durante a tomada de decisão."
        )
    else:
        return (
            "A leitura urbana indica desalinhamento entre o perfil do bairro e o padrão esperado. "
            "Esse cenário pode impactar conforto, valorização e percepção de adequação ao longo do tempo."
        )
