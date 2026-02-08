CRUZAMENTOS = {

    ("Residencial de Alto Padrão", "Apartamento usado"): (
        "Em bairros residenciais de alto padrão, apartamentos usados tendem a "
        "oferecer boa liquidez e localização privilegiada, porém exigem atenção "
        "ao nível de ruído urbano e à insolação, especialmente em áreas adensadas."
    ),

    ("Residencial de Alto Padrão", "Casa usada"): (
        "Casas usadas em bairros de alto padrão costumam apresentar excelente "
        "conforto residencial e valorização, sendo recomendável atenção ao "
        "estado de conservação e às regras urbanísticas locais."
    ),

    ("Urbano Consolidado Central", "Apartamento usado"): (
        "Apartamentos usados em regiões centrais consolidadas oferecem alta "
        "proximidade de serviços e liquidez, porém podem apresentar níveis "
        "elevados de ruído e menor conforto térmico."
    ),

    ("Urbano Consolidado Central", "Imóvel comercial"): (
        "Imóveis comerciais em áreas centrais consolidadas se beneficiam de "
        "alto fluxo e visibilidade, sendo estratégicos para atividades que "
        "dependem de acesso e exposição."
    ),

    ("Expansão Urbana Planejada", "Terreno"): (
        "Terrenos em áreas de expansão urbana planejada apresentam elevado "
        "potencial de valorização, desde que compatibilizados com o uso "
        "pretendido e o cronograma de implantação da infraestrutura."
    ),

    ("Expansão Urbana Planejada", "Casa nova"): (
        "Casas novas em áreas de expansão planejada permitem melhor adequação "
        "do projeto ao terreno e ao entorno, com potencial de valorização "
        "associado à consolidação urbana futura."
    ),

    ("Misto Residencial–Comercial", "Apartamento usado"): (
        "Apartamentos usados em regiões mistas tendem a apresentar boa "
        "localização e acesso a serviços, exigindo atenção ao conforto "
        "acústico em horários de maior atividade urbana."
    ),

    ("Zona Especial / Industrial / Logística", "Galpão / logística"): (
        "Galpões localizados em zonas especiais ou industriais apresentam "
        "compatibilidade elevada para atividades logísticas, com atenção "
        "necessária às restrições ambientais e ao tráfego pesado."
    )
}

FRASE_PADRAO = (
    "A compatibilidade entre o perfil urbano identificado e o tipo de imóvel "
    "analisado indica viabilidade condicionada à adequação do uso pretendido "
    "e às características do entorno."
)

def obter_frase_cruzamento(perfil_bairro, tipo_imovel):
    return CRUZAMENTOS.get(
        (perfil_bairro, tipo_imovel),
        FRASE_PADRAO
    )
