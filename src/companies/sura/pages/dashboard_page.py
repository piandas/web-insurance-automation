"""Página del dashboard específica para Sura."""

import asyncio
from playwright.async_api import Page
from ....shared.base_page import BasePage


class DashboardPage(BasePage):
    """Página del dashboard con navegación al cotizador en Sura."""    # Selectores reutilizables
    COTIZADOR_SELECTORS = [
        'a[onclick="openApp(\'/home/openapp?id=29\')"]',  # Selector específico del cotizador
        'img[src*="boton-cotizador.png"]',
        'a[href*="boton-cotizador.png"]',
        'img[alt="boton-cotizador.png"]',
    ]
    MENU_STEPS = [
        ('button#dropdownMenuButton', 'botón principal del menú', 10000, 2),
        ('a:has-text("Soluciones")', 'Soluciones', 5000, 1),
        ('a:has-text("Seguros Autos")', 'Seguros Autos', 5000, 1),
        ('a:has-text("Colectivos")', 'Colectivos', 5000, 1),
        ('a:has-text("Nueva Inclusión")', 'Nueva inclusión', 5000, 3),
    ]
    DOCUMENT_TYPE_MAP = {
        'C': 'CEDULA',
        'E': 'CED.EXTRANJERIA',
        'P': 'PASAPORTE',
        'A': 'NIT',
        'CA': 'NIT PERSONAS NATURALES',
        'N': 'NUIP',
        'R': 'REGISTRO CIVIL',
        'T': 'TARJ.IDENTIDAD',
        'D': 'DIPLOMATICO',
        'X': 'DOC.IDENT. DE EXTRANJEROS',
        'F': 'IDENT. FISCAL PARA EXT.',
        'TC': 'CERTIFICADO NACIDO VIVO',
        'TP': 'PASAPORTE ONU',
        'TE': 'PERMISO ESPECIAL PERMANENCIA',
        'TS': 'SALVOCONDUCTO DE PERMANENCIA',
        'TF': 'PERMISO ESPECIAL FORMACN PEPFF',
        'TT': 'PERMISO POR PROTECCION TEMPORL',
    }
    DOCUMENT_SELECTORS = [
        'input[placeholder="Documento"]',
        'input[placeholder*="documento"]',
        'input[placeholder*="Documento"]',
        'input[type="text"]',
        'input[placeholder*="cedula"]',
        'input[placeholder*="Cédula"]',
        '#documento',
        '#cedula',
        'input[name="documento"]',
        'input[name="cedula"]',
    ]
    ACCEPT_SELECTORS = [
        'button:has-text("Aceptar")',
        'button:has-text("Enviar")',
        'button:has-text("Continuar")',
        'button[type="submit"]',
        'input[type="submit"]',
        '.btn-primary',
        '.btn-success',
    ]

    def __init__(self, page: Page):
        super().__init__(page, 'sura')

    async def _find_and_click(
        self,
        selectors: list[str],
        description: str,
        timeout: int = 5000,
        sleep_after: float = 0,
    ) -> bool:
        """Busca múltiples selectores y hace clic en el primero visible."""
        for sel in selectors:
            if await self.is_visible_safe(sel, timeout=timeout):
                self.logger.info(f"✅ {description} encontrado con selector: {sel}")
                await self.safe_click(sel)
                if sleep_after:
                    await asyncio.sleep(sleep_after)
                return True
        self.logger.error(f"❌ No se pudo encontrar {description}")
        return False

    async def _navigate_sequence(self) -> bool:
        """Navega por la secuencia de menús definida en MENU_STEPS."""        # pequeña espera para carga inicial
        await asyncio.sleep(3)
        for sel, desc, timeout, sleep_after in self.MENU_STEPS:
            if not await self._find_and_click([sel], desc, timeout, sleep_after):
                return False
        self.logger.info("✅ Navegación completa por menús exitosa - Formulario listo")
        return True

    async def navigate_to_cotizador(self) -> bool:
        """Navega al cotizador de Sura y abre la nueva pestaña."""
        self.logger.info("💰 Navegando al cotizador de Sura...")
        try:
            for sel in self.COTIZADOR_SELECTORS:
                if await self.is_visible_safe(sel, timeout=2000):
                    self.logger.info(f"✅ Cotizador encontrado con selector: {sel}")
                    
                    # Configurar el listener antes del clic
                    new_page_promise = self.page.context.wait_for_event("page")
                    await self.safe_click(sel)
                    
                    # Esperar la nueva pestaña
                    new_page = await new_page_promise
                    await new_page.wait_for_load_state("networkidle", timeout=20000)
                    
                    # Cambiar a la nueva pestaña
                    self.page = new_page
                    self.logger.info(f"✅ Nueva pestaña abierta: {new_page.url}")
                    await asyncio.sleep(2)
                    return True
                    
            self.logger.error("❌ No se pudo encontrar el botón del cotizador")
            return False
        except Exception as e:
            self.logger.exception(f"❌ Error navegando al cotizador: {e}")
            return False

    async def click_main_dropdown(self) -> bool:
        """Hace clic en el botón principal y recorre el menú completo."""
        self.logger.info("🔽 Iniciando secuencia de menús...")
        return await self._navigate_sequence()

    async def select_document_type(self, document_type: str = "C") -> bool:
        """Selecciona el tipo de documento usando Material Design dropdown."""
        self.logger.info(f"📄 Seleccionando tipo de documento: {document_type}")
        if not await self._find_and_click(
            ['.mat-select-value'], "dropdown de tipo de documento", 10000, 1
        ):
            return False

        text = self.DOCUMENT_TYPE_MAP.get(document_type, 'CEDULA')
        return await self._find_and_click(
            [f'span:has-text("{text}")'],            f"opción {text}",
            5000,
            0
        )

    async def input_document_number(self, document_number: str = "1020422674") -> bool:
        """Ingresa el número de documento en el campo correspondiente."""
        self.logger.info(f"📄 Ingresando número de documento: {document_number}")
        for sel in self.DOCUMENT_SELECTORS:
            try:
                if await self.is_visible_safe(sel, timeout=5000):
                    self.logger.info(f"✅ Campo de documento encontrado con selector: {sel}")
                    await self.page.fill(sel, "")
                    await self.page.fill(sel, document_number)
                    return True
            except Exception:
                continue
        self.logger.error("❌ No se pudo encontrar el campo de número de documento")
        return False

    async def accept_form(self) -> bool:
        """Acepta o envía el formulario."""
        self.logger.info("✅ Aceptando formulario...")
        
        # Hacer clic en el botón
        if not await self._find_and_click(
            self.ACCEPT_SELECTORS,
            "botón de aceptar/enviar",
            5000,
            2
        ):
            return False
        
        # Intentar esperar que se cargue, pero no fallar si no funciona
        try:
            await self.wait_for_load_state_with_retry("networkidle", timeout=10000)
        except Exception as e:
            self.logger.warning(f"⚠️ No se pudo esperar networkidle, pero continuando: {e}")
        
        self.logger.info("✅ Formulario aceptado exitosamente")
        return True

    async def complete_navigation_flow(
        self,
        document_number: str = "1020422674",
        document_type: str = "C"
    ) -> bool:
        """Completa el flujo completo de navegación en Sura."""
        self.logger.info("🚀 Iniciando flujo completo de navegación Sura...")
        steps = [
            self.navigate_to_cotizador,
            self.click_main_dropdown,
            lambda: self.select_document_type(document_type),
            lambda: self.input_document_number(document_number),
            self.accept_form,
        ]
        for step in steps:
            if not await step():
                return False
        self.logger.info("✅ Flujo de navegación Sura completado exitosamente")
        return True
