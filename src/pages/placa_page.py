from playwright.async_api import Page
from src.utils import BasePage
import logging

class PlacaPage(BasePage):
    """Página para manejo de placa y comprobación."""
    # Selectores
    SELECTOR_INPUT_PLACA = "#DatosVehiculoIndividualBean\\$matricula"
    SELECTOR_BTN_COMPROBAR = "#btnPlaca"

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

    async def click_comprobar_placa(self) -> bool:
        """Espera y hace clic en el botón 'Comprobar' de placa."""
        self.logger.info("🖱️ Esperando y haciendo clic en botón 'Comprobar' de placa...")
        return await self.click_in_frame(
            self.SELECTOR_BTN_COMPROBAR,
            "botón 'Comprobar' de placa"
        )
