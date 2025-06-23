"""Script de prueba para el flujo de navegación de Sura."""

import asyncio
import sys
import os

# Agregar la ruta del proyecto al path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from src.companies.sura.sura_automation import SuraAutomation

async def test_sura_navigation():
    """Prueba el flujo de navegación de Sura."""
    print("🧪 Iniciando prueba de navegación Sura...")
    
    automation = SuraAutomation()
    
    try:
        # Lanzar automatización
        if not await automation.launch():
            print("❌ Error al lanzar la automatización")
            return False
        
        print("✅ Automatización lanzada correctamente")
        
        # Ejecutar login
        if not await automation.execute_login_flow():
            print("❌ Error en el login")
            return False
        
        print("✅ Login exitoso")
        
        # Ejecutar navegación
        if not await automation.execute_navigation_flow():
            print("❌ Error en la navegación")
            return False
        
        print("✅ Navegación exitosa")
          # Ejecutar cotización
        print("💰 Iniciando flujo de cotización...")
        if not await automation.execute_quote_flow():
            print("❌ Error en el flujo de cotización")
            return False
        
        print("✅ Cotización exitosa - Se completó el proceso y navegó a la página de Clientes")
        print("🎉 ¡Prueba completada exitosamente!")
        
        # Mostrar URL final
        try:
            final_url = automation.page.url if automation.page else "No disponible"
            print(f"📍 URL final: {final_url}")
        except:
            print("📍 URL final: No disponible")
        
        # Esperar para revisar resultados
        print("⏳ Esperando 10 segundos para revisar...")
        await asyncio.sleep(10)
        
        return True
        
    except Exception as e:
        print(f"❌ Error durante la prueba: {e}")
        return False
    finally:
        await automation.close()

if __name__ == "__main__":
    result = asyncio.run(test_sura_navigation())
    sys.exit(0 if result else 1)
