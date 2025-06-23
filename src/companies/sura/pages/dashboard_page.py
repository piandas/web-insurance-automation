"""Página del dashboard específica para Sura."""

import asyncio
from playwright.async_api import Page
from ....shared.base_page import BasePage

class DashboardPage(BasePage):
    """Página del dashboard con navegación al cotizador en Sura."""
    
    # Selectores
    COTIZADOR_LINK = 'a[href*="boton-cotizador.png"]'
    COTIZADOR_IMG = 'img[src*="boton-cotizador.png"]'
    HERRAMIENTAS_MENU = 'a:has-text("Herramientas")'
    MAIN_BUTTON = 'button#dropdownMenuButton'
    MAIN_ICON_BUTTON = 'button:has(img[src="assets/img/icon/main-ico.png"])'
    def __init__(self, page: Page):
        super().__init__(page, 'sura')

    async def navigate_to_cotizador(self) -> bool:
        """Navega al cotizador de Sura y abre la nueva pestaña."""
        self.logger.info("💰 Navegando al cotizador de Sura...")
        try:
            # Buscar y hacer clic en el botón del cotizador más rápido
            cotizador_found = False
            
            # Intentar diferentes selectores para encontrar el cotizador
            selectors_to_try = [
                self.COTIZADOR_IMG,
                self.COTIZADOR_LINK,
                'img[alt="boton-cotizador.png"]',
                'a[title*="cotizador"]',
                'a[title*="Cotizador"]',
                'img[src*="cotizador"]'
            ]
            
            for selector in selectors_to_try:
                try:
                    # Reducir timeout para ser más rápido
                    if await self.is_visible_safe(selector, timeout=2000):
                        self.logger.info(f"✅ Cotizador encontrado con selector: {selector}")
                        
                        # Configurar listener para nueva pestaña antes del clic
                        new_tab_promise = self.page.context.wait_for_event("page", timeout=10000)
                        
                        await self.safe_click(selector)
                        
                        # Esperar la nueva pestaña con timeout más corto
                        try:
                            new_page = await new_tab_promise
                            await new_page.wait_for_load_state("domcontentloaded", timeout=15000)
                            
                            self.logger.info("✅ Nueva pestaña del cotizador abierta")
                            
                            # Cambiar el contexto de la página actual
                            self.page = new_page
                            cotizador_found = True
                            break
                            
                        except Exception as e:
                            self.logger.warning(f"⚠️ Error esperando nueva pestaña: {e}")
                            continue
                            
                except Exception as e:
                    self.logger.debug(f"Selector {selector} no encontrado: {e}")
                    continue
            
            if not cotizador_found:
                self.logger.error("❌ No se pudo encontrar el botón del cotizador")
                return False
            
            # Esperar menos tiempo para acelerar el proceso
            await asyncio.sleep(1)
            
            self.logger.info("✅ Navegación al cotizador exitosa")
            return True
            
        except Exception as e:
            self.logger.exception(f"❌ Error navegando al cotizador: {e}")
            return False

    async def click_main_dropdown(self) -> bool:
        """Hace clic en el botón principal del dropdown y navega por toda la secuencia de menús."""
        self.logger.info("🔽 Navegando por secuencia completa: Menú → Soluciones → Seguros autos → Colectivos → Nueva inclusión...")
        try:
            # Esperar un poco más para que cargue la nueva pestaña
            await asyncio.sleep(3)
            
            # PASO 1: Hacer clic en el botón principal del menú (exacto del que funcionó)
            button_selector = 'button#dropdownMenuButton'
            
            if not await self.is_visible_safe(button_selector, timeout=10000):
                self.logger.error("❌ No se pudo encontrar el botón principal del menú")
                return False
                
            await self.safe_click(button_selector)
            self.logger.info("✅ Clic en botón principal exitoso")
            
            # Esperar que se abra el menú
            await asyncio.sleep(2)
            
            # PASO 2: Hacer clic en "Soluciones"
            soluciones_selector = 'a:has-text("Soluciones")'
            
            if not await self.is_visible_safe(soluciones_selector, timeout=5000):
                self.logger.error("❌ No se pudo encontrar Soluciones")
                return False
                
            await self.safe_click(soluciones_selector)
            self.logger.info("✅ Navegación a Soluciones exitosa")
            await asyncio.sleep(1)
            
            # PASO 3: Hacer clic en "Seguros Autos"
            seguros_autos_selector = 'a:has-text("Seguros Autos")'
            
            if not await self.is_visible_safe(seguros_autos_selector, timeout=5000):
                self.logger.error("❌ No se pudo encontrar Seguros Autos")
                return False
                
            await self.safe_click(seguros_autos_selector)
            self.logger.info("✅ Navegación a Seguros Autos exitosa")
            await asyncio.sleep(1)
            
            # PASO 4: Hacer clic en "Colectivos"
            colectivos_selector = 'a:has-text("Colectivos")'
            
            if not await self.is_visible_safe(colectivos_selector, timeout=5000):
                self.logger.error("❌ No se pudo encontrar Colectivos")
                return False
                
            await self.safe_click(colectivos_selector)
            self.logger.info("✅ Navegación a Colectivos exitosa")
            await asyncio.sleep(1)
            
            # PASO 5: Hacer clic en "Nueva inclusión"
            nueva_inclusion_selector = 'a:has-text("Nueva Inclusión")'
            
            if not await self.is_visible_safe(nueva_inclusion_selector, timeout=5000):
                self.logger.error("❌ No se pudo encontrar Nueva inclusión")
                return False
                
            await self.safe_click(nueva_inclusion_selector)
            self.logger.info("✅ Navegación a Nueva inclusión exitosa")
            
            # Esperar que cargue el formulario
            await asyncio.sleep(3)
            
            self.logger.info("✅ Navegación completa por menús exitosa - Formulario listo")
            return True
            
        except Exception as e:
            self.logger.exception(f"❌ Error navegando por secuencia de menús: {e}")
            return False    
    
    async def select_document_type(self, document_type: str = "C") -> bool:
        """Selecciona el tipo de documento del cliente usando Material Design dropdown."""
        self.logger.info(f"📄 Seleccionando tipo de documento: {document_type}")
        try:
            # Hacer clic en el dropdown Material Design (exacto del que funcionó)
            dropdown_selector = '.mat-select-value'
            
            if not await self.is_visible_safe(dropdown_selector, timeout=10000):
                self.logger.error("❌ No se pudo encontrar el dropdown de tipo de documento")
                return False
                
            await self.safe_click(dropdown_selector)
            self.logger.info("✅ Dropdown de tipo de documento abierto")
            
            # Esperar que se abran las opciones
            await asyncio.sleep(1)
            
            # Mapear el código al texto que aparece en el dropdown
            document_type_map = {
                'C': 'CEDULA',
                'E': 'CED.EXTRANJERIA',
                'P': 'PASAPORTE',
                'A': 'NIT',
                'CA': 'NIT PERSONAS NATURALES',
                'N': 'NUIP',
                'R': 'REGISTRO CIVIL',
                'T': 'TARJ.IDENTIDAD',
                'D': 'DIPLOMATICO',
                'X': 'DOC.IDENT. DE EXTRANJEROS',
                'F': 'IDENT. FISCAL PARA EXT.',
                'TC': 'CERTIFICADO NACIDO VIVO',
                'TP': 'PASAPORTE ONU',
                'TE': 'PERMISO ESPECIAL PERMANENCIA',
                'TS': 'SALVOCONDUCTO DE PERMANENCIA',
                'TF': 'PERMISO ESPECIAL FORMACN PEPFF',
                'TT': 'PERMISO POR PROTECCION TEMPORL'
            }
            
            # Obtener el texto del tipo de documento
            document_text = document_type_map.get(document_type, 'CEDULA')
            
            # Hacer clic en la opción correspondiente
            option_selector = f'span:has-text("{document_text}")'
            
            if not await self.is_visible_safe(option_selector, timeout=5000):
                self.logger.error(f"❌ No se pudo encontrar la opción: {document_text}")
                return False
                
            await self.safe_click(option_selector)
            self.logger.info(f"✅ Tipo de documento seleccionado: {document_text}")
            
            return True
            
        except Exception as e:
            self.logger.exception(f"❌ Error seleccionando tipo de documento: {e}")
            return False

    async def input_document_number(self, document_number: str = "1020422674") -> bool:
        """Ingresa el número de documento en el campo correspondiente."""
        self.logger.info(f"📄 Ingresando número de documento: {document_number}")
        try:
            # Buscar el campo de número de documento - priorizar el selector que funcionó
            document_selectors = [
                'input[placeholder="Documento"]',  # El más confiable según las pruebas
                'input[placeholder*="documento"]',
                'input[placeholder*="Documento"]',
                'input[type="text"]',
                'input[placeholder*="cedula"]',
                'input[placeholder*="Cédula"]',
                '#documento',
                '#cedula',
                'input[name="documento"]',
                'input[name="cedula"]'
            ]
            
            document_field_found = False
            
            for selector in document_selectors:
                try:
                    if await self.is_visible_safe(selector, timeout=5000):
                        self.logger.info(f"✅ Campo de documento encontrado con selector: {selector}")
                        
                        # Limpiar y llenar el campo
                        await self.page.fill(selector, "")
                        await self.page.fill(selector, document_number)
                        
                        self.logger.info(f"✅ Número de documento ingresado: {document_number}")
                        document_field_found = True
                        break
                        
                except Exception as e:
                    self.logger.debug(f"Selector {selector} no encontrado: {e}")
                    continue
            
            if not document_field_found:
                self.logger.error("❌ No se pudo encontrar el campo de número de documento")
                return False
            
            return True
            
        except Exception as e:
            self.logger.exception(f"❌ Error ingresando número de documento: {e}")
            return False

    async def accept_form(self) -> bool:
        """Acepta o envía el formulario."""
        self.logger.info("✅ Aceptando formulario...")
        try:
            # Buscar botón de aceptar/enviar
            accept_selectors = [
                'button:has-text("Aceptar")',
                'button:has-text("Enviar")',
                'button:has-text("Continuar")',
                'button[type="submit"]',
                'input[type="submit"]',
                '.btn-primary',
                '.btn-success'
            ]
            
            accept_button_found = False
            
            for selector in accept_selectors:
                try:
                    if await self.is_visible_safe(selector, timeout=5000):
                        self.logger.info(f"✅ Botón de aceptar encontrado con selector: {selector}")
                        
                        if await self.safe_click(selector):
                            self.logger.info("✅ Formulario aceptado exitosamente")
                            accept_button_found = True
                            break
                        else:
                            self.logger.warning(f"⚠️ No se pudo hacer clic en botón: {selector}")
                            
                except Exception as e:
                    self.logger.debug(f"Selector {selector} no encontrado: {e}")
                    continue
            
            if not accept_button_found:
                self.logger.error("❌ No se pudo encontrar botón de aceptar")
                return False
            
            # Esperar a que se procese
            await asyncio.sleep(2)
            await self.wait_for_load_state_with_retry("networkidle")
            
            return True
            
        except Exception as e:
            self.logger.exception(f"❌ Error aceptando formulario: {e}")
            return False

    async def complete_navigation_flow(self, document_number: str = "1020422674", document_type: str = "C") -> bool:
        """Completa el flujo completo de navegación en Sura."""
        self.logger.info("🚀 Iniciando flujo completo de navegación Sura...")
        
        try:
            # Paso 1: Navegar al cotizador
            if not await self.navigate_to_cotizador():
                return False
            
            # Paso 2: Hacer clic en el botón principal del menú y navegar por toda la secuencia
            if not await self.click_main_dropdown():
                return False
            
            # Paso 3: Seleccionar tipo de documento
            if not await self.select_document_type(document_type):
                return False
            
            # Paso 4: Ingresar número de documento
            if not await self.input_document_number(document_number):
                return False
            
            # Paso 5: Aceptar formulario
            if not await self.accept_form():
                return False
            
            self.logger.info("✅ Flujo de navegación Sura completado exitosamente")
            return True
            
        except Exception as e:
            self.logger.exception(f"❌ Error en flujo de navegación Sura: {e}")
            return False    
    async def select_document_type(self, document_type: str = "C") -> bool:
        """Selecciona el tipo de documento del cliente usando Material Design dropdown."""
        self.logger.info(f"📄 Seleccionando tipo de documento: {document_type}")
        try:
            # Hacer clic en el dropdown Material Design (exacto del que funcionó)
            dropdown_selector = '.mat-select-value'
            
            if not await self.is_visible_safe(dropdown_selector, timeout=10000):
                self.logger.error("❌ No se pudo encontrar el dropdown de tipo de documento")
                return False
                
            await self.safe_click(dropdown_selector)
            self.logger.info("✅ Dropdown de tipo de documento abierto")
            
            # Esperar que se abran las opciones
            await asyncio.sleep(1)
            
            # Mapear el código al texto que aparece en el dropdown
            document_type_map = {
                'C': 'CEDULA',
                'E': 'CED.EXTRANJERIA',
                'P': 'PASAPORTE',
                'A': 'NIT',
                'CA': 'NIT PERSONAS NATURALES',
                'N': 'NUIP',
                'R': 'REGISTRO CIVIL',
                'T': 'TARJ.IDENTIDAD',
                'D': 'DIPLOMATICO',
                'X': 'DOC.IDENT. DE EXTRANJEROS',
                'F': 'IDENT. FISCAL PARA EXT.',
                'TC': 'CERTIFICADO NACIDO VIVO',
                'TP': 'PASAPORTE ONU',
                'TE': 'PERMISO ESPECIAL PERMANENCIA',
                'TS': 'SALVOCONDUCTO DE PERMANENCIA',
                'TF': 'PERMISO ESPECIAL FORMACN PEPFF',
                'TT': 'PERMISO POR PROTECCION TEMPORL'
            }
            
            # Obtener el texto del tipo de documento
            document_text = document_type_map.get(document_type, 'CEDULA')
            
            # Hacer clic en la opción correspondiente
            option_selector = f'span:has-text("{document_text}")'
            
            if not await self.is_visible_safe(option_selector, timeout=5000):
                self.logger.error(f"❌ No se pudo encontrar la opción: {document_text}")
                return False
                
            await self.safe_click(option_selector)
            self.logger.info(f"✅ Tipo de documento seleccionado: {document_text}")
            
            return True
            
        except Exception as e:
            self.logger.exception(f"❌ Error seleccionando tipo de documento: {e}")
            return False
