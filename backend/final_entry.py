from backend import core
from backend.final_data import load_rows

# Injeta a fonte reconciliada antes de carregar as métricas finais.
core.load_rows = load_rows

from backend.delivery_core import dashboard, health, query_from_params  # noqa: E402,F401
