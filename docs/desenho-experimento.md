# Desenho do Experimento — GraphQL vs REST

## 1. Contexto

A linguagem de consulta GraphQL, proposta pelo Facebook, representa uma alternativa às APIs REST tradicionais. Enquanto REST utiliza múltiplos endpoints para diferentes operações, GraphQL permite ao cliente especificar exatamente os dados desejados em uma única requisição. Este experimento investiga quantitativamente as diferenças de desempenho entre ambas as abordagens, utilizando a API do GitHub como objeto de estudo.

---

## 2. Perguntas de Pesquisa

| # | Pergunta de Pesquisa |
|---|---|
| **RQ1** | Respostas às consultas GraphQL são mais rápidas que respostas às consultas REST? |
| **RQ2** | Respostas às consultas GraphQL têm tamanho menor que respostas às consultas REST? |

---

## A. Hipóteses Nula e Alternativa

### RQ1 — Tempo de Resposta

- **H₀₁:** Não há diferença significativa no tempo de resposta entre consultas GraphQL e consultas REST equivalentes.
  - *H₀₁: μ_tempo_GraphQL = μ_tempo_REST*
- **H₁₁:** Há diferença significativa no tempo de resposta entre consultas GraphQL e consultas REST equivalentes.
  - *H₁₁: μ_tempo_GraphQL ≠ μ_tempo_REST*

### RQ2 — Tamanho da Resposta

- **H₀₂:** Não há diferença significativa no tamanho da resposta entre consultas GraphQL e consultas REST equivalentes.
  - *H₀₂: μ_tamanho_GraphQL = μ_tamanho_REST*
- **H₁₂:** Há diferença significativa no tamanho da resposta entre consultas GraphQL e consultas REST equivalentes.
  - *H₁₂: μ_tamanho_GraphQL ≠ μ_tamanho_REST*

---

## B. Variáveis Dependentes

| Variável | Descrição | Unidade |
|---|---|---|
| **Tempo de resposta** | Tempo total desde o envio da requisição HTTP até o recebimento completo do corpo da resposta | Milissegundos (ms) |
| **Tamanho da resposta** | Tamanho total do corpo da resposta HTTP | Bytes |

---

## C. Variáveis Independentes

| Variável | Descrição | Níveis |
|---|---|---|
| **Tipo de API** | Tecnologia utilizada para consulta | GraphQL, REST |
| **Complexidade da consulta** | Quantidade de dados e relacionamentos solicitados | Simples, Média, Complexa |

---

## D. Tratamentos

O experimento define **2 tratamentos** (GraphQL e REST) aplicados a **3 níveis de complexidade** de consulta:

| Nível | GraphQL | REST |
|---|---|---|
| **Simples** | Uma query GraphQL que busca informações básicas do repositório (nome, estrelas, forks, linguagem, contadores de issues/PRs/releases/watchers) | Uma chamada REST `GET /repos/{owner}/{repo}` |
| **Médio** | Uma query GraphQL que busca informações do repositório + lista de 20 issues com detalhes | Duas chamadas REST: `GET /repos/{owner}/{repo}` + `GET /repos/{owner}/{repo}/issues` |
| **Complexo** | Uma query GraphQL que busca informações do repositório + 10 PRs com reviews e comentários | Múltiplas chamadas REST: `GET /repos/{owner}/{repo}` + `GET .../pulls` + `GET .../pulls/{n}/reviews` + `GET .../pulls/{n}/comments` para cada PR |

---

## E. Objetos Experimentais

Os objetos experimentais são os **50 repositórios mais populares do GitHub** (ordenados por número de estrelas, com pelo menos 10.000 estrelas). Estes repositórios foram escolhidos por:

1. **Representatividade:** São projetos amplamente conhecidos e ativos.
2. **Diversidade:** Cobrem diferentes linguagens e domínios.
3. **Dados ricos:** Possuem issues, PRs, reviews e releases em quantidade suficiente.
4. **Reprodutibilidade:** Critério objetivo (estrelas) facilita a replicação do estudo.

---

## F. Tipo de Projeto Experimental

O projeto experimental utiliza um **design pareado (paired design)**, onde cada repositório é testado com ambos os tratamentos (GraphQL e REST) para cada nível de complexidade de consulta. Isto permite:

- Controlar variações entre repositórios (diferentes tamanhos de resposta, disponibilidade de dados)
- Comparar diretamente o desempenho de GraphQL vs REST para os mesmos dados
- Reduzir o efeito de variáveis confundidoras externas

Para mitigar efeitos de variabilidade de rede e caching, cada medição é repetida múltiplas vezes (trials), e são realizadas requisições de warm-up antes das medições efetivas.

---

## G. Quantidade de Medições

| Parâmetro | Valor |
|---|---|
| Repositórios (objetos experimentais) | 50 |
| Tipos de consulta (complexidade) | 3 (simples, médio, complexo) |
| Tratamentos (APIs) | 2 (GraphQL, REST) |
| Trials por medição | 10 |
| **Total de medições** | **50 × 3 × 2 × 10 = 3.000** |

Cada medição registra:
- Repositório testado
- Tipo de consulta
- Tipo de API (tratamento)
- Número do trial
- Tempo de resposta (ms)
- Tamanho da resposta (bytes)

---

## H. Ameaças à Validade

### Ameaças à Validade Interna

| Ameaça | Mitigação |
|---|---|
| **Variabilidade de rede** | Execução de warm-up requests antes das medições; múltiplos trials por medição |
| **Caching no servidor** | Alternância entre GraphQL e REST para o mesmo repositório; intervalos entre requisições |
| **Rate limiting** | Tratamento de erros 403/429 com retries exponenciais; intervalos entre requisições |
| **Ordem de execução** | Para cada repositório, GraphQL e REST são executados alternadamente em cada trial |

### Ameaças à Validade Externa

| Ameaça | Mitigação |
|---|---|
| **Generalização para outras APIs** | Resultados limitados à API do GitHub; outras APIs podem ter implementações diferentes |
| **Representatividade dos repositórios** | Seleção dos top 50 por estrelas pode não representar repositórios menores |
| **Variabilidade temporal** | Os resultados dependem das condições de rede e carga do servidor GitHub no momento da execução |

### Ameaças à Validade de Construto

| Ameaça | Mitigação |
|---|---|
| **Equivalência das consultas** | As consultas GraphQL e REST foram projetadas para retornar dados equivalentes, mas REST retorna dados adicionais não solicitados (over-fetching) |
| **Medição de tempo** | Uso de `time.perf_counter()` para medição de alta precisão |
| **Tamanho da resposta** | Medido como bytes brutos do corpo HTTP, sem considerar headers |

### Ameaças à Validade de Conclusão

| Ameaça | Mitigação |
|---|---|
| **Tamanho amostral** | 50 repositórios × 10 trials = 500 medições por combinação tratamento/complexidade |
| **Testes estatísticos** | Uso de teste de Shapiro-Wilk para normalidade; Mann-Whitney U (não-paramétrico) para comparações; α = 0.05 |
| **Efeito prático** | Cálculo de tamanho de efeito (rank-biserial correlation) além da significância estatística |

---

## I. Ambiente Experimental

| Componente | Especificação |
|---|---|
| **Sistema Operacional** | Linux |
| **Linguagem** | Python 3.10+ |
| **Biblioteca HTTP** | urllib (stdlib) |
| **Medição de tempo** | `time.perf_counter()` |
| **API alvo** | GitHub REST API v3 / GitHub GraphQL API v4 |
| **Autenticação** | Personal Access Token (Bearer) |
| **Conexão** | Internet residencial/institucional |

---

## J. Procedimento Experimental

1. **Seleção dos repositórios:** Buscar os 50 repositórios mais populares via REST API search
2. **Para cada repositório:**
   a. Executar 2 requisições de warm-up
   b. Para cada nível de complexidade (simples, médio, complexo):
      - Para cada trial (1 a 10):
        - Medir GraphQL: tempo e tamanho da resposta
        - Aguardar 300ms
        - Medir REST: tempo e tamanho da resposta
        - Aguardar 500ms
3. **Salvar resultados** em CSV com todas as medições
4. **Análise estatística** dos dados coletados
