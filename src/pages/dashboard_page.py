import asyncio
from playwright.async_api import Page, TimeoutError as PlaywrightTimeout
from .base_page import BasePage

class DashboardPage(BasePage):
    """Página del dashboard con navegación a Flotas Autos."""
    
    # Selectores
    NEW_POLICY_LINK = "#link_new_policy"
    MODAL_CONTENT = ".nx-modal__content-wrapper"
    AUTOS_EXPANSION_PANEL = 'nx-expansion-panel-header:has-text("Autos")'
    EXPANSION_CONTENT = '.nx-expansion-panel__content'
    BOX_SELECTOR = "app-box .box"
    
    def __init__(self, page: Page):
        super().__init__(page)

    async def navigate_to_flotas(self) -> bool:
        """Navega directamente a Flotas Autos y envía el formulario."""
        print("🚗 Navegando a Flotas Autos...")
        
        try:
            # Hacer clic en Nueva Póliza
            if not await self.safe_click(self.NEW_POLICY_LINK):
                print("❌ Error haciendo clic en Nueva Póliza")
                return False
            
            # Esperar modal
            if not await self.wait_for_selector_safe(self.MODAL_CONTENT):
                print("❌ Error esperando modal")
                return False
            
            # Expandir sección Autos
            if not await self.safe_click(self.AUTOS_EXPANSION_PANEL):
                print("❌ Error expandiendo sección Autos")
                return False
            
            # Esperar contenido expandido
            if not await self.wait_for_selector_safe(self.EXPANSION_CONTENT):
                print("❌ Error esperando contenido expandido")
                return False
            
            # Esperar las cajas de opciones
            if not await self.wait_for_selector_safe(self.BOX_SELECTOR):
                print("❌ Error esperando cajas de opciones")
                return False
            
            # Hacer clic en Flotas Autos
            try:
                await self.page.get_by_text("Flotas Autos").click()
            except Exception as e:
                print(f"❌ Error haciendo clic en Flotas Autos: {e}")
                return False

            # Esperar navegación
            try:
                await self.page.wait_for_url("**/application**", timeout=30_000)
                print(f"✅ Navegación exitosa a: {self.page.url}")
            except PlaywrightTimeout:
                print(f"⚠️ URL actual: {self.page.url}")

            await self.wait_for_load_state_with_retry("networkidle")
            return True
            
        except Exception as e:
            print(f"❌ Error en navegación a flotas: {e}")
            return False

    async def submit_application_form(self) -> bool:
        """Envía el formulario de aplicación si está presente."""
        print("📋 Esperando formulario y enviándolo...")
        
        try:
            # Esperar más tiempo y luego verificar si existe
            await asyncio.sleep(3)  # Espera adicional para que la página cargue
            
            if await self.is_visible_safe("#applicationForm", timeout=15000):
                await self.page.evaluate("document.querySelector('#applicationForm').submit()")
                print("✅ Formulario enviado")
                await self.wait_for_load_state_with_retry("networkidle")
                
                # Esperar a que aparezca contenido del iframe después del envío
                await self.wait_for_iframe_content()
                return True
            else:
                print("⚠️ Formulario no encontrado, continuando...")
                # Esperar contenido del iframe de todas formas
                await self.wait_for_iframe_content()
                return True
        except Exception as e:
            print(f"❌ Error enviando formulario: {e}")
            # Intentar esperar contenido del iframe de todas formas
            await self.wait_for_iframe_content()
            return False
