'use strict';

const $ = (id) => document.getElementById(id);
const fmt = (n) => new Intl.NumberFormat('pt-BR').format(Number(n ?? 0));
const pct = (n) => n == null ? '—' : `${Number(n).toFixed(1).replace('.', ',')}%`;
const days = (n) => n == null ? '—' : `${Number(n).toFixed(Number.isInteger(n) ? 0 : 1).replace('.', ',')} dias`;
const dateBR = (value) => {
  if (!value) return '—';
  const [y, m, d] = String(value).slice(0, 10).split('-');
  return y && m && d ? `${d}/${m}/${y}` : value;
};
const dateTimeBR = (value) => {
  if (!value) return '—';
  const s = String(value).replace('T', ' ');
  const [datePart, timePart = ''] = s.split(' ');
  return `${dateBR(datePart)}${timePart ? ` ${timePart.slice(0,5)}` : ''}`;
};
const esc = (value) => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

const state = {
  threshold: 30,
  offset: 0,
  limit: 200,
  recordset: 'all',
  data: null,
  loadingSeq: 0,
};

function params() {
  const p = new URLSearchParams({
    from: $('from').value,
    to: $('to').value,
    threshold: String(state.threshold),
    limit: String(state.limit),
    offset: String(state.offset),
    recordset: state.recordset,
  });
  const mapping = {macro:'macro', category:'category', status:'status', owner:'owner', q:'q'};
  for (const [id, key] of Object.entries(mapping)) {
    const value = $(id).value.trim();
    if (value) p.set(key, value);
  }
  return p;
}

async function loadDashboard({preserveOffset = false} = {}) {
  if (!preserveOffset) state.offset = 0;
  const seq = ++state.loadingSeq;
  $('fatal').classList.add('hidden');
  $('loading').classList.remove('hidden');
  try {
    const response = await fetch(`/api?${params().toString()}`, {cache: 'no-store'});
    const payload = await response.json().catch(() => ({ok:false,error:'Resposta inválida do backend.'}));
    if (!response.ok || !payload.ok) throw new Error(payload.error || `HTTP ${response.status}`);
    if (seq !== state.loadingSeq) return;
    state.data = payload;
    render(payload);
    $('dashboard').classList.remove('hidden');
  } catch (err) {
    if (seq !== state.loadingSeq) return;
    $('dashboard').classList.add('hidden');
    $('fatal').textContent = `Falha no backend: ${err.message}`;
    $('fatal').classList.remove('hidden');
  } finally {
    if (seq === state.loadingSeq) $('loading').classList.add('hidden');
  }
}

function fillSelect(id, values, allLabel) {
  const select = $(id);
  const current = select.value;
  select.innerHTML = `<option value="">${esc(allLabel)}</option>` + values.map(v => `<option value="${esc(v)}">${esc(v)}</option>`).join('');
  if (values.includes(current)) select.value = current;
}

function render(data) {
  const {meta, metrics, charts, records, options, indicator_coverage: coverage, warnings} = data;
  $('updatedAt').textContent = dateTimeBR(meta.source_updated_at);
  $('baseCount').textContent = `${fmt(meta.source_rows)} protocolos · 2025+`;

  fillSelect('macro', options.macroprocesses, 'Todos');
  fillSelect('category', options.categories, 'Todas');
  fillSelect('status', options.statuses, 'Todos');
  fillSelect('owner', options.owners, 'Todos');

  $('kReceived').textContent = fmt(metrics.received);
  $('kConcluded').textContent = fmt(metrics.concluded);
  $('kStock').textContent = fmt(metrics.stock);
  $('kMedian').textContent = days(metrics.turnaround.median_days);
  $('kTurnaroundSub').textContent = metrics.turnaround.eligible ? `${fmt(metrics.turnaround.eligible)} encerramentos elegíveis` : 'sem encerramentos elegíveis';
  $('kStoppedLabel').textContent = `Parados > ${metrics.stopped.threshold_days} dias`;
  $('kStopped').textContent = pct(metrics.stopped.percent);
  $('kStoppedSub').textContent = `${fmt(metrics.stopped.count)} de ${fmt(metrics.stopped.eligible_stock)} pendentes elegíveis`;
  $('balance').textContent = `${metrics.period_balance > 0 ? '+' : ''}${fmt(metrics.period_balance)}`;
  $('completionRate').textContent = pct(metrics.completion_rate);
  $('meanDays').textContent = days(metrics.turnaround.mean_days);
  $('p90Days').textContent = days(metrics.turnaround.p90_days);

  drawFlow(charts.flow);
  renderBars('categoryBars', charts.categories, (name) => { $('category').value = name; state.recordset='stock'; loadDashboard(); });
  renderBars('agingBars', charts.aging);
  renderBars('ownerBars', charts.owners, (name) => { $('owner').value = name; state.recordset='stock'; loadDashboard(); });
  renderBars('statusBars', charts.statuses, (name) => { $('status').value = name; state.recordset='stock'; loadDashboard(); });
  renderRecords(records);
  renderCoverage(coverage);
  $('warnings').innerHTML = warnings.map(x => `<li>${esc(x)}</li>`).join('');
  document.querySelectorAll('[data-recordset]').forEach(btn => btn.classList.toggle('selected', btn.dataset.recordset === state.recordset));
}

function renderBars(id, rows, onClick) {
  const host = $(id);
  const max = Math.max(1, ...rows.map(x => x.value));
  host.innerHTML = rows.map(x => {
    const width = Math.max(1, x.value / max * 100);
    const label = onClick ? `<button type="button" data-name="${esc(x.name)}" title="${esc(x.name)}">${esc(x.name)}</button>` : `<button type="button" disabled title="${esc(x.name)}">${esc(x.name)}</button>`;
    return `<div class="bar-row">${label}<div class="bar-track"><div class="bar-fill" style="width:${width}%"></div></div><b>${fmt(x.value)}</b></div>`;
  }).join('');
  if (onClick) host.querySelectorAll('[data-name]').forEach(btn => btn.addEventListener('click', () => onClick(btn.dataset.name)));
}

function renderRecords(records) {
  const names = {all:'Todos os processos do escopo',received:'Recebidos no período',concluded:'Concluídos no período',stock:'Estoque pendente atual',stopped:`Parados > ${state.threshold} dias`};
  $('tableTitle').textContent = names[records.recordset] || 'Explorador de processos';
  const start = records.total ? records.offset + 1 : 0;
  const end = Math.min(records.total, records.offset + records.items.length);
  $('tableMeta').textContent = `${fmt(records.total)} registros · exibindo ${fmt(start)}–${fmt(end)}`;
  $('recordsBody').innerHTML = records.items.map(r => {
    const d = r.days_without_movement;
    const cls = d == null ? '' : d > 60 ? 'critical' : d > 30 ? 'warning' : '';
    return `<tr>
      <td class="mono">${esc(r.protocol)}</td>
      <td>${esc(dateBR(r.opened))}</td>
      <td>${esc(dateTimeBR(r.last_movement))}</td>
      <td>${esc(r.category)}</td>
      <td>${esc(r.status)}</td>
      <td>${esc(r.owner)}</td>
      <td class="${cls}">${d == null ? '—' : `${fmt(d)} d`}</td>
    </tr>`;
  }).join('');
  $('prevPage').disabled = records.offset <= 0;
  $('nextPage').disabled = records.offset + records.items.length >= records.total;
}

function renderCoverage(rows) {
  $('coverage').innerHTML = rows.map(item => {
    const cls = item.status === 'DISPONÍVEL' ? 'ok' : item.status === 'PARCIAL' ? 'partial' : 'off';
    return `<article class="coverage-item"><div class="id">${esc(item.id)}</div><div><strong>${esc(item.name)}</strong><p>${esc(item.reason)}</p></div><span class="badge ${cls}">${esc(item.status)}</span></article>`;
  }).join('');
}

function drawFlow(rows) {
  const canvas = $('flowChart');
  const dpr = window.devicePixelRatio || 1;
  const width = canvas.clientWidth || 900;
  const height = 300;
  canvas.width = Math.round(width * dpr);
  canvas.height = Math.round(height * dpr);
  const ctx = canvas.getContext('2d');
  ctx.scale(dpr, dpr);
  ctx.clearRect(0, 0, width, height);
  const pad = {l:46,r:20,t:18,b:38};
  const innerW = width - pad.l - pad.r;
  const innerH = height - pad.t - pad.b;
  const max = Math.max(1, ...rows.flatMap(r => [r.received, r.concluded]));
  ctx.font = '10px Segoe UI';
  ctx.strokeStyle = '#e3ebf0';
  ctx.fillStyle = '#72889a';
  ctx.textAlign = 'right';
  for (let i=0;i<=4;i++) {
    const y = pad.t + innerH * i / 4;
    const value = Math.round(max * (4-i) / 4);
    ctx.beginPath();ctx.moveTo(pad.l,y);ctx.lineTo(width-pad.r,y);ctx.stroke();
    ctx.fillText(String(value), pad.l-7, y+3);
  }
  if (!rows.length) return;
  const slot = innerW / rows.length;
  const bw = Math.max(5, Math.min(22, slot * .28));
  ctx.textAlign = 'center';
  rows.forEach((r,i) => {
    const x = pad.l + i*slot + slot/2;
    const hr = r.received / max * innerH;
    const hc = r.concluded / max * innerH;
    ctx.fillStyle = '#1683bd'; ctx.fillRect(x-bw-2, pad.t+innerH-hr, bw, hr);
    ctx.fillStyle = '#16a66b'; ctx.fillRect(x+2, pad.t+innerH-hc, bw, hc);
    ctx.fillStyle = '#72889a'; ctx.fillText(r.month.slice(5,7)+'/'+r.month.slice(2,4), x, height-13);
  });
}

function bind() {
  ['from','to','macro','category','status','owner'].forEach(id => $(id).addEventListener('change', () => {state.recordset='all'; loadDashboard();}));
  let searchTimer;
  $('q').addEventListener('input', () => {clearTimeout(searchTimer); searchTimer=setTimeout(() => {state.recordset='all'; loadDashboard();}, 250);});
  $('reset').addEventListener('click', () => {
    $('from').value='2026-01-01'; $('to').value='2026-08-20';
    ['macro','category','status','owner','q'].forEach(id => $(id).value='');
    state.threshold=30; state.offset=0; state.recordset='all';
    document.querySelectorAll('[data-threshold]').forEach(b => b.classList.toggle('active', b.dataset.threshold==='30'));
    loadDashboard();
  });
  document.querySelectorAll('[data-threshold]').forEach(btn => btn.addEventListener('click', () => {
    state.threshold=Number(btn.dataset.threshold); state.recordset='all'; state.offset=0;
    document.querySelectorAll('[data-threshold]').forEach(b => b.classList.toggle('active', b===btn));
    loadDashboard();
  }));
  document.querySelectorAll('[data-recordset]').forEach(btn => btn.addEventListener('click', () => {
    state.recordset = state.recordset === btn.dataset.recordset ? 'all' : btn.dataset.recordset;
    state.offset=0; loadDashboard({preserveOffset:true});
  }));
  $('prevPage').addEventListener('click', () => {state.offset=Math.max(0,state.offset-state.limit);loadDashboard({preserveOffset:true});});
  $('nextPage').addEventListener('click', () => {state.offset+=state.limit;loadDashboard({preserveOffset:true});});
  window.addEventListener('resize', () => state.data && drawFlow(state.data.charts.flow));
}

bind();
loadDashboard();
