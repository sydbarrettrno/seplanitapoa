"""Ajustes executivos de regra sem duplicar o motor principal.

V03: protocolos operacionalmente concluídos e apenas aguardando retirada
não compõem o estoque pendente. A produção formal (KPI02) continua sendo
calculada exclusivamente por DataEncerramento no backend.core.
"""
from backend import core

core.TERMINAL_STATUSES = {
    *core.TERMINAL_STATUSES,
    "APTO / AGUARDANDO RETIRADA",
}

# Mantém a implementação, auditoria e métricas centralizadas no core original.
dashboard = core.dashboard
health = core.health
query_from_params = core.query_from_params
