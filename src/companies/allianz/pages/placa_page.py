"""Página de placa específica para Allianz."""

import datetime
import os
from playwright.async_api import Page
from ....shared.base_page import BasePage
from ....shared.utils import Utils
from ....config.allianz_config import AllianzConfig

class PlacaPage(BasePage):
    """Página para manejo de placa y comprobación en Allianz."""
    
    # Selectores
    SELECTOR_INPUT_PLACA = "#DatosVehiculoIndividualBean\\$matricula"
    SELECTOR_BTN_COMPROBAR = "#btnPlaca"
    SELECTOR_INPUT_PLACA_IN_IFRAME = 'input[name="DatosVehiculoIndividualBean$matricula"]'
    SELECTOR_CAMPO_VERIFICACION_IN_IFRAME = 'input[name="_CVH_VehicuCol$codigoClaveVeh"]'
    
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

    async def esperar_y_llenar_placa(self, placa: str = None) -> bool:
        """Espera el input de placa y lo llena."""
        # Usar el valor del config si no se proporciona uno específico
        if placa is None:
            placa = self.config.PLACA_VEHICULO
            
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
            fecha_nacimiento = self.config.FECHA_NACIMIENTO
        if genero is None:
            genero = self.config.GENERO_ASEGURADO
        
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
            
            self.logger.info("✅ Datos del asegurado llenados correctamente")
            return True
            
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
            departamento = self.config.DEPARTAMENTO
        if ciudad is None:
            ciudad = self.config.CIUDAD
            
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
            
            # Paso 3: Primer clic en "Siguiente"
            if not await self.click_in_frame(
                self.SELECTOR_BTN_ACEPTAR,
                "botón 'Siguiente' (primera vez)"
            ):
                self.logger.error("❌ Error al hacer clic en primer 'Siguiente'")
                return False
            
            # Pausa para que cargue el frame
            await self.page.wait_for_timeout(3000)
            await self.wait_for_iframe_content()
            
            # Paso 4: Segundo clic en "Siguiente"
            if not await self.click_in_frame(
                self.SELECTOR_BTN_ACEPTAR,
                "botón 'Siguiente' (segunda vez)"
            ):
                self.logger.error("❌ Error al hacer clic en segundo 'Siguiente'")
                return False
            
            # Pausa para que aparezca el botón Archivar
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
            
            # Paso 9: Esperar y hacer clic en "Estudio de Seguro"
            await self.page.wait_for_timeout(3000)
            
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
        
    async def execute_placa_flow(self, placa: str = None, fecha_nacimiento: str = None, genero: str = None, departamento: str = None, ciudad: str = None) -> bool:
        """Ejecuta el flujo completo desde placa hasta finalización en Allianz."""
        # Usar valores del config si no se proporcionan específicos
        if placa is None:
            placa = self.config.PLACA_VEHICULO
        if fecha_nacimiento is None:
            fecha_nacimiento = self.config.FECHA_NACIMIENTO
        if genero is None:
            genero = self.config.GENERO_ASEGURADO
        if departamento is None:
            departamento = self.config.DEPARTAMENTO
        if ciudad is None:
            ciudad = self.config.CIUDAD
            
        self.logger.info(f"🚗 Iniciando flujo completo de placa Allianz con '{placa}', ciudad '{ciudad}'...")
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
            self.logger.info("✅ ¡FLUJO COMPLETO DE PLACA ALLIANZ EXITOSO!")
            return True
        except Exception as e:
            self.logger.error(f"❌ Error en flujo completo de placa Allianz: {e}")
            return False
