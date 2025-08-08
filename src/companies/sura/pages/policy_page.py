"""Página de consulta de póliza específica para Sura - Versión refactorizada"""

import datetime
from typing import Optional
from playwright.async_api import Page
from ....shared.base_page import BasePage
from ....config.sura_config import SuraConfig
from ....config.client_config import ClientConfig
from ....shared.utils import Utils

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
            
            self.logger.info(f"📄 Póliza: {ClientConfig.get_policy_number('sura')}")
            self.logger.info(f"📅 Fecha: {fecha_formateada} -> {fecha_limpia}")
            
            # Llenar ambos campos usando la función base
            field_map = {
                self.POLIZA_INPUT: ClientConfig.get_policy_number('sura'),
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
            if poliza_value != ClientConfig.get_policy_number('sura'):
                self.logger.warning(f"⚠️ Póliza - Esperado: '{ClientConfig.get_policy_number('sura')}', Actual: '{poliza_value}'")
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

    async def process_plan_selection(self) -> bool:
        """Procesa la selección del plan y llenado de fecha de vigencia únicamente."""
        self.logger.info("🎯 Procesando selección de plan...")
        
        try:
            # 1. Esperar a que aparezca la pantalla de selección de planes
            if not await self.wait_for_plan_selection():
                self.logger.error("❌ No se pudo cargar la pantalla de selección de planes")
                return False
            
            # 2. Seleccionar el plan configurado (por defecto "Plan Autos Global")
            selected_plan = ClientConfig.get_company_specific_config('sura').get('selected_plan', 'Plan Autos Global')
            if not await self.select_plan(selected_plan):
                self.logger.error(f"❌ No se pudo seleccionar el plan: {selected_plan}")
                return False
            
            # 3. Llenar la fecha de inicio de vigencia
            if not await self.fill_vigencia_date():
                self.logger.error("❌ No se pudo llenar la fecha de vigencia")
                return False
            
            self.logger.info("🎉 Selección de plan y fecha de vigencia completada exitosamente")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error procesando selección de plan: {e}")
            return False

    async def process_policy_page(self) -> bool:
        """Proceso de consulta de póliza hasta fecha de vigencia."""
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
            
            self.logger.info("🎉 Proceso de póliza completado hasta fecha de vigencia")
            return True

        except Exception as e:
            self.logger.error(f"❌ Error procesando página de consulta de póliza: {e}")
            return False
