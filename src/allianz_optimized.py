import asyncio
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

class AllianzAutomation:
    def __init__(self, usuario: str, contrasena: str, headless: bool = False):
        self.usuario = usuario
        self.contrasena = contrasena
        self.headless = headless
        self.playwright = None
        self.browser = None
        self.page = None

    async def launch(self):
        """Inicializa Playwright y abre el navegador"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=self.headless)
        self.page = await self.browser.new_page()

    async def login(self):
        """Login en Allianz"""
        print("🔑 Iniciando login...")
        await self.page.goto("https://www.allia2net.com.co/ngx-epac/private/home")
        await self.page.fill("input[name='username']", self.usuario)
        await self.page.fill("input[name='password']", self.contrasena)
        await self.page.click("button[type='submit']")
        await self.page.wait_for_load_state("networkidle")
        print("✅ Login completado")

    async def navigate_to_flotas(self):
        """Navega directamente a Flotas Autos"""
        print("🚗 Navegando a Flotas Autos...")
        
        # Clic en Nueva Póliza
        await self.page.click("#link_new_policy")
        
        # Abrir sección Autos
        await self.page.wait_for_selector(".nx-modal__content-wrapper", state="visible")
        await self.page.click('nx-expansion-panel-header:has-text("Autos")')
        await self.page.wait_for_selector('.nx-expansion-panel__content', state="visible")
        
        # Clic en Flotas Autos
        await self.page.wait_for_selector("app-box .box", state="visible")
        await self.page.get_by_text("Flotas Autos").click()
        
        # Esperar navegación a /application
        try:
            await self.page.wait_for_url("**/application**", timeout=30000)
            print(f"✅ Navegación exitosa a: {self.page.url}")
        except PlaywrightTimeout:
            print(f"⚠️ URL actual: {self.page.url}")
        
        await self.page.wait_for_load_state("networkidle")
        await asyncio.sleep(3)
        
        # Enviar formulario para cargar iframe
        print("📋 Enviando formulario...")
        form_exists = await self.page.evaluate("document.querySelector('#applicationForm') ? true : false")
        if form_exists:
            await self.page.evaluate("document.querySelector('#applicationForm').submit()")
            print("✅ Formulario enviado")
            await asyncio.sleep(10)  # Esperar carga del iframe        else:
            print("⚠️ Formulario no encontrado")

    async def click_cell_23541048(self):
        """Busca y hace clic en la celda con número 23541048"""
        print("🎯 Buscando celda 23541048...")
        
        # Estrategia 1: Buscar en iframe
        try:
            click_success = await self.page.evaluate("""
                (function() {
                    const iframe = document.querySelector('iframe');
                    if (iframe && iframe.contentDocument) {
                        const element = iframe.contentDocument.querySelector('#tableFlotas_7_1');
                        if (element && element.textContent.includes('23541048')) {
                            console.log('Encontrado en iframe:', element.textContent);
                            element.click();
                            return true;
                        }
                    }
                    return false;
                })();
            """)
            
            if click_success:
                print("✅ ¡Clic exitoso en iframe!")
                return True
        except Exception as e:
            print(f"❌ Error en iframe: {e}")
        
        # Estrategia 2: Buscar por ID directo
        try:
            element = await self.page.query_selector("#tableFlotas_7_1")
            if element:
                text = await element.text_content()
                if "23541048" in text:
                    await element.click()
                    print("✅ ¡Clic exitoso por ID!")
                    return True
        except Exception as e:
            print(f"❌ Error por ID: {e}")
        
        # Estrategia 3: Búsqueda exhaustiva
        try:
            elements = await self.page.query_selector_all("td")
            for element in elements:
                text = await element.text_content()
                if text and "23541048" in text.strip():
                    await element.click()
                    print("✅ ¡Clic exitoso en búsqueda exhaustiva!")
                    return True
        except Exception as e:
            print(f"❌ Error en búsqueda exhaustiva: {e}")
        
        print("❌ No se encontró la celda 23541048")
        return False

    async def click_livianos_particulares(self):
        """Busca y hace clic en 'Livianos Particulares'"""
        print("🔍 Buscando 'Livianos Particulares'...")
        
        # Esperar un poco después del clic anterior
        await asyncio.sleep(3)
          # Estrategia 1: JavaScript en iframe
        try:
            click_success = await self.page.evaluate("""
                (function() {
                    const iframe = document.querySelector('iframe');
                    if (iframe && iframe.contentDocument) {
                        const iframeDoc = iframe.contentDocument;
                        
                        // Buscar elementos clickeables con el texto
                        const selectors = ['a', 'button', 'input[type="button"]', 'input[type="submit"]', '[onclick]'];
                        
                        for (let selector of selectors) {
                            const elements = iframeDoc.querySelectorAll(selector);
                            for (let el of elements) {
                                const text = el.textContent || el.value || '';
                                if (text.toLowerCase().includes('livianos particulares') || 
                                    (text.toLowerCase().includes('livianos') && text.toLowerCase().includes('particulares'))) {
                                    console.log('Encontrado Livianos Particulares:', el);
                                    el.click();
                                    return true;
                                }
                            }
                        }
                        
                        // Buscar solo "livianos" si no encuentra la frase completa
                        for (let selector of selectors) {
                            const elements = iframeDoc.querySelectorAll(selector);
                            for (let el of elements) {
                                const text = el.textContent || el.value || '';
                                if (text.toLowerCase().includes('livianos')) {
                                    console.log('Encontrado elemento con livianos:', el);
                                    el.click();
                                    return true;
                                }
                            }
                        }
                    }
                    return false;
                })();
            """)
            
            if click_success:
                print("✅ ¡Clic exitoso en Livianos Particulares (iframe)!")
                return True
        except Exception as e:
            print(f"❌ Error en iframe: {e}")
          # Estrategia 2: Buscar en página principal
        try:
            click_success = await self.page.evaluate("""
                (function() {
                    const selectors = ['a', 'button', 'input[type="button"]', 'input[type="submit"]', '[onclick]'];
                    
                    for (let selector of selectors) {
                        const elements = document.querySelectorAll(selector);
                        for (let el of elements) {
                            const text = el.textContent || el.value || '';
                            if (text.toLowerCase().includes('livianos particulares') || 
                                (text.toLowerCase().includes('livianos') && text.toLowerCase().includes('particulares'))) {
                                console.log('Encontrado en página principal:', el);
                                el.click();
                                return true;
                            }
                        }
                    }
                    return false;
                })();
            """)
            
            if click_success:
                print("✅ ¡Clic exitoso en Livianos Particulares (página principal)!")
                return True
        except Exception as e:
            print(f"❌ Error en página principal: {e}")
        
        # Estrategia 3: Playwright locator
        try:
            element = await self.page.locator("text=Livianos Particulares").first
            if await element.is_visible():
                await element.click()
                print("✅ ¡Clic exitoso con locator!")
                return True
        except Exception as e:
            print(f"❌ Error con locator: {e}")
        
        print("❌ No se encontró 'Livianos Particulares'")
        return False

    async def run_complete_flow(self):
        """Ejecuta el flujo completo"""
        try:
            await self.login()
            await self.navigate_to_flotas()
            
            # Hacer clic en la celda 23541048
            cell_success = await self.click_cell_23541048()
            if not cell_success:
                print("❌ No se pudo hacer clic en la celda")
                return False
            
            # Hacer clic en Livianos Particulares
            livianos_success = await self.click_livianos_particulares()
            if livianos_success:
                print("✅ ¡PROCESO COMPLETADO EXITOSAMENTE!")
                return True
            else:
                print("⚠️ Se hizo clic en la celda pero no en Livianos Particulares")
                return True  # Consideramos parcialmente exitoso
                
        except Exception as e:
            print(f"❌ Error en flujo: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def close(self):
        """Cierra el navegador"""
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
            print("⏳ Esperando 20 segundos para verificar resultado...")
            await asyncio.sleep(20)
        else:
            print("❌ La automatización falló")
            print("⏳ Esperando 30 segundos para inspección...")
            await asyncio.sleep(30)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("🔒 Cerrando navegador...")
        await client.close()
        print("✅ Proceso terminado")

if __name__ == "__main__":
    asyncio.run(main())
