"""Página de consulta de póliza específica para Sura """

import datetime
from playwright.async_api import Page
from ....shared.base_page import BasePage
from ....config.sura_config import SuraConfig
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
        """Llena los datos de póliza y fecha con verificación individual."""
        self.logger.info("📋 Llenando datos de póliza...")
        
        try:
            # Generar fecha actual y limpiarla
            today = datetime.datetime.now()
            fecha_formateada = today.strftime("%d/%m/%Y")
            fecha_limpia = Utils.clean_date(fecha_formateada)
            
            self.logger.info(f"📄 Póliza: {self.config.POLIZA_NUMBER}")
            self.logger.info(f"📅 Fecha: {fecha_formateada} -> {fecha_limpia}")
            
            # Llenar y verificar campo de póliza
            if not await self._fill_and_verify_field(
                selector=self.POLIZA_INPUT,
                value=self.config.POLIZA_NUMBER,
                field_name="Póliza",
                max_attempts=3
            ):
                self.logger.error("❌ No se pudo llenar el campo de póliza")
                return False
            
            # Llenar y verificar campo de fecha
            if not await self._fill_and_verify_field(
                selector=self.FECHA_INPUT,
                value=fecha_limpia,
                field_name="Fecha",
                max_attempts=3
            ):
                self.logger.error("❌ No se pudo llenar el campo de fecha")
                return False
            
            self.logger.info("✅ Ambos campos verificados y llenados correctamente")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error llenando datos de póliza: {e}")
            return False

    async def _fill_and_verify_field(
        self, 
        selector: str, 
        value: str, 
        field_name: str, 
        max_attempts: int = 3
    ) -> bool:
        """
        Llena un campo y verifica que el valor se haya establecido correctamente.
        Reintenta si es necesario.
        """
        for attempt in range(1, max_attempts + 1):
            try:
                self.logger.info(f"📝 {field_name} - Intento {attempt}/{max_attempts}")
                
                # Debug: verificar que estamos apuntando al campo correcto
                try:
                    label_id = await self.page.get_attribute(selector, "aria-labelledby")
                    placeholder = await self.page.get_attribute(selector, "placeholder")
                    self.logger.info(f"🔍 {field_name} - Selector: {selector}")
                    self.logger.info(f"🔍 {field_name} - Label ID: {label_id}, Placeholder: '{placeholder}'")
                except:
                    pass
                
                # Limpiar el campo primero
                await self.page.fill(selector, "")
                await self.page.wait_for_timeout(200)
                
                # Llenar con el valor
                await self.page.fill(selector, value)
                await self.page.wait_for_timeout(300)
                
                # Verificar que el valor se estableció correctamente
                actual_value = await self.page.input_value(selector)
                  # Para el campo de fecha, aceptar tanto formato limpio como formateado
                is_date_field = "placeholder='DD/MM/YYYY'" in selector or "aria-labelledby='paper-input-label-27'" in selector
                if is_date_field:
                    # Si es campo de fecha, verificar si contiene la fecha esperada (con o sin formato)
                    expected_clean = value  # ej: "23062025"
                    if len(expected_clean) == 8:  # DDMMYYYY
                        expected_formatted = f"{expected_clean[:2]}/{expected_clean[2:4]}/{expected_clean[4:]}"  # "23/06/2025"
                        if actual_value == expected_clean or actual_value == expected_formatted:
                            self.logger.info(f"✅ {field_name} verificado correctamente: '{actual_value}' (formato aceptado)")
                            return True
                    # También aceptar si ya está en formato con barras
                    elif "/" in value and actual_value == value:
                        self.logger.info(f"✅ {field_name} verificado correctamente: '{actual_value}' (formato con barras)")
                        return True
                    # Verificación flexible adicional: si el valor actual contiene los mismos números
                    clean_actual = actual_value.replace("/", "").replace("-", "").replace(" ", "")
                    clean_expected = expected_clean.replace("/", "").replace("-", "").replace(" ", "")
                    if clean_actual == clean_expected:
                        self.logger.info(f"✅ {field_name} verificado correctamente: '{actual_value}' (formato flexible)")
                        return True
                else:
                    # Para otros campos, verificación exacta
                    if actual_value == value:
                        self.logger.info(f"✅ {field_name} verificado correctamente: '{actual_value}'")
                        return True
                
                self.logger.warning(f"⚠️ {field_name} - Esperado: '{value}', Actual: '{actual_value}'")
                
                if attempt < max_attempts:
                    self.logger.info(f"🔄 {field_name} - Reintentando...")
                    await self.page.wait_for_timeout(500)
                        
            except Exception as e:
                self.logger.warning(f"⚠️ {field_name} - Error en intento {attempt}: {e}")
                if attempt < max_attempts:
                    await self.page.wait_for_timeout(500)
        
        self.logger.error(f"❌ {field_name} - No se pudo llenar después de {max_attempts} intentos")
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
        """Espera a que aparezca la pantalla de selección de planes."""
        self.logger.info("⏳ Esperando pantalla de selección de planes...")
        
        try:
            # Esperar a que aparezca el indicador de selección de plan
            await self.page.wait_for_selector(
                self.PLAN_SELECTION_INDICATOR, 
                timeout=15000,
                state='visible'
            )
            
            self.logger.info("✅ Pantalla de selección de planes detectada")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error esperando pantalla de selección de planes: {e}")
            return False

    async def select_plan(self, plan_name: str) -> bool:
        """Selecciona un plan específico."""
        self.logger.info(f"🎯 Seleccionando plan: {plan_name}")
        
        try:
            # Crear el selector específico para el plan
            plan_selector = self.PLAN_SELECTOR_TEMPLATE.format(plan_name=plan_name)
            
            # Esperar a que el plan esté disponible
            await self.page.wait_for_selector(plan_selector, timeout=10000)
            
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
        """Llena la fecha de inicio de vigencia con la fecha de hoy."""
        self.logger.info("📅 Llenando fecha de inicio de vigencia...")
        
        try:
            # Obtener fecha de hoy en formato DDMMYYYY
            today = datetime.datetime.now()
            fecha_hoy = today.strftime("%d%m%Y")  # Formato: 23062025
            
            self.logger.info(f"📅 Fecha de hoy: {fecha_hoy}")
            
            # Llenar y verificar el campo de fecha de vigencia
            if not await self._fill_and_verify_field(
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
        """Procesa la selección del plan y llenado de fecha de vigencia."""
        self.logger.info("🎯 Procesando selección de plan...")
        
        try:
            # 1. Esperar a que aparezca la pantalla de selección de planes
            if not await self.wait_for_plan_selection():
                self.logger.error("❌ No se pudo cargar la pantalla de selección de planes")
                return False
            
            # 2. Seleccionar el plan configurado
            if not await self.select_plan(self.config.SELECTED_PLAN):
                self.logger.error(f"❌ No se pudo seleccionar el plan: {self.config.SELECTED_PLAN}")
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
            
            self.logger.info("🎉 Proceso completo de consulta de póliza y selección de plan completado exitosamente")
            return True

        except Exception as e:
            self.logger.error(f"❌ Error procesando página de consulta de póliza: {e}")
            return False
