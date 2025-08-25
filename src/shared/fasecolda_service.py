"""Módulo para automatización de consultas en Fasecolda."""

import asyncio
import logging
from typing import Optional
from playwright.async_api import Page
from ..shared.global_pause_coordinator import request_pause_for_fasecolda_selection

# Constantes para configuración
FASECOLDA_URL = 'https://www.fasecolda.com/guia-de-valores-old/'
SELECTORS = {
    'category': '#fe-categoria',
    'state': '#fe-estado', 
    'model': '#fe-modelo',
    'brand': '#fe-marca',
    'reference': '#fe-refe1',
    'search_button': 'button.btn.btn-red.fe-submit',
    'result_container': '.car-result-container',
    'cf_code': '.car-code',
    'car_brand': '.car-brand',
    'car_reference_2': '.car-reference-2',
    'car_reference_3': '.car-reference-3'
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
            await self._navigate_to_fasecolda()
            
            # Llenar formulario hasta la marca
            if not await self._fill_vehicle_form_to_brand(category, state, model_year, brand):
                return None
            
            # Obtener todas las referencias disponibles para la marca
            all_references = await self._get_all_references_for_brand(reference)
            
            if not all_references:
                self.logger.error("❌ No se encontraron referencias para la marca especificada")
                return None
            
            # Buscar exhaustivamente en cada referencia
            all_options = await self._search_all_references(all_references, category, state, model_year, brand)
            
            if not all_options:
                self.logger.error("❌ No se encontraron vehículos en ninguna referencia")
                return None
            
            # Mostrar diálogo de selección y obtener la opción elegida
            selected_option = await self._show_selection_dialog(all_options, brand, reference)
            
            if selected_option:
                return {
                    'cf_code': selected_option['cf_code'],
                    'ch_code': selected_option['ch_code']
                }
            
            return None
            
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
            await self._navigate_to_fasecolda()
            
            if not await self._fill_vehicle_form(category, state, model_year, brand, reference):
                return None
                
            if not await self._search_vehicle():
                return None
                
            return await self._extract_codes(full_reference)
            
        except Exception as e:
            self.logger.error(f"❌ Error obteniendo códigos CF/CH: {e}")
            return None
    
    async def _navigate_to_fasecolda(self):
        """Navega a la página de Fasecolda con reintentos."""
        self.logger.info("🌐 Navegando a Fasecolda...")
        
        for attempt in range(1, TIMEOUTS['max_retries'] + 1):
            try:
                self.logger.info(f"🔄 Intento {attempt}/{TIMEOUTS['max_retries']} - Navegando a Fasecolda...")
                
                await self.page.goto(FASECOLDA_URL, timeout=TIMEOUTS['page_load'])
                await self.page.wait_for_load_state('networkidle', timeout=TIMEOUTS['page_load'])
                
                # Verificar que la página cargó correctamente buscando el selector de categoría
                await self.page.wait_for_selector(SELECTORS['category'], timeout=5000)
                
                self.logger.info("✅ Página de Fasecolda cargada correctamente")
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
        """Llena el formulario con los datos del vehículo usando el método optimizado con reintentos."""
        self.logger.info("📝 Llenando formulario de vehículo...")
        
        try:
            # Configuración de campos: (nombre, emoji, selector, valor, wait_enabled, is_category)
            fields = [
                ("categoría", "📋", SELECTORS['category'], category, False, True),
                ("estado", "🏷️", SELECTORS['state'], state, True, False),
                ("modelo", "📅", SELECTORS['model'], model_year, True, False),
                ("marca", "🚗", SELECTORS['brand'], brand, True, False),
                ("referencia", "🔍", SELECTORS['reference'], reference, True, False),
            ]
            
            for field_name, emoji, selector, value, wait_enabled, is_category in fields:
                self.logger.info(f"{emoji} Seleccionando {field_name}: {value}")
                
                # Para la categoría, usar reintentos especiales
                if is_category:
                    success = await self._select_category_with_retries(selector, value, field_name)
                    if not success:
                        self.logger.error(f"❌ No se pudo seleccionar {field_name} después de múltiples intentos")
                        return False
                else:
                    # Para otros campos, usar lógica normal
                    if wait_enabled:
                        await self._wait_for_field_enabled(selector)
                    
                    # Obtener el valor para el select
                    field_value = await self._get_select_value(selector, value, field_name)
                    
                    if field_value is None:
                        self.logger.warning(f"⚠️ No se encontró {field_name}: {value} - continuando...")
                        continue  # Continuar con el siguiente campo en lugar de fallar
                    
                    # Seleccionar el valor
                    await self._select_by_value(selector, field_value)
                
                await asyncio.sleep(SLEEP_DURATION)
            
            self.logger.info("✅ Formulario llenado correctamente")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error llenando formulario: {e}")
            import traceback
            traceback.print_exc()
            return False
    
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
        """Extrae los códigos CF y CH basado en la referencia completa usando scoring de similitud."""
        self.logger.info("📊 Extrayendo códigos CF y CH...")
        
        try:
            # Esperar a que aparezcan los resultados
            await self.page.wait_for_selector('text=CF:', timeout=TIMEOUTS['cf_search'])
            
            # Buscar todos los contenedores de resultados
            result_containers = await self.page.query_selector_all(SELECTORS['result_container'])
            
            self.logger.info(f"📋 Encontrados {len(result_containers)} resultados")
            
            if len(result_containers) == 0:
                self.logger.error("❌ No se encontraron resultados")
                return None
            
            if len(result_containers) == 1:
                # Solo un resultado, extraer ambos códigos directamente
                codes = await self._extract_codes_from_container(result_containers[0])
                ch_info = f" - CH: {codes['ch_code']}" if codes['ch_code'] else ""
                self.logger.info(f"✅ Un solo resultado encontrado - CF: {codes['cf_code']}{ch_info}")
                return codes
            
            # Múltiples resultados, procesar y encontrar la mejor coincidencia
            return await self._process_multiple_codes_results(result_containers, full_reference)
                
        except Exception as e:
            self.logger.error(f"❌ Error extrayendo códigos CF/CH: {e}")
            return None
    
    async def _extract_cf_from_container(self, container) -> str:
        """Extrae el código CF de un contenedor de resultado."""
        cf_element = await container.query_selector(SELECTORS['cf_code'])
        cf_text = await cf_element.inner_text()
        return cf_text.replace('CF: ', '').strip()
    
    async def _extract_ch_from_container(self, container) -> str:
        """Extrae el código CH de un contenedor de resultado."""
        try:
            # Buscar div con clase car-code que contenga CH:
            ch_element = await container.query_selector('div.car-code[data-original-title="Código Homólogo"]')
            if ch_element:
                ch_text = await ch_element.inner_text()
                return ch_text.replace('CH: ', '').strip()
            return None
        except Exception as e:
            self.logger.warning(f"⚠️ Error extrayendo código CH: {e}")
            return None
    
    async def _extract_codes_from_container(self, container) -> dict:
        """Extrae tanto CF como CH de un contenedor de resultado."""
        try:
            cf_code = await self._extract_cf_from_container(container)
            ch_code = await self._extract_ch_from_container(container)
            
            return {
                'cf_code': cf_code,
                'ch_code': ch_code
            }
        except Exception as e:
            self.logger.warning(f"⚠️ Error extrayendo códigos: {e}")
            return {'cf_code': None, 'ch_code': None}
    
    async def _extract_result_data(self, container, index: int, full_reference: str = None) -> dict:
        """Extrae toda la información de un contenedor de resultado."""
        try:
            # Extraer ambos códigos CF y CH
            codes = await self._extract_codes_from_container(container)
            cf_code = codes['cf_code']
            ch_code = codes['ch_code']
            
            # Extraer las referencias del resultado
            brand_element = await container.query_selector(SELECTORS['car_brand'])
            ref2_element = await container.query_selector(SELECTORS['car_reference_2'])
            ref3_element = await container.query_selector(SELECTORS['car_reference_3'])
            
            brand = await brand_element.inner_text() if brand_element else ""
            ref2 = await ref2_element.inner_text() if ref2_element else ""
            ref3 = await ref3_element.inner_text() if ref3_element else ""
            
            # Extraer el valor asegurado del h3 dentro de car-value
            insured_value = ""
            try:
                value_element = await container.query_selector('.car-value h3')
                if value_element:
                    insured_value = await value_element.inner_text()
                    insured_value = insured_value.strip()
            except Exception as e:
                self.logger.debug(f"⚠️ No se pudo extraer valor asegurado para resultado {index + 1}: {e}")
                insured_value = "No disponible"
            
            # Construir referencia completa: BRAND + REF2 + REF3
            result_full_ref = f"{brand} {ref2} {ref3}".strip()
            
            # Calcular score de similitud si tenemos referencia de configuración
            score = 0
            if full_reference:
                score = self._calculate_similarity_score(full_reference, result_full_ref)
            
            return {
                'index': index + 1,
                'cf_code': cf_code,
                'ch_code': ch_code,
                'full_reference': result_full_ref,
                'insured_value': insured_value,
                'score': score
            }
            
        except Exception as e:
            self.logger.warning(f"⚠️ Error procesando resultado {index + 1}: {e}")
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
            # Seleccionar categoría
            if not await self._select_field_with_retry(SELECTORS['category'], category, "categoría"):
                return False
            
            await asyncio.sleep(SLEEP_DURATION)
            
            # Seleccionar estado
            if not await self._select_field_with_retry(SELECTORS['state'], state, "estado"):
                return False
            
            await asyncio.sleep(SLEEP_DURATION)
            
            # Seleccionar modelo (año)
            if not await self._select_field_with_retry(SELECTORS['model'], model_year, "modelo"):
                return False
            
            await asyncio.sleep(SLEEP_DURATION)
            
            # Seleccionar marca
            if not await self._select_field_with_retry(SELECTORS['brand'], brand, "marca"):
                return False
            
            await asyncio.sleep(SLEEP_DURATION)
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error llenando formulario hasta marca: {e}")
            return False

    async def _get_all_references_for_brand(self, reference_filter: str = None) -> list:
        """Obtiene todas las referencias disponibles para la marca seleccionada."""
        try:
            await self._wait_for_field_enabled(SELECTORS['reference'])
            
            # Obtener todas las opciones del dropdown de referencias
            options = await self.page.query_selector_all(f"{SELECTORS['reference']} option")
            
            all_references = []
            for option in options:
                text = await option.inner_text()
                value = await option.get_attribute('value')
                
                # Filtrar opciones válidas (excluir "Elija una opción")
                if value and value != "false" and text.strip():
                    # Si hay filtro, solo incluir referencias que contengan el filtro
                    if not reference_filter or reference_filter.lower() in text.lower():
                        all_references.append({
                            'text': text.strip(),
                            'value': value
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
        """Busca exhaustivamente en todas las referencias y recopila todos los resultados (OPTIMIZADO Y CORREGIDO)."""
        all_options = []
        option_counter = 1
        
        self.logger.info(f"🔍 Iniciando búsqueda comprensiva en {len(references)} referencias")
        
        for ref_index, reference in enumerate(references):
            self.logger.info(f"🎯 Procesando referencia {ref_index + 1}/{len(references)}: {reference['text']}")
            
            try:
                # OPTIMIZACIÓN: Solo cambiar la referencia en lugar de recargar todo el formulario
                await self._select_by_value(SELECTORS['reference'], reference['value'])
                await asyncio.sleep(SLEEP_DURATION)
                
                # Hacer clic en buscar
                self.logger.info(f"🔍 Ejecutando búsqueda para: {reference['text']}")
                await self.page.click(SELECTORS['search_button'])
                
                # Esperar resultados con timeout más largo
                try:
                    await self.page.wait_for_selector(SELECTORS['result_container'], timeout=TIMEOUTS['cf_search'])
                    await asyncio.sleep(1)  # Esperar adicional para que carguen completamente
                except:
                    self.logger.warning(f"⚠️ No se encontraron resultados para: {reference['text']}")
                    # OPTIMIZACIÓN: Si no hay resultados, volver al formulario sin recargar página
                    await self._return_to_search_form()
                    await self._restore_form_state(category, state, model_year, brand)
                    continue
                
                # Extraer todos los resultados de esta referencia
                result_containers = await self.page.query_selector_all(SELECTORS['result_container'])
                
                if result_containers:
                    self.logger.info(f"✅ Encontrados {len(result_containers)} resultado(s) en: {reference['text']}")
                    
                    # Verificar que los resultados son únicos y válidos
                    reference_results = []
                    for container_index, container in enumerate(result_containers):
                        result_data = await self._extract_complete_result_data(container, option_counter, reference['text'])
                        if result_data and self._is_valid_unique_result(result_data, all_options):
                            reference_results.append(result_data)
                            all_options.append(result_data)
                            option_counter += 1
                            self.logger.info(f"📊 Resultado {container_index + 1}: CF={result_data['cf_code']}, CH={result_data['ch_code']}")
                    
                    self.logger.info(f"🎯 Agregados {len(reference_results)} resultados únicos de la referencia: {reference['text']}")
                else:
                    self.logger.warning(f"⚠️ No se encontraron contenedores de resultados para: {reference['text']}")
                
                # OPTIMIZACIÓN: Volver al formulario sin recargar página (solo si no es la última búsqueda)
                if ref_index < len(references) - 1:  # No volver en la última iteración
                    await self._return_to_search_form()
                    await self._restore_form_state(category, state, model_year, brand)
                
            except Exception as e:
                self.logger.error(f"❌ Error buscando en referencia {reference['text']}: {e}")
                # En caso de error, intentar volver al formulario
                try:
                    await self._return_to_search_form()
                    await self._restore_form_state(category, state, model_year, brand)
                except:
                    # Si falla, recargar página como último recurso
                    self.logger.warning("🔄 Recargando página debido a error crítico")
                    await self.page.goto(FASECOLDA_URL)
                    await self._fill_vehicle_form_to_brand(category, state, model_year, brand)
                continue
        
        self.logger.info(f"🎉 Búsqueda comprensiva completada: {len(all_options)} opciones únicas encontradas")
        return all_options

    async def _extract_complete_result_data(self, container, option_number: int, reference_group: str) -> dict:
        """Extrae datos completos de un resultado incluyendo agrupación por referencia."""
        try:
            # Extraer códigos CF y CH
            codes = await self._extract_codes_from_container(container)
            cf_code = codes['cf_code']
            ch_code = codes['ch_code']
            
            # Extraer descripción completa
            brand_element = await container.query_selector(SELECTORS['car_brand'])
            ref2_element = await container.query_selector(SELECTORS['car_reference_2'])
            ref3_element = await container.query_selector(SELECTORS['car_reference_3'])
            
            brand = await brand_element.inner_text() if brand_element else ""
            ref2 = await ref2_element.inner_text() if ref2_element else ""
            ref3 = await ref3_element.inner_text() if ref3_element else ""
            
            full_description = f"{brand} {ref2} {ref3}".strip()
            
            # Extraer valor asegurado
            insured_value = "No disponible"
            try:
                value_element = await container.query_selector('.car-value h3')
                if value_element:
                    insured_value = await value_element.inner_text()
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
            self.logger.error(f"❌ Error extrayendo datos del resultado: {e}")
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
