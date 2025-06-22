"""Página del dashboard específica para Allianz."""

import asyncio
from playwright.async_api import Page
from ....shared.base_page import BasePage

class DashboardPage(BasePage):
    """Página del dashboard con navegación a Flotas Autos en Allianz."""
    
    # Selectores
    NEW_POLICY_LINK = "#link_new_policy"
    MODAL_CONTENT = ".nx-modal__content-wrapper"
    AUTOS_EXPANSION_PANEL = 'nx-expansion-panel-header:has-text("Autos")'
    EXPANSION_CONTENT = '.nx-expansion-panel__content'
    BOX_SELECTOR = "app-box .box"
    
    def __init__(self, page: Page):
        super().__init__(page, 'allianz')

    async def navigate_to_flotas(self) -> bool:
        """Navega directamente a Flotas Autos y envía el formulario."""
        self.logger.info("🚗 Navegando a Flotas Autos en Allianz...")
        try:
            # Hacer clic en Nueva Póliza
            if not await self.safe_click(self.NEW_POLICY_LINK):
                self.logger.error("❌ Error haciendo clic en Nueva Póliza")
                return False
            
            # Esperar modal
            if not await self.wait_for_selector_safe(self.MODAL_CONTENT):
                self.logger.error("❌ Error esperando modal")
                return False
            
            # Expandir sección Autos
            if not await self.safe_click(self.AUTOS_EXPANSION_PANEL):
                self.logger.error("❌ Error expandiendo sección Autos")
                return False
            
            # Esperar contenido expandido
            if not await self.wait_for_selector_safe(self.EXPANSION_CONTENT):
                self.logger.error("❌ Error esperando contenido expandido")
                return False
            
            # Esperar las cajas de opciones
            if not await self.wait_for_selector_safe(self.BOX_SELECTOR):
                self.logger.error("❌ Error esperando cajas de opciones")
                return False
            
            # Hacer clic en Flotas Autos
            try:
                await self.page.get_by_text("Flotas Autos").click()
            except Exception as e:
                self.logger.error(f"❌ Error haciendo clic en Flotas Autos: {e}")
                return False

            self.logger.info("✅ Navegación a Flotas Autos exitosa")
            return True
            
        except Exception as e:
            self.logger.exception(f"❌ Error navegando a Flotas Autos: {e}")
            return False

    async def submit_application_form(self) -> bool:
        """Envía el formulario de aplicación si está presente."""
        self.logger.info("📋 Esperando formulario de Allianz y enviándolo...")
        
        try:
            # Esperar más tiempo y luego verificar si existe
            await asyncio.sleep(3)  # Espera adicional para que la página cargue
            
            if await self.is_visible_safe("#applicationForm", timeout=15000):
                await self.page.evaluate("document.querySelector('#applicationForm').submit()")
                self.logger.info("✅ Formulario de Allianz enviado")
                await self.wait_for_load_state_with_retry("networkidle")
                
                # Esperar a que aparezca contenido del iframe después del envío
                await self.wait_for_iframe_content()
                return True
            else:
                self.logger.warning("⚠️ Formulario de Allianz no encontrado, continuando...")
                # Esperar contenido del iframe de todas formas
                await self.wait_for_iframe_content()
                return True
        except Exception as e:
            self.logger.exception(f"❌ Error enviando formulario de Allianz: {e}")
            # Intentar esperar contenido del iframe de todas formas
            await self.wait_for_iframe_content()
            return False
