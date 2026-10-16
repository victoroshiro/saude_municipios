# Saúde e Remédios por Município

Base de dados e painel interativo que mostram, para cada um dos **5.571 municípios brasileiros**:

1. **Quantas pessoas pegam remédio de graça na Farmácia Popular**, separadas por doença: só hipertensão, só diabetes, hipertensão e diabetes, e asma.
2. **Quantos moradores dependem do SUS** para remédios de alto custo, quimioterapia, radioterapia e tratamento de HIV.
3. **Quanto essas pessoas pagariam do próprio bolso** se a Farmácia Popular deixasse de existir, com base na tabela oficial de preços de medicamentos.

Tudo é feito com **dados públicos e agregados por município**. Nenhum dado individual sai do processamento.

**Painel web:** https://saude-municipios.web.app

---

## Sumário
- [Resultados para o Brasil](#resultados-para-o-brasil)
- [O que tem neste repositório](#o-que-tem-neste-repositório)
- [Fontes de dados](#fontes-de-dados)
- [Como reproduzir](#como-reproduzir)
- [Metodologia e decisões](#metodologia-e-decisões)
- [Custo do tratamento sem a Farmácia Popular](#custo-do-tratamento-sem-a-farmácia-popular)
- [Correções ao guia técnico original](#correções-ao-guia-técnico-original)
- [Dicionário de dados](#dicionário-de-dados)
- [Painel web](#painel-web)
- [Planilha Excel](#planilha-excel)
- [Limitações e cuidados de leitura](#limitações-e-cuidados-de-leitura)
- [Pendências](#pendências)

---

## Resultados para o Brasil

| Indicador | Total | Referência |
|---|---|---|
| Pessoas atendidas pela Farmácia Popular no mês | **12,96 milhões** | agosto de 2026 |
| · só hipertensão | 4,96 milhões | agosto de 2026 |
| · só diabetes | 1,81 milhão | agosto de 2026 |
| · hipertensão e diabetes | 3,24 milhões | agosto de 2026 |
| · asma | 0,88 milhão | agosto de 2026 |
| Pacientes de remédio de alto custo (estimativa) | 3,28 milhões | junho de 2026 |
| Pacientes em quimioterapia (estimativa) | 0,36 milhão | junho de 2026 |
| Pessoas em tratamento de HIV | 0,88 milhão (0,85 milhão em 600 municípios identificados) | 31/12/2025 |
| **Gasto do bolso sem a Farmácia Popular, por ano** | **R$ 4,7 bilhões (mínimo) a R$ 7,7 bilhões (mediano)** | preços de 09/10/2026 |

As doenças **não devem ser somadas**: a mesma pessoa pode estar em mais de um programa, e as datas de referência são diferentes.

---

## O que tem neste repositório

```
.
├── README.md                    este arquivo
├── DOCUMENTACAO.md              registro de decisões e validações, em formato resumido
├── requirements.txt             bibliotecas Python
├── src/
│   ├── config.py                caminhos, mês de referência, limite de município pequeno e preços da cesta
│   ├── sia_para_parquet.py      converte os arquivos .dbc do DataSUS em parquet
│   ├── consolidar.py            monta a tabela final, uma linha por município
│   ├── gerar_xlsx.py            gera a planilha Excel com dicionário e observações
│   └── exportar_dashboard.py    gera os dados do painel web
├── saida/
│   ├── saude_municipios.csv     tabela final (separador ";" e vírgula decimal, abre direto no Excel)
│   ├── saude_municipios.parquet a mesma tabela, para uso em código
│   └── saude_municipios.xlsx    planilha com as abas Dados, Dicionário de Dados e Programas e Observações
└── web/
    ├── firebase.json            configuração do Firebase Hosting
    └── public/
        ├── index.html           painel interativo
        └── dados.js             dados do painel
```

**Não estão no repositório:** os dados brutos (`brutos/`, cerca de 2,7 GB) e os arquivos intermediários (`trabalho/`). A seção [Como reproduzir](#como-reproduzir) mostra onde baixar cada um. A base de HIV do Ministério tem uma linha por pessoa (com identificador anonimizado), por isso nunca deve ser versionada; o projeto só publica os totais por município.

---

## Fontes de dados

| # | Base | Órgão | Arquivo | Referência usada | Para quê |
|---|---|---|---|---|---|
| 1 | Programa Farmácia Popular do Brasil | Ministério da Saúde · Portal de Dados Abertos do SUS | `sntpbh`, `sntpbd`, `sntpdhc`, `sntpba`, `pfpbben` (.csv.zip) | agosto de 2026 | Pessoas atendidas por doença |
| 2 | SIA/SUS · APAC de medicamentos, quimioterapia e radioterapia | Ministério da Saúde · DataSUS | `AM`, `AQ` e `AR` + UF + `2606.dbc` | movimento de junho de 2026 | Pacientes de alto custo e câncer por município de residência |
| 3 | Painel Integrado de Monitoramento do Cuidado do HIV e da Aids | Ministério da Saúde · Dathi | `Banco_PIMC_2025.zip` (`PVHA_ano.parquet`) | 31/12/2025 | Pessoas em tratamento de HIV |
| 4 | Lista de preços de medicamentos (PMC) | Anvisa · CMED | `lista_pmc__20261009_115232671.xlsx` | 09/10/2026 | Custo do tratamento sem o programa |
| 5 | Estimativas de população | IBGE | `POP2025_20260828.xls` | 1º/07/2025 | Indicadores por mil habitantes |
| 6 | BNAFAR · Posição de estoque | Ministério da Saúde · Portal de Dados Abertos do SUS | `Posicao_Estoque_csv_06-06-2026.zip` | 06/06/2026 | **Avaliada e não usada** (ver decisões) |

### Links para download

| Base | Link |
|---|---|
| Farmácia Popular · só hipertensão | https://demas-dados-abertos.s3.amazonaws.com/csv/sntpbh.csv.zip |
| Farmácia Popular · só diabetes | https://demas-dados-abertos.s3.amazonaws.com/csv/sntpbd.csv.zip |
| Farmácia Popular · hipertensão e diabetes | https://demas-dados-abertos.s3.amazonaws.com/csv/sntpdhc.csv.zip |
| Farmácia Popular · asma | https://demas-dados-abertos.s3.amazonaws.com/csv/sntpba.csv.zip |
| Farmácia Popular · total | https://demas-dados-abertos.s3.amazonaws.com/csv/pfpbben.csv.zip |
| Página do conjunto | https://dadosabertos.saude.gov.br/dataset/mgdi-programa-farmacia-popular-do-brasil |
| DataSUS SIA (FTP) | `ftp://ftp.datasus.gov.br/dissemin/publicos/SIASUS/200801_/Dados/` |
| HIV · Painel Integrado | http://mediacenter.aids.gov.br/Transparencia_Ativa/Banco_PIMC_2025.zip |
| Página do painel de HIV | https://www.gov.br/aids/pt-br/indicadores-epidemiologicos/painel-de-monitoramento/painel-integrado-de-monitoramento-do-cuidado-do-hiv |
| CMED · preço máximo ao consumidor | https://www.gov.br/anvisa/pt-br/assuntos/medicamentos/cmed/precos |
| IBGE · população 2025 | https://ftp.ibge.gov.br/Estimativas_de_Populacao/Estimativas_2025/POP2025_20260828.xls |
| BNAFAR · estoques | https://dadosabertos.saude.gov.br/dataset/bnafar-posicao-de-estoque |

A lista da CMED é atualizada todo mês e o nome do arquivo muda. Se o link do arquivo mudar, baixe a lista "PMC - xls" mais recente na página da CMED e ajuste `CMED` em `src/config.py`.

---

## Como reproduzir

### 1. Ambiente
Python 3.13.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

### 2. Dados brutos
Crie a pasta `brutos/` com esta estrutura:

```
brutos/
├── farmacia_popular/   sntpbh.csv, sntpbd.csv, sntpdhc.csv, sntpba.csv, pfpbben.csv (descompactados)
├── sia/                AM??2606.dbc, AQ??2606.dbc, AR??2606.dbc (80 arquivos)
├── hiv/                PVHA_ano.parquet (de Banco_PIMC_2025.zip)
├── cmed/               lista_PMC__20261009_115232671.xlsx
├── ibge/               POP2025_20260828.xls
└── bnafar/             Posicao_Estoque_06-06-2026.csv (opcional, não usado)
```

Os arquivos do DataSUS ficam num servidor FTP, que os navegadores atuais não abrem. Para baixar os 80 arquivos de junho de 2026 (cerca de 200 MB):

```bash
mkdir -p brutos/sia && cd brutos/sia && for p in AM AQ AR; do for uf in AC AL AM AP BA CE DF ES GO MA MG MS MT PA PB PE PI PR RJ RN RO RR RS SC SE SP TO; do curl -sfO "ftp://ftp.datasus.gov.br/dissemin/publicos/SIASUS/200801_/Dados/${p}${uf}2606.dbc" || echo "sem ${p}${uf}2606"; done; done
```

O aviso `sem ARRR2606` é esperado: Roraima não tem arquivo de radioterapia no servidor.

O link do HIV é `http://` (sem o "s") e alguns navegadores bloqueiam o download. Pelo terminal funciona:

```bash
cd brutos/hiv && curl -LO "http://mediacenter.aids.gov.br/Transparencia_Ativa/Banco_PIMC_2025.zip" && unzip -o Banco_PIMC_2025.zip
```

### 3. Processamento

```bash
.venv/bin/python src/sia_para_parquet.py     # converte os .dbc do DataSUS (≈ 3 minutos)
.venv/bin/python src/consolidar.py           # gera saida/saude_municipios.csv e .parquet
.venv/bin/python src/gerar_xlsx.py           # gera saida/saude_municipios.xlsx
.venv/bin/python src/exportar_dashboard.py   # gera web/public/dados.js
```

`consolidar.py` confere a junção antes de gravar: 5.571 municípios únicos, todos com região de saúde, totais da Farmácia Popular iguais aos publicados e 600 municípios com dado de HIV. Se algo não bater, o script para com erro.

### 4. Para mudar o período de referência
Em `src/config.py`:
- `FARMACIA_POPULAR_MES`: mês da Farmácia Popular (formato `AAAAMM`);
- `SIA_COMPETENCIA`: mês dos arquivos do DataSUS (formato `AAMM`);
- `HIV_ANO`: ano da base de HIV;
- `CESTA`: preços da CMED.

---

## Metodologia e decisões

| # | Decisão | Motivo |
|---|---|---|
| S1 | Alto custo e câncer contados pelo município de **residência** do paciente (`AP_MUNPCN`) | Os remédios de alto custo são entregues em só 210 municípios, mas os pacientes moram em 5.480. Pelo município do estabelecimento (`AP_UFMUN`), quase todo o país sairia zerado. |
| S2 | Valores municipais para todos os municípios, com a marca `municipio_pequeno` (menos de 20 mil habitantes) e o total da região de saúde ao lado | Em municípios pequenos, câncer e alto custo têm números baixos que oscilam; o total da região de saúde dá estabilidade. Com o filtro por residência, 98% dos municípios pequenos têm dado. |
| S3 | Gasto do bolso calculado com a tabela oficial da CMED | O valor de R$ 180 por mês sugerido inicialmente não tinha fonte e fica muito acima do preço real dos genéricos. |
| S4 | Hipertensão e diabetes em grupos separados, sem fator de desduplicação | O Ministério já publica "só hipertensão", "só diabetes" e "hipertensão e diabetes" separadamente. |
| S5 | Estoques (BNAFAR) fora da tabela | Só 3.114 municípios aparecem, 34% dos lotes estão vencidos e o Ministério marca a base como "em manutenção". |
| S6 | HIV pelo Painel Integrado de Monitoramento do Cuidado (31/12/2025) | Substitui a planilha de Indicadores Clínicos (2022, 713 municípios). A base nova cobre 97,4% das pessoas em tratamento em 600 municípios. |
| S7 | Cada base no período mais recente disponível | Nenhum período específico foi pedido. Os indicadores mudam devagar (poucos por cento ao ano), e alinhar tudo numa data comum descartaria dados mais novos. |

### Como os pacientes do DataSUS são contados
Os arquivos APAC trazem um registro por autorização e por mês. Para contar pessoas, o projeto usa o cartão do SUS anonimizado (`AP_CNSPCN`). Ele vem vazio em parte dos registros: 43% no alto custo, 22% na quimioterapia e 72% na radioterapia. Por isso:

> pacientes = cartões únicos + registros sem cartão × (cartões únicos ÷ registros com cartão, no país, por tipo)

No Distrito Federal, parte dos registros traz o código da região administrativa (53xxxx); todos são somados a Brasília (530010).

---

## Custo do tratamento sem a Farmácia Popular

Base: lista CMED de 09/10/2026, preço máximo ao consumidor com ICMS de 18%.

| Doença | Tratamento considerado | Mínimo (genérico mais barato) | Mediano (mediana dos genéricos) |
|---|---|---|---|
| Hipertensão | losartana potássica 50 mg, 1 comprimido por dia (caixa com 30) | R$ 16,55/mês | R$ 46,52/mês |
| Diabetes | metformina 850 mg, 2 comprimidos por dia (caixa com 60) | R$ 42,45/mês | R$ 44,25/mês |
| Hipertensão e diabetes | as duas | R$ 59,00/mês | R$ 90,77/mês |
| Asma | beclometasona 250 mcg, 2 jatos 2 vezes ao dia = 120 doses (0,6 frasco de 200 doses) | R$ 43,94/mês | R$ 45,13/mês |

> gasto anual = 12 × (só hipertensão × preço hipertensão + só diabetes × preço diabetes + hipertensão e diabetes × (preço hipertensão + preço diabetes) + asma × preço asma)

O cálculo é **conservador**: considera um remédio por doença, na dose mais comum. Quem usa doses maiores ou mais de um remédio gastaria mais. Com os R$ 180 por mês do guia original, o total anual passaria de R$ 20 bilhões e seria facilmente contestado.

---

## Correções ao guia técnico original

O projeto partiu de um guia técnico com instruções de extração. Ao conferir as bases reais, algumas instruções estavam erradas:

| No guia | Na base real |
|---|---|
| Alto custo nos arquivos `AP` | Os remédios de alto custo ficam nos arquivos **`AM`** (APAC de medicamentos) |
| `AP_UFMUN` como município de residência | `AP_UFMUN` é o município do **estabelecimento**. O de residência é **`AP_MUNPCN`** |
| Filtrar por `MUNIC_RES` | `MUNIC_RES` é o nome usado nas internações (SIH), não no SIA |
| Valor do alto custo em `AP_VL_AP` | Nos arquivos `AM`, `AP_VL_AP` vem zerado; o projeto conta pacientes, não valores |
| Valor da quimioterapia em `AQ_VL_AP` | O campo não existe; o valor fica em `AP_VL_AP` |
| "CPFs únicos" por doença na Farmácia Popular | O Ministério publica pessoas atendidas por mês, não CPFs únicos por ano |
| R$ 180 por mês por idoso | Preço oficial dos genéricos: R$ 16,55 a R$ 90,77 por mês, conforme a doença e o cenário |
| Fator de 0,75 para quem tem as duas doenças | Desnecessário: os grupos já vêm separados |

---

## Dicionário de dados

Tabela `saida/saude_municipios.*`: uma linha por município, 37 colunas. Na planilha Excel, as colunas do tipo "Fórmula" são calculadas e os preços ficam editáveis na aba "Programas e Observações".

| Coluna | Descrição | Tipo | Unidade | Fonte | Referência |
|---|---|---|---|---|---|
| `cod_ibge7` | Código IBGE do município com 7 dígitos (chave para cruzar com outras bases do IBGE). | Identificação | código | IBGE | — |
| `cod_ibge6` | Código IBGE com 6 dígitos (sem o dígito verificador), usado pelo DataSUS e pelo Ministério da Saúde. | Identificação | código | IBGE | — |
| `municipio` | Nome do município. | Identificação | texto | IBGE | — |
| `uf` | Sigla do estado. | Identificação | texto | IBGE | — |
| `co_regiao_saude` | Código da região de saúde a que o município pertence (439 regiões no país). | Identificação | código | Ministério da Saúde · Portal de Dados Abertos do SUS · Programa Farmácia Popular do Brasil | 08/2026 |
| `no_regiao_saude` | Nome da região de saúde. | Identificação | texto | Ministério da Saúde · Portal de Dados Abertos do SUS · Programa Farmácia Popular do Brasil | 08/2026 |
| `populacao_2025` | População residente estimada. | Dado | pessoas | IBGE · Estimativas de população (POP2025_20260828) | 1º/07/2025 |
| `municipio_pequeno` | VERDADEIRO se a população for menor que o limite da aba "Programas e Observações" da planilha (padrão: 20.000 habitantes). Nesses municípios. prefira os totais da região de saúde. | Fórmula | sim/não | Calculado nesta planilha | — |
| `fp_total` | Pessoas atendidas pela Farmácia Popular no mês, em qualquer medicamento ou insumo. Contadas no município da FARMÁCIA, não da residência. | Dado | pessoas/mês | Ministério da Saúde · Portal de Dados Abertos do SUS · Programa Farmácia Popular do Brasil (pfpbben) | 08/2026 |
| `fp_so_hipertensao` | Pessoas atendidas com remédio gratuito apenas para hipertensão. | Dado | pessoas/mês | Ministério da Saúde · Portal de Dados Abertos do SUS · Programa Farmácia Popular do Brasil (sntpbh) | 08/2026 |
| `fp_so_diabetes` | Pessoas atendidas com remédio gratuito apenas para diabetes. | Dado | pessoas/mês | Ministério da Saúde · Portal de Dados Abertos do SUS · Programa Farmácia Popular do Brasil (sntpbd) | 08/2026 |
| `fp_hipertensao_e_diabetes` | Pessoas atendidas com remédios gratuitos para hipertensão E diabetes. Não se sobrepõe às duas colunas anteriores. | Dado | pessoas/mês | Ministério da Saúde · Portal de Dados Abertos do SUS · Programa Farmácia Popular do Brasil (sntpdhc) | 08/2026 |
| `fp_asma` | Pessoas atendidas com remédio gratuito para asma. | Dado | pessoas/mês | Ministério da Saúde · Portal de Dados Abertos do SUS · Programa Farmácia Popular do Brasil (sntpba) | 08/2026 |
| `alto_custo_pacientes` | Moradores do município que receberam remédio do Componente Especializado (alto custo: Alzheimer, Parkinson, artrite, transplantes etc.). Estimativa de pessoas únicas (ver aba "Programas e Observações" da planilha). | Dado (estimado) | pessoas | DataSUS · SIA/SUS · APAC por município de residência (campo AP_MUNPCN) · arquivos AM | 06/2026 |
| `quimioterapia_pacientes` | Moradores do município em quimioterapia pelo SUS. Estimativa de pessoas únicas. | Dado (estimado) | pessoas | DataSUS · SIA/SUS · APAC por município de residência (campo AP_MUNPCN) · arquivos AQ | 06/2026 |
| `radioterapia_pacientes` | Moradores do município em radioterapia pelo SUS. Estimativa de pessoas únicas. | Dado (estimado) | pessoas | DataSUS · SIA/SUS · APAC por município de residência (campo AP_MUNPCN) · arquivos AR | 06/2026 |
| `hiv_pessoas_em_tratamento_2025` | Pessoas vivendo com HIV em tratamento antirretroviral regular em 31/12/2025 (sem atraso ou com até 60 dias de atraso na retirada). Contadas no município do SERVIÇO que acompanha a pessoa, não da residência. Vazio quando o município não tem serviço com 50 ou mais pessoas em acompanhamento. | Dado | pessoas | Ministério da Saúde · Painel Integrado de Monitoramento do Cuidado do HIV e da Aids (PVHA_ano) | 31/12/2025 |
| `fp_total_por_mil_hab` | fp_total para cada mil habitantes. | Fórmula | por mil hab. | Calculado nesta planilha | — |
| `fp_so_hipertensao_por_mil_hab` | fp_so_hipertensao para cada mil habitantes. | Fórmula | por mil hab. | Calculado nesta planilha | — |
| `fp_so_diabetes_por_mil_hab` | fp_so_diabetes para cada mil habitantes. | Fórmula | por mil hab. | Calculado nesta planilha | — |
| `fp_hipertensao_e_diabetes_por_mil_hab` | fp_hipertensao_e_diabetes para cada mil habitantes. | Fórmula | por mil hab. | Calculado nesta planilha | — |
| `fp_asma_por_mil_hab` | fp_asma para cada mil habitantes. | Fórmula | por mil hab. | Calculado nesta planilha | — |
| `alto_custo_pacientes_por_mil_hab` | alto_custo_pacientes para cada mil habitantes. | Fórmula | por mil hab. | Calculado nesta planilha | — |
| `quimioterapia_pacientes_por_mil_hab` | quimioterapia_pacientes para cada mil habitantes. | Fórmula | por mil hab. | Calculado nesta planilha | — |
| `fp_total_regiao_saude` | Soma de fp_total em todos os municípios da mesma região de saúde. | Fórmula | pessoas/mês | Calculado nesta planilha | 08/2026 |
| `fp_so_hipertensao_regiao_saude` | Soma de fp_so_hipertensao na região de saúde. | Fórmula | pessoas/mês | Calculado nesta planilha | 08/2026 |
| `fp_so_diabetes_regiao_saude` | Soma de fp_so_diabetes na região de saúde. | Fórmula | pessoas/mês | Calculado nesta planilha | 08/2026 |
| `fp_hipertensao_e_diabetes_regiao_saude` | Soma de fp_hipertensao_e_diabetes na região de saúde. | Fórmula | pessoas/mês | Calculado nesta planilha | 08/2026 |
| `fp_asma_regiao_saude` | Soma de fp_asma na região de saúde. | Fórmula | pessoas/mês | Calculado nesta planilha | 08/2026 |
| `alto_custo_pacientes_regiao_saude` | Soma de alto_custo_pacientes na região de saúde. | Fórmula | pessoas | Calculado nesta planilha | 06/2026 |
| `quimioterapia_pacientes_regiao_saude` | Soma de quimioterapia_pacientes na região de saúde. | Fórmula | pessoas | Calculado nesta planilha | 06/2026 |
| `radioterapia_pacientes_regiao_saude` | Soma de radioterapia_pacientes na região de saúde. | Fórmula | pessoas | Calculado nesta planilha | 06/2026 |
| `fp_total_por_mil_hab_regiao_saude` | fp_total da região de saúde para cada mil habitantes da região. Melhor medida para comparar municípios pequenos. | Fórmula | por mil hab. | Calculado nesta planilha | 08/2026 |
| `bolso_anual_minimo_rs` | Quanto as pessoas atendidas pela Farmácia Popular gastariam por ano comprando o tratamento, no cenário MÍNIMO (genérico mais barato). = 12 × (só hipertensão × preço hipertensão + só diabetes × preço diabetes + ambas × (preço hipertensão + preço diabetes) + asma × preço asma). | Fórmula | R$/ano | Calculado nesta planilha · preços da CMED na aba "Programas e Observações" da planilha | preços de 09/10/2026 |
| `bolso_anual_mediano_rs` | Mesmo cálculo, no cenário MEDIANO (preço mediano dos genéricos). | Fórmula | R$/ano | Calculado nesta planilha · preços da CMED na aba "Programas e Observações" da planilha | preços de 09/10/2026 |
| `txt_farmacia_popular` | Frase pronta para mensagem com o número de moradores atendidos (pressão ou diabetes). | Texto | texto | Gerado a partir de fp_so_hipertensao + fp_so_diabetes + fp_hipertensao_e_diabetes | 08/2026 |
| `txt_bolso` | Frase pronta com o gasto anual mínimo. É texto fixo: NÃO se atualiza se os preços da aba "Programas e Observações" da planilha forem alterados. | Texto | texto | Gerado a partir do cenário mínimo com os preços originais | — |

---

## Painel web

`web/public/index.html` é uma página estática (HTML, CSS e JavaScript, sem bibliotecas externas além das fontes do Google Fonts). Os dados vêm de `web/public/dados.js`.

**O que o painel mostra**
1. **Totais do Brasil** no topo.
2. **Busca por município**, com filtro por estado. Para o município escolhido:
   - pessoas na Farmácia Popular por doença e por mil habitantes, comparando município, região de saúde, estado e Brasil. Se a cidade não tem farmácia credenciada, o painel avisa e mostra os números da região;
   - câncer, alto custo e HIV. Em municípios com menos de 20 mil habitantes, o destaque é o total da região de saúde;
   - gasto anual do bolso sem a Farmácia Popular;
   - frases prontas para mensagem, com data e botão de copiar.
3. **Ranking de municípios**, ordenável por cinco indicadores.
4. **Série histórica** da Farmácia Popular (dezembro de 2016 a agosto de 2026) e **gráfico por estado**.
5. **Preços editáveis**: mudar o custo mensal de um tratamento recalcula o painel inteiro. Há os cenários mínimo e mediano.
6. **Estoques e repasses**: explica o que ficou de fora e por quê.
7. **Como ler**: fontes, regras e cuidados.

**Rodar localmente**

```bash
python3 -m http.server 8766 --directory web/public
```

Depois abra http://localhost:8766.

**Publicar no Firebase Hosting**

```bash
cd web && firebase deploy --only hosting --project saude-municipios
```

---

## Planilha Excel

`saida/saude_municipios.xlsx` tem três abas:
- **Dados:** os 5.571 municípios. As colunas calculadas (por mil habitantes, totais da região de saúde e gasto do bolso) são fórmulas.
- **Dicionário de Dados:** descrição, tipo, unidade, fonte e período de cada coluna.
- **Programas e Observações:** parâmetros editáveis (preços e limite de município pequeno), totais do Brasil, descrição de cada programa, bases avaliadas e não incluídas e observações de leitura.

O arquivo é gerado sem valores calculados e o Excel recalcula as fórmulas ao abrir.

---

## Limitações e cuidados de leitura

- **Os números descrevem municípios, não pessoas.**
- **Farmácia Popular é contada na cidade da farmácia.** 1.065 municípios não têm farmácia credenciada e aparecem com zero; cidades pequenas com farmácia atendem vizinhos (Pedranópolis/SP tem 439 atendidos por mil habitantes). Para comparar municípios, use as colunas da região de saúde.
- **HIV é contado no município do serviço de acompanhamento,** não no de residência. As 22.840 pessoas acompanhadas em serviços com menos de 50 pacientes só são publicadas somadas por estado, por sigilo, e ficam fora da coluna municipal.
- **Pacientes de alto custo e câncer são estimados,** porque o cartão do SUS vem vazio em parte dos registros.
- **Radioterapia tem números pequenos** e Roraima não tem arquivo no DataSUS.
- **As datas de referência variam entre as bases** (de julho de 2025 a outubro de 2026). Os indicadores mudam devagar, mas cada número deve ser citado com a própria data.
- **Não some as doenças** para dizer "X pessoas dependem do SUS".
- **Gasto do bolso é uma estimativa conservadora,** não uma previsão.

---

## Pendências

- [ ] Agentes Comunitários de Saúde por município (relatório público do e-Gestor AB).
- [ ] Repasse federal do Componente Básico da Assistência Farmacêutica (CBAF) por município: anexo da Portaria GM/MS nº 9.887/2025, ou cálculo pela regra (valor por habitante conforme o IDHM × população).
- [ ] Conferir os números de alto custo e quimioterapia de alguns municípios com uma fonte independente (TabNet/DataSUS).
- [ ] Coluna com as pessoas com tratamento de HIV interrompido (139.928 no país em 2025).
