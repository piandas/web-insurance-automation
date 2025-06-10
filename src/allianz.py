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
        """Navega directamente a Flotas Autos."""
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
        await asyncio.sleep(3)

        print("📋 Enviando formulario...")
        form_exists = await self.page.evaluate("!!document.querySelector('#applicationForm')")
        if form_exists:
            await self.page.evaluate("document.querySelector('#applicationForm').submit()")
            print("✅ Formulario enviado")
            await asyncio.sleep(10)
        else:
            print("⚠️ Formulario no encontrado")

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
                if (el?.textContent.includes('23541048')) {
                    el.click(); return true;
                }
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

        # 3) Búsqueda exhaustiva de <td>
        try:
            for el in await self.page.query_selector_all("td"):
                text = await el.text_content() or ""
                if "23541048" in text.strip():
                    await el.click()
                    print("✅ ¡Clic exitoso en búsqueda exhaustiva!")
                    return True
        except Exception as e:
            print(f"❌ Error en búsqueda exhaustiva: {e}")

        print("❌ No se encontró la celda 23541048")
        return False

    async def click_livianos_particulares(self):
        """Busca y hace clic en 'Livianos Particulares'."""
        print("🔍 Buscando 'Livianos Particulares'...")
        await asyncio.sleep(3)

        # 1) Intentar en iframe
        iframe_script = """
            (function() {
                const iframe = document.querySelector('iframe');
                const doc = iframe?.contentDocument;
                if (!doc) return false;
                const selectors = ['a','button','input[type="button"]','input[type="submit"]','[onclick]'];

                // Primera pasada: texto completo
                for (let sel of selectors) {
                    for (let el of doc.querySelectorAll(sel)) {
                        const tx = (el.textContent || el.value || '').toLowerCase();
                        if (tx.includes('livianos particulares') ||
                            (tx.includes('livianos') && tx.includes('particulares'))) {
                            el.click(); return true;
                        }
                    }
                }
                // Segunda pasada: sólo 'livianos'
                for (let sel of selectors) {
                    for (let el of doc.querySelectorAll(sel)) {
                        if ((el.textContent || el.value || '').toLowerCase().includes('livianos')) {
                            el.click(); return true;
                        }
                    }
                }
                return false;
            })();
        """
        if await self._click_with_js(iframe_script, "✅ ¡Clic exitoso en Livianos Particulares (iframe)!"):
            return True

        # 2) Intentar en página principal
        page_script = """
            (function() {
                const doc = document;
                const selectors = ['a','button','input[type="button"]','input[type="submit"]','[onclick]'];

                // Primera pasada: texto completo
                for (let sel of selectors) {
                    for (let el of doc.querySelectorAll(sel)) {
                        const tx = (el.textContent || el.value || '').toLowerCase();
                        if (tx.includes('livianos particulares') ||
                            (tx.includes('livianos') && tx.includes('particulares'))) {
                            el.click(); return true;
                        }
                    }
                }
                // Segunda pasada: sólo 'livianos'
                for (let sel of selectors) {
                    for (let el of doc.querySelectorAll(sel)) {
                        if ((el.textContent || el.value || '').toLowerCase().includes('livianos')) {
                            el.click(); return true;
                        }
                    }
                }
                return false;
            })();
        """
        if await self._click_with_js(page_script, "✅ ¡Clic exitoso en Livianos Particulares (página principal)!"):
            return True

        # 3) Playwright locator
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

    async def run_complete_flow(self):
        """Ejecuta el flujo completo."""
        try:
            await self.login()
            await self.navigate_to_flotas()

            if not await self.click_cell_23541048():
                print("❌ No se pudo hacer clic en la celda")
                return False

            if await self.click_livianos_particulares():
                print("✅ ¡PROCESO COMPLETADO EXITOSAMENTE!")
                return True

            print("⚠️ Clic en celda OK, pero no en Livianos Particulares")
            return True

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
            await asyncio.sleep(20)
        else:
            print("❌ La automatización falló")
            await asyncio.sleep(30)

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback; traceback.print_exc()
    finally:
        print("🔒 Cerrando navegador...")
        await client.close()
        print("✅ Proceso terminado")

if __name__ == "__main__":
    asyncio.run(main())
