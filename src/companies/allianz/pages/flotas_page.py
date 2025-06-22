"""Página de flotas específica para Allianz."""

from playwright.async_api import Page
from ....shared.base_page import BasePage
from ....config.allianz_config import AllianzConfig

class FlotasPage(BasePage):
    """Página de Flotas con funciones específicas para el flujo de cotización de Allianz."""

    # Selectores centralizados
    SELECTOR_CELL               = "#tableFlotas_7_1"
    SELECTOR_ACEPTAR            = "#siguiente"
    SELECTOR_LIVIANOS           = "text=Livianos Particulares"
    SELECTOR_RADIO_NO           = "#IntervinientesBean\\$esAsegurado2"
    SELECTOR_DOC_TYPE           = "#IntervinientesBean\\$nifAsegurado_tipoDoc"
    SELECTOR_DOC_NUM            = "#IntervinientesBean\\$nifAsegurado_doc"
    SELECTOR_CAT_RIESGO         = "#CategoriaRiesgoBean\\$catRiesgo"
    SELECTOR_BTN_ACEPTAR_FINAL  = "#btnAceptar"

    def __init__(self, page: Page):
        super().__init__(page, 'allianz')
        self.config = AllianzConfig()

    async def click_policy_cell(self) -> bool:
        """Hace clic en la celda con el número de póliza configurado."""
        self.logger.info(f"🔲 Haciendo clic en celda {self.config.POLICY_NUMBER}...")
        return await self.click_in_frame(
            f"{self.SELECTOR_CELL}:has-text('{self.config.POLICY_NUMBER}')",
            f"celda {self.config.POLICY_NUMBER}"
        )

    async def click_ramos_asociados(self) -> bool:
        """Hace clic en el ramo de seguro configurado."""
        self.logger.info(f"🚗 Haciendo clic en '{self.config.RAMO_SEGURO}'...")
        return await self.click_in_frame(
            f"text={self.config.RAMO_SEGURO}",
            f"'{self.config.RAMO_SEGURO}'"
        )

    async def click_aceptar(self) -> bool:
        """Hace clic en el botón 'Aceptar'."""
        self.logger.info("✅ Haciendo clic en botón 'Aceptar'...")
        return await self.click_in_frame(
            f"{self.SELECTOR_ACEPTAR}:has-text('Aceptar')",
            "botón Aceptar"
        )

    async def click_radio_no_asegurado(self) -> bool:
        """Hace clic en el radio button 'No' para la pregunta de asegurado."""
        self.logger.info("🔘 Seleccionando radio 'No' (asegurado)...")
        if await self.click_in_frame(self.SELECTOR_RADIO_NO, "radio 'No' (asegurado)"):
            return True
        return await self.click_in_frame(
            "input[name='IntervinientesBean$esAsegurado'][value='N']",
            "radio 'No' (asegurado)"
        )

    async def select_tipo_documento(self, tipo_documento: str = None) -> bool:
        """Selecciona el tipo de documento en el dropdown."""
        # Usar el valor del config si no se proporciona uno específico
        if tipo_documento is None:
            tipo_documento = self.config.TIPO_DOCUMENTO
            
        tipo_map = {
            "NIT": " ", "REG_CIVIL_NACIMIENTO": "I", "NUIP": "J",
            "TARJETA_IDENTIDAD": "B", "CEDULA_CIUDADANIA": "C", "CEDULA_EXTRANJERIA": "X",
            "PASAPORTE": "P", "IDENTIFICACION_EXTRANJEROS": "L", "MENOR_SIN_IDENTIFICACION": "Q",
            "PEP": "E", "OTROS_DOCUMENTOS": "S", "PPT": "T", "SOCIEDAD_EXTRANJERA": "W"
        }
        if tipo_documento not in tipo_map:
            self.logger.error(f"❌ Tipo de documento '{tipo_documento}' no válido.")
            return False
        return await self.select_in_frame(
            self.SELECTOR_DOC_TYPE,
            tipo_map[tipo_documento],
            f"tipo de documento '{tipo_documento}'"
        )

    async def fill_numero_documento(self, numero_documento: str = None) -> bool:
        """Llena el campo de número de documento."""
        # Usar el valor del config si no se proporciona uno específico
        if numero_documento is None:
            numero_documento = self.config.NUMERO_DOCUMENTO
            
        return await self.fill_in_frame(
            self.SELECTOR_DOC_NUM,
            numero_documento,
            "número de documento"
        )

    async def select_categoria_riesgo_liviano(self) -> bool:
        """Selecciona 'Liviano Particulares' en el dropdown de categoría de riesgo."""
        return await self.select_in_frame(
            self.SELECTOR_CAT_RIESGO,
            "L0008",
            "categoría de riesgo 'Liviano Particulares'"
        )

    async def click_btn_aceptar_final(self) -> bool:
        """Hace clic en el botón final de Aceptar."""
        return await self.click_in_frame(
            f"{self.SELECTOR_BTN_ACEPTAR_FINAL}:has-text('Aceptar')",
            "botón Aceptar final"
        )

    async def execute_flotas_flow(self) -> bool:
        """Ejecuta el flujo completo de la página de flotas de Allianz."""
        self.logger.info("🚗 Iniciando flujo de Flotas Allianz...")
        steps = [
            self.click_policy_cell,
            self.click_ramos_asociados,
            self.click_aceptar,
            self.click_radio_no_asegurado,
            self.select_tipo_documento,
            self.fill_numero_documento,
            self.select_categoria_riesgo_liviano,
            self.click_btn_aceptar_final
        ]
        try:
            for step in steps:
                if not await step():
                    return False
            self.logger.info("✅ ¡FLUJO DE FLOTAS ALLIANZ COMPLETADO EXITOSAMENTE!")
            return True
        except Exception as e:
            self.logger.error(f"❌ Error en flujo de flotas Allianz: {e}")
            return False
