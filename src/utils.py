import logging
from typing import Optional
from playwright.async_api import Page, TimeoutError as PlaywrightTimeout
from src.config import Config
from typing import Any, Callable

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
        
    async def _retry_evaluate(
        self,
        script: str,
        validate: Callable[[Any], bool],
        attempts: int = 5,
        interval_ms: int = 1000,
        log_tag: str = ""
    ) -> Any:
        """
        Ejecuta `script` en la página hasta que `validate(result)` sea True,
        esperando `interval_ms` milisegundos entre intentos, hasta `attempts` veces.
        Devuelve el resultado válido o None si no se logra.
        """
        for i in range(attempts):
            result = await self.evaluate(script)
            if validate(result):
                self.logger.info(f"✅ [{log_tag}] validado en intento {i+1}: {result}")
                return result
            self.logger.info(f"⏳ [{log_tag}] intento {i+1}/{attempts} sin éxito: {result}")
            await self.page.wait_for_timeout(interval_ms)
        self.logger.error(f"❌ [{log_tag}] fallo tras {attempts} intentos")
        return None

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

    async def select_by_text_in_frame(self, selector: str, text: str, description: str, timeout: int = 15000) -> bool:
        """Espera y selecciona un valor de dropdown por texto dentro del iframe."""
        self.logger.info(f"⏳ Esperando dropdown {description} en iframe...")
        try:
            el = self._frame.locator(selector)
            await el.wait_for(timeout=timeout)
            await el.select_option(label=text)
            # disparamos change
            await el.evaluate("e => e.dispatchEvent(new Event('change',{bubbles:true}))")
            self.logger.info(f"✅ {description} seleccionado: {text}")
            return True
        except Exception as e:
            self.logger.error(f"❌ select_by_text_in_frame('{selector}'): {e}")
            return False

    async def click_by_text_in_frame(self, text: str, description: str, timeout: int = 15000) -> bool:
        """Espera y hace clic en un elemento por texto exacto dentro del iframe."""
        self.logger.info(f"⏳ Esperando texto exacto '{text}' en iframe...")
        try:
            # Usar exact=True para coincidir exactamente con el texto
            el = self._frame.get_by_text(text, exact=True)
            await el.wait_for(timeout=timeout)
            await el.click()
            self.logger.info(f"✅ Clic en {description} exitoso!")
            return True
        except Exception as e:
            self.logger.error(f"❌ click_by_text_in_frame('{text}'): {e}")
            return False

    async def verify_element_value_in_frame(
        self, 
        selector: str, 
        description: str, 
        condition: str = "value_not_empty",
        attempts: int = 5,
        interval_ms: int = 1000,
        immediate_check: bool = True
    ) -> bool:
        """
        Verifica que un elemento dentro del iframe cumpla una condición específica.
        
        Args:
            selector (str): Selector CSS del elemento a verificar
            description (str): Descripción para logging
            condition (str): Tipo de condición - "value_not_empty", "has_method", "is_visible", etc.
            attempts (int): Número de intentos
            interval_ms (int): Intervalo entre intentos en ms
            immediate_check (bool): Si hacer verificación inmediata antes de retry
            
        Returns:
            bool: True si la verificación fue exitosa
        """
        self.logger.info(f"🔍 Verificando {description}...")
        
        # Script base que busca el elemento en iframe
        base_script = f"""
        (() => {{
            const iframe = document.querySelector('{self.IFRAME_SELECTOR}');
            if (!iframe) return null;
            const element = iframe.contentDocument.querySelector('{selector}');
            if (!element) return null;
        """
        
        # Diferentes condiciones de verificación
        if condition == "value_not_empty":
            condition_script = """
            if (element.value && element.value.trim() !== '' && element.value !== '0') {
                return element.value;
            }
            return null;
            """
        elif condition == "has_method_getValue":
            condition_script = """
            return {
                hasGetValue: typeof element.getValue === 'function',
                ready: element.offsetParent !== null
            };
            """
        elif condition == "is_visible":
            condition_script = """
            return element.offsetParent !== null;
            """
        else:
            # Condición personalizada
            condition_script = f"""
            {condition}
            """
        
        script = base_script + condition_script + "\n})();"
        
        # Verificación inmediata si está habilitada
        if immediate_check:
            immediate = await self.evaluate(script)
            if self._validate_verification_result(immediate, condition):
                self.logger.info(f"✅ {description} verificado inmediatamente: {immediate}")
                return True
        
        # Retry con _retry_evaluate
        result = await self._retry_evaluate(
            script,
            validate=lambda r: self._validate_verification_result(r, condition),
            attempts=attempts,
            interval_ms=interval_ms,
            log_tag=description
        )
        return bool(result)
    
    def _validate_verification_result(self, result, condition: str) -> bool:
        """Valida el resultado de la verificación según la condición."""
        if condition == "value_not_empty":
            return bool(result)
        elif condition == "has_method_getValue":
            return bool(result and result.get('hasGetValue') and result.get('ready'))
        elif condition == "is_visible":
            return bool(result)
        else:
            return bool(result)
