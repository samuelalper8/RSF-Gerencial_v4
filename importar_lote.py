import json
import os

# Dados limpos e saneados a partir do lote original fornecido
DADOS_LOTE = """
GOAutarquiaBela Vista De Goias - SMT23318150000143
GOAutarquiaGoiatuba - (FESG)01494665000161
GOAutarquiaGoiatuba - Fembom16571776000100
GOAutarquiaGoiatuba - IAG05098663000104
GOAutarquiaJaraguá - FMAS (Fundação)15693214000168
GOAutarquiaJaraguá - FMGM00027730000186
GOCâmaraCâmara Baliza00898626000167
GOCâmaraCamara Catalão00833942000150
GOCâmaraCâmara Ceres04340201000199
GOCâmaraCâmara Crixás01231885000100
GOCâmaraCâmara Padre Bernardo05136142000102
GOCâmaraCâmara Perolândia02254179000139
GOCâmaraCâmara São Luís de Montes Belos01725501000106
GOConselho EscCaiapônia - Caixa Escolar Geuza Costa Abreu00710259000126
GOConselho EscCaiapônia - Escola Municipal Ana Rosa de Jesus06082361000100
GOConselho EscCaiapônia - Escola Municipal Maria Cândida de Jesus02263596000148
GOConselho EscCaiapônia - Escola Ana Esméria Vilela00684459000151
GOConselho EscCaiapônia - Escola Cristiano de Castro00684457000162
GOConselho EscCaiapônia - Caixa Escolar Novo Horizonte03562668000110
GOConselho EscCaiapônia - CMEI Maria de França Araujo34323581000114
GOConselho EscGoiatuba - Cons Esc CMEI Pedro Vinicius Vieira Alves de Oliveira62812551000107
GOConselho EscGoiatuba - Cons Esc Profª Maria Luzia Rezende Simões01864764000198
GOConselho EscGoiatuba - Cons Esc Professora Ana Perciliana do Prado Vargas01864766000187
GOConselho EscGoiatuba - Conselho Esc Professora Irene Rosa Ferreira00675463000153
GOConselho EscGoiatuba - Conselho Esc Professora Noêmia de Castilho01864765000132
GOConselho EscGoiatuba - Conselho Escolar Creche José Luis Pereira Juca da Luiza10931242000152
GOConselho EscGoiatuba - Conselho Escolar Creche Lar Menino Jesus10931320000119
GOConselho EscGoiatuba - Conselho Escolar Creche Municipal Mãe Santíssima20320165000158
GOConselho EscGoiatuba - Conselho Escolar Creche Paz e Amor10931332000143
GOConselho EscGoiatuba - Conselho Escolar Geraldo de Assis01864770000145
GOConselho EscGoiatuba - Conselho Escolar José de Anchieta01864762000107
GOConselho EscGoiatuba - Conselho Escolar Maria de Lourdes Estivalet Teixeira00668659000110
GOConselho EscGoiatuba - Conselho Escolar Maria de Lourdes Martins Costa01864761000154
GOConselho EscGoiatuba - Conselho Escolar Ministro Alfredo Nasser00675466000197
GOConselho EscGoiatuba - Conselho Escolar Nara de Oliveira Borges01864763000143
GOConselho EscGoiatuba - Conselho Escolar São Carlos01864760000100
GOConselho EscGoiatuba - Conselho Escolar Vanise de Oliveira Salatiel07419603000171
GOConselho EscGoiatuba - Conselho Municipal de Educação01814100000114
GOConselho EscItaberaí - Centro Educacional Joao Silvestre Da Silva45882034000195
GOConselho EscItaberaí - CMEI Maria Heleny Heleny Perilo 50865926000118
GOConselho EscItaberaí - CMEI Norma Cabral 23918672000186
GOConselho EscItaberaí - Conselho Escolar Genoveva Cabral00664865000152
GOConselho EscItaberaí - Conselho Escolar Irani Costa26868349000133
GOConselho EscItaberaí - Conselho Escolar Jeronimo José da Silva00664878000121
GOConselho EscItaberaí - Conselho Escolar Juca Ludovico00666054000190
GOConselho EscItaberaí - Conselho Escolar Modestina Fonseca00664882000190
GOConselho EscItaberaí - Conselho Escolar Padre Eligio Silvestri01821196000148
GOConselho EscItaberaí - Conselho Escolar São Benedito00664889000101
GOConselho EscItaberaí - Conselho Escolar São Dimas26868356000135
GOConselho EscItaberaí - Creche Municipal Filhos de Davi11173370000147
GOConselho EscItaberaí - Creche Municipal Santa Clara11207200000136
GOMunicípioAmaralina01492098000104
GOMunicípioBaliza01067131000159
GOMunicípioBarro Alto 02355675000189
GOMunicípioBela Vista De Goias01005917000141
GOMunicípioBrazabrantes01756741000160
GOMunicípioBuriti Alegre01345909000144
GOMunicípioCaiapônia01164946000156
GOMunicípioCampinacu00145789000179
GOMunicípioCeres01131713000157
GOMunicípioCorumbá Goiás 01118850000151
GOMunicípioCristalina01138122000101
GOMunicípioCrixás02382067000163
GOMunicípioEdéia01788082000143
GOMunicípioGoiás (Município)02295772000123
GOMunicípioGoiatuba01753722000180
GOMunicípioHidrolina01067230000130
GOMunicípioItaberaí02451938000153
GOMunicípioItapaci01134808000124
GOMunicípioJaraguá01223916000173
GOMunicípioMontes Claros Goiás01767722000139
GOMunicípioNerópolis01105626000125
GOMunicípioNovo Gama01629276000104
GOMunicípioParanaiguara02056745000106
GOMunicípioPerolândia 24859324000148
GOMunicípioPilar De Goiás02647303000126
GOMunicípioPiranhas01168145000169
GOMunicípioPirenópolis01067941000105
GOMunicípioRianápolis01300094000187
GOMunicípioRio Quente24852675000127
GOMunicípioSão Francisco Goiás02468437000180
GOMunicípioSão Luís Montes Belos02320406000187
GOMunicípioSerranópolis01343086000118
GOMunicípioTeresina Goiás25105339000183
GOMunicípioTrindade01217538000115
GOMunicípioUirapuru37622164000160
GORPPSBaliza - RPPS11329148000190
GORPPSBarro Alto - RPPS05004744000106
GORPPSCrixás - RPPS04739716000166
GORPPSGoiatuba - RPPS04902663000152
GORPPSItaberaí - RPPS05370217000107
GORPPSParanaiguara - RPPS05990876000146
GORPPSPiranhas - RPPS07578154000104
GORPPSSerranópolis - RPPS05433433000154
GORPPSTrindade - RPPS05015173000105
MSAutarquiaJaraguari - SAAE15435936000112
MSCâmaraCâmara Costa Rica00991547000104
MSCâmaraCâmara Eldorado70524376000180
MSCâmaraCâmara Jaraguari02210819000109
MSConselho EscTacuru - APM Claudia do Nascimento47529525000182
MSConselho EscTacuru - APM Escola Cecilia M H Perecin01998376000108
MSConselho EscTacuru - APM Escola Ubaldo Arandu08814223000102
MSConselho EscTacuru - APM Sorriso da Criança12427025000155
MSConselho EscTacuru - APM Tomazia Vargas25109061000112
MSConselho EscCONSELHO MUNICIPAL ANTI DROGRAS- COMAD DE TACURU MS25307204000109
MSMunicípioAlcinópolis37226651000104
MSMunicípioAnastácio03452307000111
MSMunicípioAquinauna03452299000103
MSMunicípioChapadão do Sul24651200000172
MSMunicípioIguatemi03568318000161
MSMunicípioJaporã15905342000128
MSMunicípioJaraguari03501533000145
MSMunicípioSete Quedas03889011000162
MSMunicípioSonora24651234000167
MSMunicípioTacuru03888989000100
MSRPPSSonora - RPPS04318288000106
TOCâmaraCâmara de Monte do Carmo02289530000127
TOCâmaraCâmara de Peixe01447812000142
TOConselho EscPalmeirópolis - AACMEI - Pequenos Brilhantes10913066000126
TOConselho EscPalmeirópolis - AACMEI - Sonho Meu46951210000166
TOConselho EscPalmeirópolis - AAE - Elda Silva Barros01959799000100
TOConselho EscPalmeirópolis - AAE - Vila Bom Tempo09337407000183
TOConselho EscSanta Rita do Tocantins - AAEM01856560000105
TOConselho EscSanta Rita do Tocantins - AAEM - Analia03173321000186
TOConselho EscSanta Rita do Tocantins - APM CMEI Carlos Roberto Rezende30781706000107
TOMunicípioAguiarnópolis01634074000142
TOMunicípioAlmas01138551000189
TOMunicípioBandeirantes do Tocantins01612819000172
TOMunicípioBarra do Ouro01612818000128
TOMunicípioBom Jesus37420775000126
TOMunicípioBrejinho De Nazaré02884153000174
TOMunicípioCristalândia01067156000152
TOMunicípioGuaraí02070548000133
TOMunicípioJaú Do Tocantins37344413000101
TOMunicípioLagoa da Confusão26753137000100
TOMunicípioMarianópolis24851479000138
TOMunicípioMaurilândia do Tocantins25064015000144
TOMunicípioNatividade01809474000141
TOMunicípioPalmeiras Do Tocantins25064056000130
TOMunicípioPalmeirópolis00007401000173
TOMunicípioParaíso Do Tocantins00299180000154
TOMunicípioPedro Afonso02070589000120
TOMunicípioPeixe02396166000102
TOMunicípioPium01189497000109
TOMunicípioSanta Maria Do Tocantins37421039000192
TOMunicípioSanta Rita do Tocantins01613127000149
TOMunicípioSilvanópolis00114819000180
"""

def injetar_clientes():
    ARQUIVO = "clientes_base.json"
    clientes_existentes = []
    
    # Carrega base existente, se houver
    if os.path.exists(ARQUIVO):
        try:
            with open(ARQUIVO, "r", encoding="utf-8") as f:
                clientes_existentes = json.load(f)
        except json.JSONDecodeError:
            clientes_existentes = []

    cnpjs_cadastrados = {c['cnpj'] for c in clientes_existentes}
    novos_adicionados = 0

    print("Iniciando injeção do lote tributário...")
    
    for linha in DADOS_LOTE.split("\n"):
        linha = linha.strip()
        if not linha or "MUNICÍPIO E VINCULADOS" in linha:
            continue
            
        # O padrão material é: os últimos 14 caracteres são o CNPJ
        cnpj_puro = linha[-14:]
        texto_restante = linha[:-14]
        
        # Isolar a UF (2 primeiros caracteres)
        uf = texto_restante[:2]
        texto_restante = texto_restante[2:]
        
        # Eliminar a designação de natureza (Autarquia, Município, etc)
        naturezas = ['Autarquia', 'Câmara', 'Conselho Esc', 'Município', 'RPPS']
        for nat in naturezas:
            if texto_restante.startswith(nat):
                texto_restante = texto_restante[len(nat):]
                break
                
        # Formatar os campos
        nome = texto_restante.strip()
        cnpj_fmt = f"{cnpj_puro[:2]}.{cnpj_puro[2:5]}.{cnpj_puro[5:8]}/{cnpj_puro[8:12]}-{cnpj_puro[12:]}"
        
        # Validação de Materialidade (evita sobreposição se rodar o script 2x)
        if cnpj_fmt not in cnpjs_cadastrados:
            clientes_existentes.append({
                "cnpj": cnpj_fmt,
                "nome": f"{nome} ({uf})"
            })
            cnpjs_cadastrados.add(cnpj_fmt)
            novos_adicionados += 1

    # Gravar na base JSON
    with open(ARQUIVO, "w", encoding="utf-8") as f:
        json.dump(clientes_existentes, f, indent=4, ensure_ascii=False)

    print("-" * 50)
    print(f"✅ Operação Concluída: {novos_adicionados} novos clientes injetados na base.")
    print(f"📊 Total na carteira agora: {len(clientes_existentes)} entidades.")
    print("O painel lateral de 'Gestão de Carteira' já está atualizado.")

if __name__ == "__main__":
    injetar_clientes()
