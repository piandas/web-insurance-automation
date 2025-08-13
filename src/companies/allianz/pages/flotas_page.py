"""Página de flotas específica para Allianz."""

from playwright.async_api import Page
from ....shared.base_page import BasePage
from ....config.client_config import ClientConfig

class FlotasPage(BasePage):
    """Página de Flotas con funciones específicas para el flujo de cotización de Allianz."""

    # Selectores centralizados
    SELECTOR_CELL_BASE          = "td.table-cell"  # Busca cualquier celda de tabla
    SELECTOR_ACEPTAR            = "#siguiente"
    SELECTOR_LIVIANOS           = "text=Livianos Particulares"
    SELECTOR_RADIO_NO           = "#IntervinientesBean\\$esAsegurado2"
    SELECTOR_DOC_TYPE           = "#IntervinientesBean\\$nifAsegurado_tipoDoc"
    SELECTOR_DOC_NUM            = "#IntervinientesBean\\$nifAsegurado_doc"
    SELECTOR_CAT_RIESGO         = "#CategoriaRiesgoBean\\$catRiesgo"
    SELECTOR_BTN_ACEPTAR_FINAL  = "#btnAceptar"

    def __init__(self, page: Page):
        super().__init__(page, 'allianz')

    async def click_policy_cell(self) -> bool:
        """Hace clic en la celda con el número de póliza configurado."""
        self.logger.info(f"🔲 Haciendo clic en celda {ClientConfig.get_policy_number('allianz')}...")
        return await self.click_in_frame(
            f"{self.SELECTOR_CELL_BASE}:has-text('{ClientConfig.get_policy_number('allianz')}')",
            f"celda {ClientConfig.get_policy_number('allianz')}"
        )

    async def click_ramos_asociados(self) -> bool:
        """Hace clic en el ramo de seguro configurado."""
        ramo_seguro = ClientConfig.get_company_specific_config('allianz').get('ramo_seguro', 'Livianos Particulares')
        self.logger.info(f"🚗 Haciendo clic en '{ramo_seguro}'...")
        return await self.click_in_frame(
            f"text={ramo_seguro}",
            f"'{ramo_seguro}'"
        )

    async def click_aceptar(self) -> bool:
        """Hace clic en el botón 'Aceptar'."""
        self.logger.info("✅ Haciendo clic en botón 'Aceptar'...")
        return await self.click_in_frame(
            f"{self.SELECTOR_ACEPTAR}:has-text('Aceptar')",
            "botón Aceptar"
        )

    async def click_radio_no_asegurado(self) -> bool:
        """Hace clic en el radio button 'No' para la pregunta de asegurado, reintentando si el campo de tipo de documento no se habilita."""
        self.logger.info("🔘 Seleccionando radio 'No' (asegurado)...")
        max_attempts = 3
        for intento in range(1, max_attempts + 1):
            self.logger.info(f"🔘 Intento {intento} de seleccionar radio 'No' (asegurado)...")
            # Intentar primer selector
            clicked = await self.click_in_frame(self.SELECTOR_RADIO_NO, "radio 'No' (asegurado)")
            if not clicked:
                # Intentar selector alternativo
                clicked = await self.click_in_frame(
                    "input[name='IntervinientesBean$esAsegurado'][value='N']",
                    "radio 'No' (asegurado)"
                )
            if not clicked:
                self.logger.warning(f"❌ No se pudo hacer clic en el radio 'No' (intento {intento})")
                await self.page.wait_for_timeout(3000)
                continue
            # Verificar si el campo de tipo de documento está habilitado
            try:
                frame = self.page.frame(name="appArea") if hasattr(self.page, 'frame') else None
                if not frame:
                    self.logger.warning("⚠️ No se encontró el iframe 'appArea' para verificar habilitación de tipo de documento")
                    await self.page.wait_for_timeout(3000)
                    continue
                tipo_doc_elem = await frame.query_selector(self.SELECTOR_DOC_TYPE)
                if tipo_doc_elem:
                    is_disabled = await tipo_doc_elem.get_attribute('disabled')
                    if is_disabled is None:
                        self.logger.info("✅ Campo de tipo de documento habilitado tras seleccionar radio 'No'")
                        return True
                    else:
                        self.logger.warning(f"⚠️ Campo de tipo de documento sigue deshabilitado (intento {intento})")
                else:
                    self.logger.warning(f"⚠️ No se encontró el campo de tipo de documento para verificar habilitación (intento {intento})")
            except Exception as e:
                self.logger.warning(f"⚠️ Error verificando habilitación de tipo de documento: {e}")
            await self.page.wait_for_timeout(3000)
        self.logger.error("❌ No se pudo habilitar el campo de tipo de documento tras 3 intentos de seleccionar radio 'No'")
        return False

    async def select_tipo_documento(self, tipo_documento: str = None) -> bool:
        """Selecciona el tipo de documento en el dropdown."""
        # Usar el valor del config si no se proporciona uno específico
        if tipo_documento is None:
            tipo_documento = ClientConfig.get_client_document_type('allianz')
            
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
            numero_documento = ClientConfig.CLIENT_DOCUMENT_NUMBER
            
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
