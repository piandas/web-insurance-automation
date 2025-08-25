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
        """Navega directamente a Flotas Autos y envía el formulario con reintentos."""
        self.logger.info("🚗 Navegando a Flotas Autos en Allianz...")
        try:
            # Hacer clic en Nueva Póliza con reintentos
            self.logger.info("🔘 Haciendo clic en 'Nueva Póliza'...")
            if not await self.safe_click(self.NEW_POLICY_LINK, timeout=15000, retries=3):
                self.logger.error("❌ Error haciendo clic en Nueva Póliza")
                return False
            
            self.logger.info("✅ Click en 'Nueva Póliza' exitoso")
            
            # Esperar modal con timeout más largo
            self.logger.info("⏳ Esperando modal...")
            if not await self.wait_for_selector_safe(self.MODAL_CONTENT, timeout=20000):
                self.logger.error("❌ Error esperando modal")
                return False
            
            # Pequeña pausa para estabilidad
            await asyncio.sleep(1)
            
            # Expandir sección Autos con reintentos
            self.logger.info("🔘 Expandiendo sección 'Autos'...")
            if not await self.safe_click(self.AUTOS_EXPANSION_PANEL, timeout=15000, retries=3):
                self.logger.error("❌ Error expandiendo sección Autos")
                return False
            
            # Esperar contenido expandido
            self.logger.info("⏳ Esperando contenido expandido...")
            if not await self.wait_for_selector_safe(self.EXPANSION_CONTENT, timeout=15000):
                self.logger.error("❌ Error esperando contenido expandido")
                return False
            
            # Esperar las cajas de opciones
            self.logger.info("⏳ Esperando cajas de opciones...")
            if not await self.wait_for_selector_safe(self.BOX_SELECTOR, timeout=15000):
                self.logger.error("❌ Error esperando cajas de opciones")
                return False
            
            # Hacer clic en Flotas Autos con reintentos
            self.logger.info("🔘 Haciendo clic en 'Flotas Autos'...")
            for attempt in range(1, 4):
                try:
                    if attempt > 1:
                        self.logger.info(f"🔄 Reintento {attempt}/3 - Clic en 'Flotas Autos'")
                        await asyncio.sleep(1)
                    
                    await self.page.get_by_text("Flotas Autos").click(timeout=10000)
                    self.logger.info("✅ Click en 'Flotas Autos' exitoso")
                    break
                except Exception as e:
                    if attempt == 3:
                        self.logger.error(f"❌ Error haciendo clic en Flotas Autos: {e}")
                        return False
                    else:
                        self.logger.warning(f"⚠️ Intento {attempt} falló para 'Flotas Autos': {e}")

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
