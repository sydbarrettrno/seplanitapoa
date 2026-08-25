(() => {
  const num = (v) => fmt(Number(v || 0));
  const dec = (v) => v == null ? '—' : one(v);
  const percent = (v) => v == null ? '—' : `${dec(v)}%`;

  const toneClass = (tone) => ` chief-${tone || 'neutral'}`;

  const metric = (label, value, note, tone = 'neutral', kicker = '') => `
    <article class="chief-metric${toneClass(tone)}">
      ${kicker ? `<span class="chief-metric-kicker">${esc(kicker)}</span>` : ''}
      <span class="chief-metric-label">${esc(label)}</span>
      <strong>${esc(value)}</strong>
      <small>${esc(note)}</small>
    </article>`;

  const smallMetric = (label, value, note, tone = 'neutral') => `
    <article class="chief-small${toneClass(tone)}">
      <span>${esc(label)}</span>
      <strong>${esc(value)}</strong>
      <small>${esc(note)}</small>
    </article>`;

  const bars = (title, rows, limit = 10, tone = 'blue', subtitle = '') => {
    const data = (rows || []).slice(0, limit);
    const max = Math.max(1, ...data.map(x => Number(x.value || 0)));
    return `<article class="panel chief-panel chief-bar-panel">
      <div class="chief-panel-title"><div><span>${esc(subtitle)}</span><h3>${esc(title)}</h3></div></div>
      <div class="chief-bars">${data.map(x => {
        const value = Number(x.value || 0);
        const width = Math.max(2, value / max * 100);
        return `<div class="chief-bar-row">
          <div class="chief-bar-label">${esc(x.name)}</div>
          <div class="chief-bar-track"><div class="chief-bar-fill chief-fill-${tone}" style="width:${width}%"></div><b>${num(value)}</b></div>
        </div>`;
      }).join('')}</div>
    </article>`;
  };

  const comparison = (cmp) => {
    const cur = cmp.current || {};
    const prev = cmp.previous || {};
    const rows = [
      {name:'Recebidos', a:Number(prev.received || 0), b:Number(cur.received || 0)},
      {name:'Concluídos da própria demanda', a:Number(prev.cohort_concluded || 0), b:Number(cur.cohort_concluded || 0)}
    ];
    const max = Math.max(1, ...rows.flatMap(r => [r.a, r.b]));
    return `<article class="panel chief-panel">
      <div class="chief-panel-title"><div><span>MESMO PERÍODO · MESMA REGRA</span><h3>2025 × 2026</h3></div><div class="chief-legend"><i class="y25"></i>2025 <i class="y26"></i>2026</div></div>
      <div class="chief-compare">${rows.map(r => `
        <div class="chief-compare-row">
          <b>${esc(r.name)}</b>
          <div class="chief-compare-line"><span>2025</span><div class="chief-compare-track"><div class="chief-compare-fill y25" style="width:${Math.max(2,r.a/max*100)}%"></div><strong>${num(r.a)}</strong></div></div>
          <div class="chief-compare-line"><span>2026</span><div class="chief-compare-track"><div class="chief-compare-fill y26" style="width:${Math.max(2,r.b/max*100)}%"></div><strong>${num(r.b)}</strong></div></div>
        </div>`).join('')}</div>
    </article>`;
  };

  const flow = (rows) => {
    const data = rows || [];
    const max = Math.max(1, ...data.flatMap(x => [Number(x.received || 0), Number(x.concluded || 0)]));
    const label = (s) => {
      const [y,m] = String(s).split('-');
      return `${m}/${String(y).slice(2)}`;
    };
    return `<article class="panel chief-panel chief-flow-panel">
      <div class="chief-panel-title"><div><span>FLUXO MENSAL</span><h3>Entradas × produção operacional</h3></div><div class="chief-legend"><i class="rec"></i>Recebidos <i class="out"></i>Concluídos</div></div>
      <div class="chief-flow">${data.map(x => {
        const a = Number(x.received || 0), b = Number(x.concluded || 0);
        return `<div class="chief-flow-group">
          <div class="chief-flow-columns">
            <div class="chief-column-wrap"><b>${num(a)}</b><div class="chief-column received" style="height:${Math.max(5,a/max*170)}px"></div></div>
            <div class="chief-column-wrap"><b>${num(b)}</b><div class="chief-column concluded" style="height:${Math.max(5,b/max*170)}px"></div></div>
          </div><span>${esc(label(x.month))}</span>
        </div>`;
      }).join('')}</div>
    </article>`;
  };

  const coverageRow = (id, label, value, status, note) => `
    <div class="chief-coverage-row">
      <span class="chief-coverage-id">${esc(id)}</span>
      <b>${esc(label)}</b>
      <strong>${esc(value)}</strong>
      <span class="chief-badge ${status === 'OK' ? 'ok' : status === 'PARCIAL' ? 'partial' : 'off'}">${esc(status)}</span>
      <small>${esc(note)}</small>
    </div>`;

  renderOverview = function renderChiefOverview(data) {
    const m = data.metrics || {};
    const mg = data.management || {};
    const cmp = mg.comparison || {};
    const cur = cmp.current || {};
    const prev = cmp.previous || {};
    const complaints = mg.complaints || {};
    const inspections = mg.inspections || {};
    const projects = mg.public_projects || {};
    const t = m.turnaround || {};

    const receivedCurrent = Number(cur.received || m.received || 0);
    const concludedCurrent = Number(cur.cohort_concluded || 0);
    const pendingCurrent = Math.max(0, receivedCurrent - concludedCurrent);
    const passiveAbsorbed = Number(cur.passive_absorbed || 0);
    const totalProduction = Number(cur.concluded_total || m.concluded || 0);
    const stockTotal = Number(m.stock || 0);
    const stockPassive = Math.max(0, stockTotal - pendingCurrent);
    const demandDelta = cmp.received_change_percent == null ? '—' : `${cmp.received_change_percent > 0 ? '+' : ''}${dec(cmp.received_change_percent)}%`;
    const cohortDelta = cmp.cohort_concluded_change_percent == null ? '—' : `${cmp.cohort_concluded_change_percent > 0 ? '+' : ''}${dec(cmp.cohort_concluded_change_percent)}%`;

    document.getElementById('content').innerHTML = `
      <section class="chief-hero">
        <div>
          <span class="chief-eyebrow">SEPLAN · RESULTADOS OPERACIONAIS</span>
          <h2>O que entrou, o que saiu e o que permanece na fila</h2>
          <p>Período ${dateBR(data.meta.period?.from)} a ${dateBR(data.meta.period?.to)} · Taxonomia ${esc(data.meta.taxonomy_version || 'V07')} · ${num(data.meta.source_rows)} protocolos.</p>
        </div>
        <div class="chief-hero-stamp"><span>Comparação</span><strong>2025 × 2026</strong><small>mesmo período</small></div>
      </section>

      <section class="chief-primary-grid">
        ${metric('Processos recebidos', num(receivedCurrent), `${num(prev.received || 0)} em 2025 · ${demandDelta}`, 'blue', 'DEMANDA 2026')}
        ${metric('Produção operacional', num(totalProduction), `${num(concludedCurrent)} da demanda 2026 + ${num(passiveAbsorbed)} do passivo`, 'green', 'CONCLUÍDOS EM 2026')}
        ${metric('Estoque atual', num(stockTotal), `${num(pendingCurrent)} da demanda 2026 + ${num(stockPassive)} do passivo`, 'orange', 'POSIÇÃO EM 22/08')}
      </section>

      <section class="chief-reconcile">
        <div><span>Demanda 2026</span><strong>${num(receivedCurrent)}</strong><small>= ${num(concludedCurrent)} concluídos + ${num(pendingCurrent)} pendentes</small></div>
        <div><span>Produção 2026</span><strong>${num(totalProduction)}</strong><small>= ${num(concludedCurrent)} demanda corrente + ${num(passiveAbsorbed)} passivo</small></div>
        <div><span>Estoque atual</span><strong>${num(stockTotal)}</strong><small>= ${num(pendingCurrent)} demanda 2026 + ${num(stockPassive)} passivo 2025</small></div>
      </section>

      <section class="chief-small-grid">
        ${smallMetric('Tempo de tramitação', `${dec(t.median_days)} dias`, `mediana · média ${dec(t.mean_days)} · P90 ${dec(t.p90_days)}`, 'purple')}
        ${smallMetric(`Fila interna > ${num(m.stopped?.threshold_days)} dias`, percent(m.stopped?.percent), `${num(m.stopped?.count)} de ${num(m.stopped?.eligible_stock)} processos internos`, 'red')}
        ${smallMetric('Denúncias', `${num(complaints.received)} / ${num(complaints.responded_operational)}`, 'recebidas / concluídas no período', 'pink')}
        ${smallMetric('Fiscalização', num(inspections.protocols_received), `${num(inspections.protocols_concluded_operational)} protocolo concluído · não equivale a atos realizados`, 'cyan')}
        ${smallMetric('Projetos e obras públicas', num(projects.protocols_received), `${num(projects.protocols_stock)} protocolos em estoque · não equivale a projetos únicos`, 'indigo')}
        ${smallMetric('Produção da demanda corrente', num(concludedCurrent), `${cohortDelta} vs mesma coorte de 2025`, 'teal')}
      </section>

      <div class="chief-section-title"><div><span>DEMANDA</span><h2>Quais serviços mais chegam à SEPLAN?</h2></div></div>
      <section class="chief-grid-2">
        ${bars('Processos recebidos por categoria', data.charts?.received_categories, 10, 'blue', '2026 · valores no gráfico')}
        ${comparison(cmp)}
      </section>

      <div class="chief-section-title"><div><span>PRODUÇÃO</span><h2>Como a equipe está absorvendo a demanda?</h2></div></div>
      <section class="chief-grid-2">
        ${flow(data.charts?.flow)}
        ${bars('Conclusões por categoria', data.charts?.concluded_categories, 10, 'green', 'produção operacional no período')}
      </section>

      <div class="chief-section-title"><div><span>ESTOQUE E GARGALO</span><h2>Onde estão os processos que ainda não terminaram?</h2></div></div>
      <section class="chief-grid-3">
        ${bars('Estoque por status', data.charts?.statuses, 8, 'orange', 'posição atual')}
        ${bars('Pendências por responsabilidade', data.charts?.owners, 8, 'amber', 'posição atual')}
        ${bars('Fila interna · dias sem movimentação', data.charts?.internal_aging, 8, 'red', 'somente responsabilidade interna')}
      </section>

      <div class="chief-section-title"><div><span>11 INDICADORES SOLICITADOS</span><h2>Cobertura objetiva da base atual</h2></div></div>
      <section class="panel chief-coverage">
        ${coverageRow('01','Processos recebidos',num(m.received),'OK','Data de abertura no período.')}
        ${coverageRow('02','Processos concluídos',num(m.concluded),'OK',`${num(m.concluded_formal)} encerramentos formais; operacional separado.`)}
        ${coverageRow('03','Estoque pendente',num(m.stock),'OK',`${num(m.internal_queue)} internos · ${num(m.external_wait)} externos · ${num(m.suspended)} suspensos.`)}
        ${coverageRow('04','Tempo de tramitação',`${dec(t.mean_days)} dias`,'OK',`mediana ${dec(t.median_days)} · P90 ${dec(t.p90_days)}.`)}
        ${coverageRow('05',`Parados > ${num(m.stopped?.threshold_days)} dias`,percent(m.stopped?.percent),'OK',`${num(m.stopped?.count)} processos da fila interna.`)}
        ${coverageRow('06','Concluídos dentro do prazo','—','SEM FONTE','Não existe tabela oficial de prazos/suspensões integrada.')}
        ${coverageRow('07','Diligências por processo','—','SEM FONTE','A base possui apenas o último trâmite, não o histórico completo.')}
        ${coverageRow('08','Fiscalizações realizadas',num(inspections.protocols_received),'PARCIAL','Número exibido = protocolos de fiscalização recebidos; ato realizado não é comprovável nesta fonte.')}
        ${coverageRow('09','Denúncias recebidas / concluídas',`${num(complaints.received)} / ${num(complaints.responded_operational)}`,'PARCIAL','Conclusão operacional usada como resposta do protocolo.')}
        ${coverageRow('10','Projetos públicos por etapa',num(projects.protocols_identified),'PARCIAL','São protocolos relacionados a projetos/obras públicas, não projetos únicos.')}
        ${coverageRow('11','Pendências por responsável / setor',num(m.stock),'OK','Responsabilidade atual derivada do Status Real.')}
      </section>`;
  };
})();
