import csv
import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(BASE_DIR, 'data', 'results_experiment.csv')
HTML_PATH = os.path.join(BASE_DIR, 'reports', 'dashboard.html')

def read_csv(file_path):
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    return data

def generate_html(data, output_path):
    json_data = json.dumps(data)
    
    html_content = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GraphQL vs REST: Análise Crítica e Dashboard Avançado</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <!-- Plugin de BoxPlot para Chart.js -->
    <script src="https://unpkg.com/@sgratzl/chartjs-chart-boxplot@4.3.0/build/index.umd.min.js"></script>
    <!-- Ícones -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    
    <script>
        tailwind.config = {{
            theme: {{
                extend: {{
                    colors: {{
                        glass: 'rgba(255, 255, 255, 0.7)',
                        glassBorder: 'rgba(255, 255, 255, 0.5)',
                        primary: '#0ea5e9',
                        secondary: '#6366f1',
                        accent: '#f43f5e'
                    }},
                    fontFamily: {{
                        sans: ['Inter', 'Segoe UI', 'Roboto', 'sans-serif']
                    }}
                }}
            }}
        }}
    </script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        body {{
            background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
            color: #334155;
            min-height: 100vh;
            font-family: 'Inter', sans-serif;
        }}
        .glass-panel {{
            background: rgba(255, 255, 255, 0.85);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border: 1px solid rgba(255, 255, 255, 1);
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05), 0 8px 10px -6px rgba(0, 0, 0, 0.01);
            border-radius: 1rem;
        }}
        .tab-btn.active {{
            border-bottom: 3px solid #0ea5e9;
            color: #0369a1;
            background-color: rgba(14, 165, 233, 0.05);
        }}
        .tab-btn {{
            transition: all 0.2s ease-in-out;
        }}
        .table-filter-input {{
            background: #f8fafc;
            border: 1px solid #cbd5e1;
            color: #334155;
            padding: 6px 10px;
            border-radius: 6px;
            font-size: 12px;
            width: 100%;
            margin-top: 6px;
            transition: all 0.2s;
        }}
        .table-filter-input:focus {{
            outline: none;
            border-color: #0ea5e9;
            box-shadow: 0 0 0 2px rgba(14, 165, 233, 0.2);
        }}
        /* Chart container resizer */
        .chart-container {{
            position: relative;
            height: 350px;
            width: 100%;
        }}
        .chart-container-large {{
            position: relative;
            height: 450px;
            width: 100%;
        }}
        /* Scrollbar */
        ::-webkit-scrollbar {{ width: 6px; height: 6px; }}
        ::-webkit-scrollbar-track {{ background: transparent; }}
        ::-webkit-scrollbar-thumb {{ background: #cbd5e1; border-radius: 10px; }}
        ::-webkit-scrollbar-thumb:hover {{ background: #94a3b8; }}
        
        .stat-card-title {{ font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; font-weight: 700; color: #64748b; }}
        .stat-card-value {{ font-size: 2.5rem; font-weight: 800; line-height: 1; margin-top: 0.5rem; }}
    </style>
</head>
<body class="p-4 md:p-6 lg:p-8">
    <div class="max-w-[1600px] mx-auto">
        <!-- HEADER & GLOBAL CONTROLS -->
        <header class="mb-8 glass-panel p-6 flex flex-col md:flex-row justify-between items-center gap-6">
            <div>
                <h1 class="text-3xl font-extrabold bg-clip-text text-transparent bg-gradient-to-r from-sky-600 to-indigo-600 tracking-tight">
                    GraphQL vs REST 
                </h1>
                <p class="text-slate-500 mt-1 font-medium"><i class="fa-solid fa-chart-line text-sky-500 mr-2"></i>Dashboard Interativo & Análise Crítica</p>
            </div>
            
            <div class="flex items-center gap-4 bg-slate-50 p-3 rounded-lg border border-slate-200 shadow-sm">
                <div class="flex flex-col">
                    <label class="text-xs font-bold text-slate-500 uppercase tracking-wide mb-1"><i class="fa-solid fa-filter mr-1"></i>Contexto Global</label>
                    <select id="globalRepoFilter" class="bg-white text-sm text-slate-800 rounded border border-slate-300 p-2 w-56 focus:ring-2 focus:ring-sky-500 outline-none cursor-pointer shadow-sm">
                        <option value="all">Todos os Repositórios</option>
                        <option value="top10">Top 10 (Mais rápidos)</option>
                        <option value="bottom10">Top 10 (Mais lentos)</option>
                    </select>
                </div>
            </div>
        </header>

        <!-- TABS NAV -->
        <div class="mb-6 bg-white/80 rounded-xl overflow-hidden glass-panel shadow-sm">
            <nav class="flex overflow-x-auto" aria-label="Tabs">
                <button class="tab-btn active whitespace-nowrap py-4 px-6 font-semibold text-sm text-slate-600 hover:text-slate-900 flex items-center" data-target="overview">
                    <i class="fa-solid fa-chart-pie mr-2"></i>Visão Geral & Insights
                </button>
                <button class="tab-btn whitespace-nowrap py-4 px-6 font-semibold text-sm text-slate-600 hover:text-slate-900 flex items-center" data-target="distribution">
                    <i class="fa-solid fa-box-open mr-2"></i>Distribuição Estatística
                </button>
                <button class="tab-btn whitespace-nowrap py-4 px-6 font-semibold text-sm text-slate-600 hover:text-slate-900 flex items-center" data-target="correlation">
                    <i class="fa-solid fa-project-diagram mr-2"></i>Correlação & Anomalias
                </button>
                <button class="tab-btn whitespace-nowrap py-4 px-6 font-semibold text-sm text-slate-600 hover:text-slate-900 flex items-center" data-target="rq1">
                    <i class="fa-solid fa-stopwatch mr-2"></i>RQ1: Tempo
                </button>
                <button class="tab-btn whitespace-nowrap py-4 px-6 font-semibold text-sm text-slate-600 hover:text-slate-900 flex items-center" data-target="rq2">
                    <i class="fa-solid fa-weight-hanging mr-2"></i>RQ2: Tamanho
                </button>
                <button class="tab-btn whitespace-nowrap py-4 px-6 font-semibold text-sm text-slate-600 hover:text-slate-900 flex items-center" data-target="data">
                    <i class="fa-solid fa-table mr-2"></i>Explorador de Dados
                </button>
            </nav>
        </div>

        <!-- 1. TAB: OVERVIEW -->
        <div id="overview" class="tab-content block animate-[fadeIn_0.5s_ease-in-out]">
            
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4 mb-6">
                <div class="glass-panel p-5 border-t-4 border-t-slate-400">
                    <h3 class="stat-card-title">Medições Totais</h3>
                    <div class="stat-card-value text-slate-700" id="statTotalRows">0</div>
                    <p class="text-xs text-slate-500 mt-2" id="statTotalReposInfo">0 repositórios</p>
                </div>
                <div class="glass-panel p-5 border-t-4 border-t-emerald-500 relative overflow-hidden">
                    <div class="absolute right-[-10px] bottom-[-20px] text-emerald-100 opacity-50"><i class="fa-solid fa-bolt text-8xl"></i></div>
                    <h3 class="stat-card-title text-emerald-700">Tempo: Vitória GQL</h3>
                    <div class="stat-card-value text-emerald-600" id="statGqlWinTime">0%</div>
                    <p class="text-xs text-slate-500 mt-2 font-medium">Das requisições totais</p>
                </div>
                <div class="glass-panel p-5 border-t-4 border-t-indigo-500 relative overflow-hidden">
                    <div class="absolute right-[-10px] bottom-[-20px] text-indigo-100 opacity-50"><i class="fa-solid fa-compress text-8xl"></i></div>
                    <h3 class="stat-card-title text-indigo-700">Tamanho: Vitória GQL</h3>
                    <div class="stat-card-value text-indigo-600" id="statGqlWinSize">0%</div>
                    <p class="text-xs text-slate-500 mt-2 font-medium">Das requisições totais</p>
                </div>
                <div class="glass-panel p-5 border-t-4 border-t-amber-500">
                    <h3 class="stat-card-title text-amber-700">Redução de Banda (Avg)</h3>
                    <div class="stat-card-value text-amber-600" id="statAvgBandwidth">0x</div>
                    <p class="text-xs text-slate-500 mt-2 font-medium">Menos bytes traficados</p>
                </div>
                <div class="glass-panel p-5 border-t-4 border-t-sky-500">
                    <h3 class="stat-card-title text-sky-700">Speedup Médio Global</h3>
                    <div class="stat-card-value text-sky-600" id="statAvgSpeedup">0x</div>
                    <p class="text-xs text-slate-500 mt-2 font-medium">Aceleração agregada</p>
                </div>
            </div>

            <!-- Insights Críticos e Gráficos de Resumo -->
            <div class="grid grid-cols-1 xl:grid-cols-3 gap-6">
                <div class="xl:col-span-1 flex flex-col gap-6">
                    <div class="glass-panel p-6 flex-1">
                        <h2 class="text-lg font-bold text-slate-800 mb-4 flex items-center border-b pb-2"><i class="fa-solid fa-lightbulb text-amber-400 mr-2"></i>Análise Crítica Automática</h2>
                        <ul class="space-y-4 text-sm text-slate-600" id="criticalInsightsList">
                            <!-- Injetado por JS -->
                        </ul>
                    </div>
                </div>
                <div class="xl:col-span-2 grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div class="glass-panel p-6">
                        <h2 class="text-lg font-bold text-slate-800 mb-2 flex items-center"><i class="fa-solid fa-stopwatch text-indigo-500 mr-2"></i>Comparativo: Tempo (ms)</h2>
                        <p class="text-xs text-slate-500 mb-4">Média de tempo geral por complexidade.</p>
                        <div class="chart-container">
                            <canvas id="overviewTimeChart"></canvas>
                        </div>
                    </div>
                    <div class="glass-panel p-6">
                        <h2 class="text-lg font-bold text-slate-800 mb-2 flex items-center"><i class="fa-solid fa-weight-hanging text-indigo-500 mr-2"></i>Comparativo: Tamanho (B)</h2>
                        <p class="text-xs text-slate-500 mb-4">Média de tamanho geral (Escala Logarítmica).</p>
                        <div class="chart-container">
                            <canvas id="overviewSizeChart"></canvas>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- 2. TAB: DISTRIBUIÇÃO ESTATÍSTICA (BOXPLOTS) -->
        <div id="distribution" class="tab-content hidden animate-[fadeIn_0.5s_ease-in-out]">
            <div class="glass-panel p-6 mb-6">
                <h2 class="text-xl font-bold text-slate-800 mb-2 flex items-center"><i class="fa-solid fa-box-open text-sky-500 mr-2"></i>Boxplots: Distribuição Real de Tempo (ms)</h2>
                <p class="text-sm text-slate-500 mb-6">A média pode esconder valores discrepantes (outliers) e assimetrias. O Boxplot mostra a mediana, quartis e extremos, oferecendo uma visão muito mais precisa do comportamento de rede e latência das APIs.</p>
                
                <div class="chart-container-large mb-8">
                    <canvas id="timeBoxplotChart"></canvas>
                </div>
                
                <h2 class="text-xl font-bold text-slate-800 mb-2 flex items-center border-t border-slate-200 pt-8"><i class="fa-solid fa-weight-hanging text-indigo-500 mr-2"></i>Boxplots: Distribuição de Tamanho (Bytes)</h2>
                <p class="text-sm text-slate-500 mb-6">Demonstração visual do impacto do "Over-fetching" (REST) contra requisições exatas (GraphQL) em escala logarítmica.</p>
                <div class="chart-container-large">
                    <canvas id="sizeBoxplotChart"></canvas>
                </div>
            </div>
        </div>

        <!-- 3. TAB: CORRELAÇÃO E ANOMALIAS -->
        <div id="correlation" class="tab-content hidden animate-[fadeIn_0.5s_ease-in-out]">
            <div class="glass-panel p-6 mb-6">
                <div class="flex justify-between items-start mb-6">
                    <div>
                        <h2 class="text-xl font-bold text-slate-800 flex items-center"><i class="fa-solid fa-project-diagram text-rose-500 mr-2"></i>Correlação: Tempo vs Tamanho</h2>
                        <p class="text-sm text-slate-500 mt-1">Este gráfico de dispersão (Scatter) mapeia cada requisição individual. Permite identificar se pacotes maiores sempre significam respostas mais lentas e ajuda a localizar <b>anomalias (outliers)</b> onde o REST pode ter sido subitamente eficiente ou o GraphQL ineficiente.</p>
                    </div>
                    <div class="bg-slate-50 p-2 rounded-lg border border-slate-200">
                        <label class="text-xs font-bold text-slate-500 mb-1 block">Filtro de Visualização</label>
                        <select id="scatterQueryFilter" class="bg-white text-xs border border-slate-300 rounded p-1 w-32">
                            <option value="all">Todas Queries</option>
                            <option value="simple">Simples</option>
                            <option value="medium">Média</option>
                            <option value="complex">Complexa</option>
                        </select>
                    </div>
                </div>
                <div class="chart-container-large" style="height: 600px;">
                    <canvas id="correlationScatterChart"></canvas>
                </div>
            </div>
        </div>

        <!-- 4. TAB: RQ1 TEMPO -->
        <div id="rq1" class="tab-content hidden animate-[fadeIn_0.5s_ease-in-out]">
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                <div class="glass-panel p-6">
                    <h2 class="text-lg font-bold text-slate-800 mb-2">Tempo Médio Bruto (ms)</h2>
                    <p class="text-xs text-slate-500 mb-4">Média simples aritmética para todas as requisições por complexidade.</p>
                    <div class="chart-container">
                        <canvas id="rq1BarChart"></canvas>
                    </div>
                </div>
                
                <div class="glass-panel p-6">
                    <h2 class="text-lg font-bold text-slate-800 mb-2">Linha de Tendência de Estabilidade (Trails)</h2>
                    <p class="text-xs text-slate-500 mb-4">Acompanha a latência ao longo de repetições contínuas, identificando impactos de <i>caching</i> e aquecimento.</p>
                    <div class="flex gap-2 mb-2">
                        <button class="px-2 py-1 bg-sky-100 text-sky-700 rounded text-xs font-bold rq1-trend-btn active-btn border border-sky-300" data-query="simple">Simples</button>
                        <button class="px-2 py-1 bg-slate-100 text-slate-600 rounded text-xs font-bold rq1-trend-btn border border-slate-200 hover:bg-slate-200" data-query="medium">Média</button>
                        <button class="px-2 py-1 bg-slate-100 text-slate-600 rounded text-xs font-bold rq1-trend-btn border border-slate-200 hover:bg-slate-200" data-query="complex">Complexa</button>
                    </div>
                    <div class="chart-container" style="height: 300px;">
                        <canvas id="rq1TrendChart"></canvas>
                    </div>
                </div>
            </div>
        </div>

        <!-- 5. TAB: RQ2 TAMANHO -->
        <div id="rq2" class="tab-content hidden animate-[fadeIn_0.5s_ease-in-out]">
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                <div class="glass-panel p-6">
                    <h2 class="text-lg font-bold text-slate-800 mb-2">Tamanho Transferido (Bytes - Log Scale)</h2>
                    <p class="text-xs text-slate-500 mb-4">Gráfico em escala logarítmica detalhando as proporções astronômicas de diferença entre a precisão do GraphQL e o modelo monolítico do REST.</p>
                    <div class="chart-container">
                        <canvas id="rq2BarChart"></canvas>
                    </div>
                </div>
                
                <div class="glass-panel p-6">
                    <h2 class="text-lg font-bold text-slate-800 mb-2">Mapa do Desperdício (Over-fetching)</h2>
                    <p class="text-xs text-slate-500 mb-4">Calcula a porcentagem da largura de banda desperdiçada pelas requisições REST (assumindo que o GraphQL entrega exatamente 100% da necessidade).</p>
                    <div class="chart-container flex items-center justify-center">
                        <canvas id="rq2WasteChart"></canvas>
                    </div>
                </div>
            </div>
        </div>

        <!-- 6. TAB: TABELA DE DADOS -->
        <div id="data" class="tab-content hidden animate-[fadeIn_0.5s_ease-in-out]">
            <div class="glass-panel p-6 mb-6">
                <div class="flex flex-col md:flex-row justify-between items-center mb-6 gap-4 border-b border-slate-200 pb-4">
                    <h2 class="text-xl font-bold flex items-center text-slate-800"><i class="fa-solid fa-table mr-2 text-indigo-500"></i>Dataset Original Explorável</h2>
                    
                    <div class="relative w-full md:w-1/3">
                        <div class="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
                            <i class="fa-solid fa-search text-slate-400"></i>
                        </div>
                        <input type="text" id="globalSearch" class="bg-white border border-slate-300 text-slate-800 text-sm rounded-lg focus:ring-sky-500 focus:border-sky-500 block w-full pl-10 p-2.5 shadow-sm" placeholder="Busca livre... ex: 'facebook' ou '> 500'">
                    </div>
                </div>

                <div class="bg-slate-50 p-3 rounded-lg border border-slate-200 mb-4 text-xs text-slate-600 flex items-center gap-2">
                    <i class="fa-solid fa-circle-info text-sky-500"></i> Dica: Nos campos de Tempo e Tamanho, você pode usar operadores condicionais como <b>> 1000</b> ou <b><= 5000</b>.
                </div>

                <div class="overflow-x-auto rounded-lg border border-slate-200 shadow-sm">
                    <table class="min-w-full divide-y divide-slate-200 text-sm">
                        <thead class="bg-slate-100">
                            <tr>
                                <th class="px-4 py-3 text-left">
                                    <span class="text-xs font-bold text-slate-600 uppercase tracking-wider">Repositório</span>
                                    <select id="colFilterRepo" class="table-filter-input">
                                        <option value="">Todos</option>
                                    </select>
                                </th>
                                <th class="px-4 py-3 text-left w-32">
                                    <span class="text-xs font-bold text-slate-600 uppercase tracking-wider">Complexidade</span>
                                    <select id="colFilterQuery" class="table-filter-input">
                                        <option value="">Todas</option>
                                        <option value="simple">Simple</option>
                                        <option value="medium">Medium</option>
                                        <option value="complex">Complex</option>
                                    </select>
                                </th>
                                <th class="px-4 py-3 text-left w-32">
                                    <span class="text-xs font-bold text-slate-600 uppercase tracking-wider">API</span>
                                    <select id="colFilterApi" class="table-filter-input">
                                        <option value="">Ambas</option>
                                        <option value="graphql">GraphQL</option>
                                        <option value="rest">REST</option>
                                    </select>
                                </th>
                                <th class="px-4 py-3 text-center w-24">
                                    <span class="text-xs font-bold text-slate-600 uppercase tracking-wider">Trial</span>
                                    <input type="text" id="colFilterTrial" class="table-filter-input text-center" placeholder="Ex: 1">
                                </th>
                                <th class="px-4 py-3 text-right w-32">
                                    <span class="text-xs font-bold text-slate-600 uppercase tracking-wider">Tempo (ms)</span>
                                    <input type="text" id="colFilterTime" class="table-filter-input text-right" placeholder="Ex: > 1000">
                                </th>
                                <th class="px-4 py-3 text-right w-36">
                                    <span class="text-xs font-bold text-slate-600 uppercase tracking-wider">Tamanho (Bytes)</span>
                                    <input type="text" id="colFilterSize" class="table-filter-input text-right" placeholder="Ex: < 5000">
                                </th>
                            </tr>
                        </thead>
                        <tbody id="dataTableBody" class="divide-y divide-slate-100 bg-white">
                            <!-- Injetado via JS -->
                        </tbody>
                    </table>
                </div>
                <div class="mt-4 text-slate-500 text-sm flex justify-between font-medium items-center">
                    <span id="tableCountInfo" class="bg-sky-50 text-sky-700 px-3 py-1 rounded-full border border-sky-200">Mostrando 0 registros</span>
                    <button id="clearFiltersBtn" class="bg-slate-100 hover:bg-slate-200 text-slate-700 px-3 py-1.5 rounded-md transition-colors border border-slate-300"><i class="fa-solid fa-filter-circle-xmark mr-1"></i>Limpar Filtros</button>
                </div>
            </div>
        </div>
    </div>

    <script>
        // -------------------------------------------------------------
        // DADOS E UTILITÁRIOS GLOBAIS
        // -------------------------------------------------------------
        const originalCsvData = {json_data};
        let activeContextData = originalCsvData; 
        
        // Definição de Cores Profissionais
        const theme = {{
            rest: {{ bg: 'rgba(249, 115, 22, 0.7)', border: 'rgba(234, 88, 12, 1)', point: 'rgba(234, 88, 12, 0.8)' }}, // Laranja
            gql: {{ bg: 'rgba(14, 165, 233, 0.7)', border: 'rgba(2, 132, 199, 1)', point: 'rgba(2, 132, 199, 0.8)' }},  // Azul Claro
            text: '#334155', grid: 'rgba(226, 232, 240, 0.8)'
        }};

        Chart.defaults.color = theme.text;
        Chart.defaults.borderColor = theme.grid;
        Chart.defaults.font.family = "'Inter', sans-serif";

        const getAvg = (arr, key) => arr.length ? arr.reduce((sum, item) => sum + parseFloat(item[key]), 0) / arr.length : 0;
        
        const charts = {{}};
        function destroyChart(id) {{ if (charts[id]) charts[id].destroy(); }}

        // -------------------------------------------------------------
        // INICIALIZAÇÃO
        // -------------------------------------------------------------
        function initApp() {{
            populateFilters();
            setupEventListeners();
            
            // Render Inicial
            updateGlobalContext(); 
        }}

        function populateFilters() {{
            const repos = [...new Set(originalCsvData.map(d => d.repo))].sort();
            const colRepo = document.getElementById('colFilterRepo');
            repos.forEach(repo => {{
                const opt = document.createElement('option');
                opt.value = repo; opt.textContent = repo;
                colRepo.appendChild(opt);
            }});
        }}

        function setupEventListeners() {{
            // Global Context
            document.getElementById('globalRepoFilter').addEventListener('change', updateGlobalContext);
            
            // Tabs - AQUI FOI CORRIGIDO O BUG DA TROCA DE ABAS!
            document.querySelectorAll('.tab-btn').forEach(btn => {{
                btn.addEventListener('click', (e) => {{
                    // Remove estado ativo de todos os botões e oculta todas as abas
                    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
                    document.querySelectorAll('.tab-content').forEach(c => {{
                        c.classList.add('hidden');
                        c.classList.remove('block');
                    }});
                    
                    // Adiciona ativo no botão clicado
                    const targetBtn = e.target.closest('.tab-btn');
                    targetBtn.classList.add('active');
                    
                    // Mostra aba correspondente
                    const targetTabId = targetBtn.dataset.target;
                    const targetTab = document.getElementById(targetTabId);
                    targetTab.classList.remove('hidden');
                    targetTab.classList.add('block');
                    
                    // Render charts specifically for active tab
                    renderActiveTabCharts(targetTabId);
                }});
            }});

            // Trend Sub-tabs
            document.querySelectorAll('.rq1-trend-btn').forEach(btn => {{
                btn.addEventListener('click', (e) => {{
                    document.querySelectorAll('.rq1-trend-btn').forEach(b => {{
                        b.classList.remove('bg-sky-100', 'text-sky-700', 'active-btn', 'border-sky-300');
                        b.classList.add('bg-slate-100', 'text-slate-600', 'border-slate-200');
                    }});
                    e.target.classList.remove('bg-slate-100', 'text-slate-600', 'border-slate-200');
                    e.target.classList.add('bg-sky-100', 'text-sky-700', 'active-btn', 'border-sky-300');
                    renderRq1();
                }});
            }});

            // Scatter filter
            document.getElementById('scatterQueryFilter').addEventListener('change', renderCorrelation);

            // Table Filters
            const tableInputs = ['globalSearch', 'colFilterRepo', 'colFilterQuery', 'colFilterApi', 'colFilterTrial', 'colFilterTime', 'colFilterSize'];
            tableInputs.forEach(id => {{
                document.getElementById(id).addEventListener('input', renderTable);
                document.getElementById(id).addEventListener('change', renderTable);
            }});

            document.getElementById('clearFiltersBtn').addEventListener('click', () => {{
                tableInputs.forEach(id => document.getElementById(id).value = '');
                renderTable();
            }});
        }}

        function updateGlobalContext() {{
            const filter = document.getElementById('globalRepoFilter').value;
            
            if (filter === 'all') {{
                activeContextData = originalCsvData;
            }} else {{
                // Agrupar repos por tempo médio (GraphQL + REST somados) para definir lentos/rápidos
                const repoTimes = {{}};
                originalCsvData.forEach(d => {{
                    if(!repoTimes[d.repo]) repoTimes[d.repo] = {{ sum: 0, count: 0 }};
                    repoTimes[d.repo].sum += parseFloat(d.response_time_ms);
                    repoTimes[d.repo].count += 1;
                }});
                
                const sortedRepos = Object.keys(repoTimes)
                    .map(r => ({{ repo: r, avg: repoTimes[r].sum / repoTimes[r].count }}))
                    .sort((a,b) => a.avg - b.avg);
                
                let targetRepos = [];
                if (filter === 'top10') targetRepos = sortedRepos.slice(0, 10).map(x => x.repo);
                if (filter === 'bottom10') targetRepos = sortedRepos.slice(-10).map(x => x.repo);
                
                activeContextData = originalCsvData.filter(d => targetRepos.includes(d.repo));
            }}
            
            renderAllViews();
        }}

        function renderAllViews() {{
            renderOverview();
            renderTable();
            // Acha qual aba está visível e manda renderizar
            const activeTab = document.querySelector('.tab-content.block');
            if(activeTab) {{
                renderActiveTabCharts(activeTab.id);
            }} else {{
                renderActiveTabCharts('overview'); // fallback
            }}
        }}

        function renderActiveTabCharts(activeId) {{
            if (activeId === 'overview') renderOverviewCharts();
            if (activeId === 'distribution') renderDistribution();
            if (activeId === 'correlation') renderCorrelation();
            if (activeId === 'rq1') renderRq1();
            if (activeId === 'rq2') renderRq2();
        }}

        // -------------------------------------------------------------
        // RENDER: OVERVIEW & INSIGHTS
        // -------------------------------------------------------------
        function renderOverview() {{
            document.getElementById('statTotalRows').textContent = activeContextData.length.toLocaleString('pt-BR');
            const uniqueRepos = new Set(activeContextData.map(d => d.repo)).size;
            document.getElementById('statTotalReposInfo').textContent = `${{uniqueRepos}} repositórios neste contexto`;

            // Calculate Wins
            let gqlWinsTime = 0, restWinsTime = 0;
            let gqlWinsSize = 0, restWinsSize = 0;
            
            // Need to pair them up by Repo + Query + Trial
            const pairs = {{}};
            activeContextData.forEach(d => {{
                const key = `${{d.repo}}_${{d.query_type}}_${{d.trial}}`;
                if(!pairs[key]) pairs[key] = {{}};
                pairs[key][d.api_type] = d;
            }});

            let validPairs = 0;
            for (let k in pairs) {{
                if (pairs[k].graphql && pairs[k].rest) {{
                    validPairs++;
                    const gTime = parseFloat(pairs[k].graphql.response_time_ms);
                    const rTime = parseFloat(pairs[k].rest.response_time_ms);
                    const gSize = parseFloat(pairs[k].graphql.response_size_bytes);
                    const rSize = parseFloat(pairs[k].rest.response_size_bytes);
                    
                    if (gTime < rTime) gqlWinsTime++; else restWinsTime++;
                    if (gSize < rSize) gqlWinsSize++; else restWinsSize++;
                }}
            }}

            const timeWinPct = validPairs ? (gqlWinsTime / validPairs * 100) : 0;
            const sizeWinPct = validPairs ? (gqlWinsSize / validPairs * 100) : 0;
            
            document.getElementById('statGqlWinTime').textContent = timeWinPct.toFixed(1) + '%';
            document.getElementById('statGqlWinSize').textContent = sizeWinPct.toFixed(1) + '%';
            
            // Averages
            const restTime = getAvg(activeContextData.filter(d=>d.api_type==='rest'), 'response_time_ms');
            const gqlTime = getAvg(activeContextData.filter(d=>d.api_type==='graphql'), 'response_time_ms');
            const restSize = getAvg(activeContextData.filter(d=>d.api_type==='rest'), 'response_size_bytes');
            const gqlSize = getAvg(activeContextData.filter(d=>d.api_type==='graphql'), 'response_size_bytes');

            const speedup = gqlTime > 0 ? (restTime / gqlTime) : 0;
            const bandwidth = gqlSize > 0 ? (restSize / gqlSize) : 0;
            
            document.getElementById('statAvgSpeedup').textContent = speedup.toFixed(1) + 'x';
            document.getElementById('statAvgBandwidth').textContent = bandwidth.toFixed(1) + 'x';

            // Critical Insights Text
            const list = document.getElementById('criticalInsightsList');
            list.innerHTML = `
                <li><i class="fa-solid fa-check text-emerald-500 mr-2"></i><b>Desempenho Geral:</b> O GraphQL foi mais rápido em <b>${{timeWinPct.toFixed(1)}}%</b> das medições avaliadas. A diferença média consolida uma aceleração de <b>${{speedup.toFixed(1)}}x</b> no tempo de requisição.</li>
                <li><i class="fa-solid fa-check text-emerald-500 mr-2"></i><b>Tráfego de Rede:</b> Em <b>${{sizeWinPct.toFixed(1)}}%</b> dos casos o payload do GraphQL foi menor. O over-fetching do REST causou um tráfego <b>${{bandwidth.toFixed(1)}}x</b> maior na média global.</li>
                <li><i class="fa-solid fa-triangle-exclamation text-amber-500 mr-2"></i><b>Comportamento por Complexidade:</b> À medida que a consulta exige dados aninhados (PRs, Comments), o modelo monolítico do REST escala linearmente a latência devido à explosão de chamadas N+1 necessárias, enquanto a chamada única do GraphQL estabiliza o tempo e a banda.</li>
            `;
        }}

        function renderOverviewCharts() {{
            const qTypes = ['simple', 'medium', 'complex'];
            const labels = ['Simples', 'Média', 'Complexa'];

            // Time Chart
            destroyChart('overviewTimeChart');
            charts['overviewTimeChart'] = new Chart(document.getElementById('overviewTimeChart'), {{
                type: 'bar',
                data: {{
                    labels: labels,
                    datasets: [
                        {{ label: 'REST (ms)', data: qTypes.map(q => getAvg(activeContextData.filter(d=>d.api_type==='rest' && d.query_type===q), 'response_time_ms')), backgroundColor: theme.rest.bg, borderRadius: 4 }},
                        {{ label: 'GraphQL (ms)', data: qTypes.map(q => getAvg(activeContextData.filter(d=>d.api_type==='graphql' && d.query_type===q), 'response_time_ms')), backgroundColor: theme.gql.bg, borderRadius: 4 }}
                    ]
                }},
                options: {{ responsive: true, maintainAspectRatio: false }}
            }});

            // Size Chart
            destroyChart('overviewSizeChart');
            charts['overviewSizeChart'] = new Chart(document.getElementById('overviewSizeChart'), {{
                type: 'bar',
                data: {{
                    labels: labels,
                    datasets: [
                        {{ label: 'REST (Bytes)', data: qTypes.map(q => getAvg(activeContextData.filter(d=>d.api_type==='rest' && d.query_type===q), 'response_size_bytes')), backgroundColor: theme.rest.bg, borderRadius: 4 }},
                        {{ label: 'GraphQL (Bytes)', data: qTypes.map(q => getAvg(activeContextData.filter(d=>d.api_type==='graphql' && d.query_type===q), 'response_size_bytes')), backgroundColor: theme.gql.bg, borderRadius: 4 }}
                    ]
                }},
                options: {{ 
                    responsive: true, maintainAspectRatio: false, 
                    scales: {{ y: {{ type: 'logarithmic', title: {{ display: true, text: 'Bytes (Log)' }} }} }}
                }}
            }});
        }}

        // -------------------------------------------------------------
        // RENDER: DISTRIBUIÇÃO ESTATÍSTICA (BOXPLOT)
        // -------------------------------------------------------------
        function renderDistribution() {{
            const queries = ['simple', 'medium', 'complex'];
            const formatForBoxplot = (api, key) => {{
                return queries.map(q => {{
                    const subset = activeContextData.filter(d => d.api_type === api && d.query_type === q).map(d => parseFloat(d[key]));
                    return subset;
                }});
            }};

            destroyChart('timeBoxplotChart');
            charts['timeBoxplotChart'] = new Chart(document.getElementById('timeBoxplotChart'), {{
                type: 'boxplot',
                data: {{
                    labels: ['Query Simples', 'Query Média', 'Query Complexa'],
                    datasets: [
                        {{
                            label: 'REST',
                            data: formatForBoxplot('rest', 'response_time_ms'),
                            backgroundColor: theme.rest.bg, borderColor: theme.rest.border,
                            borderWidth: 1, itemRadius: 2, itemBackgroundColor: theme.rest.border
                        }},
                        {{
                            label: 'GraphQL',
                            data: formatForBoxplot('graphql', 'response_time_ms'),
                            backgroundColor: theme.gql.bg, borderColor: theme.gql.border,
                            borderWidth: 1, itemRadius: 2, itemBackgroundColor: theme.gql.border
                        }}
                    ]
                }},
                options: {{ responsive: true, maintainAspectRatio: false }}
            }});

            destroyChart('sizeBoxplotChart');
            charts['sizeBoxplotChart'] = new Chart(document.getElementById('sizeBoxplotChart'), {{
                type: 'boxplot',
                data: {{
                    labels: ['Query Simples', 'Query Média', 'Query Complexa'],
                    datasets: [
                        {{
                            label: 'REST',
                            data: formatForBoxplot('rest', 'response_size_bytes'),
                            backgroundColor: theme.rest.bg, borderColor: theme.rest.border,
                            borderWidth: 1, itemRadius: 0
                        }},
                        {{
                            label: 'GraphQL',
                            data: formatForBoxplot('graphql', 'response_size_bytes'),
                            backgroundColor: theme.gql.bg, borderColor: theme.gql.border,
                            borderWidth: 1, itemRadius: 0
                        }}
                    ]
                }},
                options: {{ 
                    responsive: true, maintainAspectRatio: false,
                    scales: {{ y: {{ type: 'logarithmic' }} }} 
                }}
            }});
        }}

        // -------------------------------------------------------------
        // RENDER: CORRELAÇÃO & OUTLIERS (SCATTER)
        // -------------------------------------------------------------
        function renderCorrelation() {{
            const qFilter = document.getElementById('scatterQueryFilter').value;
            let dataset = activeContextData;
            if (qFilter !== 'all') dataset = activeContextData.filter(d => d.query_type === qFilter);

            if (dataset.length > 2000) {{
                const step = Math.ceil(dataset.length / 2000);
                dataset = dataset.filter((_, i) => i % step === 0);
            }}

            const restPoints = dataset.filter(d => d.api_type === 'rest').map(d => ({{ 
                x: parseFloat(d.response_size_bytes), 
                y: parseFloat(d.response_time_ms), 
                repo: d.repo, q: d.query_type 
            }}));
            const gqlPoints = dataset.filter(d => d.api_type === 'graphql').map(d => ({{ 
                x: parseFloat(d.response_size_bytes), 
                y: parseFloat(d.response_time_ms), 
                repo: d.repo, q: d.query_type 
            }}));

            destroyChart('correlationScatterChart');
            charts['correlationScatterChart'] = new Chart(document.getElementById('correlationScatterChart'), {{
                type: 'scatter',
                data: {{
                    datasets: [
                        {{
                            label: 'REST (Bytes vs ms)',
                            data: restPoints,
                            backgroundColor: theme.rest.point, borderColor: 'rgba(255,255,255,0.2)', borderWidth: 1,
                            pointRadius: 4, pointHoverRadius: 7
                        }},
                        {{
                            label: 'GraphQL (Bytes vs ms)',
                            data: gqlPoints,
                            backgroundColor: theme.gql.point, borderColor: 'rgba(255,255,255,0.2)', borderWidth: 1,
                            pointRadius: 4, pointHoverRadius: 7
                        }}
                    ]
                }},
                options: {{
                    responsive: true, maintainAspectRatio: false,
                    scales: {{
                        x: {{ type: 'logarithmic', title: {{ display: true, text: 'Tamanho do Payload (Bytes) - Log' }} }},
                        y: {{ title: {{ display: true, text: 'Tempo de Resposta (ms)' }} }}
                    }},
                    plugins: {{
                        tooltip: {{
                            callbacks: {{
                                label: (ctx) => `${{ctx.raw.repo}} (${{ctx.raw.q}}): ${{ctx.parsed.y}}ms / ${{ctx.parsed.x.toLocaleString('pt-BR')}}B`
                            }}
                        }}
                    }}
                }}
            }});
        }}

        // -------------------------------------------------------------
        // RENDER: RQ1 e RQ2
        // -------------------------------------------------------------
        function renderRq1() {{
            const queries = ['simple', 'medium', 'complex'];
            
            destroyChart('rq1BarChart');
            charts['rq1BarChart'] = new Chart(document.getElementById('rq1BarChart'), {{
                type: 'bar',
                data: {{
                    labels: ['Simples', 'Média', 'Complexa'],
                    datasets: [
                        {{ label: 'REST', data: queries.map(q => getAvg(activeContextData.filter(d=>d.api_type==='rest' && d.query_type===q), 'response_time_ms')), backgroundColor: theme.rest.bg, borderRadius: 4 }},
                        {{ label: 'GraphQL', data: queries.map(q => getAvg(activeContextData.filter(d=>d.api_type==='graphql' && d.query_type===q), 'response_time_ms')), backgroundColor: theme.gql.bg, borderRadius: 4 }}
                    ]
                }},
                options: {{ responsive: true, maintainAspectRatio: false }}
            }});

            const activeBtn = document.querySelector('.rq1-trend-btn.active-btn');
            const qType = activeBtn ? activeBtn.dataset.query : 'medium';
            const filtered = activeContextData.filter(d => d.query_type === qType);
            
            const maxTrials = Math.max(...filtered.map(d => parseInt(d.trial)));
            const labels = Array.from({{length: maxTrials}}, (_, i) => `T${{i+1}}`);
            
            const restTrend = labels.map((_, i) => getAvg(filtered.filter(d=>d.api_type==='rest' && parseInt(d.trial) === i+1), 'response_time_ms'));
            const gqlTrend = labels.map((_, i) => getAvg(filtered.filter(d=>d.api_type==='graphql' && parseInt(d.trial) === i+1), 'response_time_ms'));

            destroyChart('rq1TrendChart');
            charts['rq1TrendChart'] = new Chart(document.getElementById('rq1TrendChart'), {{
                type: 'line',
                data: {{
                    labels: labels,
                    datasets: [
                        {{ label: 'REST Avg', data: restTrend, borderColor: theme.rest.border, backgroundColor: theme.rest.point, tension: 0.3 }},
                        {{ label: 'GQL Avg', data: gqlTrend, borderColor: theme.gql.border, backgroundColor: theme.gql.point, tension: 0.3 }}
                    ]
                }},
                options: {{ responsive: true, maintainAspectRatio: false }}
            }});
        }}

        function renderRq2() {{
            const queries = ['simple', 'medium', 'complex'];
            
            destroyChart('rq2BarChart');
            charts['rq2BarChart'] = new Chart(document.getElementById('rq2BarChart'), {{
                type: 'bar',
                data: {{
                    labels: ['Simples', 'Média', 'Complexa'],
                    datasets: [
                        {{ label: 'REST (Bytes)', data: queries.map(q => getAvg(activeContextData.filter(d=>d.api_type==='rest' && d.query_type===q), 'response_size_bytes')), backgroundColor: theme.rest.bg, borderRadius: 4 }},
                        {{ label: 'GraphQL (Bytes)', data: queries.map(q => getAvg(activeContextData.filter(d=>d.api_type==='graphql' && d.query_type===q), 'response_size_bytes')), backgroundColor: theme.gql.bg, borderRadius: 4 }}
                    ]
                }},
                options: {{ 
                    responsive: true, maintainAspectRatio: false,
                    scales: {{ y: {{ type: 'logarithmic' }} }}
                }}
            }});

            const rSize = getAvg(activeContextData.filter(d=>d.api_type==='rest'), 'response_size_bytes');
            const gSize = getAvg(activeContextData.filter(d=>d.api_type==='graphql'), 'response_size_bytes');
            const waste = Math.max(0, rSize - gSize);

            destroyChart('rq2WasteChart');
            charts['rq2WasteChart'] = new Chart(document.getElementById('rq2WasteChart'), {{
                type: 'doughnut',
                data: {{
                    labels: ['Dados Úteis Equivalentes (GraphQL)', 'Desperdício de Banda (REST)'],
                    datasets: [{{
                        data: [gSize, waste],
                        backgroundColor: [theme.gql.bg, 'rgba(239, 68, 68, 0.6)'],
                        borderColor: ['#fff', '#fff'], borderWidth: 2
                    }}]
                }},
                options: {{ responsive: true, maintainAspectRatio: false, cutout: '65%' }}
            }});
        }}

        // -------------------------------------------------------------
        // RENDER: TABELA DE EXPLORAÇÃO
        // -------------------------------------------------------------
        function parseCondition(filterValue, actualValue) {{
            if (!filterValue) return true;
            filterValue = filterValue.trim();
            const numVal = parseFloat(actualValue);
            
            if (filterValue.startsWith('>=')) return numVal >= parseFloat(filterValue.substring(2));
            if (filterValue.startsWith('<=')) return numVal <= parseFloat(filterValue.substring(2));
            if (filterValue.startsWith('>')) return numVal > parseFloat(filterValue.substring(1));
            if (filterValue.startsWith('<')) return numVal < parseFloat(filterValue.substring(1));
            if (filterValue.startsWith('=')) return numVal === parseFloat(filterValue.substring(1));
            
            return actualValue.toString().toLowerCase().includes(filterValue.toLowerCase());
        }}

        function renderTable() {{
            const globalSearch = document.getElementById('globalSearch').value.toLowerCase();
            const colRepo = document.getElementById('colFilterRepo').value;
            const colQuery = document.getElementById('colFilterQuery').value;
            const colApi = document.getElementById('colFilterApi').value;
            const colTrial = document.getElementById('colFilterTrial').value;
            const colTime = document.getElementById('colFilterTime').value;
            const colSize = document.getElementById('colFilterSize').value;

            const filteredData = activeContextData.filter(row => {{
                if (globalSearch) {{
                    const rowText = Object.values(row).join(' ').toLowerCase();
                    if (!rowText.includes(globalSearch)) return false;
                }}
                
                if (colRepo && row.repo !== colRepo) return false;
                if (colQuery && row.query_type !== colQuery) return false;
                if (colApi && row.api_type !== colApi) return false;
                if (!parseCondition(colTrial, row.trial)) return false;
                if (!parseCondition(colTime, row.response_time_ms)) return false;
                if (!parseCondition(colSize, row.response_size_bytes)) return false;

                return true;
            }});

            const displayData = filteredData.slice(0, 300); // Pagination/Limit
            
            const tbody = document.getElementById('dataTableBody');
            tbody.innerHTML = '';
            
            displayData.forEach(row => {{
                const tr = document.createElement('tr');
                tr.className = 'hover:bg-slate-50 transition-colors';
                
                const ms = parseFloat(row.response_time_ms);
                const timeColorClass = ms > 2500 ? 'text-red-600 font-bold' : (ms < 500 ? 'text-emerald-600' : 'text-slate-700');
                
                tr.innerHTML = `
                    <td class="px-4 py-2 whitespace-nowrap text-slate-800 font-medium">${{row.repo.split('/')[1] || row.repo}}</td>
                    <td class="px-4 py-2 whitespace-nowrap text-slate-600 capitalize">${{row.query_type}}</td>
                    <td class="px-4 py-2 whitespace-nowrap uppercase text-center">
                        <span class="px-2 py-0.5 rounded text-[10px] font-black tracking-wider ${{row.api_type === 'graphql' ? 'bg-sky-100 text-sky-700 border border-sky-200' : 'bg-orange-100 text-orange-700 border border-orange-200'}}">
                            ${{row.api_type}}
                        </span>
                    </td>
                    <td class="px-4 py-2 whitespace-nowrap text-slate-600 text-center">${{row.trial}}</td>
                    <td class="px-4 py-2 whitespace-nowrap text-right ${{timeColorClass}}">${{ms.toFixed(0)}}</td>
                    <td class="px-4 py-2 whitespace-nowrap text-right text-slate-600 font-mono text-xs">${{parseInt(row.response_size_bytes).toLocaleString('pt-BR')}}</td>
                `;
                tbody.appendChild(tr);
            }});

            let infoText = `Exibindo ${{displayData.length}} de ${{filteredData.length}} itens (filtrados)`;
            if(filteredData.length > 300) infoText += ` - Limitado aos 300 primeiros para performance.`;
            document.getElementById('tableCountInfo').textContent = infoText;
        }}

        window.addEventListener('DOMContentLoaded', initApp);
    </script>
</body>
</html>"""
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"Dashboard gerado com sucesso em: {output_path}")

if __name__ == "__main__":
    if not os.path.exists(CSV_PATH):
        print(f"Erro: CSV não encontrado em {CSV_PATH}")
    else:
        data = read_csv(CSV_PATH)
        generate_html(data, HTML_PATH)
