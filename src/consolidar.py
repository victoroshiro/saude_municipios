"""Tabela consolidada de saúde por município (uma linha por município, chave IBGE de 7 dígitos)."""
import re

import duckdb
import numpy as np
import pandas as pd

from config import (CESTA, FARMACIA_POPULAR, FARMACIA_POPULAR_MES, HIV, HIV_ANO, LIMITE_MUNICIPIO_PEQUENO,
                    PARQUET, POPULACAO, RAIZ)

SAIDA = RAIZ / "saida"


def populacao() -> pd.DataFrame:
    p = pd.read_excel(POPULACAO, "Municípios", header=1, dtype=str)
    p = p[p["COD. MUNIC"].notna() & p["COD. UF"].str.fullmatch(r"\d{2}", na=False)]
    p["cod_ibge7"] = p["COD. UF"] + p["COD. MUNIC"].str.zfill(5)
    p["populacao_2025"] = p["POPULAÇÃO ESTIMADA"].map(lambda s: int(re.sub(r"\D", "", s.split("(")[0])))
    return p[["cod_ibge7", "UF", "NOME DO MUNICÍPIO", "populacao_2025"]].rename(
        columns={"UF": "uf", "NOME DO MUNICÍPIO": "municipio"})


def farmacia_popular() -> pd.DataFrame:
    arquivos = {"pfpbben": "fp_total", "sntpbh": "fp_so_hipertensao", "sntpbd": "fp_so_diabetes",
                "sntpdhc": "fp_hipertensao_e_diabetes", "sntpba": "fp_asma"}
    partes = []
    for arq, col in arquivos.items():
        d = pd.read_csv(FARMACIA_POPULAR / f"{arq}.csv", dtype=str)
        d = d[d["co_anomes"] == FARMACIA_POPULAR_MES]
        partes.append(d.set_index("co_ibge")["vl_indicador_calculado_mun"].astype(float).rename(col))
        if arq == "pfpbben":
            regiao = d.set_index("co_ibge")[["co_regiao_saude", "no_regiao_saude"]]
    fp = pd.concat(partes, axis=1).fillna(0).astype(int).join(regiao)
    fp.index.name = "cod_ibge6"
    return fp.reset_index()


def sia() -> pd.DataFrame:
    """Pacientes por município de residência (AP_MUNPCN), junho de 2026.

    O cartão SUS anonimizado vem vazio em parte dos registros. Pacientes estimados =
    cartões únicos + registros sem cartão × (cartões únicos / registros com cartão, no país, por tipo).
    """
    con = duckdb.connect()
    con.sql(f"CREATE VIEW s AS SELECT * FROM read_parquet('{PARQUET}/sia/*.parquet', union_by_name=true)")
    fator = con.sql("""SELECT tipo, count(DISTINCT nullif(trim(AP_CNSPCN),'')) / count(*) FILTER (trim(AP_CNSPCN)<>'') f
                       FROM s GROUP BY 1""").df().set_index("tipo")["f"]
    # No DF, parte dos registros traz o código da região administrativa (53xxxx); todas pertencem a Brasília (530010).
    m = con.sql("""SELECT CASE WHEN AP_MUNPCN LIKE '53%' THEN '530010' ELSE AP_MUNPCN END cod_ibge6, tipo, count(*) registros,
                          count(*) FILTER (trim(AP_CNSPCN)<>'') com_cns,
                          count(DISTINCT nullif(trim(AP_CNSPCN),'')) cns_unicos
                   FROM s GROUP BY ALL""").df()
    m["pacientes"] = m["cns_unicos"] + (m["registros"] - m["com_cns"]) * m["tipo"].map(fator)
    nomes = {"AM": "alto_custo_pacientes", "AQ": "quimioterapia_pacientes", "AR": "radioterapia_pacientes"}
    out = m.pivot(index="cod_ibge6", columns="tipo", values="pacientes").rename(columns=nomes)
    return out.round().fillna(0).astype(int).reset_index()


def hiv() -> pd.DataFrame:
    """Pessoas em tratamento antirretroviral regular (status 'Tarv') em 31/12 do ano, por município.

    O município é o do SERVIÇO que acompanha a pessoa (instituição que pediu o último exame),
    não o de residência. Serviços em municípios com menos de 50 pessoas no cuidado vêm agrupados
    por UF (código UF99999) e não entram no valor municipal.
    """
    d = duckdb.sql(f"""
        SELECT ibge_inst_solicitante::VARCHAR AS cod_ibge7, count(*) AS hiv_pessoas_em_tratamento_{HIV_ANO}
        FROM read_parquet('{HIV}')
        WHERE ano = {HIV_ANO} AND status_fim_ano = 'Tarv'
          AND ibge_inst_solicitante IS NOT NULL AND ibge_inst_solicitante % 100000 <> 99999
        GROUP BY 1""").df()
    return d


def consolidar() -> pd.DataFrame:
    t = populacao()
    t["cod_ibge6"] = t["cod_ibge7"].str[:6]
    for parte in (farmacia_popular(), sia()):
        t = t.merge(parte, on="cod_ibge6", how="left", validate="one_to_one")
    t = t.merge(hiv(), on="cod_ibge7", how="left", validate="one_to_one")
    for c in ["alto_custo_pacientes", "quimioterapia_pacientes", "radioterapia_pacientes"]:
        t[c] = t[c].fillna(0).astype(int)

    t["municipio_pequeno"] = t["populacao_2025"] < LIMITE_MUNICIPIO_PEQUENO
    por_mil = lambda c: (1000 * t[c] / t["populacao_2025"]).round(1)
    for c in ["fp_total", "fp_so_hipertensao", "fp_so_diabetes", "fp_hipertensao_e_diabetes", "fp_asma",
              "alto_custo_pacientes", "quimioterapia_pacientes"]:
        t[f"{c}_por_mil_hab"] = por_mil(c)

    # Totais da região de saúde, para mostrar no lugar do municipal quando o município é pequeno
    # A Farmácia Popular conta pelo município da farmácia (cidades sem farmácia credenciada ficam com zero),
    # então o total da região de saúde também é mostrado para ela.
    for c in ["fp_total", "fp_so_hipertensao", "fp_so_diabetes", "fp_hipertensao_e_diabetes", "fp_asma",
              "alto_custo_pacientes", "quimioterapia_pacientes", "radioterapia_pacientes"]:
        t[f"{c}_regiao_saude"] = t.groupby("co_regiao_saude")[c].transform("sum")
    pop_reg = t.groupby("co_regiao_saude")["populacao_2025"].transform("sum")
    t["fp_total_por_mil_hab_regiao_saude"] = (1000 * t["fp_total_regiao_saude"] / pop_reg).round(1)

    # Impacto no bolso: pessoas atendidas no mês × custo mensal da cesta (cenários mínimo e mediano)
    for cen in ("minimo", "mediano"):
        mensal = (t["fp_so_hipertensao"] * CESTA["hipertensao"][cen]
                  + t["fp_so_diabetes"] * CESTA["diabetes"][cen]
                  + t["fp_hipertensao_e_diabetes"] * (CESTA["hipertensao"][cen] + CESTA["diabetes"][cen])
                  + t["fp_asma"] * CESTA["asma"][cen])
        t[f"bolso_anual_{cen}_rs"] = (12 * mensal).round(0)

    pessoas_hd = t["fp_so_hipertensao"] + t["fp_so_diabetes"] + t["fp_hipertensao_e_diabetes"]
    t["txt_farmacia_popular"] = [
        f"{n:,.0f}".replace(",", ".") + " moradores pegam remédio de pressão ou diabetes de graça na Farmácia Popular"
        for n in pessoas_hd]
    t["txt_bolso"] = [
        "Sem o programa, gastariam pelo menos R$ " + (f"{v / 1e6:,.1f} milhões" if v >= 1e6 else f"{v / 1e3:,.0f} mil").replace(",", "X").replace(".", ",").replace("X", ".") + " por ano"
        for v in t["bolso_anual_minimo_rs"]]

    ordem = ["cod_ibge7", "cod_ibge6", "municipio", "uf", "co_regiao_saude", "no_regiao_saude", "populacao_2025",
             "municipio_pequeno"]
    return t[ordem + [c for c in t.columns if c not in ordem]].sort_values("cod_ibge7").reset_index(drop=True)


def checar(t: pd.DataFrame) -> None:
    assert len(t) == 5571 and t["cod_ibge7"].is_unique, len(t)
    assert t["fp_total"].notna().all(), "município sem Farmácia Popular"
    assert t["co_regiao_saude"].notna().all(), "município sem região de saúde"
    assert t["hiv_pessoas_em_tratamento_2025"].notna().sum() == 600, "municípios com HIV"
    for c, esperado in {"fp_so_hipertensao": 4962509, "fp_hipertensao_e_diabetes": 3239501}.items():
        assert t[c].sum() == esperado, (c, t[c].sum())


if __name__ == "__main__":
    t = consolidar()
    checar(t)
    SAIDA.mkdir(exist_ok=True)
    t.to_csv(SAIDA / "saude_municipios.csv", index=False, encoding="utf-8-sig", sep=";", decimal=",")
    t.to_parquet(SAIDA / "saude_municipios.parquet", index=False)
    print(t.shape)
    print(t[["municipio", "uf", "populacao_2025", "fp_total", "fp_hipertensao_e_diabetes", "alto_custo_pacientes",
             "quimioterapia_pacientes", "hiv_pessoas_em_tratamento_2025", "bolso_anual_minimo_rs"]].head())
