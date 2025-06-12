from playwright.async_api import Page
from src.utils import BasePage
from src.config import Config
import logging
from typing import Optional

class LoginPage(BasePage):
    """Página de login con sus selectores y métodos específicos."""
    
    # URLs
    LOGIN_URL: str = Config.BASE_URL + "/ngx-epac/private/home"
    
    # Selectores
    USERNAME_INPUT = "input[name='username']"
    PASSWORD_INPUT = "input[name='password']"
    SUBMIT_BUTTON = "button[type='submit']"
    
    def __init__(self, page: Page):
        super().__init__(page)
        self.logger = logging.getLogger('allianz')

    async def navigate_to_login(self):
        """Navega a la página de login."""
        self.logger.info("🌐 Navegando a página de login...")
        await self.page.goto(self.LOGIN_URL)

    async def login(self, usuario: str, contrasena: str) -> bool:
        """Realiza el proceso de login."""
        self.logger.info("🔑 Iniciando login...")
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
            self.logger.info("✅ Login completado")
            return True
            
        except Exception as e:
            self.logger.exception(f"❌ Error en login: {e}")
            return False
