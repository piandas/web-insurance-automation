"""Página de placa específica para Allianz."""

import datetime
import os
from playwright.async_api import Page
from ....shared.base_page import BasePage
from ....shared.utils import Utils
from ....config.allianz_config import AllianzConfig
from ....config.client_config import ClientConfig
from .fasecolda_page import FasecoldaPage

class PlacaPage(BasePage):
    # Selector para el input de valor asegurado en el iframe
    SELECTOR_INPUT_VALOR_ASEGURADO = 'input[name="DatosVehiculoIndividualBean$valorAsegurado"]'
    async def _get_input_value_by_id(self, frame, input_id):
        """Obtiene el valor de un input por su id dentro del frame dado."""
        try:
            input_elem = await frame.query_selector(f'input#{input_id}')
            if input_elem:
                return await input_elem.get_attribute('value')
        except Exception as e:
            self.logger.warning(f"No se pudo extraer el valor de {input_id}: {e}")
        return ''
    """Página para manejo de placa y comprobación en Allianz."""
    
    # Selectores
    SELECTOR_INPUT_PLACA = "#DatosVehiculoIndividualBean\\$matricula"
    SELECTOR_BTN_COMPROBAR = "#btnPlaca"
    SELECTOR_INPUT_PLACA_IN_IFRAME = 'input[name="DatosVehiculoIndividualBean$matricula"]'
    SELECTOR_CAMPO_VERIFICACION_IN_IFRAME = 'input[name="_CVH_VehicuCol$codigoClaveVeh"]'
    
    # Selectores para vehículos nuevos (código FASECOLDA)
    SELECTOR_CODIGO_FASECOLDA = "#_CVH_VehicuCol\\$codigoClaveVeh"
    SELECTOR_BTN_BUSCAR_VEHICULO = "#_CVH_VehicuCol\\$codigoClaveVeh_AjaxVehFinderImg"
    SELECTOR_VEHICULO_0KMS = "#DatosVehiculoIndividualBean\\$vehNuevo"
    SELECTOR_ANO_MODELO = "#VehicuCol\\$annoModelo"
    
    # Selectores para datos del asegurado
    SELECTOR_FECHA_NACIMIENTO = "#DatosAseguradoAutosBean\\$fechaNacimiento"
    SELECTOR_GENERO = "#DatosAseguradoAutosBean\\$idSexo"
    
    # Selectores para buscador de poblaciones
    SELECTOR_DEPARTAMENTO = "#idCity_1_node1"
    SELECTOR_BTN_BUSCAR_CIUDAD = "#idCity_1_node2AjaxFinderImg"
    SELECTOR_INPUT_CIUDAD = "#idCity_1_node2"
    SELECTOR_CODIGO_CIUDAD = "#idFinderCod"
    SELECTOR_LISTA_CIUDADES = "#div_loc_idCity_1"
    
    # Selectores para consulta y finalización
    SELECTOR_BTN_CONSULTAR_DTO = "#consultaWsBtn"
    SELECTOR_POLIZA_ANTECEDENTES = 'input[name="AntecedentesBean$poliza"]'
    SELECTOR_BTN_ACEPTAR = "#btnAceptar"
    SELECTOR_BTN_ARCHIVAR = "#btnArchivar"
    SELECTOR_BTN_ARCHIVAR_SEGUNDO = "#o_2"
    SELECTOR_ESTUDIO_SEGURO = "#doc0"

    def __init__(self, page: Page):
        super().__init__(page, 'allianz')
        self.config = AllianzConfig()
        self.fasecolda_page = FasecoldaPage(page)

    async def esperar_y_llenar_placa(self, placa: str = None) -> bool:
        """Espera el input de placa y lo llena."""
        # Usar el valor del config si no se proporciona uno específico
        if placa is None:
            placa = ClientConfig.VEHICLE_PLATE
            
        self.logger.info(f"📝 Esperando y llenando input de placa con '{placa}'...")
        return await self.fill_in_frame(
            self.SELECTOR_INPUT_PLACA,
            placa,
            "input de placa"
        )

    async def verificar_input_ready(self) -> bool:
        """Verifica que el input de placa esté listo y tenga el método getValue."""
        return await self.verify_element_value_in_frame(
            self.SELECTOR_INPUT_PLACA_IN_IFRAME,
            "input listo",
            condition="has_method_getValue",
            attempts=5,
            interval_ms=1000,
            immediate_check=False
        )

    async def click_comprobar_placa(self) -> bool:
        """Hace clic en el botón 'Comprobar' usando click_in_frame."""
        self.logger.info("🖱️ Haciendo clic en botón 'Comprobar'...")
        if not await self.verificar_input_ready():
            return False
        if not await self.click_in_frame(self.SELECTOR_BTN_COMPROBAR, "botón 'Comprobar'"):
            return False
        # Pausa breve para que se procese
        await self.page.wait_for_timeout(2000)
        return True

    async def verificar_campo_lleno(self) -> bool:
        """Verifica que el campo de verificación no esté vacío, esperando hasta 10s."""
        return await self.verify_element_value_in_frame(
            self.SELECTOR_CAMPO_VERIFICACION_IN_IFRAME,
            "campo de verificación",
            condition="value_not_empty",
            attempts=20,
            interval_ms=1000,
            immediate_check=True
        )
    
    async def llenar_datos_asegurado(self, fecha_nacimiento: str = None, genero: str = None) -> bool:
        """
        Llena los datos del asegurado: fecha de nacimiento y género.
        
        Args:
            fecha_nacimiento (str): Fecha en formato dd/mm/yyyy (default: valor de Config)
            genero (str): Género - M (Masculino), F (Femenino), J (Jurídico) (default: valor de Config)
        
        Returns:
            bool: True si se llenaron los datos correctamente, False en caso contrario
        """
        # Usar valores del config si no se proporcionan específicos
        if fecha_nacimiento is None:
            fecha_nacimiento = ClientConfig.get_client_birth_date('allianz')
        if genero is None:
            genero = ClientConfig.CLIENT_GENDER
        
        # Limpiar fecha de nacimiento usando Utils
        fecha_limpia = Utils.clean_date(fecha_nacimiento)
            
        self.logger.info(f"👤 Llenando datos del asegurado - Fecha: {fecha_limpia}, Género: {genero}")
        
        try:
            # Llenar fecha de nacimiento
            if not await self.fill_in_frame(
                self.SELECTOR_FECHA_NACIMIENTO,
                fecha_limpia,
                "fecha de nacimiento"
            ):
                self.logger.error("❌ Error al llenar fecha de nacimiento")
                return False
            
            # Seleccionar género
            if not await self.select_in_frame(
                self.SELECTOR_GENERO,
                genero,
                "género"
            ):
                self.logger.error("❌ Error al seleccionar género")
                return False
            
            #self.logger.info("✅ Datos del asegurado llenados correctamente")
            # Llenar el campo valor asegurado recibido (siempre, nuevo o usado)
            #valor_asegurado = ClientConfig.VEHICLE_INSURED_VALUE_RECEIVED
            #self.logger.info(f"💵 Llenando campo valor asegurado con '{valor_asegurado}'")
            #if not await self.fill_in_frame(
            #    self.SELECTOR_INPUT_VALOR_ASEGURADO,
            #    valor_asegurado,
            #    "valor asegurado"
            #):
            #    self.logger.error("❌ Error al llenar campo valor asegurado")
            #    return False
            #return True
            
        except Exception as e:
            self.logger.error(f"❌ Error al llenar datos del asegurado: {e}")
            return False

    async def buscador_poblaciones(self, departamento: str = None, ciudad: str = None) -> bool:
        """
        Busca y selecciona una población específica.
        
        Args:
            departamento (str): Nombre del departamento (default: valor de Config)
            ciudad (str): Nombre de la ciudad (default: valor de Config)
        
        Returns:
            bool: True si se seleccionó la población correctamente, False en caso contrario
        """
        # Usar valores del config si no se proporcionan específicos
        if departamento is None:
            departamento = ClientConfig.CLIENT_DEPARTMENT
        if ciudad is None:
            ciudad = ClientConfig.get_client_city('allianz')
            
        self.logger.info(f"🏙️ Buscando población - Departamento: {departamento}, Ciudad: {ciudad}")
        
        try:
            # Paso 1: Seleccionar departamento por texto
            if not await self.select_by_text_in_frame(
                self.SELECTOR_DEPARTAMENTO,
                departamento,
                f"departamento ({departamento})"
            ):
                self.logger.error("❌ Error al seleccionar departamento")
                return False
            
            # Pausa breve para que se procese la selección
            await self.page.wait_for_timeout(1000)
            
            # Paso 2: Hacer clic en el botón de búsqueda
            if not await self.click_in_frame(
                self.SELECTOR_BTN_BUSCAR_CIUDAD,
                "botón de búsqueda de ciudad"
            ):
                self.logger.error("❌ Error al hacer clic en botón de búsqueda")
                return False
            
            # Paso 3: Llenar el campo de ciudad
            if not await self.fill_in_frame(
                self.SELECTOR_INPUT_CIUDAD,
                ciudad,
                f"campo de ciudad ({ciudad})"
            ):
                self.logger.error("❌ Error al llenar campo de ciudad")
                return False
            
            # Pausa para que aparezca la lista
            await self.page.wait_for_timeout(2000)
              
            # Paso 4: Buscar y hacer clic en la ciudad en la lista desplegable
            if not await self.click_by_text_in_frame(
                ciudad,
                f"ciudad '{ciudad}' en la lista"
            ):
                self.logger.error(f"❌ No se pudo encontrar la ciudad '{ciudad}' en la lista")
                return False
            
            # Pausa para que se procese la selección
            await self.page.wait_for_timeout(2000)
            
            # Paso 5: Verificar que se llenó el código de ciudad
            codigo_resultado = await self.verify_element_value_in_frame(
                self.SELECTOR_CODIGO_CIUDAD,
                "código de ciudad",
                condition="value_not_empty",
                attempts=5,
                interval_ms=1000,
                immediate_check=False
            )
            
            if codigo_resultado:
                self.logger.info(f"✅ Población seleccionada correctamente")
                return True
            else:
                self.logger.error("❌ No se encontró código de ciudad después de la selección")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error en buscador de poblaciones: {e}")
            return False

    async def consultar_y_finalizar(self) -> bool:
        """
        Ejecuta la secuencia de consulta DTO y finalización del proceso.
        
        Returns:
            bool: True si se ejecutó la secuencia correctamente, False en caso contrario
        """
        self.logger.info("📋 Iniciando consulta DTO y finalización...")
        
        try:
            # Paso 1: Hacer clic en "Consultar Dto"
            if not await self.click_in_frame(
                self.SELECTOR_BTN_CONSULTAR_DTO,
                "botón 'Consultar Dto'"
            ):
                self.logger.error("❌ Error al hacer clic en 'Consultar Dto'")
                return False
            
            # Pausa para que se procese la consulta
            await self.page.wait_for_timeout(3000)
            
            # Paso 2: Verificar que el campo de póliza tenga valor
            if not await self.verify_element_value_in_frame(
                self.SELECTOR_POLIZA_ANTECEDENTES,
                "campo de póliza antecedentes",
                condition="value_not_empty",
                attempts=10,
                interval_ms=1000,
                immediate_check=False
            ):
                self.logger.error("❌ El campo de póliza no se llenó después de la consulta")
                return False
            
            # Paso 3: Clic en "Siguiente" (solo una vez si es vehículo nuevo)
            from ....config.client_config import ClientConfig
            if ClientConfig.VEHICLE_STATE.lower() == 'nuevo':
                if not await self.click_in_frame(
                    self.SELECTOR_BTN_ACEPTAR,
                    "botón 'Siguiente' (único clic para nuevo)"
                ):
                    self.logger.error("❌ Error al hacer clic en 'Siguiente' (vehículo nuevo)")
                    return False
                # Pausa para que aparezca el botón Archivar
                await self.page.wait_for_timeout(3000)
                await self.wait_for_iframe_content()
            else:
                # Primer clic en Siguiente
                if not await self.click_in_frame(
                    self.SELECTOR_BTN_ACEPTAR,
                    "botón 'Siguiente' (primera vez)"
                ):
                    self.logger.error("❌ Error al hacer clic en primer 'Siguiente'")
                    return False
                await self.page.wait_for_timeout(3000)
                await self.wait_for_iframe_content()
                # Segundo clic en Siguiente
                if not await self.click_in_frame(
                    self.SELECTOR_BTN_ACEPTAR,
                    "botón 'Siguiente' (segunda vez)"
                ):
                    self.logger.error("❌ Error al hacer clic en segundo 'Siguiente'")
                    return False
                await self.page.wait_for_timeout(3000)
                await self.wait_for_iframe_content()
            
            # Paso 5: Verificar que aparezca el botón "Archivar"
            if not await self.verify_element_value_in_frame(
                self.SELECTOR_BTN_ARCHIVAR,
                "botón 'Archivar'",
                condition="is_visible",
                attempts=10,
                interval_ms=1000,
                immediate_check=False
            ):
                self.logger.error("❌ El botón 'Archivar' no apareció")
                return False
            
            # Paso 6: Hacer clic en el primer botón "Archivar"
            if not await self.click_in_frame(
                self.SELECTOR_BTN_ARCHIVAR,
                "primer botón 'Archivar'"
            ):
                self.logger.error("❌ Error al hacer clic en primer botón 'Archivar'")
                return False
            
            # Pausa para que aparezca el segundo botón
            await self.page.wait_for_timeout(3000)
            
            # Paso 7: Esperar y hacer clic en el segundo botón "Archivar"
            if not await self.verify_element_value_in_frame(
                self.SELECTOR_BTN_ARCHIVAR_SEGUNDO,
                "segundo botón 'Archivar'",
                condition="is_visible",
                attempts=10,
                interval_ms=1000,
                immediate_check=False
            ):
                self.logger.error("❌ El segundo botón 'Archivar' no apareció")
                return False
            
            if not await self.click_in_frame(
                self.SELECTOR_BTN_ARCHIVAR_SEGUNDO,
                "segundo botón 'Archivar'"
            ):
                self.logger.error("❌ Error al hacer clic en segundo botón 'Archivar'")
                return False
            
            # Paso 8: Manejar alert de confirmación
            try:
                await self.page.wait_for_timeout(2000)  # Esperar que aparezca el alert
                # Aceptar el alert automáticamente
                await self.page.on("dialog", lambda dialog: dialog.accept())
                self.logger.info("✅ Alert de confirmación aceptado")
            except Exception as e:
                self.logger.warning(f"⚠️ No se detectó alert o ya fue manejado: {e}")
            
            # Paso 9: EXTRAER VALORES DE LA PÁGINA (antes de abrir el PDF)
            await self.page.wait_for_timeout(3000)
            try:
                frame = self.page.frame(name="appArea")
                # 1. Número de cotización
                cotiz_td = await frame.query_selector('td.rowAppErrorInfoTextBlock.cellNoImage')
                cotiz_text = await cotiz_td.inner_text() if cotiz_td else ''
                num_cotizacion = ''
                import re
                m = re.search(r'número (\d+)', cotiz_text)
                if m:
                    num_cotizacion = m.group(1)
                self.logger.info(f"[EXTRACCIÓN] Número de cotización: {num_cotizacion}")

                # 2. Autos Esencial (modalidad_1_0_primaRecibo)
                autos_esencial = await self._get_input_value_by_id(frame, "modalidad_1_0_primaRecibo")
                self.logger.info(f"[EXTRACCIÓN] Autos Esencial: {autos_esencial}")

                # 3. Autos Plus (modalidad_2_0_primaRecibo)
                autos_plus = await self._get_input_value_by_id(frame, "modalidad_2_0_primaRecibo")
                self.logger.info(f"[EXTRACCIÓN] Autos Plus: {autos_plus}")

                # 4. Autos Llave en Mano (modalidad_3_0_primaRecibo)
                autos_llave = await self._get_input_value_by_id(frame, "modalidad_3_0_primaRecibo")
                self.logger.info(f"[EXTRACCIÓN] Autos Llave en Mano: {autos_llave}")

                # Si necesitas el valor de "Autos Esencial + Totales", puedes agregar lógica similar aquí si hay un campo específico
            except Exception as e:
                self.logger.error(f"❌ Error extrayendo valores de la página: {e}")
            # Paso 10: Esperar y hacer clic en "Estudio de Seguro"
            if not await self.verify_element_value_in_frame(
                self.SELECTOR_ESTUDIO_SEGURO,
                "enlace 'Estudio de Seguro'",
                condition="is_visible",
                attempts=15,
                interval_ms=1000,
                immediate_check=False
            ):
                self.logger.error("❌ El enlace 'Estudio de Seguro' no apareció")
                return False
            if not await self.click_in_frame(
                self.SELECTOR_ESTUDIO_SEGURO,
                "enlace 'Estudio de Seguro'"
            ):
                self.logger.error("❌ Error al hacer clic en 'Estudio de Seguro'")
                return False
            
            # Paso 10: Descargar PDF directamente desde la URL
            self.logger.info("🌐 Detectando nueva pestaña con el PDF...")
            nuevo_popup = await self.page.context.wait_for_event("page")
            await nuevo_popup.wait_for_load_state("networkidle")

            pdf_url = nuevo_popup.url
            self.logger.info(f"🔗 URL del PDF: {pdf_url}")

            # Descargar vía API de Playwright (más fiable que interactuar con el visor)
            response = await self.page.context.request.get(pdf_url)
            if not response.ok:
                self.logger.error(f"❌ Falló la descarga del PDF (status {response.status})")
                return False

            # Generar nombre de archivo usando Utils
            nombre = Utils.generate_filename('allianz', 'Cotizacion')
            
            # Usar el directorio de descargas específico de Allianz
            downloads_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))), 'downloads', 'allianz')
            Utils.ensure_directory(downloads_dir)
            
            ruta = os.path.join(downloads_dir, nombre)
            with open(ruta, "wb") as f:
                f.write(await response.body())
            self.logger.info(f"✅ PDF de Allianz guardado en {ruta}")

            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error en consulta y finalización de Allianz: {e}")
            return False
    
    # Métodos específicos para vehículos nuevos (código FASECOLDA)
    async def llenar_codigo_fasecolda(self) -> bool:
        """Llena el campo del código FASECOLDA dentro del iframe 'appArea'."""
        self.logger.info("📋 Obteniendo y llenando código FASECOLDA en iframe 'appArea'...")
        try:
            # Obtener códigos FASECOLDA del extractor global
            codes = await self.fasecolda_page.get_fasecolda_code()
            if not codes or not codes.get('cf_code'):
                self.logger.error("❌ No se pudo obtener código FASECOLDA")
                return False
            cf_code = codes['cf_code']
            self.logger.info(f"📝 Llenando código FASECOLDA: {cf_code}")

            # Seleccionar el iframe 'appArea' y llenar el campo
            for intento in range(1, 6):
                try:
                    frame = self.page.frame(name="appArea")
                    if not frame:
                        self.logger.warning(f"⚠️ No se encontró el iframe 'appArea' (intento {intento})")
                        await self.page.wait_for_timeout(1000)
                        continue
                    await frame.fill(self.SELECTOR_CODIGO_FASECOLDA, cf_code)
                    # Verificar que el campo se llenó correctamente
                    valor = await frame.input_value(self.SELECTOR_CODIGO_FASECOLDA)
                    if valor == cf_code:
                        self.logger.info("✅ Código FASECOLDA llenado correctamente en el iframe")
                        return True
                    else:
                        self.logger.warning(f"⚠️ El campo no se llenó correctamente (intento {intento})")
                        await self.page.wait_for_timeout(1000)
                except Exception as e:
                    self.logger.warning(f"⚠️ Error llenando el campo en el iframe (intento {intento}): {e}")
                    await self.page.wait_for_timeout(1000)
            self.logger.error("❌ No se pudo llenar el campo Código FASECOLDA en el iframe después de varios intentos")
            return False
        except Exception as e:
            self.logger.error(f"❌ Error llenando código FASECOLDA: {e}")
            return False
    
    async def click_buscar_vehiculo(self) -> bool:
        """Hace clic en la lupa (botón buscar vehículo) dentro del iframe 'appArea' hasta que el select de marca tenga opciones. Luego llena la placa con 'XXX123' si es vehículo nuevo."""
        self.logger.info("🔍 Haciendo clic en buscar vehículo (lupa) en el iframe 'appArea' hasta que aparezca marca...")
        try:
            for intento in range(1, 11):
                frame = self.page.frame(name="appArea")
                if not frame:
                    self.logger.warning(f"⚠️ No se encontró el iframe 'appArea' (intento {intento})")
                    await self.page.wait_for_timeout(1000)
                    continue
                boton_lupa = await frame.query_selector('#_CVH_VehicuCol\\$codigoClaveVeh_AjaxVehFinderImg')
                if not boton_lupa:
                    self.logger.warning(f"[Depuración] No se encontró el botón lupa en el DOM del iframe (intento {intento})")
                    await self.page.wait_for_timeout(1000)
                    continue
                is_visible = await boton_lupa.is_visible()
                is_enabled = await boton_lupa.is_enabled()
                self.logger.info(f"[Depuración] Estado del botón lupa: visible={is_visible}, enabled={is_enabled}")
                try:
                    await boton_lupa.click()
                    self.logger.info(f"[Depuración] Click en la lupa ejecutado (intento {intento})")
                except Exception as click_error:
                    self.logger.error(f"[Depuración] Error al hacer click en la lupa: {click_error}")
                    await self.page.wait_for_timeout(1000)
                    continue
                await self.page.wait_for_timeout(800)
                # Verificar si el select de marca tiene opciones válidas
                select_marca = await frame.query_selector('select#_M_VehicuCol\\$marca')
                if select_marca:
                    options = await select_marca.query_selector_all('option')
                    opciones_validas = [await o.get_attribute('value') for o in options if (await o.get_attribute('value')) and (await o.get_attribute('value')).strip()]
                    if len(opciones_validas) > 0:
                        self.logger.info(f"✅ ¡Marca disponible tras {intento} clic(s)! Opciones: {opciones_validas[:5]}...")
                        # Si el vehículo es nuevo, llenar la placa con 'XXX123' en el mismo iframe
                        from ....config.client_config import ClientConfig
                        if ClientConfig.VEHICLE_STATE.lower() == 'nuevo':
                            try:
                                await frame.fill(self.SELECTOR_INPUT_PLACA, 'XXX123')
                                self.logger.info("✅ Placa genérica 'XXX123' llenada correctamente en el iframe tras la lupa")
                            except Exception as e:
                                self.logger.warning(f"⚠️ No se pudo llenar la placa genérica en el iframe: {e}")
                        return True
                self.logger.info(f"[Depuración] Marca aún no disponible tras {intento} clic(s)")
            self.logger.error("❌ No se pudo obtener la marca tras 10 clics en la lupa. El campo marca sigue vacío o sin opciones válidas.")
            return False
        except Exception as e:
            self.logger.error(f"❌ Error haciendo clic en buscar vehículo: {e}")
            return False
    
    async def seleccionar_vehiculo_0kms(self) -> bool:
        """Selecciona la opción 'Sí' de vehículo 0kms dentro del iframe 'appArea'."""
        self.logger.info("🆕 Seleccionando vehículo 0kms (Sí) en el iframe 'appArea'...")
        try:
            await self.page.wait_for_timeout(2000)
            for intento in range(1, 6):
                try:
                    frame = self.page.frame(name="appArea")
                    if not frame:
                        self.logger.warning(f"⚠️ No se encontró el iframe 'appArea' (intento {intento})")
                        await self.page.wait_for_timeout(1000)
                        continue
                    await frame.click('input#DatosVehiculoIndividualBean\\$vehNuevo[value="true"]')
                    self.logger.info("✅ Opción 'Sí' de 0kms seleccionada correctamente en el iframe")
                    return True
                except Exception as e:
                    self.logger.warning(f"⚠️ Error seleccionando 0kms en el iframe (intento {intento}): {e}")
                    await self.page.wait_for_timeout(1000)
            self.logger.error("❌ No se pudo seleccionar 0kms en el iframe después de varios intentos")
            return False
        except Exception as e:
            self.logger.error(f"❌ Error seleccionando vehículo 0kms: {e}")
            return False
    
    async def llenar_ano_modelo(self) -> bool:
        """Llena el año del modelo del vehículo dentro del iframe 'appArea'."""
        ano_modelo = ClientConfig.VEHICLE_MODEL_YEAR
        self.logger.info(f"📅 Llenando año del modelo: {ano_modelo}")
        for intento in range(1, 6):
            self.logger.info(f"📝 Año del modelo - Intento {intento}/5")
            try:
                frame = self.page.frame(name="appArea")
                if not frame:
                    self.logger.warning(f"⚠️ No se encontró el iframe 'appArea' (intento {intento})")
                    await self.page.wait_for_timeout(1000)
                    continue
                await frame.fill(self.SELECTOR_ANO_MODELO, ano_modelo)
                valor = await frame.input_value(self.SELECTOR_ANO_MODELO)
                if valor == ano_modelo:
                    self.logger.info("✅ Año del modelo llenado correctamente en el iframe")
                    return True
                else:
                    self.logger.warning(f"⚠️ El campo año modelo no se llenó correctamente (intento {intento})")
                    await self.page.wait_for_timeout(1000)
            except Exception as e:
                self.logger.warning(f"⚠️ Año del modelo - Error en intento {intento}: {e}")
                await self.page.wait_for_timeout(2000)
        self.logger.error("❌ No se pudo llenar el año del modelo en el iframe después de 5 intentos")
        return False
        
    async def execute_placa_flow(self, placa: str = None, fecha_nacimiento: str = None, genero: str = None, departamento: str = None, ciudad: str = None) -> bool:
        """Ejecuta el flujo completo desde placa hasta finalización en Allianz."""
        # Decidir qué flujo usar según el estado del vehículo
        if ClientConfig.VEHICLE_STATE == 'Nuevo':
            self.logger.info("🆕 Vehículo NUEVO detectado - usando flujo con código FASECOLDA")
            return await self.execute_vehiculo_nuevo_flow(fecha_nacimiento, genero, departamento, ciudad)
        else:
            self.logger.info("🔄 Vehículo USADO detectado - usando flujo tradicional con placa")
            return await self.execute_vehiculo_usado_flow(placa, fecha_nacimiento, genero, departamento, ciudad)
    
    async def execute_vehiculo_usado_flow(self, placa: str = None, fecha_nacimiento: str = None, genero: str = None, departamento: str = None, ciudad: str = None) -> bool:
        """Ejecuta el flujo para vehículos usados (flujo tradicional con placa)."""
        # Usar valores del config si no se proporcionan específicos
        if placa is None:
            placa = ClientConfig.VEHICLE_PLATE
        if fecha_nacimiento is None:
            fecha_nacimiento = ClientConfig.get_client_birth_date('allianz')
        if genero is None:
            genero = ClientConfig.CLIENT_GENDER
        if departamento is None:
            departamento = ClientConfig.CLIENT_DEPARTMENT
        if ciudad is None:
            ciudad = ClientConfig.get_client_city('allianz')
            
        self.logger.info(f"🚗 Iniciando flujo de vehículo USADO con placa '{placa}', ciudad '{ciudad}'...")
        steps = [
            self.esperar_y_llenar_placa,
            self.click_comprobar_placa,
            self.verificar_campo_lleno,
            self.llenar_datos_asegurado,
            self.buscador_poblaciones,
            self.consultar_y_finalizar
        ]
        try:
            for i, step in enumerate(steps, 1):
                self.logger.info(f"📋 Ejecutando paso {i}/{len(steps)}...")
                if not await step():
                    self.logger.error(f"❌ Falló el paso {i}")
                    return False
            self.logger.info("✅ ¡FLUJO DE VEHÍCULO USADO EXITOSO!")
            return True
        except Exception as e:
            self.logger.error(f"❌ Error en flujo de vehículo usado: {e}")
            return False
    
    async def execute_vehiculo_nuevo_flow(self, fecha_nacimiento: str = None, genero: str = None, departamento: str = None, ciudad: str = None) -> bool:
        """Ejecuta el flujo para vehículos nuevos (con código FASECOLDA)."""
        # Usar valores del config si no se proporcionan específicos
        if fecha_nacimiento is None:
            fecha_nacimiento = ClientConfig.get_client_birth_date('allianz')
        if genero is None:
            genero = ClientConfig.CLIENT_GENDER
        if departamento is None:
            departamento = ClientConfig.CLIENT_DEPARTMENT
        if ciudad is None:
            ciudad = ClientConfig.get_client_city('allianz')
            
        self.logger.info(f"🆕 Iniciando flujo de vehículo NUEVO con código FASECOLDA, ciudad '{ciudad}'...")
        steps = [
            self.llenar_codigo_fasecolda,
            self.click_buscar_vehiculo,
            self.seleccionar_vehiculo_0kms,
            self.llenar_ano_modelo,
            self.llenar_datos_asegurado,
            self.buscador_poblaciones,
            self.consultar_y_finalizar
        ]
        try:
            for i, step in enumerate(steps, 1):
                self.logger.info(f"📋 Ejecutando paso {i}/{len(steps)}...")
                if not await step():
                    self.logger.error(f"❌ Falló el paso {i}")
                    return False
            self.logger.info("✅ ¡FLUJO DE VEHÍCULO NUEVO EXITOSO!")
            return True
        except Exception as e:
            self.logger.error(f"❌ Error en flujo de vehículo nuevo: {e}")
            return False
