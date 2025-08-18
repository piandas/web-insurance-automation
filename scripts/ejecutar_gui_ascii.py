#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Launcher alternativo para la interfaz gráfica (modo compatibilidad ASCII).

Este script evita problemas de codificación Unicode en Windows.
"""

import sys
import os
from pathlib import Path

# Configurar para evitar problemas de Unicode
os.environ['PYTHONIOENCODING'] = 'ascii:replace'

# Asegurar que el directorio del proyecto esté en el path
project_dir = Path(__file__).parent.parent  # Subir un nivel desde scripts/ a la raíz
sys.path.insert(0, str(project_dir))

# Cambiar al directorio del proyecto
os.chdir(project_dir)

try:
    from src.interfaces.gui_interface import main
    
    if __name__ == "__main__":
        print("[START] Iniciando interfaz grafica...")
        try:
            main()
        except Exception as e:
            print(f"[ERROR] Error inesperado: {e}")
            sys.exit(1)
        
except ImportError as e:
    print(f"[ERROR] Error de importacion: {e}")
    print("Asegurate de que todas las dependencias esten instaladas.")
    sys.exit(1)
except Exception as e:
    print(f"[ERROR] Error inesperado: {e}")
    sys.exit(1)
