"""Gera web/public/dados.js para o painel de saúde.

Uso:
    .venv/bin/python src/exportar_dashboard.py   (depois de src/consolidar.py)
"""
import json

import duckdb
import pandas as pd

from config import CESTA, FARMACIA_POPULAR, HIV, LIMITE_MUNICIPIO_PEQUENO, RAIZ

ENTRADA = RAIZ / "saida" / "saude_municipios.parquet"
SAIDA = RAIZ / "web" / "public" / "dados.js"

# Colunas enviadas para a página, em formato compacto (lista de linhas).
CAMPOS = [
    ("cod", "cod_ibge7"), ("nome", "municipio"), ("uf", "uf"), ("reg", "co_regiao_saude"), ("pop", "populacao_2025"),
    ("fp", "fp_total"), ("h", "fp_so_hipertensao"), ("d", "fp_so_diabetes"), ("hd", "fp_hipertensao_e_diabetes"),
    ("a", "fp_asma"), ("ac", "alto_custo_pacientes"), ("qt", "quimioterapia_pacientes"),
    ("rt", "radioterapia_pacientes"), ("hiv", "hiv_pessoas_em_tratamento_2025"),
]


def serie_farmacia_popular() -> list[dict]:
    """Total nacional por mês publicado (dezembro de cada ano e o mês mais recente)."""
    arqs = {"sntpbh": "h", "sntpbd": "d", "sntpdhc": "hd", "sntpba": "a"}
    partes = []
    for arq, chave in arqs.items():
        d = duckdb.sql(f"""SELECT co_anomes, sum(vl_indicador_calculado_mun::DOUBLE)::BIGINT v
                           FROM read_csv('{FARMACIA_POPULAR / (arq + ".csv")}', all_varchar=true) GROUP BY 1""").df()
        partes.append(d.set_index("co_anomes")["v"].rename(chave))
    s = pd.concat(partes, axis=1).sort_index()
    return [{"mes": f"{k[4:]}/{k[:4]}", **{c: int(v) for c, v in row.items()}} for k, row in s.iterrows()]


def serie_hiv() -> list[dict]:
    d = duckdb.sql(f"""SELECT ano, count(*) FILTER (status_fim_ano = 'Tarv') tarv,
                              count(*) FILTER (status_fim_ano = 'Interrupção de Tarv') interrupcao
                       FROM read_parquet('{HIV}') GROUP BY 1 ORDER BY 1""").df()
    return [{"ano": int(r.ano), "tarv": int(r.tarv), "interrupcao": int(r.interrupcao)} for r in d.itertuples()]


def main() -> None:
    t = pd.read_parquet(ENTRADA).sort_values(["uf", "municipio"])
    regioes = (t.groupby("co_regiao_saude")
               .agg(nome=("no_regiao_saude", "first"), uf=("uf", lambda s: s.mode()[0]), pop=("populacao_2025", "sum"),
                    fp=("fp_total", "sum"), h=("fp_so_hipertensao", "sum"), d=("fp_so_diabetes", "sum"),
                    hd=("fp_hipertensao_e_diabetes", "sum"), a=("fp_asma", "sum"), ac=("alto_custo_pacientes", "sum"),
                    qt=("quimioterapia_pacientes", "sum"), rt=("radioterapia_pacientes", "sum"), n=("cod_ibge7", "size")))
    linhas = []
    for r in t.itertuples(index=False):
        linha = []
        for _, col in CAMPOS:
            v = getattr(r, col)
            linha.append(None if pd.isna(v) else (int(v) if isinstance(v, float) and v == int(v) else v))
        linhas.append(linha)
    dados = {
        "campos": [c for c, _ in CAMPOS],
        "municipios": linhas,
        "regioes": {k: {c: (int(v) if c not in ("nome", "uf") else v) for c, v in row.items()} for k, row in regioes.iterrows()},
        "cesta": CESTA,
        "limite_pequeno": LIMITE_MUNICIPIO_PEQUENO,
        "serie_fp": serie_farmacia_popular(),
        "serie_hiv": serie_hiv(),
        "referencias": {"fp": "agosto de 2026", "sia": "junho de 2026", "hiv": "31/12/2025",
                        "pop": "1º/07/2025", "cmed": "09/10/2026"},
        "gerado_em": pd.Timestamp.now(tz="America/Sao_Paulo").strftime("%d/%m/%Y %H:%M"),
    }
    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    SAIDA.write_text("window.DADOS = " + json.dumps(dados, ensure_ascii=False, separators=(",", ":")) + ";\n", encoding="utf-8")
    print(f"{SAIDA} · {SAIDA.stat().st_size / 1024:.0f} KB · {len(linhas)} municípios · {len(regioes)} regiões")


if __name__ == "__main__":
    main()
