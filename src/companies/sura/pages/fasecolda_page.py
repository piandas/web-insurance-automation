"""Página de manejo de código Fasecolda específica para Sura"""

import os
import base64
import asyncio
from typing import Optional, Dict, List
from playwright.async_api import Page
from ....shared.base_page import BasePage
from ....config.sura_config import SuraConfig
from ....config.client_config import ClientConfig
from ....shared.fasecolda_service import FasecoldaService
from ....shared.fasecolda_extractor import get_global_fasecolda_codes
from ....shared.utils import Utils

class FasecoldaPage(BasePage):
    async def select_10_1_smlmv_in_dropdowns(self) -> bool:
        """Selecciona '1 SMLMV' en el dropdown de 'Pérdida Parcial' en ambos contenedores (Daños y Hurto)."""
        self.logger.info("🔽 Seleccionando '1 SMLMV' en los dropdowns de 'Pérdida Parcial' (Daños y Hurto)...")
        try:
            # Buscar todos los dropdowns de "Pérdida Parcial" usando el ID exacto
            dropdowns = await self.page.query_selector_all('dropdown-list[id="Pérdida Parcial"]')
            
            if len(dropdowns) < 2:
                self.logger.error(f"❌ No se encontraron dos dropdowns 'Pérdida Parcial' (encontrados: {len(dropdowns)})")
                return False
                
            self.logger.info(f"✅ Encontrados {len(dropdowns)} dropdowns de 'Pérdida Parcial'")
            
            # Procesar los primeros 2 dropdowns
            for idx in range(min(2, len(dropdowns))):
                dropdown = dropdowns[idx]
                
                # Hacer clic en el paper-dropdown-menu dentro del dropdown-list
                paper_dropdown = await dropdown.query_selector('paper-dropdown-menu')
                if not paper_dropdown:
                    self.logger.error(f"❌ No se encontró paper-dropdown-menu en dropdown #{idx+1}")
                    continue
                    
                await paper_dropdown.click()
                self.logger.info(f"✅ Desplegable 'Pérdida Parcial' #{idx+1} abierto")
                
                # Esperar un momento para que aparezcan las opciones
                await self.page.wait_for_timeout(500)
                
                # Buscar la opción exacta "1 SMLMV" (no "10% - 1 SMLMV")
                # Usar JavaScript para encontrar y hacer clic en el elemento correcto
                selection_result = await self.page.evaluate("""
                    () => {
                        const items = document.querySelectorAll('paper-item');
                        for (let item of items) {
                            if (item.textContent.trim() === '1 SMLMV' && item.offsetParent !== null) {
                                item.click();
                                return { success: true, text: item.textContent.trim() };
                            }
                        }
                        return { success: false, message: 'No encontrado' };
                    }
                """)
                
                if selection_result.get('success'):
                    self.logger.info(f"✅ Opción '1 SMLMV' seleccionada en 'Pérdida Parcial' #{idx+1}")
                else:
                    self.logger.error(f"❌ No se pudo seleccionar '1 SMLMV' en dropdown #{idx+1}")
                    
                await self.page.wait_for_timeout(500)
            
            return True
        except Exception as e:
            self.logger.error(f"❌ Error seleccionando '1 SMLMV' en dropdowns de 'Pérdida Parcial': {e}")
            return False

    async def select_limite_3040(self) -> bool:
        """Selecciona '3.040.000.000' en el dropdown de 'Limite' con reintentos."""
        self.logger.info("🔽 Seleccionando '3.040.000.000' en el dropdown de 'Limite'...")
        
        max_attempts = 5
        wait_time = 2000  # 2 segundos
        
        for attempt in range(1, max_attempts + 1):
            try:
                self.logger.info(f"🔄 Intento {attempt}/{max_attempts} para encontrar dropdown 'Limite'...")
                
                # Buscar el dropdown de "Limite" usando el ID exacto
                limite_dropdown = await self.page.query_selector('dropdown-list[id="Limite"]')
                
                if not limite_dropdown:
                    self.logger.warning(f"⚠️ Intento {attempt}: No se encontró el dropdown 'Limite'")
                    if attempt < max_attempts:
                        self.logger.info(f"⏳ Esperando {wait_time/1000} segundos antes del siguiente intento...")
                        await self.page.wait_for_timeout(wait_time)
                        continue
                    else:
                        self.logger.error("❌ No se encontró el dropdown 'Limite' después de todos los intentos")
                        return False
                    
                self.logger.info(f"✅ Intento {attempt}: Encontrado dropdown de 'Limite'")
                
                # Hacer clic en el paper-dropdown-menu dentro del dropdown-list
                paper_dropdown = await limite_dropdown.query_selector('paper-dropdown-menu')
                if not paper_dropdown:
                    self.logger.warning(f"⚠️ Intento {attempt}: No se encontró paper-dropdown-menu en dropdown 'Limite'")
                    if attempt < max_attempts:
                        await self.page.wait_for_timeout(wait_time)
                        continue
                    else:
                        self.logger.error("❌ No se encontró paper-dropdown-menu después de todos los intentos")
                        return False
                    
                await paper_dropdown.click()
                self.logger.info("✅ Desplegable 'Limite' abierto")
                
                # Esperar un momento para que aparezcan las opciones
                await self.page.wait_for_timeout(500)
                
                # Buscar y seleccionar la opción exacta "3.040.000.000"
                selection_result = await self.page.evaluate("""
                    () => {
                        const items = document.querySelectorAll('paper-item');
                        for (let item of items) {
                            if (item.textContent.trim() === '3.040.000.000' && item.offsetParent !== null) {
                                item.click();
                                return { success: true, text: item.textContent.trim() };
                            }
                        }
                        return { success: false, message: 'No encontrado' };
                    }
                """)
                
                if selection_result.get('success'):
                    self.logger.info("✅ Opción '3.040.000.000' seleccionada en 'Limite'")
                    
                    # Verificar que se mantenga seleccionado (la página puede cambiar el valor)
                    await self.page.wait_for_timeout(1000)
                    
                    # Verificar el valor actual del dropdown
                    current_value = await self.page.evaluate("""
                        () => {
                            const dropdown = document.querySelector('dropdown-list[id="Limite"]');
                            if (dropdown) {
                                const input = dropdown.querySelector('paper-input input');
                                return input ? input.value : null;
                            }
                            return null;
                        }
                    """)
                    
                    if current_value and '3.040.000.000' in current_value:
                        self.logger.info(f"✅ Límite confirmado y mantenido: {current_value}")
                        return True
                    else:
                        self.logger.warning(f"⚠️ Intento {attempt}: El valor cambió a '{current_value}', reintentando...")
                        if attempt < max_attempts:
                            await self.page.wait_for_timeout(wait_time)
                            continue
                        else:
                            self.logger.error("❌ No se pudo mantener el valor seleccionado después de todos los intentos")
                            return False
                else:
                    self.logger.warning(f"⚠️ Intento {attempt}: No se pudo seleccionar '3.040.000.000' en dropdown 'Limite'")
                    if attempt < max_attempts:
                        await self.page.wait_for_timeout(wait_time)
                        continue
                    else:
                        self.logger.error("❌ No se pudo seleccionar la opción después de todos los intentos")
                        return False
                    
            except Exception as e:
                self.logger.warning(f"⚠️ Error en intento {attempt} seleccionando dropdown 'Limite': {e}")
                if attempt < max_attempts:
                    await self.page.wait_for_timeout(wait_time)
                    continue
                else:
                    self.logger.error(f"❌ Error persistente después de {max_attempts} intentos: {e}")
                    return False
        
        self.logger.error("❌ Se agotaron todos los intentos para seleccionar el dropdown 'Limite'")
        return False

    async def process_used_vehicle_plate(self) -> bool:
        """Flujo especial para vehículos usados: solo ingresar placa y dar clic en la lupa."""
        self.logger.info("🔄 Proceso especial para vehículo USADO: solo placa y lupa...")
        try:
            # Input de placa (input dentro de #placa)
            plate_selector = self.SELECTORS['form_fields']['plate']
            lupa_selector = "#placa + paper-icon-button, #placa ~ paper-icon-button, #placa img[src*='ico-buscar'], #placa .style-scope.iron-icon, #placa ~ * img[src*='ico-buscar']"
            # Llenar placa
            await self.page.fill(plate_selector, ClientConfig.VEHICLE_PLATE)
            self.logger.info(f"✅ Placa '{ClientConfig.VEHICLE_PLATE}' ingresada")
            # Buscar y dar clic en la lupa
            lupa_clicked = False
            for sel in lupa_selector.split(","):
                sel = sel.strip()
                try:
                    await self.page.wait_for_selector(sel, timeout=3000)
                    await self.page.click(sel, timeout=2000)
                    self.logger.info(f"✅ Clic en lupa con selector: {sel}")
                    lupa_clicked = True
                    break
                except Exception as e:
                    self.logger.debug(f"No se pudo hacer clic en lupa con {sel}: {e}")
            if not lupa_clicked:
                self.logger.error("❌ No se pudo hacer clic en la lupa de placa")
                return False
            # Esperar a que aparezca la marca (o algún campo de datos del vehículo)
            # Inspirado en otros waits: intentar varios selectores y reintentar
            marca_selectors = [
                "#marca",  # div o input con id marca
                "input[ng-reflect-name*='marca']",
                "#referencia",  # a veces aparece referencia
                "input[ng-reflect-name*='referencia']",
                "#modelo",  # año/modelo
                "input[ng-reflect-name*='modelo']",
                "#clase",  # clase vehículo
                "input[ng-reflect-name*='clase']"
            ]
            found = False
            for i in range(10):  # hasta 10 intentos (10s)
                for sel in marca_selectors:
                    try:
                        el = await self.page.query_selector(sel)
                        if el:
                            visible = await el.is_visible()
                            if visible:
                                self.logger.info(f"✅ Campo de datos detectado: {sel}")
                                found = True
                                break
                    except Exception:
                        continue
                if found:
                    break
                await self.page.wait_for_timeout(1000)
            if not found:
                # Loggear HTML para debug
                html = await self.page.content()
                self.logger.error("❌ No se detectó ningún campo de datos del vehículo tras ingresar la placa. Dump HTML para debug:")
                self.logger.error(html[:2000])
                return False
            self.logger.info("✅ Marca o campo de datos detectado, datos del vehículo cargados")
            return True
        except Exception as e:
            self.logger.error(f"❌ Error en flujo de placa usada: {e}")
            return False
    """Página de manejo de código Fasecolda para Sura."""
    
    # Selectores principales - agrupados por funcionalidad
    SELECTORS = {
        'fasecolda': {
            'input': "input[aria-labelledby*='paper-input-label']:not([placeholder*='DD/MM/YYYY'])",
            'error_message': "#divMessage:has-text('No existe el fasecolda')",
            'accept_button': "#btnOne:has-text('Aceptar')"
        },
        'dropdowns': {
            'vehicle_category': "#clase",
            'model_year': "#modelo", 
            'service_type': "#tipoServicio",
            'limite': 'dropdown-list[id="Limite"]'
        },
        'form_fields': {
            'city': "input[aria-label='Ciudad']",
            'plate': "#placa input",
            'zero_km_radio': "paper-radio-button[title='opcion-Si']",
            'valor_asegurado': "input[name='amount'][required]"  # Selector más específico para el campo requerido
        },
        'plans': {
            'prima_anual': "#primaAnual",
            'clasico': "div.horizontal.layout.contenedor-nom-plan:has-text('Plan Autos Clásico')",
            'global': "div.horizontal.layout.contenedor-nom-plan:has-text('Plan Autos Global')"
        },
        'actions': {
            'modal_accept': "#btnOne",
            'modal_dialog': "div.dialog-content-base.info",
            'ver_cotizacion': "paper-button.boton-accion-principal:has-text('Ver cotización')",
            'menu_toggle': "paper-fab[icon='apps']",
            'pdf_download': "paper-fab[data-menuitem='Descargar PDF']"
        }
    }
    
    # Opciones de dropdown
    OPTIONS = {
        'vehicle_category': "paper-item:has-text('AUTOMÓVILES')",
        'service_type': "paper-item:has-text('Particular')",
        'city': "vaadin-combo-box-item:has-text('Medellin - (Antioquia)')",
        'model_year_template': "paper-item:has-text('{year}')",
        'limite': "paper-item:has-text('3.040.000.000')"
    }

    def __init__(self, page: Page):
        super().__init__(page, 'sura')
        self.config = SuraConfig()

    async def get_fasecolda_code(self) -> Optional[dict]:
        """Obtiene los códigos Fasecolda desde el extractor global o usa el código por defecto."""
        self.logger.info("🔍 Obteniendo códigos Fasecolda...")
        
        try:
            # Verificar si Fasecolda está habilitado globalmente
            if not ClientConfig.is_fasecolda_enabled():
                manual_codes = ClientConfig.get_manual_fasecolda_codes()
                self.logger.info(f"📋 Fasecolda deshabilitado - usando códigos manuales - CF: {manual_codes['cf_code']}, CH: {manual_codes['ch_code']}")
                return manual_codes
            
            # Verificar configuración específica de Sura
            if not ClientConfig.should_use_fasecolda_for_company('sura'):
                manual_codes = ClientConfig.get_manual_fasecolda_codes()
                self.logger.info(f"⏭️ Búsqueda automática de Fasecolda deshabilitada para Sura - usando códigos manuales - CF: {manual_codes['cf_code']}, CH: {manual_codes['ch_code']}")
                return manual_codes
            
            if ClientConfig.VEHICLE_STATE != 'Nuevo':
                self.logger.info(f"⏭️ Vehículo '{ClientConfig.VEHICLE_STATE}' - no requiere código Fasecolda")
                return None
            
            # Obtener códigos del extractor global
            codes = await get_global_fasecolda_codes(timeout=30)
            
            if codes and codes.get('cf_code'):
                ch_info = f" - CH: {codes.get('ch_code')}" if codes.get('ch_code') else ""
                self.logger.info(f"✅ Códigos Fasecolda obtenidos del extractor global - CF: {codes['cf_code']}{ch_info}")
                return codes
            else:
                # Fallback: usar códigos manuales cuando la búsqueda automática falla
                manual_codes = ClientConfig.get_manual_fasecolda_codes()
                self.logger.warning(f"⚠️ No se pudieron obtener códigos Fasecolda del extractor global - usando códigos manuales como fallback - CF: {manual_codes['cf_code']}, CH: {manual_codes['ch_code']}")
                return manual_codes
                
        except Exception as e:
            # Fallback: usar códigos manuales cuando hay errores
            manual_codes = ClientConfig.get_manual_fasecolda_codes()
            self.logger.error(f"❌ Error obteniendo códigos Fasecolda: {e} - usando códigos manuales como fallback - CF: {manual_codes['cf_code']}, CH: {manual_codes['ch_code']}")
            return manual_codes

    async def fill_fasecolda_code(self, cf_code: str) -> bool:
        """Llena el campo del código Fasecolda buscando dinámicamente por etiqueta."""
        self.logger.info(f"📋 Llenando código Fasecolda: {cf_code}")
        
        try:
            fasecolda_selector = await self._find_fasecolda_input_selector()
            if not fasecolda_selector:
                self.logger.error("❌ No se pudo encontrar el campo de Fasecolda")
                return False
            
            self.logger.info(f"📝 Campo Fasecolda encontrado con selector: {fasecolda_selector}")
            
            # Usar método de la clase base
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
        """Verifica y maneja el mensaje de error 'No existe el fasecolda'."""
        self.logger.info("🔍 Verificando si hay error de Fasecolda...")
        
        try:
            if await self.is_visible_safe(self.SELECTORS['fasecolda']['error_message'], timeout=3000):
                self.logger.warning("⚠️ Detectado mensaje 'No existe el fasecolda'")
                
                if await self.safe_click(self.SELECTORS['fasecolda']['accept_button'], timeout=5000):
                    self.logger.info("✅ Botón 'Aceptar' presionado exitosamente")
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
        codes_to_try = [(t, codes.get(f'{t.lower()}_code')) for t in ['CH', 'CF'] if codes.get(f'{t.lower()}_code')]
        
        if not codes_to_try:
            self.logger.error("❌ No hay códigos disponibles para intentar")
            return False
        
        for attempt, (code_type, code_value) in enumerate(codes_to_try, 1):
            self.logger.info(f"🎯 Intento {attempt}: Probando código {code_type}: {code_value}")
            
            # Llenar el código y seleccionar opciones
            steps = [
                (self.fill_fasecolda_code, [code_value], f"código {code_type}"),
                (self._select_dropdown_option, ['vehicle_category'], "categoría AUTOMÓVILES"),
                (self._select_dropdown_option, ['model_year'], "año del modelo")
            ]
            
            success = True
            for step_func, step_args, step_desc in steps:
                if not await step_func(*step_args):
                    self.logger.warning(f"⚠️ No se pudo {step_desc}")
                    success = False
                    break
            
            if not success:
                await self._clear_fasecolda_field()
                continue
            
            # Verificar si apareció error
            if not await self.check_and_handle_fasecolda_error():
                self.logger.info(f"✅ Código {code_type} aceptado exitosamente")
                return True
            else:
                self.logger.warning(f"⚠️ Código {code_type} rechazado, continuando con siguiente...")
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
            return await self.page.evaluate("""
                () => {
                    const inputs = Array.from(document.querySelectorAll('input'));
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
        except Exception as e:
            self.logger.warning(f"⚠️ Error buscando selector de Fasecolda dinámicamente: {e}")
            return None

    async def _select_dropdown_option(self, dropdown_type: str) -> bool:
        """Método genérico para seleccionar opciones de dropdown."""
        dropdown_info = {
            'vehicle_category': {
                'dropdown': self.SELECTORS['dropdowns']['vehicle_category'],
                'option': self.OPTIONS['vehicle_category'],
                'description': "categoría de vehículo: AUTOMÓVILES"
            },
            'model_year': {
                'dropdown': self.SELECTORS['dropdowns']['model_year'],
                'option': self.OPTIONS['model_year_template'].format(year=ClientConfig.VEHICLE_MODEL_YEAR),
                'description': f"año del modelo: {ClientConfig.VEHICLE_MODEL_YEAR}"
            },
            'service_type': {
                'dropdown': self.SELECTORS['dropdowns']['service_type'],
                'option': self.OPTIONS['service_type'],
                'description': "tipo de servicio: Particular"
            },
            'limite': {
                'dropdown': self.SELECTORS['dropdowns']['limite'],
                'option': self.OPTIONS['limite'],
                'description': "límite: 3.040.000.000"
            }
        }
        
        if dropdown_type not in dropdown_info:
            self.logger.error(f"❌ Tipo de dropdown no reconocido: {dropdown_type}")
            return False
        
        info = dropdown_info[dropdown_type]
        self.logger.info(f"🔽 Seleccionando {info['description']}...")
        
        try:
            # Abrir dropdown
            if not await self.safe_click(info['dropdown'], timeout=10000):
                return False
            
            await self.page.wait_for_timeout(1000)
            
            # Seleccionar opción
            if not await self.safe_click(info['option'], timeout=5000):
                return False
            
            self.logger.info(f"✅ {info['description']} seleccionado exitosamente")
            await self.page.wait_for_timeout(1500)
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error seleccionando {info['description']}: {e}")
            return False

    async def fill_city(self) -> bool:
        """Llena el campo de ciudad y selecciona la opción correspondiente."""
        client_city = ClientConfig.get_client_city('sura')
        self.logger.info(f"🏙️ Llenando ciudad: {client_city}...")
        
        try:
            # Llenar el campo de ciudad
            await self.page.fill(self.SELECTORS['form_fields']['city'], client_city)
            await self.page.wait_for_timeout(1500)
            
            # Crear selector dinámico basado en la ciudad del cliente
            # Para Envigado, la opción aparece como "Envigado - (Antioquia)"
            if client_city.upper() == "ENVIGADO":
                city_selector = "vaadin-combo-box-item:has-text('Envigado - (Antioquia)')"
            elif client_city.upper() in ["MEDELLIN", "MEDELLÍN"]:
                city_selector = "vaadin-combo-box-item:has-text('Medellin - (Antioquia)')"
            else:
                # Para otras ciudades, intentar con el formato general
                city_selector = f"vaadin-combo-box-item:has-text('{client_city} - (Antioquia)')"
            
            self.logger.info(f"🎯 Intentando seleccionar opción: {city_selector}")
            
            if not await self.safe_click(city_selector, timeout=5000):
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
        
        return await self.fill_and_verify_field_flexible(
            selector=self.SELECTORS['form_fields']['plate'],
            value="XXX123",
            field_name="Placa",
            max_attempts=3
        )

    async def fill_valor_asegurado(self, valor: str = None) -> bool:
        """
        Llena el campo de valor asegurado en Sura.
        
        Args:
            valor: Valor asegurado como string numérico (ej: "95000000")
                  Si es None, se toma del ClientConfig
        
        Returns:
            bool: True si se llenó exitosamente, False en caso contrario
        """
        if valor is None:
            valor = ClientConfig.get_vehicle_insured_value()
            
        # Debug logging
        vehicle_state = ClientConfig.get_vehicle_state()
        self.logger.info(f"🔍 DEBUG - Estado del vehículo: {vehicle_state}")
        self.logger.info(f"🔍 DEBUG - Valor asegurado obtenido: '{valor}'")
        
        if not valor:
            # Para vehículos nuevos, el valor es obligatorio
            if ClientConfig.get_vehicle_state() == "Nuevo":
                self.logger.error("❌ Valor asegurado es obligatorio para vehículos nuevos")
                return False
            else:
                self.logger.info("ℹ️ No se proporcionó valor asegurado (se extraerá automáticamente para vehículos usados)")
                return True
        
        self.logger.info(f"💰 Llenando valor asegurado en Sura: {valor}")
        
        try:
            # Formatear valor para Sura (solo números, sin símbolos)
            valor_formateado = valor if valor.isdigit() else valor
            
            # Intentar con varios selectores para encontrar el campo correcto
            selectors_to_try = [
                "input[name='amount'][required]",  # Selector específico con required
                "input[name='amount'][maxlength='13']",  # Selector con maxlength
                "input[name='amount']",  # Selector básico
                "paper-input input[name='amount']"  # Selector con contenedor paper-input
            ]
            
            for selector in selectors_to_try:
                self.logger.info(f"🔍 Intentando llenar valor asegurado con selector: {selector}")
                success = await self.fill_valor_asegurado_con_validacion_personalizada(
                    selector=selector,
                    value=valor_formateado,
                    max_attempts=2
                )
                if success:
                    self.logger.info(f"✅ Valor asegurado llenado exitosamente con selector: {selector}")
                    return True
                else:
                    self.logger.warning(f"⚠️ Falló con selector: {selector}")
            
            self.logger.error("❌ No se pudo llenar el valor asegurado con ningún selector")
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Error llenando valor asegurado: {e}")
            return False

    async def fill_valor_asegurado_con_validacion_personalizada(self, selector: str, value: str, max_attempts: int = 2) -> bool:
        """
        Llena el campo de valor asegurado con validación personalizada que acepta formato con puntos.
        
        Args:
            selector: Selector CSS del campo
            value: Valor a llenar (formato sin puntos, ej: "259000000")
            max_attempts: Número máximo de intentos
            
        Returns:
            bool: True si se llenó exitosamente, False en caso contrario
        """
        for attempt in range(1, max_attempts + 1):
            self.logger.info(f"🔍 Valor asegurado - Intento {attempt}/{max_attempts}")
            
            try:
                # Llenar el campo
                await self.page.fill(selector, value)
                await self.page.wait_for_timeout(500)
                
                # Obtener el valor actual del campo para verificar
                actual_value = await self.page.input_value(selector)
                
                # Validación personalizada: aceptar tanto el formato original como el formato con puntos
                value_clean = value.replace(".", "").replace(",", "")  # Formato limpio
                actual_clean = actual_value.replace(".", "").replace(",", "")  # Formato limpio
                
                if value_clean == actual_clean:
                    self.logger.info(f"✅ Valor asegurado llenado correctamente: '{actual_value}'")
                    return True
                else:
                    self.logger.warning(f"⚠️ Valor asegurado - Esperado: '{value}', Actual: '{actual_value}' (ambos válidos)")
                    # Si los valores limpios coinciden, considerarlo exitoso
                    if len(actual_clean) > 0 and actual_clean.isdigit():
                        self.logger.info(f"✅ Valor asegurado aceptado en formato con puntos: '{actual_value}'")
                        return True
                    
                    if attempt < max_attempts:
                        self.logger.info("🔄 Valor asegurado - Reintentando...")
                        await self.page.wait_for_timeout(1000)
                    
            except Exception as e:
                self.logger.warning(f"⚠️ Valor asegurado - Error en intento {attempt}: {e}")
                if attempt < max_attempts:
                    await self.page.wait_for_timeout(1000)
        
        self.logger.error(f"❌ Valor asegurado - No se pudo llenar después de {max_attempts} intentos")
        return False

    async def select_zero_kilometers(self) -> bool:
        """Selecciona 'Sí' en la opción de cero kilómetros."""
        self.logger.info("🆕 Seleccionando vehículo cero kilómetros: Sí...")
        
        try:
            if not await self.safe_click(self.SELECTORS['form_fields']['zero_km_radio'], timeout=10000):
                self.logger.error("❌ No se pudo seleccionar la opción de cero kilómetros")
                return False
            
            self.logger.info("✅ Opción 'Sí' para cero kilómetros seleccionada exitosamente")
            await self.page.wait_for_timeout(1500)
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error seleccionando cero kilómetros: {e}")
            return False

    async def trigger_quote_calculation(self) -> bool:
        """Hace clic en un área vacía para deseleccionar y activar el cálculo de la cotización."""
        self.logger.info("🎯 Activando cálculo de cotización...")
        
        try:
            await self.page.click("body")
            await self.page.wait_for_timeout(3000)
            self.logger.info("✅ Cálculo de cotización activado")
            
            # Verificar y reseleccionar límite si cambió (máximo 3 intentos cada 2 segundos)
            await self._verify_and_reselect_limite()
            
            return True
        except Exception as e:
            self.logger.error(f"❌ Error activando cálculo de cotización: {e}")
            return False

    async def _verify_and_reselect_limite(self) -> bool:
        """Verifica que el límite siga en 3.040.000.000 y lo reselecciona si cambió."""
        max_attempts = 3
        
        for attempt in range(1, max_attempts + 1):
            try:
                await self.page.wait_for_timeout(2000)  # Esperar 2 segundos
                
                # Verificar el valor actual del dropdown
                current_value = await self.page.evaluate("""
                    () => {
                        const dropdown = document.querySelector('dropdown-list[id="Limite"]');
                        if (dropdown) {
                            const input = dropdown.querySelector('paper-input input');
                            return input ? input.value : null;
                        }
                        return null;
                    }
                """)
                
                if current_value and '3.040.000.000' in current_value:
                    self.logger.info(f"✅ Verificación {attempt}/3: Límite mantenido - {current_value}")
                    return True
                else:
                    self.logger.warning(f"⚠️ Verificación {attempt}/3: Límite cambió a '{current_value}', reseleccionando...")
                    
                    # Intentar reseleccionar rápidamente
                    limite_dropdown = await self.page.query_selector('dropdown-list[id="Limite"]')
                    if limite_dropdown:
                        paper_dropdown = await limite_dropdown.query_selector('paper-dropdown-menu')
                        if paper_dropdown:
                            await paper_dropdown.click()
                            await self.page.wait_for_timeout(500)
                            
                            # Seleccionar la opción correcta
                            selection_result = await self.page.evaluate("""
                                () => {
                                    const items = document.querySelectorAll('paper-item');
                                    for (let item of items) {
                                        if (item.textContent.trim() === '3.040.000.000' && item.offsetParent !== null) {
                                            item.click();
                                            return true;
                                        }
                                    }
                                    return false;
                                }
                            """)
                            
                            if selection_result:
                                self.logger.info(f"✅ Límite reseleccionado exitosamente en intento {attempt}")
                                continue  # Verificar en la siguiente iteración
                            else:
                                self.logger.warning(f"⚠️ No se pudo reseleccionar límite en intento {attempt}")
                    
                    if attempt == max_attempts:
                        self.logger.warning("⚠️ No se pudo mantener el límite después de 3 intentos, continuando...")
                        return False
                        
            except Exception as e:
                self.logger.warning(f"⚠️ Error en verificación {attempt}: {e}")
                if attempt == max_attempts:
                    return False
        
        return True

    async def extract_prima_anual_value(self, max_wait_seconds: int = 20) -> Optional[float]:
        """Extrae el valor numérico de la prima anual esperando hasta que aparezca."""
        self.logger.info(f"💰 Esperando y extrayendo valor de prima anual (máximo {max_wait_seconds} segundos)...")
        
        try:
            for attempt in range(max_wait_seconds):
                try:
                    element = await self.page.query_selector(self.SELECTORS['plans']['prima_anual'])
                    if element:
                        text_content = await element.text_content()
                        if text_content and text_content.strip():
                            # ⏱️ VERIFICAR ESTABILIDAD DEL VALOR (3 intentos de 1 segundo)
                            self.logger.info("✅ Valor detectado, verificando estabilidad...")
                            
                            import re
                            
                            # Obtener valor inicial
                            initial_numbers = re.sub(r'[^\d]', '', text_content)
                            if not initial_numbers:
                                continue
                            
                            stable_value = None
                            
                            # 3 reintentos de 1 segundo para verificar estabilidad
                            for stability_check in range(1, 4):
                                await self.page.wait_for_timeout(1000)  # Esperar 1 segundo
                                
                                # Volver a extraer el valor
                                element = await self.page.query_selector(self.SELECTORS['plans']['prima_anual'])
                                if element:
                                    current_text = await element.text_content()
                                    if current_text and current_text.strip():
                                        current_numbers = re.sub(r'[^\d]', '', current_text)
                                        
                                        if current_numbers == initial_numbers:
                                            self.logger.info(f"🔄 Estabilidad {stability_check}/3: Valor mantenido - {current_numbers}")
                                            stable_value = current_numbers
                                        else:
                                            self.logger.info(f"🔄 Estabilidad {stability_check}/3: Valor cambió de {initial_numbers} a {current_numbers}")
                                            initial_numbers = current_numbers  # Actualizar para el siguiente check
                                            stable_value = current_numbers
                                    else:
                                        self.logger.warning(f"⚠️ Estabilidad {stability_check}/3: No se pudo leer el valor")
                                        break
                                else:
                                    self.logger.warning(f"⚠️ Estabilidad {stability_check}/3: Elemento no encontrado")
                                    break
                            
                            if stable_value and stable_value.isdigit():
                                value = float(stable_value)
                                self.logger.info(f"✅ Prima anual estabilizada extraída: ${value:,.0f}")
                                return value
                            else:
                                self.logger.warning("⚠️ No se pudo estabilizar el valor de prima anual")
                    
                    await self.page.wait_for_timeout(1000)
                    
                except Exception as e:
                    self.logger.debug(f"Intento {attempt + 1} fallido: {e}")
                    await self.page.wait_for_timeout(1000)
            
            self.logger.warning("⚠️ No se pudo extraer el valor de prima anual después de esperar")
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Error extrayendo prima anual: {e}")
            return None

    async def _click_plan(self, plan_type: str) -> bool:
        """Método genérico para hacer clic en planes."""
        plan_info = {
            'clasico': {'selector': self.SELECTORS['plans']['clasico'], 'name': 'Plan Autos Clásico'},
            'global': {'selector': self.SELECTORS['plans']['global'], 'name': 'Plan Autos Global'}
        }
        
        if plan_type not in plan_info:
            self.logger.error(f"❌ Tipo de plan no reconocido: {plan_type}")
            return False
        
        info = plan_info[plan_type]
        self.logger.info(f"🎯 Haciendo clic en {info['name']}...")
        
        try:
            if not await self.safe_click(info['selector'], timeout=10000):
                self.logger.error(f"❌ No se pudo hacer clic en {info['name']}")
                return False
            
            self.logger.info(f"✅ Clic en {info['name']} exitoso")
            await self.page.wait_for_timeout(3000)
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error haciendo clic en {info['name']}: {e}")
            return False

    async def click_plan_autos_clasico(self) -> bool:
        """Hace clic en el Plan Autos Clásico."""
        return await self._click_plan('clasico')

    async def click_plan_autos_global(self) -> bool:
        """Hace clic en el Plan Autos Global y maneja modales opcionales."""
        if await self._click_plan('global'):
            # Manejar modales después del cambio de plan
            await self.check_and_handle_continuity_modal()
            await self.handle_optional_modal()
            return True
        return False

    async def handle_optional_modal(self) -> bool:
        """Maneja un modal opcional que puede aparecer después de seleccionar el plan."""
        self.logger.info("🔍 Verificando si aparece modal opcional...")
        
        try:
            # Verificar si apareció algún modal
            modal_selectors = [
                self.SELECTORS['actions']['modal_dialog'],
                self.SELECTORS['actions']['modal_accept']
            ]
            
            # Evaluar cada selector de forma secuencial para evitar async generator error
            modal_visible = False
            for selector in modal_selectors:
                if await self.is_visible_safe(selector, timeout=5000):
                    modal_visible = True
                    break
            
            if modal_visible:
                self.logger.info("📋 Modal opcional detectado, haciendo clic en Aceptar...")
                
                # Intentar con múltiples selectores
                accept_selectors = [
                    self.SELECTORS['actions']['modal_accept'],
                    "paper-button:has-text('Aceptar')"
                ]
                
                for selector in accept_selectors:
                    if await self.safe_click(selector, timeout=5000):
                        self.logger.info("✅ Botón 'Aceptar' del modal presionado exitosamente")
                        await self.page.wait_for_timeout(3000)
                        return True
                
                self.logger.error("❌ No se pudo hacer clic en el botón 'Aceptar' del modal")
                return False
            else:
                self.logger.info("✅ No se detectó modal opcional")
                return True
                
        except Exception as e:
            self.logger.warning(f"⚠️ Error verificando modal opcional: {e}")
            return True  # No bloqueamos el flujo

    async def check_and_handle_continuity_modal(self) -> bool:
        """Verifica y maneja específicamente el modal de continuidad de placa."""
        self.logger.info("🔍 Verificando modal de continuidad de placa...")
        
        try:
            if await self.is_visible_safe("div:has-text('La placa ingresada al momento de la cotización  cumple con continuidad')", timeout=3000):
                self.logger.info("📋 Modal de continuidad detectado, haciendo clic en Aceptar...")
                
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

    async def handle_pre_action_modal(self) -> bool:
        """Maneja modal con botón 'Aceptar' que puede aparecer antes de acciones principales."""
        self.logger.info("🔍 Verificando modal pre-acción con botón 'Aceptar'...")
        
        try:
            # Selectores específicos para el modal "Aceptar"
            modal_selectors = [
                "paper-button:has-text('Aceptar')",
                "#btnOne:has-text('Aceptar')",
                "paper-button[class*='accent']:has-text('Aceptar')"
            ]
            
            # Verificar si existe algún modal con botón Aceptar
            modal_found = False
            for selector in modal_selectors:
                if await self.is_visible_safe(selector, timeout=3000):
                    self.logger.info(f"📋 Modal pre-acción detectado con selector: {selector}")
                    
                    if await self.safe_click(selector, timeout=5000):
                        self.logger.info("✅ Botón 'Aceptar' del modal pre-acción presionado exitosamente")
                        await self.page.wait_for_timeout(2000)
                        modal_found = True
                        break
                    else:
                        self.logger.warning(f"⚠️ No se pudo hacer clic en el modal con selector: {selector}")
            
            if not modal_found:
                self.logger.info("✅ No se detectó modal pre-acción")
            
            return True
                
        except Exception as e:
            self.logger.warning(f"⚠️ Error verificando modal pre-acción: {e}")
            return True  # No bloqueamos el flujo

    async def click_ver_cotizacion(self) -> bool:
        """Hace clic en el botón 'Ver cotización'."""
        self.logger.info("🎯 Haciendo clic en 'Ver cotización'...")
        
        try:
            # Primero manejar cualquier modal que pueda aparecer
            await self.handle_pre_action_modal()
            
            if not await self.safe_click(self.SELECTORS['actions']['ver_cotizacion'], timeout=10000):
                self.logger.error("❌ No se pudo hacer clic en 'Ver cotización'")
                return False
            
            self.logger.info("✅ Clic en 'Ver cotización' exitoso")
            await self.page.wait_for_timeout(2000)
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error haciendo clic en 'Ver cotización': {e}")
            return False

    async def activate_menu_toggle(self) -> bool:
        """Activa el menú flotante haciendo clic en el botón de apps."""
        self.logger.info("📱 Activando menú flotante...")
        
        try:
            if not await self.safe_click(self.SELECTORS['actions']['menu_toggle'], timeout=10000):
                self.logger.error("❌ No se pudo hacer clic en el botón de menú")
                return False
            
            self.logger.info("✅ Menú flotante activado exitosamente")
            await self.page.wait_for_timeout(1500)
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error activando menú flotante: {e}")
            return False

    async def _handle_optional_pdf_modal(self) -> bool:
        """Maneja específicamente el modal opcional que aparece justo antes del PDF."""
        self.logger.info("🔍 Verificando modal opcional específico antes del PDF...")
        
        try:
            # Primero verificar si hay un iron-overlay-backdrop activo
            backdrop_visible = await self.is_visible_safe("iron-overlay-backdrop.opened", timeout=1000)
            if backdrop_visible:
                self.logger.info("🎭 Detectado iron-overlay-backdrop activo, buscando modal...")
                
                # Verificar específicamente el modal de continuidad de placa
                continuity_modal = await self.is_visible_safe(".dialog-content-base.info", timeout=1000)
                if continuity_modal:
                    self.logger.info("📋 Modal de continuidad de placa detectado")
                    
                    # Intentar hacer clic en el botón Aceptar específico
                    if await self.safe_click("#btnOne", timeout=3000):
                        self.logger.info("✅ Botón 'Aceptar' del modal de continuidad presionado")
                        await self.page.wait_for_timeout(2000)
                        return True
            
            # Selectores más específicos para el modal antes del PDF (en orden de prioridad)
            pdf_modal_selectors = [
                # Primero probar el botón específico del modal de continuidad
                "#btnOne",
                "#btnOne:has-text('Aceptar')",
                
                # Luego otros botones específicos por ID
                "#btnAceptar", 
                "#accept-btn",
                "#confirm-btn",
                
                # Botones de aceptar/confirmar genéricos
                "paper-button:has-text('Aceptar')",
                "paper-button:has-text('ACEPTAR')",
                "paper-button:has-text('Confirmar')",
                "paper-button:has-text('OK')",
                "paper-button:has-text('Continuar')",
                "paper-button:has-text('Sí')",
                
                # Por clases
                "paper-button[class*='accent']",
                "paper-button[class*='primary']",
                ".accept-button",
                ".confirm-button",
                
                # Botones en diálogos/modales
                "paper-dialog paper-button:has-text('Aceptar')",
                "paper-dialog-scrollable paper-button:has-text('Aceptar')",
                "iron-overlay-backdrop ~ * paper-button:has-text('Aceptar')"
            ]
            
            # Intentar con cada selector
            for selector in pdf_modal_selectors:
                try:
                    self.logger.info(f"🔍 Probando selector: {selector}")
                    
                    # Verificar visibilidad con timeout corto
                    if await self.is_visible_safe(selector, timeout=1000):
                        self.logger.info(f"📋 Modal PDF específico encontrado: {selector}")
                        
                        # Hacer clic con timeout más largo
                        if await self.safe_click(selector, timeout=5000):
                            self.logger.info("✅ Modal PDF específico manejado exitosamente")
                            await self.page.wait_for_timeout(2000)
                            return True
                        else:
                            self.logger.warning(f"⚠️ No se pudo hacer clic en modal PDF: {selector}")
                            
                except Exception as e:
                    self.logger.debug(f"Selector {selector} falló: {e}")
                    continue
            
            self.logger.info("✅ No se detectó modal opcional específico para PDF")
            return True
                
        except Exception as e:
            self.logger.warning(f"⚠️ Error verificando modal PDF específico: {e}")
            return True  # No bloqueamos el flujo

    async def download_pdf_quote(self) -> bool:
        """Descarga el PDF de la cotización usando conversión blob → base64."""
        self.logger.info("📄 Iniciando descarga de PDF...")

        try:
            # Primero manejar cualquier modal que pueda aparecer
            await self.handle_pre_action_modal()
            
            # Verificación específica para modal opcional antes del PDF
            await self._handle_optional_pdf_modal()
            
            # Esperar 2 segundos para que se estabilice antes de descargar PDF
            self.logger.info("⏳ Esperando 2 segundos para estabilización antes de descargar PDF...")
            await asyncio.sleep(2)
            
            # Esperar por nueva pestaña y hacer clic en PDF (con reintento si es necesario)
            self.logger.info("🌐 Detectando nueva pestaña con el PDF...")
            nuevo_popup = None
            
            # Primer intento
            try:
                # Verificación adicional de backdrop antes del clic
                backdrop_check = await self.is_visible_safe("iron-overlay-backdrop.opened", timeout=500)
                if backdrop_check:
                    self.logger.warning("⚠️ Detectado backdrop activo antes del clic PDF, manejando modal...")
                    await self._handle_optional_pdf_modal()
                    await asyncio.sleep(1)
                
                async with self.page.context.expect_page(timeout=5000) as new_page_info:
                    if not await self.safe_click(self.SELECTORS['actions']['pdf_download'], timeout=10000):
                        self.logger.error("❌ No se pudo hacer clic en el botón de descarga PDF")
                        return False
                    self.logger.info("✅ Clic en botón PDF exitoso")

                nuevo_popup = await new_page_info.value
                
            except Exception as e:
                self.logger.warning(f"⚠️ No se detectó nueva pestaña en 5 segundos, reintentando con modal opcional: {e}")
                
                # Intentar manejar modal opcional nuevamente y reintentar
                await self._handle_optional_pdf_modal()
                await asyncio.sleep(1)
                
                # Segundo intento
                try:
                    # Verificación adicional de backdrop en el reintento
                    backdrop_check_retry = await self.is_visible_safe("iron-overlay-backdrop.opened", timeout=500)
                    if backdrop_check_retry:
                        self.logger.warning("⚠️ Backdrop sigue activo en reintento, manejando modal nuevamente...")
                        await self._handle_optional_pdf_modal()
                        await asyncio.sleep(1)
                    
                    async with self.page.context.expect_page(timeout=5000) as new_page_info_retry:
                        if not await self.safe_click(self.SELECTORS['actions']['pdf_download'], timeout=10000):
                            self.logger.error("❌ No se pudo hacer clic en el botón de descarga PDF en segundo intento")
                            return False
                        self.logger.info("✅ Clic en botón PDF exitoso (segundo intento)")

                    nuevo_popup = await new_page_info_retry.value
                    
                except Exception as retry_e:
                    self.logger.error(f"❌ Falló segundo intento de detección de pestaña PDF: {retry_e}")
                    return False
            
            if not nuevo_popup:
                self.logger.error("❌ No se pudo obtener la nueva pestaña con el PDF")
                return False
            await nuevo_popup.wait_for_load_state("networkidle")

            # Esperar URL real del PDF (máximo 45 segundos)
            self.logger.info("⏳ Esperando que aparezca la URL real del PDF (máximo 45 segundos)...")
            pdf_url = None
            for attempt in range(45):
                current_url = nuevo_popup.url
                if current_url != "about:blank" and (current_url.startswith("blob:") or current_url.startswith("http")):
                    pdf_url = current_url
                    self.logger.info(f"✅ URL del PDF encontrada: {pdf_url}")
                    break
                await nuevo_popup.wait_for_timeout(1000)

            if not pdf_url or pdf_url == "about:blank":
                self.logger.error("❌ No se pudo obtener una URL válida del PDF después de 45 segundos")
                await nuevo_popup.close()
                return False

            # Preparar ruta de guardado
            nombre = Utils.generate_filename('sura', 'Cotizacion')
            downloads_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))),
                'downloads', 'sura'
            )
            Utils.ensure_directory(downloads_dir)
            ruta = os.path.join(downloads_dir, nombre)

            # Convertir blob a base64 con JavaScript
            self.logger.info("🔄 Convirtiendo blob a base64 con JavaScript…")
            try:
                js = f"""
                    async () => {{
                        const response = await fetch('{pdf_url}');
                        if (!response.ok) throw new Error(`HTTP error! status: ${{response.status}}`);
                        const blob = await response.blob();
                        return new Promise((resolve, reject) => {{
                            const reader = new FileReader();
                            reader.onloadend = () => resolve(reader.result);
                            reader.onerror = () => reject(reader.error);
                            reader.readAsDataURL(blob);
                        }});
                    }}
                """
                blob_data = await nuevo_popup.evaluate(js)

                if blob_data and blob_data.startswith('data:'):
                    _, data = blob_data.split(',', 1)
                    pdf_bytes = base64.b64decode(data)
                    with open(ruta, 'wb') as f:
                        f.write(pdf_bytes)
                    self.logger.info(f"✅ PDF guardado en: {ruta} ({len(pdf_bytes)} bytes)")
                    return True
                else:
                    self.logger.error(f"❌ Error en conversión blob: {blob_data}")
                    return False

            except Exception as e:
                self.logger.error(f"❌ Error en conversión blob: {e}")
                return False

            finally:
                await nuevo_popup.close()

        except Exception as e:
            self.logger.error(f"❌ Error general descargando PDF: {e}")
            return False

    async def process_prima_and_plan_selection(self) -> dict:
        """
        Proceso completo para extraer las 3 primas de Sura:
        1. Global Franquicia - Prima anual inicial que aparece por defecto
        2. Autos Global - Prima tras seleccionar '1 SMLMV' en ambos desplegables  
        3. Autos Clásico - Prima del plan clásico
        
        SIEMPRE calcula las 3 opciones, tanto para vehículos nuevos como usados.
        """
        self.logger.info("🔄 Procesando extracción de las 3 primas de Sura...")
        results = {
            'global_franquicia': None, 
            'autos_global': None, 
            'autos_clasico': None, 
            'success': False
        }
        
        try:
            # 1. Extraer prima "Global Franquicia" (la primera que aparece por defecto)
            self.logger.info("📊 Extrayendo prima 'Global Franquicia' (prima anual inicial)...")
            prima_global_franquicia = await self.extract_prima_anual_value(max_wait_seconds=20)
            if prima_global_franquicia is None:
                self.logger.error("❌ No se pudo extraer la prima 'Global Franquicia'")
                return results
            results['global_franquicia'] = prima_global_franquicia
            self.logger.info(f"✅ Prima Global Franquicia: ${prima_global_franquicia:,.0f}")
            
            # 2. Seleccionar '1 SMLMV' en ambos desplegables y extraer prima "Autos Global"
            self.logger.info("🔽 Seleccionando '1 SMLMV' para obtener prima 'Autos Global'...")
            if not await self.select_10_1_smlmv_in_dropdowns():
                self.logger.error("❌ No se pudo seleccionar '1 SMLMV' en los desplegables")
                return results
                
            # Esperar y extraer prima "Autos Global" tras los cambios de desplegables
            self.logger.info("📊 Extrayendo prima 'Autos Global' tras seleccionar 1 SMLMV...")
            prima_autos_global = await self.extract_prima_anual_value(max_wait_seconds=20)
            results['autos_global'] = prima_autos_global
            if prima_autos_global:
                self.logger.info(f"✅ Prima Autos Global: ${prima_autos_global:,.0f}")
            else:
                self.logger.warning("⚠️ No se pudo extraer prima 'Autos Global'")
            
            # 3. Cambiar a Plan Autos Clásico y extraer prima "Autos Clásico"
            self.logger.info("🎯 Cambiando a Plan Autos Clásico...")
            if not await self.click_plan_autos_clasico():
                self.logger.error("❌ No se pudo seleccionar Plan Autos Clásico")
                return results
                
            # Manejar modales que pueden aparecer tras el cambio
            await self.check_and_handle_continuity_modal()
            await self.handle_optional_modal()
            
            # Extraer prima "Autos Clásico"
            self.logger.info("📊 Extrayendo prima 'Autos Clásico'...")
            prima_autos_clasico = await self.extract_prima_anual_value(max_wait_seconds=20)
            results['autos_clasico'] = prima_autos_clasico
            if prima_autos_clasico is None:
                self.logger.error("❌ No se pudo extraer la prima 'Autos Clásico'")
                return results
            self.logger.info(f"✅ Prima Autos Clásico: ${prima_autos_clasico:,.0f}")
            
            # Marcar como exitoso
            results['success'] = True
            
            # Log de resumen con las 3 primas
            self.logger.info("🎉 Las 3 primas de Sura extraídas exitosamente:")
            self.logger.info(f"   📈 Global Franquicia: ${prima_global_franquicia:,.0f}")
            autos_global_str = f"${prima_autos_global:,.0f}" if prima_autos_global else "N/A"
            self.logger.info(f"   📈 Autos Global: {autos_global_str}")
            self.logger.info(f"   📈 Autos Clásico: ${prima_autos_clasico:,.0f}")
            
            return results
            
        except Exception as e:
            self.logger.error(f"❌ Error procesando las 3 primas de Sura: {e}")
            return results

    async def complete_vehicle_information_filling(self) -> dict:
        """Proceso completo para llenar la información adicional del vehículo después del Fasecolda."""
        self.logger.info("📋 Completando información del vehículo...")
        results = {
            'global_franquicia': None, 
            'autos_global': None, 
            'autos_clasico': None, 
            'success': False
        }
        try:
            # Para usados, NO volver a llenar la placa (ya se hizo en el flujo especial)
            if ClientConfig.VEHICLE_STATE == 'Usado':
                vehicle_steps = [
                    (self._select_dropdown_option, ['service_type'], "tipo de servicio"),
                    (self.select_limite_3040, [], "límite 3.040.000.000"),  # Paso adicional ANTES de ciudad
                    (self.fill_city, [], "ciudad"),
                    (self.fill_valor_asegurado, [], "valor asegurado"),  # Nuevo paso
                    # No fill_plate ni select_zero_kilometers aquí
                    (self.trigger_quote_calculation, [], "cálculo de cotización")
                ]
            else:
                vehicle_steps = [
                    (self._select_dropdown_option, ['service_type'], "tipo de servicio"),
                    (self.fill_city, [], "ciudad"),
                    (self.fill_valor_asegurado, [], "valor asegurado"),  # Nuevo paso
                    (self.fill_plate, [], "placa"),
                    (self.select_zero_kilometers, [], "cero kilómetros"),
                    (self.select_limite_3040, [], "límite 3.040.000.000"),  # Paso adicional DESPUÉS de cero kilómetros
                    (self.trigger_quote_calculation, [], "cálculo de cotización")
                ]
            for step_func, step_args, step_desc in vehicle_steps:
                if not await step_func(*step_args):
                    self.logger.warning(f"⚠️ No se pudo completar: {step_desc}")
                    return results
            # Procesar extracción de primas
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
        """Proceso completo de obtención y llenado de códigos Fasecolda, información del vehículo y descarga de cotización."""
        self.logger.info("🔍 Procesando llenado de código Fasecolda, información del vehículo y descarga...")
        results = {
            'global_franquicia': None, 
            'autos_global': None, 
            'autos_clasico': None, 
            'success': False, 
            'pdf_downloaded': False
        }
        try:
            if ClientConfig.VEHICLE_STATE == 'Usado':
                self.logger.info("🚗 Vehículo USADO: solo se ingresa placa y lupa, sin fasecolda/modelo/clase...")
                if not await self.process_used_vehicle_plate():
                    self.logger.error("❌ No se pudo completar el flujo de placa usada")
                    return results
            else:
                # Obtener y llenar códigos Fasecolda (solo para vehículos nuevos)
                codes = await self.get_fasecolda_code()
                if codes:
                    if not await self.fill_fasecolda_with_retry(codes):
                        self.logger.warning("⚠️ No se pudieron llenar los códigos Fasecolda")
                        return results
                else:
                    self.logger.info("⏭️ No se obtuvieron códigos Fasecolda (vehículo usado o búsqueda deshabilitada)")
            # Completar información del vehículo y extraer primas
            results = await self.complete_vehicle_information_filling()
            if results['success']:
                self.logger.info("✅ Extracción de primas completada, procediendo con cotización final...")
                # Completar cotización y descargar PDF
                if await self.complete_quote_and_download():
                    results['pdf_downloaded'] = True
                    self.logger.info("🎉 Proceso completo finalizado exitosamente con descarga de PDF")
                else:
                    self.logger.warning("⚠️ Extracción de primas exitosa pero problemas con descarga de PDF")
            else:
                self.logger.warning("⚠️ Hubo problemas en el proceso completo")
            return results
        except Exception as e:
            self.logger.error(f"❌ Error procesando llenado de Fasecolda: {e}")
            return results

    async def complete_quote_and_download(self) -> bool:
        """Proceso completo para finalizar cotización y descargar PDF."""
        self.logger.info("🎯 Completando cotización y descarga de PDF...")
        
        try:
            # Lista de pasos para completar la cotización
            final_steps = [
                (self.click_plan_autos_global, [], "regresar a Plan Autos Global"),
                (lambda: self.page.wait_for_timeout(3000), [], "esperar carga del Plan Global"),
                (self.select_limite_3040, [], "límite 3.040.000.000"),  # Paso adicional ANTES de ver cotización
                (self.click_ver_cotizacion, [], "hacer clic en 'Ver cotización'"),
                (self.activate_menu_toggle, [], "activar menú flotante"),
                (self.download_pdf_quote, [], "descargar PDF")
            ]
            
            for step_func, step_args, step_desc in final_steps:
                if asyncio.iscoroutinefunction(step_func):
                    if not await step_func(*step_args):
                        self.logger.error(f"❌ No se pudo {step_desc}")
                        return False
                else:
                    await step_func(*step_args)
                
                # Manejar modales después de pasos específicos
                if step_desc in ["regresar a Plan Autos Global", "límite 3.040.000.000", "hacer clic en 'Ver cotización'"]:
                    await self.check_and_handle_continuity_modal()
                    await self.handle_optional_modal()
            
            self.logger.info("🎉 Proceso de cotización y descarga completado exitosamente")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error completando cotización y descarga: {e}")
            return False
