# Dashboard-Selic
Dashboard em Python (Streamlit + Plotly) que cruza Selic, IPCA e Salário Mínimo com dados oficiais da API do Banco Central (SGS) — do dado bruto ao gráfico interativo.


# 💹 Como a Selic afeta o seu bolso

Dashboard interativo em Python que cruza **Selic, IPCA (inflação) e Salário
Mínimo** ao longo dos últimos anos, usando dados oficiais e gratuitos do
**Banco Central do Brasil (API SGS)**. Feito para publicar no LinkedIn — como
app interativo (link ao vivo) ou como imagem estática pronta para o post.

![status](https://img.shields.io/badge/status-pronto_para_uso-2FA37F)
![python](https://img.shields.io/badge/python-3.10+-D8AA3F)

## O que tem aqui

| Arquivo | O que faz |
|---|---|
| `app.py` | Dashboard interativo (Streamlit + Plotly) |
| `bcb_data.py` | Camada de acesso à API do BCB (SGS), com cache |
| `utils.py` | Cálculos: Selic real (Fisher), salário mínimo deflacionado, variações |
| `export_linkedin_image.py` | Gera uma imagem `.png` pronta para post, sem precisar rodar o app |
| `tests/test_app_smoke.py` | Teste automatizado que roda o app inteiro com dados simulados |
| `requirements.txt` | Dependências |

**Séries do BCB usadas:** Selic Meta (432) · IPCA mensal (433) · IPCA
acumulado 12 meses (13522) · Dólar PTAX venda (1) · Salário Mínimo (1619).

## Como rodar

```bash
# 1. Crie um ambiente virtual (recomendado)
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 2. Instale as dependências
pip install -r requirements.txt

# 3. Rode o dashboard
streamlit run app.py
```

Isso abre o app em `http://localhost:8501`. A barra lateral deixa escolher o
período (de 2 a 10 anos); os dados são buscados ao vivo na API do BCB e
ficam em cache por 1h.

## Gerar a imagem para o post do LinkedIn

Se você só quer a imagem (sem publicar o app), rode:

```bash
python export_linkedin_image.py --anos 5 --saida painel_selic.png
```

Isso gera um `.png` em 1200×1500px (formato retrato, bom para o feed do
LinkedIn), com título, KPIs, os dois gráficos principais e a fonte dos
dados — sem precisar do Streamlit rodando.

## Publicar o app de graça (link ao vivo pro LinkedIn)

O jeito mais simples é o **Streamlit Community Cloud** (gratuito):

1. Suba esta pasta para um repositório no GitHub.
2. Entre em [share.streamlit.io](https://share.streamlit.io), conecte o
   repositório e aponte para `app.py`.
3. Em alguns minutos você tem uma URL pública (`seu-app.streamlit.app`) —
   ótima para colocar no comentário fixado do post, já que o LinkedIn não
   permite embutir apps interativos diretamente no feed.

## Rodar os testes

```bash
pip install streamlit  # já incluso no requirements.txt
python tests/test_app_smoke.py
```

O teste roda o `app.py` inteiro com dados sintéticos (sem precisar de
internet) e falha se qualquer parte do app lançar uma exceção — útil para
validar antes de publicar.

## Sugestão de texto para o post

> Como a variação da Selic afeta o seu bolso nos últimos 5 anos — em um
> dashboard interativo com dados oficiais do Banco Central. 📊
>
> [imagem ou link do app]
>
> Fonte: Banco Central do Brasil (SGS) · api.bcb.gov.br

## Customizar

- **Cores/tema:** edite o dicionário `PALETA` no topo de `app.py` (e o
  equivalente em `export_linkedin_image.py`).
- **Período padrão:** altere o `value=5` do slider em `app.py`.
- **Novas séries:** adicione uma entrada em `SERIES` em `bcb_data.py` com o
  código SGS correspondente (confirme em
  [localizador de séries do BCB](https://www3.bcb.gov.br/sgspub/localizarseries/localizarSeries.do)).

## Fonte dos dados

Banco Central do Brasil — Sistema Gerenciador de Séries Temporais (SGS),
API pública gratuita: `https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados`
