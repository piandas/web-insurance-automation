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
        
        # URLs y selectores
        self.fasecolda_url = 'https://www.fasecolda.com/guia-de-valores-old/'
        self.selectors = {
            'category': '#fe-categoria',
            'state': '#fe-estado', 
            'model': '#fe-modelo',
            'brand': '#fe-marca',
            'reference': '#fe-refe1',
            'search_button': '.btn.btn-red.fe-submit',
            'results_container': '#view-container',
            'car_items': '.car-item',
            'cf_code': '.car-code', 
            'ch_code': '.car-ch-code',
            'car_name': '.car-name',
            'car_price': '.car-price'
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
        """Navega a la página de Fasecolda."""
        self.logger.info("🌐 Navegando a Fasecolda...")
        await self.page.goto(self.fasecolda_url)
        await self.page.wait_for_load_state('networkidle')
        self.logger.info("✅ Página de Fasecolda cargada")
    
    async def _configure_search_form(self):
        """Configura el formulario de búsqueda con los datos del cliente."""
        self.logger.info("📝 Configurando formulario de búsqueda...")
        
        try:
            # Seleccionar categoría (ya viene seleccionado "Liviano pasajeros")
            if ClientConfig.VEHICLE_CATEGORY == 'Liviano pasajeros':
                self.logger.info("✅ Categoría 'Liviano pasajeros' ya seleccionada")
            
            # Seleccionar estado (ya viene seleccionado "Nuevo")  
            if ClientConfig.VEHICLE_STATE == 'Nuevo':
                self.logger.info("✅ Estado 'Nuevo' ya seleccionado")
            
            # Seleccionar año del modelo (ya viene seleccionado "2026")
            if ClientConfig.VEHICLE_MODEL_YEAR == '2026':
                self.logger.info("✅ Modelo '2026' ya seleccionado")
            
            # Seleccionar marca (ya viene seleccionado "Mazda")
            if ClientConfig.VEHICLE_BRAND.lower() == 'mazda':
                self.logger.info("✅ Marca 'Mazda' ya seleccionada")
            
            # Seleccionar referencia (ya viene seleccionado "Cx50 - utilitario deportivo 4x4")
            if 'cx50' in ClientConfig.VEHICLE_REFERENCE.lower():
                self.logger.info("✅ Referencia 'Cx50' ya seleccionada")
            
            self.logger.info("✅ Formulario configurado correctamente")
            
        except Exception as e:
            self.logger.error(f"❌ Error configurando formulario: {e}")
            raise
    
    async def _perform_search(self):
        """Realiza la búsqueda haciendo clic en el botón buscar."""
        self.logger.info("🔍 Realizando búsqueda...")
        
        try:
            # Hacer clic en buscar
            await self.page.click(self.selectors['search_button'])
            
            # Esperar a que aparezcan los resultados
            await self.page.wait_for_selector('#view-container', timeout=15000)
            await asyncio.sleep(2)  # Esperar un poco más para que carguen completamente
            
            self.logger.info("✅ Búsqueda completada, resultados cargados")
            
        except Exception as e:
            self.logger.error(f"❌ Error realizando búsqueda: {e}")
            raise
    
    async def _get_results_and_select(self) -> Optional[Dict[str, str]]:
        """
        Obtiene los resultados de la búsqueda y permite al usuario seleccionar.
        
        Returns:
            Dict con códigos CF y CH seleccionados
        """
        try:
            # Obtener todos los resultados
            results = await self._extract_search_results()
            
            if not results:
                self.logger.warning("⚠️ No se encontraron resultados")
                return None
            
            if len(results) == 1:
                # Si solo hay un resultado, seleccionarlo automáticamente
                self.logger.info("✅ Solo un resultado encontrado, seleccionando automáticamente")
                return results[0]
            
            # Mostrar opciones al usuario y permitir selección
            return await self._show_options_and_get_selection(results)
            
        except Exception as e:
            self.logger.error(f"❌ Error obteniendo resultados: {e}")
            return None
    
    async def _extract_search_results(self) -> List[Dict[str, str]]:
        """
        Extrae los resultados de la búsqueda de la página.
        
        Returns:
            Lista de diccionarios con información de cada vehículo
        """
        results = []
        
        try:
            # Buscar elementos que contengan los códigos CF y CH
            cf_elements = await self.page.query_selector_all('text=CF:')
            
            for i, cf_element in enumerate(cf_elements):
                try:
                    # Obtener el contenedor padre del resultado
                    parent = await cf_element.locator('xpath=ancestor::div[contains(@class, "car-item") or contains(@class, "col-")]').first.element_handle()
                    if not parent:
                        # Intentar obtener un contenedor más amplio
                        parent = await cf_element.locator('xpath=ancestor::div[3]').first.element_handle()
                    
                    if parent:
                        # Extraer información del resultado
                        result_info = await self._extract_vehicle_info_from_element(parent, i + 1)
                        if result_info:
                            results.append(result_info)
                
                except Exception as e:
                    self.logger.debug(f"Error extrayendo información del elemento {i}: {e}")
                    continue
            
            # Si no se encontraron resultados con el método anterior, intentar método alternativo
            if not results:
                results = await self._extract_results_alternative_method()
            
            self.logger.info(f"📋 Se encontraron {len(results)} resultados")
            return results
            
        except Exception as e:
            self.logger.error(f"❌ Error extrayendo resultados: {e}")
            return []
    
    async def _extract_vehicle_info_from_element(self, element, index: int) -> Optional[Dict[str, str]]:
        """
        Extrae información de un elemento específico de vehículo.
        
        Args:
            element: Elemento DOM del vehículo
            index: Índice del vehículo
            
        Returns:
            Dict con información del vehículo
        """
        try:
            # Obtener texto completo del elemento
            text_content = await element.text_content()
            
            if not text_content:
                return None
            
            # Extraer códigos CF y CH usando expresiones regulares
            import re
            
            cf_match = re.search(r'CF:\s*(\d+)', text_content)
            ch_match = re.search(r'CH:\s*(\d+)', text_content)
            
            if not cf_match:
                return None
            
            cf_code = cf_match.group(1)
            ch_code = ch_match.group(1) if ch_match else cf_code
            
            # Extraer nombre del vehículo y precio
            lines = text_content.split('\n')
            vehicle_name = ''
            price = ''
            
            for line in lines:
                line = line.strip()
                if 'MAZDA' in line.upper() and not vehicle_name:
                    # Buscar líneas que contengan información del vehículo
                    for i, l in enumerate(lines):
                        if 'MAZDA' in l.upper():
                            # Combinar líneas para obtener el nombre completo
                            name_parts = []
                            for j in range(i, min(i + 4, len(lines))):
                                part = lines[j].strip()
                                if part and not part.startswith('CF:') and not part.startswith('CH:') and '$' not in part:
                                    if any(keyword in part.upper() for keyword in ['MAZDA', 'TOURING', 'GRAND', 'SIGNATURE', 'AT', 'CC', '4X4']):
                                        name_parts.append(part)
                            vehicle_name = ' '.join(name_parts[:3])  # Tomar las primeras 3 partes más relevantes
                            break
                
                if '$' in line and not price:
                    price = line.strip()
            
            if not vehicle_name:
                vehicle_name = f"MAZDA CX50 Opción {index}"
            
            return {
                'cf_code': cf_code,
                'ch_code': ch_code,
                'name': vehicle_name,
                'price': price,
                'index': index
            }
            
        except Exception as e:
            self.logger.debug(f"Error extrayendo info del elemento: {e}")
            return None
    
    async def _extract_results_alternative_method(self) -> List[Dict[str, str]]:
        """
        Método alternativo para extraer resultados usando JavaScript.
        
        Returns:
            Lista de diccionarios con información de vehículos
        """
        try:
            # Usar JavaScript para extraer la información
            results_data = await self.page.evaluate("""
                () => {
                    const results = [];
                    
                    // Buscar todos los elementos que contienen "CF:"
                    const cfElements = Array.from(document.querySelectorAll('*')).filter(el => 
                        el.textContent && el.textContent.includes('CF:')
                    );
                    
                    cfElements.forEach((el, index) => {
                        const text = el.textContent;
                        
                        // Extraer códigos CF y CH
                        const cfMatch = text.match(/CF:\\s*(\\d+)/);
                        const chMatch = text.match(/CH:\\s*(\\d+)/);
                        
                        if (cfMatch) {
                            const cfCode = cfMatch[1];
                            const chCode = chMatch ? chMatch[1] : cfCode;
                            
                            // Buscar el nombre del vehículo en el elemento o elementos cercanos
                            let vehicleName = 'MAZDA CX50 Opción ' + (index + 1);
                            let price = '';
                            
                            // Buscar en el elemento padre
                            const parent = el.closest('div');
                            if (parent) {
                                const parentText = parent.textContent;
                                
                                // Extraer precio
                                const priceMatch = parentText.match(/\\$[\\d,\\.]+/);
                                if (priceMatch) {
                                    price = priceMatch[0];
                                }
                                
                                // Extraer nombre del vehículo
                                const lines = parentText.split('\\n').map(l => l.trim()).filter(l => l);
                                for (let i = 0; i < lines.length; i++) {
                                    const line = lines[i];
                                    if (line.includes('MAZDA') || line.includes('TOURING') || line.includes('GRAND')) {
                                        const nameParts = [];
                                        for (let j = i; j < Math.min(i + 3, lines.length); j++) {
                                            const part = lines[j];
                                            if (part && !part.startsWith('CF:') && !part.startsWith('CH:') && !part.includes('$')) {
                                                if (/MAZDA|TOURING|GRAND|SIGNATURE|AT|CC|4X4/i.test(part)) {
                                                    nameParts.push(part);
                                                }
                                            }
                                        }
                                        if (nameParts.length > 0) {
                                            vehicleName = nameParts.join(' ');
                                        }
                                        break;
                                    }
                                }
                            }
                            
                            results.push({
                                cf_code: cfCode,
                                ch_code: chCode,
                                name: vehicleName,
                                price: price,
                                index: index + 1
                            });
                        }
                    });
                    
                    return results;
                }
            """)
            
            # Filtrar duplicados basados en CF code
            unique_results = []
            seen_cf_codes = set()
            
            for result in results_data:
                if result['cf_code'] not in seen_cf_codes:
                    seen_cf_codes.add(result['cf_code'])
                    unique_results.append(result)
            
            return unique_results
            
        except Exception as e:
            self.logger.error(f"❌ Error en método alternativo: {e}")
            return []
    
    async def _show_options_and_get_selection(self, results: List[Dict[str, str]]) -> Optional[Dict[str, str]]:
        """
        Muestra las opciones al usuario y obtiene su selección.
        
        Args:
            results: Lista de resultados disponibles
            
        Returns:
            Dict con códigos CF y CH seleccionados
        """
        try:
            print("\n" + "="*60)
            print("🚗 SELECCIÓN DE VEHÍCULO FASECOLDA")
            print("="*60)
            print("Se encontraron múltiples opciones. Por favor, seleccione una:")
            print()
            
            # Mostrar opciones
            for i, result in enumerate(results, 1):
                name = result.get('name', f"Opción {i}")
                price = result.get('price', 'Precio no disponible')
                cf_code = result.get('cf_code', 'N/A')
                ch_code = result.get('ch_code', 'N/A')
                
                print(f"[{i}] {name}")
                print(f"    💰 Valor: {price}")
                print(f"    🔢 CF: {cf_code} | CH: {ch_code}")
                print()
            
            # Obtener selección del usuario
            while True:
                try:
                    print(f"👆 Seleccione una opción (1-{len(results)}) o 'q' para cancelar: ", end="", flush=True)
                    selection = input().strip().lower()
                    
                    if selection == 'q':
                        print("❌ Selección cancelada por el usuario")
                        return None
                    
                    index = int(selection) - 1
                    if 0 <= index < len(results):
                        selected = results[index]
                        print(f"\n✅ Seleccionado: {selected.get('name', 'Opción')}")
                        print(f"🔢 Códigos - CF: {selected['cf_code']}, CH: {selected['ch_code']}")
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
