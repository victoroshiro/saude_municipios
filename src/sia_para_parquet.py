"""Converte os APAC do SIA/SUS (.dbc) em parquet, só com as colunas usadas.

Arquivos: AM (medicamentos de alto custo, CEAF), AQ (quimioterapia), AR (radioterapia).
Campos-chave (conferidos nos próprios arquivos de 06/2026):
    AP_MUNPCN  município de RESIDÊNCIA do paciente (IBGE, 6 dígitos)  <- usar este
    AP_UFMUN   município do ESTABELECIMENTO (não usar para contar moradores)
    AP_CNSPCN  cartão SUS do paciente, anonimizado (vazio em parte de AQ/AR)
"""
import sys
from concurrent.futures import ProcessPoolExecutor

import pandas as pd
import pyreaddbc
from dbfread import DBF

from config import PARQUET, SIA, SIA_COMPETENCIA, TRABALHO

COLUNAS = ["AP_CMP", "AP_AUTORIZ", "AP_PRIPAL", "AP_VL_AP", "AP_UFMUN", "AP_MUNPCN", "AP_CNSPCN",
           "AP_NUIDADE", "AP_SEXO", "AP_CIDPRI", "AP_TPAPAC", "AQ_CID10", "AR_CID10"]


def converter(dbc):
    dbf = TRABALHO / "dbf" / (dbc.stem + ".dbf")
    dbf.parent.mkdir(parents=True, exist_ok=True)
    pyreaddbc.dbc2dbf(str(dbc), str(dbf))
    tabela = DBF(str(dbf), encoding="iso-8859-1", char_decode_errors="replace")
    usar = [c for c in COLUNAS if c in tabela.field_names]
    df = pd.DataFrame(({c: r[c] for c in usar} for r in tabela), columns=usar)
    df.insert(0, "arquivo", dbc.stem)
    df.insert(1, "tipo", dbc.stem[:2])
    df.insert(2, "uf_arquivo", dbc.stem[2:4])
    saida = PARQUET / "sia" / (dbc.stem + ".parquet")
    saida.parent.mkdir(parents=True, exist_ok=True)
    df.astype({c: "string" for c in df.columns if c != "AP_VL_AP"}).to_parquet(saida, index=False)
    dbf.unlink()
    return dbc.stem, len(df)


if __name__ == "__main__":
    arquivos = sorted(SIA.glob(f"A[MQR]??{SIA_COMPETENCIA}.dbc"))
    print(f"{len(arquivos)} arquivos")
    with ProcessPoolExecutor(max_workers=8) as ex:
        for nome, n in ex.map(converter, arquivos):
            print(f"{nome}: {n:,} linhas", flush=True)
