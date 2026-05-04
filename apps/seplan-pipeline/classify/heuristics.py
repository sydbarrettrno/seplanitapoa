from __future__ import annotations

from typing import Any

TAXONOMY = {
    "prancha_arquitetonica", "planta_baixa", "implantacao", "corte", "fachada",
    "cobertura", "quadro_areas", "sistema_esgoto", "memorial", "art_rrt",
    "matricula", "documento_administrativo", "correcao_resposta", "planilha",
    "imagem", "dxf", "svg", "json", "texto", "artefato_dados", "outro", "desconhecido",
}

NAME_RULES: list[tuple[str, tuple[str, ...], float]] = [
    ("art_rrt", ("art", "rrt", "anotacao de responsabilidade tecnica", "registro de responsabilidade tecnica"), 0.95),
    ("matricula", ("matricula", "matrícula", "registro de imovel", "registro de imóvel"), 0.90),
    ("memorial", ("memorial", "descritivo"), 0.90),
    ("implantacao", ("implantacao", "implantação", "situacao", "situação", "locacao", "locação"), 0.88),
    ("planta_baixa", ("planta baixa", "planta_baixa", "pavimento", "layout"), 0.86),
    ("corte", ("corte", "seção", "secao"), 0.85),
    ("fachada", ("fachada", "elevação", "elevacao"), 0.85),
    ("cobertura", ("cobertura", "telhado"), 0.85),
    ("quadro_areas", ("quadro de areas", "quadro de áreas", "areas", "áreas"), 0.82),
    ("sistema_esgoto", ("esgoto", "sanitario", "sanitário", "fossa", "sumidouro", "caixa de gordura"), 0.84),
    ("correcao_resposta", ("correcao", "correção", "resposta", "adequacao", "adequação"), 0.80),
    ("prancha_arquitetonica", ("prancha", "arquitetonico", "arquitetônico", "arquitetura"), 0.82),
    ("documento_administrativo", ("protocolo", "requerimento", "alvara", "alvará", "oficio", "ofício"), 0.78),
]


def normalize(text: str) -> str:
    return text.lower().replace("-", " ").replace("_", " ").replace(".", " ")


def classify_document(file_item: dict[str, Any]) -> dict[str, Any]:
    extension = str(file_item.get("extension") or "").lower()
    name = normalize(f"{file_item.get('file_name', '')} {file_item.get('relative_path', '')}")
    extension_map = {
        ".xls": ("planilha", 0.90, "extensão indica planilha"),
        ".xlsx": ("planilha", 0.90, "extensão indica planilha"),
        ".csv": ("planilha", 0.86, "extensão indica tabela CSV"),
        ".ods": ("planilha", 0.86, "extensão indica planilha"),
        ".jpg": ("imagem", 0.88, "extensão indica imagem"),
        ".jpeg": ("imagem", 0.88, "extensão indica imagem"),
        ".png": ("imagem", 0.88, "extensão indica imagem"),
        ".tif": ("imagem", 0.86, "extensão indica imagem"),
        ".tiff": ("imagem", 0.86, "extensão indica imagem"),
        ".webp": ("imagem", 0.84, "extensão indica imagem"),
        ".bmp": ("imagem", 0.84, "extensão indica imagem"),
        ".dxf": ("dxf", 0.95, "extensão é .dxf"),
        ".svg": ("svg", 0.95, "extensão é .svg"),
        ".json": ("json", 0.92, "extensão é .json"),
        ".txt": ("texto", 0.86, "extensão indica texto"),
        ".md": ("texto", 0.86, "extensão indica texto"),
    }
    class_name, confidence, evidence = extension_map.get(
        extension,
        ("desconhecido", 0.25, "nome e extensão não acionaram heurística suficiente"),
    )
    for candidate_class, terms, score in NAME_RULES:
        matched = next((term for term in terms if term in name), None)
        if matched and score >= confidence:
            class_name = candidate_class
            confidence = score
            evidence = f"nome contém '{matched}'"
            if extension:
                evidence = f"{evidence} e extensão é {extension}"
            break
    if extension == ".pdf" and class_name == "desconhecido":
        class_name = "outro"
        confidence = 0.45
        evidence = "extensão é .pdf, mas o nome não indica classe documental específica"
    needs_review = confidence < 0.70 or class_name in {"desconhecido", "outro"}
    return {
        "file_name": file_item.get("file_name"),
        "relative_path": file_item.get("relative_path"),
        "extension": extension,
        "class": class_name if class_name in TAXONOMY else "desconhecido",
        "confidence": round(float(confidence), 2),
        "evidence": evidence,
        "needs_review": bool(needs_review),
    }


def classify_inventory(inventory: dict[str, Any], generated_at: str) -> dict[str, Any]:
    return {
        "run_id": inventory["run_id"],
        "generated_at": generated_at,
        "documents": [classify_document(item) for item in inventory.get("files", [])],
    }
