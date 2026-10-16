"""Caminhos do projeto de dados de saúde (separado do projeto eleitoral)."""
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
BRUTOS = RAIZ / "brutos"
TRABALHO = RAIZ / "trabalho"
PARQUET = TRABALHO / "parquet"

FARMACIA_POPULAR = BRUTOS / "farmacia_popular"
FARMACIA_POPULAR_MES = "202608"  # mês mais recente publicado
SIA = BRUTOS / "sia"
SIA_COMPETENCIA = "2606"  # junho de 2026: mês mais recente com todos os estados
HIV = BRUTOS / "hiv" / "PVHA_ano.parquet"  # Painel Integrado de Monitoramento do Cuidado do HIV (Banco_PIMC_2025.zip)
HIV_ANO = 2025
CMED = BRUTOS / "cmed" / "lista_PMC__20261009_115232671.xlsx"
POPULACAO = BRUTOS / "ibge" / "POP2025_20260828.xls"
BNAFAR = BRUTOS / "bnafar" / "Posicao_Estoque_06-06-2026.csv"

# Município pequeno: abaixo disso, câncer e alto custo são mostrados agregados por região de saúde.
LIMITE_MUNICIPIO_PEQUENO = 20_000

# Custo mensal do tratamento sem a Farmácia Popular (lista CMED de 09/10/2026, PMC com ICMS de 18%).
# "minimo" = genérico mais barato no preço máximo permitido; "mediano" = mediana dos genéricos.
# Posologia padrão e conservadora; a Farmácia Popular tem outros remédios para as mesmas doenças.
CESTA = {
    "hipertensao": {"descricao": "losartana potássica 50 mg, 1 comprimido/dia (caixa com 30)",
                    "minimo": 16.55, "mediano": 46.52},
    "diabetes": {"descricao": "metformina 850 mg, 2 comprimidos/dia (caixa com 60)",
                 "minimo": 42.45, "mediano": 44.25},
    "asma": {"descricao": "beclometasona 250 mcg, 2 jatos 2x/dia = 120 doses (0,6 frasco de 200 doses)",
             "minimo": round(0.6 * 73.23, 2), "mediano": round(0.6 * 75.21, 2)},
}
