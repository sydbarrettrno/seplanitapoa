from functools import lru_cache

from backend import core
from backend.final_data import load_rows as load_rows_base
from backend.taxonomy_v07 import apply_taxonomy_v07


@lru_cache(maxsize=1)
def load_rows():
    rows = [apply_taxonomy_v07(dict(row)) for row in load_rows_base()]
    categories = {core._clean(r.get("Categoria")) for r in rows}
    if len(rows) != 6975 or len(categories) != 42:
        raise RuntimeError("Carga bloqueada: taxonomia V07 não reconciliada.")
    return rows


# Injeta a fonte reconciliada + taxonomia V07 antes de calcular as métricas.
core.load_rows = load_rows

from backend.delivery_v07 import dashboard, health, query_from_params  # noqa: E402,F401
