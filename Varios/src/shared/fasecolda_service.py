"""Módulo para automatización de consultas en Fasecolda."""

import asyncio
import logging
import tkinter as tk
from tkinter import messagebox
from typing import Optional
from playwright.async_api import Page
from ..shared.global_pause_coordinator import request_pause_for_fasecolda_selection


class FasecoldaReferenceNotFoundError(Exception):
    """Excepción lanzada cuando no se encuentra la referencia en Fasecolda."""
    
    def __init__(self, brand: str, reference: str, message: str = None):
        self.brand = brand
        self.reference = reference
        default_message = f"No se encontró la referencia '{reference}' para la marca '{brand}' en Fasecolda"
        super().__init__(message or default_message)

# Constantes para configuración - NUEVA PÁGINA DE FASECOLDA
# Usar directamente la URL del contenido (CloudFront) para evitar iframe
FASECOLDA_URL = 'https://d2eqscyubtix40.cloudfront.net/'
SELECTORS = {
    'basic_search_link': 'text=Búsqueda básica',
    'category': 'select[aria-label="Select category"]',
    'state_button_new': 'button:has-text("Nuevo")',
    'state_button_used': 'button:has-text("Usado")',
    'model': 'select[aria-label="Select model"]',
    'brand': 'select[aria-label="Select marca"]',
    'reference': 'select[aria-label="Select referencia"]',
    'search_button': 'button.bg-btn-primary:has-text("Buscar")',
    'vehicle_card': 'div.px-4.py-4',
    'vehicle_name': 'div.font-bold.items-center.text-base',
    'vehicle_codes': 'p.text-gray-700.text-sm.mt-1.border-b',
    'vehicle_price': 'p.text-gray-700.text-base.font-bold.mt-1'
}

TIMEOUTS = {
    'page_load': 10000,    # Reducido para detección más rápida
    'field_enable': 5000,  # Tiempo para que se habiliten los campos
    'cf_search': 15000,    # Tiempo para búsqueda de resultados
    'retry_interval': 2000, # Intervalo entre reintentos (2 segundos)
    'max_retries': 5       # Máximo 5 reintentos (10 segundos total)
}

SCORE_THRESHOLD = 0.3
SLEEP_DURATION = 1  # seconds

# Marcas disponibles en Fasecolda (extraídas del select)
SUPPORTED_BRANDS = [
    'AUDI', 'BAIC', 'BMW', 'BRENSON', 'BYD', 'CHANGAN', 'CHERY', 'CHEVROLET',
    'CITROEN', 'CUPRA', 'DFSK', 'DFM', 'DFZL', 'DS', 'FAW AMI', 'FIAT', 'FORD',
    'FOTON', 'GAC', 'GREAT WALL', 'HONDA', 'HYUNDAI', 'JAC', 'JAGUAR', 'JEEP',
    'JETOUR', 'JMC', 'KIA', 'KYC', 'LAND ROVER', 'MAXUS', 'MAZDA', 'MERCEDES BENZ',
    'MG', 'MINI', 'MITSUBISHI', 'NISSAN', 'OPEL', 'PEUGEOT', 'PORSCHE', 'RAYSINCE',
    'RENAULT', 'SEAT', 'SHINERAY', 'SMART', 'SSANGYONG', 'SUBARU', 'SUZUKI',
    'TOYOTA', 'VOLKSWAGEN', 'VOLVO', 'ZEEKR'
]

# Patrones de motor y especificaciones técnicas
ENGINE_PATTERNS = [
    # Cilindrada
    '1000CC', '1200CC', '1300CC', '1400CC', '1500CC', '1600CC', '1800CC', '2000CC',
    '2200CC', '2400CC', '2500CC', '2700CC', '3000CC', '3200CC', '3500CC', '4000CC',
    '5000CC', '6000CC',
    # Transmisión
    'TP', 'MT', 'AT', 'CVT', 'AMT', 'DSG',
    # Tipo de motor
    'TURBO', 'T', 'HYBRID', 'ELECTRIC', 'DIESEL', 'GAS', 'GNV', 'FLEX',
    # Configuración
    '4X2', '4X4', 'AWD', 'FWD', 'RWD',
    # Versiones comunes
    'LS', 'LT', 'LTZ', 'RS', 'SPORT', 'PREMIUM', 'LUXURY', 'BASE',
    'GL', 'GLS', 'GLX', 'SE', 'SL', 'SR', 'SV', 'SX',
    # Otros patrones técnicos
    'DOHC', 'SOHC', 'V6', 'V8', 'L4', 'H4'
]

class FasecoldaService:
    """Servicio para consultar códigos CF en Fasecolda."""
    
    def __init__(self, page: Page, logger: logging.Logger = None):
        self.page = page
        self.logger = logger or logging.getLogger(__name__)
        # Rastrear búsqueda actual para manejo de errores
        self._current_brand = None
        self._current_reference = None
        
    async def get_cf_code_comprehensive(
        self,
        category: str,
        state: str,
        model_year: str,
        brand: str,
        reference: str,
        full_reference: str = None
    ) -> Optional[dict]:
        """
        Obtiene códigos CF y CH buscando exhaustivamente en TODAS las referencias disponibles.
        
        Args:
            category: Categoría del vehículo ("Liviano pasajeros", "Motos")
            state: Estado del vehículo ("Nuevo", "Usado")
            model_year: Año del modelo (ej: "2026", "2025")
            brand: Marca del vehículo (ej: "Toyota")
            reference: Referencia base (ej: "Fortuner")
            full_reference: Referencia completa para matching exacto
            
        Returns:
            Diccionario con códigos CF y CH del vehículo seleccionado
        """
        try:
            # Rastrear búsqueda actual
            self._current_brand = brand
            self._current_reference = reference
            
            await self._navigate_to_fasecolda()
            
            # Llenar formulario hasta la marca
            if not await self._fill_vehicle_form_to_brand(category, state, model_year, brand):
                return None
            
            # Obtener todas las referencias disponibles para la marca
            all_references = await self._get_all_references_for_brand(reference)
            
            if not all_references:
                self.logger.error("❌ No se encontraron referencias para la marca especificada")
                # Mostrar popup informativo y lanzar excepción
                self._show_reference_not_found_popup(brand, reference, "No se encontraron referencias para la marca especificada")
                raise FasecoldaReferenceNotFoundError(brand, reference)
            
            # Buscar exhaustivamente en cada referencia
            all_options = await self._search_all_references(all_references, category, state, model_year, brand)
            
            if not all_options:
                self.logger.error("❌ No se encontraron vehículos en ninguna referencia")
                # Mostrar popup informativo y lanzar excepción
                self._show_reference_not_found_popup(brand, reference, "No se encontraron vehículos en ninguna referencia")
                raise FasecoldaReferenceNotFoundError(brand, reference)
            
            # Mostrar diálogo de selección y obtener la opción elegida
            selected_option = await self._show_selection_dialog(all_options, brand, reference)
            
            if selected_option:
                return {
                    'cf_code': selected_option['cf_code'],
                    'ch_code': selected_option['ch_code']
                }
            
            return None
            
        except FasecoldaReferenceNotFoundError:
            # Re-lanzar la excepción específica para que se propague correctamente
            raise
            
        except Exception as e:
            self.logger.error(f"❌ Error en búsqueda exhaustiva de código Fasecolda: {e}")
            return None

    async def get_cf_code(
        self,
        category: str,
        state: str,
        model_year: str,
        brand: str,
        reference: str,
        full_reference: str = None
    ) -> Optional[dict]:
        """
        Obtiene los códigos CF y CH de Fasecolda para un vehículo específico.
        
        Args:
            category: Categoría del vehículo ("Liviano pasajeros", "Motos")
            state: Estado del vehículo ("Nuevo", "Usado")
            model_year: Año del modelo (ej: "2026", "2025")
            brand: Marca del vehículo (ej: "Chevrolet")
            reference: Referencia específica (ej: "Tracker [2] - utilitario deportivo 4x2")
            full_reference: Referencia completa para matching exacto (ej: "CHEVROLET TRACKER [2] LS TP 1200CC T")
            
        Returns:
            Diccionario con códigos CF y CH si se encuentra, None en caso contrario
            Formato: {'cf_code': 'xxxxx', 'ch_code': 'yyyyyyy'}
        """
        try:
            # Rastrear búsqueda actual
            self._current_brand = brand
            self._current_reference = reference
            
            await self._navigate_to_fasecolda()
            
            if not await self._fill_vehicle_form(category, state, model_year, brand, reference):
                return None
                
            if not await self._search_vehicle():
                return None
                
            return await self._extract_codes(full_reference)
            
        except FasecoldaReferenceNotFoundError:
            # Re-lanzar la excepción específica para que se propague correctamente
            raise
            
        except Exception as e:
            self.logger.error(f"❌ Error obteniendo códigos CF/CH: {e}")
            return None
    
    async def _navigate_to_fasecolda(self):
        """Navega a la página de Fasecolda con reintentos y accede a búsqueda básica."""
        self.logger.info("🌐 Navegando a Fasecolda...")
        
        for attempt in range(1, TIMEOUTS['max_retries'] + 1):
            try:
                self.logger.info(f"🔄 Intento {attempt}/{TIMEOUTS['max_retries']} - Navegando a Fasecolda...")
                
                await self.page.goto(FASECOLDA_URL, timeout=TIMEOUTS['page_load'])
                await self.page.wait_for_load_state('networkidle', timeout=TIMEOUTS['page_load'])
                await asyncio.sleep(1)
                
                # Hacer clic en "Búsqueda básica"
                self.logger.info("🔍 Accediendo a búsqueda básica...")
                
                # Esperar a que el link esté visible y hacer clic
                await self.page.click(SELECTORS['basic_search_link'], timeout=10000)
                
                self.logger.info("✅ Clic en búsqueda básica realizado")
                
                # Esperar navegación
                await self.page.wait_for_load_state('networkidle', timeout=TIMEOUTS['page_load'])
                await asyncio.sleep(1)
                
                # Verificar que el formulario cargó correctamente buscando el selector de categoría
                await self.page.wait_for_selector(SELECTORS['category'], timeout=10000)
                
                self.logger.info("✅ Formulario de búsqueda básica cargado correctamente")
                return
                
            except Exception as e:
                self.logger.warning(f"⚠️ Intento {attempt} falló: {e}")
                
                if attempt < TIMEOUTS['max_retries']:
                    self.logger.info(f"⏳ Esperando {TIMEOUTS['retry_interval']/1000} segundos antes del siguiente intento...")
                    await asyncio.sleep(TIMEOUTS['retry_interval'] / 1000)
                else:
                    self.logger.error(f"❌ Error navegando a Fasecolda después de {TIMEOUTS['max_retries']} intentos")
                    raise
        
    async def _fill_vehicle_form(
        self,
        category: str,
        state: str,
        model_year: str,
        brand: str,
        reference: str
    ) -> bool:
        """Llena el formulario con los datos del vehículo usando los nuevos selectores."""
        self.logger.info("📝 Llenando formulario de vehículo...")
        
        try:
            # 1. Seleccionar categoría - Automóvil (value="1")
            self.logger.info("🚗 Seleccionando categoría: Automóvil...")
            await self.page.select_option(SELECTORS['category'], value='1')
            await asyncio.sleep(0.5)
            self.logger.info("✅ Categoría seleccionada")
            
            # 2. Seleccionar estado - Nuevo o Usado (botones, no select)
            self.logger.info(f"📋 Seleccionando estado: {state}...")
            if state.lower() == 'nuevo':
                await self.page.click(SELECTORS['state_button_new'])
            else:
                await self.page.click(SELECTORS['state_button_used'])
            await asyncio.sleep(0.5)
            self.logger.info(f"✅ Estado '{state}' seleccionado")
            
            # 3. Seleccionar año del modelo
            self.logger.info(f"📅 Seleccionando modelo: {model_year}...")
            await self.page.select_option(SELECTORS['model'], label=model_year)
            await asyncio.sleep(0.5)
            self.logger.info(f"✅ Modelo '{model_year}' seleccionado")
            
            # 4. Seleccionar marca
            self.logger.info(f"🏭 Seleccionando marca: {brand}...")
            brand_normalized = brand.title()  # Capitalizar primera letra
            await self.page.select_option(SELECTORS['brand'], label=brand_normalized)
            await asyncio.sleep(1)  # Esperar a que se carguen las referencias
            self.logger.info(f"✅ Marca '{brand}' seleccionada")
            
            # 5. Seleccionar referencia
            self.logger.info(f"🔍 Seleccionando referencia: {reference}...")
            # Buscar la referencia que mejor coincida
            ref_value = await self._find_matching_reference(reference)
            if ref_value:
                await self.page.select_option(SELECTORS['reference'], value=ref_value)
                await asyncio.sleep(0.5)
                self.logger.info(f"✅ Referencia seleccionada")
            else:
                self.logger.warning(f"⚠️ No se encontró referencia exacta para: {reference}")
                # Continuar de todas formas, se manejará en la búsqueda
            
            self.logger.info("✅ Formulario llenado correctamente")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error llenando formulario: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def _find_matching_reference(self, reference: str) -> Optional[str]:
        """
        Busca la referencia que mejor coincida con el texto proporcionado.
        
        Args:
            reference: Texto de referencia a buscar
            
        Returns:
            Value del option que mejor coincida, o None
        """
        try:
            # Obtener todas las opciones del select de referencias
            options = await self.page.evaluate("""
                (selector) => {
                    const select = document.querySelector(selector);
                    if (!select) return [];
                    
                    return Array.from(select.options)
                        .filter(opt => opt.value && opt.value !== '')
                        .map(opt => ({
                            value: opt.value,
                            text: opt.text
                        }));
                }
            """, SELECTORS['reference'])
            
            if not options:
                return None
            
            # Normalizar el texto de búsqueda
            ref_lower = reference.lower()
            
            # Buscar coincidencia exacta primero
            for opt in options:
                if opt['text'].lower() == ref_lower:
                    return opt['value']
            
            # Buscar coincidencia parcial (contiene)
            for opt in options:
                if ref_lower in opt['text'].lower():
                    return opt['value']
            
            # Si no se encuentra, retornar la primera opción
            self.logger.warning(f"⚠️ No se encontró coincidencia para '{reference}', usando primera opción")
            return options[0]['value'] if options else None
            
        except Exception as e:
            self.logger.error(f"❌ Error buscando referencia: {e}")
            return None
    
    async def _select_field_with_retry(self, selector: str, value: str, field_name: str) -> bool:
        """Selecciona un campo con reintentos."""
        self.logger.info(f"🔽 Seleccionando {field_name}: {value}")
        
        try:
            # Esperar a que el campo esté habilitado
            await self._wait_for_field_enabled(selector)
            
            # Obtener el valor para el select
            field_value = await self._get_select_value(selector, value, field_name)
            
            if field_value is None:
                self.logger.warning(f"⚠️ No se encontró {field_name}: {value}")
                return False
            
            # Seleccionar el valor
            await self._select_by_value(selector, field_value)
            
            # Verificar que la selección funcionó
            selected_value = await self.page.evaluate(f"document.querySelector('{selector}').value")
            if selected_value == field_value:
                self.logger.info(f"✅ {field_name} seleccionado correctamente: {value}")
                return True
            else:
                self.logger.warning(f"⚠️ La selección de {field_name} no se aplicó correctamente")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error seleccionando {field_name}: {e}")
            return False

    async def _select_category_with_retries(self, selector: str, category: str, field_name: str) -> bool:
        """Selecciona la categoría con reintentos robustos."""
        for attempt in range(1, TIMEOUTS['max_retries'] + 1):
            try:
                self.logger.info(f"🔄 Intento {attempt}/{TIMEOUTS['max_retries']} - Seleccionando {field_name}: {category}")
                
                # Esperar a que el selector exista
                await self.page.wait_for_selector(selector, timeout=5000)
                
                # Obtener el valor para el select
                field_value = await self._get_select_value(selector, category, field_name)
                
                if field_value is None:
                    raise Exception(f"No se encontró la opción {category}")
                
                # Seleccionar el valor
                await self._select_by_value(selector, field_value)
                
                # Verificar que la selección funcionó
                selected_value = await self.page.evaluate(f"document.querySelector('{selector}').value")
                if selected_value == field_value:
                    self.logger.info(f"✅ {field_name} seleccionado correctamente: {category}")
                    return True
                else:
                    raise Exception(f"La selección no se aplicó correctamente")
                
            except Exception as e:
                self.logger.warning(f"⚠️ Intento {attempt} falló para {field_name}: {e}")
                
                if attempt < TIMEOUTS['max_retries']:
                    self.logger.info(f"⏳ Esperando {TIMEOUTS['retry_interval']/1000} segundos antes del siguiente intento...")
                    await asyncio.sleep(TIMEOUTS['retry_interval'] / 1000)
                else:
                    self.logger.error(f"❌ Error seleccionando {field_name} después de {TIMEOUTS['max_retries']} intentos")
                    return False
        
        return False
    
    async def _get_select_value(self, selector: str, search_value: str, field_type: str) -> Optional[str]:
        """
        Método unificado para obtener el valor de cualquier select.
        
        Args:
            selector: Selector CSS del select
            search_value: Valor a buscar en las opciones
            field_type: Tipo de campo para aplicar lógica específica
            
        Returns:
            Valor del option encontrado o None si no se encuentra
        """
        # Mapeos estáticos para campos conocidos
        static_mappings = {
            "categoría": {
                "Liviano carga": "2",
                "Liviano pasajeros": "1", 
                "Motos": "3",
                "Pesado carga": "4",
                "Pesado pasajeros": "5",
                "Pesado semirremolque": "6"
            },
            "estado": {
                "Nuevo": "1",
                "Usado": "0"
            }
        }
        
        # Verificar si existe un mapeo estático para este campo
        if field_type in static_mappings:
            return static_mappings[field_type].get(search_value, "false")
        
        # Para campos dinámicos, buscar en las opciones del DOM
        try:
            options = await self.page.query_selector_all(f'{selector} option')
            for option in options:
                text = await option.inner_text()
                text_clean = text.strip()
                
                # Lógica de matching según el tipo de campo
                if field_type == "marca":
                    # Para marcas, hacer comparación case-insensitive
                    if text_clean.lower() == search_value.lower():
                        return await option.get_attribute('value')
                else:
                    # Para otros campos (modelo, referencia), comparación exacta
                    if text_clean == search_value:
                        return await option.get_attribute('value')
            
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Error buscando valor en {field_type}: {e}")
            return None
    
    async def _wait_for_field_enabled(self, selector: str, timeout: int = None):
        """Espera a que un campo se habilite con manejo de errores mejorado y reintentos."""
        timeout = timeout or TIMEOUTS['field_enable']
        
        for attempt in range(1, 4):  # 3 intentos máximo para campos
            try:
                self.logger.debug(f"🔄 Intento {attempt}/3 - Esperando que se habilite {selector}")
                
                # Primero verificar si el elemento existe
                await self.page.wait_for_selector(selector, timeout=3000)
                
                # Luego esperar a que se habilite
                await self.page.wait_for_function(
                    f"() => {{ const el = document.querySelector('{selector}'); return el && !el.disabled; }}",
                    timeout=timeout
                )
                self.logger.debug(f"✅ Campo {selector} habilitado")
                return
                
            except Exception as e:
                self.logger.warning(f"⚠️ Intento {attempt} - Campo {selector} no se habilitó: {e}")
                
                if attempt < 3:
                    await asyncio.sleep(1)  # Esperar 1 segundo entre intentos
                else:
                    self.logger.warning(f"⚠️ Campo {selector} no se habilitó después de 3 intentos")
                    # Continuar sin fallar, ya que algunos campos pueden no necesitar habilitación
                    pass
    
    async def _select_by_value(self, selector: str, value: str):
        """Selecciona una opción por su valor usando JavaScript."""
        js_code = f"""
        () => {{
            const select = document.querySelector('{selector}');
            if (select) {{
                select.value = '{value}';
                select.dispatchEvent(new Event('change', {{ bubbles: true }}));
                // También disparar el evento en select2 si existe jQuery
                if (typeof $ !== 'undefined') {{
                    $(select).trigger('change');
                }}
                return true;
            }}
            return false;
        }}
        """
        
        result = await self.page.evaluate(js_code)
        if not result:
            self.logger.error(f"❌ No se pudo seleccionar valor '{value}' en '{selector}'")
            
    async def _search_vehicle(self) -> bool:
        """Hace clic en el botón de búsqueda."""
        self.logger.info("🔍 Iniciando búsqueda...")
        try:
            await self.page.click(SELECTORS['search_button'])
            await self.page.wait_for_load_state('networkidle')
            self.logger.info("✅ Búsqueda completada")
            return True
        except Exception as e:
            self.logger.error(f"❌ Error en búsqueda: {e}")
            return False
    
    async def _extract_codes(self, full_reference: str = None) -> Optional[dict]:
        """Extrae los códigos CF y CH basado en la nueva estructura HTML."""
        self.logger.info("📊 Extrayendo códigos CF y CH...")
        
        try:
            # Esperar a que aparezcan las tarjetas de vehículos
            await asyncio.sleep(2)  # Dar tiempo para que carguen los resultados
            
            # Buscar todas las tarjetas de vehículos
            vehicle_cards = await self.page.query_selector_all(SELECTORS['vehicle_card'])
            
            self.logger.info(f"📋 Encontradas {len(vehicle_cards)} tarjetas de vehículos")
            
            if len(vehicle_cards) == 0:
                self.logger.error("❌ No se encontraron resultados")
                # Mostrar popup y lanzar excepción
                brand = self._current_brand or 'Desconocida'
                reference = self._current_reference or 'Desconocida'
                self._show_reference_not_found_popup(brand, reference, "No se encontraron resultados para la búsqueda")
                raise FasecoldaReferenceNotFoundError(brand, reference)
            
            if len(vehicle_cards) == 1:
                # Solo un resultado, extraer ambos códigos directamente
                codes = await self._extract_codes_from_card(vehicle_cards[0])
                ch_info = f" - CH: {codes['ch_code']}" if codes['ch_code'] else ""
                self.logger.info(f"✅ Un solo resultado encontrado - CF: {codes['cf_code']}{ch_info}")
                return codes
            
            # Múltiples resultados, procesar y encontrar la mejor coincidencia
            return await self._process_multiple_codes_results_new(vehicle_cards, full_reference)
                
        except Exception as e:
            self.logger.error(f"❌ Error extrayendo códigos CF/CH: {e}")
            return None
    
    async def _extract_codes_from_card(self, card_element) -> dict:
        """Extrae códigos CF y CH de una tarjeta de vehículo de la nueva estructura."""
        try:
            import re
            
            # Extraer códigos CF y CH del elemento de códigos
            codes_element = await card_element.query_selector(SELECTORS['vehicle_codes'])
            if not codes_element:
                return {'cf_code': None, 'ch_code': None}
            
            codes_text = await codes_element.text_content()
            codes_text = codes_text.strip()
            
            # Extraer CF y CH con regex
            # Formato esperado: "CF - 03033048 CH - 03001135"
            cf_match = re.search(r'CF\s*-\s*(\d+)', codes_text)
            ch_match = re.search(r'CH\s*-\s*(\d+)', codes_text)
            
            cf_code = cf_match.group(1) if cf_match else None
            ch_code = ch_match.group(1) if ch_match else cf_code
            
            return {
                'cf_code': cf_code,
                'ch_code': ch_code
            }
        except Exception as e:
            self.logger.warning(f"⚠️ Error extrayendo códigos de tarjeta: {e}")
            return {'cf_code': None, 'ch_code': None}
    
    async def _extract_result_data_from_card(self, card_element, index: int, full_reference: str = None) -> dict:
        """Extrae toda la información de una tarjeta de vehículo."""
        try:
            import re
            
            # Extraer códigos CF y CH
            codes = await self._extract_codes_from_card(card_element)
            cf_code = codes['cf_code']
            ch_code = codes['ch_code']
            
            # Extraer nombre del vehículo
            name_element = await card_element.query_selector(SELECTORS['vehicle_name'])
            vehicle_name = await name_element.text_content() if name_element else ""
            vehicle_name = vehicle_name.strip()
            
            # Extraer precio
            price_element = await card_element.query_selector(SELECTORS['vehicle_price'])
            insured_value = await price_element.text_content() if price_element else "No disponible"
            insured_value = insured_value.strip()
            
            # Calcular score de similitud si tenemos referencia de configuración
            score = 0
            if full_reference:
                score = self._calculate_similarity_score(full_reference, vehicle_name)
            
            return {
                'index': index + 1,
                'cf_code': cf_code,
                'ch_code': ch_code,
                'full_reference': vehicle_name,
                'insured_value': insured_value,
                'score': score
            }
            
        except Exception as e:
            self.logger.warning(f"⚠️ Error procesando tarjeta {index + 1}: {e}")
            return None
    
    async def _process_multiple_codes_results_new(self, vehicle_cards, full_reference: str = None) -> Optional[dict]:
        """Procesa múltiples tarjetas de vehículos con opción de selección manual."""
        self.logger.info(f"🔍 Múltiples resultados, analizando similitudes...")
        
        # Extraer datos de todas las tarjetas
        all_results = []
        best_match = None
        best_score = -1
        
        for i, card in enumerate(vehicle_cards):
            result_data = await self._extract_result_data_from_card(card, i, full_reference)
            
            if result_data:
                all_results.append(result_data)
                ch_info = f" - CH: {result_data['ch_code']}" if result_data['ch_code'] else ""
                value_info = f" - Valor: {result_data['insured_value']}" if result_data.get('insured_value') else ""
                self.logger.info(f"📝 Resultado {result_data['index']}: CF: {result_data['cf_code']}{ch_info}{value_info} - {result_data['full_reference']} (Score: {result_data['score']:.2f})")
                
                # Verificar si es la mejor coincidencia hasta ahora
                if result_data['score'] > best_score:
                    best_score = result_data['score']
                    best_match = result_data
        
        # Si hay múltiples resultados, permitir selección manual
        if len(all_results) > 1:
            return await self._show_selection_dialog(all_results, self._current_brand, self._current_reference)
        elif all_results:
            return {
                'cf_code': all_results[0]['cf_code'],
                'ch_code': all_results[0]['ch_code']
            }
        
        return None
    
    async def _process_multiple_results(self, result_containers, full_reference: str = None) -> Optional[str]:
        """Procesa múltiples resultados y encuentra la mejor coincidencia."""
        self.logger.info(f"🔍 Múltiples resultados, analizando similitudes...")
        
        best_match = None
        best_score = -1
        
        for i, container in enumerate(result_containers):
            result_data = await self._extract_result_data(container, i, full_reference)
            
            if result_data:
                ch_info = f" - CH: {result_data['ch_code']}" if result_data['ch_code'] else ""
                self.logger.info(f"📝 Resultado {result_data['index']}: CF: {result_data['cf_code']}{ch_info} - {result_data['full_reference']} (Score: {result_data['score']:.2f})")
                
                # Verificar si es la mejor coincidencia hasta ahora
                if result_data['score'] > best_score:
                    best_score = result_data['score']
                    best_match = result_data
        
        # Determinar el resultado a retornar
        return await self._select_best_result(best_match, best_score, result_containers[0])
    
    async def _process_multiple_codes_results(self, result_containers, full_reference: str = None) -> Optional[dict]:
        """Procesa múltiples resultados con opción de selección manual."""
        self.logger.info(f"🔍 Múltiples resultados, analizando similitudes...")
        
        # Extraer datos de todos los resultados
        all_results = []
        best_match = None
        best_score = -1
        
        for i, container in enumerate(result_containers):
            result_data = await self._extract_result_data(container, i, full_reference)
            
            if result_data:
                all_results.append(result_data)
                ch_info = f" - CH: {result_data['ch_code']}" if result_data['ch_code'] else ""
                value_info = f" - Valor: {result_data['insured_value']}" if result_data.get('insured_value') else ""
                self.logger.info(f"📝 Resultado {result_data['index']}: CF: {result_data['cf_code']}{ch_info}{value_info} - {result_data['full_reference']} (Score: {result_data['score']:.2f})")
                
                # Verificar si es la mejor coincidencia hasta ahora
                if result_data['score'] > best_score:
                    best_score = result_data['score']
                    best_match = result_data
        
        # Si hay múltiples resultados, permitir selección manual
        if len(all_results) > 1:
            # Verificar si el mejor resultado tiene un score suficientemente alto
            SCORE_THRESHOLD = 0.8
            if best_score < SCORE_THRESHOLD:
                # Score bajo, solicitar selección manual
                self.logger.info(f"⚠️ Score más alto es {best_score:.2f} (< {SCORE_THRESHOLD}), solicitando selección manual...")
                
                # Preparar opciones para selección
                formatted_results = []
                for result in all_results:
                    formatted_results.append({
                        'cf_code': result['cf_code'],
                        'ch_code': result['ch_code'],
                        'description': result['full_reference'],
                        'insured_value': result.get('insured_value', 'No disponible'),
                        'score': result['score']
                    })
                
                # Solicitar selección manual (pausará todas las automatizaciones)
                selected_index = await request_pause_for_fasecolda_selection(
                    company='fasecolda',  # Identificador genérico
                    options=list(range(1, len(formatted_results) + 1)),
                    results=formatted_results
                )
                
                # Retornar el resultado seleccionado
                selected_result = all_results[selected_index]
                return {
                    'cf_code': selected_result['cf_code'], 
                    'ch_code': selected_result['ch_code']
                }
        
        # Si solo hay un resultado o el score es alto, usar lógica automática
        return await self._select_best_codes_result(best_match, best_score, result_containers[0])
    
    async def _select_best_result(self, best_match: dict, best_score: float, first_container) -> str:
        """Selecciona el mejor resultado basado en el score o usa fallback."""
        if best_match and best_score > SCORE_THRESHOLD:
            self.logger.info(f"✅ Mejor coincidencia encontrada - CF: {best_match['cf_code']} (Score: {best_score:.2f})")
            return best_match['cf_code']
        elif best_match:
            self.logger.warning(f"⚠️ Score bajo ({best_score:.2f}), retornando mejor opción - CF: {best_match['cf_code']}")
            return best_match['cf_code']
        else:
            # Fallback al primer resultado si no hay matches
            self.logger.warning("⚠️ No se encontraron coincidencias, retornando primer resultado")
            cf_code = await self._extract_cf_from_container(first_container)
            self.logger.warning(f"⚠️ Retornando primer CF como fallback: {cf_code}")
            return cf_code
    
    async def _select_best_codes_result(self, best_match: dict, best_score: float, first_container) -> dict:
        """Selecciona el mejor resultado basado en el score o usa fallback para códigos CF y CH."""
        if best_match and best_score > SCORE_THRESHOLD:
            ch_info = f" - CH: {best_match['ch_code']}" if best_match['ch_code'] else ""
            self.logger.info(f"✅ Mejor coincidencia encontrada - CF: {best_match['cf_code']}{ch_info} (Score: {best_score:.2f})")
            return {'cf_code': best_match['cf_code'], 'ch_code': best_match['ch_code']}
        elif best_match:
            ch_info = f" - CH: {best_match['ch_code']}" if best_match['ch_code'] else ""
            self.logger.warning(f"⚠️ Score bajo ({best_score:.2f}), retornando mejor opción - CF: {best_match['cf_code']}{ch_info}")
            return {'cf_code': best_match['cf_code'], 'ch_code': best_match['ch_code']}
        else:
            # Fallback al primer resultado si no hay matches
            self.logger.warning("⚠️ No se encontraron coincidencias, retornando primer resultado")
            codes = await self._extract_codes_from_container(first_container)
            ch_info = f" - CH: {codes['ch_code']}" if codes['ch_code'] else ""
            self.logger.warning(f"⚠️ Retornando primer resultado como fallback - CF: {codes['cf_code']}{ch_info}")
            return codes
    
    def _calculate_similarity_score(self, reference: str, candidate: str) -> float:
        """
        Calcula un score de similitud entre la referencia de configuración y un candidato.
        
        Args:
            reference: Referencia de configuración (ej: "CHEVROLET TRACKER [2] LS TP 1200CC T")
            candidate: Candidato encontrado (ej: "CHEVROLET TRACKER [2] LS TP 1200CC T")
            
        Returns:
            Score de similitud entre 0.0 y 1.0
        """
        if not reference or not candidate:
            return 0.0
        
        # Normalizar strings (mayúsculas, espacios)
        ref_normalized = reference.upper().strip()
        cand_normalized = candidate.upper().strip()
        
        # Coincidencia exacta = score perfecto
        if ref_normalized == cand_normalized:
            return 1.0
        
        # Dividir en tokens para análisis granular
        ref_tokens = set(ref_normalized.split())
        cand_tokens = set(cand_normalized.split())
        
        # Calcular intersección de tokens
        common_tokens = ref_tokens.intersection(cand_tokens)
        total_tokens = ref_tokens.union(cand_tokens)
        
        # Score base por tokens comunes (Jaccard similarity)
        token_score = len(common_tokens) / len(total_tokens) if total_tokens else 0.0
        
        # Bonus por patrones específicos importantes
        bonus = self._calculate_pattern_bonus(ref_normalized, cand_normalized)
        
        # Score final (limitado a 1.0)
        return min(1.0, token_score + bonus)
    
    def _calculate_pattern_bonus(self, ref_normalized: str, cand_normalized: str) -> float:
        """Calcula bonificaciones por patrones específicos en las referencias."""
        bonus = 0.0
        
        # Bonus si coincide la marca exacta (peso alto)
        for brand in SUPPORTED_BRANDS:
            if brand in ref_normalized and brand in cand_normalized:
                bonus += 0.25
                break
        
        # Bonus si coincide el modelo exacto (ej: TRACKER [2]) - peso muy alto
        import re
        ref_model_match = re.search(r'(\w+)\s*\[[^\]]+\]', ref_normalized)
        cand_model_match = re.search(r'(\w+)\s*\[[^\]]+\]', cand_normalized)
        
        if ref_model_match and cand_model_match:
            if ref_model_match.group() == cand_model_match.group():
                bonus += 0.35
        
        # Bonus por coincidencias de especificaciones técnicas
        engine_matches = 0
        for pattern in ENGINE_PATTERNS:
            if pattern in ref_normalized and pattern in cand_normalized:
                engine_matches += 1
        
        # Dar más peso si hay múltiples coincidencias técnicas
        if engine_matches > 0:
            bonus += min(0.3, engine_matches * 0.05)  # Máximo 0.3, 0.05 por cada coincidencia
        
        return bonus

    async def _fill_vehicle_form_to_brand(self, category: str, state: str, model_year: str, brand: str) -> bool:
        """Llena el formulario hasta la marca (sin seleccionar referencia específica)."""
        try:
            # 1. Seleccionar categoría - Automóvil (value="1")
            self.logger.info("🚗 Seleccionando categoría: Automóvil...")
            await self.page.select_option(SELECTORS['category'], value='1')
            await asyncio.sleep(0.5)
            
            # 2. Seleccionar estado - Nuevo o Usado (botones, no select)
            self.logger.info(f"📋 Seleccionando estado: {state}...")
            if state.lower() == 'nuevo':
                await self.page.click(SELECTORS['state_button_new'])
            else:
                await self.page.click(SELECTORS['state_button_used'])
            await asyncio.sleep(0.5)
            
            # 3. Seleccionar año del modelo
            self.logger.info(f"📅 Seleccionando modelo: {model_year}...")
            await self.page.select_option(SELECTORS['model'], label=model_year)
            await asyncio.sleep(0.5)
            
            # 4. Seleccionar marca
            self.logger.info(f"🏭 Seleccionando marca: {brand}...")
            brand_normalized = brand.title()
            await self.page.select_option(SELECTORS['brand'], label=brand_normalized)
            await asyncio.sleep(1)  # Esperar a que se carguen las referencias
            
            self.logger.info("✅ Formulario llenado hasta marca correctamente")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error llenando formulario hasta marca: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def _get_all_references_for_brand(self, reference_filter: str = None) -> list:
        """Obtiene todas las referencias disponibles para la marca seleccionada."""
        try:
            # Esperar a que el select de referencias esté disponible
            await self.page.wait_for_selector(SELECTORS['reference'], timeout=5000)
            await asyncio.sleep(0.5)
            
            # Obtener todas las opciones del dropdown de referencias usando JavaScript
            options_data = await self.page.evaluate("""
                (selector) => {
                    const select = document.querySelector(selector);
                    if (!select) return [];
                    
                    return Array.from(select.options)
                        .filter(opt => opt.value && opt.value !== '')
                        .map(opt => ({
                            value: opt.value,
                            text: opt.text
                        }));
                }
            """, SELECTORS['reference'])
            
            all_references = []
            for opt_data in options_data:
                # Si hay filtro, solo incluir referencias que contengan el filtro
                if not reference_filter or reference_filter.lower() in opt_data['text'].lower():
                    all_references.append({
                        'text': opt_data['text'].strip(),
                        'value': opt_data['value']
                    })
            
            self.logger.info(f"🔍 Encontradas {len(all_references)} referencias disponibles")
            for i, ref in enumerate(all_references[:5]):  # Mostrar solo las primeras 5 en el log
                self.logger.info(f"  {i+1}. {ref['text']}")
            
            if len(all_references) > 5:
                self.logger.info(f"  ... y {len(all_references) - 5} más")
            
            return all_references
            
        except Exception as e:
            self.logger.error(f"❌ Error obteniendo referencias: {e}")
            return []

    async def _search_all_references(self, references: list, category: str, state: str, model_year: str, brand: str) -> list:
        """Busca exhaustivamente en todas las referencias y recopila todos los resultados."""
        all_options = []
        option_counter = 1
        
        self.logger.info(f"🔍 Iniciando búsqueda comprensiva en {len(references)} referencias")
        
        for ref_index, reference in enumerate(references):
            self.logger.info(f"🎯 Procesando referencia {ref_index + 1}/{len(references)}: {reference['text']}")
            
            try:
                # Seleccionar esta referencia
                await self.page.select_option(SELECTORS['reference'], value=reference['value'])
                await asyncio.sleep(0.5)
                
                # Hacer clic en buscar
                self.logger.info(f"🔍 Ejecutando búsqueda para: {reference['text']}")
                await self.page.click(SELECTORS['search_button'])
                await asyncio.sleep(2)  # Esperar a que carguen los resultados
                
                # Buscar tarjetas de vehículos
                vehicle_cards = await self.page.query_selector_all(SELECTORS['vehicle_card'])
                
                if vehicle_cards:
                    self.logger.info(f"✅ Encontradas {len(vehicle_cards)} tarjeta(s) en: {reference['text']}")
                    
                    # Procesar cada tarjeta
                    reference_results = []
                    for card_index, card in enumerate(vehicle_cards):
                        result_data = await self._extract_complete_result_data_from_card(card, option_counter, reference['text'])
                        if result_data and self._is_valid_unique_result(result_data, all_options):
                            reference_results.append(result_data)
                            all_options.append(result_data)
                            option_counter += 1
                            self.logger.info(f"📊 Resultado {card_index + 1}: CF={result_data['cf_code']}, CH={result_data['ch_code']}")
                    
                    self.logger.info(f"🎯 Agregados {len(reference_results)} resultados únicos de la referencia: {reference['text']}")
                else:
                    self.logger.warning(f"⚠️ No se encontraron tarjetas de vehículos para: {reference['text']}")
                
            except Exception as e:
                self.logger.error(f"❌ Error buscando en referencia {reference['text']}: {e}")
                continue
        
        self.logger.info(f"🎉 Búsqueda comprensiva completada: {len(all_options)} opciones únicas encontradas")
        return all_options

    async def _extract_complete_result_data_from_card(self, card_element, option_number: int, reference_group: str) -> dict:
        """Extrae datos completos de una tarjeta de vehículo."""
        try:
            import re
            
            # Extraer códigos CF y CH
            codes = await self._extract_codes_from_card(card_element)
            cf_code = codes['cf_code']
            ch_code = codes['ch_code']
            
            # Extraer nombre del vehículo (descripción completa)
            name_element = await card_element.query_selector(SELECTORS['vehicle_name'])
            full_description = await name_element.text_content() if name_element else ""
            full_description = full_description.strip()
            
            # Extraer valor asegurado (precio)
            insured_value = "No disponible"
            try:
                price_element = await card_element.query_selector(SELECTORS['vehicle_price'])
                if price_element:
                    insured_value = await price_element.text_content()
                    insured_value = insured_value.strip()
            except:
                pass
            
            return {
                'option_number': option_number,
                'cf_code': cf_code,
                'ch_code': ch_code,
                'description': full_description,
                'insured_value': insured_value,
                'reference_group': reference_group
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error extrayendo datos de la tarjeta: {e}")
            return None

    async def _return_to_search_form(self):
        """Vuelve al formulario de búsqueda de manera optimizada (sin recargar página)."""
        try:
            self.logger.info("🔄 Volviendo al formulario de búsqueda...")
            
            # Buscar el botón "Nueva búsqueda" o similar
            nueva_busqueda_selectors = [
                'a[href="/fasecolda/consulta"]',  # Enlace directo a consulta
                'a[onclick*="consulta"]',          # Botón con onclick que contiene consulta
                'button:has-text("Nueva búsqueda")', # Botón con texto específico
                'a:has-text("Buscar")',           # Enlace con texto Buscar
                'a:has-text("Nueva")',            # Enlace con texto Nueva
                '.btn:has-text("Buscar")',        # Botón con clase btn y texto Buscar
            ]
            
            # Intentar encontrar y hacer clic en el botón de nueva búsqueda
            for selector in nueva_busqueda_selectors:
                try:
                    element = await self.page.query_selector(selector)
                    if element:
                        await element.click()
                        await self.page.wait_for_load_state('networkidle', timeout=5000)
                        self.logger.info("✅ Vuelto al formulario usando botón de nueva búsqueda")
                        return
                except:
                    continue
            
            # Si no encontramos botón específico, intentar navegación directa
            current_url = self.page.url
            if 'fasecolda' in current_url and '/consulta' not in current_url:
                await self.page.goto(FASECOLDA_URL)
                await self.page.wait_for_load_state('networkidle', timeout=5000)
                self.logger.info("✅ Vuelto al formulario mediante navegación directa")
                return
            
            # Si ya estamos en la página de consulta, no hacer nada
            if '/consulta' in current_url:
                self.logger.info("✅ Ya estamos en el formulario de búsqueda")
                return
                
        except Exception as e:
            self.logger.warning(f"⚠️ Error volviendo al formulario optimizado: {e}")
            # Fallback: recargar página completa
            await self.page.goto(FASECOLDA_URL)
            await self.page.wait_for_load_state('networkidle')
            self.logger.info("✅ Vuelto al formulario mediante recarga completa (fallback)")

    async def _restore_form_state(self, category: str, state: str, model_year: str, brand: str):
        """Restaura el estado del formulario después de volver desde resultados."""
        try:
            self.logger.info("🔄 Restaurando estado del formulario...")
            
            # Verificar si los campos ya están llenos
            current_category = await self.page.evaluate(f"document.querySelector('{SELECTORS['category']}').value")
            
            if not current_category or current_category == "false":
                # Si los campos están vacíos, llenar todo el formulario
                self.logger.info("📝 Llenando formulario completo...")
                await self._fill_vehicle_form_to_brand(category, state, model_year, brand)
            else:
                # Si ya están llenos, solo verificar que estén correctos
                self.logger.info("✅ Formulario ya está en estado correcto")
                
        except Exception as e:
            self.logger.warning(f"⚠️ Error restaurando formulario: {e}")
            # Fallback: llenar formulario completo
            await self._fill_vehicle_form_to_brand(category, state, model_year, brand)

    def _is_valid_unique_result(self, result_data: dict, existing_results: list) -> bool:
        """Verifica que el resultado sea válido y único."""
        if not result_data or not result_data.get('cf_code'):
            return False
        
        # Verificar que no sea duplicado
        for existing in existing_results:
            if (existing.get('cf_code') == result_data.get('cf_code') and 
                existing.get('ch_code') == result_data.get('ch_code')):
                return False
        
        return True

    def _show_reference_not_found_popup(self, brand: str, reference: str, details: str = "") -> None:
        """
        Muestra un popup informativo cuando no se encuentra la referencia en Fasecolda.
        
        Args:
            brand: Marca del vehículo
            reference: Referencia buscada
            details: Detalles adicionales del error
        """
        try:
            # Crear ventana temporal para mostrar el popup
            root = tk.Tk()
            root.withdraw()  # Ocultar la ventana principal
            
            # Configurar ventana para que aparezca en primer plano
            root.attributes('-topmost', True)  # Siempre encima
            root.lift()  # Elevar la ventana
            root.focus_force()  # Forzar el foco
            
            # En Windows, traer al frente
            try:
                root.wm_attributes('-topmost', 1)
                root.after(100, lambda: root.wm_attributes('-topmost', 0))  # Quitar topmost después de 100ms
            except:
                pass  # Si falla en otros sistemas operativos
            
            # Configurar el mensaje del popup
            title = "⚠️ Referencia Fasecolda No Encontrada"
            
            message = f"No se encontró la referencia en Fasecolda:\n\n"
            message += f"🚗 Marca: {brand}\n"
            message += f"🔍 Referencia: {reference}\n\n"
            
            if details:
                message += f"📋 Detalle: {details}\n\n"
            
            message += "❗ El proceso se ha detenido completamente.\n\n"
            message += "🚫 Los navegadores de cotización NO se abrirán.\n\n"
            message += "📝 Para continuar:\n"
            message += "• Verifica los datos del vehículo\n"
            message += "• Actualiza la referencia en la edición del cliente\n"
            message += "• O ingresa manualmente los códigos CF y CH"
            
            # Mostrar popup modal que se mantenga en primer plano
            messagebox.showerror(title, message, parent=root)
            
            # Limpiar recursos de tkinter
            root.destroy()
            
            self.logger.info(f"💬 Popup mostrado: Referencia {reference} no encontrada para {brand}")
            
        except Exception as e:
            self.logger.warning(f"⚠️ Error mostrando popup de referencia no encontrada: {e}")

    async def _show_selection_dialog(self, all_options: list, brand: str, reference: str) -> dict:
        """Muestra un diálogo de selección en la interfaz GUI."""
        try:
            # Importar aquí para evitar dependencias circulares
            from ..interfaces.fasecolda_selection_dialog import FasecoldaSelectionDialog
            
            # Crear y mostrar el diálogo
            dialog = FasecoldaSelectionDialog(all_options, brand, reference)
            selected_option = dialog.show()
            
            return selected_option
            
        except Exception as e:
            self.logger.error(f"❌ Error mostrando diálogo de selección: {e}")
            import traceback
            traceback.print_exc()
            return None
