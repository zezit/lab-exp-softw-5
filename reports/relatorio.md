# GraphQL vs REST: Um Experimento Controlado

## Relatório Final — Lab 05

---

# 1 Introdução

## 1.1 Contextualização

A linguagem de consulta GraphQL, proposta pelo Facebook em 2015, representa uma alternativa às populares APIs REST para comunicação entre clientes e servidores web. Baseada em grafos, a linguagem permite que clientes especifiquem exatamente os dados que necessitam em uma única requisição, evitando o problema de *over-fetching* (receber dados desnecessários) e *under-fetching* (necessidade de múltiplas requisições para obter todos os dados desejados) que frequentemente ocorre com APIs REST.

APIs REST baseiam-se em *endpoints*: operações pré-definidas que podem ser chamadas por clientes que desejam consultar, deletar, atualizar ou escrever dados. Cada recurso tipicamente possui seu próprio endpoint, e quando dados de múltiplos recursos relacionados são necessários, múltiplas chamadas HTTP devem ser realizadas.

Desde o surgimento do GraphQL, diversos sistemas realizaram a migração entre ambas as soluções, mantendo compatibilidade REST enquanto oferecem os benefícios da nova linguagem de consulta. Entretanto, não está claro quais os reais benefícios da adoção de uma API GraphQL em detrimento de uma API REST, especialmente em termos de desempenho.

## 1.2 Problema

Este estudo busca avaliar quantitativamente os benefícios da adoção de uma API GraphQL em comparação com uma API REST, utilizando a API do GitHub como caso de estudo. O GitHub oferece ambas as interfaces (REST API v3 e GraphQL API v4) para os mesmos dados, configurando um cenário ideal para um experimento controlado.

## 1.3 Perguntas de Pesquisa

| # | Pergunta de Pesquisa |
|---|---|
| **RQ1** | Respostas às consultas GraphQL são mais rápidas que respostas às consultas REST? |
| **RQ2** | Respostas às consultas GraphQL têm tamanho menor que respostas às consultas REST? |

## 1.4 Hipóteses

### RQ1 — Tempo de Resposta

- **H₀₁:** Não há diferença significativa no tempo de resposta entre consultas GraphQL e REST equivalentes.
- **H₁₁:** Há diferença significativa no tempo de resposta entre consultas GraphQL e REST equivalentes.

### RQ2 — Tamanho da Resposta

- **H₀₂:** Não há diferença significativa no tamanho da resposta entre consultas GraphQL e REST equivalentes.
- **H₁₂:** Há diferença significativa no tamanho da resposta entre consultas GraphQL e REST equivalentes.

## 1.5 Hipóteses Informais

Com base na literatura e nas características técnicas de cada abordagem, formulamos as seguintes expectativas:

1. **RQ1 (Tempo):** Esperamos que consultas GraphQL apresentem tempos de resposta **comparáveis ou ligeiramente maiores** para consultas simples (devido ao overhead de parsing da query), mas **significativamente menores** para consultas complexas, onde REST necessita de múltiplas chamadas HTTP sequenciais.

2. **RQ2 (Tamanho):** Esperamos que respostas GraphQL tenham tamanho **significativamente menor** que respostas REST, uma vez que o GraphQL retorna apenas os campos solicitados, enquanto REST retorna todos os campos do recurso (*over-fetching*).

---

# 2 Metodologia

## 2.1 Desenho do Experimento

O experimento utiliza um **design pareado (paired design)** onde cada repositório é testado com ambos os tratamentos (GraphQL e REST) para cada nível de complexidade de consulta.

### Variáveis

| Tipo | Variável | Descrição |
|---|---|---|
| **Independente** | Tipo de API | GraphQL ou REST |
| **Independente** | Complexidade da consulta | Simples, Média, Complexa |
| **Dependente** | Tempo de resposta | Tempo total da requisição HTTP (ms) |
| **Dependente** | Tamanho da resposta | Tamanho do corpo da resposta (bytes) |

### Tratamentos

| Complexidade | GraphQL | REST |
|---|---|---|
| **Simples** | 1 query: info básica do repositório | 1 chamada: `GET /repos/{owner}/{repo}` |
| **Média** | 1 query: repositório + 20 issues | 2 chamadas: repo + issues |
| **Complexa** | 1 query: repositório + 10 PRs com reviews | N chamadas: repo + PRs + reviews + comments (por PR) |

### Objetos Experimentais

50 repositórios mais populares do GitHub (por número de estrelas, com ≥ 10.000 estrelas).

### Quantidade de Medições

- **50** repositórios × **3** tipos de consulta × **2** APIs × **10** trials = **3.000 medições**

## 2.2 Procedimento

1. **Seleção dos repositórios:** Busca dos top 50 repositórios via REST API search
2. **Para cada repositório:**
   - Execução de 2 requisições de warm-up para estabilizar conexões
   - Para cada nível de complexidade:
     - Para cada trial (1 a 10):
       - Medição GraphQL (tempo + tamanho)
       - Intervalo de 300ms
       - Medição REST (tempo + tamanho)
       - Intervalo de 500ms
3. **Registro:** Todos os resultados salvos em CSV

## 2.3 Ferramentas e Ambiente

| Componente | Especificação |
|---|---|
| Sistema Operacional | Linux |
| Linguagem | Python 3.10+ |
| Biblioteca HTTP | `urllib` (stdlib) |
| Medição de tempo | `time.perf_counter()` |
| API alvo | GitHub REST API v3 / GraphQL API v4 |
| Autenticação | Personal Access Token (Bearer) |
| Análise estatística | scipy, pandas, seaborn, matplotlib |

## 2.4 Análise Estatística

1. **Teste de Normalidade:** Shapiro-Wilk para verificar a distribuição dos dados
2. **Teste de Comparação:** Mann-Whitney U (não-paramétrico) para comparar GraphQL vs REST
3. **Tamanho de Efeito:** Correlação rank-biserial
4. **Nível de significância:** α = 0.05

---

# 3 Resultados

## 3.1 Visão Geral do Dataset

*(Os valores abaixo devem ser preenchidos após a execução do experimento)*

O dataset final contém **N** medições provenientes de **50** repositórios. As medições estão distribuídas igualmente entre GraphQL e REST, com **10 trials** por combinação de repositório, tipo de consulta e API.

## 3.2 RQ1 — Tempo de Resposta

### Consultas Simples

Para consultas simples, onde uma única chamada é necessária em ambas as APIs, observamos que...

*(Resultados a serem preenchidos após análise)*

### Consultas Médias

Para consultas de complexidade média, onde REST requer 2 chamadas e GraphQL apenas 1...

*(Resultados a serem preenchidos após análise)*

### Consultas Complexas

Para consultas complexas, onde REST requer N chamadas (repo + PRs + reviews por PR + comments por PR) e GraphQL apenas 1...

*(Resultados a serem preenchidos após análise)*

### Resultado Agregado (RQ1)

| Query Type | Mediana GraphQL (ms) | Mediana REST (ms) | U Statistic | p-value | Significativo? |
|---|---|---|---|---|---|
| Simples | — | — | — | — | — |
| Média | — | — | — | — | — |
| Complexa | — | — | — | — | — |
| **Agregado** | — | — | — | — | — |

## 3.3 RQ2 — Tamanho da Resposta

### Consultas Simples

Para consultas simples, o GraphQL retorna apenas os campos solicitados enquanto REST retorna todos os campos do recurso...

*(Resultados a serem preenchidos após análise)*

### Consultas Médias e Complexas

À medida que a complexidade aumenta, a diferença de tamanho tende a se acentuar...

*(Resultados a serem preenchidos após análise)*

### Resultado Agregado (RQ2)

| Query Type | Mediana GraphQL (bytes) | Mediana REST (bytes) | U Statistic | p-value | Significativo? |
|---|---|---|---|---|---|
| Simples | — | — | — | — | — |
| Média | — | — | — | — | — |
| Complexa | — | — | — | — | — |
| **Agregado** | — | — | — | — | — |

---

# 4 Discussão

## 4.1 Interpretação dos Resultados

### RQ1 — Tempo de Resposta

O tempo de resposta é influenciado por dois fatores principais:

1. **Número de chamadas HTTP:** REST requer múltiplas chamadas para dados relacionados, enquanto GraphQL consolida tudo em uma única chamada. Este fator se torna mais relevante com o aumento da complexidade.

2. **Overhead de processamento:** GraphQL requer parsing da query no servidor, o que pode adicionar latência em consultas simples.

Esperamos observar que:
- Para **consultas simples**: tempos comparáveis (GraphQL pode ter leve overhead de parsing)
- Para **consultas complexas**: GraphQL significativamente mais rápido (elimina latência de múltiplas round-trips)

### RQ2 — Tamanho da Resposta

O tamanho da resposta é fundamentalmente diferente entre as abordagens:

1. **Over-fetching no REST:** A API REST retorna todos os campos de um recurso, incluindo campos não solicitados. GraphQL retorna apenas os campos especificados na query.

2. **Composição de dados:** Quando dados de múltiplos recursos são necessários, REST retorna informações redundantes e metadados completos de cada recurso.

Esperamos observar:
- GraphQL consistentemente **menor** em todos os níveis de complexidade
- A diferença de tamanho se **acentua** com a complexidade (mais dados redundantes em REST)

## 4.2 Ameaças à Validade

### Validade Interna
- **Variabilidade de rede:** Mitigada com warm-up requests e múltiplos trials
- **Caching:** Mitigada com alternância entre APIs e intervalos entre requisições
- **Rate limiting:** Tratado com retries exponenciais

### Validade Externa
- Os resultados são específicos para a API do GitHub e podem não generalizar para outras implementações GraphQL/REST
- A seleção dos 50 repositórios mais populares pode não representar repositórios menores

### Validade de Construto
- As consultas foram projetadas para solicitar dados equivalentes, mas REST inerentemente retorna mais dados (over-fetching)
- A medição de tempo inclui latência de rede, processamento no servidor e deserialização

### Validade de Conclusão
- Tamanho amostral adequado (500 medições por combinação)
- Uso de testes não-paramétricos apropriados para distribuições potencialmente não-normais

---

# 5 Conclusão

Este experimento controlado investigou quantitativamente as diferenças de desempenho entre APIs GraphQL e REST, utilizando a API do GitHub como caso de estudo. Os resultados obtidos permitem responder às perguntas de pesquisa formuladas:

**RQ1 (Tempo de Resposta):** *(A ser preenchido com os resultados estatísticos)*

**RQ2 (Tamanho da Resposta):** *(A ser preenchido com os resultados estatísticos)*

Os resultados deste estudo contribuem para a compreensão das diferenças práticas entre GraphQL e REST, fornecendo evidências quantitativas que podem auxiliar equipes de desenvolvimento na escolha da tecnologia mais adequada para seus projetos.

---

# 6 Referências

- [GitHub REST API](https://docs.github.com/en/rest)
- [GitHub GraphQL API](https://docs.github.com/en/graphql)
- [GraphQL Specification](https://spec.graphql.org/)
- Brito, G., & Valente, M. T. (2020). "REST vs GraphQL: A controlled experiment." IEEE International Conference on Software Architecture (ICSA).
- Vogel, M., Weber, S., & Zirpins, C. (2017). "Experiences on migrating RESTful Web Services to GraphQL." International Conference on Service-Oriented Computing.
