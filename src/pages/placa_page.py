from playwright.async_api import Page
from src.utils import BasePage
import logging
import asyncio

class PlacaPage(BasePage):
    """Página para manejo de placa y comprobación."""
    
    # Selectores
    SELECTOR_INPUT_PLACA = "#DatosVehiculoIndividualBean\\$matricula"
    SELECTOR_BTN_COMPROBAR = "#btnPlaca"
    SELECTOR_CAMPO_VERIFICACION = "#_CVH_VehicuCol\\$codigoClaveVeh"

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
        
        script = """
        (() => {
            const iframe = document.querySelector('iframe');
            if (iframe) {
                const input = iframe.contentDocument.querySelector('input[name="DatosVehiculoIndividualBean$matricula"]');
                if (input) {
                    return {
                        hasGetValue: typeof input.getValue === 'function',
                        value: input.value,
                        ready: input.offsetParent !== null
                    };
                }
            }
            return null;
        })()
        """
        
        for attempt in range(5):  # 5 intentos
            result = await self.evaluate(script)
            if result and result.get('hasGetValue') and result.get('ready'):
                self.logger.info(f"✅ Input listo con getValue: {result}")
                return True
            
            self.logger.info(f"⏳ Intento {attempt + 1}/5 - Input no está listo: {result}")
            await asyncio.sleep(1)
        
        self.logger.error("❌ Input no está listo después de 5 intentos")
        return False

    async def click_comprobar_placa(self) -> bool:
        """Hace clic en el botón 'Comprobar' ejecutando su onclick."""
        self.logger.info("🖱️ Preparando para ejecutar onclick del botón 'Comprobar'...")
        
        # Verificar que el input esté listo
        if not await self.verificar_input_ready():
            return False
        
        # Esperar un poco más para asegurar que todo esté cargado
        await asyncio.sleep(1)
        
        # Ejecutar el onclick del botón directamente
        script = """
        (() => {
            const iframe = document.querySelector('iframe');
            if (iframe) {
                const btn = iframe.contentDocument.querySelector('#btnPlaca');
                if (btn && btn.onclick) {
                    try {
                        btn.onclick();
                        return { success: true, message: 'onClick ejecutado' };
                    } catch (error) {
                        return { success: false, message: error.toString() };
                    }
                }
            }
            return { success: false, message: 'Botón no encontrado' };
        })()
        """
        
        result = await self.evaluate(script)
        
        if result and result.get('success'):
            self.logger.info("✅ onClick ejecutado exitosamente")
            # Esperar a que procese
            await asyncio.sleep(3)
            return True
        else:
            self.logger.error(f"❌ onClick falló: {result.get('message', 'Error desconocido')}")
            return False

    async def verificar_campo_lleno(self) -> bool:
        """Verifica que el campo de verificación no esté vacío (espera hasta 30 segundos)."""
        self.logger.info("🔍 Verificando que el campo de verificación tenga valor (timeout 30s)...")
        
        script = """
        (() => {
            const iframe = document.querySelector('iframe');
            if (iframe) {
                const campo = iframe.contentDocument.querySelector('input[name="_CVH_VehicuCol$codigoClaveVeh"]');
                if (campo && campo.value && campo.value !== '0' && campo.value.trim() !== '') {
                    return campo.value;
                }
            }
            return null;
        })()
        """
        
        # Esperar hasta 30 segundos
        for attempt in range(30):  # 30 intentos de 1 segundo cada uno
            result = await self.evaluate(script)
            if result:
                self.logger.info(f"✅ Campo verificado exitosamente con valor: '{result}' (después de {attempt + 1} segundos)")
                return True
            
            if attempt % 5 == 0:  # Log cada 5 segundos
                self.logger.info(f"⏳ Esperando campo se llene... {attempt + 1}/30 segundos")
            
            await asyncio.sleep(1)
        
        self.logger.error("❌ El campo de verificación está vacío después de 30 segundos - timeout")
        return False

    async def execute_placa_flow(self, placa: str = "IOS190") -> bool:
        """Ejecuta el flujo completo de placa."""
        self.logger.info(f"🚗 Iniciando flujo de placa con '{placa}'...")
        
        steps = [
            lambda: self.esperar_y_llenar_placa(placa),
            self.click_comprobar_placa,
            self.verificar_campo_lleno
        ]
        
        try:
            for i, step in enumerate(steps, 1):
                self.logger.info(f"📋 Ejecutando paso {i}/{len(steps)}...")
                if not await step():
                    self.logger.error(f"❌ Falló el paso {i}")
                    return False
            
            self.logger.info("✅ ¡FLUJO DE PLACA COMPLETADO EXITOSAMENTE!")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error en flujo de placa: {e}")
            return False
