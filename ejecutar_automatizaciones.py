#!/usr/bin/env python
"""
Script principal para ejecutar automatizaciones de cotizaciones.

Este script evita problemas de importación de módulos y proporciona
una interfaz directa para ejecutar las automatizaciones.

ejecutar_automatizaciones.py --companies allianz sura --parallel
"""

import sys
import os
import asyncio
import subprocess
from pathlib import Path

def get_venv_python():
    """Obtiene la ruta del Python del entorno virtual."""
    project_dir = Path(__file__).parent
    venv_python = project_dir / ".venv" / "Scripts" / "python.exe"
    
    if venv_python.exists():
        return str(venv_python)
    return None

def restart_with_venv():
    """Reinicia el script usando el Python del entorno virtual."""
    venv_python = get_venv_python()
    if venv_python and sys.executable != venv_python:
        print("🔄 Reiniciando con entorno virtual...")
        # Ejecutar este mismo script con el Python del entorno virtual
        subprocess.run([venv_python] + [__file__] + sys.argv[1:])
        return True
    return False

# Verificar si necesita reiniciar con entorno virtual
if restart_with_venv():
    sys.exit(0)

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
