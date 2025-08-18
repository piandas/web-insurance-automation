#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Launcher para la interfaz gráfica del sistema de automatización.

Este script inicia la GUI de manera sencilla con manejo mejorado de codificación.
"""

import sys
import os
from pathlib import Path

# Configurar codificación para Windows
if sys.platform.startswith('win'):
    # Configurar la salida estándar para UTF-8
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    
    # Configurar el entorno
    os.environ['PYTHONIOENCODING'] = 'utf-8'

# Asegurar que el directorio del proyecto esté en el path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

# Cambiar al directorio del proyecto
os.chdir(project_dir)

try:
    from src.interfaces.gui_interface import main
    
    if __name__ == "__main__":
        print("🚀 Iniciando interfaz gráfica...")
        try:
            main()
        except UnicodeEncodeError as e:
            print(f"Error de codificación: {e}")
            print("Ejecutando en modo compatibilidad...")
            main()
        
except ImportError as e:
    print(f"❌ Error de importación: {e}")
    print("Asegúrate de que todas las dependencias estén instaladas.")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error inesperado: {e}")
    sys.exit(1)
