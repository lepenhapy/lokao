def gerar_analise(bairro):
    bairro = bairro.lower()

    if bairro in ["goiabeiras", "popular", "duque de caxias"]:
        return {
            "perfil_bairro": (
                "Bairro consolidado com perfil urbano tradicional."
            ),
            "aderencia": "Alta",
            "liquidez": "Alta",
            "argumento": (
                "Este bairro apresenta alta aceitacao comercial e historico "
                "de boa liquidez, sendo uma escolha segura para compradores "
                "que priorizam estabilidade e facilidade de revenda."
            ),
        }

    if bairro in ["jardim italia", "florais", "alphaville"]:
        return {
            "perfil_bairro": "Bairro de alto padrao com foco residencial.",
            "aderencia": "Muito alta",
            "liquidez": "Moderada",
            "argumento": (
                "O perfil do bairro favorece compradores mais exigentes, "
                "com foco em qualidade de vida e padrao construtivo, "
                "o que pode demandar abordagem mais consultiva."
            ),
        }

    return {
        "perfil_bairro": "Bairro em desenvolvimento ou perfil misto.",
        "aderencia": "Moderada",
        "liquidez": "Moderada",
        "argumento": (
            "O bairro apresenta potencial de valorizacao, sendo indicado "
            "para compradores que avaliam oportunidade e crescimento futuro."
        ),
    }
