"""Módulo para automatización de consultas en Fasecolda."""

import asyncio
import logging
from typing import Optional
from playwright.async_api import Page

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
    ) -> Optional[str]:
        """
        Obtiene el código CF de Fasecolda para un vehículo específico.
        
        Args:
            category: Categoría del vehículo ("Liviano pasajeros", "Motos")
            state: Estado del vehículo ("Nuevo", "Usado")
            model_year: Año del modelo (ej: "2026", "2025")
            brand: Marca del vehículo (ej: "Chevrolet")
            reference: Referencia específica (ej: "Tracker [2] - utilitario deportivo 4x2")
            full_reference: Referencia completa para matching exacto (ej: "CHEVROLET TRACKER [2] LS TP 1200CC T")
            
        Returns:
            Código CF si se encuentra, None en caso contrario
        """
        try:
            await self._navigate_to_fasecolda()
            
            if not await self._fill_vehicle_form(category, state, model_year, brand, reference):
                return None
                
            if not await self._search_vehicle():
                return None
                
            return await self._extract_cf_code(full_reference)
            
        except Exception as e:
            self.logger.error(f"❌ Error obteniendo código CF: {e}")
            return None
    
    async def _navigate_to_fasecolda(self):
        """Navega a la página de Fasecolda."""
        self.logger.info("🌐 Navegando a Fasecolda...")
        await self.page.goto('https://www.fasecolda.com/guia-de-valores-old/')
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
            # Categoría - usar el select original directamente
            self.logger.info(f"📋 Seleccionando categoría: {category}")
            category_value = await self._get_category_value(category)
            await self._select_by_value('#fe-categoria', category_value)
            await asyncio.sleep(1)
            
            # Estado - esperar a que se habilite y seleccionar
            self.logger.info(f"🏷️ Seleccionando estado: {state}")
            await self._wait_for_field_enabled('#fe-estado')
            state_value = await self._get_state_value(state)
            await self._select_by_value('#fe-estado', state_value)
            await asyncio.sleep(1)
            
            # Modelo (año)
            self.logger.info(f"📅 Seleccionando modelo: {model_year}")
            await self._wait_for_field_enabled('#fe-modelo')
            model_value = await self._get_model_value(model_year)
            await self._select_by_value('#fe-modelo', model_value)
            await asyncio.sleep(1)
            
            # Marca
            self.logger.info(f"🚗 Seleccionando marca: {brand}")
            await self._wait_for_field_enabled('#fe-marca')
            brand_value = await self._get_brand_value(brand)
            await self._select_by_value('#fe-marca', brand_value)
            await asyncio.sleep(1)
            
            # Referencia - buscar y seleccionar por texto que coincida
            self.logger.info(f"🔍 Seleccionando referencia: {reference}")
            await self._wait_for_field_enabled('#fe-refe1')
            reference_value = await self._get_reference_value(reference)
            if reference_value:
                await self._select_by_value('#fe-refe1', reference_value)
                await asyncio.sleep(1)
            else:
                self.logger.error(f"❌ No se encontró la referencia: {reference}")
                return False
            
            self.logger.info("✅ Formulario llenado correctamente")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error llenando formulario: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def _get_category_value(self, category: str) -> str:
        """Obtiene el valor del select para la categoría especificada."""
        category_map = {
            "Liviano carga": "2",
            "Liviano pasajeros": "1", 
            "Motos": "3",
            "Pesado carga": "4",
            "Pesado pasajeros": "5",
            "Pesado semirremolque": "6"
        }
        return category_map.get(category, "false")
    
    async def _get_state_value(self, state: str) -> str:
        """Obtiene el valor del select para el estado especificado."""
        state_map = {
            "Nuevo": "1",
            "Usado": "0"
        }
        return state_map.get(state, "false")
    
    async def _get_model_value(self, model_year: str) -> str:
        """Obtiene el valor del select para el año del modelo."""
        # Buscar en las opciones disponibles del select
        options = await self.page.query_selector_all('#fe-modelo option')
        for option in options:
            text = await option.inner_text()
            if text.strip() == model_year:
                value = await option.get_attribute('value')
                return value
        return "false"
    
    async def _get_brand_value(self, brand: str) -> str:
        """Obtiene el valor del select para la marca especificada."""
        # Buscar en las opciones disponibles del select
        options = await self.page.query_selector_all('#fe-marca option')
        for option in options:
            text = await option.inner_text()
            if text.strip().lower() == brand.lower():
                value = await option.get_attribute('value')
                return value
        return "false"
    
    async def _get_reference_value(self, reference: str) -> str:
        """Obtiene el valor del select para la referencia especificada."""
        # Buscar en las opciones disponibles del select
        options = await self.page.query_selector_all('#fe-refe1 option')
        for option in options:
            text = await option.inner_text()
            if text.strip() == reference:
                value = await option.get_attribute('value')
                return value
        return None
    
    async def _wait_for_field_enabled(self, selector: str, timeout: int = 5000):
        """Espera a que un campo se habilite."""
        await self.page.wait_for_function(
            f"document.querySelector('{selector}').disabled === false",
            timeout=timeout
        )
    
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
            await self.page.click('button.btn.btn-red.fe-submit')
            await self.page.wait_for_load_state('networkidle')
            self.logger.info("✅ Búsqueda completada")
            return True
        except Exception as e:
            self.logger.error(f"❌ Error en búsqueda: {e}")
            return False
    
    async def _extract_cf_code(self, full_reference: str = None) -> Optional[str]:
        """Extrae el código CF basado en la referencia completa usando scoring de similitud."""
        self.logger.info("📊 Extrayendo código CF...")
        
        try:
            # Esperar a que aparezcan los resultados
            await self.page.wait_for_selector('text=CF:', timeout=10000)
            
            # Buscar todos los contenedores de resultados
            result_containers = await self.page.query_selector_all('.car-result-container')
            
            self.logger.info(f"📋 Encontrados {len(result_containers)} resultados")
            
            if len(result_containers) == 1:
                # Solo un resultado, extraer el CF directamente
                cf_element = await result_containers[0].query_selector('.car-code')
                cf_text = await cf_element.inner_text()
                cf_code = cf_text.replace('CF: ', '').strip()
                self.logger.info(f"✅ Un solo resultado encontrado - CF: {cf_code}")
                return cf_code
            
            elif len(result_containers) > 1:
                # Múltiples resultados, usar scoring para encontrar la mejor coincidencia
                self.logger.info(f"🔍 Múltiples resultados, analizando similitudes...")
                
                best_match = None
                best_score = -1
                all_results = []
                
                for i, container in enumerate(result_containers):
                    try:
                        # Extraer el código CF
                        cf_element = await container.query_selector('.car-code')
                        cf_text = await cf_element.inner_text()
                        cf_code = cf_text.replace('CF: ', '').strip()
                        
                        # Extraer las referencias del resultado
                        brand_element = await container.query_selector('.car-brand')
                        ref2_element = await container.query_selector('.car-reference-2')
                        ref3_element = await container.query_selector('.car-reference-3')
                        
                        brand = await brand_element.inner_text() if brand_element else ""
                        ref2 = await ref2_element.inner_text() if ref2_element else ""
                        ref3 = await ref3_element.inner_text() if ref3_element else ""
                        
                        # Construir referencia completa: BRAND + REF2 + REF3
                        result_full_ref = f"{brand} {ref2} {ref3}".strip()
                        
                        # Calcular score de similitud si tenemos referencia de configuración
                        score = 0
                        if full_reference:
                            score = self._calculate_similarity_score(full_reference, result_full_ref)
                        
                        result_data = {
                            'index': i + 1,
                            'cf_code': cf_code,
                            'full_reference': result_full_ref,
                            'score': score
                        }
                        all_results.append(result_data)
                        
                        self.logger.info(f"📝 Resultado {i+1}: CF: {cf_code} - {result_full_ref} (Score: {score:.2f})")
                        
                        # Verificar si es la mejor coincidencia hasta ahora
                        if score > best_score:
                            best_score = score
                            best_match = result_data
                            
                    except Exception as e:
                        self.logger.warning(f"⚠️ Error procesando resultado {i+1}: {e}")
                
                # Determinar el resultado a retornar
                if full_reference and best_match and best_score > 0.3:  # Threshold mínimo del 30%
                    self.logger.info(f"✅ Mejor coincidencia encontrada - CF: {best_match['cf_code']} (Score: {best_score:.2f})")
                    return best_match['cf_code']
                elif best_match:
                    self.logger.warning(f"⚠️ Score bajo ({best_score:.2f}), retornando mejor opción - CF: {best_match['cf_code']}")
                    return best_match['cf_code']
                else:
                    # Fallback al primer resultado si no hay matches
                    self.logger.warning("⚠️ No se encontraron coincidencias, retornando primer resultado")
                    cf_element = await result_containers[0].query_selector('.car-code')
                    cf_text = await cf_element.inner_text()
                    cf_code = cf_text.replace('CF: ', '').strip()
                    self.logger.warning(f"⚠️ Retornando primer CF como fallback: {cf_code}")
                    return cf_code
            
            else:
                self.logger.error("❌ No se encontraron resultados")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Error extrayendo código CF: {e}")
            return None
    
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
        bonus = 0.0
        
        # Bonus si coincide la marca exacta
        if any(brand in ref_normalized for brand in ['CHEVROLET', 'TOYOTA', 'FORD', 'HONDA']):
            if any(brand in cand_normalized for brand in ['CHEVROLET', 'TOYOTA', 'FORD', 'HONDA']):
                for brand in ['CHEVROLET', 'TOYOTA', 'FORD', 'HONDA']:
                    if brand in ref_normalized and brand in cand_normalized:
                        bonus += 0.2
                        break
        
        # Bonus si coincide el modelo exacto (ej: TRACKER [2])
        import re
        ref_model_match = re.search(r'(\w+)\s*\[[^\]]+\]', ref_normalized)
        cand_model_match = re.search(r'(\w+)\s*\[[^\]]+\]', cand_normalized)
        
        if ref_model_match and cand_model_match:
            if ref_model_match.group() == cand_model_match.group():
                bonus += 0.3
        
        # Bonus por coincidencias de motores/transmisiones (ej: TP 1200CC T)
        engine_patterns = ['1200CC', '1500CC', '2000CC', 'TP', 'MT', 'AT']
        for pattern in engine_patterns:
            if pattern in ref_normalized and pattern in cand_normalized:
                bonus += 0.1
        
        # Score final (limitado a 1.0)
        final_score = min(1.0, token_score + bonus)
        
        return final_score
