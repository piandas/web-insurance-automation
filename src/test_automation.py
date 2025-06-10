"""
Script de prueba para verificar que la automatización modular funciona correctamente.
"""
import asyncio
import sys
import os

# Agregar el directorio actual al path para imports relativos
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from allianz_automation import AllianzAutomation
    print("✅ Imports exitosos - todas las clases cargadas correctamente")
    
    async def test_basic_functionality():
        """Prueba básica de funcionalidad sin ejecutar el flujo completo."""
        print("🧪 Iniciando prueba básica...")
        
        # Crear instancia
        automation = AllianzAutomation("test_user", "test_pass", headless=True)
        print("✅ Instancia creada correctamente")
        
        # Verificar que las páginas se pueden inicializar
        try:
            await automation.launch()
            print("✅ Navegador lanzado y páginas inicializadas")
            await automation.close()
            print("✅ Navegador cerrado correctamente")
            return True
        except Exception as e:
            print(f"❌ Error en prueba básica: {e}")
            return False
    
    # Ejecutar prueba
    if __name__ == "__main__":
        result = asyncio.run(test_basic_functionality())
        if result:
            print("🎉 ¡Prueba básica exitosa! La estructura modular funciona correctamente.")
            print("📝 Para ejecutar la automatización completa, ejecuta: python allianz_automation.py")
        else:
            print("❌ La prueba básica falló")
            
except ImportError as e:
    print(f"❌ Error de import: {e}")
    print("Verificando estructura de archivos...")
    
    # Verificar archivos
    import os
    current_dir = os.path.dirname(os.path.abspath(__file__))
    pages_dir = os.path.join(current_dir, 'pages')
    
    print(f"Directorio actual: {current_dir}")
    print(f"Directorio pages: {pages_dir}")
    
    if os.path.exists(pages_dir):
        print("✅ Directorio pages existe")
        files = os.listdir(pages_dir)
        print(f"Archivos en pages: {files}")
    else:
        print("❌ Directorio pages no existe")
