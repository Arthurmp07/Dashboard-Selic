import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

"""Teste de fumaça: roda app.py de ponta a ponta com dados sintéticos,
sem precisar de acesso à internet, usando o AppTest do Streamlit."""

from unittest.mock import patch

import numpy as np
import pandas as pd
from streamlit.testing.v1 import AppTest


def _dados_sinteticos(anos=5, referencia=None):
    rng = pd.date_range("2021-08-01", "2026-07-31", freq="D")
    np.random.seed(1)
    selic = pd.DataFrame({
        "Data": rng,
        "Valor": np.interp(np.arange(len(rng)), [0, 400, 900, 1500, len(rng) - 1], [4.25, 13.75, 13.75, 10.5, 15.0]),
    })
    meses = pd.date_range("2021-08-01", "2026-07-31", freq="ME")
    ipca_m = pd.DataFrame({"Data": meses, "Valor": np.random.normal(0.4, 0.3, len(meses))})
    ipca_12 = pd.DataFrame({"Data": meses, "Valor": np.clip(np.cumsum(np.random.normal(0, 0.1, len(meses))) + 5, 2, 12)})
    dolar = pd.DataFrame({"Data": rng, "Valor": 5 + np.cumsum(np.random.normal(0, 0.01, len(rng)))})
    sal_dates = pd.to_datetime(["2021-08-01", "2022-01-01", "2023-01-01", "2024-01-01", "2025-01-01", "2026-01-01"])
    salario = pd.DataFrame({"Data": sal_dates, "Valor": [1100, 1212, 1302, 1412, 1518, 1620]})
    return {
        "selic_meta": selic,
        "ipca_mensal": ipca_m,
        "ipca_12m": ipca_12,
        "dolar_ptax": dolar,
        "salario_minimo": salario,
    }


with patch("bcb_data.fetch_all", side_effect=_dados_sinteticos):
    at = AppTest.from_file("../app.py", default_timeout=60)
    at.run()

    assert not at.exception, f"Exceção no app: {[str(e) for e in at.exception]}"
    print(f"OK - rodou sem exceções. {len(at.metric)} métricas, "
          f"{len(at.get('plotly_chart'))} gráficos plotly renderizados.")
    for m in at.metric:
        print(f"  METRIC: {m.label} = {m.value}  (delta={m.delta})")
