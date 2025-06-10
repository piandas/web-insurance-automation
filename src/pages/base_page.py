from playwright.async_api import Page, TimeoutError as PlaywrightTimeout

class BasePage:
    """Clase base con métodos genéricos para interacciones con páginas."""
    
    def __init__(self, page: Page):
        self.page = page

    async def wait_for_element_with_text(self, text: str, timeout: int = 30000) -> bool:
        """Espera a que aparezca un elemento con el texto especificado."""
        print(f"⏳ Esperando texto '{text}' con timeout de {timeout/1000}s...")
        try:
            await self.page.wait_for_function(
                f"""
                () => {{
                    const txt = '{text.lower()}';
                    const check = (doc) => {{
                        for (const el of doc.querySelectorAll('*')) {{
                            if (el.textContent && el.textContent.toLowerCase().includes(txt) && el.offsetParent) {{
                                return true;
                            }}
                        }}
                        return false;
                    }};
                    const iframe = document.querySelector('iframe');
                    if (iframe?.contentDocument && check(iframe.contentDocument)) return true;
                    return check(document);
                }}
                """,
                timeout=timeout
            )
            print(f"✅ Texto '{text}' encontrado")
            return True
        except Exception as e:
            print(f"❌ Timeout esperando texto '{text}': {e}")
            return False

    async def wait_for_iframe_content(self, timeout: int = 30000) -> bool:
        """Espera a que aparezca contenido en el iframe."""
        print(f"⏳ Esperando contenido del iframe con timeout de {timeout/1000}s...")
        try:
            await self.page.wait_for_function(
                """
                () => {
                    const iframe = document.querySelector('iframe');
                    return iframe && iframe.contentDocument && iframe.contentDocument.body && iframe.contentDocument.body.children.length > 0;
                }
                """,
                timeout=timeout
            )
            print("✅ Contenido del iframe cargado")
            return True
        except Exception as e:
            print(f"❌ Timeout esperando contenido del iframe: {e}")
            return False

    async def wait_for_element_by_id_in_iframe(self, element_id: str, timeout: int = 30000) -> bool:
        """Espera a que aparezca un elemento específico por ID en el iframe."""
        print(f"⏳ Esperando elemento #{element_id} en iframe con timeout de {timeout/1000}s...")
        try:
            await self.page.wait_for_function(
                f"""
                () => {{
                    const iframe = document.querySelector('iframe');
                    if (!iframe?.contentDocument) return false;
                    const element = iframe.contentDocument.querySelector('#{element_id}');
                    return element && element.offsetParent;
                }}
                """,
                timeout=timeout
            )
            print(f"✅ Elemento #{element_id} encontrado en iframe")
            return True
        except Exception as e:
            print(f"❌ Timeout esperando elemento #{element_id} en iframe: {e}")
            return False

    async def evaluate_iframe(self, script: str) -> bool:
        """Ejecuta un script en el contexto de la página (para iframe o main)."""
        try:
            return await self.page.evaluate(script)
        except Exception as e:
            print(f"❌ Error en evaluate: {e}")
            return False

    async def click_with_js(self, script: str, success_msg: str) -> bool:
        """Ejecuta un bloque JS que intenta hacer clic y loggea."""
        clicked = await self.evaluate_iframe(script)
        if clicked:
            print(success_msg)
            return True
        return False

    async def wait_for_load_state_with_retry(self, state: str = "networkidle", timeout: int = 30000):
        """Espera a que la página cargue con reintentos."""
        try:
            await self.page.wait_for_load_state(state, timeout=timeout)
        except PlaywrightTimeout:
            print(f"⚠️ Timeout esperando estado '{state}', continuando...")

    async def safe_click(self, selector: str, timeout: int = 10000) -> bool:
        """Intenta hacer clic de forma segura con timeout."""
        try:
            await self.page.click(selector, timeout=timeout)
            return True
        except Exception as e:
            print(f"❌ Error haciendo clic en '{selector}': {e}")
            return False

    async def safe_fill(self, selector: str, value: str, timeout: int = 10000) -> bool:
        """Llena un campo de forma segura con timeout."""
        try:
            await self.page.fill(selector, value, timeout=timeout)
            return True
        except Exception as e:
            print(f"❌ Error llenando campo '{selector}': {e}")
            return False

    async def wait_for_selector_safe(self, selector: str, state: str = "visible", timeout: int = 15000) -> bool:
        """Espera un selector de forma segura."""
        print(f"⏳ Esperando selector '{selector}' con estado '{state}' por {timeout/1000}s...")
        try:
            await self.page.wait_for_selector(selector, state=state, timeout=timeout)
            print(f"✅ Selector '{selector}' encontrado")
            return True
        except Exception as e:
            print(f"❌ Error esperando selector '{selector}': {e}")
            return False

    async def is_visible_safe(self, selector: str, timeout: int = 5000) -> bool:
        """Verifica si un elemento es visible de forma segura."""
        try:
            return await self.page.is_visible(selector, timeout=timeout)
        except Exception:
            return False
