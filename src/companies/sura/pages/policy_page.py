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
                is_date_field = "placeholder='DD/MM/YYYY'" in selector
                if is_date_field:
                    # Si es campo de fecha, verificar si contiene la fecha esperada (con o sin formato)
                    expected_clean = value  # ej: "23062025"
                    if len(expected_clean) == 8:  # DDMMYYYY
                        expected_formatted = f"{expected_clean[:2]}/{expected_clean[2:4]}/{expected_clean[4:]}"  # "23/06/2025"
                        if actual_value == expected_clean or actual_value == expected_formatted:
                            self.logger.info(f"✅ {field_name} verificado correctamente: '{actual_value}' (formato aceptado)")
                            return True
                    else:
                        if actual_value == value:
                            self.logger.info(f"✅ {field_name} verificado correctamente: '{actual_value}'")
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
            
            self.logger.info("🎉 Proceso de consulta de póliza completado exitosamente")
            return True

        except Exception as e:
            self.logger.error(f"❌ Error procesando página de consulta de póliza: {e}")
            return False
