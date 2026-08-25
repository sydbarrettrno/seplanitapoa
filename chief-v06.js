(() => {
  const num = (v) => fmt(Number(v || 0));
  const dec = (v) => v == null ? '—' : one(v);

  const card = (n, title, value, note, available = true) => `
    <article class="chief-kpi ${available ? '' : 'chief-kpi-off'}">
      <div class="chief-kpi-id">${n}</div>
      <div class="chief-kpi-title">${esc(title)}</div>
      <div class="chief-kpi-value">${esc(value)}</div>
      <div class="chief-kpi-note">${esc(note)}</div>
    </article>`;

  const bars = (title, rows, limit = 10) => {
    const data = (rows || []).slice(0, limit);
    const max = Math.max(1, ...data.map(x => Number(x.value || 0)));
    return `<article class="panel chief-panel">
      <h3>${esc(title)}</h3>
      <div class="chief-bars">${data.map(x => {
        const value = Number(x.value || 0);
        const width = Math.max(2, value / max * 100);
        return `<div class="chief-bar-row" data-filter-value="${esc(x.name)}">
          <div class="chief-bar-label">${esc(x.name)}</div>
          <div class="chief-bar-track"><div class="chief-bar-fill" style="width:${width}%"></div><b>${num(value)}</b></div>
        </div>`;
      }).join('')}</div>
    </article>`;
  };

  const compareChart = (cmp) => {
    const cur = cmp.current || {};
    const prev = cmp.previous || {};
    const rows = [
      {name:'Recebidos', y2025:Number(prev.received || 0), y2026:Number(cur.received || 0)},
      {name:'Concluídos da demanda corrente', y2025:Number(prev.cohort_concluded_formal || 0), y2026:Number(cur.cohort_concluded_formal || 0)}
    ];
    const max = Math.max(1, ...rows.flatMap(r => [r.y2025, r.y2026]));
    return `<article class="panel chief-panel">
      <div class="chief-panel-head"><h3>2025 × 2026 — mesmo período</h3><div class="chief-legend"><span><i class="c25"></i>2025</span><span><i class="c26"></i>2026</span></div></div>
      <div class="chief-compare">${rows.map(r => `
        <div class="chief-compare-row">
          <div class="chief-compare-label">${esc(r.name)}</div>
          <div class="chief-compare-bars">
            <div class="chief-compare-line"><span>2025</span><div class="chief-compare-track"><div class="chief-compare-fill y25" style="width:${Math.max(2,r.y2025/max*100)}%"></div><b>${num(r.y2025)}</b></div></div>
            <div class="chief-compare-line"><span>2026</span><div class="chief-compare-track"><div class="chief-compare-fill y26" style="width:${Math.max(2,r.y2026/max*100)}%"></div><b>${num(r.y2026)}</b></div></div>
          </div>
        </div>`).join('')}</div>
    </article>`;
  };

  const flowChart = (flow) => {
    const data = flow || [];
    const max = Math.max(1, ...data.flatMap(x => [Number(x.received || 0), Number(x.concluded || 0)]));
    const month = (s) => {
      const [y,m] = String(s).split('-');
      return `${m}/${String(y).slice(2)}`;
    };
    return `<article class="panel chief-panel chief-flow-panel">
      <div class="chief-panel-head"><h3>Entrada × saída mensal</h3><div class="chief-legend"><span><i class="rec"></i>Recebidos</span><span><i class="con"></i>Concluídos</span></div></div>
      <div class="chief-flow">${data.map(x => {
        const a=Number(x.received||0), b=Number(x.concluded||0);
        return `<div class="chief-flow-group">
          <div class="chief-columns">
            <div class="chief-col-wrap"><b>${num(a)}</b><div class="chief-col received" style="height:${Math.max(4,a/max*170)}px"></div></div>
            <div class="chief-col-wrap"><b>${num(b)}</b><div class="chief-col concluded" style="height:${Math.max(4,b/max*170)}px"></div></div>
          </div>
          <span>${esc(month(x.month))}</span>
        </div>`;
      }).join('')}</div>
    </article>`;
  };

  renderOverview = function renderChiefOverview(data) {
    const m = data.metrics || {};
    const mg = data.management || {};
    const cmp = mg.comparison || {};
    const prev = cmp.previous || {};
    const complaints = mg.complaints || {};
    const t = m.turnaround || {};
    const change = cmp.received_change_percent == null ? 'sem comparação' : `${cmp.received_change_percent > 0 ? '+' : ''}${dec(cmp.received_change_percent)}% vs 2025`;

    document.getElementById('content').innerHTML = `
      <section class="chief-head">
        <div><span>SEPLAN · INDICADORES SOLICITADOS</span><h2>Resultados da Secretaria de Planejamento</h2></div>
        <div class="chief-period">${dateBR(data.meta.period?.from)} a ${dateBR(data.meta.period?.to)}</div>
      </section>

      <section class="chief-kpi-grid">
        ${card('01','Processos recebidos',num(m.received),`${num(prev.received || 0)} em 2025 · ${change}`)}
        ${card('02','Processos concluídos',num(m.concluded),`${num(m.concluded_formal)} formais · conclusão operacional no período`)}
        ${card('03','Estoque pendente',num(m.stock),`${num(m.internal_queue)} fila interna · ${num(m.external_wait)} espera externa · ${num(m.suspended)} suspensos`)}
        ${card('04','Tempo de tramitação',`${dec(t.mean_days)} dias`,`mediana ${dec(t.median_days)} · P90 ${dec(t.p90_days)} dias`)}
        ${card('05',`Parados > ${num(m.stopped?.threshold_days)} dias`,pct(m.stopped?.percent),`${num(m.stopped?.count)} de ${num(m.stopped?.eligible_stock)} na fila interna`)}
        ${card('06','Concluídos dentro do prazo','—','Sem fonte oficial de prazos e suspensões',false)}
        ${card('07','Diligências por processo','—','Sem histórico completo de eventos',false)}
        ${card('08','Fiscalizações realizadas','—','A base identifica protocolos de fiscalização, não comprova o ato realizado',false)}
        ${card('09','Denúncias recebidas / respondidas',`${num(complaints.received)} / ${num(complaints.responded_operational)}`,`${num(complaints.stock)} pendentes`)}
        ${card('10','Projetos públicos por etapa','—','Carteira de projetos não integrada',false)}
        ${card('11','Pendências por responsável / setor',num(m.stock),`Interno ${num(m.internal_queue)} · Externo ${num(m.external_wait)} · Suspenso ${num(m.suspended)}`)}
      </section>

      <section class="chief-grid-2">
        ${compareChart(cmp)}
        ${flowChart(data.charts?.flow)}
      </section>

      <section class="chief-grid-2">
        ${bars('Estoque por status', data.charts?.statuses, 8)}
        ${bars('Pendências por responsável / setor', data.charts?.owners, 8)}
      </section>

      <section class="chief-grid-2">
        ${bars('Fila interna — dias sem movimentação', data.charts?.internal_aging, 8)}
        ${bars('Fila interna por categoria', data.charts?.internal_categories, 10)}
      </section>`;
  };
})();
