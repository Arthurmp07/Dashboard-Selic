"""
bcb_data.py
Camada de acesso aos dados do Banco Central do Brasil (Sistema Gerenciador
de Séries Temporais - SGS) via API pública.

Documentação oficial: https://dadosabertos.bcb.gov.br/dataset/22707-serie-de-taxa-selic
Formato de endpoint:
  https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados?formato=json&dataInicial=DD/MM/AAAA&dataFinal=DD/MM/AAAA
"""

from __future__ import annotations

from datetime import datetime, timedelta

import pandas as pd
import requests
import streamlit as st

BCB_BASE_URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados"
TIMEOUT_SEGUNDOS = 30

# Códigos de série no SGS. Confirme sempre em:
# https://www3.bcb.gov.br/sgspub/localizarseries/localizarSeries.do
SERIES: dict[str, dict] = {
    "selic_meta": {
        "codigo": 432,
        "nome": "Selic Meta",
        "unidade": "% a.a.",
        "periodicidade": "eventos do Copom",
    },
    "ipca_mensal": {
        "codigo": 433,
        "nome": "IPCA Mensal",
        "unidade": "%",
        "periodicidade": "mensal",
    },
    "ipca_12m": {
        "codigo": 13522,
        "nome": "IPCA Acumulado 12 Meses",
        "unidade": "%",
        "periodicidade": "mensal",
    },
    "dolar_ptax": {
        "codigo": 1,
        "nome": "Dólar PTAX (venda)",
        "unidade": "R$",
        "periodicidade": "diária",
    },
    "salario_minimo": {
        "codigo": 1619,
        "nome": "Salário Mínimo Nominal",
        "unidade": "R$",
        "periodicidade": "eventos de reajuste",
    },
}


class BCBDataError(Exception):
    """Erro ao consultar ou interpretar dados do SGS/BCB."""


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_series(codigo: int, data_inicial: str, data_final: str) -> pd.DataFrame:
    """
    Busca uma série temporal do SGS/BCB e devolve um DataFrame com colunas
    'Data' (datetime64) e 'Valor' (float).

    O cache do Streamlit evita bater na API a cada interação do usuário
    (TTL de 1h). Para uso fora do Streamlit, basta chamar a função normalmente.
    """
    url = BCB_BASE_URL.format(codigo=codigo)
    params = {
        "formato": "json",
        "dataInicial": data_inicial,
        "dataFinal": data_final,
    }
    try:
        resp = requests.get(url, params=params, timeout=TIMEOUT_SEGUNDOS)
        resp.raise_for_status()
    except requests.RequestException as exc:
        raise BCBDataError(f"Falha ao consultar a série {codigo}: {exc}") from exc

    payload = resp.json()
    if not payload:
        return pd.DataFrame(columns=["Data", "Valor"])

    df = pd.DataFrame(payload)
    df["data"] = pd.to_datetime(df["data"], format="%d/%m/%Y")
    df["valor"] = df["valor"].astype(str).str.replace(",", ".", regex=False).astype(float)
    df = df.rename(columns={"data": "Data", "valor": "Valor"})
    return df.sort_values("Data").reset_index(drop=True)


def fetch_all(anos: int = 5, referencia: datetime | None = None) -> dict[str, pd.DataFrame]:
    """
    Busca todas as séries definidas em SERIES para os últimos `anos` anos
    a partir de `referencia` (hoje, por padrão).

    A API do BCB não aceita intervalos maiores que ~10 anos por requisição,
    então até 5-10 anos uma única chamada por série é suficiente.
    """
    referencia = referencia or datetime.today()
    inicio = referencia - timedelta(days=365 * anos + 31)
    data_inicial = inicio.strftime("%d/%m/%Y")
    data_final = referencia.strftime("%d/%m/%Y")

    resultado: dict[str, pd.DataFrame] = {}
    for chave, info in SERIES.items():
        try:
            resultado[chave] = fetch_series(info["codigo"], data_inicial, data_final)
        except BCBDataError as exc:
            st.warning(f"Não foi possível carregar **{info['nome']}**: {exc}")
            resultado[chave] = pd.DataFrame(columns=["Data", "Valor"])
    return resultado
