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
from ....shared.utils import Utils

class FasecoldaPage(BasePage):
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
            'service_type': "#tipoServicio"
        },
        'form_fields': {
            'city': "input[aria-label='Ciudad']",
            'plate': "#placa input",
            'zero_km_radio': "paper-radio-button[title='opcion-Si']"
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
        'model_year_template': "paper-item:has-text('{year}')"
    }

    def __init__(self, page: Page):
        super().__init__(page, 'sura')
        self.config = SuraConfig()

    async def get_fasecolda_code(self) -> Optional[dict]:
        """Obtiene los códigos Fasecolda usando FasecoldaService en una nueva pestaña."""
        self.logger.info("🔍 Obteniendo códigos Fasecolda...")
        
        try:
            # Verificar configuración
            auto_fetch = ClientConfig.get_company_specific_config('sura').get('auto_fetch_fasecolda', True)
            if not auto_fetch:
                self.logger.info("⏭️ Búsqueda automática de Fasecolda deshabilitada")
                return None
            
            if ClientConfig.VEHICLE_STATE != 'Nuevo':
                self.logger.info(f"⏭️ Vehículo '{ClientConfig.VEHICLE_STATE}' - no requiere código Fasecolda")
                return None
            
            # Crear nueva pestaña para Fasecolda
            self.logger.info("🌐 Abriendo nueva pestaña para Fasecolda...")
            new_page = await self.page.context.new_page()
            
            try:
                fasecolda_service = FasecoldaService(new_page, self.logger)
                codes = await fasecolda_service.get_cf_code(
                    category=ClientConfig.VEHICLE_CATEGORY,
                    state=ClientConfig.VEHICLE_STATE,
                    model_year=ClientConfig.VEHICLE_MODEL_YEAR,
                    brand=ClientConfig.VEHICLE_BRAND,
                    reference=ClientConfig.VEHICLE_REFERENCE,
                    full_reference=ClientConfig.VEHICLE_FULL_REFERENCE
                )
                
                if codes and codes.get('cf_code'):
                    ch_info = f" - CH: {codes.get('ch_code')}" if codes.get('ch_code') else ""
                    self.logger.info(f"✅ Códigos Fasecolda obtenidos - CF: {codes['cf_code']}{ch_info}")
                    return codes
                else:
                    self.logger.warning("⚠️ No se pudieron obtener códigos Fasecolda")
                    return None
                    
            finally:
                await new_page.close()
                self.logger.info("🗂️ Pestaña de Fasecolda cerrada")
                
        except Exception as e:
            self.logger.error(f"❌ Error obteniendo códigos Fasecolda: {e}")
            return None

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
        """Llena el campo de ciudad y selecciona la opción de Medellín."""
        self.logger.info(f"🏙️ Llenando ciudad: {ClientConfig.get_client_city('sura')}...")
        
        try:
            # Llenar y seleccionar ciudad usando método reutilizable
            await self.page.fill(self.SELECTORS['form_fields']['city'], ClientConfig.get_client_city('sura'))
            await self.page.wait_for_timeout(1500)
            
            if not await self.safe_click(self.OPTIONS['city'], timeout=5000):
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
            return True
        except Exception as e:
            self.logger.error(f"❌ Error activando cálculo de cotización: {e}")
            return False

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
                            # Extraer solo los números del texto
                            import re
                            numbers = re.sub(r'[^\d]', '', text_content)
                            if numbers:
                                value = float(numbers)
                                self.logger.info(f"✅ Prima anual extraída: ${value:,.0f} (texto original: '{text_content.strip()}')")
                                return value
                    
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

    async def click_ver_cotizacion(self) -> bool:
        """Hace clic en el botón 'Ver cotización'."""
        self.logger.info("🎯 Haciendo clic en 'Ver cotización'...")
        
        try:
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

    async def download_pdf_quote(self) -> bool:
        """Descarga el PDF de la cotización usando conversión blob → base64."""
        self.logger.info("📄 Iniciando descarga de PDF...")

        try:
            # Esperar por nueva pestaña y hacer clic en PDF
            self.logger.info("🌐 Detectando nueva pestaña con el PDF...")
            async with self.page.context.expect_page() as new_page_info:
                if not await self.safe_click(self.SELECTORS['actions']['pdf_download'], timeout=10000):
                    self.logger.error("❌ No se pudo hacer clic en el botón de descarga PDF")
                    return False
                self.logger.info("✅ Clic en botón PDF exitoso")

            nuevo_popup = await new_page_info.value
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
        """Proceso completo para extraer prima inicial, seleccionar plan clásico y extraer segunda prima."""
        self.logger.info("🔄 Procesando extracción de primas y selección de plan...")
        
        results = {'prima_global': None, 'prima_clasico': None, 'success': False}
        
        try:
            # 1. Extraer prima del Plan Global
            self.logger.info("📊 Extrayendo prima del Plan Global...")
            prima_global = await self.extract_prima_anual_value(max_wait_seconds=20)
            
            if prima_global is None:
                self.logger.error("❌ No se pudo extraer la prima del Plan Global")
                return results
            
            results['prima_global'] = prima_global
            self.logger.info(f"✅ Prima Plan Global: ${prima_global:,.0f}")
            
            # 2. Cambiar a Plan Autos Clásico
            self.logger.info("🎯 Cambiando a Plan Autos Clásico...")
            if not await self.click_plan_autos_clasico():
                self.logger.error("❌ No se pudo seleccionar Plan Autos Clásico")
                return results
            
            # 3. Manejar modales
            await self.check_and_handle_continuity_modal()
            await self.handle_optional_modal()
            
            # 4. Extraer prima del Plan Clásico
            self.logger.info("📊 Extrayendo prima del Plan Autos Clásico...")
            prima_clasico = await self.extract_prima_anual_value(max_wait_seconds=20)
            
            if prima_clasico is None:
                self.logger.error("❌ No se pudo extraer la prima del Plan Autos Clásico")
                return results
            
            results['prima_clasico'] = prima_clasico
            results['success'] = True
            
            self.logger.info(f"✅ Prima Plan Autos Clásico: ${prima_clasico:,.0f}")
            
            # Validación
            if prima_global == prima_clasico:
                self.logger.warning(f"⚠️ Ambas primas tienen el mismo valor (${prima_global:,.0f}). Verificar cambio de plan.")
            else:
                self.logger.info(f"✅ Primas diferentes - Global: ${prima_global:,.0f}, Clásico: ${prima_clasico:,.0f}")
            
            self.logger.info("🎉 Proceso de extracción de primas completado exitosamente")
            return results
            
        except Exception as e:
            self.logger.error(f"❌ Error procesando primas y selección de plan: {e}")
            return results

    async def complete_vehicle_information_filling(self) -> dict:
        """Proceso completo para llenar la información adicional del vehículo después del Fasecolda."""
        self.logger.info("📋 Completando información del vehículo...")
        
        results = {'prima_global': None, 'prima_clasico': None, 'success': False}
        
        try:
            # Llenar información del vehículo usando método de clase base
            vehicle_steps = [
                (self._select_dropdown_option, ['service_type'], "tipo de servicio"),
                (self.fill_city, [], "ciudad"),
                (self.fill_plate, [], "placa"),
                (self.select_zero_kilometers, [], "cero kilómetros"),
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
        
        results = {'prima_global': None, 'prima_clasico': None, 'success': False, 'pdf_downloaded': False}
        
        try:
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
                if step_desc in ["regresar a Plan Autos Global", "hacer clic en 'Ver cotización'"]:
                    await self.check_and_handle_continuity_modal()
                    await self.handle_optional_modal()
            
            self.logger.info("🎉 Proceso de cotización y descarga completado exitosamente")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error completando cotización y descarga: {e}")
            return False
