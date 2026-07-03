# LAB05 — GraphQL vs REST: Um Experimento Controlado

## 🔗 Links Rápidos e Documentos Principais

- **[Planejamento do Experimento (PDF)](./docs/desenho-experimento.pdf)**
- **[Relatório Final de Resultados (PDF)](./reports/relatorio.pdf)**
- **[Dashboard Interativo (GitHub Pages)](https://zezit.github.io/lab-exp-softw-5/)** *(Verifique se o Actions de deploy finalizou no seu fork!)*

## 1. Visão Geral

**Disciplina:** Laboratório de Experimentação de Software  
**Curso:** Engenharia de Software  
**Professor:** Danilo  
**Valor:** 20 pontos

---

## Integrantes

<table>
  <tr>
    <td align="center">
      <a href="https://github.com/moraisjo">
        <img src="https://avatars.githubusercontent.com/u/92741380?v=4" width="100px;" alt="Joana Morais"/><br />
        <sub><b>Joana Morais</b></sub>
      </a>
    </td>
    <td align="center">
      <a href="https://github.com/zezit">
        <img src="https://avatars.githubusercontent.com/u/95448020?v=4" width="100px;" alt="José Dias"/><br />
        <sub><b>José Dias</b></sub>
      </a>
    </td>
  </tr>
</table>

---

## Descrição

Este laboratório realiza um **experimento controlado** para avaliar quantitativamente os benefícios da adoção de uma API GraphQL em detrimento de uma API REST. Utilizando a API do GitHub como caso de estudo (REST API v3 e GraphQL API v4), o experimento mede e compara:

| # | Pergunta de Pesquisa | Métrica |
|---|---|---|
| **RQ1** | Respostas às consultas GraphQL são mais rápidas que respostas às consultas REST? | Tempo de resposta (ms) |
| **RQ2** | Respostas às consultas GraphQL têm tamanho menor que respostas às consultas REST? | Tamanho da resposta (bytes) |

O experimento utiliza **3 níveis de complexidade** de consulta (simples, médio, complexo) aplicados a **50 repositórios** populares do GitHub, com **10 trials** por medição, totalizando **3.000 medições**.

---

## Entregas

### Lab05S01 — Desenho e Preparação do Experimento *(5 pontos)*
- Desenho do experimento com hipóteses, variáveis, tratamentos e ameaças à validade
- Scripts de coleta e medição preparados

### Lab05S02 — Execução, Análise e Relatório *(10 pontos)*
- Execução do experimento com coleta de dados
- Análise estatística (Shapiro-Wilk, Mann-Whitney U, rank-biserial correlation)
- Relatório final com resultados e discussão

### Lab05S03 — Dashboard de Visualização *(5 pontos)*
- Dashboard com 6 painéis de visualização usando Pandas, Matplotlib e Seaborn
- Tabelas descritivas e gráficos comparativos

---

## Configuração do Ambiente

### Pré-requisitos

- **Python 3.10+**
- **Git**
- **GitHub Personal Access Token (PAT)** com permissão `public_repo`

### Instalação

```bash
# 1. Clone o repositório
git clone <url-do-repositório>
cd <nome-do-repositório>/lab-5

# 2. Crie e ative um ambiente virtual
python -m venv .venv
# Linux/macOS:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate

# 3. Instale as dependências
pip install -r requirements.txt
```

### Configuração do Token GitHub

```bash
cp .env.example .env
```

Edite o arquivo `.env` e preencha com seu token:
```text
GITHUB_TOKEN=ghp_seu_token_aqui
```

**Como obter um token:**
1. Acesse [GitHub Settings → Developer settings → Personal access tokens](https://github.com/settings/tokens)
2. Clique em "Generate new token (classic)"
3. Selecione o escopo `public_repo`
4. Copie o token gerado e armazene-o com segurança

> **⚠️ IMPORTANTE:** Nunca versione o arquivo `.env` com seu token real.

---

## Como Executar

### 1. Executar o Experimento (Sprint 1 + Sprint 2)

```bash
python src/01-run-experiment.py
```

**Opções disponíveis:**
```bash
python src/01-run-experiment.py --repos 50 --trials 10 --output data/results_experiment.csv
```

| Parâmetro | Padrão | Descrição |
|---|---|---|
| `--repos` | 50 | Número de repositórios a testar |
| `--trials` | 10 | Número de trials por medição |
| `--output` | `data/results_experiment.csv` | Arquivo de saída |

### 2. Análise Estatística (Sprint 2)

```bash
python src/02-analyze-results.py
```

**Opções:**
```bash
python src/02-analyze-results.py --input data/results_experiment.csv --output-dir reports/figures
```

Gera:
- Testes de normalidade (Shapiro-Wilk)
- Testes de Mann-Whitney U para RQ1 e RQ2
- Box plots, violin plots, gráficos de barras
- Heatmap de p-values
- CSVs de resumo estatístico em `data/summary/`

### 3. Dashboard de Visualização (Sprint 3)

```bash
python src/03-dashboard.py
```

**Opções:**
```bash
python src/03-dashboard.py --input data/results_experiment.csv --output-dir reports/figures
```

Gera 6 painéis de dashboard:
1. **Overview** — Visão geral do experimento com métricas-chave
2. **RQ1 Detail** — Box plots e histogramas de tempo de resposta
3. **RQ2 Detail** — Box plots e histogramas de tamanho da resposta
4. **Speedup** — Análise de ganho relativo GraphQL vs REST
5. **Descriptive Table** — Tabela completa de estatísticas descritivas
6. **Trial Trend** — Tendência do tempo de resposta ao longo dos trials

---

## Estrutura do Projeto

```text
.
├── requirements.txt                  # Dependências Python
├── README.md                         # Este arquivo
├── .env.example                      # Template de variáveis de ambiente
├── .gitignore                        # Regras de git ignore
├── data/                             # Dados do experimento
│   ├── results_experiment.csv        # Resultados brutos (gerado)
│   └── summary/                      # CSVs de resumo estatístico (gerado)
├── docs/
│   ├── desenho-experimento.md        # Desenho do experimento (Sprint 1)
│   └── LABORATÓRIO 05 - ...pdf       # Especificação do laboratório
├── reports/
│   ├── relatorio.md                  # Relatório final
│   └── figures/                      # Gráficos e visualizações (gerado)
│       ├── rq1_boxplot.png
│       ├── rq1_violin.png
│       ├── rq1_bar_medians.png
│       ├── rq1_per_repo.png
│       ├── rq2_boxplot.png
│       ├── rq2_violin.png
│       ├── rq2_bar_medians.png
│       ├── rq2_per_repo.png
│       ├── pvalue_heatmap.png
│       ├── dashboard_overview.png
│       ├── dashboard_rq1_detail.png
│       ├── dashboard_rq2_detail.png
│       ├── dashboard_speedup.png
│       ├── dashboard_descriptive_table.png
│       └── dashboard_trial_trend.png
└── src/
    ├── 01-run-experiment.py          # Script de execução do experimento
    ├── 02-analyze-results.py         # Script de análise estatística
    └── 03-dashboard.py               # Script do dashboard de visualização
```

---

## Metodologia

### Design Experimental

O experimento utiliza um **design pareado** onde cada repositório é testado com GraphQL e REST para 3 níveis de complexidade:

| Nível | GraphQL (1 query) | REST (N chamadas) |
|---|---|---|
| **Simples** | Info básica do repositório | `GET /repos/{owner}/{repo}` |
| **Médio** | Repositório + 20 issues | 2 chamadas |
| **Complexo** | Repositório + 10 PRs com reviews | 2 + 2×10 chamadas |

### Testes Estatísticos

| Teste | Objetivo |
|---|---|
| Shapiro-Wilk | Verificar normalidade dos dados |
| Mann-Whitney U | Comparar distribuições GraphQL vs REST |
| Rank-biserial correlation | Medir tamanho de efeito |

**Nível de significância:** α = 0.05

---

## Solução de Problemas

### Erro: `GITHUB_TOKEN não encontrado`
- Crie o arquivo `.env`: `cp .env.example .env`
- Adicione seu token: `GITHUB_TOKEN=ghp_seu_token_aqui`

### Erro: `401` ou `403`
- Token inválido ou expirado
- Gere novo em [github.com/settings/tokens](https://github.com/settings/tokens)

### Erro: `ModuleNotFoundError`
```bash
source .venv/bin/activate
pip install -r requirements.txt
```

### Rate limiting
- O script trata automaticamente com retries exponenciais
- Reduza `--repos` ou `--trials` para diminuir o uso da API

---

## Referências

- [GitHub REST API v3](https://docs.github.com/en/rest)
- [GitHub GraphQL API v4](https://docs.github.com/en/graphql)
- [GraphQL Specification](https://spec.graphql.org/)
