"use client";

import React, { useState, useEffect, useMemo } from "react";
import Papa from "papaparse";
import {
  Card, Grid, Metric, Text, Title, TabGroup, TabList, Tab, TabPanels, TabPanel,
  BarChart, DonutChart, ScatterChart, Flex, BadgeDelta, Select, SelectItem,
  MultiSelect, MultiSelectItem, Table, TableHead, TableRow, TableHeaderCell,
  TableBody, TableCell, Badge, Divider, TextInput
} from "@tremor/react";
import {
  RiTimerFlashLine, RiDatabase2Line, RiLineChartLine, RiTableLine,
  RiErrorWarningLine, RiFilter3Line, RiSearchLine,
  RiArrowUpSLine, RiArrowDownSLine, RiArrowUpDownLine
} from "@remixicon/react";

export default function Dashboard() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);

  // Advanced BI Filters
  const [selectedRepos, setSelectedRepos] = useState([]);
  const [selectedComplexities, setSelectedComplexities] = useState([]);
  const [maxTimeFilter, setMaxTimeFilter] = useState("all");

  // Table specific state
  const [tableSearch, setTableSearch] = useState("");
  const [tablePage, setTablePage] = useState(1);
  const itemsPerPage = 20;
  const [sortConfig, setSortConfig] = useState({ key: null, direction: "asc" });
  const [colFilters, setColFilters] = useState({
    repo: "",
    api_type: "all",
    query_type: "all",
  });

  useEffect(() => {
    setTablePage(1);
  }, [selectedRepos, selectedComplexities, maxTimeFilter, tableSearch, colFilters, sortConfig]);

  useEffect(() => {
    async function loadData() {
      try {
        const response = await fetch("/results_experiment.csv");
        const csvText = await response.text();
        Papa.parse(csvText, {
          header: true,
          skipEmptyLines: true,
          complete: (results) => {
            setData(results.data);
            setLoading(false);
          },
        });
      } catch (err) {
        console.error("Error loading CSV:", err);
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const allRepos = useMemo(() => Array.from(new Set(data.map(d => d.repo))).sort(), [data]);
  const allComplexities = useMemo(() => Array.from(new Set(data.map(d => d.query_type))).sort(), [data]);

  // Apply all filters
  const activeData = useMemo(() => {
    return data.filter(d => {
      // Filter by Repo
      if (selectedRepos.length > 0 && !selectedRepos.includes(d.repo)) return false;
      
      // Filter by Complexity
      if (selectedComplexities.length > 0 && !selectedComplexities.includes(d.query_type)) return false;
      
      // Filter by Time limit (outlier removal)
      if (maxTimeFilter !== "all") {
        if (parseFloat(d.response_time_ms) > parseInt(maxTimeFilter)) return false;
      }
      
      return true;
    });
  }, [data, selectedRepos, selectedComplexities, maxTimeFilter]);

  const stats = useMemo(() => {
    if (!activeData.length) return null;

    let gqlWinsTime = 0, restWinsTime = 0;
    let gqlWinsSize = 0, restWinsSize = 0;

    const pairs = {};
    activeData.forEach(d => {
      const key = `${d.repo}_${d.query_type}_${d.trial}`;
      if (!pairs[key]) pairs[key] = {};
      pairs[key][d.api_type] = d;
    });

    let validPairs = 0;
    Object.values(pairs).forEach(p => {
      if (p.graphql && p.rest) {
        validPairs++;
        if (parseFloat(p.graphql.response_time_ms) < parseFloat(p.rest.response_time_ms)) gqlWinsTime++;
        else restWinsTime++;

        if (parseFloat(p.graphql.response_size_bytes) < parseFloat(p.rest.response_size_bytes)) gqlWinsSize++;
        else restWinsSize++;
      }
    });

    const getAvg = (arr, key) => arr.length ? arr.reduce((acc, curr) => acc + parseFloat(curr[key] || 0), 0) / arr.length : 0;
    const restData = activeData.filter(d => d.api_type === "rest");
    const gqlData = activeData.filter(d => d.api_type === "graphql");

    const restTime = getAvg(restData, "response_time_ms");
    const gqlTime = getAvg(gqlData, "response_time_ms");
    const restSize = getAvg(restData, "response_size_bytes");
    const gqlSize = getAvg(gqlData, "response_size_bytes");

    const speedup = gqlTime > 0 ? (restTime / gqlTime) : 0;
    const bandwidth = gqlSize > 0 ? (restSize / gqlSize) : 0;

    return {
      total: activeData.length,
      timeWinPct: validPairs ? ((gqlWinsTime / validPairs) * 100).toFixed(1) : 0,
      sizeWinPct: validPairs ? ((gqlWinsSize / validPairs) * 100).toFixed(1) : 0,
      speedup: speedup.toFixed(1),
      bandwidth: bandwidth.toFixed(1),
      waste: Math.max(0, restSize - gqlSize),
      gSize: gqlSize
    };
  }, [activeData]);

  const overviewBarData = useMemo(() => {
    const qTypes = selectedComplexities.length > 0 ? selectedComplexities : ["simple", "medium", "complex"];
    const labels = { simple: "Simples", medium: "Média", complex: "Complexa" };
    const getAvg = (arr, key) => arr.length ? arr.reduce((acc, curr) => acc + parseFloat(curr[key] || 0), 0) / arr.length : 0;

    return qTypes.map(q => {
      const gSubset = activeData.filter(d => d.api_type === "graphql" && d.query_type === q);
      const rSubset = activeData.filter(d => d.api_type === "rest" && d.query_type === q);
      return {
        name: labels[q] || q,
        "GraphQL (ms)": getAvg(gSubset, "response_time_ms"),
        "REST (ms)": getAvg(rSubset, "response_time_ms"),
        "GraphQL (Bytes)": getAvg(gSubset, "response_size_bytes"),
        "REST (Bytes)": getAvg(rSubset, "response_size_bytes"),
      };
    });
  }, [activeData, selectedComplexities]);

  const scatterData = useMemo(() => {
    let d = activeData;
    if (d.length > 800) {
      const step = Math.ceil(d.length / 800);
      d = d.filter((_, i) => i % step === 0);
    }
    return d.map(item => ({
      api: item.api_type.toUpperCase(),
      x: parseFloat(item.response_size_bytes || 0),
      y: parseFloat(item.response_time_ms || 0),
      repo: item.repo,
    }));
  }, [activeData]);

  // Table computations
  const tableData = useMemo(() => {
    let d = activeData;
    
    if (tableSearch) {
      const lowerSearch = tableSearch.toLowerCase();
      d = d.filter(item => 
        item.repo.toLowerCase().includes(lowerSearch) || 
        item.api_type.toLowerCase().includes(lowerSearch) ||
        item.query_type.toLowerCase().includes(lowerSearch)
      );
    }

    if (colFilters.repo) d = d.filter(item => item.repo.toLowerCase().includes(colFilters.repo.toLowerCase()));
    if (colFilters.api_type !== "all") d = d.filter(item => item.api_type === colFilters.api_type);
    if (colFilters.query_type !== "all") d = d.filter(item => item.query_type === colFilters.query_type);

    if (sortConfig.key) {
      d = [...d].sort((a, b) => {
        let valA = a[sortConfig.key];
        let valB = b[sortConfig.key];

        if (sortConfig.key === "response_time_ms" || sortConfig.key === "response_size_bytes") {
          valA = parseFloat(valA || 0);
          valB = parseFloat(valB || 0);
        } else {
          valA = String(valA).toLowerCase();
          valB = String(valB).toLowerCase();
        }

        if (valA < valB) return sortConfig.direction === "asc" ? -1 : 1;
        if (valA > valB) return sortConfig.direction === "asc" ? 1 : -1;
        return 0;
      });
    }

    return d;
  }, [activeData, tableSearch, colFilters, sortConfig]);

  const totalTablePages = Math.max(1, Math.ceil(tableData.length / itemsPerPage));
  const paginatedData = tableData.slice((tablePage - 1) * itemsPerPage, tablePage * itemsPerPage);

  const requestSort = (key) => {
    let direction = "asc";
    if (sortConfig.key === key && sortConfig.direction === "asc") direction = "desc";
    setSortConfig({ key, direction });
  };

  const SortIcon = ({ columnKey }) => {
    if (sortConfig.key !== columnKey) return <RiArrowUpDownLine className="w-4 h-4 ml-1 text-gray-400" />;
    return sortConfig.direction === "asc" 
      ? <RiArrowUpSLine className="w-4 h-4 ml-1 text-tremor-brand" /> 
      : <RiArrowDownSLine className="w-4 h-4 ml-1 text-tremor-brand" />;
  };

  if (loading) {
    return <div className="flex items-center justify-center h-screen"><Text>Carregando Dados do Experimento...</Text></div>;
  }

  if (!stats) return <div className="p-10"><Title>Sem dados para exibir com os filtros atuais.</Title></div>;

  return (
    <div className="flex flex-col md:flex-row h-screen bg-slate-50">
      
      {/* POWER BI STYLE FILTER PANE (SIDEBAR) */}
      <div className="w-full md:w-80 bg-white border-r border-gray-200 p-6 flex flex-col h-full shadow-sm overflow-y-auto">
        <div className="flex items-center gap-2 mb-6">
          <RiFilter3Line className="w-6 h-6 text-tremor-brand" />
          <Title className="text-xl">Filtros (BI)</Title>
        </div>

        <Text className="font-semibold mb-2 mt-4 text-sm">Repositório GitHub</Text>
        <MultiSelect 
          value={selectedRepos} 
          onValueChange={setSelectedRepos}
          placeholder="Todos os repositórios..."
          className="mb-6"
        >
          {allRepos.map(r => <MultiSelectItem key={r} value={r}>{r}</MultiSelectItem>)}
        </MultiSelect>

        <Text className="font-semibold mb-2 mt-2 text-sm">Nível de Complexidade</Text>
        <MultiSelect 
          value={selectedComplexities} 
          onValueChange={setSelectedComplexities}
          placeholder="Todas as complexidades..."
          className="mb-6"
        >
          {allComplexities.map(c => <MultiSelectItem key={c} value={c}>{c.toUpperCase()}</MultiSelectItem>)}
        </MultiSelect>

        <Text className="font-semibold mb-2 mt-2 text-sm">Filtrar Latência Máxima (Outliers)</Text>
        <Select value={maxTimeFilter} onValueChange={setMaxTimeFilter}>
          <SelectItem value="all">Sem Limite</SelectItem>
          <SelectItem value="1000">Até 1 Segundo (1000ms)</SelectItem>
          <SelectItem value="5000">Até 5 Segundos (5000ms)</SelectItem>
          <SelectItem value="10000">Até 10 Segundos (10000ms)</SelectItem>
        </Select>

        <Divider />
        
        <Card className="bg-slate-50 p-4 border-dashed border-2 border-slate-200 shadow-none">
          <Text className="text-xs font-semibold text-slate-500 uppercase">Amostras Filtradas</Text>
          <Metric className="text-2xl mt-1 text-slate-700">{activeData.length}</Metric>
          <Text className="text-xs text-slate-400 mt-1">
            {((activeData.length / data.length) * 100).toFixed(1)}% do Dataset Global
          </Text>
        </Card>
      </div>

      {/* DASHBOARD MAIN CONTENT */}
      <main className="flex-1 p-6 md:p-8 overflow-y-auto w-full">
        <Flex className="flex-col md:flex-row gap-4 items-start md:items-center justify-between mb-8">
          <div>
            <Title className="text-3xl font-bold">Performance: GraphQL vs REST</Title>
            <Text>Painel Interativo de Análise Multidimensional</Text>
          </div>
        </Flex>

        <Grid numItemsSm={2} numItemsLg={4} className="gap-6">
          <Card decoration="top" decorationColor="emerald">
            <Text>GraphQL Vence (Tempo)</Text>
            <Metric>{stats.timeWinPct}%</Metric>
            <Flex className="mt-2 text-xs"><Text>Em Latência Bruta</Text></Flex>
          </Card>
          <Card decoration="top" decorationColor="indigo">
            <Text>GraphQL Vence (Tamanho)</Text>
            <Metric>{stats.sizeWinPct}%</Metric>
            <Flex className="mt-2 text-xs"><Text>Menos Bytes Trafegados</Text></Flex>
          </Card>
          <Card decoration="top" decorationColor="amber">
            <Text>Eficiência de Banda REST</Text>
            <Metric className="text-rose-600">-{stats.bandwidth}x</Metric>
            <Flex className="mt-2 text-xs"><Text>Overfetching Crítico</Text></Flex>
          </Card>
          <Card decoration="top" decorationColor="cyan">
            <Text>Aceleração de Tempo GQL</Text>
            <Metric className="text-emerald-600">+{stats.speedup}x</Metric>
            <Flex className="mt-2 text-xs"><Text>Speedup Médio</Text></Flex>
          </Card>
        </Grid>

        <TabGroup className="mt-8">
          <TabList>
            <Tab icon={RiTimerFlashLine}>Comparativo Direto</Tab>
            <Tab icon={RiDatabase2Line}>Eficiência de Tráfego</Tab>
            <Tab icon={RiLineChartLine}>Dispersão de Outliers</Tab>
            <Tab icon={RiTableLine}>Raw Data Drilldown</Tab>
          </TabList>
          <TabPanels>
            {/* TAB 1 */}
            <TabPanel>
              <Grid numItemsLg={2} className="gap-6 mt-6">
                <Card>
                  <Title>Tempo de Resposta Médio (ms)</Title>
                  <BarChart
                    className="mt-4 h-80"
                    data={overviewBarData}
                    index="name"
                    categories={["GraphQL (ms)", "REST (ms)"]}
                    colors={["cyan", "orange"]}
                    valueFormatter={(num) => `${num.toFixed(1)} ms`}
                    yAxisWidth={60}
                  />
                </Card>
                <Card>
                  <Title>Payload Trafegado (Bytes)</Title>
                  <BarChart
                    className="mt-4 h-80"
                    data={overviewBarData}
                    index="name"
                    categories={["GraphQL (Bytes)", "REST (Bytes)"]}
                    colors={["indigo", "amber"]}
                    valueFormatter={(num) => `${(num/1024).toFixed(2)} KB`}
                    yAxisWidth={70}
                  />
                </Card>
              </Grid>
            </TabPanel>

            {/* TAB 2 */}
            <TabPanel>
               <Grid numItemsLg={2} className="gap-6 mt-6">
                <Card>
                  <Title>Distribuição de Tráfego: Overfetching</Title>
                  <Text className="mt-2 text-sm text-gray-500">
                    O gráfico mostra o quanto de rede foi consumido estritamente pelo dado útil (GraphQL) versus o "lixo" trafegado extra pelo REST (Desperdício).
                  </Text>
                  <DonutChart
                    className="mt-6 h-64"
                    data={[
                      { name: "Dado Útil / Alvo (GraphQL)", value: stats.gSize },
                      { name: "Desperdício de Rede (REST)", value: stats.waste }
                    ]}
                    category="value"
                    index="name"
                    colors={["emerald", "rose"]}
                    valueFormatter={(v) => `${(v/1024).toFixed(1)} KB`}
                  />
                </Card>
                <Card>
                  <Title>Métricas Detalhadas de Payload</Title>
                  <Table className="mt-5 h-[300px] overflow-y-auto">
                    <TableHead>
                      <TableRow>
                        <TableHeaderCell>Query</TableHeaderCell>
                        <TableHeaderCell className="text-right">GQL Tamanho</TableHeaderCell>
                        <TableHeaderCell className="text-right">REST Tamanho</TableHeaderCell>
                        <TableHeaderCell className="text-right">Multiplicador</TableHeaderCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {overviewBarData.map((item) => (
                        <TableRow key={item.name}>
                          <TableCell className="font-semibold">{item.name}</TableCell>
                          <TableCell className="text-right text-emerald-600 font-medium">{(item["GraphQL (Bytes)"]/1024).toFixed(1)} KB</TableCell>
                          <TableCell className="text-right text-rose-600 font-medium">{(item["REST (Bytes)"]/1024).toFixed(1)} KB</TableCell>
                          <TableCell className="text-right">
                            <BadgeDelta deltaType={item["REST (Bytes)"] > item["GraphQL (Bytes)"] ? "increase" : "decrease"}>
                              {(item["REST (Bytes)"] / (item["GraphQL (Bytes)"] || 1)).toFixed(1)}x maior
                            </BadgeDelta>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </Card>
               </Grid>
            </TabPanel>

            {/* TAB 3 */}
            <TabPanel>
              <Card className="mt-6">
                <Title>Correlação Latência vs Tamanho do Payload</Title>
                <Text>Amostra visual de até 800 pontos. Utilize os filtros laterais para realizar Drilldown em repositórios específicos.</Text>
                <ScatterChart
                  className="mt-6 h-[500px]"
                  yAxisWidth={60}
                  data={scatterData}
                  category="api"
                  x="x"
                  y="y"
                  size="x"
                  colors={["cyan", "orange"]}
                  valueFormatter={{
                    x: (val) => `${(val/1024).toFixed(1)} KB`,
                    y: (val) => `${val.toFixed(0)} ms`,
                    size: () => ''
                  }}
                />
              </Card>
            </TabPanel>

            {/* TAB 4 */}
            <TabPanel>
              <Card className="mt-6">
                <div className="flex flex-col md:flex-row items-start md:items-center justify-between mb-4 gap-4">
                  <div>
                    <Title>Drilldown dos Dados Brutos (Raw)</Title>
                    <Text>Explore todas as medições detalhadamente. Exibindo {tableData.length} registros.</Text>
                  </div>
                  <TextInput 
                    icon={RiSearchLine} 
                    placeholder="Filtrar tabela (ex: repo, api)..." 
                    className="max-w-xs"
                    value={tableSearch}
                    onValueChange={setTableSearch}
                  />
                </div>
                <div className="overflow-x-auto">
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableHeaderCell>ID Original</TableHeaderCell>
                        <TableHeaderCell>
                          <div className="cursor-pointer flex items-center mb-2 hover:text-gray-900" onClick={() => requestSort('repo')}>
                            Repositório <SortIcon columnKey="repo" />
                          </div>
                          <TextInput 
                            placeholder="Buscar repo..." 
                            value={colFilters.repo} 
                            onValueChange={(v) => setColFilters({...colFilters, repo: v})}
                          />
                        </TableHeaderCell>
                        <TableHeaderCell>
                          <div className="cursor-pointer flex items-center mb-2 hover:text-gray-900" onClick={() => requestSort('api_type')}>
                            Padrão Arquitetural <SortIcon columnKey="api_type" />
                          </div>
                          <Select value={colFilters.api_type} onValueChange={(v) => setColFilters({...colFilters, api_type: v})}>
                            <SelectItem value="all">Todas</SelectItem>
                            <SelectItem value="graphql">GraphQL</SelectItem>
                            <SelectItem value="rest">REST</SelectItem>
                          </Select>
                        </TableHeaderCell>
                        <TableHeaderCell>
                          <div className="cursor-pointer flex items-center mb-2 hover:text-gray-900" onClick={() => requestSort('query_type')}>
                            Complexidade <SortIcon columnKey="query_type" />
                          </div>
                          <Select value={colFilters.query_type} onValueChange={(v) => setColFilters({...colFilters, query_type: v})}>
                            <SelectItem value="all">Todas</SelectItem>
                            <SelectItem value="simple">Simples</SelectItem>
                            <SelectItem value="medium">Média</SelectItem>
                            <SelectItem value="complex">Complexa</SelectItem>
                          </Select>
                        </TableHeaderCell>
                        <TableHeaderCell className="text-right align-top">
                          <div className="cursor-pointer flex items-center justify-end hover:text-gray-900" onClick={() => requestSort('response_time_ms')}>
                            Latência (ms) <SortIcon columnKey="response_time_ms" />
                          </div>
                        </TableHeaderCell>
                        <TableHeaderCell className="text-right align-top">
                          <div className="cursor-pointer flex items-center justify-end hover:text-gray-900" onClick={() => requestSort('response_size_bytes')}>
                            Tamanho da Resposta <SortIcon columnKey="response_size_bytes" />
                          </div>
                        </TableHeaderCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {paginatedData.map((item, idx) => (
                        <TableRow key={idx}>
                          <TableCell className="text-xs text-gray-400">#{((tablePage - 1) * itemsPerPage) + idx + 1}</TableCell>
                          <TableCell className="font-mono text-sm">{item.repo}</TableCell>
                          <TableCell>
                            <Badge color={item.api_type === "graphql" ? "emerald" : "rose"}>
                              {item.api_type.toUpperCase()}
                            </Badge>
                          </TableCell>
                          <TableCell>{item.query_type}</TableCell>
                          <TableCell className="text-right font-semibold">{parseFloat(item.response_time_ms || 0).toFixed(0)}</TableCell>
                          <TableCell className="text-right">{parseInt(item.response_size_bytes || 0).toLocaleString()}</TableCell>
                        </TableRow>
                      ))}
                      {paginatedData.length === 0 && (
                        <TableRow>
                          <TableCell colSpan={6} className="text-center py-4 text-gray-500">
                            Nenhum registro encontrado para essa busca.
                          </TableCell>
                        </TableRow>
                      )}
                    </TableBody>
                  </Table>
                </div>
                
                {/* Pagination Controls */}
                <div className="flex items-center justify-between mt-6 border-t pt-4">
                  <Text className="text-sm text-gray-500">
                    Página <b>{tablePage}</b> de <b>{totalTablePages}</b>
                  </Text>
                  <div className="flex gap-2">
                    <button 
                      onClick={() => setTablePage(p => Math.max(1, p - 1))}
                      disabled={tablePage === 1}
                      className="px-4 py-2 bg-white border border-gray-200 text-sm font-medium rounded shadow-sm hover:bg-gray-50 disabled:opacity-50"
                    >
                      Anterior
                    </button>
                    <button 
                      onClick={() => setTablePage(p => Math.min(totalTablePages, p + 1))}
                      disabled={tablePage === totalTablePages}
                      className="px-4 py-2 bg-white border border-gray-200 text-sm font-medium rounded shadow-sm hover:bg-gray-50 disabled:opacity-50"
                    >
                      Próxima
                    </button>
                  </div>
                </div>
              </Card>
            </TabPanel>

          </TabPanels>
        </TabGroup>
      </main>
    </div>
  );
}
