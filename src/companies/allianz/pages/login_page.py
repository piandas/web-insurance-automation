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
        """Navega a la página de login de Allianz o detecta si ya está logueado."""
        self.logger.info("🌐 Navegando a página de login Allianz...")
        await self.page.goto(self.config.LOGIN_URL)
        try:
            current_url = self.page.url
            # Si ya está logueado, Allianz redirige a un dashboard o página interna
            if "login" not in current_url and "allianz" in current_url:
                self.logger.info("✅ ¡Ya estás logueado! (sesión activa desde perfil persistente)")
                return True
            # Si no está logueado, esperar a que aparezcan los elementos de login
            self.logger.info("✅ Página de login Allianz cargada correctamente")
            return False
        except Exception as e:
            self.logger.exception(f"❌ Error navegando a login Allianz: {e}")
            return False

    async def login(self, usuario: str, contrasena: str) -> bool:
        """Realiza el proceso de login en Allianz, usando perfil persistente si es posible."""
        self.logger.info("🔑 Iniciando login en Allianz...")
        try:
            ya_logueado = await self.navigate_to_login()
            if ya_logueado:
                self.logger.info("🔓 Sesión Allianz ya iniciada, saltando login.")
                return True
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
