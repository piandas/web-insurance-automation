import asyncio
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

from pages import LoginPage, DashboardPage, FlotasPage

class AllianzAutomation:
    """Clase principal que orquesta todo el flujo de automatización de Allianz."""
    
    def __init__(self, usuario: str, contrasena: str, headless: bool = False):
        self.usuario = usuario
        self.contrasena = contrasena
        self.headless = headless
        self.browser = None
        self.page = None
        self.playwright = None
        
        # Páginas
        self.login_page = None
        self.dashboard_page = None
        self.flotas_page = None

    async def launch(self):
        """Inicializa Playwright y abre el navegador."""
        print("🚀 Lanzando navegador...")
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=self.headless)
        self.page = await self.browser.new_page()
        
        # Inicializar páginas
        self.login_page = LoginPage(self.page)
        self.dashboard_page = DashboardPage(self.page)
        self.flotas_page = FlotasPage(self.page)
        
        print("✅ Navegador lanzado y páginas inicializadas")

    async def execute_login_flow(self) -> bool:
        """Ejecuta el flujo de login."""
        print("🔐 Ejecutando flujo de login...")
        return await self.login_page.login(self.usuario, self.contrasena)

    async def execute_navigation_flow(self) -> bool:
        """Ejecuta el flujo de navegación al dashboard y flotas."""
        print("🧭 Ejecutando flujo de navegación...")
        
        # Navegar a flotas
        if not await self.dashboard_page.navigate_to_flotas():
            print("❌ Error navegando a flotas")
            return False
        
        # Enviar formulario si existe
        await self.dashboard_page.submit_application_form()
        return True

    async def execute_flotas_flow(self) -> bool:
        """Ejecuta el flujo específico de flotas."""
        print("🚗 Ejecutando flujo de flotas...")
        return await self.flotas_page.execute_flotas_flow()

    async def run_complete_flow(self) -> bool:
        """Ejecuta el flujo completo de automatización."""
        print("🎬 Iniciando flujo completo de automatización...")
        
        try:
            # Paso 1: Login
            if not await self.execute_login_flow():
                print("❌ Falló el flujo de login")
                return False

            # Paso 2: Navegación
            if not await self.execute_navigation_flow():
                print("❌ Falló el flujo de navegación")
                return False

            # Paso 3: Flujo de flotas
            if not await self.execute_flotas_flow():
                print("❌ Falló el flujo de flotas")
                return False

            print("🎉 ¡PROCESO COMPLETO EJECUTADO EXITOSAMENTE!")
            return True

        except Exception as e:
            print(f"❌ Error en flujo completo: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def close(self):
        """Cierra el navegador y limpia recursos."""
        print("🔒 Cerrando navegador...")
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        print("✅ Recursos liberados")

async def main():
    """Función principal para ejecutar la automatización."""
    print("🚀 Iniciando automatización Allianz optimizada y modular...")
    
    # Configuración
    usuario = "CA031800"
    contrasena = "Agenciainfondo**"
    headless = False
    
    # Crear instancia de automatización
    automation = AllianzAutomation(usuario, contrasena, headless)

    try:
        # Lanzar navegador
        await automation.launch()

        # Ejecutar flujo completo
        success = await automation.run_complete_flow()
        
        if success:
            print("✅ ¡AUTOMATIZACIÓN COMPLETADA!")
            # Espera para revisar resultados
            print("⏱️ Esperando 15 segundos para revisión...")
            await asyncio.sleep(15)
        else:
            print("❌ La automatización falló")
            await asyncio.sleep(15)

    except Exception as e:
        print(f"❌ Error general: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Siempre cerrar el navegador
        await automation.close()
        print("✅ Proceso terminado")

if __name__ == "__main__":
    asyncio.run(main())
