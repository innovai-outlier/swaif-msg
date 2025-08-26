# estoque/config.py
"""
Configurações globais do sistema de estoque.
"""

from estoque.domain.models import Params

# Caminho padrão do banco de dados SQLite
DB_PATH = "estoque.db"

# Valores padrão dos parâmetros globais
DEFAULTS = Params()

