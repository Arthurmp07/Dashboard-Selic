"""
export_linkedin_image.py
Gera uma imagem estática (PNG), pronta para post no LinkedIn, resumindo
Selic x IPCA x Salário Mínimo nos últimos N anos.

Não depende de servidor: roda direto no terminal e salva um arquivo local.

Uso:
    python export_linkedin_image.py --anos 5 --saida painel_selic.png
"""

from __future__ import annotations

import argparse
from datetime import datetime

import plotly.graph_objects as go
from plotly.subplots import make_subplots

from bcb_data import fetch_all
from utils import para_mensal, salario_minimo_deflacionado, ultimo_valor, variacao_pontos

PALETA = {
    "fundo": "#0E1B2B",
    "texto": "#EAEDF2",
    "texto_suave": "#93A1B5",
    "selic": "#D8AA3F",
    "ipca": "#C4574B",
    "salario_nominal": "#5C7A99",
    "salario_real": "#2FA37F",
}


def montar_figura(anos: int) -> go.Figure:
    dados = fetch_all(anos=anos)
    selic_mensal = para_mensal(dados["selic_meta"])
    ipca_12m = dados["ipca_12m"]
    sal_deflacionado = salario_minimo_deflacionado(dados["salario_minimo"], dados["ipca_mensal"])

    fig = make_subplots(
        rows=2, cols=1,
        row_heights=[0.5, 0.5],
        vertical_spacing=0.18,
    )

    selic_hoje = ultimo_valor(selic_mensal)
    ipca_hoje = ultimo_valor(ipca_12m)
    var_selic = variacao_pontos(selic_mensal)

    # --- Gráfico principal: Selic x IPCA 12m
    fig.add_trace(go.Scatter(
        x=selic_mensal["Data"], y=selic_mensal["Valor"], name="Selic Meta (% a.a.)",
        line=dict(color=PALETA["selic"], width=3.4),
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=ipca_12m["Data"], y=ipca_12m["Valor"], name="IPCA 12m (%)",
        line=dict(color=PALETA["ipca"], width=3.4),
        fill="tozeroy", fillcolor="rgba(196,87,75,0.10)",
    ), row=1, col=1)

    # --- Gráfico secundário: salário mínimo nominal x real
    if not sal_deflacionado.empty:
        fig.add_trace(go.Scatter(
            x=sal_deflacionado["Data"], y=sal_deflacionado["Real (poder de compra atual)"],
            name="Valor real (poder de compra hoje)",
            line=dict(color=PALETA["salario_real"], width=3.2),
            fill="tozeroy", fillcolor="rgba(47,163,127,0.12)",
        ), row=2, col=1)
        fig.add_trace(go.Scatter(
            x=sal_deflacionado["Data"], y=sal_deflacionado["Nominal"],
            name="Valor nominal (na época)",
            line=dict(color=PALETA["salario_nominal"], width=2.6, dash="dot"),
        ), row=2, col=1)

    fig.update_xaxes(showgrid=False, linecolor="#243349", tickfont=dict(size=13))
    fig.update_yaxes(showgrid=True, gridcolor="#243349", tickfont=dict(size=13))
    fig.update_yaxes(title_text="% a.a. / % acumulado 12m", row=1, col=1)
    fig.update_yaxes(title_text="R$", row=2, col=1)

    kpi_texto = (
        f"<b>Selic hoje: {selic_hoje:.2f}%</b>".replace(".", ",")
        + f"   ·   <b>IPCA 12m: {ipca_hoje:.2f}%</b>".replace(".", ",")
        + (f"   ·   Selic variou {var_selic:+.2f} p.p. em {anos} anos".replace(".", ",")
           if var_selic is not None else "")
    )

    fig.update_layout(
        width=1200,
        height=1500,
        paper_bgcolor=PALETA["fundo"],
        plot_bgcolor=PALETA["fundo"],
        font=dict(family="Inter, Arial, sans-serif", color=PALETA["texto"]),
        legend=dict(orientation="h", yanchor="bottom", y=-0.05, xanchor="center", x=0.5,
                    font=dict(size=13), bgcolor="rgba(0,0,0,0)"),
        margin=dict(l=70, r=50, t=200, b=100),
    )

    fig.add_annotation(text="COMO A SELIC AFETA O SEU BOLSO", x=0, y=1.16, xref="paper", yref="paper",
                        showarrow=False, font=dict(size=15, color=PALETA["selic"], family="Inter"),
                        xanchor="left")
    fig.add_annotation(text=f"Selic, inflação e salário mínimo nos últimos {anos} anos",
                        x=0, y=1.10, xref="paper", yref="paper", showarrow=False,
                        font=dict(size=24, color=PALETA["texto"], family="Georgia, serif"), xanchor="left")
    fig.add_annotation(text=kpi_texto, x=0, y=1.035, xref="paper", yref="paper", showarrow=False,
                        font=dict(size=15, color=PALETA["texto_suave"]), xanchor="left")
    fig.add_annotation(text="SALÁRIO MÍNIMO — NOMINAL x PODER DE COMPRA", x=0, y=0.50,
                        xref="paper", yref="paper", showarrow=False,
                        font=dict(size=13, color=PALETA["salario_real"], family="Inter"), xanchor="left")
    fig.add_annotation(
        text=f"Fonte: Banco Central do Brasil (SGS) · api.bcb.gov.br · gerado em {datetime.today().strftime('%d/%m/%Y')}",
        x=0, y=-0.11, xref="paper", yref="paper", showarrow=False,
        font=dict(size=11, color=PALETA["texto_suave"]), xanchor="left",
    )
    return fig


def main():
    parser = argparse.ArgumentParser(description="Gera imagem do painel Selic x IPCA x Salário Mínimo para LinkedIn.")
    parser.add_argument("--anos", type=int, default=5, help="Quantidade de anos para trás (padrão: 5)")
    parser.add_argument("--saida", type=str, default="painel_selic_linkedin.png", help="Nome do arquivo de saída")
    args = parser.parse_args()

    fig = montar_figura(args.anos)
    fig.write_image(args.saida, scale=2)
    print(f"Imagem salva em: {args.saida}")


if __name__ == "__main__":
    main()
