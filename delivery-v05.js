(() => {
  const delta = (value, suffix = '%') => {
    if (value == null) return 'sem comparação';
    const sign = value > 0 ? '+' : '';
    return `${sign}${one(value)}${suffix}`;
  };

  const fact = (label, value, note, tone='neutral') => `
    <article class="mgmt-signal ${tone}">
      <span>${esc(label)}</span>
      <strong>${esc(value)}</strong>
      <small>${esc(note)}</small>
    </article>`;

  renderOverview = function renderDeliveryOverview(data) {
    const m = data.metrics;
    const mg = data.management || {};
    const cmp = mg.comparison || {};
    const cur = cmp.current || {};
    const prev = cmp.previous || {};
    const pos = mg.position || {};
    const ina = mg.inactivity || {};
    const tm = mg.time || {};
    const dq = mg.data_quality || {};
    const sourceDate = dateBR(data.meta.source_updated_at);

    const receivedNote = prev.received
      ? `${fmt(prev.received)} no mesmo período de 2025 · ${delta(cmp.received_change_percent)}`
      : 'sem base comparável';

    const prodNote = `${fmt(cur.passive_absorbed || 0)} do passivo absorvido no período`;

    document.getElementById('content').innerHTML = `
      <section class="mgmt-hero">
        <div>
          <span>SEPLAN · PAINEL EXECUTIVO</span>
          <h2>Demanda, produção e fila atual</h2>
          <p>Leitura factual da base reconciliada. Atualização: ${esc(sourceDate)}. Sem metas ou SLA inventados.</p>
        </div>
        <div class="mgmt-hero-side"><b>${fmt(data.meta.source_rows)}</b><small>protocolos 2025+</small></div>
      </section>

      <section class="mgmt-signals">
        ${fact('Demanda recebida', fmt(m.received), receivedNote, 'neutral')}
        ${fact('Produção operacional', fmt(m.concluded), prodNote, 'good')}
        ${fact('Estoque atual', fmt(m.stock), 'posição atual da base', 'attention')}
        ${fact('Fila interna SEPLAN', fmt(m.internal_queue), `${pct(pos.internal_percent)} do estoque`, 'critical')}
        ${fact('Aguardando ação externa', fmt(m.external_wait), `${pct(pos.external_percent)} do estoque`, 'attention')}
        ${fact('Tempo típico / P90', `${one(tm.operational?.median_days)} d / ${one(tm.operational?.p90_days)} d`, `${fmt(tm.operational?.eligible || 0)} conclusões operacionais`, 'neutral')}
      </section>

      <section class="panel mgmt-agenda">
        <table>
          <thead><tr><th>Leitura</th><th>Atual</th><th>Referência</th><th>Interpretação segura</th></tr></thead>
          <tbody>
            <tr><td>Demanda</td><td><b>${fmt(m.received)}</b></td><td>${fmt(prev.received || 0)} em 2025</td><td>${delta(cmp.received_change_percent)} no mesmo período</td></tr>
            <tr><td>Conclusão formal da demanda corrente</td><td><b>${fmt(cur.cohort_concluded_formal || 0)}</b></td><td>${fmt(prev.cohort_concluded_formal || 0)} em 2025</td><td>${delta(cmp.cohort_formal_change_percent)} no mesmo período</td></tr>
            <tr><td>Produção operacional total</td><td><b>${fmt(cur.concluded_total || 0)}</b></td><td>inclui passivo</td><td>${fmt(cur.passive_absorbed || 0)} processos abertos antes do período</td></tr>
            <tr><td>Fila interna sem movimento &gt; ${fmt(ina.threshold_days || m.stopped.threshold_days)} dias</td><td><b>${fmt(ina.internal_stopped || m.stopped.count)}</b></td><td>${fmt(ina.internal_total || m.internal_queue)} na fila interna</td><td>${pct(ina.internal_stopped_percent || m.stopped.percent)} da fila interna</td></tr>
          </tbody>
        </table>
      </section>

      <div class="section-title"><div><h2>Fluxo e composição da fila</h2><p>O gráfico temporal compara entradas e conclusões operacionais. O aging abaixo usa somente a fila interna para não atribuir à SEPLAN espera de requerente, RT ou terceiro.</p></div></div>
      <div class="grid-2 exec-flow-row">
        <article class="panel"><div class="panel-head"><div><span class="eyebrow">FLUXO MENSAL</span><h3>Recebidos × concluídos operacionais</h3></div></div><canvas id="flowChart" height="280"></canvas></article>
        <article class="panel"><span class="eyebrow">FILA INTERNA</span><h3>Dias sem movimentação</h3>${barChart(data.charts.internal_aging, COLORS.red)}</article>
      </div>

      <div class="grid-2">
        ${barPanel('Fila interna por categoria', data.charts.internal_categories, COLORS.orange, 'category')}
        ${barPanel('Estoque por responsável atual', data.charts.owners, COLORS.amber, 'owner')}
      </div>

      <div class="section-title"><div><h2>Qualidade do dado</h2><p>A conclusão operacional e o encerramento formal permanecem separados.</p></div></div>
      <section class="panel">
        <div class="detail-list">
          <div><span>Encerrados operacionalmente sem DataEncerramento formal</span><b>${fmt(dq.operational_closed_without_formal_date || 0)}</b></div>
          <div><span>Conclusões formais no período</span><b>${fmt(m.concluded_formal)}</b></div>
          <div><span>Conclusões operacionais no período</span><b>${fmt(m.concluded)}</b></div>
          <div><span>Suspensos</span><b>${fmt(m.suspended)}</b></div>
        </div>
      </section>

      <div class="mgmt-note"><strong>Regra de leitura:</strong> volume recebido é demanda; produção é saída; estoque é posição atual; processos aguardando terceiros não compõem a fila interna SEPLAN.</div>`;

    drawFlow(data.charts.flow);
    bindBarFilters();
  };
})();
