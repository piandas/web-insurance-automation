"""Página de consulta de póliza específica para Sura - Versión refactorizada"""

import datetime
from typing import Optional
from playwright.async_api import Page
from ....shared.base_page import BasePage
from ....config.sura_config import SuraConfig
from ....shared.utils import Utils
from ....shared.fasecolda_service import FasecoldaService

class PolicyPage(BasePage):
    """Página de consulta de póliza para Sura."""
    
    # Selectores basados en el HTML real - usar aria-labelledby específico
    POLIZA_INPUT = "input[aria-labelledby='paper-input-label-23']"  # Basado en el HTML que mostraste
    FECHA_INPUT = "input[placeholder='DD/MM/YYYY']"
    CONSULTAR_BUTTON = "paper-button#botonConsultarPoliza"
    
    # Elementos que indican que la página está cargada
    PAGE_READY_SELECTORS = [
        "input[aria-labelledby='paper-input-label-23']",
        "input[placeholder='DD/MM/YYYY']",
        "paper-button#botonConsultarPoliza"
    ]
    
    # Nuevos selectores para la página de selección de planes
    PLAN_SELECTION_INDICATOR = "span.self-center:has-text('Seleccione el plan')"
    PLAN_SELECTOR_TEMPLATE = "div.nombre-plan:has-text('{plan_name}')"  # Selector correcto basado en HTML real
    VIGENCIA_FECHA_INPUT = "input[aria-labelledby='paper-input-label-27']"  # Selector específico para fecha de vigencia
    
    # Selector para el código Fasecolda - se busca dinámicamente por etiqueta
    FASECOLDA_CODE_INPUT = "input[aria-labelledby*='paper-input-label']:not([placeholder*='DD/MM/YYYY'])"  # Fallback genérico
    
    # Selectores para dropdown de categoría de vehículo y año del modelo
    VEHICLE_CATEGORY_DROPDOWN_ID = "#clase"  # ID del dropdown de categoría/clase de vehículo
    VEHICLE_CATEGORY_OPTION = "paper-item:has-text('AUTOMÓVILES')"  # Opción para seleccionar AUTOMÓVILES
    MODEL_YEAR_DROPDOWN_ID = "#modelo"  # ID del dropdown de año del modelo
    MODEL_YEAR_OPTION_TEMPLATE = "paper-item:has-text('{year}')"  # Template para seleccionar año del modelo

    def __init__(self, page: Page):
        super().__init__(page, 'sura')
        self.config = SuraConfig()

    async def wait_for_page_ready(self) -> bool:
        """Espera a que la página de consulta de póliza esté lista usando funciones base."""
        self.logger.info("⏳ Esperando página de consulta de póliza lista...")

        async def _check_page_ready() -> bool:
            """Función interna para verificar si la página está lista."""
            try:
                # Verificar URL esperada
                current_url = self.page.url
                if "datosBasicos" not in current_url:
                    return False
                
                # Usar wait_for_selector_safe de la clase base para el elemento principal
                if not await self.wait_for_selector_safe(self.POLIZA_INPUT, timeout=3000):
                    return False
                
                # Verificar que al menos 2 de 3 elementos estén presentes
                elements_found = 0
                for selector in self.PAGE_READY_SELECTORS:
                    if await self.is_visible_safe(selector, timeout=1000):
                        elements_found += 1
                
                if elements_found >= 2:
                    self.logger.info(f"✅ Página lista con {elements_found}/3 elementos - URL: {current_url}")
                    return True
                else:
                    self.logger.warning(f"⚠️ Solo {elements_found}/3 elementos encontrados")
                    return False
                    
            except Exception as e:
                self.logger.warning(f"⚠️ Error verificando página: {e}")
                return False

        # Usar retry_action de la clase base para los reintentos automáticos
        return await self.retry_action(
            action_func=_check_page_ready,
            description="verificar página de póliza lista",
            max_attempts=20,
            delay_seconds=2.0
        )

    async def fill_policy_data(self) -> bool:
        """Llena los datos de póliza y fecha con verificación individual usando funciones base."""
        self.logger.info("📋 Llenando datos de póliza...")
        
        try:
            # Generar fecha actual y limpiarla
            today = datetime.datetime.now()
            fecha_formateada = today.strftime("%d/%m/%Y")
            fecha_limpia = Utils.clean_date(fecha_formateada)
            
            self.logger.info(f"📄 Póliza: {self.config.POLIZA_NUMBER}")
            self.logger.info(f"📅 Fecha: {fecha_formateada} -> {fecha_limpia}")
            
            # Llenar ambos campos usando la función base
            field_map = {
                self.POLIZA_INPUT: self.config.POLIZA_NUMBER,
                self.FECHA_INPUT: fecha_limpia
            }
            
            # Usar fill_multiple_fields de la clase base
            if not await self.fill_multiple_fields(
                field_map=field_map,
                description="datos de póliza",
                timeout=5000,
                delay_between_fields=0.5
            ):
                self.logger.error("❌ No se pudieron llenar los campos de póliza")
                return False
            
            # Verificar que los valores se establecieron correctamente
            if not await self._verify_policy_fields(fecha_limpia):
                self.logger.warning("⚠️ Verificación de campos falló, pero continuando...")
            
            self.logger.info("✅ Campos de póliza llenados correctamente")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error llenando datos de póliza: {e}")
            return False

    async def _verify_policy_fields(self, expected_date: str) -> bool:
        """Verifica que los campos de póliza se llenaron correctamente."""
        try:
            # Verificar campo de póliza
            poliza_value = await self.page.input_value(self.POLIZA_INPUT)
            if poliza_value != self.config.POLIZA_NUMBER:
                self.logger.warning(f"⚠️ Póliza - Esperado: '{self.config.POLIZA_NUMBER}', Actual: '{poliza_value}'")
                return False
            
            # Verificar campo de fecha (con validación flexible)
            fecha_value = await self.page.input_value(self.FECHA_INPUT)
            if not self._validate_date_field(expected_date, fecha_value):
                self.logger.warning(f"⚠️ Fecha - Esperado: '{expected_date}', Actual: '{fecha_value}'")
                return False
            
            self.logger.info("✅ Verificación de campos exitosa")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error verificando campos: {e}")
            return False

    def _validate_date_field(self, expected: str, actual: str) -> bool:
        """Valida campos de fecha con múltiples formatos aceptados."""
        # Usar la función de validación de la clase base
        try:
            # Normalizar valores
            expected_clean = expected.strip()
            actual_clean = actual.strip()
            
            # Verificación directa
            if actual_clean == expected_clean:
                return True
            
            # Si el expected es formato DDMMYYYY (8 dígitos)
            if len(expected_clean) == 8 and expected_clean.isdigit():
                expected_formatted = f"{expected_clean[:2]}/{expected_clean[2:4]}/{expected_clean[4:]}"
                if actual_clean == expected_formatted:
                    return True
            
            # Verificación flexible: comparar solo números
            actual_numbers = ''.join(filter(str.isdigit, actual_clean))
            expected_numbers = ''.join(filter(str.isdigit, expected_clean))
            
            return actual_numbers == expected_numbers
            
        except Exception:
            return False

    async def click_consultar(self) -> bool:
        """Hace clic en el botón Consultar usando funciones base."""
        self.logger.info("🔍 Haciendo clic en Consultar...")
        
        try:
            current_url = self.page.url
            self.logger.info(f"📍 URL actual: {current_url}")
            
            # Usar safe_click de la clase base
            if not await self.safe_click(self.CONSULTAR_BUTTON, timeout=5000):
                return False
            
            self.logger.info("✅ Clic en Consultar exitoso")
            
            # Esperar un poco para que procese la consulta
            await self.page.wait_for_timeout(3000)
            
            # Verificar si hay algún cambio en la página o navegación
            new_url = self.page.url
            if new_url != current_url:
                self.logger.info(f"🔄 Navegación detectada - Nueva URL: {new_url}")
            else:
                self.logger.info("📄 Página procesada sin cambio de URL")
            
            return True
                
        except Exception as e:
            self.logger.error(f"❌ Error haciendo clic en Consultar: {e}")
            return False

    async def wait_for_plan_selection(self) -> bool:
        """Espera a que aparezca la pantalla de selección de planes usando funciones base."""
        self.logger.info("⏳ Esperando pantalla de selección de planes...")
        
        # Usar wait_for_selector_safe de la clase base
        return await self.wait_for_selector_safe(
            self.PLAN_SELECTION_INDICATOR, 
            timeout=15000
        )

    async def select_plan(self, plan_name: str) -> bool:
        """Selecciona un plan específico usando funciones base."""
        self.logger.info(f"🎯 Seleccionando plan: {plan_name}")
        
        try:
            # Crear el selector específico para el plan
            plan_selector = self.PLAN_SELECTOR_TEMPLATE.format(plan_name=plan_name)
            
            # Esperar a que el plan esté disponible y hacer clic usando funciones base
            if not await self.wait_for_selector_safe(plan_selector, timeout=10000):
                self.logger.error(f"❌ Plan '{plan_name}' no disponible")
                return False
            
            # Hacer clic en el plan usando safe_click
            if not await self.safe_click(plan_selector, timeout=5000):
                self.logger.error(f"❌ No se pudo hacer clic en el plan: {plan_name}")
                return False
            
            self.logger.info(f"✅ Plan '{plan_name}' seleccionado exitosamente")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error seleccionando plan '{plan_name}': {e}")
            return False

    async def fill_vigencia_date(self) -> bool:
        """Llena la fecha de inicio de vigencia con la fecha de hoy usando funciones base."""
        self.logger.info("📅 Llenando fecha de inicio de vigencia...")
        
        try:
            # Obtener fecha de hoy en formato DDMMYYYY
            today = datetime.datetime.now()
            fecha_hoy = today.strftime("%d%m%Y")  # Formato: 23062025
            
            self.logger.info(f"📅 Fecha de hoy: {fecha_hoy}")
            
            # Usar fill_and_verify_field_flexible de la clase base
            if not await self.fill_and_verify_field_flexible(
                selector=self.VIGENCIA_FECHA_INPUT,
                value=fecha_hoy,
                field_name="Fecha de Vigencia",
                max_attempts=3
            ):
                self.logger.error("❌ No se pudo llenar el campo de fecha de vigencia")
                return False
            
            self.logger.info("✅ Fecha de vigencia llenada exitosamente")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error llenando fecha de vigencia: {e}")
            return False

    async def get_fasecolda_code(self) -> Optional[str]:
        """Obtiene el código Fasecolda usando FasecoldaService en una nueva pestaña."""
        self.logger.info("🔍 Obteniendo código Fasecolda...")
        
        try:
            # Verificar si debe buscar automáticamente
            if not self.config.AUTO_FETCH_FASECOLDA:
                self.logger.info("⏭️ Búsqueda automática de Fasecolda deshabilitada")
                return None
            
            # Solo buscar si es vehículo nuevo
            if self.config.VEHICLE_STATE != 'Nuevo':
                self.logger.info(f"⏭️ Vehículo '{self.config.VEHICLE_STATE}' - no requiere código Fasecolda")
                return None
            
            # Crear nueva pestaña para Fasecolda
            self.logger.info("🌐 Abriendo nueva pestaña para Fasecolda...")
            new_page = await self.page.context.new_page()
            
            try:
                # Inicializar el servicio de Fasecolda
                fasecolda_service = FasecoldaService(new_page, self.logger)
                
                # Obtener el código CF
                cf_code = await fasecolda_service.get_cf_code(
                    category=self.config.VEHICLE_CATEGORY,
                    state=self.config.VEHICLE_STATE,
                    model_year=self.config.VEHICLE_MODEL_YEAR,
                    brand=self.config.VEHICLE_BRAND,
                    reference=self.config.VEHICLE_REFERENCE,
                    full_reference=self.config.VEHICLE_FULL_REFERENCE
                )
                
                if cf_code:
                    self.logger.info(f"✅ Código Fasecolda obtenido: {cf_code}")
                    return cf_code
                else:
                    self.logger.warning("⚠️ No se pudo obtener código Fasecolda")
                    return None
                    
            finally:
                # Cerrar la pestaña de Fasecolda
                await new_page.close()
                self.logger.info("🗂️ Pestaña de Fasecolda cerrada")
                
        except Exception as e:
            self.logger.error(f"❌ Error obteniendo código Fasecolda: {e}")
            return None

    async def fill_fasecolda_code(self, cf_code: str) -> bool:
        """Llena el campo del código Fasecolda buscando dinámicamente por etiqueta."""
        self.logger.info(f"📋 Llenando código Fasecolda: {cf_code}")
        
        try:
            # Buscar dinámicamente el campo de Fasecolda por su etiqueta
            fasecolda_selector = await self._find_fasecolda_input_selector()
            
            if not fasecolda_selector:
                self.logger.error("❌ No se pudo encontrar el campo de Fasecolda")
                return False
            
            self.logger.info(f"📝 Campo Fasecolda encontrado con selector: {fasecolda_selector}")
            
            # Usar fill_and_verify_field_flexible de la clase base
            if not await self.fill_and_verify_field_flexible(
                selector=fasecolda_selector,
                value=cf_code,
                field_name="Código Fasecolda",
                max_attempts=3
            ):
                self.logger.error("❌ No se pudo llenar el campo de código Fasecolda")
                return False
            
            self.logger.info("✅ Código Fasecolda llenado exitosamente")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error llenando código Fasecolda: {e}")
            return False

    async def _find_fasecolda_input_selector(self) -> str:
        """Encuentra dinámicamente el selector del campo de Fasecolda por su etiqueta."""
        try:
            # Ejecutar JavaScript para buscar el campo de Fasecolda dinámicamente
            fasecolda_selector = await self.page.evaluate("""
                () => {
                    // Buscar todos los inputs
                    const inputs = Array.from(document.querySelectorAll('input'));
                    
                    // Filtrar por aquellos que tengan una etiqueta con texto "Fasecolda"
                    const fasecoldaInputs = inputs.filter(input => {
                        const labelId = input.getAttribute('aria-labelledby');
                        if (labelId) {
                            const labelElement = document.getElementById(labelId);
                            if (labelElement && labelElement.textContent.toLowerCase().includes('fasecolda')) {
                                return true;
                            }
                        }
                        return false;
                    });
                    
                    if (fasecoldaInputs.length > 0) {
                        const input = fasecoldaInputs[0];
                        const labelId = input.getAttribute('aria-labelledby');
                        return `input[aria-labelledby='${labelId}']`;
                    }
                    
                    return null;
                }
            """)
            
            return fasecolda_selector
            
        except Exception as e:
            self.logger.warning(f"⚠️ Error buscando selector de Fasecolda dinámicamente: {e}")
            return None

    async def select_vehicle_category(self) -> bool:
        """Selecciona 'AUTOMÓVILES' del dropdown de categoría de vehículo."""
        self.logger.info("🚗 Seleccionando categoría de vehículo: AUTOMÓVILES...")
        
        try:
            # Hacer clic en el dropdown de categoría para abrirlo
            if not await self.safe_click(self.VEHICLE_CATEGORY_DROPDOWN_ID, timeout=10000):
                self.logger.error("❌ No se pudo hacer clic en el dropdown de categoría de vehículo")
                return False
            
            # Esperar a que aparezcan las opciones
            await self.page.wait_for_timeout(1000)
            
            # Hacer clic en AUTOMÓVILES
            if not await self.safe_click(self.VEHICLE_CATEGORY_OPTION, timeout=5000):
                self.logger.error("❌ No se pudo seleccionar AUTOMÓVILES")
                return False
            
            self.logger.info("✅ Categoría 'AUTOMÓVILES' seleccionada exitosamente")
            
            # Esperar un poco para que se procese la selección
            await self.page.wait_for_timeout(1500)
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error seleccionando categoría de vehículo: {e}")
            return False

    async def select_model_year(self) -> bool:
        """Selecciona el año del modelo configurado del dropdown."""
        self.logger.info(f"📅 Seleccionando año del modelo: {self.config.VEHICLE_MODEL_YEAR}...")
        
        try:
            # Hacer clic en el dropdown de modelo/año para abrirlo
            if not await self.safe_click(self.MODEL_YEAR_DROPDOWN_ID, timeout=10000):
                self.logger.error("❌ No se pudo hacer clic en el dropdown de modelo/año")
                return False
            
            # Esperar a que aparezcan las opciones
            await self.page.wait_for_timeout(1000)
            
            # Crear el selector específico para el año
            year_selector = self.MODEL_YEAR_OPTION_TEMPLATE.format(year=self.config.VEHICLE_MODEL_YEAR)
            
            # Hacer clic en el año configurado
            if not await self.safe_click(year_selector, timeout=5000):
                self.logger.error(f"❌ No se pudo seleccionar el año: {self.config.VEHICLE_MODEL_YEAR}")
                return False
            
            self.logger.info(f"✅ Año '{self.config.VEHICLE_MODEL_YEAR}' seleccionado exitosamente")
            
            # Esperar un poco para que se procese la selección
            await self.page.wait_for_timeout(1500)
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error seleccionando año del modelo: {e}")
            return False

    async def process_plan_selection(self) -> bool:
        """Procesa la selección del plan, llenado de fecha de vigencia y código Fasecolda."""
        self.logger.info("🎯 Procesando selección de plan...")
        
        try:
            # 1. Esperar a que aparezca la pantalla de selección de planes
            if not await self.wait_for_plan_selection():
                self.logger.error("❌ No se pudo cargar la pantalla de selección de planes")
                return False
            
            # 2. Seleccionar el plan configurado (por defecto "Plan Autos Global")
            if not await self.select_plan(self.config.SELECTED_PLAN):
                self.logger.error(f"❌ No se pudo seleccionar el plan: {self.config.SELECTED_PLAN}")
                return False
            
            # 3. Llenar la fecha de inicio de vigencia
            if not await self.fill_vigencia_date():
                self.logger.error("❌ No se pudo llenar la fecha de vigencia")
                return False
            
            # 4. Obtener y llenar código Fasecolda (solo para vehículos nuevos)
            cf_code = await self.get_fasecolda_code()
            if cf_code:
                if not await self.fill_fasecolda_code(cf_code):
                    self.logger.warning("⚠️ No se pudo llenar el código Fasecolda, pero continuando...")
                else:
                    # 5. Seleccionar categoría de vehículo (AUTOMÓVILES) después de llenar Fasecolda
                    if not await self.select_vehicle_category():
                        self.logger.warning("⚠️ No se pudo seleccionar categoría AUTOMÓVILES, pero continuando...")
                    
                    # 6. Seleccionar año del modelo después de seleccionar categoría
                    if not await self.select_model_year():
                        self.logger.warning("⚠️ No se pudo seleccionar año del modelo, pero continuando...")
            else:
                self.logger.info("⏭️ No se obtuvo código Fasecolda (vehículo usado o búsqueda deshabilitada)")
            
            self.logger.info("🎉 Selección de plan, fecha de vigencia, código Fasecolda, categoría y año completada exitosamente")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error procesando selección de plan: {e}")
            return False

    async def process_policy_page(self) -> bool:
        """Proceso completo de consulta de póliza usando funciones base."""
        self.logger.info("🚀 Procesando página de consulta de póliza...")
        
        try:
            # 1. Verificar que la página esté lista
            if not await self.wait_for_page_ready():
                self.logger.error("❌ La página de consulta de póliza no está lista")
                return False

            self.logger.info("✅ Página de consulta de póliza lista y detectada correctamente")
            
            # 2. Llenar datos de póliza
            if not await self.fill_policy_data():
                self.logger.error("❌ No se pudieron llenar los datos de póliza")
                return False
            
            # 3. Hacer clic en Consultar
            if not await self.click_consultar():
                self.logger.error("❌ No se pudo hacer clic en Consultar")
                return False
            
            # 4. Procesar selección de plan y fecha de vigencia
            if not await self.process_plan_selection():
                self.logger.error("❌ No se pudo procesar la selección de plan")
                return False
            
            self.logger.info("🎉 Proceso completo de consulta de póliza, selección de plan, categoría y año completado exitosamente")
            return True

        except Exception as e:
            self.logger.error(f"❌ Error procesando página de consulta de póliza: {e}")
            return False
