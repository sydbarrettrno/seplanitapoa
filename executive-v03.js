(() => {
  function executiveSummary(data) {
    const m = data.metrics;
    const topOwner = data.charts.owners?.[0];
    const topAging = data.charts.aging?.reduce((best, item) => !best || item.value > best.value ? item : best, null);
    const balance = Number(m.period_balance || 0);
    const stopped = Number(m.stopped?.percent || 0);

    const tone = balance > 0 || stopped >= 50 ? 'attention' : 'good';
    const headline = balance > 0
      ? `A demanda superou a produção formal em ${fmt(balance)} processos no período.`
      : `A produção formal absorveu a demanda do período, com saldo ${fmt(balance)}.`;

    const bullets = [
      `${pct(m.stopped?.percent)} do estoque operacional está sem movimentação há mais de ${m.stopped?.threshold_days} dias.`,
      topAging ? `A maior faixa de aging é ${topAging.name}, com ${fmt(topAging.value)} processos.` : '',
      topOwner ? `Maior concentração operacional: ${topOwner.name}, com ${fmt(topOwner.value)} processos.` : '',
      `Tempo de tramitação dos concluídos: média ${days(m.turnaround?.mean_days)}, mediana ${days(m.turnaround?.median_days)} e P90 ${days(m.turnaround?.p90_days)}.`
    ].filter(Boolean);

    return `<article class="exec-diagnosis ${tone}">
      <div class="exec-diagnosis-head"><span>LEITURA EXECUTIVA</span><strong>${esc(headline)}</strong></div>
      <div class="exec-diagnosis-list">${bullets.map(x => `<div><i></i><span>${esc(x)}</span></div>`).join('')}</div>
    </article>`;
  }

  function executiveCoverage(data) {
    const coverage = coverageMap(data);
    const ready = INDICATORS.filter(i => ['DISPONÍVEL', 'PARCIAL'].includes(coverage.get(i.id)?.status));
    const pending = INDICATORS.filter(i => !['DISPONÍVEL', 'PARCIAL'].includes(coverage.get(i.id)?.status));

    return `<div class="exec-coverage-grid">
      <article class="panel exec-ready">
        <div class="panel-head"><div><span class="eyebrow">INDICADORES OPERACIONAIS</span><h3>Dados disponíveis para decisão</h3></div><span class="exec-count ok">${ready.length}</span></div>
        <div class="exec-link-grid">${ready.map(item => {
          const val = indicatorValue(data, item.id);
          return `<a href="#/indicador/${item.id}" style="--accent:${item.color}"><span>${item.id}</span><strong>${esc(item.title)}</strong><b>${esc(val.value)}</b></a>`;
        }).join('')}</div>
      </article>
      <article class="panel exec-pending">
        <div class="panel-head"><div><span class="eyebrow">COBERTURA DE DADOS</span><h3>Aguardando fonte complementar</h3></div><span class="exec-count">${pending.length}</span></div>
        <div class="exec-pending-list">${pending.map(item => {
          const cov = coverage.get(item.id) || {status:'PENDENTE', reason:'Fonte não integrada'};
          return `<a href="#/indicador/${item.id}"><span>${item.id}</span><div><strong>${esc(item.title)}</strong><small>${esc(cov.status)}</small></div></a>`;
        }).join('')}</div>
        <p class="exec-footnote">Sem estimativas: indicadores sem fonte suficiente permanecem explicitamente não publicados.</p>
      </article>
    </div>`;
  }

  renderOverview = function renderExecutiveOverview(data) {
    const m = data.metrics;
    const sourceDate = dateBR(data.meta.source_updated_at);
    const stockNote = 'Exclui protocolos operacionalmente concluídos e apenas aguardando retirada.';
    const content = document.getElementById('content');

    content.innerHTML = `
      <section class="exec-hero">
        <div>
          <span class="exec-kicker">SEPLAN · GESTÃO OPERACIONAL</span>
          <h2>Situação atual em uma tela</h2>
          <p>Entrada, produção, estoque, tempo e gargalos. Base oficial atualizada em ${esc(sourceDate)}.</p>
        </div>
        <div class="exec-base"><strong>${fmt(data.meta.source_rows)}</strong><span>protocolos 2025+</span></div>
      </section>

      <section class="exec-scoreboard">
        ${kpi('Recebidos no período', fmt(m.received), 'entrada', COLORS.blue)}
        ${kpi('Concluídos formais', fmt(m.concluded), 'produção com DataEncerramento', COLORS.green)}
        ${kpi('Saldo entrada − saída', `${m.period_balance >= 0 ? '+' : ''}${fmt(m.period_balance)}`, 'pressão sobre a fila', m.period_balance > 0 ? COLORS.red : COLORS.green)}
        ${kpi('Estoque operacional', fmt(m.stock), 'pendências atuais', COLORS.orange)}
        ${kpi(`Parados > ${m.stopped.threshold_days} dias`, pct(m.stopped.percent), `${fmt(m.stopped.count)} processos`, COLORS.red)}
        ${kpi('Tempo médio', days(m.turnaround.mean_days), `mediana ${days(m.turnaround.median_days)} · P90 ${days(m.turnaround.p90_days)}`, COLORS.purple)}
      </section>
      <div class="exec-stock-note">${esc(stockNote)}</div>

      ${executiveSummary(data)}

      <div class="section-title"><div><h2>Fluxo e envelhecimento</h2><p>Onde a demanda está pressionando a operação.</p></div><a class="exec-all-link" href="#/indicadores">Ver os 11 indicadores →</a></div>
      <div class="grid-2 exec-flow-row">
        <article class="panel"><div class="panel-head"><div><span class="eyebrow">FLUXO MENSAL</span><h3>Recebidos × concluídos</h3></div><div class="legend"><span><i class="dot" style="background:${COLORS.blue}"></i>Recebidos</span><span><i class="dot" style="background:${COLORS.green}"></i>Concluídos</span></div></div><canvas id="flowChart" height="280"></canvas></article>
        <article class="panel"><span class="eyebrow">AGING</span><h3>Idade do estoque</h3>${barChart(data.charts.aging, COLORS.red)}</article>
      </div>

      <div class="grid-2 exec-bottlenecks">
        ${barPanel('Estoque por status operacional', data.charts.statuses, COLORS.purple, 'status')}
        ${barPanel('Pendências por gargalo operacional', data.charts.owners, COLORS.amber, 'owner')}
      </div>

      <div class="section-title"><div><h2>Cobertura dos indicadores</h2><p>O que pode ser usado agora e o que ainda depende de fonte complementar.</p></div></div>
      ${executiveCoverage(data)}`;

    drawFlow(data.charts.flow);
    bindBarFilters();
  };
})();
