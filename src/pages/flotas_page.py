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

    async def click_radio_no_asegurado(self) -> bool:
        """Busca y hace clic en el radio button 'No' para la pregunta de asegurado."""
        print("🔘 Buscando radio button 'No' para asegurado...")
        
        try:
            # Esperar dinámicamente a que aparezca el radio button en iframe
            print("⏳ Esperando radio button 'No' en iframe...")
            await self.page.wait_for_function(
                """
                () => {
                    const iframe = document.querySelector('iframe');
                    const doc = iframe?.contentDocument;
                    if (!doc) return false;
                    
                    // Buscar por ID
                    const radioNo = doc.querySelector('#IntervinientesBean\\\\$esAsegurado2');
                    if (radioNo && radioNo.offsetParent) return true;
                    
                    // Buscar por name con value='N'
                    const radiosByName = doc.querySelectorAll('input[name="IntervinientesBean$esAsegurado"]');
                    for (let radio of radiosByName) {
                        if (radio.value === 'N' && radio.offsetParent) return true;
                    }
                    return false;
                }
                """,
                timeout=15000
            )
            print("✅ Radio button 'No' detectado!")
            
            # Hacer clic en el radio button
            clicked = await self.page.evaluate("""
                () => {
                    const iframe = document.querySelector('iframe');
                    const doc = iframe?.contentDocument;
                    if (!doc) return false;
                    
                    // Buscar el radio button con id IntervinientesBean$esAsegurado2
                    const radioNo = doc.querySelector('#IntervinientesBean\\\\$esAsegurado2');
                    if (radioNo) {
                        radioNo.click();
                        return true;
                    }
                    
                    // Buscar por name si no se encuentra por ID
                    const radiosByName = doc.querySelectorAll('input[name="IntervinientesBean$esAsegurado"]');
                    for (let radio of radiosByName) {
                        if (radio.value === 'N') {
                            radio.click();
                            return true;
                        }
                    }
                    return false;
                }
            """)
            if clicked:
                print("✅ ¡Clic en radio button 'No' exitoso!")
                return True
            
            print("❌ No se pudo hacer clic en el radio button")
            return False
            
        except Exception as e:
            print(f"❌ Timeout o error esperando radio button 'No': {e}")
            return False

    async def select_tipo_documento(self, tipo_documento: str = "CEDULA_CIUDADANIA") -> bool:
        """
        Selecciona el tipo de documento en el dropdown.
        """
        # Mapeo de tipos de documento a valores del select
        tipo_map = {
            "NIT": " ",
            "REG_CIVIL_NACIMIENTO": "I",
            "NUIP": "J", 
            "TARJETA_IDENTIDAD": "B",
            "CEDULA_CIUDADANIA": "C",
            "CEDULA_EXTRANJERIA": "X",
            "PASAPORTE": "P",
            "IDENTIFICACION_EXTRANJEROS": "L",
            "MENOR_SIN_IDENTIFICACION": "Q",
            "PEP": "E",
            "OTROS_DOCUMENTOS": "S",
            "PPT": "T",
            "SOCIEDAD_EXTRANJERA": "W"
        }
        
        if tipo_documento not in tipo_map:
            print(f"❌ Tipo de documento '{tipo_documento}' no válido. Opciones: {list(tipo_map.keys())}")
            return False
            
        valor_select = tipo_map[tipo_documento]
        print(f"📋 Seleccionando '{tipo_documento}' en tipo de documento...")
        
        try:
            # Esperar dinámicamente a que aparezca el select en iframe
            print("⏳ Esperando dropdown de tipo de documento en iframe...")
            await self.page.wait_for_function(
                """
                () => {
                    const iframe = document.querySelector('iframe');
                    const doc = iframe?.contentDocument;
                    if (!doc) return false;
                    
                    const select = doc.querySelector('#IntervinientesBean\\\\$nifAsegurado_tipoDoc');
                    return select && select.offsetParent && select.options.length > 0;
                }
                """,
                timeout=15000
            )
            print("✅ Dropdown de tipo de documento detectado!")
            
            # Seleccionar el tipo de documento especificado
            selected = await self.page.evaluate(f"""
                () => {{
                    const iframe = document.querySelector('iframe');
                    const doc = iframe?.contentDocument;
                    if (!doc) return false;
                    
                    const select = doc.querySelector('#IntervinientesBean\\\\$nifAsegurado_tipoDoc');
                    if (select) {{
                        // Seleccionar el tipo de documento especificado
                        select.value = "{valor_select}";
                        
                        // Disparar evento change para notificar el cambio
                        const changeEvent = new Event('change', {{ bubbles: true }});
                        select.dispatchEvent(changeEvent);
                        
                        return {{
                            success: true,
                            newValue: select.value,
                            selectedText: select.options[select.selectedIndex].title
                        }};
                    }}
                    return {{ success: false }};
                }}
            """)
            
            if selected and selected.get('success'):
                print(f"✅ ¡{tipo_documento} seleccionado exitosamente! Valor: {selected.get('newValue')}")
                return True
            
            print(f"❌ No se pudo seleccionar {tipo_documento}")
            return False
            
        except Exception as e:
            print(f"❌ Timeout o error seleccionando tipo de documento: {e}")
            return False

    async def fill_numero_documento(self, numero_documento: str = "1026258710") -> bool:
        """
        Llena el campo de número de documento.
        
        Args:
            numero_documento (str): Número de documento a ingresar (por defecto: "1026258710")
        """
        print(f"📝 Llenando número de documento: {numero_documento}...")
        
        try:
            # Esperar dinámicamente a que aparezca el input en iframe
            print("⏳ Esperando campo de número de documento en iframe...")
            await self.page.wait_for_function(
                """
                () => {
                    const iframe = document.querySelector('iframe');
                    const doc = iframe?.contentDocument;
                    if (!doc) return false;
                    
                    const input = doc.querySelector('#IntervinientesBean\\\\$nifAsegurado_doc');
                    return input && input.offsetParent;
                }
                """,
                timeout=15000
            )
            print("✅ Campo de número de documento detectado!")
            
            # Llenar el campo con el número especificado
            filled = await self.page.evaluate(f"""
                () => {{
                    const iframe = document.querySelector('iframe');
                    const doc = iframe?.contentDocument;
                    if (!doc) return false;
                    
                    const input = doc.querySelector('#IntervinientesBean\\\\$nifAsegurado_doc');
                    if (input) {{
                        // Limpiar el campo y escribir el nuevo número
                        input.value = '';
                        input.value = '{numero_documento}';
                        
                        // Disparar eventos para notificar el cambio
                        const inputEvent = new Event('input', {{ bubbles: true }});
                        const changeEvent = new Event('change', {{ bubbles: true }});
                        
                        input.dispatchEvent(inputEvent);
                        input.dispatchEvent(changeEvent);
                        
                        return {{
                            success: true,
                            newValue: input.value,
                            id: input.id
                        }};
                    }}
                    return {{ success: false }};
                }}
            """)
            
            if filled and filled.get('success'):
                print(f"✅ ¡Número de documento {numero_documento} ingresado exitosamente!")
                return True
            
            print(f"❌ No se pudo llenar el número de documento")
            return False
            
        except Exception as e:
            print(f"❌ Timeout o error llenando número de documento: {e}")
            return False

    async def select_categoria_riesgo_liviano(self) -> bool:
        """
        Selecciona 'Liviano Particulares' del dropdown CategoriaRiesgoBean$catRiesgo.
        """
        print("📋 Seleccionando 'Liviano Particulares' en categoría de riesgo...")
        
        try:
            # Esperar dinámicamente a que aparezca el select en iframe
            print("⏳ Esperando dropdown de categoría de riesgo en iframe...")
            await self.page.wait_for_function(
                """
                () => {
                    const iframe = document.querySelector('iframe');
                    const doc = iframe?.contentDocument;
                    if (!doc) return false;
                    
                    const select = doc.querySelector('#CategoriaRiesgoBean\\\\$catRiesgo');
                    return select && select.offsetParent && select.options.length > 0;
                }
                """,
                timeout=15000
            )
            print("✅ Dropdown de categoría de riesgo detectado!")
            
            # Seleccionar "Liviano Particulares" (valor "L0008")
            selected = await self.page.evaluate("""
                () => {
                    const iframe = document.querySelector('iframe');
                    const doc = iframe?.contentDocument;
                    if (!doc) return false;
                    
                    const select = doc.querySelector('#CategoriaRiesgoBean\\\\$catRiesgo');
                    if (select) {
                        // Seleccionar "Liviano Particulares" (valor L0008)
                        select.value = "L0008";
                        
                        // Disparar evento change para notificar el cambio y ejecutar cargarCodigo()
                        const changeEvent = new Event('change', { bubbles: true });
                        select.dispatchEvent(changeEvent);
                        
                        // También ejecutar la función onchange directamente si existe
                        if (typeof cargarCodigo === 'function') {
                            cargarCodigo(select);
                        }
                        
                        return {
                            success: true,
                            newValue: select.value,
                            selectedText: select.options[select.selectedIndex].title
                        };
                    }
                    return { success: false };
                }
            """)
            
            if selected and selected.get('success'):
                print(f"✅ ¡'Liviano Particulares' seleccionado exitosamente! Valor: {selected.get('newValue')}")
                return True
            
            print("❌ No se pudo seleccionar 'Liviano Particulares'")
            return False
            
        except Exception as e:
            print(f"❌ Timeout o error seleccionando categoría de riesgo: {e}")
            return False

    async def click_btn_aceptar_final(self) -> bool:
        """
        Hace clic en el botón final #btnAceptar que ejecuta eventoSiguiente().
        """
        print("🔘 Buscando botón Aceptar final (#btnAceptar)...")
        
        try:
            # Esperar dinámicamente a que aparezca el botón en iframe
            print("⏳ Esperando botón Aceptar final en iframe...")
            await self.page.wait_for_function(
                """
                () => {
                    const iframe = document.querySelector('iframe');
                    const doc = iframe?.contentDocument;
                    if (!doc) return false;
                    
                    const btnAceptar = doc.querySelector('#btnAceptar');
                    return btnAceptar && btnAceptar.offsetParent && 
                           btnAceptar.textContent.toLowerCase().includes('aceptar');
                }
                """,
                timeout=15000
            )
            print("✅ Botón Aceptar final detectado!")
            
            # Hacer clic en el botón final
            clicked = await self.page.evaluate("""
                () => {
                    const iframe = document.querySelector('iframe');
                    const doc = iframe?.contentDocument;
                    if (!doc) return false;
                    
                    const btnAceptar = doc.querySelector('#btnAceptar');
                    if (btnAceptar) {
                        // Hacer clic en el botón (esto ejecutará eventoSiguiente())
                        btnAceptar.click();
                        
                        // También ejecutar eventoSiguiente() directamente si existe
                        if (typeof eventoSiguiente === 'function') {
                            eventoSiguiente();
                        }
                        
                        return {
                            success: true,
                            id: btnAceptar.id,
                            text: btnAceptar.textContent.trim()
                        };
                    }
                    return { success: false };
                }
            """)
            
            if clicked and clicked.get('success'):
                print(f"✅ ¡Clic en botón Aceptar final exitoso! ID: {clicked.get('id')}")
                return True
            
            print("❌ No se pudo hacer clic en el botón Aceptar final")
            return False
            
        except Exception as e:
            print(f"❌ Timeout o error haciendo clic en botón Aceptar final: {e}")
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

            # Paso 4: Click en radio button 'No' asegurado
            if not await self.click_radio_no_asegurado():
                print("⚠️ Falló clic en radio button 'No' asegurado")
                return False
                
            print("✅ Opción 'No' asegurado seleccionada")
            
            # Paso 5: Seleccionar tipo de documento (por defecto: Cédula de ciudadanía)         
            if not await self.select_tipo_documento("CEDULA_CIUDADANIA"):
                print("⚠️ Falló selección de tipo de documento")
                return False
                
            print("✅ Tipo de documento seleccionado")
            
            # Paso 6: Llenar número de documento
            if not await self.fill_numero_documento("1026258710"):
                print("⚠️ Falló llenado de número de documento")
                return False
                
            print("✅ Número de documento ingresado")
              # Paso 7: Seleccionar categoría de riesgo 'Liviano Particulares'
            if not await self.select_categoria_riesgo_liviano():
                print("⚠️ Falló selección de categoría de riesgo")
                return False
                
            print("✅ Categoría de riesgo seleccionada")
            
            # Paso 8: Click en botón Aceptar final
            if not await self.click_btn_aceptar_final():
                print("⚠️ Falló clic en botón Aceptar final")
                return False
                
            print("✅ Botón Aceptar final presionado")
                
            print("✅ ¡FLUJO DE FLOTAS COMPLETADO EXITOSAMENTE!")
            return True

        except Exception as e:
            print(f"❌ Error en flujo de flotas: {e}")
            import traceback
            traceback.print_exc()
            return False
