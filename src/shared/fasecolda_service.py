"""Módulo para automatización de consultas en Fasecolda."""

import asyncio
import logging
from typing import Optional
from playwright.async_api import Page

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
    'page_load': 10000,
    'field_enable': 3000,  # Reducido de 5000 a 3000ms
    'cf_search': 15000     # Aumentado para dar más tiempo a la búsqueda
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
        """Navega a la página de Fasecolda."""
        self.logger.info("🌐 Navegando a Fasecolda...")
        await self.page.goto(FASECOLDA_URL)
        await self.page.wait_for_load_state('networkidle')
        self.logger.info("✅ Página de Fasecolda cargada")
        
    async def _fill_vehicle_form(
        self,
        category: str,
        state: str,
        model_year: str,
        brand: str,
        reference: str
    ) -> bool:
        """Llena el formulario con los datos del vehículo usando el método optimizado."""
        self.logger.info("📝 Llenando formulario de vehículo...")
        
        try:
            # Configuración de campos: (nombre, emoji, selector, valor, wait_enabled)
            fields = [
                ("categoría", "📋", SELECTORS['category'], category, False),
                ("estado", "🏷️", SELECTORS['state'], state, True),
                ("modelo", "📅", SELECTORS['model'], model_year, True),
                ("marca", "🚗", SELECTORS['brand'], brand, True),
                ("referencia", "🔍", SELECTORS['reference'], reference, True),
            ]
            
            for field_name, emoji, selector, value, wait_enabled in fields:
                self.logger.info(f"{emoji} Seleccionando {field_name}: {value}")
                
                # Esperar a que el campo se habilite si es necesario
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
        """Espera a que un campo se habilite con manejo de errores mejorado."""
        timeout = timeout or TIMEOUTS['field_enable']
        
        try:
            # Primero verificar si el elemento existe
            await self.page.wait_for_selector(selector, timeout=2000)
            
            # Luego esperar a que se habilite
            await self.page.wait_for_function(
                f"() => {{ const el = document.querySelector('{selector}'); return el && !el.disabled; }}",
                timeout=timeout
            )
            self.logger.debug(f"✅ Campo {selector} habilitado")
            
        except Exception as e:
            self.logger.warning(f"⚠️ Campo {selector} no se habilitó en {timeout}ms: {e}")
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
        """Procesa múltiples resultados y encuentra la mejor coincidencia retornando códigos CF y CH."""
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
