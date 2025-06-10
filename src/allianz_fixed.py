# filepath: c:\Users\santi\OneDrive\Escritorio\PROYECTOS\AGENCIA INFONDO\COTIZACIONES\MCP\src\allianz_fixed.py
import asyncio
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

class AllianzAutomation:
    def __init__(self, usuario: str, contrasena: str, headless: bool = False):
        self.usuario = usuario
        self.contrasena = contrasena
        self.headless = headless
        self.browser = None
        self.page = None
        self.playwright = None

    async def launch(self):
        """Inicializa Playwright y abre el navegador."""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=self.headless)
        self.page = await self.browser.new_page()

    async def login(self):
        """Login en Allianz."""
        print("🔑 Iniciando login...")
        await self.page.goto("https://www.allia2net.com.co/ngx-epac/private/home")
        await self.page.fill("input[name='username']", self.usuario)
        await self.page.fill("input[name='password']", self.contrasena)
        await self.page.click("button[type='submit']")
        await self.page.wait_for_load_state("networkidle")
        print("✅ Login completado")

    async def navigate_to_flotas(self):
        """Navega directamente a Flotas Autos y envía el formulario."""
        print("🚗 Navegando a Flotas Autos...")
        await self.page.click("#link_new_policy")
        await self.page.wait_for_selector(".nx-modal__content-wrapper", state="visible")
        await self.page.click('nx-expansion-panel-header:has-text("Autos")')
        await self.page.wait_for_selector('.nx-expansion-panel__content', state="visible")
        await self.page.wait_for_selector("app-box .box", state="visible")
        await self.page.get_by_text("Flotas Autos").click()

        try:
            await self.page.wait_for_url("**/application**", timeout=30_000)
            print(f"✅ Navegación exitosa a: {self.page.url}")
        except PlaywrightTimeout:
            print(f"⚠️ URL actual: {self.page.url}")

        await self.page.wait_for_load_state("networkidle")

        print("📋 Esperando formulario y enviándolo...")
        if await self.page.is_visible("#applicationForm", timeout=10000):
            await self.page.evaluate("document.querySelector('#applicationForm').submit()")
            print("✅ Formulario enviado")
            await self.page.wait_for_load_state("networkidle")
        else:
            print("⚠️ Formulario no encontrado")

    async def _wait_for_element_with_text(self, text: str, timeout: int = 20000) -> bool:
        """Espera a que aparezca un elemento con el texto especificado."""
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
            return True
        except Exception as e:
            print(f"❌ Timeout esperando texto '{text}': {e}")
            return False

    async def _evaluate_iframe(self, script: str) -> bool:
        """Ejecuta un script en el contexto de la página (para iframe o main)."""
        try:
            return await self.page.evaluate(script)
        except Exception as e:
            print(f"❌ Error en evaluate: {e}")
            return False

    async def _click_with_js(self, script: str, success_msg: str) -> bool:
        """Ejecuta un bloque JS que intenta hacer clic y loggea."""
        clicked = await self._evaluate_iframe(script)
        if clicked:
            print(success_msg)
            return True
        return False

    async def click_cell_23541048(self):
        """Busca y hace clic en la celda con número 23541048."""
        print("🎯 Buscando celda 23541048...")

        # 1) Intento en iframe usando JS
        iframe_script = """
            (function() {
                const iframe = document.querySelector('iframe');
                if (!iframe?.contentDocument) return false;
                const el = iframe.contentDocument.querySelector('#tableFlotas_7_1');
                if (el?.textContent.includes('23541048')) { el.click(); return true; }
                return false;
            })();
        """
        if await self._click_with_js(iframe_script, "✅ ¡Clic exitoso en iframe!"):
            return True

        # 2) ID directo
        try:
            el = await self.page.query_selector("#tableFlotas_7_1")
            if el and "23541048" in (await el.text_content()):
                await el.click()
                print("✅ ¡Clic exitoso por ID!")
                return True
        except Exception as e:
            print(f"❌ Error por ID: {e}")

        print("❌ No se encontró la celda 23541048")
        return False

    async def click_livianos_particulares(self):
        """Busca y hace clic en 'Livianos Particulares' con espera inteligente."""
        print("🔍 Buscando 'Livianos Particulares'...")
        # Espera inteligente hasta que aparezca el texto
        await self._wait_for_element_with_text("livianos particulares")

        # 1) Intentar en iframe
        iframe_script = """
            (function() {
                const iframe = document.querySelector('iframe');
                const doc = iframe?.contentDocument;
                if (!doc) return false;
                const sels = ['a','button','input[type="button"]','input[type="submit"]','[onclick]'];
                for (let sel of sels) {
                    for (let el of doc.querySelectorAll(sel)) {
                        const tx = (el.textContent||el.value||'').toLowerCase();
                        if (tx.includes('livianos particulares')) { el.click(); return true; }
                    }
                }
                return false;
            })();
        """
        if await self._click_with_js(iframe_script, "✅ ¡Clic exitoso en Livianos Particulares (iframe)!"):
            return True

        # 2) Playwright locator
        try:
            locator = self.page.locator("text=\"Livianos Particulares\"").first
            if await locator.is_visible():
                await locator.click()
                print("✅ ¡Clic exitoso con locator!")
                return True
        except Exception as e:
            print(f"❌ Error con locator: {e}")

        print("❌ No se encontró 'Livianos Particulares'")
        return False

    async def click_aceptar(self):
        """Busca y hace clic en el botón 'Aceptar' después de seleccionar Livianos Particulares."""
        print("🔍 Esperando botón 'Aceptar'...")
        try:
            await self.page.wait_for_function(
                """
                () => {
                    const txt = 'aceptar';
                    const iframe = document.querySelector('iframe');
                    if (!iframe?.contentDocument) return false;
                    const btn = iframe.contentDocument.querySelector('#siguiente');
                    return btn && btn.textContent.toLowerCase().includes(txt) && btn.offsetParent;
                }
                """,
                timeout=15000
            )
            print("✅ Botón 'Aceptar' detectado!")
            clicked = await self.page.evaluate("""
                () => {
                    const iframe = document.querySelector('iframe');
                    const btn = iframe?.contentDocument?.querySelector('#siguiente');
                    if (btn && btn.textContent.toLowerCase().includes('aceptar')) {
                        btn.click();
                        return true;
                    }
                    return false;
                }
            """)
            if clicked:
                print("✅ ¡Clic en botón Aceptar!")
                return True
            print("❌ No se pudo hacer clic en el botón")
            return False
        except Exception as e:
            print(f"❌ Timeout o error esperando botón Aceptar: {e}")
            return False

    async def run_complete_flow(self):
        """Ejecuta el flujo completo."""
        try:
            await self.login()
            await self.navigate_to_flotas()

            if not await self.click_cell_23541048():
                print("❌ No se pudo hacer clic en la celda")
                return False

            if await self.click_livianos_particulares():
                print("✅ Livianos Particulares seleccionado")
                if await self.click_aceptar():
                    print("✅ ¡PROCESO COMPLETADO EXITOSAMENTE!")
                    return True
                print("⚠️ Falló clic en 'Aceptar'")
                return False
            print("⚠️ Falló clic en 'Livianos Particulares'")
            return False

        except Exception as e:
            print(f"❌ Error en flujo: {e}")
            import traceback; traceback.print_exc()
            return False

    async def close(self):
        """Cierra el navegador."""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

async def main():
    print("🚀 Iniciando automatización Allianz optimizada...")
    client = AllianzAutomation("CA031800", "Infondo2025*", headless=False)

    try:
        await client.launch()
        print("✅ Navegador lanzado")

        success = await client.run_complete_flow()
        if success:
            print("✅ ¡AUTOMATIZACIÓN COMPLETADA!")
            # Espera corta para revisión de resultados
            await asyncio.sleep(15)
        else:
            print("❌ La automatización falló")
            await asyncio.sleep(15)

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback; traceback.print_exc()
    finally:
        print("🔒 Cerrando navegador...")
        await client.close()
        print("✅ Proceso terminado")

if __name__ == "__main__":
    asyncio.run(main())
