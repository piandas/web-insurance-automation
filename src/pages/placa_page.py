from playwright.async_api import Page
from src.utils import BasePage
import logging

class PlacaPage(BasePage):
    """Página para manejo de placa y comprobación."""
    
    # Selectores
    SELECTOR_INPUT_PLACA = "#DatosVehiculoIndividualBean\\$matricula"
    SELECTOR_BTN_COMPROBAR = "#btnPlaca"
    SELECTOR_IFRAME = "iframe"
    SELECTOR_INPUT_PLACA_IN_IFRAME = 'input[name="DatosVehiculoIndividualBean$matricula"]'
    SELECTOR_CAMPO_VERIFICACION_IN_IFRAME = 'input[name="_CVH_VehicuCol$codigoClaveVeh"]'    # Selectores para datos del asegurado
    SELECTOR_FECHA_NACIMIENTO = "#DatosAseguradoAutosBean\\$fechaNacimiento"
    SELECTOR_GENERO = "#DatosAseguradoAutosBean\\$idSexo"
    # Selectores para buscador de poblaciones
    SELECTOR_DEPARTAMENTO = "#idCity_1_node1"
    SELECTOR_BTN_BUSCAR_CIUDAD = "#idCity_1_node2AjaxFinderImg"
    SELECTOR_INPUT_CIUDAD = "#idCity_1_node2"
    SELECTOR_CODIGO_CIUDAD = "#idFinderCod"
    SELECTOR_LISTA_CIUDADES = "#div_loc_idCity_1"

    def __init__(self, page: Page):
        super().__init__(page)
        self.logger = logging.getLogger('allianz')

    async def esperar_y_llenar_placa(self, placa: str = "IOS190") -> bool:
        """Espera el input de placa y lo llena."""
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
    
    async def llenar_datos_asegurado(self, fecha_nacimiento: str = "01/06/1999", genero: str = "M") -> bool:
        """
        Llena los datos del asegurado: fecha de nacimiento y género.
        
        Args:
            fecha_nacimiento (str): Fecha en formato dd/mm/yyyy (default: "01/06/1999")
            genero (str): Género - M (Masculino), F (Femenino), J (Jurídico) (default: "M")
        
        Returns:
            bool: True si se llenaron los datos correctamente, False en caso contrario
        """
        self.logger.info(f"👤 Llenando datos del asegurado - Fecha: {fecha_nacimiento}, Género: {genero}")
        
        try:
            # Llenar fecha de nacimiento
            if not await self.fill_in_frame(
                self.SELECTOR_FECHA_NACIMIENTO,
                fecha_nacimiento,
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

    async def buscador_poblaciones(self, departamento: str = "ANTIOQUIA", ciudad: str = "BELLO") -> bool:
        """
        Busca y selecciona una población específica.
        
        Args:
            departamento (str): Nombre del departamento (default: "ANTIOQUIA")
            ciudad (str): Nombre de la ciudad (default: "BELLO")
        
        Returns:
            bool: True si se seleccionó la población correctamente, False en caso contrario
        """
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

    async def execute_placa_flow(self, placa: str = "IOS190", fecha_nacimiento: str = "01/06/1989", genero: str = "M", departamento: str = "ANTIOQUIA", ciudad: str = "BELLO") -> bool:
        """Ejecuta el flujo completo de placa, datos del asegurado y selección de población."""
        self.logger.info(f"🚗 Iniciando flujo completo con placa '{placa}', ciudad '{ciudad}'...")
        steps = [
            lambda: self.esperar_y_llenar_placa(placa),
            self.click_comprobar_placa,
            self.verificar_campo_lleno,
            lambda: self.llenar_datos_asegurado(fecha_nacimiento, genero),
            lambda: self.buscador_poblaciones(departamento, ciudad)
        ]
        try:
            for i, step in enumerate(steps, 1):
                self.logger.info(f"📋 Ejecutando paso {i}/{len(steps)}...")
                if not await step():
                    self.logger.error(f"❌ Falló el paso {i}")
                    return False
            self.logger.info("✅ ¡FLUJO COMPLETO EXITOSO!")
            return True
        except Exception as e:
            self.logger.error(f"❌ Error en flujo completo: {e}")
            return False