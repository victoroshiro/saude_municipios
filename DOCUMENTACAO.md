# Dados de Saúde e Remédios por Município

Projeto separado do Mapa do 2º Turno. Última atualização: 15/10/2026.

## 1. Objetivo
Responder, por município:
1. Quantas pessoas pegam remédio de graça na Farmácia Popular (pressão, diabetes e asma).
2. Quantos moradores dependem de remédio de alto custo, quimioterapia, radioterapia e tratamento de HIV pelo SUS.
3. Quanto essas pessoas pagariam do próprio bolso sem a Farmácia Popular.

Só dados públicos e agregados por município. Nenhum dado individual sai do processamento.

## 2. Decisões
| # | Decisão | Motivo |
|---|---|---|
| S1 | Município de **residência** do paciente (`AP_MUNPCN`) nos dados do DataSUS | O alto custo é entregue em 210 municípios, mas os pacientes moram em 5.480. Pelo município do estabelecimento (`AP_UFMUN`), quase todo o país sairia zerado. |
| S2 | Valores municipais para todos os municípios, com a marca `municipio_pequeno` (menos de 20 mil habitantes) e o total da região de saúde ao lado | Pedido do time: "se tiver de tudo, melhor". Em município pequeno, o número é baixo e oscila; o total regional dá estabilidade. |
| S3 | Impacto no bolso calculado com a tabela oficial de preços da CMED, e não com R$ 180 por mês | Os R$ 180 não tinham fonte e ficam muito acima do preço real dos genéricos. |
| S4 | Pressão e diabetes contadas em grupos separados, sem fator de desduplicação | O Ministério já publica "só hipertensão", "só diabetes" e "hipertensão e diabetes" separados. O fator de 0,75 do guia era desnecessário. |
| S5 | Estoques (BNAFAR) fora da tabela | Só 3.114 municípios aparecem, 34% dos lotes estão vencidos e o Ministério marca a base como "em manutenção". |
| S6 | HIV: pessoas em tratamento regular em 31/12/2025, pelo Painel Integrado de Monitoramento do Cuidado do HIV | Substitui a planilha de Indicadores Clínicos (2022, 713 municípios). A base nova traz 600 municípios com 97,4% das pessoas em tratamento. O município é o do serviço de acompanhamento, não o de residência. |
| S7 | "Cluster A / 711 cidades" do guia desconsiderado | Pedido do usuário. |

## 3. Fontes e validação
| Base | Arquivo | Período | Validação |
|---|---|---|---|
| Farmácia Popular (Portal de Dados Abertos do SUS) | `brutos/farmacia_popular/` (5 arquivos) | dezembro de 2016 a 2025 e agosto de 2026; a tabela usa 08/2026 | 5.571 municípios, sem duplicados. Soma municipal ≈ total nacional publicado (diferença < 0,5%). |
| DataSUS SIA, APAC | `brutos/sia/` (80 arquivos `.dbc`: AM 27, AQ 27, AR 26) | movimento de junho de 2026 (mês mais recente com todos os estados) | Roraima não tem arquivo de radioterapia no servidor. Campos conferidos nos arquivos. |
| HIV, Painel Integrado de Monitoramento do Cuidado (Ministério da Saúde) | `brutos/hiv/PVHA_ano.parquet` (de `Banco_PIMC_2025.zip`) | 2016 a 2025; a tabela usa 31/12/2025 | Brasil: 877.658 em tratamento regular. 854.817 (97,4%) em 600 municípios; 22.840 só por UF (serviços com menos de 50 pessoas). O município é o do serviço que pediu o último exame. A planilha antiga `Indicadores Clinicos.xlsx` (2022) não é mais usada. |
| Preços CMED, preço máximo ao consumidor (Anvisa) | `brutos/cmed/lista_PMC__20261009_115232671.xlsx` | 09/10/2026 | 26.635 apresentações. |
| População estimada (IBGE) | `brutos/ibge/POP2025_20260828.xls` | 1º/07/2025 | 5.571 municípios; total 213.421.037. |
| Estoques BNAFAR | `brutos/bnafar/Posicao_Estoque_06-06-2026.csv` | 06/06/2026 | Não usada (decisão S5). |

### Correções ao guia técnico recebido
- **Alto custo:** os remédios ficam nos arquivos **`AM`**, não `AP`.
- **Município de residência:** é o campo **`AP_MUNPCN`**. O `AP_UFMUN` é o do estabelecimento. `MUNIC_RES` é o nome usado nas internações (SIH), não no SIA.
- **Valor dos remédios de alto custo:** o campo `AP_VL_AP` vem zerado nos arquivos `AM`, porque o custo é pago por outro mecanismo. Contamos pacientes, não valores.
- **Valor da quimioterapia:** fica em `AP_VL_AP`; não existe `AQ_VL_AP`.
- **Cartão do SUS anonimizado (`AP_CNSPCN`):** vem vazio em 43% dos registros de alto custo, 22% dos de quimioterapia e 72% dos de radioterapia. Pacientes estimados = cartões únicos + registros sem cartão × (cartões únicos ÷ registros com cartão, no país, por tipo).
- **Distrito Federal:** parte dos registros traz o código da região administrativa (53xxxx); todos foram somados a Brasília (530010).
- **Farmácia Popular:** a contagem é feita pelo município da farmácia. Os 1.065 municípios com zero não têm farmácia credenciada, e cidades pequenas com farmácia atendem vizinhos (Pedranópolis/SP tem 439 atendidos por mil habitantes). Use o total da região de saúde para comparar.

## 4. Custo do tratamento sem a Farmácia Popular
Base: lista CMED de 09/10/2026, preço máximo ao consumidor com ICMS de 18%.

| Doença | Tratamento padrão | Mínimo (genérico mais barato) | Mediano (mediana dos genéricos) |
|---|---|---|---|
| Hipertensão | losartana 50 mg, 1 comprimido por dia | R$ 16,55/mês | R$ 46,52/mês |
| Diabetes | metformina 850 mg, 2 comprimidos por dia | R$ 42,45/mês | R$ 44,25/mês |
| Hipertensão e diabetes | as duas | R$ 59,00/mês | R$ 90,77/mês |
| Asma | beclometasona 250 mcg, 120 doses por mês | R$ 43,94/mês | R$ 45,13/mês |

Impacto anual = pessoas atendidas no mês × custo mensal × 12. É conservador: há quem use doses maiores ou mais de um remédio.

## 5. Resultado (Brasil)
| Indicador | Total |
|---|---|
| Pessoas atendidas pela Farmácia Popular em 08/2026 | 12,96 mi |
| · só hipertensão | 4,96 mi |
| · só diabetes | 1,81 mi |
| · hipertensão e diabetes | 3,24 mi |
| · asma | 0,88 mi |
| Pacientes de remédio de alto custo, 06/2026 (estimativa) | 3,28 mi |
| Pacientes em quimioterapia, 06/2026 (estimativa) | 0,36 mi |
| Pessoas em tratamento de HIV, 31/12/2025 (600 municípios com serviço) | 0,85 mi (Brasil: 0,88 mi) |
| Gasto do bolso sem a Farmácia Popular, por ano | **R$ 4,7 bi (mínimo) a R$ 7,7 bi (mediano)** |

## 6. Como gerar a tabela
```bash
cd ~/Downloads/"Dados Saude"
.venv/bin/python src/sia_para_parquet.py   # converte os .dbc (≈ 3 min)
.venv/bin/python src/consolidar.py         # gera saida/saude_municipios.csv e .parquet
.venv/bin/python src/gerar_xlsx.py         # gera saida/saude_municipios.xlsx (Dados, Dicionário de Dados, Programas e Observações)
```
Na planilha, as colunas calculadas são fórmulas do Excel e os preços da cesta ficam editáveis na aba "Programas e Observações". O arquivo é gerado sem valores calculados e o Excel recalcula ao abrir.
O CSV usa `;` como separador e vírgula decimal, para abrir direto no Excel em português.

## Painel web (`web/`)
- `web/public/index.html`: painel interativo, seguindo as orientações iniciais do time:
  1. Farmácia Popular por doença (só pressão, só diabetes, as duas, asma), com comparação por mil habitantes entre município, região de saúde, estado e Brasil.
  2. Câncer, alto custo e HIV. Em municípios com menos de 20 mil habitantes, o destaque é o total da região de saúde, e o valor municipal aparece embaixo.
  3. Gasto do bolso, com os preços da cesta editáveis e os cenários mínimo e mediano.
  4. Estoques e repasses: explica por que o BNAFAR foi excluído e que CBAF e ACS estão pendentes.
  - Mais: frases prontas com data, ranking de municípios por estado, série da Farmácia Popular (2016–2026) e gráfico por estado.
- `web/public/dados.js`: gerado por `src/exportar_dashboard.py`, a partir de `saida/saude_municipios.parquet`.
- `web/firebase.json`: configuração do Firebase Hosting (falta criar o projeto).

## 7. Pendências
- [ ] Agentes Comunitários de Saúde por município (relatório público do e-Gestor AB).
- [ ] Repasse federal do postinho (CBAF): anexo da Portaria GM/MS nº 9.887/2025 ou cálculo pela regra (valor por habitante conforme o IDHM × população).
- [ ] Validar os números de alto custo e quimioterapia de alguns municípios com uma fonte independente (TabNet/DataSUS).
