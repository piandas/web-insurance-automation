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
    SELECTOR_CAMPO_VERIFICACION_IN_IFRAME = 'input[name="_CVH_VehicuCol$codigoClaveVeh"]'
    # Selectores para datos del asegurado
    SELECTOR_FECHA_NACIMIENTO = "#DatosAseguradoAutosBean\\$fechaNacimiento"
    SELECTOR_GENERO = "#DatosAseguradoAutosBean\\$idSexo"

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
        self.logger.info("🔍 Verificando que el input esté listo...")
        script = f"""
        (() => {{
            const iframe = document.querySelector('{self.SELECTOR_IFRAME}');
            if (!iframe) return null;
            const input = iframe.contentDocument.querySelector('{self.SELECTOR_INPUT_PLACA_IN_IFRAME}');
            if (!input) return null;
            return {{
                hasGetValue: typeof input.getValue === 'function',
                ready: input.offsetParent !== null
            }};
        }})()
        """
        result = await self._retry_evaluate(
            script,
            validate=lambda r: bool(r and r.get('hasGetValue') and r.get('ready')),
            attempts=5,
            interval_ms=1000,
            log_tag="input listo"
        )
        return bool(result)

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
        self.logger.info("🔍 Verificando que el campo de verificación tenga valor...")
        script = f"""
        (() => {{
            const iframe = document.querySelector('{self.SELECTOR_IFRAME}');
            if (!iframe) return null;
            const campo = iframe.contentDocument.querySelector('{self.SELECTOR_CAMPO_VERIFICACION_IN_IFRAME}');
            if (campo && campo.value && campo.value.trim() !== '' && campo.value !== '0') {{
                return campo.value;
            }}
            return null;
        }})()
        """
        # Verificación inmediata
        immediate = await self.evaluate(script)
        if immediate:
            self.logger.info(f"✅ Campo verificado inmediatamente con valor: '{immediate}'")
            return True

        # Retry hasta 10 segundos (20 intentos de 1s)
        result = await self._retry_evaluate(
            script,
            validate=lambda r: bool(r),
            attempts=20,
            interval_ms=1000,
            log_tag="campo de verificación"
        )
        return bool(result)
    
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


    async def execute_placa_flow(self, placa: str = "IOS190", fecha_nacimiento: str = "01/06/1999", genero: str = "M") -> bool:
        """Ejecuta el flujo completo de placa y datos del asegurado."""
        self.logger.info(f"🚗 Iniciando flujo completo con placa '{placa}'...")
        steps = [
            lambda: self.esperar_y_llenar_placa(placa),
            self.click_comprobar_placa,
            self.verificar_campo_lleno,
            lambda: self.llenar_datos_asegurado(fecha_nacimiento, genero)
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