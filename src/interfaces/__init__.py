"""Interfaces para interactuar con el sistema."""

# Importación lazy para evitar problemas de dependencias circulares
def get_cli_interface():
    """Función lazy para obtener CLIInterface."""
    from .cli_interface import CLIInterface
    return CLIInterface

__all__ = ['get_cli_interface']
