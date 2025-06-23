"""Página de cotización específica para Sura - Versión corregida."""

from playwright.async_api import Page
from ....shared.base_page import BasePage
from ....config.sura_config import SuraConfig

class QuotePage(BasePage):
    """Página de cotización para Sura."""
    
    # Selectores basados en el HTML real
    PRIMER_NOMBRE_INPUT    = "input[ng-reflect-name='primerNombreControl']"
    SEGUNDO_NOMBRE_INPUT   = "input[ng-reflect-name='segundoNombreControl']" 
    PRIMER_APELLIDO_INPUT  = "input[ng-reflect-name='primerApellidoControl']"
    SEGUNDO_APELLIDO_INPUT = "input[ng-reflect-name='segundoApellidoControl']"
    NUMERO_DOCUMENTO_INPUT = "input[ng-reflect-name='documentControl']"
    FECHA_NACIMIENTO_INPUT = "input[ng-reflect-name='fechaNacimientoControl']"
    SEXO_MASCULINO         = "mat-radio-button[value='M']"
    SEXO_FEMENINO          = "mat-radio-button[value='F']"
    
    # Selectores para dirección
    DIRECCION_TRABAJO_INPUT = "input[ng-reflect-name='bloqueDireccion_1DireccionCtrl']"
    TELEFONO_TRABAJO_INPUT  = "input[ng-reflect-name='bloqueDireccion_1TelefonoCtrl']"
    CIUDAD_TRABAJO_INPUT    = "input[ng-reflect-name='bloqueDireccion_1CiudadCtrl']"
    
    CONTINUAR_BUTTON       = "button:has-text('Continuar')"

    def __init__(self, page: Page):
        super().__init__(page, 'sura')
        self.config = SuraConfig()

    async def wait_for_page_ready(self) -> bool:
        """Espera a que la página de cotización esté lista."""
        self.logger.info("⏳ Esperando página de cotización lista...")
        try:
            cotizacion_selectors = [
                "input[ng-reflect-name='primerNombreControl']",
                "input[ng-reflect-name='documentControl']",
                "text=Cotizador Conectado",
                "text=Cliente",
                "mat-select"
            ]
            
            for i, selector in enumerate(cotizacion_selectors):
                try:
                    self.logger.info(f"🔍 Intentando selector {i+1}/{len(cotizacion_selectors)}: {selector}")
                    await self.page.wait_for_selector(selector, timeout=5000, state='visible')
                    self.logger.info(f"✅ Página lista - detectada con selector: {selector}")
                    
                    current_url = self.page.url
                    self.logger.info(f"📍 URL: {current_url}")
                    return True
                except Exception as e:
                    self.logger.warning(f"⚠️ Selector {selector} no encontrado: {e}")
                    continue            
            current_url = self.page.url
            self.logger.error(f"❌ Página de cotización no detectada. URL actual: {current_url}")
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Error esperando página de cotización: {e}")
            return False

    async def verify_data(self) -> bool:
        """Verificación con comparación detallada entre config y valores encontrados."""
        self.logger.info("🔍 Verificando datos...")
        try:
            expected_data = {
                "Nombre": self.config.CLIENT_FIRST_NAME,
                "Apellido": self.config.CLIENT_FIRST_LASTNAME,
                "Documento": self.config.CLIENT_DOCUMENT_NUMBER,
            }
            self.logger.info("📋 COMPARACIÓN CONFIG vs PÁGINA:")
            self.logger.info("=" * 50)            
            
            # Para cada input, seleccionamos solo el primero que NO esté disabled
            fields = [
                (self.PRIMER_NOMBRE_INPUT + ":not([disabled])", "Nombre"),
                (self.PRIMER_APELLIDO_INPUT + ":not([disabled])", "Apellido"),
                (self.NUMERO_DOCUMENTO_INPUT + ":not([disabled])", "Documento"),
            ]

            # Usar función optimizada de la clase base para verificar valores
            for selector, field_name in fields:
                try:
                    await self.page.wait_for_selector(selector, timeout=5000)
                    # Usar función de la clase base sin el :first problemático
                    await self.verify_element_value_equals(
                        selector=selector,  # Remover :first que causa error
                        expected_value=expected_data[field_name],
                        property_name="value",
                        description=field_name
                    )
                except Exception as e:
                    self.logger.warning(f"❌ ERROR {field_name}: {e}")

            # Verificar sexo
            try:
                expected_gender = self.config.CLIENT_GENDER.upper()  # 'M' o 'F'
                # Apuntamos al input interno de cada mat-radio-button
                masc_input = f"{self.SEXO_MASCULINO} input[type='radio']"
                fem_input  = f"{self.SEXO_FEMENINO} input[type='radio']"

                if expected_gender == 'M':
                    checked = await self.page.locator(masc_input).first.is_checked(timeout=2000)
                    status = "✅ MATCH" if checked else "⚠️ DIFF"
                    self.logger.info(f"{status} Sexo: Config='M' | Página='{'M' if checked else 'F'}'")
                else:
                    checked = await self.page.locator(fem_input).first.is_checked(timeout=2000)
                    status = "✅ MATCH" if checked else "⚠️ DIFF"
                    self.logger.info(f"{status} Sexo: Config='F' | Página='{'F' if checked else 'M'}'")
            except Exception as e:
                self.logger.warning(f"❌ ERROR Sexo: {e}")

            self.logger.info("=" * 50)
            self.logger.info("✅ Verificación completada")
            return True

        except Exception as e:
            self.logger.error(f"❌ Error verificando: {e}")
            return False

    async def process_quote_page(self) -> bool:
        """Proceso completo de cotización."""
        self.logger.info("🚀 Procesando página de cotización...")
        try:
            # 1. Verificar que la página esté lista
            if not await self.wait_for_page_ready():
                self.logger.error("❌ La página de cotización no está lista")
                return False

            self.logger.info("✅ Página de cotización lista y detectada correctamente")
            
            # 2. Verificar datos existentes
            await self.verify_data()
            
            # 3. Seleccionar ocupación del cliente
            if not await self.select_occupation():
                self.logger.error("❌ No se pudo seleccionar ocupación")
                return False

            # 4. Seleccionar "Trabajo" como tipo de dirección
            if not await self.select_work_address_type():
                self.logger.error("❌ No se pudo seleccionar tipo de dirección")
                return False

            # 5. Llenar datos de dirección
            if not await self.fill_address():
                self.logger.error("❌ No se pudo llenar dirección")
                return False

            # 6. Hacer clic en Continuar
            if not await self.click_continue():
                self.logger.error("❌ No se pudo continuar o navegar")
                return False
            
            self.logger.info("🎉 Proceso de cotización completado exitosamente")
            self.logger.info("📄 Se redirigió correctamente a la página de Clientes")
            return True

        except Exception as e:
            self.logger.error(f"❌ Error procesando página de cotización: {e}")
            return False

    async def select_occupation(self) -> bool:
        """Selecciona la ocupación del cliente desde el config."""
        self.logger.info("👔 Verificando y seleccionando ocupación...")
        try:
            ocupacion_esperada = self.config.CLIENT_OCCUPATION
            self.logger.info(f"📋 Ocupación esperada desde config: {ocupacion_esperada}")
            
            # Buscar el elemento específico de ocupación con placeholder
            ocupacion_selectors = [
                "mat-select:has(span:text('Ocupación *'))",
                "mat-select .mat-select-placeholder:text('Ocupación *')",
                "mat-select:has(.mat-select-placeholder)",
                "mat-select.ng-invalid"
            ]
            
            ocupacion_element = None
            for selector in ocupacion_selectors:
                try:
                    elements = await self.page.locator(selector).all()
                    for element in elements:
                        text_content = await element.text_content()
                        if "Ocupación" in text_content and "*" in text_content:
                            ocupacion_element = element
                            self.logger.info(f"✅ Elemento de ocupación encontrado con selector: {selector}")
                            break
                    if ocupacion_element:
                        break
                except:
                    continue
            
            if not ocupacion_element:
                self.logger.error("❌ No se encontró el elemento de ocupación")
                return False
            
            # Verificar si ya está seleccionada
            current_text = await ocupacion_element.text_content()
            if ocupacion_esperada in current_text:
                self.logger.info(f"✅ Ocupación ya seleccionada: {ocupacion_esperada}")
                return True
            
            # Usar función optimizada de la clase base para seleccionar
            return await self.select_from_material_dropdown(
                dropdown_selector="mat-select:has(span:text('Ocupación *'))",
                option_text=ocupacion_esperada,
                description=f"ocupación {ocupacion_esperada}"
            )
                
        except Exception as e:
            self.logger.error(f"❌ Error seleccionando ocupación: {e}")
            return False

    async def select_work_address_type(self) -> bool:
        """Selecciona 'Trabajo' como tipo de dirección en el contenedor correcto."""
        self.logger.info("🏢 Seleccionando tipo de dirección: Trabajo...")
        try:
            # Solo los mat-radio-button habilitados dentro del bloque bloqueDireccion_1
            selector = (
                "mat-radio-group[ng-reflect-name='bloqueDireccion_1RadioCtrl'] "
                "mat-radio-button[ng-reflect-value='TR']:not(.mat-radio-disabled)"
            )
            await self.page.wait_for_selector(selector, timeout=5000, state='visible')
            await self.page.locator(selector).first.click(timeout=5000)
            await self.page.wait_for_timeout(500)
            self.logger.info("✅ Tipo de dirección 'Trabajo' seleccionado")
            return True

        except Exception as e:
            self.logger.error(f"❌ Error seleccionando tipo de dirección 'Trabajo': {e}")
            return False

    async def fill_address(self) -> bool:
        """Llena los datos de dirección desde el config, eligiendo siempre el input habilitado."""
        self.logger.info("🏠 Llenando dirección...")
        try:
            # Corregir los selectores para evitar errores de sintaxis
            field_map = {
                self.DIRECCION_TRABAJO_INPUT: self.config.CLIENT_ADDRESS,
                self.TELEFONO_TRABAJO_INPUT: self.config.CLIENT_PHONE_WORK,
                self.CIUDAD_TRABAJO_INPUT: self.config.CLIENT_CITY,
            }
            
            success = await self.fill_multiple_fields(
                field_map=field_map,
                description="datos de dirección",
                timeout=5000,
                delay_between_fields=0.3
            )
            
            if success:
                # Intentar seleccionar primera opción de autocompletado
                try:
                    await self.page.locator("mat-option").first.click(timeout=3000)
                except:
                    pass
                
                self.logger.info(f"✅ Dirección llenada: {self.config.CLIENT_ADDRESS}, {self.config.CLIENT_PHONE_WORK}, {self.config.CLIENT_CITY}")
            
            return success
        except Exception as e:
            self.logger.error(f"❌ Error llenando dirección: {e}")
            return False
    async def click_continue(self) -> bool:
        """Hace clic en el botón Continuar y verifica la navegación."""
        self.logger.info("➡️ Haciendo clic en Continuar...")
        try:
            current_url = self.page.url
            self.logger.info(f"📍 URL actual: {current_url}")
            
            await self.page.locator(self.CONTINUAR_BUTTON).click(timeout=5000)
            self.logger.info("✅ Clic en Continuar exitoso")
            
            # Usar función optimizada de navegación de la clase base
            expected_url_parts = ["cotizadores.sura.com", "Clientes"]
            return await self.wait_for_page_navigation(
                expected_url_parts=expected_url_parts,
                timeout=3000,
                description="página de Clientes"
            )
                
        except Exception as e:
            self.logger.error(f"❌ Error haciendo clic en Continuar: {e}")
            return False
