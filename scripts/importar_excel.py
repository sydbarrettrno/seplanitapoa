from __future__ import annotations

import argparse
import base64
import gzip
import hashlib
import json
import zipfile
from collections import Counter
from datetime import date, datetime, timedelta
from pathlib import Path
import xml.etree.ElementTree as ET

NS_MAIN = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
NS_REL = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
BASE_DATE = date(2025, 1, 1)

RAW_STATUS_MAP = {
    "Aberto": "Em tramitação",
    "Tramitando": "Em tramitação",
    "Em Análise": "Em análise técnica",
    "Paralisado": "Paralisado / revisar",
    "Encerrado": "Encerrado administrativo",
    "Arquivado": "Arquivado",
    "Cancelado": "Cancelado",
}

RAW_CATEGORY_MAP = {
    "2ª VIA DOCUMENTOS": ("2ª Via de Documentos", "Licenciamento de Obras"),
    "ALVARÁ DE AMPLIAÇÃO": ("Alvará de Ampliação", "Licenciamento de Obras"),
    "ALVARÁ DE CONSTRUÇÃO": ("Alvará de Construção", "Licenciamento de Obras"),
    "ALVARÁ DE DEMOLIÇÃO DE CONSTRUÇÃO": ("Alvará de Demolição", "Licenciamento de Obras"),
    "ALVARÁ DE REGULARIZAÇÃO": ("Alvará de Regularização", "Licenciamento de Obras"),
    "ALVARÁ MODIFICATIVO": ("Alvará Modificativo", "Licenciamento de Obras"),
    "CANCELAMENTO": ("Cancelamento", "Administrativo e Institucional"),
    "CDUI": ("CDUI", "Planejamento Urbano"),
    "CERTIDÃO DE DECADENCIA": ("Certidão de Decadência", "Certidões e Declarações"),
    "CERTIDÃO DE FINALIDADE URBANA": ("Certidão de Finalidade Urbana", "Certidões e Declarações"),
    "CERTIDÃO DE USO E OCUPAÇÃO DO SOLO": ("Certidão de Uso e Ocupação do Solo", "Certidões e Declarações"),
    "CERTIDÃO DE USO E OCUPAÇÃO DO SOLO nn": ("Certidão de Uso e Ocupação do Solo", "Certidões e Declarações"),
    "CERTIDÃO NARRATIVA": ("Certidão Narrativa", "Certidões e Declarações"),
    "COMUNICADO": ("Comunicado", "Administrativo e Institucional"),
    "CONFORME REQUERIMENTO": ("Diversos", "Administrativo e Institucional"),
    "COPIA DE DOCUMENTOS": ("2ª Via de Documentos", "Certidões e Declarações"),
    "DECLARAÇÃO NÃO OPOSIÇÃO": ("Declaração de Não Oposição", "Certidões e Declarações"),
    "DENUNCIA": ("Denúncia", "Fiscalização e Posturas"),
    "DESARQUIVAMENTO DE PROTOCOLO": ("Desarquivamento de Protocolo", "Administrativo e Institucional"),
    "DESDOBRO": ("Alvará de Desdobro", "Parcelamento do Solo"),
    "ENTREGA DE MEDIÇÕES ( OBRAS PUBLICAS )": ("Entrega de Medições - Obras Públicas", "Projetos e Obras Públicas"),
    "HABITE-SE": ("Habite-se", "Licenciamento de Obras"),
    "INDICAÇÃO DE VEREADOR (A)": ("Indicação de Vereador", "Administrativo e Institucional"),
    "ISENCAO ISS OBRA": ("Isenção de ISS-Obra", "Tributação da Construção"),
    "JUNTADA DE DOCUMENTOS": ("Juntada de Documentos", "Administrativo e Institucional"),
    "LARGURA DA CALÇADA/VIA": ("Largura da Calçada/Via", "Infraestrutura Urbana e Vias"),
    "PAVIMENTAÇÃO COMUNITÁRIA": ("Pavimentação Comunitária", "Infraestrutura Urbana e Vias"),
    "PEDIDO DE DESARQUIVAMENTO": ("Desarquivamento de Protocolo", "Administrativo e Institucional"),
    "PEDIDO DE VISTORIA": ("Pedido de Vistoria", "Fiscalização e Posturas"),
    "PROGRAMA ADOTE UMA PRAÇA - CPAP": ("Programa Adote uma Praça - CPAP", "Áreas Públicas e Uso do Espaço"),
    "PRORROGAÇÃO DE PRAZO": ("Prorrogação de Prazo", "Administrativo e Institucional"),
    "REBAIXAMENTO DE GUIA DA CALÇADA": ("Rebaixamento de Guia da Calçada", "Infraestrutura Urbana e Vias"),
    "RESSARCIMENTO": ("Ressarcimento", "Tributação da Construção"),
    "RETIFICAÇÃO DE AREA": ("Retificação de Área", "Parcelamento do Solo"),
    "REVISAO DE AREA CONSTRUIDA PARA FINS DE IPTU": ("Revisão de Área Construída para IPTU", "Cadastro e Cartografia"),
    "UNIFICAÇÃO": ("Alvará de Unificação", "Parcelamento do Solo"),
}

AMBIGUOUS_RAW = {
    "ALVARA ATENDIMENTO",
    "CERTIDÕES E DECLARAÇÕES",
    "DESDOBRO/UNIFICAÇÃO ATENDIMENTO",
    "DIVERSOS",
    "INFORMAÇÕES DIVERSAS",
}


def _col_index(ref: str) -> int:
    n = 0
    for ch in ref:
        if not ch.isalpha():
            break
        n = n * 26 + (ord(ch.upper()) - 64)
    return n - 1


def _sheet_rows(path: Path, sheet_name: str):
    with zipfile.ZipFile(path) as z:
        workbook = ET.fromstring(z.read("xl/workbook.xml"))
        rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
        relmap = {r.attrib["Id"]: r.attrib["Target"] for r in rels}
        targets = {}
        for sheet in workbook.find(NS_MAIN + "sheets"):
            targets[sheet.attrib["name"]] = relmap[sheet.attrib[NS_REL + "id"]]
        if sheet_name not in targets:
            raise RuntimeError(f"Aba obrigatória ausente: {sheet_name}")

        shared = []
        if "xl/sharedStrings.xml" in z.namelist():
            root = ET.fromstring(z.read("xl/sharedStrings.xml"))
            for item in root:
                shared.append("".join(t.text or "" for t in item.iter(NS_MAIN + "t")))

        target = targets[sheet_name]
        sheet_path = target if target.startswith("xl/") else "xl/" + target.lstrip("/")
        root = ET.fromstring(z.read(sheet_path))
        headers = {}
        for row_no, row in enumerate(root.findall(".//" + NS_MAIN + "sheetData/" + NS_MAIN + "row")):
            values = {}
            for cell in row.findall(NS_MAIN + "c"):
                idx = _col_index(cell.attrib.get("r", "A1"))
                cell_type = cell.attrib.get("t")
                node = cell.find(NS_MAIN + "v")
                value = "" if node is None else (node.text or "")
                if cell_type == "s" and value:
                    value = shared[int(value)]
                elif cell_type == "inlineStr":
                    inline = cell.find(NS_MAIN + "is")
                    value = "" if inline is None else "".join(t.text or "" for t in inline.iter(NS_MAIN + "t"))
                values[idx] = value
            if row_no == 0:
                headers = {name.strip(): idx for idx, name in values.items() if name.strip()}
                continue
            yield {name: values.get(idx, "") for name, idx in headers.items()}


def _excel_datetime(value) -> datetime | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        serial = float(text)
        return datetime(1899, 12, 30) + timedelta(days=serial)
    except ValueError:
        pass
    candidates = (
        "%d/%m/%Y %H:%M:%S",
        "%d/%m/%Y %H:%M",
        "%d/%m/%Y",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
    )
    for fmt in candidates:
        try:
            return datetime.strptime(text[:19], fmt)
        except ValueError:
            continue
    return None


def _protocol_parts(number_year: str) -> tuple[int, int] | None:
    text = str(number_year or "").strip()
    if "/" not in text:
        return None
    number_text, year_text = text.rsplit("/", 1)
    try:
        number = int(number_text.strip())
        year = int(year_text.strip())
    except ValueError:
        return None
    return number, year


def _load_classification(path: Path | None) -> dict[str, tuple[str, str, str]]:
    if not path:
        return {}
    out = {}
    for sheet_name in ("CLASSIFICADOS_100", "PARA_ANALISE"):
        for row in _sheet_rows(path, sheet_name):
            pid = str(row.get("ProtocoloID", "")).strip()
            category = str(row.get("Categoria Consolidada V08", "") or row.get("Categoria Final", "")).strip()
            macro = str(row.get("Macrogrupo Semântico V07", "")).strip()
            status = str(row.get("Status Anterior", "")).strip()
            if pid and category:
                out[pid] = (category, macro or "Outros / Revisar", status or "Em tramitação")
    return out


def _load_published_memory(repo_root: Path) -> dict[str, tuple[str, str, str]]:
    meta_path = repo_root / "data" / "metadata.json"
    if not meta_path.exists():
        return {}
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        artifact = meta.get("artifact", {})
        directory = repo_root / "data" / str(artifact.get("directory", "safe_chunks"))
        parts = artifact.get("parts", [])
        if not parts:
            return {}
        encoded = "".join((directory / name).read_text(encoding="ascii") for name in parts)
        payload = json.loads(gzip.decompress(base64.b64decode(encoded)).decode("utf-8"))
        d = payload["d"]
        c = payload["c"]
        out = {}
        count = len(c["n"])
        for i in range(count):
            year = 2025 + int(c["y"][i])
            number = int(c["n"][i])
            category = d["Categoria"][int(c["g"][i])]
            macro = d["Macroprocesso"][int(c["x"][i])]
            status = d["StatusOperacional"][int(c["t"][i])]
            out[f"{year}-{number}"] = (category, macro, status)
        return out
    except Exception:
        return {}


def _fallback_category(raw: str) -> tuple[str, str, bool]:
    raw = str(raw or "").strip()
    if raw in RAW_CATEGORY_MAP:
        cat, macro = RAW_CATEGORY_MAP[raw]
        return cat, macro, False
    if raw in AMBIGUOUS_RAW:
        label = raw.title() if raw else "Diversos"
        return label, "Outros / Revisar", True
    if not raw:
        return "Não identificado", "Outros / Revisar", True
    return raw.title(), "Outros / Revisar", True


def _dictionary(values: list[str]) -> tuple[list[str], dict[str, int]]:
    unique = sorted(set(values))
    return unique, {value: idx for idx, value in enumerate(unique)}


def build(raw_path: Path, repo_root: Path, classification_path: Path | None = None, chunk_size: int = 12000):
    classification = _load_published_memory(repo_root)
    classification.update(_load_classification(classification_path))

    records = []
    years = Counter()
    fallback_ids = []
    max_movement = None

    required = {
        "Número/Ano", "DataAbertura", "UltTramiteData", "Situação", "Categoria",
        "DataEncerramento", "CCAtual",
    }

    for row_no, row in enumerate(_sheet_rows(raw_path, "BASE23-26"), start=2):
        if row_no == 2:
            missing = sorted(required.difference(row.keys()))
            if missing:
                raise RuntimeError("Colunas obrigatórias ausentes: " + ", ".join(missing))
        parts = _protocol_parts(row.get("Número/Ano", ""))
        if not parts:
            continue
        number, year = parts
        if year < 2025:
            continue
        pid = f"{year}-{number}"
        memory_status = ""
        if pid in classification:
            category, macro, memory_status = classification[pid]
            fallback = False
        else:
            category, macro, fallback = _fallback_category(row.get("Categoria", ""))
        if fallback:
            fallback_ids.append(pid)

        opened = _excel_datetime(row.get("DataAbertura"))
        moved = _excel_datetime(row.get("UltTramiteData"))
        closed = _excel_datetime(row.get("DataEncerramento"))
        if opened is None:
            raise RuntimeError(f"Data de abertura inválida em {pid} (linha {row_no}).")
        if moved is None:
            moved = opened
        if moved < opened:
            raise RuntimeError(f"Último trâmite anterior à abertura em {pid}.")
        if closed is not None and closed < opened:
            raise RuntimeError(f"Encerramento anterior à abertura em {pid}.")
        if max_movement is None or moved > max_movement:
            max_movement = moved

        raw_status = str(row.get("Situação", "")).strip()
        raw_mapped_status = RAW_STATUS_MAP.get(raw_status, raw_status or "Em tramitação")
        if raw_status in {"Encerrado", "Arquivado", "Cancelado"}:
            status = raw_mapped_status
        else:
            status = memory_status or raw_mapped_status
        records.append({
            "number": number,
            "year": year,
            "opened": (opened.date() - BASE_DATE).days,
            "moved": (moved.date() - BASE_DATE).days,
            "closed": -1 if closed is None else (closed.date() - BASE_DATE).days,
            "macro": macro,
            "category": category,
            "status": status,
        })
        years[str(year)] += 1

    if not records:
        raise RuntimeError("Nenhum protocolo 2025+ encontrado no Excel.")
    ids = [f"{r['year']}-{r['number']}" for r in records]
    if len(ids) != len(set(ids)):
        raise RuntimeError("Protocolos duplicados no Excel 2025+; publicação bloqueada.")

    macros, macro_idx = _dictionary([r["macro"] for r in records])
    cats, cat_idx = _dictionary([r["category"] for r in records])
    statuses, status_idx = _dictionary([r["status"] for r in records])
    payload = {
        "v": 6,
        "d": {
            "Macroprocesso": macros,
            "Categoria": cats,
            "StatusOperacional": statuses,
        },
        "c": {
            "n": [r["number"] for r in records],
            "y": [r["year"] - 2025 for r in records],
            "o": [r["opened"] for r in records],
            "m": [r["moved"] for r in records],
            "c": [r["closed"] for r in records],
            "x": [macro_idx[r["macro"]] for r in records],
            "g": [cat_idx[r["category"]] for r in records],
            "t": [status_idx[r["status"]] for r in records],
        },
    }

    raw_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    compressed = gzip.compress(raw_json, compresslevel=9, mtime=0)
    encoded = base64.b64encode(compressed).decode("ascii")
    chunks = [encoded[i:i + chunk_size] for i in range(0, len(encoded), chunk_size)]
    part_names = [f"part-{i:03d}" for i in range(len(chunks))]

    data_dir = repo_root / "data"
    chunk_dir = data_dir / "safe_chunks"
    chunk_dir.mkdir(parents=True, exist_ok=True)
    for old in chunk_dir.iterdir():
        if old.is_file():
            old.unlink()
    for name, content in zip(part_names, chunks):
        (chunk_dir / name).write_text(content, encoding="ascii")

    source_updated = (max_movement or datetime.now()).strftime("%Y-%m-%d %H:%M:%S")
    default_year = (max_movement or datetime.now()).year
    meta = {
        "schema_version": 6,
        "dataset": "SEPLAN 2025+ — Excel como fonte oficial, visão pública sanitizada",
        "source_rows": len(records),
        "years": dict(sorted(years.items())),
        "source_updated_at": source_updated,
        "generated_from": [raw_path.name] + ([classification_path.name] if classification_path else []),
        "source_of_truth": {
            "type": "xlsx",
            "sheet": "BASE23-26",
            "note": "Os números do dashboard são regenerados a partir do Excel. O arquivo bruto não é publicado no repositório.",
        },
        "privacy": {
            "excluded_fields": [
                "Requerente", "CPF_CNPJ_REQUERENTE", "NomeRT", "CPF_CNPJ_RT",
                "ObsAbertura", "UltTramiteOBS", "UsuarioAtual",
            ],
            "note": "Dataset sanitizado para repositório público: não contém nomes, CPF/CNPJ nem observações livres.",
        },
        "default_period": {
            "from": f"{default_year}-01-01",
            "to": (max_movement or datetime.now()).date().isoformat(),
        },
        "default_threshold_days": 30,
        "import_audit": {
            "protocols_2025_plus": len(records),
            "classification_memory_hits": len(records) - len(fallback_ids),
            "new_or_unmapped": len(fallback_ids),
            "new_or_unmapped_protocols": fallback_ids[:100],
        },
        "artifact": {
            "storage": "gzip+base64-chunks",
            "format": "public-compact-v6",
            "gzip_bytes": len(compressed),
            "gzip_sha256": hashlib.sha256(compressed).hexdigest(),
            "date_encoding": "days since 2025-01-01; -1 = null",
            "note": "Transporte gerado automaticamente a partir do Excel; inclui apenas campos sanitizados.",
            "directory": "safe_chunks",
            "parts": part_names,
            "base64_chars": len(encoded),
        },
    }
    (data_dir / "metadata.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return meta


def main():
    parser = argparse.ArgumentParser(description="Importa BASE2326.xlsx e atualiza o transporte sanitizado do Dashboard SEPLAN.")
    parser.add_argument("excel", type=Path, help="Caminho do Excel bruto (aba BASE23-26).")
    parser.add_argument("--classificacao", type=Path, default=None, help="Excel consolidado opcional com CLASSIFICADOS_100/PARA_ANALISE.")
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1], help="Raiz do repositório seplanitapoa.")
    args = parser.parse_args()
    if not args.excel.exists():
        raise SystemExit(f"Excel não encontrado: {args.excel}")
    if args.classificacao and not args.classificacao.exists():
        raise SystemExit(f"Excel de classificação não encontrado: {args.classificacao}")
    meta = build(args.excel, args.repo, args.classificacao)
    print(json.dumps({
        "ok": True,
        "source_rows": meta["source_rows"],
        "source_updated_at": meta["source_updated_at"],
        "years": meta["years"],
        "audit": meta["import_audit"],
        "parts": len(meta["artifact"]["parts"]),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
