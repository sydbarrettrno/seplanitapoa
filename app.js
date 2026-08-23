'use strict';

const app = document.getElementById('app');

const COLORS = {
  blue: '#2563eb', teal: '#0f9f93', green: '#16a34a', orange: '#ea580c', red: '#dc2626',
  purple: '#7c3aed', violet: '#8b5cf6', cyan: '#0891b2', pink: '#db2777', indigo: '#4f46e5', amber: '#d97706'
};

const INDICATORS = [
  { id: 'KPI01', title: 'Processos Recebidos', color: COLORS.blue, icon: '↙', recordset: 'received' },
  { id: 'KPI02', title: 'Processos Concluídos', color: COLORS.green, icon: '✓', recordset: 'concluded' },
  { id: 'KPI03', title: 'Estoque Pendente', color: COLORS.orange, icon: '▤', recordset: 'stock' },
  { id: 'KPI04', title: 'Tempo Médio', color: COLORS.purple, icon: '⏱', recordset: 'concluded' },
  { id: 'KPI05', title: '% de Processos Parados > Período', color: COLORS.red, icon: '!', recordset: 'stopped' },
  { id: 'KPI06', title: '% de Processos Concluídos no Prazo', color: COLORS.teal, icon: '◷', recordset: 'all' },
  { id: 'KPI07', title: 'Diligências por Processo', color: COLORS.violet, icon: '↪', recordset: 'all' },
  { id: 'KPI08', title: 'Fiscalizações', color: COLORS.cyan, icon: '◎', recordset: 'all' },
  { id: 'KPI09', title: 'Denúncias Recebidas / Respondidas', color: COLORS.pink, icon: '✉', recordset: 'all' },
  { id: 'KPI10', title: 'Projetos Públicos por Etapa', color: COLORS.indigo, icon: '◆', recordset: 'all' },
  { id: 'KPI11', title: 'Pendências por Responsável / Setor', color: COLORS.amber, icon: '◫', recordset: 'stock' }
];

const PAGE_NAV = [
  ['overview', 'Visão Geral', '⌂'],
  ['protocolos', 'Protocolos', '▤'],
  ['analises', 'Análises', '◒'],
  ['indicadores', 'Indicadores', '▦'],
  ['relatorios', 'Relatórios', '▣'],
  ['unidades', 'Unidades', '◇'],
  ['responsaveis', 'Responsáveis', '◫'],
  ['configuracoes', 'Configurações', '⚙']
];

const state = {
  threshold: 30,
  offset: 0,
  limit: 100,
  recordset: 'all',
  data: null,
  loadingSeq: 0,
  lastRecordset: null
};

const fmt = (n) => new Intl.NumberFormat('pt-BR').format(Number(n ?? 0));
const one = (n) => Number(n ?? 0).toFixed(1).replace('.', ',');
const pct = (n) => n == null ? '—' : `${one(n)}%`;
const days = (n) => n == null ? '—' : `${one(n)} dias`;
const dateBR = (value) => {
  if (!value) return '—';
  const s = String(value).slice(0, 10);
  if (s.length < 10) return String(value);
  return `${s.slice(8,10)}/${s.slice(5,7)}/${s.slice(0,4)}`;
};
const dateTimeBR = (value) => {
  if (!value) return '—';
  const s = String(value).replace('T', ' ');
  const parts = s.split(' ');
  return `${dateBR(parts[0])}${parts[1] ? ` ${parts[1].slice(0,5)}` : ''}`;
};
const esc = (value) => String(value ?? '')
  .replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;')
  .replaceAll('"', '&quot;').replaceAll("'", '&#39;');

function route() {
  const raw = location.hash.replace('#/', '') || 'overview';
  const parts = raw.split('/');
  if (parts[0] === 'indicador' && parts[1]) return { type: 'indicator', id: parts[1].toUpperCase() };
  return { type: 'page', id: parts[0] || 'overview' };
}

function desiredRecordset() {
  const r = route();
  if (r.type === 'indicator') return INDICATORS.find(i => i.id === r.id)?.recordset || 'all';
  if (r.id === 'protocolos') return 'all';
  if (r.id === 'responsaveis' || r.id === 'unidades') return 'stock';
  return 'all';
}

function currentIndicator() {
  const r = route();
  return r.type === 'indicator' ? INDICATORS.find(i => i.id === r.id) : null;
}

function coverageMap(data) {
  const map = new Map();
  (data.indicator_coverage || []).forEach(item => map.set(item.id, item));
  return map;
}

function params() {
  const p = new URLSearchParams({
    from: document.getElementById('from')?.value || '2026-01-01',
    to: document.getElementById('to')?.value || '2026-08-20',
    threshold: String(state.threshold),
    limit: String(state.limit),
    offset: String(state.offset),
    recordset: state.recordset
  });
  const mapping = { macro: 'macro', category: 'category', status: 'status', owner: 'owner', q: 'q' };
  for (const [id, key] of Object.entries(mapping)) {
    const el = document.getElementById(id);
    const value = el ? el.value.trim() : '';
    if (value) p.set(key, value);
  }
  return p;
}

function indicatorValue(data, id) {
  const m = data.metrics;
  const cov = coverageMap(data).get(id);
  if (id === 'KPI01') return { value: fmt(m.received), unit: 'processos recebidos' };
  if (id === 'KPI02') return { value: fmt(m.concluded), unit: 'processos concluídos' };
  if (id === 'KPI03') return { value: fmt(m.stock), unit: 'processos pendentes' };
  if (id === 'KPI04') return { value: days(m.turnaround.mean_days), unit: `${fmt(m.turnaround.eligible)} encerramentos elegíveis` };
  if (id === 'KPI05') return { value: pct(m.stopped.percent), unit: `${fmt(m.stopped.count)} de ${fmt(m.stopped.eligible_stock)} pendentes` };
  if (id === 'KPI11') return { value: fmt(m.stock), unit: 'pendências mapeadas por gargalo operacional' };
  return { value: cov?.status || 'PENDENTE', unit: cov?.reason || 'Fonte ainda não integrada' };
}

function statusClass(status) {
  if (status === 'DISPONÍVEL') return 'ok';
  if (status === 'PARCIAL') return 'partial';
  if (status === 'TAXONOMIA PENDENTE') return 'warn';
  return 'off';
}

function shell() {
  app.innerHTML = `
    <div class="app-shell">
      <aside class="sidebar">
        <div class="brand"><div class="brand-mark">S</div><div><strong>SEPLAN</strong><small>Secretaria Municipal<br>de Planejamento</small></div></div>
        <nav class="nav" id="nav">
          ${PAGE_NAV.map(([id,label,icon]) => `<a href="#/${id}" data-page="${id}"><span class="nav-icon">${icon}</span><span>${label}</span></a>`).join('')}
        </nav>
        <div class="side-foot"><strong>Prefeitura de Itapoá</strong><br>Indicadores de gestão · base 2025+</div>
      </aside>
      <main class="main">
        <header class="topbar">
          <div class="title"><div class="eyebrow" id="eyebrow">GESTÃO OPERACIONAL</div><h1 id="pageTitle">Visão Geral</h1><div class="crumb" id="crumb">SEPLAN / Visão Geral</div></div>
          <div class="actions"><span class="updated">Atualizado em <strong id="updatedAt">—</strong></span><button id="refresh" class="icon-btn" title="Atualizar">↻</button><button id="print" class="icon-btn" title="Imprimir">⎙</button></div>
        </header>
        <section class="filterbar" id="filters">
          <div class="field"><label>Período inicial</label><input id="from" type="date" value="2026-01-01"></div>
          <div class="field"><label>Período final</label><input id="to" type="date" value="2026-08-20"></div>
          <div class="field"><label>Macroprocesso</label><select id="macro"><option value="">Todos</option></select></div>
          <div class="field"><label>Categoria</label><select id="category"><option value="">Todas</option></select></div>
          <div class="field"><label>Status</label><select id="status"><option value="">Todos</option></select></div>
          <div class="field"><label>Responsável / setor</label><select id="owner"><option value="">Todos</option></select></div>
          <div class="field search-field"><label>Busca</label><input id="q" type="search" placeholder="Protocolo"></div>
          <div class="filter-actions"><button id="reset" class="soft-btn">Limpar filtros</button></div>
        </section>
        <section id="loading" class="notice loading">Carregando indicadores…</section>
        <section id="fatal" class="notice error hidden"></section>
        <section id="content" class="hidden"></section>
      </main>
    </div>`;
  bindShell();
}

function fillSelect(id, values, allLabel) {
  const select = document.getElementById(id);
  if (!select) return;
  const current = select.value;
  select.innerHTML = `<option value="">${esc(allLabel)}</option>` + values.map(v => `<option value="${esc(v)}">${esc(v)}</option>`).join('');
  if (values.includes(current)) select.value = current;
}

async function loadDashboard({ preserveOffset = false } = {}) {
  if (!preserveOffset) state.offset = 0;
  const nextRecordset = desiredRecordset();
  if (state.recordset !== nextRecordset) {
    state.recordset = nextRecordset;
    state.offset = 0;
  }
  const seq = ++state.loadingSeq;
  document.getElementById('fatal').classList.add('hidden');
  document.getElementById('loading').classList.remove('hidden');
  try {
    const response = await fetch(`/api?${params().toString()}`, { cache: 'no-store' });
    const payload = await response.json().catch(() => ({ ok: false, error: 'Resposta inválida do backend.' }));
    if (!response.ok || !payload.ok) throw new Error(payload.error || `HTTP ${response.status}`);
    if (seq !== state.loadingSeq) return;
    state.data = payload;
    hydrateFilters(payload.options);
    render(payload);
    document.getElementById('content').classList.remove('hidden');
  } catch (err) {
    if (seq !== state.loadingSeq) return;
    document.getElementById('content').classList.add('hidden');
    const fatal = document.getElementById('fatal');
    fatal.textContent = `Falha ao carregar a base: ${err.message}`;
    fatal.classList.remove('hidden');
  } finally {
    if (seq === state.loadingSeq) document.getElementById('loading').classList.add('hidden');
  }
}

function hydrateFilters(options) {
  fillSelect('macro', options.macroprocesses || [], 'Todos');
  fillSelect('category', options.categories || [], 'Todas');
  fillSelect('status', options.statuses || [], 'Todos');
  fillSelect('owner', options.owners || [], 'Todos');
}

function updateHeader(data) {
  const r = route();
  const indicator = currentIndicator();
  const pageName = indicator?.title || PAGE_NAV.find(x => x[0] === r.id)?.[1] || 'Visão Geral';
  document.getElementById('pageTitle').textContent = indicator ? `Detalhamento — ${pageName}` : pageName;
  document.getElementById('eyebrow').textContent = indicator ? indicator.id : 'GESTÃO OPERACIONAL';
  document.getElementById('crumb').textContent = indicator ? `Indicadores / ${pageName}` : `SEPLAN / ${pageName}`;
  document.getElementById('updatedAt').textContent = dateTimeBR(data.meta.source_updated_at);
  document.querySelectorAll('[data-page]').forEach(a => a.classList.toggle('active', r.type === 'page' && a.dataset.page === r.id));
}

function render(data) {
  updateHeader(data);
  const r = route();
  if (r.type === 'indicator') return renderIndicatorPage(data, r.id);
  if (r.id === 'protocolos') return renderProtocols(data);
  if (r.id === 'analises') return renderAnalyses(data);
  if (r.id === 'indicadores') return renderIndicatorDirectory(data);
  if (r.id === 'relatorios') return renderReports(data);
  if (r.id === 'unidades') return renderUnits(data);
  if (r.id === 'responsaveis') return renderOwners(data);
  if (r.id === 'configuracoes') return renderSettings(data);
  return renderOverview(data);
}

function indicatorCards(data, compact = false) {
  const coverage = coverageMap(data);
  return `<div class="indicator-grid ${compact ? 'compact' : ''}">${INDICATORS.map(item => {
    const val = indicatorValue(data, item.id);
    const cov = coverage.get(item.id) || { status: 'PENDENTE', reason: '' };
    const available = ['DISPONÍVEL', 'PARCIAL'].includes(cov.status);
    return `<a class="indicator-card" href="#/indicador/${item.id}" style="--accent:${item.color}">
      <div class="indicator-top"><div class="indicator-icon">${item.icon}</div><span class="coverage-badge ${statusClass(cov.status)}">${esc(cov.status)}</span></div>
      <div class="indicator-label">${esc(item.title)}</div>
      <div class="indicator-value ${available ? '' : 'textual'}">${esc(val.value)}</div>
      <div class="indicator-unit">${esc(val.unit)}</div>
      <div class="indicator-go">Abrir detalhamento →</div>
    </a>`;
  }).join('')}</div>`;
}

function quickInsights(data) {
  const m = data.metrics;
  const topCat = data.charts.categories?.[0];
  const topOwner = data.charts.owners?.[0];
  const balance = m.received - m.concluded;
  const items = [
    `${fmt(m.received)} processos recebidos e ${fmt(m.concluded)} concluídos no período; saldo ${balance >= 0 ? '+' : ''}${fmt(balance)}.`,
    `O estoque atual possui ${fmt(m.stock)} processos pendentes.`,
    `${pct(m.stopped.percent)} do estoque elegível está sem movimentação há mais de ${m.stopped.threshold_days} dias.`,
    `O tempo médio de tramitação dos concluídos é ${days(m.turnaround.mean_days)}; mediana ${days(m.turnaround.median_days)}.`,
    topCat ? `${topCat.name} é a maior categoria do estoque atual, com ${fmt(topCat.value)} processos.` : '',
    topOwner ? `${topOwner.name} concentra ${fmt(topOwner.value)} pendências no recorte operacional.` : ''
  ].filter(Boolean);
  return `<div class="insights">${items.map((x,i) => `<div class="insight" style="--accent:${INDICATORS[i % INDICATORS.length].color}"><i></i><span>${esc(x)}</span></div>`).join('')}</div>`;
}

function renderOverview(data) {
  const content = document.getElementById('content');
  content.innerHTML = `
    <section class="hero-note"><div><strong>Painel executivo da SEPLAN</strong><div>Os 11 indicadores abaixo correspondem exatamente à solicitação da Chefia. Indicadores sem fonte suficiente são exibidos como pendentes, sem estimativas inventadas.</div></div><div class="base-pill">${fmt(data.meta.source_rows)} protocolos · 2025+</div></section>
    ${indicatorCards(data)}
    <div class="section-title"><div><h2>Leitura operacional</h2><p>Fluxo, estoque e gargalos derivados da base sanitizada.</p></div></div>
    <div class="grid-2">
      <article class="panel"><div class="panel-head"><div><span class="eyebrow">FLUXO MENSAL</span><h3>Recebidos × concluídos</h3></div><div class="legend"><span><i class="dot" style="background:${COLORS.blue}"></i>Recebidos</span><span><i class="dot" style="background:${COLORS.green}"></i>Concluídos</span></div></div><canvas id="flowChart" height="280"></canvas></article>
      <article class="panel"><h3>Leituras rápidas</h3>${quickInsights(data)}</article>
    </div>
    <div class="grid-3">
      ${barPanel('Estoque por categoria', data.charts.categories, COLORS.orange, 'category')}
      ${barPanel('Aging do estoque', data.charts.aging, COLORS.red)}
      ${barPanel('Pendências por responsável / setor', data.charts.owners, COLORS.amber, 'owner')}
    </div>`;
  drawFlow(data.charts.flow);
  bindBarFilters();
}

function renderIndicatorDirectory(data) {
  document.getElementById('content').innerHTML = `
    <section class="hero-note"><div><strong>Índice oficial de indicadores</strong><div>Clique em qualquer indicador para abrir a página individual. O status de cobertura vem da base e impede publicação de números sem fonte suficiente.</div></div></section>
    ${indicatorCards(data)}`;
}

function renderIndicatorPage(data, id) {
  const indicator = INDICATORS.find(x => x.id === id);
  if (!indicator) {
    document.getElementById('content').innerHTML = `<div class="notice error">Indicador não encontrado.</div>`;
    return;
  }
  const cov = coverageMap(data).get(id) || { status: 'PENDENTE', reason: 'Sem definição de cobertura.' };
  const value = indicatorValue(data, id);
  const available = cov.status === 'DISPONÍVEL' || cov.status === 'PARCIAL';
  const content = document.getElementById('content');
  let body = `<a class="back-link" href="#/indicadores">← Voltar aos indicadores</a>
    <section class="metric-banner" style="--accent:${indicator.color}"><div><span class="coverage-badge light">${esc(cov.status)}</span><h2>${esc(indicator.title)}</h2><div class="big">${esc(value.value)}</div><small>${esc(value.unit)}</small></div><div class="banner-side"><strong>Rastreabilidade do indicador</strong><br>${esc(cov.reason)}</div></section>`;

  if (!available) {
    body += unavailableIndicator(indicator, cov);
    content.innerHTML = body;
    return;
  }

  if (id === 'KPI01') body += receivedDetail(data);
  else if (id === 'KPI02') body += concludedDetail(data);
  else if (id === 'KPI03') body += stockDetail(data);
  else if (id === 'KPI04') body += turnaroundDetail(data);
  else if (id === 'KPI05') body += stoppedDetail(data);
  else if (id === 'KPI11') body += ownerDetail(data);
  content.innerHTML = body;
  if (['KPI01','KPI02'].includes(id)) drawFlow(data.charts.flow);
  bindBarFilters();
  bindThresholdButtons();
  bindPager();
}

function unavailableIndicator(indicator, cov) {
  const requirements = {
    KPI06: ['Tabela oficial de prazos por tipo de processo', 'Regras de suspensão/interrupção de prazo', 'Data inicial e data final computáveis por processo'],
    KPI07: ['Histórico completo de trâmites/eventos', 'Tipo de diligência por evento', 'Vínculo inequívoco evento → protocolo'],
    KPI08: ['Registro do ato de fiscalização efetivamente realizado', 'Data da vistoria/fiscalização', 'Resultado e situação do ato'],
    KPI09: ['Separação taxonômica entre denúncia e fiscalização', 'Data de recebimento da denúncia', 'Registro formal da resposta/conclusão'],
    KPI10: ['Carteira complementar de projetos públicos', 'Etapa atual padronizada', 'Datas de início/fim e situação do projeto']
  };
  const reqs = requirements[indicator.id] || ['Fonte complementar ainda não integrada'];
  return `<div class="grid-2">
    <article class="panel unavailable"><div class="unavailable-icon" style="--accent:${indicator.color}">${indicator.icon}</div><h3>Indicador ainda não publicável</h3><p>${esc(cov.reason)}</p><div class="callout"><strong>Regra aplicada:</strong> o dashboard não estima nem infere este indicador enquanto a fonte necessária não estiver integrada.</div></article>
    <article class="panel"><h3>Dados necessários para liberar</h3><ul class="requirements">${reqs.map(x => `<li>${esc(x)}</li>`).join('')}</ul><p class="muted">Assim que a fonte for integrada, esta mesma página passa a exibir número principal, gráficos, detalhamento e casos que compõem o indicador.</p></article>
  </div>`;
}

function receivedDetail(data) {
  return `<div class="kpis">${kpi('Recebidos', fmt(data.metrics.received), 'processos', COLORS.blue)}${kpi('Concluídos', fmt(data.metrics.concluded), 'no período', COLORS.green)}${kpi('Saldo', `${data.metrics.period_balance >= 0 ? '+' : ''}${fmt(data.metrics.period_balance)}`, 'recebidos − concluídos', COLORS.orange)}${kpi('Taxa de conclusão', pct(data.metrics.completion_rate), 'concluídos / recebidos', COLORS.teal)}</div>
    <div class="grid-2"><article class="panel"><h3>Evolução mensal</h3><canvas id="flowChart" height="280"></canvas></article><article class="panel"><h3>Leituras rápidas</h3>${quickInsights(data)}</article></div>
    ${recordsPanel(data, 'Processos recebidos no período')}`;
}

function concludedDetail(data) {
  return `<div class="kpis">${kpi('Concluídos', fmt(data.metrics.concluded), 'processos', COLORS.green)}${kpi('Taxa de conclusão', pct(data.metrics.completion_rate), 'concluídos / recebidos', COLORS.teal)}${kpi('Tempo médio', days(data.metrics.turnaround.mean_days), 'concluídos', COLORS.purple)}${kpi('P90', days(data.metrics.turnaround.p90_days), '90% concluem até', COLORS.indigo)}</div>
    <div class="grid-2"><article class="panel"><h3>Recebidos × concluídos</h3><canvas id="flowChart" height="280"></canvas></article><article class="panel"><h3>Leituras rápidas</h3>${quickInsights(data)}</article></div>
    ${recordsPanel(data, 'Processos concluídos no período')}`;
}

function stockDetail(data) {
  return `<div class="kpis">${kpi('Estoque atual', fmt(data.metrics.stock), 'pendentes', COLORS.orange)}${kpi(`Parados > ${data.metrics.stopped.threshold_days} dias`, fmt(data.metrics.stopped.count), 'processos', COLORS.red)}${kpi('% parados', pct(data.metrics.stopped.percent), 'do estoque elegível', COLORS.red)}${kpi('Maior gargalo', esc(data.charts.owners?.[0]?.name || '—'), `${fmt(data.charts.owners?.[0]?.value || 0)} processos`, COLORS.amber)}</div>
    <div class="grid-3">${barPanel('Estoque por categoria', data.charts.categories, COLORS.orange, 'category')}${barPanel('Aging do estoque', data.charts.aging, COLORS.red)}${barPanel('Estoque por status', data.charts.statuses, COLORS.purple, 'status')}</div>
    ${recordsPanel(data, 'Estoque pendente atual')}`;
}

function turnaroundDetail(data) {
  return `<div class="kpis">${kpi('Tempo médio', days(data.metrics.turnaround.mean_days), 'indicador principal', COLORS.purple)}${kpi('Mediana', days(data.metrics.turnaround.median_days), '50% concluem até', COLORS.violet)}${kpi('P90', days(data.metrics.turnaround.p90_days), '90% concluem até', COLORS.indigo)}${kpi('Amostra', fmt(data.metrics.turnaround.eligible), 'encerramentos elegíveis', COLORS.blue)}</div>
    <div class="grid-2"><article class="panel"><h3>Distribuição operacional disponível</h3>${barChart(data.charts.aging, COLORS.purple)}</article><article class="panel"><h3>Interpretação</h3><div class="insights"><div class="insight" style="--accent:${COLORS.purple}"><i></i><span>A média é sensível a casos muito longos; por isso a mediana e o P90 são exibidos como contexto.</span></div><div class="insight" style="--accent:${COLORS.indigo}"><i></i><span>O indicador principal solicitado é o tempo médio, calculado apenas para processos formalmente encerrados e elegíveis.</span></div></div></article></div>
    ${recordsPanel(data, 'Processos concluídos que compõem a análise')}`;
}

function thresholdControl() {
  return `<div class="threshold"><span>Considerar parado há mais de:</span>${[15,30,60,90,120].map(n => `<button type="button" data-threshold="${n}" class="${state.threshold === n ? 'active' : ''}">${n}d</button>`).join('')}</div>`;
}

function stoppedDetail(data) {
  return `${thresholdControl()}<div class="kpis">${kpi('% parados', pct(data.metrics.stopped.percent), 'indicador principal', COLORS.red)}${kpi('Quantidade', fmt(data.metrics.stopped.count), `> ${data.metrics.stopped.threshold_days} dias`, COLORS.red)}${kpi('Estoque elegível', fmt(data.metrics.stopped.eligible_stock), 'processos', COLORS.orange)}${kpi('Estoque total', fmt(data.metrics.stock), 'pendentes', COLORS.amber)}</div>
    <div class="grid-2"><article class="panel"><h3>Aging do estoque</h3>${barChart(data.charts.aging, COLORS.red)}</article><article class="panel"><h3>Gargalos</h3>${barChart(data.charts.owners, COLORS.amber, 'owner')}</article></div>
    ${recordsPanel(data, `Processos parados > ${data.metrics.stopped.threshold_days} dias`)}`;
}

function ownerDetail(data) {
  return `<div class="status-ribbon partial"><strong>COBERTURA PARCIAL</strong><span>O campo representa gargalo operacional derivado do status; não corresponde necessariamente ao responsável formal.</span></div>
    <div class="kpis">${kpi('Pendências mapeadas', fmt(data.metrics.stock), 'estoque atual', COLORS.amber)}${kpi('Maior gargalo', esc(data.charts.owners?.[0]?.name || '—'), `${fmt(data.charts.owners?.[0]?.value || 0)} processos`, COLORS.amber)}${kpi('Status predominante', esc(data.charts.statuses?.[0]?.name || '—'), `${fmt(data.charts.statuses?.[0]?.value || 0)} processos`, COLORS.purple)}</div>
    <div class="grid-2"><article class="panel"><h3>Pendências por responsável / setor</h3>${barChart(data.charts.owners, COLORS.amber, 'owner')}</article><article class="panel"><h3>Estoque por etapa operacional</h3>${barChart(data.charts.statuses, COLORS.purple, 'status')}</article></div>
    ${recordsPanel(data, 'Pendências que compõem o indicador')}`;
}

function renderProtocols(data) {
  document.getElementById('content').innerHTML = `<section class="hero-note"><div><strong>Explorador de protocolos</strong><div>Use os filtros acima para localizar processos e auditar os números apresentados nos indicadores.</div></div><div class="base-pill">${fmt(data.records.total)} registros no recorte</div></section>${recordsPanel(data, 'Protocolos')}`;
  bindPager();
}

function renderAnalyses(data) {
  document.getElementById('content').innerHTML = `<div class="grid-2"><article class="panel"><h3>Fluxo mensal</h3><canvas id="flowChart" height="280"></canvas></article><article class="panel"><h3>Leituras rápidas</h3>${quickInsights(data)}</article></div><div class="grid-3">${barPanel('Categorias', data.charts.categories, COLORS.blue, 'category')}${barPanel('Aging', data.charts.aging, COLORS.red)}${barPanel('Status', data.charts.statuses, COLORS.purple, 'status')}</div>`;
  drawFlow(data.charts.flow); bindBarFilters();
}

function renderReports(data) {
  document.getElementById('content').innerHTML = `<section class="metric-banner" style="--accent:${COLORS.indigo}"><div><h2>Relatório do recorte atual</h2><div class="big">${fmt(data.meta.scope_rows)}</div><small>registros no escopo da base</small></div><div class="banner-side">Use os filtros globais para definir o recorte e clique em “Imprimir” no topo para gerar PDF pelo navegador.</div></section>${indicatorCards(data, true)}<article class="panel"><h3>Notas de leitura e rastreabilidade</h3><ul class="requirements">${(data.warnings || []).map(x => `<li>${esc(x)}</li>`).join('')}</ul></article>`;
}

function renderUnits(data) {
  document.getElementById('content').innerHTML = `<section class="hero-note"><div><strong>Unidades / gargalos operacionais</strong><div>A base pública sanitizada não publica nomes pessoais; esta visão usa categorias operacionais disponíveis.</div></div></section><div class="grid-2"><article class="panel"><h3>Pendências por unidade operacional</h3>${barChart(data.charts.owners, COLORS.cyan, 'owner')}</article><article class="panel"><h3>Status do estoque</h3>${barChart(data.charts.statuses, COLORS.purple, 'status')}</article></div>`; bindBarFilters();
}

function renderOwners(data) {
  document.getElementById('content').innerHTML = `<div class="status-ribbon partial"><strong>ATENÇÃO À INTERPRETAÇÃO</strong><span>“Responsável / setor” representa o gargalo operacional disponível na base sanitizada.</span></div><div class="grid-2"><article class="panel"><h3>Pendências por responsável / setor</h3>${barChart(data.charts.owners, COLORS.amber, 'owner')}</article><article class="panel"><h3>Leituras rápidas</h3>${quickInsights(data)}</article></div>${recordsPanel(data, 'Processos pendentes')}`; bindBarFilters(); bindPager();
}

function renderSettings(data) {
  const coverage = coverageMap(data);
  document.getElementById('content').innerHTML = `<div class="settings"><article class="panel"><h3>Parâmetro de processo parado</h3><p class="muted">Define o período usado no KPI05.</p>${thresholdControl()}</article><article class="panel"><h3>Base de dados</h3><div class="detail-list"><div><span>Dataset</span><b>${esc(data.meta.dataset)}</b></div><div><span>Linhas</span><b>${fmt(data.meta.source_rows)}</b></div><div><span>Atualização</span><b>${dateTimeBR(data.meta.source_updated_at)}</b></div><div><span>Schema</span><b>v${esc(data.meta.schema_version)}</b></div></div></article></div><div class="section-title"><div><h2>Cobertura dos 11 indicadores</h2><p>Disponibilidade técnica da fonte.</p></div></div><div class="coverage-grid">${INDICATORS.map(i => { const c=coverage.get(i.id)||{}; return `<article class="coverage-item"><div class="coverage-id" style="--accent:${i.color}">${i.id}</div><div><strong>${esc(i.title)}</strong><p>${esc(c.reason || 'Sem informação')}</p></div><span class="coverage-badge ${statusClass(c.status)}">${esc(c.status || 'PENDENTE')}</span></article>`; }).join('')}</div>`;
  bindThresholdButtons();
}

function kpi(label, value, unit, color) {
  return `<article class="kpi" style="--accent:${color}"><span>${esc(label)}</span><strong>${value}</strong><small>${esc(unit)}</small></article>`;
}

function barPanel(title, rows, color, filterKey) {
  return `<article class="panel"><h3>${esc(title)}</h3>${barChart(rows, color, filterKey)}</article>`;
}

function barChart(rows = [], color, filterKey) {
  const max = Math.max(1, ...rows.map(x => Number(x.value || 0)));
  return `<div class="bars">${rows.map(x => `<div class="bar-row ${filterKey ? 'clickable' : ''}" ${filterKey ? `data-filter-key="${filterKey}" data-filter-value="${esc(x.name)}"` : ''} style="--accent:${color}"><span class="bar-name" title="${esc(x.name)}">${esc(x.name)}</span><div class="bar-track"><div class="bar-fill" style="width:${Math.max(1, Number(x.value || 0) / max * 100)}%"></div></div><b>${fmt(x.value)}</b></div>`).join('')}</div>`;
}

function recordsPanel(data, title) {
  const records = data.records;
  const start = records.total ? records.offset + 1 : 0;
  const end = Math.min(records.total, records.offset + records.items.length);
  return `<article class="panel table-panel"><div class="table-toolbar"><div><span class="eyebrow">DRILL-DOWN AUDITÁVEL</span><h3>${esc(title)}</h3><p>${fmt(records.total)} registros · exibindo ${fmt(start)}–${fmt(end)}</p></div><div class="pager"><button id="prevPage" ${records.offset <= 0 ? 'disabled' : ''}>← Anterior</button><button id="nextPage" ${records.offset + records.items.length >= records.total ? 'disabled' : ''}>Próxima →</button></div></div><div class="table-wrap"><table><thead><tr><th>Protocolo</th><th>Abertura</th><th>Último trâmite</th><th>Categoria</th><th>Status</th><th>Responsável / setor</th><th>Sem mov.</th></tr></thead><tbody>${records.items.map(r => `<tr><td class="protocol">${esc(r.protocol)}</td><td>${esc(dateBR(r.opened))}</td><td>${esc(dateTimeBR(r.last_movement))}</td><td>${esc(r.category)}</td><td><span class="table-badge">${esc(r.status)}</span></td><td>${esc(r.owner)}</td><td class="${r.days_without_movement > 60 ? 'critical' : r.days_without_movement > 30 ? 'warning' : ''}">${r.days_without_movement == null ? '—' : `${fmt(r.days_without_movement)} d`}</td></tr>`).join('')}</tbody></table></div></article>`;
}

function drawFlow(rows = []) {
  const canvas = document.getElementById('flowChart');
  if (!canvas) return;
  const dpr = window.devicePixelRatio || 1;
  const width = canvas.clientWidth || 900;
  const height = 280;
  canvas.width = Math.round(width * dpr);
  canvas.height = Math.round(height * dpr);
  const ctx = canvas.getContext('2d');
  ctx.scale(dpr, dpr);
  ctx.clearRect(0, 0, width, height);
  const pad = { l: 44, r: 16, t: 20, b: 38 };
  const innerW = width - pad.l - pad.r;
  const innerH = height - pad.t - pad.b;
  const max = Math.max(1, ...rows.flatMap(r => [r.received, r.concluded]));
  ctx.font = '10px Segoe UI';
  ctx.strokeStyle = '#e4ebf2';
  ctx.fillStyle = '#6b7d90';
  ctx.textAlign = 'right';
  for (let i = 0; i <= 4; i++) {
    const y = pad.t + innerH * i / 4;
    const v = Math.round(max * (4 - i) / 4);
    ctx.beginPath(); ctx.moveTo(pad.l, y); ctx.lineTo(width - pad.r, y); ctx.stroke();
    ctx.fillText(String(v), pad.l - 7, y + 3);
  }
  if (!rows.length) return;
  const slot = innerW / rows.length;
  const bw = Math.max(6, Math.min(24, slot * .28));
  ctx.textAlign = 'center';
  rows.forEach((r, i) => {
    const x = pad.l + i * slot + slot / 2;
    const hr = r.received / max * innerH;
    const hc = r.concluded / max * innerH;
    ctx.fillStyle = COLORS.blue; ctx.fillRect(x - bw - 2, pad.t + innerH - hr, bw, hr);
    ctx.fillStyle = COLORS.green; ctx.fillRect(x + 2, pad.t + innerH - hc, bw, hc);
    ctx.fillStyle = '#64748b'; ctx.fillText(`${r.month.slice(5,7)}/${r.month.slice(2,4)}`, x, height - 14);
  });
}

function bindBarFilters() {
  document.querySelectorAll('[data-filter-key]').forEach(row => row.addEventListener('click', () => {
    const el = document.getElementById(row.dataset.filterKey);
    if (el) {
      el.value = row.dataset.filterValue;
      loadDashboard();
    }
  }));
}

function bindPager() {
  const prev = document.getElementById('prevPage');
  const next = document.getElementById('nextPage');
  if (prev) prev.addEventListener('click', () => { state.offset = Math.max(0, state.offset - state.limit); loadDashboard({ preserveOffset: true }); });
  if (next) next.addEventListener('click', () => { state.offset += state.limit; loadDashboard({ preserveOffset: true }); });
}

function bindThresholdButtons() {
  document.querySelectorAll('[data-threshold]').forEach(btn => btn.addEventListener('click', () => {
    state.threshold = Number(btn.dataset.threshold);
    state.offset = 0;
    loadDashboard();
  }));
}

function bindShell() {
  ['from','to','macro','category','status','owner'].forEach(id => document.getElementById(id).addEventListener('change', () => loadDashboard()));
  let searchTimer;
  document.getElementById('q').addEventListener('input', () => {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => loadDashboard(), 250);
  });
  document.getElementById('reset').addEventListener('click', () => {
    document.getElementById('from').value = '2026-01-01';
    document.getElementById('to').value = '2026-08-20';
    ['macro','category','status','owner','q'].forEach(id => document.getElementById(id).value = '');
    state.threshold = 30; state.offset = 0;
    loadDashboard();
  });
  document.getElementById('refresh').addEventListener('click', () => loadDashboard({ preserveOffset: true }));
  document.getElementById('print').addEventListener('click', () => window.print());
  window.addEventListener('hashchange', () => { state.offset = 0; loadDashboard(); });
  window.addEventListener('resize', () => state.data && drawFlow(state.data.charts.flow));
}

shell();
loadDashboard();
