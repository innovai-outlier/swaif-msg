# estoque/config.py
"""
Configurações gerais do sistema de estoque.
"""

from dataclasses import dataclass

# Path padrão do banco SQLite
DB_PATH = "data/estoque.db"

@dataclass
class DefaultConfig:
    """Configurações padrão do sistema."""
    nivel_servico: float = 0.95
    mu_t_dias_uteis: float = 7.0
    sigma_t_dias_uteis: float = 2.0

DEFAULTS = DefaultConfig()