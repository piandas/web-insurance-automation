"""Página de login específica para Allianz."""

from playwright.async_api import Page
from ....shared.base_page import BasePage
from ....config.allianz_config import AllianzConfig
from typing import Optional

class LoginPage(BasePage):
    """Página de login con sus selectores y métodos específicos para Allianz."""
    
    # Selectores
    USERNAME_INPUT = "input[name='username']"
    PASSWORD_INPUT = "input[name='password']"
    SUBMIT_BUTTON = "button[type='submit']"
    
    def __init__(self, page: Page):
        super().__init__(page, 'allianz')
        self.config = AllianzConfig()

    async def navigate_to_login(self):
        """Navega a la página de login."""
        self.logger.info("🌐 Navegando a página de login Allianz...")
        await self.page.goto(self.config.LOGIN_URL)

    async def login(self, usuario: str, contrasena: str) -> bool:
        """Realiza el proceso de login en Allianz."""
        self.logger.info("🔑 Iniciando login en Allianz...")
        try:
            await self.navigate_to_login()
            
            # Llenar campos
            if not await self.safe_fill(self.USERNAME_INPUT, usuario):
                self.logger.error("❌ Error llenando usuario")
                return False
                
            if not await self.safe_fill(self.PASSWORD_INPUT, contrasena):
                self.logger.error("❌ Error llenando contraseña")
                return False
            
            # Hacer clic en submit
            if not await self.safe_click(self.SUBMIT_BUTTON):
                self.logger.error("❌ Error haciendo clic en submit")
                return False
            
            # Esperar a que cargue
            await self.wait_for_load_state_with_retry("networkidle")
            self.logger.info("✅ Login en Allianz completado")
            return True
            
        except Exception as e:
            self.logger.exception(f"❌ Error en login Allianz: {e}")
            return False
