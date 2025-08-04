"""Página de manejo de código Fasecolda específica para Sura"""

import datetime
from typing import Optional
from playwright.async_api import Page
from ....shared.base_page import BasePage
from ....config.sura_config import SuraConfig
from ....shared.fasecolda_service import FasecoldaService

class FasecoldaPage(BasePage):
    """Página de manejo de código Fasecolda para Sura."""
    
    # Selector para el código Fasecolda - se busca dinámicamente por etiqueta
    FASECOLDA_CODE_INPUT = "input[aria-labelledby*='paper-input-label']:not([placeholder*='DD/MM/YYYY'])"  # Fallback genérico
    
    # Selectores para mensaje de error y botón Aceptar
    ERROR_MESSAGE_SELECTOR = "#divMessage:has-text('No existe el fasecolda')"
    ACCEPT_BUTTON_SELECTOR = "#btnOne:has-text('Aceptar')"
    
    # Selectores para dropdown de categoría de vehículo y año del modelo
    VEHICLE_CATEGORY_DROPDOWN_ID = "#clase"  # ID del dropdown de categoría/clase de vehículo
    VEHICLE_CATEGORY_OPTION = "paper-item:has-text('AUTOMÓVILES')"  # Opción para seleccionar AUTOMÓVILES
    MODEL_YEAR_DROPDOWN_ID = "#modelo"  # ID del dropdown de año del modelo
    MODEL_YEAR_OPTION_TEMPLATE = "paper-item:has-text('{year}')"  # Template para seleccionar año del modelo

    def __init__(self, page: Page):
        super().__init__(page, 'sura')
        self.config = SuraConfig()

    async def get_fasecolda_code(self) -> Optional[dict]:
        """Obtiene los códigos Fasecolda usando FasecoldaService en una nueva pestaña."""
        self.logger.info("🔍 Obteniendo códigos Fasecolda...")
        
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
                
                # Obtener los códigos CF y CH
                codes = await fasecolda_service.get_cf_code(
                    category=self.config.VEHICLE_CATEGORY,
                    state=self.config.VEHICLE_STATE,
                    model_year=self.config.VEHICLE_MODEL_YEAR,
                    brand=self.config.VEHICLE_BRAND,
                    reference=self.config.VEHICLE_REFERENCE,
                    full_reference=self.config.VEHICLE_FULL_REFERENCE
                )
                
                if codes and codes.get('cf_code'):
                    ch_info = f" - CH: {codes.get('ch_code')}" if codes.get('ch_code') else ""
                    self.logger.info(f"✅ Códigos Fasecolda obtenidos - CF: {codes['cf_code']}{ch_info}")
                    return codes
                else:
                    self.logger.warning("⚠️ No se pudieron obtener códigos Fasecolda")
                    return None
                    
            finally:
                # Cerrar la pestaña de Fasecolda
                await new_page.close()
                self.logger.info("🗂️ Pestaña de Fasecolda cerrada")
                
        except Exception as e:
            self.logger.error(f"❌ Error obteniendo códigos Fasecolda: {e}")
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

    async def check_and_handle_fasecolda_error(self) -> bool:
        """Verifica si apareció el mensaje de error 'No existe el fasecolda' y lo maneja."""
        self.logger.info("🔍 Verificando si hay error de Fasecolda...")
        
        try:
            # Verificar si apareció el mensaje de error con timeout corto
            error_visible = await self.is_visible_safe(self.ERROR_MESSAGE_SELECTOR, timeout=3000)
            
            if error_visible:
                self.logger.warning("⚠️ Detectado mensaje 'No existe el fasecolda'")
                
                # Hacer clic en el botón Aceptar
                if await self.safe_click(self.ACCEPT_BUTTON_SELECTOR, timeout=5000):
                    self.logger.info("✅ Botón 'Aceptar' presionado exitosamente")
                    
                    # Esperar un poco para que el modal se cierre
                    await self.page.wait_for_timeout(2000)
                    return True
                else:
                    self.logger.error("❌ No se pudo hacer clic en el botón 'Aceptar'")
                    return False
            else:
                self.logger.info("✅ No se detectó error de Fasecolda")
                return False
                
        except Exception as e:
            self.logger.warning(f"⚠️ Error verificando mensaje de error Fasecolda: {e}")
            return False

    async def fill_fasecolda_with_retry(self, codes: dict) -> bool:
        """Llena el código Fasecolda con reintentos usando CH primero y CF como fallback."""
        self.logger.info("🔄 Iniciando proceso de llenado de Fasecolda con reintentos...")
        
        # Lista de códigos a intentar: primero CH, luego CF
        codes_to_try = []
        
        if codes.get('ch_code'):
            codes_to_try.append(('CH', codes['ch_code']))
        
        if codes.get('cf_code'):
            codes_to_try.append(('CF', codes['cf_code']))
        
        if not codes_to_try:
            self.logger.error("❌ No hay códigos disponibles para intentar")
            return False
        
        for attempt, (code_type, code_value) in enumerate(codes_to_try, 1):
            self.logger.info(f"🎯 Intento {attempt}: Probando código {code_type}: {code_value}")
            
            # Llenar el código Fasecolda
            if not await self.fill_fasecolda_code(code_value):
                self.logger.warning(f"⚠️ No se pudo llenar el código {code_type}")
                continue
            
            # Seleccionar categoría de vehículo después de llenar Fasecolda
            if not await self.select_vehicle_category():
                self.logger.warning("⚠️ No se pudo seleccionar categoría AUTOMÓVILES")
                continue
            
            # Seleccionar año del modelo después de seleccionar categoría
            if not await self.select_model_year():
                self.logger.warning("⚠️ No se pudo seleccionar año del modelo")
                continue
            
            # Verificar si apareció error de Fasecolda
            error_occurred = await self.check_and_handle_fasecolda_error()
            
            if not error_occurred:
                self.logger.info(f"✅ Código {code_type} aceptado exitosamente")
                return True
            else:
                self.logger.warning(f"⚠️ Código {code_type} rechazado, continuando con siguiente...")
                # Limpiar el campo antes del siguiente intento si es necesario
                await self._clear_fasecolda_field()
        
        self.logger.error("❌ Todos los códigos fueron rechazados")
        return False

    async def _clear_fasecolda_field(self) -> bool:
        """Limpia el campo de Fasecolda para el siguiente intento."""
        try:
            fasecolda_selector = await self._find_fasecolda_input_selector()
            if fasecolda_selector:
                await self.page.fill(fasecolda_selector, "")
                await self.page.wait_for_timeout(500)
                return True
        except Exception as e:
            self.logger.warning(f"⚠️ Error limpiando campo Fasecolda: {e}")
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

    async def process_fasecolda_filling(self) -> bool:
        """Proceso completo de obtención y llenado de códigos Fasecolda."""
        self.logger.info("🔍 Procesando llenado de código Fasecolda...")
        
        try:
            # Obtener códigos Fasecolda (solo para vehículos nuevos)
            codes = await self.get_fasecolda_code()
            if codes:
                if not await self.fill_fasecolda_with_retry(codes):
                    self.logger.warning("⚠️ No se pudieron llenar los códigos Fasecolda")
                    return False
            else:
                self.logger.info("⏭️ No se obtuvieron códigos Fasecolda (vehículo usado o búsqueda deshabilitada)")
                return True  # No es error si no necesita Fasecolda
            
            self.logger.info("🎉 Proceso de llenado de código Fasecolda completado exitosamente")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error procesando llenado de Fasecolda: {e}")
            return False
