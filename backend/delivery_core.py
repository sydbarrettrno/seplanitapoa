from __future__ import annotations

from collections import Counter
from datetime import timedelta
from typing import Any

from backend import core

core.TERMINAL_STATUSES = {"ENCERRADO"}

_OWNER_BY_STATUS = {
    "ENCERRADO": "Nenhum",
    "EM ANÁLISE": "Interno",
    "EM FORMALIZAÇÃO": "Interno",
    "AGUARDANDO REQUERENTE": "Requerente",
    "AGUARDANDO RT": "RT",
    "AGUARDANDO TERCEIRO/SETOR": "Terceiro / Setor",
    "SUSPENSO": "Indefinido",
}

INDICATOR_COVERAGE = [
    {"id":"KPI01","name":"Processos recebidos","status":"DISPONÍVEL","reason":"Data de abertura e protocolo."},
    {"id":"KPI02","name":"Processos concluídos","status":"DISPONÍVEL","reason":"Conclusão operacional e encerramento formal permanecem separados."},
    {"id":"KPI03","name":"Estoque pendente","status":"DISPONÍVEL","reason":"Status Real atual, separado por responsabilidade."},
    {"id":"KPI04","name":"Tempo de tramitação","status":"DISPONÍVEL","reason":"Média, mediana e P90 da conclusão operacional; formal disponível para auditoria."},
    {"id":"KPI05","name":"% parados > X dias","status":"DISPONÍVEL","reason":"Calculado sobre a fila interna SEPLAN."},
    {"id":"KPI06","name":"% concluído dentro do prazo","status":"FONTE NÃO INTEGRADA","reason":"Falta dimensão oficial de prazos e regras de suspensão."},
    {"id":"KPI07","name":"Diligências por processo","status":"FONTE NÃO INTEGRADA","reason":"Exige histórico completo de eventos."},
    {"id":"KPI08","name":"Fiscalizações realizadas","status":"PARCIAL","reason":"A categoria identifica demanda, mas não comprova todos os atos executados."},
    {"id":"KPI09","name":"Denúncias recebidas/respondidas","status":"PARCIAL","reason":"Denúncia está separada na taxonomia; encerramento operacional permite medir respostas."},
    {"id":"KPI10","name":"Projetos públicos por etapa","status":"BASE COMPLEMENTAR","reason":"Protocolo não substitui carteira de projetos."},
    {"id":"KPI11","name":"Pendências por responsável/setor","status":"DISPONÍVEL","reason":"Responsabilidade atual derivada do Status Real."},
]

Query = core.Query
query_from_params = core.query_from_params

def _rows():
    rows = core.load_rows()
    for r in rows:
        status = core._clean(r.get("StatusOperacional")).upper()
        r["GargaloOperacional"] = _OWNER_BY_STATUS.get(status, "Indefinido")
        if status == "ENCERRADO":
            r["DataConclusaoOperacional"] = r.get("DataEncerramento") or r.get("UltimoTramiteDataHora")
        else:
            r["DataConclusaoOperacional"] = ""
    return rows

def _is_stock(r):
    return core._clean(r.get("StatusOperacional")).upper() != "ENCERRADO"

def _is_internal(r):
    return core._clean(r.get("GargaloOperacional")).upper() == "INTERNO"

def _is_external(r):
    return core._clean(r.get("GargaloOperacional")).upper() in {"REQUERENTE","RT","TERCEIRO / SETOR"}

def _turnaround(rows, end_field):
    vals = [d for d in (core._days_between(r.get("DataAbertura"), r.get(end_field)) for r in rows) if d is not None]
    return {
        "eligible": len(vals),
        "median_days": round(core._median(vals), 1) if vals else None,
        "mean_days": round(core._mean(vals), 1) if vals else None,
        "p90_days": round(core._percentile(vals, .9), 1) if vals else None,
    }

def _aging(rows):
    out=[]
    for name,low,high in core.AGING_BANDS:
        n=sum(1 for r in rows if int(r.get("DiasSemMovimento",-1)) >= low and (high is None or int(r.get("DiasSemMovimento",-1)) <= high))
        out.append({"name":name,"value":n})
    return out

def _top(rows,key,limit=12):
    c=Counter(core._clean(r.get(key)) or "Não identificado" for r in rows)
    return [{"name":k,"value":v} for k,v in c.most_common(limit)]

def _record(r):
    return {
        "protocol": r.get("NumeroAnoOriginal") or r.get("ProtocoloID"),
        "protocol_id": r.get("ProtocoloID"),
        "opened": r.get("DataAbertura"),
        "last_movement": r.get("UltimoTramiteDataHora"),
        "closed": r.get("DataEncerramento") or None,
        "operational_close": r.get("DataConclusaoOperacional") or None,
        "category": r.get("Categoria"),
        "macroprocess": r.get("Macroprocesso"),
        "status": r.get("StatusOperacional"),
        "owner": r.get("GargaloOperacional"),
        "days_without_movement": r.get("DiasSemMovimento") if int(r.get("DiasSemMovimento",-1)) >= 0 else None,
    }

def dashboard(query):
    rows=_rows()
    scoped=[r for r in rows if core._matches_scope(r,query)]
    received=[r for r in scoped if core._in_period(r.get("DataAbertura"),query.start,query.end)]
    concluded=[r for r in scoped if core._in_period(r.get("DataConclusaoOperacional"),query.start,query.end)]
    formal=[r for r in scoped if core._in_period(r.get("DataEncerramento"),query.start,query.end)]
    stock=[r for r in scoped if _is_stock(r)]
    internal=[r for r in stock if _is_internal(r)]
    external=[r for r in stock if _is_external(r)]
    suspended=[r for r in stock if core._clean(r.get("StatusOperacional")).upper()=="SUSPENSO"]
    stopped=[r for r in internal if int(r.get("DiasSemMovimento",-1)) > query.threshold]

    flow={m:{"month":m,"received":0,"concluded":0,"concluded_formal":0} for m in core._month_keys(query.start,query.end)}
    for r in received:
        d=core._as_date(r.get("DataAbertura")); key=f"{d.year:04d}-{d.month:02d}"
        if key in flow: flow[key]["received"]+=1
    for r in concluded:
        d=core._as_date(r.get("DataConclusaoOperacional")); key=f"{d.year:04d}-{d.month:02d}"
        if key in flow: flow[key]["concluded"]+=1
    for r in formal:
        d=core._as_date(r.get("DataEncerramento")); key=f"{d.year:04d}-{d.month:02d}"
        if key in flow: flow[key]["concluded_formal"]+=1

    try:
        ps=query.start.replace(year=query.start.year-1); pe=query.end.replace(year=query.end.year-1)
    except ValueError:
        ps=query.start-timedelta(days=365); pe=query.end-timedelta(days=365)
    prev_received=[r for r in scoped if core._in_period(r.get("DataAbertura"),ps,pe)]
    cohort=[r for r in scoped if core._in_period(r.get("DataAbertura"),query.start,query.end) and core._in_period(r.get("DataConclusaoOperacional"),query.start,query.end)]
    cohort_formal=[r for r in scoped if core._in_period(r.get("DataAbertura"),query.start,query.end) and core._in_period(r.get("DataEncerramento"),query.start,query.end)]
    prev_cohort=[r for r in scoped if core._in_period(r.get("DataAbertura"),ps,pe) and core._in_period(r.get("DataConclusaoOperacional"),ps,pe)]
    prev_cohort_formal=[r for r in scoped if core._in_period(r.get("DataAbertura"),ps,pe) and core._in_period(r.get("DataEncerramento"),ps,pe)]

    metrics={
        "received":len(received),
        "concluded":len(concluded),
        "concluded_formal":len(formal),
        "stock":len(stock),
        "internal_queue":len(internal),
        "external_wait":len(external),
        "suspended":len(suspended),
        "turnaround":_turnaround(concluded,"DataConclusaoOperacional"),
        "turnaround_formal":_turnaround(formal,"DataEncerramento"),
        "stopped":{"threshold_days":query.threshold,"count":len(stopped),"eligible_stock":len(internal),"percent":core._pct(len(stopped),len(internal)),"denominator_label":"fila interna SEPLAN"},
        "period_balance":len(received)-len(concluded),
        "completion_rate":core._pct(len(concluded),len(received)),
        "formal_completion_rate":core._pct(len(formal),len(received)),
    }

    complaint_received=[r for r in received if core._clean(r.get("Categoria"))=="Denúncia"]
    complaint_responded=[r for r in concluded if core._clean(r.get("Categoria"))=="Denúncia"]
    complaint_stock=[r for r in stock if core._clean(r.get("Categoria"))=="Denúncia"]

    management={
        "comparison":{
            "current":{"received":len(received),"concluded_total":len(concluded),"concluded_formal_total":len(formal),"cohort_concluded":len(cohort),"cohort_concluded_formal":len(cohort_formal),"passive_absorbed":len(concluded)-len(cohort),"passive_absorbed_formal":len(formal)-len(cohort_formal)},
            "previous":{"from":ps.isoformat(),"to":pe.isoformat(),"received":len(prev_received),"cohort_concluded":len(prev_cohort),"cohort_concluded_formal":len(prev_cohort_formal)},
            "received_change_percent":round((len(received)-len(prev_received))/len(prev_received)*100,1) if prev_received else None,
            "cohort_concluded_change_percent":round((len(cohort)-len(prev_cohort))/len(prev_cohort)*100,1) if prev_cohort else None,
            "cohort_formal_change_percent":round((len(cohort_formal)-len(prev_cohort_formal))/len(prev_cohort_formal)*100,1) if prev_cohort_formal else None,
            "note":"Comparação de produção usa coorte do próprio período para evitar assimetria de passivo anterior a 2025."
        },
        "position":{"stock":len(stock),"internal_queue":len(internal),"external_wait":len(external),"suspended":len(suspended),"internal_percent":core._pct(len(internal),len(stock)),"external_percent":core._pct(len(external),len(stock))},
        "inactivity":{"threshold_days":query.threshold,"internal_stopped":len(stopped),"internal_total":len(internal),"internal_stopped_percent":core._pct(len(stopped),len(internal))},
        "time":{"operational":metrics["turnaround"],"formal":metrics["turnaround_formal"]},
        "data_quality":{"operational_closed_without_formal_date":sum(1 for r in scoped if core._clean(r.get("StatusOperacional")).upper()=="ENCERRADO" and not core._clean(r.get("DataEncerramento")))},
        "complaints":{"received":len(complaint_received),"responded_operational":len(complaint_responded),"stock":len(complaint_stock)},
    }

    record_source={"all":scoped,"received":received,"concluded":concluded,"stock":stock,"stopped":stopped}.get(query.recordset,scoped)
    sorted_records=sorted(record_source,key=lambda r:(core._clean(r.get("UltimoTramiteDataHora")),core._clean(r.get("ProtocoloID"))),reverse=True)
    page=sorted_records[query.offset:query.offset+query.limit]

    return {
        "ok":True,
        "meta":{"dataset":core.metadata().get("dataset"),"source_rows":core.metadata().get("source_rows"),"source_updated_at":core.metadata().get("source_updated_at"),"schema_version":core.metadata().get("schema_version"),"privacy_note":core.metadata().get("privacy",{}).get("note"),"scope_rows":len(scoped),"period":{"from":query.start.isoformat(),"to":query.end.isoformat()}},
        "metrics":metrics,
        "management":management,
        "charts":{"flow":list(flow.values()),"aging":_aging(stock),"internal_aging":_aging(internal),"categories":_top(stock,"Categoria"),"internal_categories":_top(internal,"Categoria"),"owners":_top(stock,"GargaloOperacional"),"statuses":_top(stock,"StatusOperacional")},
        "records":{"total":len(record_source),"offset":query.offset,"limit":query.limit,"recordset":query.recordset,"items":[_record(r) for r in page]},
        "options":{"categories":sorted({core._clean(r.get("Categoria")) for r in rows if core._clean(r.get("Categoria"))},key=str.casefold),"statuses":sorted({core._clean(r.get("StatusOperacional")) for r in rows if core._clean(r.get("StatusOperacional"))},key=str.casefold),"owners":sorted({_OWNER_BY_STATUS.get(core._clean(r.get("StatusOperacional")).upper(),"Indefinido") for r in rows},key=str.casefold),"macroprocesses":sorted({core._clean(r.get("Macroprocesso")) for r in rows if core._clean(r.get("Macroprocesso"))},key=str.casefold)},
        "indicator_coverage":INDICATOR_COVERAGE,
        "warnings":["Estoque e responsabilidade representam a posição atual da base.","KPI05 usa somente a fila interna SEPLAN como denominador.","Conclusão operacional e encerramento formal são métricas distintas.","O dataset público é sanitizado."]
    }

def health():
    rows=_rows()
    stock=[r for r in rows if _is_stock(r)]
    internal=[r for r in stock if _is_internal(r)]
    external=[r for r in stock if _is_external(r)]
    suspended=[r for r in stock if core._clean(r.get("StatusOperacional")).upper()=="SUSPENSO"]
    return {"status":"ok","service":"SEPLAN — Painel Executivo","dataset":core.metadata().get("dataset"),"source_updated_at":core.metadata().get("source_updated_at"),"audit":{"ok":True,"rows":len(rows),"unique_protocols":len({r["ProtocoloID"] for r in rows}),"stock":len(stock),"internal_queue":len(internal),"external_wait":len(external),"suspended":len(suspended)}}
