"""
utils.py
Transformações e métricas derivadas a partir das séries brutas do BCB.
"""

from __future__ import annotations

import pandas as pd


def para_mensal(df: pd.DataFrame, agregacao: str = "last") -> pd.DataFrame:
    """
    Reamostra uma série diária/irregular para frequência mensal (fim do mês).

    Usa dt.to_period('M') + groupby em vez de resample('ME'), porque o alias
    de frequência mudou entre versões do pandas ('M' em versões antigas,
    'ME' a partir do pandas 2.2) — assim a função funciona em qualquer versão.
    """
    if df.empty:
        return df
    d = df.copy()
    d["_periodo"] = d["Data"].dt.to_period("M")
    agrupado = d.groupby("_periodo")["Valor"]
    valor = agrupado.last() if agregacao == "last" else agrupado.mean()
    out = valor.reset_index()
    out["Data"] = out["_periodo"].dt.to_timestamp(how="end").dt.normalize()
    out = out[["Data", "Valor"]]
    return out.dropna().reset_index(drop=True)


def selic_real(selic_meta_mensal: pd.DataFrame, ipca_12m: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula a taxa Selic real (deflacionada pelo IPCA acumulado 12 meses)
    usando a equação de Fisher: (1 + i_nominal) / (1 + inflação) - 1.
    Ambas as séries de entrada devem estar em % a.a. e já em frequência mensal.
    """
    df = pd.merge_asof(
        selic_meta_mensal.sort_values("Data"),
        ipca_12m.sort_values("Data"),
        on="Data",
        direction="backward",
        suffixes=("_selic", "_ipca"),
    ).dropna()
    df["Selic Real"] = (
        (1 + df["Valor_selic"] / 100) / (1 + df["Valor_ipca"] / 100) - 1
    ) * 100
    return df[["Data", "Selic Real"]]


def salario_minimo_deflacionado(
    salario_nominal: pd.DataFrame, ipca_mensal: pd.DataFrame
) -> pd.DataFrame:
    """
    Traz o salário mínimo nominal para valores reais na data mais recente
    disponível, aplicando o IPCA mensal acumulado "para frente" (deflator
    encadeado). O resultado mostra quanto cada salário mínimo histórico
    valeria em poder de compra de hoje.
    """
    if salario_nominal.empty or ipca_mensal.empty:
        return pd.DataFrame(columns=["Data", "Nominal", "Real (poder de compra atual)"])

    ipca = ipca_mensal.sort_values("Data").copy()
    ipca["fator"] = 1 + ipca["Valor"] / 100
    # fator acumulado da data até o fim da série (hoje), de trás para frente
    ipca["fator_acumulado_ate_hoje"] = ipca["fator"][::-1].cumprod()[::-1]

    sal = salario_nominal.sort_values("Data").copy()
    sal = pd.merge_asof(sal, ipca[["Data", "fator_acumulado_ate_hoje"]], on="Data", direction="forward")
    sal["fator_acumulado_ate_hoje"] = sal["fator_acumulado_ate_hoje"].fillna(1.0)
    sal["Real (poder de compra atual)"] = sal["Valor"] * sal["fator_acumulado_ate_hoje"]
    sal = sal.rename(columns={"Valor": "Nominal"})
    return sal[["Data", "Nominal", "Real (poder de compra atual)"]]


def variacao_percentual(df: pd.DataFrame, coluna: str = "Valor") -> float | None:
    """Variação percentual entre o primeiro e o último valor de uma série."""
    if df.empty or len(df) < 2:
        return None
    inicio, fim = df[coluna].iloc[0], df[coluna].iloc[-1]
    if inicio == 0:
        return None
    return (fim / inicio - 1) * 100


def ultimo_valor(df: pd.DataFrame, coluna: str = "Valor"):
    if df.empty:
        return None
    return df[coluna].iloc[-1]


def variacao_pontos(df: pd.DataFrame, coluna: str = "Valor") -> float | None:
    """Variação em pontos percentuais (para taxas, ao invés de variação %)."""
    if df.empty or len(df) < 2:
        return None
    return df[coluna].iloc[-1] - df[coluna].iloc[0]
