"""Página de login específica para Allianz."""

import asyncio
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
            
            # Hacer clic en submit con reintentos y verificación de sesión
            return await self._login_with_retry()
            
        except Exception as e:
            self.logger.exception(f"❌ Error en login Allianz: {e}")
            return False

    async def _login_with_retry(self) -> bool:
        """Hace clic en el botón de login con reintentos y verifica que la sesión se inicie."""
        self.logger.info("🔐 Iniciando proceso de login con verificación...")
        
        for attempt in range(1, 6):  # 5 intentos máximo
            try:
                if attempt > 1:
                    self.logger.info(f"🔄 Intento {attempt}/5 - Haciendo clic en 'Iniciar sesión'")
                    await asyncio.sleep(2)  # Esperar 2 segundos entre intentos
                else:
                    self.logger.info("🔐 Primer intento - Haciendo clic en 'Iniciar sesión'")
                
                # Hacer clic en el botón de submit
                if not await self.safe_click(self.SUBMIT_BUTTON):
                    self.logger.warning(f"⚠️ Intento {attempt}: No se pudo hacer clic en el botón")
                    continue
                
                # Verificar que el login fue exitoso
                if await self._verify_login_success():
                    self.logger.info(f"✅ Login exitoso en intento {attempt}")
                    return True
                else:
                    self.logger.warning(f"⚠️ Intento {attempt}: Login no completado, reintentando...")
                    continue
                    
            except Exception as e:
                self.logger.warning(f"⚠️ Error en intento {attempt}: {e}")
                if attempt == 5:
                    self.logger.error("❌ Todos los intentos de login fallaron")
                    return False
                continue
        
        self.logger.error("❌ No se pudo completar el login después de 5 intentos")
        return False

    async def _verify_login_success(self) -> bool:
        """Verifica que el login haya sido exitoso."""
        try:
            # Esperar a que cargue después del clic
            await asyncio.sleep(3)  # Tiempo para que procese el login
            
            # Verificar que la URL haya cambiado (indicando login exitoso)
            current_url = self.page.url
            
            # Si ya no está en la página de login, el login fue exitoso
            if "login" not in current_url.lower():
                self.logger.info("✅ Login verificado: URL cambió (ya no está en login)")
                return True
            
            # Verificar si aparecieron elementos del dashboard o página interna
            dashboard_selectors = [
                'nav', 'header', '.dashboard', '#dashboard', 
                '[class*="dashboard"]', '[class*="main"]', 
                '.menu', '#menu', '[class*="menu"]'
            ]
            
            for selector in dashboard_selectors:
                if await self.is_visible_safe(selector, timeout=2000):
                    self.logger.info(f"✅ Login verificado: Elemento del dashboard encontrado ({selector})")
                    return True
            
            # Verificar si desapareció el formulario de login
            login_form_visible = await self.is_visible_safe(self.SUBMIT_BUTTON, timeout=2000)
            if not login_form_visible:
                self.logger.info("✅ Login verificado: Formulario de login desapareció")
                return True
            
            self.logger.warning("⚠️ Login no verificado: Aún en página de login")
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Error verificando login: {e}")
            return False
