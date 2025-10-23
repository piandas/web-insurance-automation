"""
Módulo interactivo de Fasecolda que permite al usuario seleccionar la opción correcta
cuando hay múltiples resultados disponibles.
"""

import asyncio
from typing import Optional, Dict, List, Tuple
from playwright.async_api import Page, Browser, async_playwright

from ..config.client_config import ClientConfig
from ..core.logger_factory import LoggerFactory


class InteractiveFasecoldaSelector:
    """Servicio interactivo para búsqueda de códigos Fasecolda."""

import os
import asyncio
import re
from typing import Optional, Dict, List, Tuple
from playwright.async_api import Page, Browser, async_playwright

from .fasecolda_service import FasecoldaService
from ..config.client_config import ClientConfig
from ..config.base_config import BaseConfig
from ..core.logger_factory import LoggerFactory


class InteractiveFasecoldaSelector:
    """Servicio interactivo para búsqueda de códigos Fasecolda."""
    
    def __init__(self, headless: bool = False):
        self.logger = LoggerFactory.create_logger('interactive_fasecolda')
        self.playwright = None
        self.browser = None
        self.page = None
        self.headless = headless
        
        # URLs y selectores para la NUEVA página de Fasecolda
        # Usar directamente la URL del contenido (CloudFront) para evitar iframe
        self.fasecolda_url = 'https://d2eqscyubtix40.cloudfront.net/'
        self.selectors = {
            'basic_search_link': 'text=Búsqueda básica',
            'category_select': 'select[aria-label="Select category"]',
            'state_button_new': 'button:has-text("Nuevo")',
            'state_button_used': 'button:has-text("Usado")',
            'model_select': 'select[aria-label="Select model"]',
            'brand_select': 'select[aria-label="Select marca"]',
            'reference_select': 'select[aria-label="Select referencia"]',
            'search_button': 'button.bg-btn-primary:has-text("Buscar")',
            'vehicle_card': 'div.px-4.py-4',
            'vehicle_name': 'div.font-bold.items-center.text-base',
            'vehicle_codes': 'p.text-gray-700.text-sm.mt-1.border-b',
            'vehicle_price': 'p.text-gray-700.text-base.font-bold.mt-1'
        }
    
    async def __aenter__(self):
        """Context manager entry."""
        await self._initialize_browser()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        await self._cleanup()
    
    async def _initialize_browser(self):
        """Inicializa el navegador y la página."""
        try:
            self.playwright = await async_playwright().start()
            
            # Determinar configuración de headless
            gui_show_browser = os.getenv('GUI_SHOW_BROWSER', 'False').lower() == 'true'
            should_hide = not gui_show_browser  # Si GUI dice mostrar = False, ocultar = True
            
            # Configurar argumentos del navegador
            browser_args = ['--no-sandbox', '--disable-dev-shm-usage']
            
            # Si debe estar oculto, usar ventana minimizada en lugar de headless
            if should_hide:
                browser_args.extend([
                    '--start-minimized',
                    '--window-position=-32000,-32000',  # Mover fuera de la pantalla
                    '--window-size=1,1',  # Tamaño mínimo
                    '--disable-background-timer-throttling',  # Evita que se ralenticen los timers
                    '--disable-renderer-backgrounding',  # Evita que el renderer se pause
                    '--disable-backgrounding-occluded-windows'  # No pausar ventanas ocultas
                ])
                headless_mode = False  # No usar headless real para evitar problemas
            else:
                headless_mode = False
            
            self.browser = await self.playwright.chromium.launch(
                headless=headless_mode,
                args=browser_args
            )
            self.page = await self.browser.new_page()
            
            # Configurar timeouts más largos
            self.page.set_default_timeout(30000)
            
            self.logger.info("🌐 Navegador inicializado exitosamente")
            
        except Exception as e:
            self.logger.error(f"❌ Error inicializando navegador: {e}")
            await self._cleanup()
            raise
    
    async def _cleanup(self):
        """Limpia recursos del navegador."""
        try:
            if self.page:
                await self.page.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            self.logger.info("🧹 Recursos del navegador liberados")
        except Exception as e:
            self.logger.error(f"❌ Error en cleanup: {e}")
    
    async def search_and_select_vehicle(self) -> Optional[Dict[str, str]]:
        """
        Realiza la búsqueda en Fasecolda y permite al usuario seleccionar la opción correcta.
        
        Returns:
            Dict con códigos CF y CH seleccionados, o None si falla
        """
        try:
            self.logger.info("🔍 Iniciando búsqueda interactiva en Fasecolda...")
            
            # Navegar a Fasecolda
            await self._navigate_to_fasecolda()
            
            # Configurar formulario de búsqueda
            await self._configure_search_form()
            
            # Realizar búsqueda
            await self._perform_search()
            
            # Obtener resultados y permitir selección
            selected_codes = await self._get_results_and_select()
            
            if selected_codes:
                self.logger.info(f"✅ Códigos seleccionados - CF: {selected_codes['cf_code']}, CH: {selected_codes['ch_code']}")
                return selected_codes
            else:
                self.logger.warning("⚠️ No se seleccionó ninguna opción")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Error en búsqueda interactiva: {e}")
            return None
    
    async def _navigate_to_fasecolda(self):
        """Navega a la página de Fasecolda y accede a búsqueda básica."""
        self.logger.info("🌐 Navegando a Fasecolda...")
        await self.page.goto(self.fasecolda_url)
        await self.page.wait_for_load_state('networkidle')
        await asyncio.sleep(1)
        self.logger.info("✅ Página de Fasecolda cargada")
        
        # Hacer clic en "Búsqueda básica"
        self.logger.info("🔍 Accediendo a búsqueda básica...")
        
        # Hacer clic usando el selector text=
        await self.page.click(self.selectors['basic_search_link'], timeout=10000)
        
        self.logger.info("✅ Clic en búsqueda básica realizado")
        
        # Esperar navegación
        await self.page.wait_for_load_state('networkidle')
        await asyncio.sleep(1)
        
        # Verificar que el formulario cargó
        await self.page.wait_for_selector(self.selectors['category'], timeout=10000)
        self.logger.info("✅ Formulario de búsqueda básica cargado")
    
    async def _configure_search_form(self):
        """Configura el formulario de búsqueda con los datos del cliente."""
        self.logger.info("📝 Configurando formulario de búsqueda...")
        
        try:
            # 1. Seleccionar categoría - Automóvil (value="1")
            self.logger.info("🚗 Seleccionando categoría: Automóvil...")
            await self.page.select_option(self.selectors['category_select'], value='1')
            await asyncio.sleep(0.5)
            self.logger.info("✅ Categoría seleccionada")
            
            # 2. Seleccionar estado - Nuevo o Usado
            vehicle_state = ClientConfig.VEHICLE_STATE
            self.logger.info(f"📋 Seleccionando estado: {vehicle_state}...")
            if vehicle_state.lower() == 'nuevo':
                await self.page.click(self.selectors['state_button_new'])
            else:
                await self.page.click(self.selectors['state_button_used'])
            await asyncio.sleep(0.5)
            self.logger.info(f"✅ Estado '{vehicle_state}' seleccionado")
            
            # 3. Seleccionar año del modelo
            model_year = ClientConfig.VEHICLE_MODEL_YEAR
            self.logger.info(f"📅 Seleccionando modelo: {model_year}...")
            await self.page.select_option(self.selectors['model_select'], label=model_year)
            await asyncio.sleep(0.5)
            self.logger.info(f"✅ Modelo '{model_year}' seleccionado")
            
            # 4. Seleccionar marca
            brand = ClientConfig.VEHICLE_BRAND
            self.logger.info(f"🏭 Seleccionando marca: {brand}...")
            # Normalizar nombre de marca para que coincida con las opciones del select
            brand_normalized = brand.title()  # Capitalizar primera letra de cada palabra
            await self.page.select_option(self.selectors['brand_select'], label=brand_normalized)
            await asyncio.sleep(1)  # Esperar a que se carguen las referencias
            self.logger.info(f"✅ Marca '{brand}' seleccionada")
            
            self.logger.info("✅ Formulario configurado correctamente")
            
        except Exception as e:
            self.logger.error(f"❌ Error configurando formulario: {e}")
            raise
    
    async def _perform_search(self):
        """
        Realiza búsquedas iterativas para cada opción de referencia disponible.
        Extrae todos los resultados de todas las referencias relacionadas.
        """
        all_results = []
        
        try:
            # Obtener todas las opciones de referencia disponibles
            reference_options = await self._get_reference_options()
            
            if not reference_options:
                self.logger.warning("⚠️ No se encontraron opciones de referencia")
                return all_results
            
            self.logger.info(f"� Se encontraron {len(reference_options)} opciones de referencia")
            
            # Iterar sobre cada opción de referencia
            for idx, ref_option in enumerate(reference_options, 1):
                ref_value = ref_option['value']
                ref_text = ref_option['text']
                
                self.logger.info(f"🔍 [{idx}/{len(reference_options)}] Buscando: {ref_text}")
                
                try:
                    # Seleccionar esta referencia
                    await self.page.select_option(self.selectors['reference_select'], value=ref_value)
                    await asyncio.sleep(0.5)
                    
                    # Hacer clic en buscar
                    await self.page.click(self.selectors['search_button'])
                    await asyncio.sleep(2)  # Esperar a que carguen los resultados
                    
                    # Extraer resultados de esta búsqueda
                    results = await self._extract_search_results()
                    
                    if results:
                        self.logger.info(f"✅ Encontrados {len(results)} resultados para '{ref_text}'")
                        all_results.extend(results)
                    else:
                        self.logger.info(f"ℹ️ No se encontraron resultados para '{ref_text}'")
                    
                    # Volver al formulario si no es la última búsqueda
                    if idx < len(reference_options):
                        # Esperar un poco antes de la siguiente búsqueda
                        await asyncio.sleep(1)
                    
                except Exception as e:
                    self.logger.error(f"❌ Error buscando referencia '{ref_text}': {e}")
                    continue
            
            self.logger.info(f"✅ Búsqueda completada. Total de resultados: {len(all_results)}")
            
            # Guardar los resultados para uso posterior
            self._all_results = all_results
            
        except Exception as e:
            self.logger.error(f"❌ Error en proceso de búsqueda: {e}")
            raise
    
    async def _get_reference_options(self) -> List[Dict[str, str]]:
        """
        Obtiene todas las opciones disponibles del select de referencias.
        
        Returns:
            Lista de diccionarios con 'value' y 'text' de cada opción
        """
        try:
            # Esperar a que el select de referencias esté disponible
            await self.page.wait_for_selector(self.selectors['reference_select'], timeout=5000)
            
            # Extraer las opciones usando JavaScript
            options = await self.page.evaluate("""
                (selector) => {
                    const select = document.querySelector(selector);
                    if (!select) return [];
                    
                    const options = Array.from(select.options);
                    return options
                        .filter(opt => opt.value && opt.value !== '')  // Filtrar la opción "Elija una opción"
                        .map(opt => ({
                            value: opt.value,
                            text: opt.text
                        }));
                }
            """, self.selectors['reference_select'])
            
            return options
            
        except Exception as e:
            self.logger.error(f"❌ Error obteniendo opciones de referencia: {e}")
            return []
    
    async def _get_results_and_select(self) -> Optional[Dict[str, str]]:
        """
        Obtiene los resultados de la búsqueda y permite al usuario seleccionar.
        
        Returns:
            Dict con códigos CF y CH seleccionados
        """
        try:
            # Usar los resultados ya extraídos en _perform_search
            results = getattr(self, '_all_results', [])
            
            if not results:
                self.logger.warning("⚠️ No se encontraron resultados")
                return None
            
            # Eliminar duplicados basados en código CF
            unique_results = self._remove_duplicate_results(results)
            
            if len(unique_results) == 1:
                # Si solo hay un resultado, seleccionarlo automáticamente
                self.logger.info("✅ Solo un resultado encontrado, seleccionando automáticamente")
                return {
                    'cf_code': unique_results[0]['cf_code'],
                    'ch_code': unique_results[0]['ch_code']
                }
            
            # Mostrar opciones al usuario y permitir selección
            return await self._show_options_and_get_selection(unique_results)
            
        except Exception as e:
            self.logger.error(f"❌ Error obteniendo resultados: {e}")
            return None
    
    def _remove_duplicate_results(self, results: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Elimina resultados duplicados basándose en el código CF.
        
        Args:
            results: Lista de resultados
            
        Returns:
            Lista de resultados sin duplicados
        """
        seen_cf = set()
        unique_results = []
        
        for result in results:
            cf_code = result.get('cf_code')
            if cf_code and cf_code not in seen_cf:
                seen_cf.add(cf_code)
                unique_results.append(result)
        
        return unique_results
    
    async def _extract_search_results(self) -> List[Dict[str, str]]:
        """
        Extrae los resultados de la búsqueda de la página usando la nueva estructura HTML.
        
        Returns:
            Lista de diccionarios con información de cada vehículo
        """
        results = []
        
        try:
            # Esperar a que aparezcan las tarjetas de vehículos
            await asyncio.sleep(1)
            
            # Buscar todas las tarjetas de vehículos
            vehicle_cards = await self.page.query_selector_all(self.selectors['vehicle_card'])
            
            if not vehicle_cards:
                self.logger.debug("No se encontraron tarjetas de vehículos")
                return []
            
            self.logger.debug(f"Encontradas {len(vehicle_cards)} tarjetas de vehículos")
            
            # Extraer información de cada tarjeta
            for idx, card in enumerate(vehicle_cards, 1):
                try:
                    result_info = await self._extract_vehicle_info_from_card(card, idx)
                    if result_info:
                        results.append(result_info)
                except Exception as e:
                    self.logger.debug(f"Error extrayendo info de tarjeta {idx}: {e}")
                    continue
            
            return results
            
        except Exception as e:
            self.logger.error(f"❌ Error extrayendo resultados: {e}")
            return []
    
    async def _extract_vehicle_info_from_card(self, card_element, index: int) -> Optional[Dict[str, str]]:
        """
        Extrae información de una tarjeta de vehículo de la nueva página.
        
        Args:
            card_element: Elemento DOM de la tarjeta del vehículo
            index: Índice del vehículo
            
        Returns:
            Dict con información del vehículo
        """
        try:
            import re
            
            # Extraer el nombre del vehículo
            name_element = await card_element.query_selector(self.selectors['vehicle_name'])
            vehicle_name = await name_element.text_content() if name_element else f"Vehículo {index}"
            vehicle_name = vehicle_name.strip()
            
            # Extraer códigos CF y CH
            codes_element = await card_element.query_selector(self.selectors['vehicle_codes'])
            if not codes_element:
                return None
            
            codes_text = await codes_element.text_content()
            codes_text = codes_text.strip()
            
            # Extraer CF y CH con regex
            # Formato esperado: "CF - 03033048 CH - 03001135"
            cf_match = re.search(r'CF\s*-\s*(\d+)', codes_text)
            ch_match = re.search(r'CH\s*-\s*(\d+)', codes_text)
            
            if not cf_match:
                self.logger.debug(f"No se encontró código CF en: {codes_text}")
                return None
            
            cf_code = cf_match.group(1)
            ch_code = ch_match.group(1) if ch_match else cf_code
            
            # Extraer precio
            price_element = await card_element.query_selector(self.selectors['vehicle_price'])
            price = await price_element.text_content() if price_element else "Precio no disponible"
            price = price.strip()
            
            return {
                'cf_code': cf_code,
                'ch_code': ch_code,
                'name': vehicle_name,
                'price': price,
                'index': index
            }
            
        except Exception as e:
            self.logger.debug(f"Error extrayendo info de tarjeta {index}: {e}")
            return None
    

    
    async def _show_options_and_get_selection(self, results: List[Dict[str, str]]) -> Optional[Dict[str, str]]:
        """
        Muestra las opciones al usuario y obtiene su selección.
        
        Args:
            results: Lista de resultados disponibles
            
        Returns:
            Dict con códigos CF y CH seleccionados
        """
        try:
            print("\n" + "="*80)
            print("🚗 SELECCIÓN DE VEHÍCULO FASECOLDA")
            print("="*80)
            print(f"Se encontraron {len(results)} opciones. Por favor, seleccione una:")
            print()
            
            # Mostrar opciones
            for i, result in enumerate(results, 1):
                name = result.get('name', f"Opción {i}")
                price = result.get('price', 'Precio no disponible')
                cf_code = result.get('cf_code', 'N/A')
                ch_code = result.get('ch_code', 'N/A')
                
                print(f"[{i:2d}] {name}")
                print(f"      💰 Valor: {price}")
                print(f"      🔢 CF: {cf_code} | CH: {ch_code}")
                print()
            
            print("="*80)
            
            # Obtener selección del usuario
            while True:
                try:
                    print(f"\n👆 Seleccione una opción (1-{len(results)}) o 'q' para cancelar: ", end="", flush=True)
                    selection = input().strip().lower()
                    
                    if selection == 'q':
                        print("❌ Selección cancelada por el usuario")
                        return None
                    
                    index = int(selection) - 1
                    if 0 <= index < len(results):
                        selected = results[index]
                        print(f"\n✅ Seleccionado: {selected.get('name', 'Opción')}")
                        print(f"   � Valor: {selected.get('price', 'N/A')}")
                        print(f"   🔢 CF: {selected['cf_code']} | CH: {selected['ch_code']}")
                        print()
                        return {
                            'cf_code': selected['cf_code'],
                            'ch_code': selected['ch_code']
                        }
                    else:
                        print(f"❌ Opción inválida. Seleccione entre 1 y {len(results)}")
                        
                except ValueError:
                    print("❌ Por favor ingrese un número válido")
                except KeyboardInterrupt:
                    print("\n❌ Selección cancelada por el usuario")
                    return None
                    
        except Exception as e:
            self.logger.error(f"❌ Error mostrando opciones: {e}")
            return None


async def get_interactive_fasecolda_codes(headless: bool = False) -> Optional[Dict[str, str]]:
    """
    Función helper para obtener códigos Fasecolda de forma interactiva.
    
    Args:
        headless: Si ejecutar el navegador en modo headless
        
    Returns:
        Dict con códigos CF y CH seleccionados, o None si falla
    """
    try:
        async with InteractiveFasecoldaSelector(headless=headless) as selector:
            return await selector.search_and_select_vehicle()
    except Exception as e:
        logger = LoggerFactory.create_logger('interactive_fasecolda')
        logger.error(f"❌ Error en búsqueda interactiva de Fasecolda: {e}")
        return None
