"""Camada L3 de análise baseada em IA.

Por enquanto, fornece apenas acesso ao histórico de
conversas salvo pela camada L2.
"""

from depths.core.lead_memory import load_history


class L3AI:
    """Interface simples para recuperação de histórico."""

    def get_history(self, lead_phone: str):
        """Retorna histórico de conversas do lead."""
        return load_history(lead_phone)
