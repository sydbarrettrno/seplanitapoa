(() => {
  const signal = (label, value, note, tone='critical') => `
    <article class="mgmt-signal ${tone}">
      <span>${esc(label)}</span><strong>${esc(value)}</strong><small>${esc(note)}</small>
    </article>`;

  const issue = (tag, title, evidence, impact, decision, tone='critical') => `
    <article class="mgmt-issue ${tone}">
      <div class="mgmt-issue-tag">${esc(tag)}</div>
      <h3>${esc(title)}</h3>
      <dl>
        <div><dt>Evidência</dt><dd>${esc(evidence)}</dd></div>
        <div><dt>Impacto</dt><dd>${esc(impact)}</dd></div>
        <div><dt>Decisão necessária</dt><dd>${esc(decision)}</dd></div>
      </dl>
    </article>`;

  renderOverview = function renderManagementOverview(data) {
    const m = data.metrics;
    const g = data.management || {};
    const flow = g.flow || {};
    const backlog = g.backlog || {};
    const visibility = g.visibility || {};
    const external = g.external || {};
    const dq = g.data_quality || {};
    const sourceDate = dateBR(data.meta.source_updated_at);

    const formalAbs = flow.formal_absorption_percent ?? m.completion_rate;
    const operationalAbs = flow.minimum_operational_absorption_percent;
    const operationalGap = flow.minimum_operational_gap;

    document.getElementById('content').innerHTML = `
      <section class="mgmt-hero">
        <div>
          <span>SEPLAN · PAINEL DE GESTÃO</span>
          <h2>O que exige decisão agora</h2>
          <p>Indicadores só aparecem quando ajudam a identificar desvio, impacto e ação. Base atualizada em ${esc(sourceDate)}.</p>
        </div>
        <div class="mgmt-hero-side"><b>${fmt(data.meta.source_rows)}</b><small>protocolos analisados</small></div>
      </section>

      <section class="mgmt-signals">
        ${signal('Absorção formal da demanda', pct(formalAbs), `${fmt(flow.formal_concluded ?? m.concluded)} encerrados / ${fmt(flow.received ?? m.received)} recebidos`, formalAbs >= 100 ? 'good' : 'critical')}
        ${signal('Estoque > 120 dias', pct(backlog.over_120_percent), `${fmt(backlog.over_120_days)} processos`, backlog.over_120_percent > 50 ? 'critical' : 'attention')}
        ${signal('“Em tramitação” genérico', pct(visibility.generic_transit_percent), `${fmt(visibility.generic_transit)} processos sem etapa diagnosticável`, visibility.generic_transit_percent > 50 ? 'critical' : 'attention')}
        ${signal('Dependência externa', pct(external.waiting_external_percent), `${fmt(external.waiting_external)} processos`, 'attention')}
      </section>

      <div class="section-title"><div><h2>Diagnóstico gerencial</h2><p>Problema → impacto → decisão. Sem atribuir causa onde a base não permite.</p></div></div>
      <section class="mgmt-issues">
        ${issue(
          'P1 · FLUXO',
          'A fila continua recebendo mais do que formalmente encerra',
          `${fmt(flow.received)} recebidos contra ${fmt(flow.formal_concluded)} encerrados formais; saldo +${fmt(flow.formal_gap)}.`,
          `A pressão sobre a fila permanece positiva. Mesmo incluindo ${fmt(flow.ready_without_formal_close_opened_in_period)} casos de 2026 já aptos para retirada, ainda existe um déficit operacional mínimo de ${fmt(operationalGap)} processos no período.`,
          'Acompanhar entrada × saída como indicador de equilíbrio e impedir crescimento líquido da fila.'
        )}
        ${issue(
          'P1 · PASSIVO',
          'Mais da metade do estoque está envelhecido',
          `${fmt(backlog.over_120_days)} de ${fmt(backlog.stock)} pendentes estão há mais de 120 dias sem movimentação (${pct(backlog.over_120_percent)}).`,
          'O problema não é apenas demanda nova: existe passivo antigo suficiente para manter prazo e estoque pressionados mesmo que a entrada caia.',
          'Separar uma fila de recuperação do passivo >120 dias da fila corrente e medir redução semanal desse estoque.'
        )}
        ${issue(
          'P1 · VISIBILIDADE',
          'O maior “gargalo” não é um gargalo diagnosticado',
          `${fmt(visibility.generic_transit)} processos (${pct(visibility.generic_transit_percent)}) estão classificados apenas como “Em tramitação”.`,
          'A Chefia vê volume, mas não consegue saber se o atraso está em análise, assinatura, distribuição, fiscalização, documentação ou outro estágio.',
          'Quebrar “Em tramitação” em etapas operacionais exclusivas antes de cobrar desempenho por setor.'
        )}
        ${issue(
          'P1 · QUALIDADE DO DADO',
          'A produção formal está subregistrada',
          `${fmt(dq.ready_without_formal_close_opened_in_period)} protocolos abertos em 2026 e ${fmt(dq.ready_without_formal_close_total)} no total estão aptos/aguardando retirada sem DataEncerramento.`,
          `O KPI formal de conclusão (${pct(formalAbs)}) não representa sozinho a produção efetiva. O mínimo operacional conhecido sobe para ${pct(operationalAbs)} da entrada de 2026.`,
          'Fechar ou reconciliar automaticamente esses casos para que produção e estoque usem a mesma definição de concluído.'
        , 'attention')}
        ${issue(
          'P2 · DEPENDÊNCIA EXTERNA',
          'Parte do estoque não está sob controle direto da SEPLAN',
          `${fmt(external.waiting_external)} pendências (${pct(external.waiting_external_percent)}) estão em exigência externa / responsável técnico.`,
          'Misturar essa espera com tempo interno distorce avaliação de desempenho e impede cálculo justo de prazo.',
          'Separar tempo interno de tempo aguardando terceiro e só então liberar KPI de cumprimento de prazo.'
        , 'attention')}
      </section>

      <div class="section-title"><div><h2>Agenda de gestão</h2><p>O que deve sair da reunião como decisão operacional.</p></div></div>
      <section class="panel mgmt-agenda">
        <table>
          <thead><tr><th>Prioridade</th><th>Decisão</th><th>Indicador de controle</th><th>Resultado esperado</th></tr></thead>
          <tbody>
            <tr><td><b>P1</b></td><td>Criar fila específica para passivo &gt;120 dias</td><td>${fmt(backlog.over_120_days)} casos</td><td>Redução contínua do passivo antigo</td></tr>
            <tr><td><b>P1</b></td><td>Desmembrar “Em tramitação” em etapas reais</td><td>${pct(visibility.generic_transit_percent)} do estoque</td><td>Identificar causa e responsável do gargalo</td></tr>
            <tr><td><b>P1</b></td><td>Reconciliar aptos sem encerramento formal</td><td>${fmt(dq.ready_without_formal_close_total)} casos</td><td>Produção e estoque coerentes</td></tr>
            <tr><td><b>P1</b></td><td>Controlar semanalmente entrada × saída</td><td>Absorção ≥ 100%</td><td>Parar crescimento líquido da fila</td></tr>
            <tr><td><b>P2</b></td><td>Separar espera externa do tempo interno</td><td>${fmt(external.waiting_external)} casos</td><td>Prazo e desempenho sem distorção</td></tr>
          </tbody>
        </table>
      </section>

      <div class="section-title"><div><h2>Evidência operacional</h2><p>Dados que sustentam o diagnóstico acima.</p></div><a class="exec-all-link" href="#/indicadores">Abrir indicadores →</a></div>
      <div class="grid-2 exec-flow-row">
        <article class="panel"><div class="panel-head"><div><span class="eyebrow">FLUXO MENSAL</span><h3>Recebidos × concluídos formais</h3></div></div><canvas id="flowChart" height="280"></canvas></article>
        <article class="panel"><span class="eyebrow">AGING</span><h3>Idade do estoque atual</h3>${barChart(data.charts.aging, COLORS.red)}</article>
      </div>
      <div class="grid-2">
        ${barPanel('Estoque por status operacional', data.charts.statuses, COLORS.purple, 'status')}
        ${barPanel('Pendências por gargalo operacional', data.charts.owners, COLORS.amber, 'owner')}
      </div>
      <div class="mgmt-note"><strong>Leitura correta:</strong> os gráficos são evidência para o diagnóstico; eles não são o produto final da gestão.</div>`;

    drawFlow(data.charts.flow);
    bindBarFilters();
  };
})();
