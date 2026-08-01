"""
app.py
Dashboard interativo: Selic, Inflação (IPCA) e Salário Mínimo no Brasil.
Fonte de dados: Banco Central do Brasil - SGS (API pública).

Rodar localmente:
    pip install -r requirements.txt
    streamlit run app.py
"""

from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from bcb_data import SERIES, fetch_all
from utils import (
    para_mensal,
    salario_minimo_deflacionado,
    selic_real,
    ultimo_valor,
    variacao_percentual,
    variacao_pontos,
)

# ----------------------------------------------------------------------------
# CONFIGURAÇÃO DA PÁGINA E TEMA
# ----------------------------------------------------------------------------
st.set_page_config(
    page_title="Selic, Inflação & Salário Mínimo | Painel Econômico",
    page_icon="💹",
    layout="wide",
    initial_sidebar_state="expanded",
)

PALETA = {
    "fundo": "#0E1B2B",       # azul-tinta profundo (papel de escrituração / BC)
    "fundo_card": "#132437",
    "texto": "#EAEDF2",
    "texto_suave": "#93A1B5",
    "selic": "#D8AA3F",        # ouro/mostarda -> custo do dinheiro
    "ipca": "#C4574B",         # terracota-vermelho -> perda de valor
    "salario_nominal": "#5C7A99",
    "salario_real": "#2FA37F", # verde-teal -> poder de compra
    "dolar": "#8B7BC4",
    "grid": "#243349",
    "borda": "#22364C",
}

FONTE_DISPLAY = "'Source Serif 4', Georgia, serif"
FONTE_MONO = "'IBM Plex Mono', 'Roboto Mono', monospace"
FONTE_BASE = "'Inter', -apple-system, sans-serif"

st.markdown(
    f"""
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Source+Serif+4:wght@600;700&family=Inter:wght@400;500;600&family=IBM+Plex+Mono:wght@500;600&display=swap" rel="stylesheet">
    <style>
      .stApp {{
        background-color: {PALETA['fundo']};
        color: {PALETA['texto']};
        font-family: {FONTE_BASE};
      }}
      section[data-testid="stSidebar"] {{
        background-color: {PALETA['fundo_card']};
        border-right: 1px solid {PALETA['borda']};
      }}
      h1, h2, h3 {{
        font-family: {FONTE_DISPLAY} !important;
        color: {PALETA['texto']} !important;
        letter-spacing: -0.01em;
      }}
      .titulo-eyebrow {{
        font-family: {FONTE_MONO};
        text-transform: uppercase;
        letter-spacing: 0.12em;
        font-size: 0.72rem;
        color: {PALETA['selic']};
        margin-bottom: 0.3rem;
      }}
      .subtitulo {{
        color: {PALETA['texto_suave']};
        font-size: 1rem;
        max-width: 62ch;
        margin-top: -0.4rem;
      }}
      div[data-testid="stMetric"] {{
        background-color: {PALETA['fundo_card']};
        border: 1px solid {PALETA['borda']};
        border-radius: 10px;
        padding: 1rem 1.1rem 0.8rem 1.1rem;
      }}
      div[data-testid="stMetricValue"] {{
        font-family: {FONTE_MONO} !important;
        font-size: 1.7rem !important;
      }}
      div[data-testid="stMetricLabel"] {{
        color: {PALETA['texto_suave']} !important;
        font-family: {FONTE_MONO};
        text-transform: uppercase;
        font-size: 0.68rem !important;
        letter-spacing: 0.08em;
      }}
      .fonte-rodape {{
        color: {PALETA['texto_suave']};
        font-size: 0.78rem;
        font-family: {FONTE_MONO};
        border-top: 1px solid {PALETA['borda']};
        padding-top: 0.8rem;
        margin-top: 1.5rem;
      }}
      .bloco-insight {{
        background-color: {PALETA['fundo_card']};
        border-left: 3px solid {PALETA['selic']};
        border-radius: 6px;
        padding: 0.9rem 1.1rem;
        margin: 0.6rem 0 1.2rem 0;
        font-size: 0.95rem;
        color: {PALETA['texto']};
      }}
    </style>
    """,
    unsafe_allow_html=True,
)


def estilo_grafico(fig: go.Figure, altura: int = 430) -> go.Figure:
    fig.update_layout(
        height=altura,
        paper_bgcolor=PALETA["fundo"],
        plot_bgcolor=PALETA["fundo"],
        font=dict(family=FONTE_BASE, color=PALETA["texto"], size=13),
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0,
            bgcolor="rgba(0,0,0,0)",
        ),
        margin=dict(l=10, r=10, t=40, b=10),
        hovermode="x unified",
    )
    fig.update_xaxes(showgrid=False, zeroline=False, linecolor=PALETA["borda"])
    fig.update_yaxes(showgrid=True, gridcolor=PALETA["grid"], zeroline=False)
    return fig


# ----------------------------------------------------------------------------
# CABEÇALHO
# ----------------------------------------------------------------------------
st.markdown('<div class="titulo-eyebrow">Banco Central do Brasil · Série Temporal SGS</div>', unsafe_allow_html=True)
st.markdown("## Como a Selic afeta o seu bolso")
st.markdown(
    '<p class="subtitulo">Selic, inflação (IPCA) e salário mínimo lado a lado — '
    "para entender, em números reais, o que aconteceu com o poder de compra "
    "nos últimos anos.</p>",
    unsafe_allow_html=True,
)
st.write("")

# ----------------------------------------------------------------------------
# SIDEBAR — CONTROLES
# ----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### Período de análise")
    anos = st.slider("Últimos N anos", min_value=2, max_value=10, value=5)
    st.markdown("---")
    st.markdown("### Sobre")
    st.caption(
        "Dados oficiais do **Banco Central do Brasil**, via API pública do "
        "Sistema Gerenciador de Séries Temporais (SGS). Atualizado a cada "
        "execução (cache de 1h)."
    )
    st.caption(f"Séries: Selic Meta ({SERIES['selic_meta']['codigo']}) · "
               f"IPCA mensal ({SERIES['ipca_mensal']['codigo']}) · "
               f"IPCA 12m ({SERIES['ipca_12m']['codigo']}) · "
               f"Dólar PTAX ({SERIES['dolar_ptax']['codigo']}) · "
               f"Salário mínimo ({SERIES['salario_minimo']['codigo']})")

# ----------------------------------------------------------------------------
# DADOS
# ----------------------------------------------------------------------------
with st.spinner("Consultando a API do Banco Central..."):
    dados = fetch_all(anos=anos)

selic_diaria = dados["selic_meta"]
ipca_mensal = dados["ipca_mensal"]
ipca_12m = dados["ipca_12m"]
dolar_diario = dados["dolar_ptax"]
salario_nominal = dados["salario_minimo"]

if selic_diaria.empty and ipca_mensal.empty:
    st.error(
        "Não foi possível carregar dados da API do Banco Central agora. "
        "Verifique sua conexão com **api.bcb.gov.br** e tente novamente."
    )
    st.stop()

selic_mensal = para_mensal(selic_diaria)
dolar_mensal = para_mensal(dolar_diario)
sr = selic_real(selic_mensal, ipca_12m)
sal_deflacionado = salario_minimo_deflacionado(salario_nominal, ipca_mensal)

# ----------------------------------------------------------------------------
# KPIs
# ----------------------------------------------------------------------------
c1, c2, c3, c4 = st.columns(4)

with c1:
    st.metric(
        "Selic hoje",
        f"{ultimo_valor(selic_mensal):.2f}%".replace(".", ",") if ultimo_valor(selic_mensal) is not None else "—",
        delta=f"{variacao_pontos(selic_mensal):+.2f} p.p. em {anos} anos".replace(".", ",")
        if variacao_pontos(selic_mensal) is not None else None,
        delta_color="inverse",
    )
with c2:
    st.metric(
        "IPCA 12 meses",
        f"{ultimo_valor(ipca_12m):.2f}%".replace(".", ",") if ultimo_valor(ipca_12m) is not None else "—",
    )
with c3:
    st.metric(
        "Dólar (PTAX)",
        f"R$ {ultimo_valor(dolar_mensal):.2f}".replace(".", ",") if ultimo_valor(dolar_mensal) is not None else "—",
        delta=f"{variacao_percentual(dolar_mensal):+.1f}% em {anos} anos".replace(".", ",")
        if variacao_percentual(dolar_mensal) is not None else None,
    )
with c4:
    st.metric(
        "Salário mínimo",
        f"R$ {ultimo_valor(salario_nominal):.2f}".replace(".", ",") if ultimo_valor(salario_nominal) is not None else "—",
        delta=f"{variacao_percentual(salario_nominal):+.1f}% nominal em {anos} anos".replace(".", ",")
        if variacao_percentual(salario_nominal) is not None else None,
    )

st.write("")

# ----------------------------------------------------------------------------
# GRÁFICO 1 — SELIC x IPCA 12M
# ----------------------------------------------------------------------------
st.markdown("### Selic Meta vs. Inflação (IPCA 12 meses)")
st.markdown(
    '<div class="bloco-insight">Quando a linha dourada (Selic) fica bem acima '
    "da vermelha (IPCA), o juro real está alto: bom para quem investe em renda "
    "fixa, mais caro para quem toma crédito.</div>",
    unsafe_allow_html=True,
)

fig1 = go.Figure()
fig1.add_trace(go.Scatter(
    x=selic_mensal["Data"], y=selic_mensal["Valor"], name="Selic Meta (% a.a.)",
    line=dict(color=PALETA["selic"], width=2.6), mode="lines",
))
fig1.add_trace(go.Scatter(
    x=ipca_12m["Data"], y=ipca_12m["Valor"], name="IPCA 12m (%)",
    line=dict(color=PALETA["ipca"], width=2.6), mode="lines",
    fill="tozeroy", fillcolor="rgba(196,87,75,0.08)",
))
fig1 = estilo_grafico(fig1)
fig1.update_yaxes(title_text="% ao ano / % acumulado")
st.plotly_chart(fig1, width="stretch", config={"displaylogo": False})

# ----------------------------------------------------------------------------
# GRÁFICO 2 — SELIC REAL
# ----------------------------------------------------------------------------
st.markdown("### Selic Real (Selic descontada da inflação)")
fig2 = go.Figure()
fig2.add_trace(go.Bar(
    x=sr["Data"], y=sr["Selic Real"], name="Selic Real (%)",
    marker_color=[PALETA["selic"] if v >= 0 else PALETA["ipca"] for v in sr["Selic Real"]],
))
fig2.add_hline(y=0, line_color=PALETA["texto_suave"], line_width=1)
fig2 = estilo_grafico(fig2, altura=340)
fig2.update_yaxes(title_text="% a.a. (Fisher)")
fig2.update_layout(showlegend=False)
st.plotly_chart(fig2, width="stretch", config={"displaylogo": False})

# ----------------------------------------------------------------------------
# GRÁFICO 3 — SALÁRIO MÍNIMO NOMINAL x REAL
# ----------------------------------------------------------------------------
st.markdown("### Salário Mínimo: nominal vs. poder de compra atual")
if not sal_deflacionado.empty:
    perda = None
    if len(sal_deflacionado) >= 2:
        primeiro_real = sal_deflacionado["Real (poder de compra atual)"].iloc[0]
        ultimo_nominal_como_real = sal_deflacionado["Nominal"].iloc[-1]
        # quanto o 1o salário do período valeria hoje, comparado ao salário nominal de hoje
        perda = (ultimo_nominal_como_real / primeiro_real - 1) * 100

    if perda is not None:
        direcao = "ganhou" if perda >= 0 else "perdeu"
        st.markdown(
            f'<div class="bloco-insight">Em termos reais, o salário mínimo de hoje '
            f'{direcao} <b>{abs(perda):.1f}%</b>'.replace(".", ",")
            + f" de poder de compra frente ao início do período analisado "
            f"({sal_deflacionado['Data'].iloc[0].strftime('%m/%Y')}).</div>",
            unsafe_allow_html=True,
        )

    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(
        x=sal_deflacionado["Data"], y=sal_deflacionado["Real (poder de compra atual)"],
        name="Valor real (poder de compra de hoje)", mode="lines+markers",
        line=dict(color=PALETA["salario_real"], width=2.6),
        fill="tozeroy", fillcolor="rgba(47,163,127,0.10)",
    ))
    fig3.add_trace(go.Scatter(
        x=sal_deflacionado["Data"], y=sal_deflacionado["Nominal"],
        name="Valor nominal (na época)", mode="lines+markers",
        line=dict(color=PALETA["salario_nominal"], width=2.2, dash="dot"),
    ))
    fig3 = estilo_grafico(fig3)
    fig3.update_yaxes(title_text="R$")
    st.plotly_chart(fig3, width="stretch", config={"displaylogo": False})
else:
    st.info("Sem dados de salário mínimo suficientes no período selecionado.")

# ----------------------------------------------------------------------------
# GRÁFICO 4 — DÓLAR
# ----------------------------------------------------------------------------
st.markdown("### Câmbio: Dólar (PTAX)")
fig4 = go.Figure()
fig4.add_trace(go.Scatter(
    x=dolar_diario["Data"], y=dolar_diario["Valor"], name="USD/BRL",
    line=dict(color=PALETA["dolar"], width=1.8),
    fill="tozeroy", fillcolor="rgba(139,123,196,0.08)",
))
fig4 = estilo_grafico(fig4, altura=320)
fig4.update_yaxes(title_text="R$ por US$")
fig4.update_layout(showlegend=False)
st.plotly_chart(fig4, width="stretch", config={"displaylogo": False})

# ----------------------------------------------------------------------------
# RODAPÉ
# ----------------------------------------------------------------------------
st.markdown(
    f'<div class="fonte-rodape">Fonte: Banco Central do Brasil — Sistema '
    f"Gerenciador de Séries Temporais (SGS), api.bcb.gov.br · "
    f"Painel gerado em {datetime.today().strftime('%d/%m/%Y')} · "
    f"Selic real calculada pela equação de Fisher · Salário mínimo real "
    f"deflacionado pelo IPCA mensal encadeado.</div>",
    unsafe_allow_html=True,
)
