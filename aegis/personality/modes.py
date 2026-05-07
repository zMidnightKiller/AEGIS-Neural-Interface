"""
aegis/personality/modes.py

Define os modos de operação da AEGIS que ajustam a verbosidade e o comportamento.
"""
from enum import Enum


class OperatingMode(str, Enum):
    """
    Modos de operação que controlam como a AEGIS interage com o usuário.
    """
    STANDARD = "STANDARD"  # Equilibrado - padrão para a maioria das tarefas.
    BRIEFING = "BRIEFING"  # Ultra-conciso - apenas informações críticas.
    ANALYSIS = "ANALYSIS"  # Raciocínio estendido, chain-of-thought explícito.
    SILENT = "SILENT"      # Executa sem narração; apenas confirma a conclusão.
    VERBOSE = "VERBOSE"    # Narra cada passo em tempo real.
