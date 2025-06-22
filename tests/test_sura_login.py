"""Script de prueba para el login de Sura."""

import asyncio
import os
import sys
from pathlib import Path

# Agregar el directorio raíz del proyecto al path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.companies.sura.sura_automation import SuraAutomation

async def test_sura_login():
    """Prueba el login de Sura."""
    print("🚀 Iniciando prueba de login Sura...")
    
    # Verificar que las variables de entorno estén configuradas
    usuario = os.getenv('SURA_USUARIO')
    contrasena = os.getenv('SURA_CONTRASENA')
    
    if not usuario or not contrasena:
        print("❌ Error: Credenciales de Sura no configuradas en .env")
        print("   Asegúrate de tener SURA_USUARIO y SURA_CONTRASENA en tu archivo .env")
        return False
    
    print(f"✅ Credenciales encontradas para usuario: {usuario}")
    
    # Crear automatización
    automation = SuraAutomation(headless=False)  # No headless para poder ver
    
    try:
        # Lanzar navegador
        await automation.launch()
        print("✅ Navegador lanzado")
        
        # Probar solo el login
        login_success = await automation.execute_login_flow()
        
        if login_success:
            print("🎉 ¡LOGIN DE SURA EXITOSO!")
            print("⏸️ Esperando 10 segundos para revisar...")
            await asyncio.sleep(10)
        else:
            print("❌ Login de Sura falló")
            
        return login_success
        
    except Exception as e:
        print(f"❌ Error en prueba: {e}")
        return False
    finally:
        await automation.close()
        print("🔚 Navegador cerrado")

if __name__ == "__main__":
    result = asyncio.run(test_sura_login())
    if result:
        print("\n✅ PRUEBA EXITOSA")
    else:
        print("\n❌ PRUEBA FALLÓ")
