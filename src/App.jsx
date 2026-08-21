import React, { useEffect, useMemo, useState } from 'react'

const TERMINAIS = new Set(['ENCERRADO','ARQUIVADO','CANCELADO'])
const MESES = ['Jan','Fev','Mar','Abr','Mai','Jun','Jul','Ago','Set','Out','Nov','Dez']
const CUTS = [15,30,60,90,120]
const clean = v => v == null ? '' : String(v).trim()
const num = v => Number.isFinite(Number(v)) ? Number(v) : 0
const toDate = v => { const s=clean(v); if(!s) return null; const d=new Date(s.length===10?`${s}T12:00:00`:s); return Number.isNaN(d.getTime())?null:d }
const fmtDate = v => { const d=toDate(v); return d?d.toLocaleDateString('pt-BR'):'—' }
const fmtDateTime = v => { const d=toDate(v); return d?d.toLocaleString('pt-BR'):'—' }
const mean = a => a.length ? a.reduce((x,y)=>x+y,0)/a.length : 0
const median = a => { if(!a.length)return 0; const s=[...a].sort((x,y)=>x-y),m=Math.floor(s.length/2); return s.length%2?s[m]:(s[m-1]+s[m])/2 }
const daysBetween = (a,b) => { const x=toDate(a),y=toDate(b); return !x||!y?null:Math.max(0,Math.round((y-x)/86400000)) }
const yearOf = v => toDate(v)?.getFullYear() || null

function normalize(r){
  const situacao=clean(r.s)
  const encerradoFormal=Boolean(clean(r.e))
  const terminal=TERMINAIS.has(situacao.toUpperCase())
  return {
    id:clean(r.id), protocolo:clean(r.n)||clean(r.id), ano:num(r.y), abertura:clean(r.a), ultimo:clean(r.u), encerramento:clean(r.e),
    situacao, categoria:clean(r.c)==='NÃO DETERMINADO'||!clean(r.c)?'Classificação pendente':clean(r.c),
    status:clean(r.st)||'Não identificado', responsavel:clean(r.r)||'Não identificado', dias:num(r.d), prioridade:clean(r.p)||'—',
    inscricao:clean(r.i), encerradoFormal, ativo:!encerradoFormal&&!terminal
  }
}

async function loadData(){
  const urls=['/data/2025-a.json','/data/2025-b.json','/data/2026.json']
  const parts=await Promise.all(urls.map(async u=>{const r=await fetch(u,{cache:'no-store'}); if(!r.ok)throw new Error(`Falha ao carregar ${u}`); return r.json()}))
  return parts.flat().map(normalize)
}

function groupCount(rows,key,limit=10){
  const m=new Map(); rows.forEach(r=>{const k=clean(r[key])||'Não identificado';m.set(k,(m.get(k)||0)+1)})
  return [...m.entries()].sort((a,b)=>b[1]-a[1]).slice(0,limit).map(([label,value])=>({label,value}))
}

function Header({updated,total}){
  return <>
    <div className="brandStripe"><span></span><span></span></div>
    <header className="topbar">
      <div className="brandWrap">
        <img src="/logo-itapoa.png" className="logo" alt="Município de Itapoá" />
        <div><div className="eyebrow">SECRETARIA DE PLANEJAMENTO</div><h1>Gestão à Vista <span>SEPLAN</span></h1><p>Indicadores operacionais e gerenciais · Protocolos 2025+</p></div>
      </div>
      <div className="baseBox"><span>BASE ATUALIZADA</span><strong>{updated||'—'}</strong><small>{total.toLocaleString('pt-BR')} protocolos na base</small></div>
    </header>
  </>
}

const TABS=['Visão Executiva','Pendências','Processos','Qualidade da Base']
function Nav({tab,setTab}){return <nav className="tabs">{TABS.map(t=><button key={t} onClick={()=>setTab(t)} className={tab===t?'active':''}>{t}</button>)}</nav>}

function FilterBar({period,setPeriod,category,setCategory,status,setStatus,responsible,setResponsible,categories,statuses,responsibles}){
  const active=period!=='2026'||category||status||responsible
  return <div className="filtersPanel">
    <div className="filterGroup"><label>Período</label><div className="segmented">{['2026','2025','Todos'].map(v=><button key={v} className={period===v?'active':''} onClick={()=>setPeriod(v)}>{v==='Todos'?'2025 + 2026':v}</button>)}</div></div>
    <div className="filterGroup"><label>Categoria</label><select value={category} onChange={e=>setCategory(e.target.value)}><option value="">Todas</option>{categories.map(x=><option key={x}>{x}</option>)}</select></div>
    <div className="filterGroup"><label>Status</label><select value={status} onChange={e=>setStatus(e.target.value)}><option value="">Todos</option>{statuses.map(x=><option key={x}>{x}</option>)}</select></div>
    <div className="filterGroup wide"><label>Responsável</label><select value={responsible} onChange={e=>setResponsible(e.target.value)}><option value="">Todos</option>{responsibles.map(x=><option key={x}>{x}</option>)}</select></div>
    {active&&<button className="clearBtn" onClick={()=>{setPeriod('2026');setCategory('');setStatus('');setResponsible('')}}>Limpar filtros</button>}
  </div>
}

function Kpi({label,value,sub,color,icon,onClick}){
  return <button className={`kpi ${color}`} onClick={onClick}>
    <div className="kpiIcon">{icon}</div><div className="kpiText"><span>{label}</span><strong>{value}</strong><small>{sub}</small></div>
  </button>
}

function Bars({data,onClick,color='blue'}){
  const max=Math.max(1,...data.map(x=>x.value))
  return <div className={`bars ${color}`}>{data.map(d=><button className="barRow" key={d.label} onClick={()=>onClick?.(d)}><span className="barLabel" title={d.label}>{d.label}</span><div className="barTrack"><i style={{width:`${(d.value/max)*100}%`}}/></div><b>{d.value.toLocaleString('pt-BR')}</b></button>)}</div>
}

function FlowChart({data}){
  const w=820,h=250,p=32,max=Math.max(1,...data.flatMap(d=>[d.in,d.out]))
  const x=i=>p+i*(w-2*p)/Math.max(1,data.length-1), y=v=>h-p-(v/max)*(h-2*p)
  const pts=k=>data.map((d,i)=>`${x(i)},${y(d[k])}`).join(' ')
  return <div className="flow"><svg viewBox={`0 0 ${w} ${h}`}>
    {[0,.25,.5,.75,1].map((q,i)=><line key={i} x1={p} x2={w-p} y1={p+q*(h-2*p)} y2={p+q*(h-2*p)} className="gridline"/>)}
    <polyline points={pts('in')} className="line incoming"/><polyline points={pts('out')} className="line outgoing"/>
    {data.map((d,i)=><g key={d.label}><circle cx={x(i)} cy={y(d.in)} r="4" className="dotIn"/><circle cx={x(i)} cy={y(d.out)} r="4" className="dotOut"/><text x={x(i)} y={h-7} textAnchor="middle">{d.label}</text></g>)}
  </svg><div className="legend"><span><i className="lg blue"></i>Recebidos</span><span><i className="lg green"></i>Concluídos</span></div></div>
}

function Threshold({value,setValue}){return <div className="threshold"><span>Parados por mais de</span>{CUTS.map(n=><button key={n} className={value===n?'active':''} onClick={()=>setValue(n)}>{n}d</button>)}</div>}

function Drawer({state,onClose}){
  if(!state)return null
  const {title,rows}=state
  return <div className="overlay" onClick={onClose}><aside className="drawer" onClick={e=>e.stopPropagation()}><div className="drawerHead"><div><small>DRILL-DOWN</small><h2>{title}</h2><p>{rows.length.toLocaleString('pt-BR')} protocolos</p></div><button onClick={onClose}>×</button></div><div className="tableWrap"><table><thead><tr><th>Protocolo</th><th>Abertura</th><th>Categoria</th><th>Status</th><th>Responsável</th><th>Dias s/ mov.</th><th>Inscrição</th></tr></thead><tbody>{rows.slice(0,600).map(r=><tr key={r.id}><td className="mono">{r.protocolo}</td><td>{fmtDate(r.abertura)}</td><td>{r.categoria}</td><td>{r.status}</td><td>{r.responsavel}</td><td className={r.dias>60?'critical':r.dias>30?'warning':''}>{r.dias}</td><td className="mono">{r.inscricao||'—'}</td></tr>)}</tbody></table>{rows.length>600&&<p className="tableNote">Exibindo os primeiros 600 registros deste recorte.</p>}</div></aside></div>
}

function ResponsaveisTable({rows,threshold,setDrawer}){
  const map=new Map()
  rows.forEach(r=>{const k=r.responsavel||'Não identificado'; if(!map.has(k))map.set(k,[]);map.get(k).push(r)})
  const data=[...map].map(([name,arr])=>({name,arr,stock:arr.length,cut:arr.filter(r=>r.dias>threshold).length,d60:arr.filter(r=>r.dias>60).length,med:Math.round(median(arr.map(r=>r.dias))) })).sort((a,b)=>b.stock-a.stock).slice(0,12)
  return <div className="respTable"><div className="respHead"><span>Responsável / gargalo</span><span>Estoque</span><span>&gt;{threshold}d</span><span>&gt;60d</span><span>Mediana</span></div>{data.map(d=><button key={d.name} onClick={()=>setDrawer({title:`Pendências · ${d.name}`,rows:d.arr})}><span title={d.name}>{d.name}</span><b>{d.stock}</b><b className={d.cut?'warning':''}>{d.cut}</b><b className={d.d60?'critical':''}>{d.d60}</b><b>{d.med}d</b></button>)}</div>
}

function Executive({all,received,concluded,stock,period,threshold,setThreshold,setDrawer}){
  const durations=concluded.map(r=>daysBetween(r.abertura,r.encerramento)).filter(v=>v!=null)
  const avg=durations.length?Math.round(mean(durations)):0, med=durations.length?Math.round(median(durations)):0
  const stopped=stock.filter(r=>r.dias>threshold), pct=stock.length?100*stopped.length/stock.length:0
  const months=period==='Todos'?[...Array(24)].map((_,i)=>{const y=i<12?2025:2026,m=i%12;return {y,m,label:`${MESES[m]}/${String(y).slice(2)}`}}):MESES.map((m,i)=>({y:Number(period),m:i,label:m}))
  const flow=months.map(x=>({label:x.label,in:all.filter(r=>yearOf(r.abertura)===x.y&&toDate(r.abertura)?.getMonth()===x.m).length,out:all.filter(r=>yearOf(r.encerramento)===x.y&&toDate(r.encerramento)?.getMonth()===x.m).length}))
  const aging=[['0–15',r=>r.dias<=15],['16–30',r=>r.dias>=16&&r.dias<=30],['31–60',r=>r.dias>=31&&r.dias<=60],['61–90',r=>r.dias>=61&&r.dias<=90],['91–120',r=>r.dias>=91&&r.dias<=120],['>120',r=>r.dias>120]].map(([label,fn])=>({label,value:stock.filter(fn).length,fn}))
  const status=groupCount(stock,'status',9), categories=groupCount(received,'categoria',9)
  return <>
    <div className="sectionTitle"><div><span>INDICADORES SOLICITADOS</span><h2>Visão executiva</h2></div><Threshold value={threshold} setValue={setThreshold}/></div>
    <div className="kpiGrid">
      <Kpi label="Processos recebidos" value={received.length.toLocaleString('pt-BR')} sub={period==='Todos'?'abertos em 2025–2026':`abertos em ${period}`} color="blue" icon="↘" onClick={()=>setDrawer({title:'Processos recebidos',rows:received})}/>
      <Kpi label="Processos concluídos" value={concluded.length.toLocaleString('pt-BR')} sub={period==='Todos'?'encerrados em 2025–2026':`encerrados em ${period}`} color="green" icon="✓" onClick={()=>setDrawer({title:'Processos concluídos',rows:concluded})}/>
      <Kpi label="Estoque pendente" value={stock.length.toLocaleString('pt-BR')} sub="processos ativos na base atual" color="orange" icon="▤" onClick={()=>setDrawer({title:'Estoque atual de pendências',rows:stock})}/>
      <Kpi label="Tempo médio" value={durations.length?`${avg} dias`:'—'} sub={durations.length?`mediana: ${med} dias · ${durations.length.toLocaleString('pt-BR')} concluídos`:'sem encerramentos formais'} color="purple" icon="◷" onClick={()=>setDrawer({title:'Concluídos usados no tempo médio',rows:concluded})}/>
      <Kpi label={`Parados >${threshold} dias`} value={`${pct.toFixed(1)}%`} sub={`${stopped.length.toLocaleString('pt-BR')} de ${stock.length.toLocaleString('pt-BR')} pendentes`} color="red" icon="!" onClick={()=>setDrawer({title:`Parados há mais de ${threshold} dias`,rows:stopped})}/>
    </div>
    <div className="insightRow"><div><span>Saldo do período</span><strong className={received.length-concluded.length>0?'bad':'good'}>{received.length-concluded.length>0?'+':''}{(received.length-concluded.length).toLocaleString('pt-BR')}</strong><small>recebidos − concluídos</small></div><div><span>Estoque crítico &gt;60d</span><strong>{stock.filter(r=>r.dias>60).length.toLocaleString('pt-BR')}</strong><small>{stock.length?`${(100*stock.filter(r=>r.dias>60).length/stock.length).toFixed(1)}% do estoque`:''}</small></div><div><span>Estoque muito crítico &gt;120d</span><strong>{stock.filter(r=>r.dias>120).length.toLocaleString('pt-BR')}</strong><small>{stock.length?`${(100*stock.filter(r=>r.dias>120).length/stock.length).toFixed(1)}% do estoque`:''}</small></div></div>
    <div className="layout">
      <section className="panel wide"><div className="panelHead"><div><span>FLUXO MENSAL</span><h3>Entradas × conclusões</h3></div><small>clique nos demais blocos para abrir os protocolos</small></div><FlowChart data={flow}/></section>
      <section className="panel"><div className="panelHead"><div><span>ENVELHECIMENTO</span><h3>Tempo sem movimentação</h3></div></div><Bars color="warm" data={aging} onClick={d=>setDrawer({title:`Sem movimentação · ${d.label} dias`,rows:stock.filter(d.fn)})}/></section>
      <section className="panel"><div className="panelHead"><div><span>STATUS OPERACIONAL</span><h3>Onde estão os pendentes?</h3></div></div><Bars color="teal" data={status} onClick={d=>setDrawer({title:d.label,rows:stock.filter(r=>r.status===d.label)})}/></section>
      <section className="panel"><div className="panelHead"><div><span>DEMANDAS</span><h3>O que mais chega à SEPLAN?</h3></div></div><Bars color="blue" data={categories} onClick={d=>setDrawer({title:d.label,rows:received.filter(r=>r.categoria===d.label)})}/></section>
      <section className="panel"><div className="panelHead"><div><span>RESPONSABILIDADE</span><h3>Pendências por responsável</h3></div></div><ResponsaveisTable rows={stock} threshold={threshold} setDrawer={setDrawer}/></section>
    </div>
  </>
}

function Pendencias({stock,threshold,setThreshold,setDrawer}){
  const critical=[...stock].sort((a,b)=>b.dias-a.dias)
  return <><div className="sectionTitle"><div><span>GESTÃO DA FILA</span><h2>Pendências</h2></div><Threshold value={threshold} setValue={setThreshold}/></div><div className="layout"><section className="panel"><div className="panelHead"><div><span>RESPONSÁVEIS</span><h3>Distribuição do estoque</h3></div></div><ResponsaveisTable rows={stock} threshold={threshold} setDrawer={setDrawer}/></section><section className="panel"><div className="panelHead"><div><span>MAIOR INATIVIDADE</span><h3>Fila crítica</h3></div></div><div className="tableWrap"><table><thead><tr><th>Protocolo</th><th>Categoria</th><th>Responsável</th><th>Dias</th></tr></thead><tbody>{critical.slice(0,250).map(r=><tr key={r.id} onClick={()=>setDrawer({title:r.protocolo,rows:[r]})}><td className="mono">{r.protocolo}</td><td>{r.categoria}</td><td>{r.responsavel}</td><td className={r.dias>60?'critical':r.dias>30?'warning':''}>{r.dias}</td></tr>)}</tbody></table></div></section></div></>
}

function Processes({rows,setDrawer}){
  const [q,setQ]=useState('')
  const result=useMemo(()=>{const s=q.toLowerCase().trim();return !s?rows:rows.filter(r=>[r.protocolo,r.inscricao,r.categoria,r.responsavel,r.status].some(v=>clean(v).toLowerCase().includes(s)))},[rows,q])
  return <section className="panel full"><div className="searchHead"><div><span>EXPLORADOR</span><h2>Processos</h2></div><input value={q} onChange={e=>setQ(e.target.value)} placeholder="Buscar protocolo, inscrição, categoria, responsável…"/></div><p className="resultCount">{result.length.toLocaleString('pt-BR')} registros</p><div className="tableWrap tall"><table><thead><tr><th>Protocolo</th><th>Abertura</th><th>Categoria</th><th>Status</th><th>Responsável</th><th>Dias s/ mov.</th><th>Inscrição</th></tr></thead><tbody>{result.slice(0,500).map(r=><tr key={r.id} onClick={()=>setDrawer({title:r.protocolo,rows:[r]})}><td className="mono">{r.protocolo}</td><td>{fmtDate(r.abertura)}</td><td>{r.categoria}</td><td>{r.status}</td><td>{r.responsavel}</td><td>{r.dias}</td><td className="mono">{r.inscricao||'—'}</td></tr>)}</tbody></table></div></section>
}

function Quality({all}){
  const unique=new Set(all.map(r=>r.id)).size, review=all.filter(r=>r.categoria==='Classificação pendente').length, inscriptions=all.filter(r=>r.inscricao).length
  const cards=[['Registros da base',all.length,'blue'],['Protocolos únicos',unique,'green'],['Classificação pendente',review,'orange'],['Inscrições identificadas',inscriptions,'purple']]
  return <><div className="qualityGrid">{cards.map(([l,v,c])=><div key={l} className={`quality ${c}`}><span>{l}</span><strong>{Number(v).toLocaleString('pt-BR')}</strong></div>)}</div><section className="panel full note"><h3>Escopo desta versão</h3><p>O painel usa somente indicadores sustentados pela base atual de protocolos. Diligências, fiscalizações, denúncias respondidas, cumprimento de prazo oficial e projetos públicos serão integrados quando existirem bases próprias e regras validadas.</p></section></>
}

export default function App(){
  const [data,setData]=useState([]),[loading,setLoading]=useState(true),[error,setError]=useState(''),[tab,setTab]=useState('Visão Executiva')
  const [period,setPeriod]=useState('2026'),[category,setCategory]=useState(''),[status,setStatus]=useState(''),[responsible,setResponsible]=useState(''),[threshold,setThreshold]=useState(30),[drawer,setDrawer]=useState(null)
  useEffect(()=>{loadData().then(setData).catch(e=>setError(e.message)).finally(()=>setLoading(false))},[])
  const updated=useMemo(()=>data.map(r=>r.ultimo).filter(Boolean).sort().at(-1),[data])
  const common=useMemo(()=>data.filter(r=>(!category||r.categoria===category)&&(!status||r.status===status)&&(!responsible||r.responsavel===responsible)),[data,category,status,responsible])
  const received=useMemo(()=>common.filter(r=>period==='Todos'||String(yearOf(r.abertura))===period),[common,period])
  const concluded=useMemo(()=>common.filter(r=>r.encerradoFormal&&(period==='Todos'||String(yearOf(r.encerramento))===period)),[common,period])
  const stock=useMemo(()=>common.filter(r=>r.ativo),[common])
  const categories=useMemo(()=>[...new Set(data.map(r=>r.categoria))].sort(),[data]), statuses=useMemo(()=>[...new Set(data.map(r=>r.status))].sort(),[data]), responsibles=useMemo(()=>[...new Set(data.map(r=>r.responsavel))].sort(),[data])
  if(loading)return <div className="loading"><div className="spinner"></div><h2>Carregando Gestão à Vista…</h2><p>Preparando os indicadores da base SEPLAN.</p></div>
  if(error)return <div className="loading error"><h2>Falha ao carregar os dados</h2><p>{error}</p></div>
  return <div className="app"><Header updated={fmtDateTime(updated)} total={data.length}/><Nav tab={tab} setTab={setTab}/><main><FilterBar period={period} setPeriod={setPeriod} category={category} setCategory={setCategory} status={status} setStatus={setStatus} responsible={responsible} setResponsible={setResponsible} categories={categories} statuses={statuses} responsibles={responsibles}/>{tab==='Visão Executiva'&&<Executive all={common} received={received} concluded={concluded} stock={stock} period={period} threshold={threshold} setThreshold={setThreshold} setDrawer={setDrawer}/>} {tab==='Pendências'&&<Pendencias stock={stock} threshold={threshold} setThreshold={setThreshold} setDrawer={setDrawer}/>} {tab==='Processos'&&<Processes rows={common} setDrawer={setDrawer}/>} {tab==='Qualidade da Base'&&<Quality all={data}/>}</main><Drawer state={drawer} onClose={()=>setDrawer(null)}/><footer>SEPLAN · Município de Itapoá · Fonte oficial: base XLSX de protocolos 2025+</footer></div>
}
