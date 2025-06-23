"""Página del dashboard específica para Sura."""

import asyncio
from playwright.async_api import Page
from ....shared.base_page import BasePage


class DashboardPage(BasePage):
    """Página del dashboard con navegación al cotizador en Sura."""
    
    # Selectores reutilizables
    COTIZADOR_SELECTORS = [
        'a[onclick="openApp(\'/home/openapp?id=29\')"]',  # Selector específico del cotizador
        'img[src*="boton-cotizador.png"]',
        'a[href*="boton-cotizador.png"]',
        'img[alt="boton-cotizador.png"]',
    ]
    
    MENU_STEPS = [
        ('button#dropdownMenuButton', 'botón principal del menú', 20000, 0),  # Sin espera para evitar que se cierre
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

    # Selectores para verificar si el menú está desplegado
    MENU_DROPDOWN_OPEN_SELECTORS = [
        'button#dropdownMenuButton[aria-expanded="true"]',
        '.dropdown-menu.show',
        '.dropdown-menu:not(.d-none)',
        '.dropdown.show',
    ]

    def __init__(self, page: Page):
        super().__init__(page, 'sura')

    async def _find_and_click(
        self,
        selectors: list[str],
        description: str,
        timeout: int = 5000,
        sleep_after: float = 0,
        max_attempts: int = 5,
        retry_delay: float = 1.0,
    ) -> bool:
        """Busca múltiples selectores y hace clic en el primero visible con reintentos."""
        
        async def _try_click_selectors():
            """Función interna para intentar hacer clic en los selectores."""
            for sel in selectors:
                if await self.is_visible_safe(sel, timeout=timeout):
                    self.logger.info(f"✅ {description} encontrado con selector: {sel}")
                    success = await self.safe_click(sel)
                    if success and sleep_after:
                        await asyncio.sleep(sleep_after)
                    return success
            return False
        
        # Usar la función de reintentos de la clase base
        return await self.retry_action(
            _try_click_selectors,
            description,
            max_attempts=max_attempts,
            delay_seconds=retry_delay
        )

    async def navigate_to_cotizador(self) -> bool:
        """Navega al cotizador de Sura y abre la nueva pestaña."""
        self.logger.info("💰 Navegando al cotizador de Sura...")
        max_attempts = 20
        
        for attempt in range(1, max_attempts + 1):
            try:
                self.logger.info(f"🔄 Intento {attempt} de {max_attempts} para encontrar el cotizador...")
                
                for sel in self.COTIZADOR_SELECTORS:
                    if await self.is_visible_safe(sel, timeout=2000):
                        self.logger.info(f"✅ Cotizador encontrado con selector: {sel}")
                        
                        # Configurar el listener antes del clic
                        new_page_promise = self.page.context.wait_for_event("page")
                        await self.safe_click(sel)
                        
                        # Esperar la nueva pestaña
                        new_page = await new_page_promise
                        await new_page.wait_for_load_state("networkidle", timeout=25000)
                        
                        # Cambiar a la nueva pestaña
                        self.page = new_page
                        self.logger.info(f"✅ Nueva pestaña abierta: {new_page.url}")
                        await asyncio.sleep(2)
                        return True
                
                # Si no se encontró el botón y no es el último intento, esperar 2 segundos
                if attempt < max_attempts:
                    self.logger.warning(f"⚠️ Intento {attempt} fallido. Esperando 2 segundos antes del siguiente intento...")
                    await asyncio.sleep(2)
                    
            except Exception as e:
                self.logger.warning(f"⚠️ Error en intento {attempt}: {e}")
                if attempt < max_attempts:
                    await asyncio.sleep(2)
                else:
                    self.logger.exception(f"❌ Error navegando al cotizador después de {max_attempts} intentos: {e}")
                    return False
                    
        self.logger.error(f"❌ No se pudo encontrar el botón del cotizador después de {max_attempts} intentos")
        return False
    
    async def _navigate_sequence(self) -> bool:
        """Navega por la secuencia de menús definida en MENU_STEPS con reintentos completos."""
        max_full_attempts = 3  # Intentos completos de toda la secuencia
        
        for full_attempt in range(1, max_full_attempts + 1):
            self.logger.info(f"🔄 Intento completo {full_attempt}/{max_full_attempts} de navegación por menús...")
            
            # Pequeña espera para carga inicial
            await asyncio.sleep(3)
            
            sequence_success = True
            
            for step_index, (sel, desc, timeout, sleep_after) in enumerate(self.MENU_STEPS):
                self.logger.info(f"📍 Paso {step_index + 1}/{len(self.MENU_STEPS)}: {desc}")
                  # Para el primer paso (botón principal), usar lógica especial
                if step_index == 0:
                    success = await self._find_and_click(
                        [sel], 
                        desc, 
                        timeout, 
                        0,  # No esperar después del primer clic
                        max_attempts=5,
                        retry_delay=1.0
                    )
                    
                    if success:
                        # Esperar 3 segundos para que el menú se estabilice
                        self.logger.info("⏳ Esperando 3 segundos para verificar que el menú siga abierto...")
                        await asyncio.sleep(3)
                        
                        # Verificar si el menú sigue abierto
                        if not await self.is_menu_open():
                            self.logger.warning("⚠️ El menú se cerró, intentando abrirlo nuevamente...")
                            # Intentar abrirlo una vez más
                            if await self.safe_click('button#dropdownMenuButton'):
                                await asyncio.sleep(1)  # Espera corta después del segundo clic
                                if not await self.is_menu_open():
                                    self.logger.error("❌ No se pudo mantener el menú abierto")
                                    success = False
                                else:
                                    self.logger.info("✅ Menú reabierto exitosamente")
                            else:
                                success = False
                        else:
                            self.logger.info("✅ Menú sigue abierto después de 3 segundos")
                else:
                    # Para los demás pasos, asegurar que el menú esté abierto primero
                    if not await self.ensure_menu_open():
                        self.logger.error(f"❌ No se pudo asegurar que el menú esté abierto para {desc}")
                        success = False
                    else:
                        # Ahora hacer clic en el elemento del menú
                        success = await self._find_and_click(
                            [sel], 
                            desc, 
                            timeout, 
                            sleep_after,
                            max_attempts=3,  # Menos intentos ya que el menú debería estar abierto
                            retry_delay=0.5  # Menos espera entre intentos
                        )
                
                if not success:
                    self.logger.warning(f"⚠️ Falló el paso {step_index + 1} ({desc}) en intento completo {full_attempt}")
                    sequence_success = False
                    break  # Salir del loop de pasos y reintentar toda la secuencia
            
            if sequence_success:
                self.logger.info("✅ Navegación completa por menús exitosa - Formulario listo")
                return True
            
            # Si no es el último intento completo, esperar antes de reintentar
            if full_attempt < max_full_attempts:
                self.logger.warning(f"🔄 Reintentando secuencia completa en 2 segundos...")
                await asyncio.sleep(2)
        
        self.logger.error(f"❌ No se pudo completar la navegación por menús después de {max_full_attempts} intentos completos")
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
            [f'span:has-text("{text}")'],
            f"opción {text}",
            5000,
            0
        )

    async def is_menu_open(self) -> bool:
        """Verifica si el menú desplegable está abierto."""
        for selector in self.MENU_DROPDOWN_OPEN_SELECTORS:
            if await self.is_visible_safe(selector, timeout=1000):
                self.logger.info(f"✅ Menú abierto detectado con selector: {selector}")
                return True
        return False

    async def ensure_menu_open(self, max_attempts: int = 3) -> bool:
        """Asegura que el menú esté abierto, intentando abrirlo si está cerrado."""
        for attempt in range(1, max_attempts + 1):
            if await self.is_menu_open():
                self.logger.info("✅ Menú ya está abierto")
                return True
            
            self.logger.warning(f"⚠️ Menú cerrado, intentando abrirlo (intento {attempt}/{max_attempts})")
            
            # Intentar abrir el menú
            if await self.safe_click('button#dropdownMenuButton'):
                await asyncio.sleep(0.5)  # Espera corta para que se abra
                
                if await self.is_menu_open():
                    self.logger.info(f"✅ Menú abierto exitosamente en intento {attempt}")
                    return True
            
            if attempt < max_attempts:
                await asyncio.sleep(1)
        
        self.logger.error(f"❌ No se pudo abrir el menú después de {max_attempts} intentos")
        return False


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