import asyncio
from playwright.async_api import Page
from .base_page import BasePage

class FlotasPage(BasePage):
    """Página de Flotas con funciones específicas para el flujo de cotización."""
    
    # Selectores específicos
    CELL_23541048_ID = "#tableFlotas_7_1"
    ACEPTAR_BUTTON_ID = "#siguiente"
    
    def __init__(self, page: Page):
        super().__init__(page)

    async def click_cell_23541048(self) -> bool:
        """Busca y hace clic en la celda con número 23541048."""
        print("🎯 Buscando celda 23541048...")

        # Primero esperar a que aparezca contenido del iframe
        print("⏳ Esperando contenido del iframe...")
        if not await self.wait_for_iframe_content():
            print("❌ No se pudo cargar contenido del iframe")
            return False

        # Esperar específicamente por el elemento de la tabla
        print("⏳ Esperando tabla de flotas...")
        if not await self.wait_for_element_by_id_in_iframe("tableFlotas_7_1"):
            print("❌ No se encontró la tabla de flotas")
            return False

        # Esperar a que aparezca el texto específico
        if not await self.wait_for_element_with_text("23541048"):
            print("❌ No se encontró el texto 23541048")
            return False

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
        if await self.click_with_js(iframe_script, "✅ ¡Clic exitoso en iframe!"):
            return True

        # 2) ID directo
        try:
            el = await self.page.query_selector(self.CELL_23541048_ID)
            if el and "23541048" in (await el.text_content()):
                await el.click()
                print("✅ ¡Clic exitoso por ID!")
                return True
        except Exception as e:
            print(f"❌ Error por ID: {e}")

        print("❌ No se encontró la celda 23541048")
        return False

    async def click_livianos_particulares(self) -> bool:
        """Busca y hace clic en 'Livianos Particulares' con espera inteligente."""
        print("🔍 Buscando 'Livianos Particulares'...")
        
        # Espera inteligente hasta que aparezca el texto
        if not await self.wait_for_element_with_text("livianos particulares"):
            print("❌ No se encontró el texto 'Livianos Particulares'")
            return False

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
        if await self.click_with_js(iframe_script, "✅ ¡Clic exitoso en Livianos Particulares (iframe)!"):
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

    async def click_aceptar(self) -> bool:
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

    async def execute_flotas_flow(self) -> bool:
        """Ejecuta el flujo completo de la página de flotas."""
        print("🚗 Iniciando flujo de Flotas...")
        
        try:
            # Paso 1: Click en celda 23541048
            if not await self.click_cell_23541048():
                print("❌ No se pudo hacer clic en la celda")
                return False

            # Paso 2: Click en Livianos Particulares
            if not await self.click_livianos_particulares():
                print("⚠️ Falló clic en 'Livianos Particulares'")
                return False
                
            print("✅ Livianos Particulares seleccionado")

            # Paso 3: Click en Aceptar
            if not await self.click_aceptar():
                print("⚠️ Falló clic en 'Aceptar'")
                return False
                
            print("✅ ¡FLUJO DE FLOTAS COMPLETADO EXITOSAMENTE!")
            return True

        except Exception as e:
            print(f"❌ Error en flujo de flotas: {e}")
            import traceback
            traceback.print_exc()
            return False
