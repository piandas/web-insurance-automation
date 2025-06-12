import logging
from typing import Optional
from playwright.async_api import Page, TimeoutError as PlaywrightTimeout
from src.config import Config

class BasePage:
    """Clase base con métodos genéricos para interacciones con páginas."""
    IFRAME_SELECTOR: str = "iframe"

    def __init__(self, page: Page):
        self.page: Page = page
        self._frame = self.page.frame_locator(self.IFRAME_SELECTOR)
        self.logger = logging.getLogger('allianz')

    async def wait_for_element_with_text(self, text: str, timeout: Optional[int] = None) -> bool:
        """Espera un texto en el main o en el iframe."""
        lower = text.lower()
        timeout = timeout or Config.TIMEOUT
        self.logger.info(f"⏳ Esperando texto '{text}' (<= {timeout/1000}s)...")
        fn = f"""
        () => {{
            const t = '{lower}';
            const exists = doc => Array.from(doc.querySelectorAll('*'))
                .some(el => el.textContent?.toLowerCase().includes(t) && el.offsetParent);
            return exists(document) || (() => {{
                const f = document.querySelector('{self.IFRAME_SELECTOR}');
                return f?.contentDocument && exists(f.contentDocument);
            }})();
        }}"""
        try:
            await self.page.wait_for_function(fn, timeout=timeout)
            self.logger.info(f"✅ Texto '{text}' encontrado")
            return True
        except Exception as e:
            self.logger.error(f"❌ Timeout buscando texto '{text}': {e}")
            return False

    async def wait_for_iframe_content(self, timeout: Optional[int] = None) -> bool:
        """Espera a que el iframe tenga hijos en su body."""
        timeout = timeout or Config.TIMEOUT
        self.logger.info(f"⏳ Esperando contenido de iframe (<= {timeout/1000}s)...")
        try:
            await self.page.wait_for_function(
                f"() => document.querySelector('{self.IFRAME_SELECTOR}')?.contentDocument?.body?.children.length > 0",
                timeout=timeout
            )
            self.logger.info("✅ Contenido de iframe cargado")
            return True
        except Exception as e:
            self.logger.error(f"❌ Timeout cargando iframe: {e}")
            return False

    async def wait_for_element_by_id_in_iframe(self, element_id: str, timeout: Optional[int] = None) -> bool:
        """Espera un elemento por ID dentro del iframe."""
        timeout = timeout or Config.TIMEOUT
        sel = f"#{element_id}"
        self.logger.info(f"⏳ Esperando '{sel}' en iframe (<= {timeout/1000}s)...")
        try:
            await self.page.wait_for_function(
                f"() => !!document.querySelector('{self.IFRAME_SELECTOR}')"
                f"?.contentDocument.querySelector('{sel}')?.offsetParent",
                timeout=timeout
            )
            self.logger.info(f"✅ Elemento '{sel}' en iframe encontrado")
            return True
        except Exception as e:
            self.logger.error(f"❌ Timeout esperando '{sel}' en iframe: {e}")
            return False

    async def evaluate(self, script: str) -> bool:
        """Ejecuta un script en el contexto de la página."""
        try:
            return await self.page.evaluate(script)
        except Exception as e:
            self.logger.error(f"❌ Error evaluate(): {e}")
            return False

    async def click_with_js(self, script: str, success_msg: str) -> bool:
        """Click via JS y log."""
        if await self.evaluate(script):
            self.logger.info(success_msg)
            return True
        return False

    async def wait_for_load_state_with_retry(self, state: str = "networkidle", timeout: int = 30000):
        """Espera load_state con retry silencioso."""
        try:
            await self.page.wait_for_load_state(state, timeout=timeout)
        except PlaywrightTimeout:
            self.logger.warning(f"⚠️ Timeout load_state='{state}', continuando...")

    async def safe_click(self, selector: str, timeout: int = 10000) -> bool:
        """Click normal con manejo de error."""
        try:
            await self.page.click(selector, timeout=timeout)
            return True
        except Exception as e:
            self.logger.error(f"❌ safe_click('{selector}'): {e}")
            return False

    async def safe_fill(self, selector: str, value: str, timeout: int = 10000) -> bool:
        """Fill normal con manejo de error."""
        try:
            await self.page.fill(selector, value, timeout=timeout)
            return True
        except Exception as e:
            self.logger.error(f"❌ safe_fill('{selector}'): {e}")
            return False

    async def wait_for_selector_safe(self, selector: str, state: str = "visible", timeout: int = 15000) -> bool:
        """Wait for selector con manejo de error."""
        self.logger.info(f"⏳ Esperando selector '{selector}' ({state}) <={timeout/1000}s...")
        try:
            await self.page.wait_for_selector(selector, state=state, timeout=timeout)
            self.logger.info(f"✅ Selector '{selector}' {state}")
            return True
        except Exception as e:
            self.logger.error(f"❌ wait_for_selector_safe('{selector}'): {e}")
            return False

    async def is_visible_safe(self, selector: str, timeout: int = 5000) -> bool:
        """Comprueba visibilidad con manejo de error."""
        try:
            return await self.page.is_visible(selector, timeout=timeout)
        except Exception:
            return False

    # ————————————————
    # Métodos genéricos para iframe:
    # ————————————————

    async def click_in_frame(self, selector: str, description: str, timeout: int = 15000) -> bool:
        """Espera y hace clic en un selector dentro del iframe."""
        self.logger.info(f"⏳ Esperando {description} en iframe...")
        try:
            el = self._frame.locator(selector)
            await el.wait_for(timeout=timeout)
            await el.click()
            self.logger.info(f"✅ Clic en {description} exitoso!")
            return True
        except Exception as e:
            self.logger.error(f"❌ click_in_frame('{selector}'): {e}")
            return False

    async def fill_in_frame(self, selector: str, value: str, description: str, timeout: int = 15000) -> bool:
        """Espera y rellena un input dentro del iframe."""
        self.logger.info(f"⏳ Esperando campo {description} en iframe...")
        try:
            el = self._frame.locator(selector)
            await el.wait_for(timeout=timeout)
            await el.fill(value)
            self.logger.info(f"✅ Campo {description} = '{value}'")
            return True
        except Exception as e:
            self.logger.error(f"❌ fill_in_frame('{selector}'): {e}")
            return False

    async def select_in_frame(self, selector: str, value: str, description: str, timeout: int = 15000) -> bool:
        """Espera y selecciona un valor de dropdown dentro del iframe."""
        self.logger.info(f"⏳ Esperando dropdown {description} en iframe...")
        try:
            el = self._frame.locator(selector)
            await el.wait_for(timeout=timeout)
            await el.select_option(value)
            # disparamos change
            await el.evaluate("e => e.dispatchEvent(new Event('change',{bubbles:true}))")
            self.logger.info(f"✅ {description} seleccionado: {value}")
            return True
        except Exception as e:
            self.logger.error(f"❌ select_in_frame('{selector}'): {e}")
            return False
