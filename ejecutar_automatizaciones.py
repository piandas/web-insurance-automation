#!/usr/bin/env python
"""
Script principal para ejecutar automatizaciones de cotizaciones.

Este script evita problemas de importación de módulos y proporciona
una interfaz directa para ejecutar las automatizaciones.
"""

import sys
import os
import asyncio
from pathlib import Path

# Asegurar que el directorio del proyecto esté en el path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

# Cambiar al directorio del proyecto
os.chdir(project_dir)

# Importar después de configurar el path
from src.interfaces.cli_interface import CLIInterface


async def main():
    """Función principal asíncrona."""
    try:
        cli = CLIInterface()
        exit_code = await cli.run()
        return exit_code
    except Exception as e:
        print(f"❌ Error crítico: {e}")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⚠️ Proceso interrumpido por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error fatal: {e}")
        sys.exit(1)
