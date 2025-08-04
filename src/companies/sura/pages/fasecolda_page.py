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
    
    # Selectores para campos adicionales después del Fasecolda
    SERVICE_TYPE_DROPDOWN_ID = "#tipoServicio"  # ID del dropdown de tipo de servicio
    SERVICE_TYPE_OPTION = "paper-item:has-text('Particular')"  # Opción para seleccionar Particular
    CITY_INPUT_SELECTOR = "input[aria-label='Ciudad']"  # Campo de ciudad
    CITY_OPTION_TEMPLATE = "vaadin-combo-box-item:has-text('Medellin - (Antioquia)')"  # Opción de ciudad
    PLATE_INPUT_SELECTOR = "#placa input"  # Campo de placa
    ZERO_KM_RADIO_SELECTOR = "paper-radio-button[title='opcion-Si']"  # Radio button para cero kilómetros
    
    # Selectores para primas y planes
    PRIMA_ANUAL_SELECTOR = "#primaAnual"  # Selector para el valor de prima anual
    PLAN_AUTOS_CLASICO_SELECTOR = "div.horizontal.layout.contenedor-nom-plan:has-text('Plan Autos Clásico')"  # Selector para el plan autos clásico
    ACCEPT_BUTTON_MODAL_SELECTOR = "#btnOne"  # Botón aceptar específico del modal de continuidad
    MODAL_DIALOG_SELECTOR = "div.dialog-content-base.info"  # Selector del modal de continuidad

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

    async def select_service_type(self) -> bool:
        """Selecciona 'Particular' del dropdown de tipo de servicio."""
        self.logger.info("🏠 Seleccionando tipo de servicio: Particular...")
        
        try:
            # Hacer clic en el dropdown de tipo de servicio para abrirlo
            if not await self.safe_click(self.SERVICE_TYPE_DROPDOWN_ID, timeout=10000):
                self.logger.error("❌ No se pudo hacer clic en el dropdown de tipo de servicio")
                return False
            
            # Esperar a que aparezcan las opciones
            await self.page.wait_for_timeout(1000)
            
            # Hacer clic en Particular
            if not await self.safe_click(self.SERVICE_TYPE_OPTION, timeout=5000):
                self.logger.error("❌ No se pudo seleccionar Particular")
                return False
            
            self.logger.info("✅ Tipo de servicio 'Particular' seleccionado exitosamente")
            
            # Esperar un poco para que se procese la selección
            await self.page.wait_for_timeout(1500)
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error seleccionando tipo de servicio: {e}")
            return False

    async def fill_city(self) -> bool:
        """Llena el campo de ciudad y selecciona la opción de Medellín."""
        self.logger.info(f"🏙️ Llenando ciudad: {self.config.CLIENT_CITY}...")
        
        try:
            # Llenar el campo de ciudad directamente con fill()
            await self.page.fill(self.CITY_INPUT_SELECTOR, self.config.CLIENT_CITY)
            
            # Esperar a que aparezcan las opciones del autocompletado
            await self.page.wait_for_timeout(1500)
            
            # Seleccionar la opción de Medellín - Antioquia
            if not await self.safe_click(self.CITY_OPTION_TEMPLATE, timeout=5000):
                self.logger.error("❌ No se pudo seleccionar la opción de ciudad")
                return False
            
            self.logger.info("✅ Ciudad seleccionada exitosamente")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error llenando ciudad: {e}")
            return False

    async def fill_plate(self) -> bool:
        """Llena el campo de placa con una placa genérica."""
        self.logger.info("🚗 Llenando placa genérica: XXX123...")
        
        try:
            # Llenar el campo de placa con una placa genérica
            if not await self.fill_and_verify_field_flexible(
                selector=self.PLATE_INPUT_SELECTOR,
                value="XXX123",
                field_name="Placa",
                max_attempts=3
            ):
                self.logger.error("❌ No se pudo llenar el campo de placa")
                return False
            
            self.logger.info("✅ Placa llenada exitosamente")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error llenando placa: {e}")
            return False

    async def select_zero_kilometers(self) -> bool:
        """Selecciona 'Sí' en la opción de cero kilómetros."""
        self.logger.info("🆕 Seleccionando vehículo cero kilómetros: Sí...")
        
        try:
            # Hacer clic en el radio button de Sí para cero kilómetros
            if not await self.safe_click(self.ZERO_KM_RADIO_SELECTOR, timeout=10000):
                self.logger.error("❌ No se pudo seleccionar la opción de cero kilómetros")
                return False
            
            self.logger.info("✅ Opción 'Sí' para cero kilómetros seleccionada exitosamente")
            
            # Esperar un poco para que se procese la selección
            await self.page.wait_for_timeout(1500)
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error seleccionando cero kilómetros: {e}")
            return False

    async def trigger_quote_calculation(self) -> bool:
        """Hace clic en un área vacía para deseleccionar y activar el cálculo de la cotización."""
        self.logger.info("🎯 Activando cálculo de cotización...")
        
        try:
            # Hacer clic en el body para deseleccionar cualquier elemento activo
            await self.page.click("body")
            
            # Esperar a que se procese y se calcule la cotización
            await self.page.wait_for_timeout(3000)
            
            self.logger.info("✅ Cálculo de cotización activado")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error activando cálculo de cotización: {e}")
            return False

    async def extract_prima_anual_value(self, max_wait_seconds: int = 20) -> Optional[float]:
        """Extrae el valor numérico de la prima anual esperando hasta que aparezca."""
        self.logger.info(f"💰 Esperando y extrayendo valor de prima anual (máximo {max_wait_seconds} segundos)...")
        
        try:
            # Esperar hasta que el elemento aparezca y tenga valor
            for attempt in range(max_wait_seconds):
                try:
                    # Verificar si el elemento existe y tiene contenido
                    element = await self.page.query_selector(self.PRIMA_ANUAL_SELECTOR)
                    if element:
                        text_content = await element.text_content()
                        if text_content and text_content.strip():
                            # Extraer solo los números del texto
                            import re
                            numbers = re.sub(r'[^\d]', '', text_content)
                            if numbers:
                                value = float(numbers)
                                self.logger.info(f"✅ Prima anual extraída: ${value:,.0f} (texto original: '{text_content.strip()}')")
                                return value
                    
                    # Esperar 1 segundo antes del siguiente intento
                    await self.page.wait_for_timeout(1000)
                    
                except Exception as e:
                    self.logger.debug(f"Intento {attempt + 1} fallido: {e}")
                    await self.page.wait_for_timeout(1000)
            
            self.logger.warning("⚠️ No se pudo extraer el valor de prima anual después de esperar")
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Error extrayendo prima anual: {e}")
            return None

    async def click_plan_autos_clasico(self) -> bool:
        """Hace clic en el Plan Autos Clásico."""
        self.logger.info("🎯 Haciendo clic en Plan Autos Clásico...")
        
        try:
            # Hacer clic en el plan autos clásico
            if not await self.safe_click(self.PLAN_AUTOS_CLASICO_SELECTOR, timeout=10000):
                self.logger.error("❌ No se pudo hacer clic en Plan Autos Clásico")
                return False
            
            self.logger.info("✅ Clic en Plan Autos Clásico exitoso")
            
            # Esperar más tiempo para que se procese el cambio de plan
            self.logger.info("⏳ Esperando que se procese el cambio de plan...")
            await self.page.wait_for_timeout(3000)
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error haciendo clic en Plan Autos Clásico: {e}")
            return False

    async def handle_optional_modal(self) -> bool:
        """Maneja un modal opcional que puede aparecer después de seleccionar el plan."""
        self.logger.info("🔍 Verificando si aparece modal opcional...")
        
        try:
            # Verificar si apareció el modal de continuidad o cualquier modal con btnOne
            modal_visible = await self.is_visible_safe(self.MODAL_DIALOG_SELECTOR, timeout=5000)
            button_visible = await self.is_visible_safe(self.ACCEPT_BUTTON_MODAL_SELECTOR, timeout=5000)
            
            if modal_visible or button_visible:
                self.logger.info("📋 Modal opcional detectado, haciendo clic en Aceptar...")
                
                # Intentar hacer clic en el botón específico #btnOne
                if await self.safe_click(self.ACCEPT_BUTTON_MODAL_SELECTOR, timeout=5000):
                    self.logger.info("✅ Botón 'Aceptar' del modal presionado exitosamente")
                    
                    # Esperar más tiempo a que el modal se cierre y se procese el cambio
                    self.logger.info("⏳ Esperando que se procese después del modal...")
                    await self.page.wait_for_timeout(3000)
                    return True
                else:
                    # Intentar con selector alternativo
                    self.logger.info("🔄 Intentando con selector alternativo...")
                    if await self.safe_click("paper-button:has-text('Aceptar')", timeout=5000):
                        self.logger.info("✅ Botón 'Aceptar' alternativo presionado exitosamente")
                        await self.page.wait_for_timeout(3000)
                        return True
                    else:
                        self.logger.error("❌ No se pudo hacer clic en el botón 'Aceptar' del modal")
                        return False
            else:
                self.logger.info("✅ No se detectó modal opcional")
                return True
                
        except Exception as e:
            self.logger.warning(f"⚠️ Error verificando modal opcional: {e}")
            return True  # No bloqueamos el flujo si hay error verificando el modal

    async def check_and_handle_continuity_modal(self) -> bool:
        """Verifica y maneja específicamente el modal de continuidad de placa."""
        self.logger.info("🔍 Verificando modal de continuidad de placa...")
        
        try:
            # Verificar si apareció el modal con mensaje de continuidad
            modal_message_visible = await self.is_visible_safe("div:has-text('La placa ingresada al momento de la cotización  cumple con continuidad')", timeout=3000)
            
            if modal_message_visible:
                self.logger.info("📋 Modal de continuidad detectado, haciendo clic en Aceptar...")
                
                # Intentar hacer clic en el botón Aceptar del modal
                if await self.safe_click("#btnOne", timeout=5000):
                    self.logger.info("✅ Modal de continuidad cerrado exitosamente")
                    await self.page.wait_for_timeout(2000)
                    return True
                else:
                    self.logger.error("❌ No se pudo cerrar el modal de continuidad")
                    return False
            else:
                self.logger.info("✅ No se detectó modal de continuidad")
                return False
                
        except Exception as e:
            self.logger.warning(f"⚠️ Error verificando modal de continuidad: {e}")
            return False

    async def process_prima_and_plan_selection(self) -> dict:
        """Proceso completo para extraer prima inicial, seleccionar plan clásico y extraer segunda prima."""
        self.logger.info("🔄 Procesando extracción de primas y selección de plan...")
        
        results = {
            'prima_global': None,
            'prima_clasico': None,
            'success': False
        }
        
        try:
            # 1. Extraer primer valor de prima anual (Plan Global)
            self.logger.info("📊 Extrayendo prima del Plan Global...")
            prima_global = await self.extract_prima_anual_value(max_wait_seconds=20)
            
            if prima_global is None:
                self.logger.error("❌ No se pudo extraer la prima del Plan Global")
                return results
            
            results['prima_global'] = prima_global
            self.logger.info(f"✅ Prima Plan Global: ${prima_global:,.0f}")
            
            # 2. Hacer clic en Plan Autos Clásico
            self.logger.info("🎯 Cambiando a Plan Autos Clásico...")
            if not await self.click_plan_autos_clasico():
                self.logger.error("❌ No se pudo seleccionar Plan Autos Clásico")
                return results
            
            # 3. Verificar y manejar modal de continuidad específico
            await self.check_and_handle_continuity_modal()
            
            # 4. Manejar cualquier otro modal opcional
            if not await self.handle_optional_modal():
                self.logger.warning("⚠️ Hubo problemas manejando el modal opcional, pero continuando...")
            
            # 5. Extraer segundo valor de prima anual (Plan Clásico) - DESPUÉS del cambio de plan
            self.logger.info("📊 Extrayendo prima del Plan Autos Clásico (después del cambio)...")
            prima_clasico = await self.extract_prima_anual_value(max_wait_seconds=20)
            
            if prima_clasico is None:
                self.logger.error("❌ No se pudo extraer la prima del Plan Autos Clásico")
                return results
            
            results['prima_clasico'] = prima_clasico
            results['success'] = True
            
            self.logger.info(f"✅ Prima Plan Autos Clásico: ${prima_clasico:,.0f}")
            
            # Verificar que los valores sean diferentes (como validación)
            if prima_global == prima_clasico:
                self.logger.warning(f"⚠️ Ambas primas tienen el mismo valor (${prima_global:,.0f}). Verificar si el cambio de plan fue efectivo.")
            else:
                self.logger.info(f"✅ Primas diferentes detectadas - Global: ${prima_global:,.0f}, Clásico: ${prima_clasico:,.0f}")
            
            self.logger.info("🎉 Proceso de extracción de primas completado exitosamente")
            
            return results
            
        except Exception as e:
            self.logger.error(f"❌ Error procesando primas y selección de plan: {e}")
            return results

    async def complete_vehicle_information_filling(self) -> dict:
        """Proceso completo para llenar la información adicional del vehículo después del Fasecolda."""
        self.logger.info("📋 Completando información del vehículo...")
        
        results = {
            'prima_global': None,
            'prima_clasico': None,
            'success': False
        }
        
        try:
            # 1. Seleccionar tipo de servicio: Particular
            if not await self.select_service_type():
                self.logger.warning("⚠️ No se pudo seleccionar tipo de servicio")
                return results
            
            # 2. Llenar ciudad
            if not await self.fill_city():
                self.logger.warning("⚠️ No se pudo llenar la ciudad")
                return results
            
            # 3. Llenar placa
            if not await self.fill_plate():
                self.logger.warning("⚠️ No se pudo llenar la placa")
                return results
            
            # 4. Seleccionar cero kilómetros
            if not await self.select_zero_kilometers():
                self.logger.warning("⚠️ No se pudo seleccionar cero kilómetros")
                return results
            
            # 5. Activar cálculo de cotización
            if not await self.trigger_quote_calculation():
                self.logger.warning("⚠️ No se pudo activar el cálculo de cotización")
                return results
            
            # 6. Procesar extracción de primas y selección de planes
            results = await self.process_prima_and_plan_selection()
            
            if results['success']:
                self.logger.info("🎉 Información del vehículo y extracción de primas completada exitosamente")
            else:
                self.logger.warning("⚠️ Hubo problemas en la extracción de primas")
            
            return results
            
        except Exception as e:
            self.logger.error(f"❌ Error completando información del vehículo: {e}")
            return results

    async def process_fasecolda_filling(self) -> dict:
        """Proceso completo de obtención y llenado de códigos Fasecolda y información del vehículo."""
        self.logger.info("🔍 Procesando llenado de código Fasecolda y información del vehículo...")
        
        results = {
            'prima_global': None,
            'prima_clasico': None,
            'success': False
        }
        
        try:
            # Obtener códigos Fasecolda (solo para vehículos nuevos)
            codes = await self.get_fasecolda_code()
            if codes:
                if not await self.fill_fasecolda_with_retry(codes):
                    self.logger.warning("⚠️ No se pudieron llenar los códigos Fasecolda")
                    return results
            else:
                self.logger.info("⏭️ No se obtuvieron códigos Fasecolda (vehículo usado o búsqueda deshabilitada)")
                # Para vehículos usados, aún necesitamos llenar la información adicional
            
            # Completar el llenado de información adicional del vehículo y extraer primas
            results = await self.complete_vehicle_information_filling()
            
            if results['success']:
                self.logger.info("🎉 Proceso de llenado de código Fasecolda, información del vehículo y extracción de primas completado exitosamente")
            else:
                self.logger.warning("⚠️ Hubo problemas en el proceso completo")
            
            return results
            
        except Exception as e:
            self.logger.error(f"❌ Error procesando llenado de Fasecolda: {e}")
            return results
