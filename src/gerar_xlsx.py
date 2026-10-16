"""Gera saida/saude_municipios.xlsx com três abas: Dados, Dicionário de Dados e Programas e Observações.

Uso:
    .venv/bin/python src/gerar_xlsx.py   (depois de src/consolidar.py)

As colunas calculadas (por mil habitantes, totais da região de saúde e impacto no bolso) são fórmulas
do Excel. Os preços da cesta ficam na aba "Programas e Observações" e podem ser editados.
"""
import pandas as pd
from openpyxl import Workbook
from openpyxl.comments import Comment
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from config import CESTA, LIMITE_MUNICIPIO_PEQUENO, RAIZ

ENTRADA = RAIZ / "saida" / "saude_municipios.parquet"
SAIDA = RAIZ / "saida" / "saude_municipios.xlsx"
ABA_DADOS, ABA_DIC, ABA_PROG = "Dados", "Dicionário de Dados", "Programas e Observações"
REF_PROG = f"'{ABA_PROG}'"

FONTE = "Arial"
VERMELHO = "C8102E"
F_TITULO = Font(name=FONTE, size=14, bold=True, color=VERMELHO)
F_SECAO = Font(name=FONTE, size=12, bold=True, color="FFFFFF")
F_CAB = Font(name=FONTE, size=10, bold=True, color="FFFFFF")
F_TXT = Font(name=FONTE, size=10)
F_NEG = Font(name=FONTE, size=10, bold=True)
F_ENTRADA = Font(name=FONTE, size=10, color="0000FF")
F_VERDE = Font(name=FONTE, size=10, color="008000")
P_CAB = PatternFill("solid", fgColor=VERMELHO)
P_SECAO = PatternFill("solid", fgColor="8E0C22")
P_ENTRADA = PatternFill("solid", fgColor="FFFF00")
P_CINZA = PatternFill("solid", fgColor="F2F2F2")
BORDA = Border(bottom=Side(style="thin", color="D9D9D9"))
QUEBRA = Alignment(wrap_text=True, vertical="top")

# ---------------------------------------------------------------- aba Dados: layout das colunas
# (coluna no parquet ou None para fórmula, cabeçalho, largura, formato)
COLUNAS = [
    ("cod_ibge7", "cod_ibge7", 11, "@"),
    ("cod_ibge6", "cod_ibge6", 10, "@"),
    ("municipio", "municipio", 28, "@"),
    ("uf", "uf", 5, "@"),
    ("co_regiao_saude", "co_regiao_saude", 10, "@"),
    ("no_regiao_saude", "no_regiao_saude", 26, "@"),
    ("populacao_2025", "populacao_2025", 13, "#,##0"),
    (None, "municipio_pequeno", 11, "General"),
    ("fp_total", "fp_total", 11, "#,##0"),
    ("fp_so_hipertensao", "fp_so_hipertensao", 11, "#,##0"),
    ("fp_so_diabetes", "fp_so_diabetes", 11, "#,##0"),
    ("fp_hipertensao_e_diabetes", "fp_hipertensao_e_diabetes", 11, "#,##0"),
    ("fp_asma", "fp_asma", 10, "#,##0"),
    ("alto_custo_pacientes", "alto_custo_pacientes", 11, "#,##0"),
    ("quimioterapia_pacientes", "quimioterapia_pacientes", 11, "#,##0"),
    ("radioterapia_pacientes", "radioterapia_pacientes", 11, "#,##0"),
    ("hiv_pessoas_em_tratamento_2025", "hiv_pessoas_em_tratamento_2025", 12, "#,##0"),
    (None, "fp_total_por_mil_hab", 10, "#,##0.0"),
    (None, "fp_so_hipertensao_por_mil_hab", 10, "#,##0.0"),
    (None, "fp_so_diabetes_por_mil_hab", 10, "#,##0.0"),
    (None, "fp_hipertensao_e_diabetes_por_mil_hab", 10, "#,##0.0"),
    (None, "fp_asma_por_mil_hab", 10, "#,##0.0"),
    (None, "alto_custo_pacientes_por_mil_hab", 10, "#,##0.0"),
    (None, "quimioterapia_pacientes_por_mil_hab", 10, "#,##0.0"),
    (None, "fp_total_regiao_saude", 12, "#,##0"),
    (None, "fp_so_hipertensao_regiao_saude", 12, "#,##0"),
    (None, "fp_so_diabetes_regiao_saude", 12, "#,##0"),
    (None, "fp_hipertensao_e_diabetes_regiao_saude", 12, "#,##0"),
    (None, "fp_asma_regiao_saude", 12, "#,##0"),
    (None, "alto_custo_pacientes_regiao_saude", 12, "#,##0"),
    (None, "quimioterapia_pacientes_regiao_saude", 12, "#,##0"),
    (None, "radioterapia_pacientes_regiao_saude", 12, "#,##0"),
    (None, "fp_total_por_mil_hab_regiao_saude", 12, "#,##0.0"),
    (None, "bolso_anual_minimo_rs", 15, '"R$" #,##0'),
    (None, "bolso_anual_mediano_rs", 15, '"R$" #,##0'),
    ("txt_farmacia_popular", "txt_farmacia_popular", 60, "@"),
    ("txt_bolso", "txt_bolso", 48, "@"),
]
L = {cab: get_column_letter(i + 1) for i, (_, cab, _, _) in enumerate(COLUNAS)}

# ---------------------------------------------------------------- aba Programas: células dos parâmetros
PARAM = {}  # nome -> referência absoluta na aba de programas


def dicionario() -> list[tuple]:
    """(coluna, descrição, tipo, unidade, fonte, período)."""
    fp = "Ministério da Saúde · Portal de Dados Abertos do SUS · Programa Farmácia Popular do Brasil"
    sia = "DataSUS · SIA/SUS · APAC por município de residência (campo AP_MUNPCN)"
    calc = "Calculado nesta planilha"
    return [
        ("cod_ibge7", "Código IBGE do município com 7 dígitos (chave para cruzar com outras bases do IBGE).", "Identificação", "código", "IBGE", "—"),
        ("cod_ibge6", "Código IBGE com 6 dígitos (sem o dígito verificador), usado pelo DataSUS e pelo Ministério da Saúde.", "Identificação", "código", "IBGE", "—"),
        ("municipio", "Nome do município.", "Identificação", "texto", "IBGE", "—"),
        ("uf", "Sigla do estado.", "Identificação", "texto", "IBGE", "—"),
        ("co_regiao_saude", "Código da região de saúde a que o município pertence (439 regiões no país).", "Identificação", "código", fp, "08/2026"),
        ("no_regiao_saude", "Nome da região de saúde.", "Identificação", "texto", fp, "08/2026"),
        ("populacao_2025", "População residente estimada.", "Dado", "pessoas", "IBGE · Estimativas de população (POP2025_20260828)", "1º/07/2025"),
        ("municipio_pequeno", f"VERDADEIRO se a população for menor que o limite da aba {ABA_PROG} (padrão: {LIMITE_MUNICIPIO_PEQUENO:,} habitantes). Nesses municípios, prefira os totais da região de saúde.".replace(",", "."), "Fórmula", "sim/não", calc, "—"),
        ("fp_total", "Pessoas atendidas pela Farmácia Popular no mês, em qualquer medicamento ou insumo. Contadas no município da FARMÁCIA, não da residência.", "Dado", "pessoas/mês", fp + " (pfpbben)", "08/2026"),
        ("fp_so_hipertensao", "Pessoas atendidas com remédio gratuito apenas para hipertensão.", "Dado", "pessoas/mês", fp + " (sntpbh)", "08/2026"),
        ("fp_so_diabetes", "Pessoas atendidas com remédio gratuito apenas para diabetes.", "Dado", "pessoas/mês", fp + " (sntpbd)", "08/2026"),
        ("fp_hipertensao_e_diabetes", "Pessoas atendidas com remédios gratuitos para hipertensão E diabetes. Não se sobrepõe às duas colunas anteriores.", "Dado", "pessoas/mês", fp + " (sntpdhc)", "08/2026"),
        ("fp_asma", "Pessoas atendidas com remédio gratuito para asma.", "Dado", "pessoas/mês", fp + " (sntpba)", "08/2026"),
        ("alto_custo_pacientes", "Moradores do município que receberam remédio do Componente Especializado (alto custo: Alzheimer, Parkinson, artrite, transplantes etc.). Estimativa de pessoas únicas (ver aba de programas).", "Dado (estimado)", "pessoas", sia + " · arquivos AM", "06/2026"),
        ("quimioterapia_pacientes", "Moradores do município em quimioterapia pelo SUS. Estimativa de pessoas únicas.", "Dado (estimado)", "pessoas", sia + " · arquivos AQ", "06/2026"),
        ("radioterapia_pacientes", "Moradores do município em radioterapia pelo SUS. Estimativa de pessoas únicas.", "Dado (estimado)", "pessoas", sia + " · arquivos AR", "06/2026"),
        ("hiv_pessoas_em_tratamento_2025", "Pessoas vivendo com HIV em tratamento antirretroviral regular em 31/12/2025 (sem atraso ou com até 60 dias de atraso na retirada). Contadas no município do SERVIÇO que acompanha a pessoa, não da residência. Vazio quando o município não tem serviço com 50 ou mais pessoas em acompanhamento.", "Dado", "pessoas", "Ministério da Saúde · Painel Integrado de Monitoramento do Cuidado do HIV e da Aids (PVHA_ano)", "31/12/2025"),
        ("fp_total_por_mil_hab", "fp_total para cada mil habitantes.", "Fórmula", "por mil hab.", calc, "—"),
        ("fp_so_hipertensao_por_mil_hab", "fp_so_hipertensao para cada mil habitantes.", "Fórmula", "por mil hab.", calc, "—"),
        ("fp_so_diabetes_por_mil_hab", "fp_so_diabetes para cada mil habitantes.", "Fórmula", "por mil hab.", calc, "—"),
        ("fp_hipertensao_e_diabetes_por_mil_hab", "fp_hipertensao_e_diabetes para cada mil habitantes.", "Fórmula", "por mil hab.", calc, "—"),
        ("fp_asma_por_mil_hab", "fp_asma para cada mil habitantes.", "Fórmula", "por mil hab.", calc, "—"),
        ("alto_custo_pacientes_por_mil_hab", "alto_custo_pacientes para cada mil habitantes.", "Fórmula", "por mil hab.", calc, "—"),
        ("quimioterapia_pacientes_por_mil_hab", "quimioterapia_pacientes para cada mil habitantes.", "Fórmula", "por mil hab.", calc, "—"),
        ("fp_total_regiao_saude", "Soma de fp_total em todos os municípios da mesma região de saúde.", "Fórmula", "pessoas/mês", calc, "08/2026"),
        ("fp_so_hipertensao_regiao_saude", "Soma de fp_so_hipertensao na região de saúde.", "Fórmula", "pessoas/mês", calc, "08/2026"),
        ("fp_so_diabetes_regiao_saude", "Soma de fp_so_diabetes na região de saúde.", "Fórmula", "pessoas/mês", calc, "08/2026"),
        ("fp_hipertensao_e_diabetes_regiao_saude", "Soma de fp_hipertensao_e_diabetes na região de saúde.", "Fórmula", "pessoas/mês", calc, "08/2026"),
        ("fp_asma_regiao_saude", "Soma de fp_asma na região de saúde.", "Fórmula", "pessoas/mês", calc, "08/2026"),
        ("alto_custo_pacientes_regiao_saude", "Soma de alto_custo_pacientes na região de saúde.", "Fórmula", "pessoas", calc, "06/2026"),
        ("quimioterapia_pacientes_regiao_saude", "Soma de quimioterapia_pacientes na região de saúde.", "Fórmula", "pessoas", calc, "06/2026"),
        ("radioterapia_pacientes_regiao_saude", "Soma de radioterapia_pacientes na região de saúde.", "Fórmula", "pessoas", calc, "06/2026"),
        ("fp_total_por_mil_hab_regiao_saude", "fp_total da região de saúde para cada mil habitantes da região. Melhor medida para comparar municípios pequenos.", "Fórmula", "por mil hab.", calc, "08/2026"),
        ("bolso_anual_minimo_rs", "Quanto as pessoas atendidas pela Farmácia Popular gastariam por ano comprando o tratamento, no cenário MÍNIMO (genérico mais barato). = 12 × (só hipertensão × preço hipertensão + só diabetes × preço diabetes + ambas × (preço hipertensão + preço diabetes) + asma × preço asma).", "Fórmula", "R$/ano", calc + " · preços da CMED na aba de programas", "preços de 09/10/2026"),
        ("bolso_anual_mediano_rs", "Mesmo cálculo, no cenário MEDIANO (preço mediano dos genéricos).", "Fórmula", "R$/ano", calc + " · preços da CMED na aba de programas", "preços de 09/10/2026"),
        ("txt_farmacia_popular", "Frase pronta para mensagem com o número de moradores atendidos (pressão ou diabetes).", "Texto", "texto", "Gerado a partir de fp_so_hipertensao + fp_so_diabetes + fp_hipertensao_e_diabetes", "08/2026"),
        ("txt_bolso", "Frase pronta com o gasto anual mínimo. É texto fixo: NÃO se atualiza se os preços da aba de programas forem alterados.", "Texto", "texto", "Gerado a partir do cenário mínimo com os preços originais", "—"),
    ]


def montar_programas(ws) -> None:
    ws.sheet_view.showGridLines = False
    for col, w in zip("ABCDEFG", [30, 62, 16, 16, 44, 16, 16]):
        ws.column_dimensions[col].width = w
    r = 1

    def titulo(texto):
        nonlocal r
        ws.cell(r, 1, texto).font = F_TITULO
        r += 2

    def secao(texto):
        nonlocal r
        for c in range(1, 6):
            ws.cell(r, c).fill = P_SECAO
        ws.cell(r, 1, texto).font = F_SECAO
        r += 1

    def cabecalho(*textos):
        nonlocal r
        for i, t in enumerate(textos, 1):
            cel = ws.cell(r, i, t)
            cel.font, cel.fill, cel.alignment = F_CAB, P_CAB, QUEBRA
        r += 1

    def linha(*valores, negrito=False):
        nonlocal r
        for i, v in enumerate(valores, 1):
            cel = ws.cell(r, i, v)
            cel.font = F_NEG if (negrito and i == 1) else F_TXT
            cel.alignment, cel.border = QUEBRA, BORDA
        r += 1

    titulo("Saúde e remédios por município · programas, parâmetros e observações")
    linha("Gerado em", "15/10/2026. Uma linha por município (5.571) na aba Dados; descrição de cada coluna na aba Dicionário de Dados.")
    linha("Como usar", "Células com fundo amarelo e texto azul são parâmetros e podem ser alteradas: a aba Dados recalcula sozinha. Todos os números são agregados por município; nenhum dado individual foi usado.")
    r += 1

    # ---- Parâmetros
    secao("1. Parâmetros editáveis")
    cabecalho("Parâmetro", "Descrição", "Mínimo (R$/mês)", "Mediano (R$/mês)", "Fonte")
    nomes = {"hipertensao": "Hipertensão", "diabetes": "Diabetes", "asma": "Asma"}
    for chave, nome in nomes.items():
        ws.cell(r, 1, f"Custo mensal · {nome}").font = F_NEG
        ws.cell(r, 2, CESTA[chave]["descricao"]).font = F_TXT
        for col, cen in ((3, "minimo"), (4, "mediano")):
            cel = ws.cell(r, col, CESTA[chave][cen])
            cel.font, cel.fill, cel.number_format = F_ENTRADA, P_ENTRADA, '"R$" #,##0.00'
            PARAM[f"{chave}_{cen}"] = f"{REF_PROG}!${get_column_letter(col)}${r}"
        ws.cell(r, 5, "Anvisa · Lista CMED de preço máximo ao consumidor (PMC), 09/10/2026, ICMS 18%").font = F_TXT
        for c in range(1, 6):
            ws.cell(r, c).alignment, ws.cell(r, c).border = QUEBRA, BORDA
        r += 1
    ws.cell(r - 1, 2).comment = Comment("Asma: 0,6 frasco de 200 doses por mês (2 jatos, 2 vezes ao dia = 120 doses). Preço por frasco: R$ 73,23 (mínimo) e R$ 75,21 (mediano).", "Equipe de dados")
    ws.cell(r, 1, "Limite de município pequeno").font = F_NEG
    ws.cell(r, 2, "Abaixo desta população, os números de câncer e alto custo são baixos e oscilam; use os totais da região de saúde.").font = F_TXT
    cel = ws.cell(r, 3, LIMITE_MUNICIPIO_PEQUENO)
    cel.font, cel.fill, cel.number_format = F_ENTRADA, P_ENTRADA, "#,##0"
    PARAM["limite"] = f"{REF_PROG}!$C${r}"
    ws.cell(r, 5, "Definição do time (instrução recebida em 15/10/2026)").font = F_TXT
    for c in range(1, 6):
        ws.cell(r, c).alignment, ws.cell(r, c).border = QUEBRA, BORDA
    r += 2

    # ---- Totais Brasil (fórmulas sobre a aba Dados)
    secao("2. Totais do Brasil (calculados a partir da aba Dados)")
    cabecalho("Indicador", "Descrição", "Total", "", "Período")
    n = PARAM["n_linhas"]
    totais = [
        ("Farmácia Popular · total", "Pessoas atendidas no mês", "fp_total", "08/2026"),
        ("Farmácia Popular · só hipertensão", "Pessoas atendidas no mês", "fp_so_hipertensao", "08/2026"),
        ("Farmácia Popular · só diabetes", "Pessoas atendidas no mês", "fp_so_diabetes", "08/2026"),
        ("Farmácia Popular · hipertensão e diabetes", "Pessoas atendidas no mês", "fp_hipertensao_e_diabetes", "08/2026"),
        ("Farmácia Popular · asma", "Pessoas atendidas no mês", "fp_asma", "08/2026"),
        ("Alto custo (CEAF)", "Pacientes estimados", "alto_custo_pacientes", "06/2026"),
        ("Quimioterapia", "Pacientes estimados", "quimioterapia_pacientes", "06/2026"),
        ("Radioterapia", "Pacientes estimados", "radioterapia_pacientes", "06/2026"),
        ("HIV em tratamento", "Pessoas em tratamento regular, em 600 municípios com serviço (97% do total do país)", "hiv_pessoas_em_tratamento_2025", "31/12/2025"),
        ("Gasto do bolso · mínimo", "R$ por ano sem a Farmácia Popular", "bolso_anual_minimo_rs", "preços de 09/10/2026"),
        ("Gasto do bolso · mediano", "R$ por ano sem a Farmácia Popular", "bolso_anual_mediano_rs", "preços de 09/10/2026"),
    ]
    for nome, desc, col, per in totais:
        letra = L[col]
        ws.cell(r, 1, nome).font = F_NEG
        ws.cell(r, 2, desc).font = F_TXT
        cel = ws.cell(r, 3, f"=SUM('{ABA_DADOS}'!{letra}2:{letra}{n + 1})")
        cel.font = F_VERDE
        cel.number_format = '"R$" #,##0' if col.startswith("bolso") else "#,##0"
        ws.cell(r, 5, per).font = F_TXT
        for c in range(1, 6):
            ws.cell(r, c).alignment, ws.cell(r, c).border = QUEBRA, BORDA
        r += 1
    r += 1

    # ---- Programas
    secao("3. Programas e bases incluídas")
    cabecalho("Programa", "O que é e como contamos", "Fonte", "Período", "Observações e limites")
    programas = [
        ("Farmácia Popular do Brasil",
         "Remédios gratuitos em farmácias privadas credenciadas ('Aqui Tem Farmácia Popular'). Desde 02/2025 todos os itens são gratuitos. A planilha usa as pessoas atendidas no mês, já separadas pelo Ministério em: só hipertensão, só diabetes, hipertensão e diabetes, e asma.",
         "Portal de Dados Abertos do SUS · conjunto [MGDI] Programa Farmácia Popular do Brasil", "08/2026 (mês mais recente)",
         "Contado no município da FARMÁCIA. 1.065 municípios não têm farmácia credenciada e aparecem com zero; cidades pequenas com farmácia atendem vizinhos (ex.: Pedranópolis/SP, 439 por mil hab.). Para comparar, use as colunas da região de saúde."),
        ("Componente Especializado (alto custo, CEAF)",
         "Remédios caros para doenças crônicas graves (Alzheimer, Parkinson, artrite, esclerose, transplantes etc.), retirados nas farmácias do estado. Contamos os moradores de cada município pelo campo de residência do paciente (AP_MUNPCN).",
         "DataSUS · SIA/SUS · APAC de medicamentos (arquivos AM, 27 estados)", "Movimento de 06/2026",
         "Entregues em só 210 municípios, mas os pacientes moram em 5.480. O cartão SUS anonimizado vem vazio em 43% dos registros: pacientes = cartões únicos + registros sem cartão × (cartões únicos ÷ registros com cartão, no país)."),
        ("Oncologia · quimioterapia",
         "Pacientes em quimioterapia pelo SUS, por município de residência.",
         "DataSUS · SIA/SUS · APAC de quimioterapia (arquivos AQ, 27 estados)", "Movimento de 06/2026",
         "Tratamento concentrado em hospitais habilitados (CACON/UNACON). Cartão vazio em 22% dos registros; mesma estimativa do alto custo."),
        ("Oncologia · radioterapia",
         "Pacientes em radioterapia pelo SUS, por município de residência.",
         "DataSUS · SIA/SUS · APAC de radioterapia (arquivos AR, 26 estados)", "Movimento de 06/2026",
         "Roraima não tem arquivo de radioterapia no servidor. Cartão vazio em 72% dos registros; números pequenos, use com cautela."),
        ("HIV/Aids · tratamento antirretroviral",
         "Pessoas vivendo com HIV em tratamento antirretroviral regular em 31/12/2025, contadas no município do serviço que as acompanha (instituição que pediu o último exame).",
         "Ministério da Saúde · Painel Integrado de Monitoramento do Cuidado do HIV e da Aids · base PVHA_ano (Banco_PIMC_2025.zip)", "31/12/2025",
         "Brasil: 877.658 em tratamento. 854.817 (97,4%) estão em 600 municípios com valor; 22.840 estão em serviços com menos de 50 pessoas, que o Ministério só publica somados por estado, e ficam fora da coluna. Como é o município do serviço, cidades-polo concentram pacientes de cidades vizinhas. Outras 139.928 pessoas estavam com o tratamento interrompido (mais de 60 dias sem retirar remédio)."),
        ("População", "Base para os indicadores por mil habitantes.", "IBGE · Estimativas de população", "1º/07/2025", "—"),
    ]
    for p in programas:
        linha(*p, negrito=True)
    r += 1

    secao("4. Bases avaliadas e não incluídas")
    cabecalho("Base", "Motivo", "Fonte", "Período", "Situação")
    linha("Estoques de remédios (BNAFAR)",
          "Só 3.114 dos 5.571 municípios aparecem; 34% dos lotes registrados estão vencidos; o próprio Ministério marca a base como 'em manutenção'.",
          "Portal de Dados Abertos do SUS · BNAFAR Posição de Estoque", "06/06/2026", "Fora até a base ser corrigida", negrito=True)
    linha("Agentes Comunitários de Saúde", "Relatório público do e-Gestor AB, gerado por formulário.", "e-Gestor AB", "—", "Pendente", negrito=True)
    linha("Repasse do postinho (CBAF)", "Valor fixo por habitante (R$ 8,20 a R$ 9,05/ano conforme o IDHM); mede sobretudo o tamanho da população.", "Portaria GM/MS nº 9.887/2025 · Fundo Nacional de Saúde", "2026", "Pendente", negrito=True)
    r += 1

    secao("5. Observações importantes")
    obs = [
        ("Leitura correta", "Os números descrevem municípios, não pessoas. 'Gasto do bolso' é uma estimativa do que as famílias pagariam sem o programa, não uma previsão."),
        ("Por que não R$ 180/mês", "O guia técnico sugeria R$ 180 por mês por idoso, sem fonte. Pela tabela oficial da CMED, o tratamento mais barato custa R$ 16,55 (pressão) e R$ 59,00 (pressão e diabetes). Com R$ 180, o total anual passaria de R$ 20 bilhões e seria facilmente contestado."),
        ("Cenário conservador", "Os preços consideram um remédio por doença, na dose mais comum. Quem usa doses maiores ou mais de um remédio gastaria mais; o valor real tende a ficar acima do mínimo."),
        ("Sem dupla contagem", "As colunas de hipertensão e diabetes são excludentes: quem tem as duas doenças está só em fp_hipertensao_e_diabetes. Por isso não há fator de desduplicação."),
        ("Município de residência", "Alto custo e câncer usam o município onde o paciente mora (AP_MUNPCN). Usar o município do estabelecimento (AP_UFMUN) zeraria quase todo o país."),
        ("Distrito Federal", "Parte dos registros do DataSUS traz o código da região administrativa (53xxxx); todos foram somados a Brasília."),
        ("Frases prontas", "A coluna txt_bolso é texto fixo, gerado com os preços originais. Se os preços forem alterados, ela não muda."),
        ("Reprodução", "Scripts e documentação na pasta 'Dados Saude' (src/consolidar.py, src/gerar_xlsx.py, DOCUMENTACAO.md)."),
    ]
    for o in obs:
        linha(o[0], o[1], negrito=True)
        ws.merge_cells(start_row=r - 1, start_column=2, end_row=r - 1, end_column=5)


def montar_dados(ws, df: pd.DataFrame) -> None:
    for i, (_, cab, larg, _) in enumerate(COLUNAS, 1):
        cel = ws.cell(1, i, cab)
        cel.font, cel.fill = F_CAB, P_CAB
        cel.alignment = Alignment(wrap_text=True, vertical="center")
        ws.column_dimensions[get_column_letter(i)].width = larg
    ws.row_dimensions[1].height = 45
    n = len(df)
    fim = n + 1
    reg = f"${L['co_regiao_saude']}$2:${L['co_regiao_saude']}${fim}"
    for idx, linha_df in enumerate(df.itertuples(index=False), start=2):
        d = linha_df._asdict()
        pop = f"{L['populacao_2025']}{idx}"
        for i, (orig, cab, _, fmt) in enumerate(COLUNAS, 1):
            if orig is not None:
                v = d[orig]
                valor = None if pd.isna(v) else (int(v) if fmt in ("#,##0",) else v)
            elif cab == "municipio_pequeno":
                valor = f"={pop}<{PARAM['limite']}"
            elif cab == "fp_total_por_mil_hab_regiao_saude":
                valor = (f"=IF(SUMIFS(${L['populacao_2025']}$2:${L['populacao_2025']}${fim},{reg},{L['co_regiao_saude']}{idx})>0,"
                         f"1000*{L['fp_total_regiao_saude']}{idx}/SUMIFS(${L['populacao_2025']}$2:${L['populacao_2025']}${fim},{reg},{L['co_regiao_saude']}{idx}),0)")
            elif cab.endswith("_por_mil_hab"):
                base = L[cab.removesuffix("_por_mil_hab")]
                valor = f"=IF({pop}>0,1000*{base}{idx}/{pop},0)"
            elif cab.endswith("_regiao_saude"):
                base = L[cab.removesuffix("_regiao_saude")]
                valor = f"=SUMIFS(${base}$2:${base}${fim},{reg},{L['co_regiao_saude']}{idx})"
            elif cab.startswith("bolso_anual_"):
                cen = "minimo" if "minimo" in cab else "mediano"
                h, dd, a = PARAM[f"hipertensao_{cen}"], PARAM[f"diabetes_{cen}"], PARAM[f"asma_{cen}"]
                valor = (f"=12*({L['fp_so_hipertensao']}{idx}*{h}+{L['fp_so_diabetes']}{idx}*{dd}"
                         f"+{L['fp_hipertensao_e_diabetes']}{idx}*({h}+{dd})+{L['fp_asma']}{idx}*{a})")
            cel = ws.cell(idx, i, valor)
            cel.font = F_TXT
            cel.number_format = fmt
    ws.freeze_panes = "D2"
    ws.auto_filter.ref = f"A1:{get_column_letter(len(COLUNAS))}{fim}"


def montar_dicionario(ws) -> None:
    cab = ["Coluna", "Descrição", "Tipo", "Unidade", "Fonte", "Período / referência"]
    for i, (t, w) in enumerate(zip(cab, [36, 80, 15, 13, 52, 18]), 1):
        cel = ws.cell(1, i, t)
        cel.font, cel.fill, cel.alignment = F_CAB, P_CAB, QUEBRA
        ws.column_dimensions[get_column_letter(i)].width = w
    for r, linha in enumerate(dicionario(), start=2):
        for c, v in enumerate(linha, 1):
            cel = ws.cell(r, c, v)
            cel.font = F_NEG if c == 1 else F_TXT
            cel.alignment, cel.border = QUEBRA, BORDA
            if linha[2] == "Fórmula":
                cel.fill = P_CINZA
    ws.freeze_panes = "B2"
    assert [x[0] for x in dicionario()] == [c[1] for c in COLUNAS], "dicionário fora de ordem com a aba Dados"


def main() -> None:
    df = pd.read_parquet(ENTRADA)
    PARAM["n_linhas"] = len(df)
    wb = Workbook()
    ws_dados = wb.active
    ws_dados.title = ABA_DADOS
    ws_dic = wb.create_sheet(ABA_DIC)
    ws_prog = wb.create_sheet(ABA_PROG)
    montar_programas(ws_prog)  # define as células dos parâmetros antes das fórmulas da aba Dados
    montar_dados(ws_dados, df)
    montar_dicionario(ws_dic)
    for ws in (ws_dados, ws_dic, ws_prog):
        ws.sheet_properties.tabColor = VERMELHO
    wb.calculation.fullCalcOnLoad = True
    wb.save(SAIDA)
    print(f"{SAIDA} · {SAIDA.stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
