"""Clase base para todas las páginas de automatización."""

import logging
import asyncio
from typing import Optional, Any, Callable, Dict, List, Union
from playwright.async_api import Page, TimeoutError as PlaywrightTimeout

from ..core.constants import Constants

class BasePage:
    """Clase base con métodos genéricos para interacciones con páginas."""
    
    IFRAME_SELECTOR: str = "iframe" # Selector del iframe principal (Allianz)
    
    # Mapeo común de tipos de documento (Sura)
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

    def __init__(self, page: Page, company: str = "generic"):
        self.page: Page = page
        self.company = company
        self._frame = self.page.frame_locator(self.IFRAME_SELECTOR)
        self.logger = logging.getLogger(company)    
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # FUNCIONES REUTILIZABLES EXTRAÍDAS DE LAS PÁGINAS DE SURA
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    async def get_element_value(self, selector: str, property_name: str = "value") -> str:
        """
        Obtiene el valor de una propiedad de un elemento.
        
        Args:
            selector: Selector CSS del elemento
            property_name: Propiedad a obtener (value, textContent, innerHTML, etc.)
            
        Returns:
            Valor de la propiedad o cadena vacía si no se encuentra
        """
        try:
            return await self.page.evaluate(
                """(args) => { 
                    const el = document.querySelector(args.selector); 
                    return el ? el[args.property] || '' : ''; 
                }""",
                {"selector": selector, "property": property_name}
            )
        except Exception as e:
            self.logger.error(f"❌ Error obteniendo {property_name} de '{selector}': {e}")
            return ""

    async def find_and_click_from_selectors(
        self,
        selectors: List[str],
        description: str,
        timeout: int = 5000,
        sleep_after: float = 0,
        max_attempts: int = 5,
        retry_delay: float = 1.0,
    ) -> bool:
        """
        Busca múltiples selectores y hace clic en el primero visible con reintentos.
        
        Args:
            selectors: Lista de selectores CSS a probar
            description: Descripción para logging
            timeout: Timeout para cada selector individual
            sleep_after: Tiempo de espera después del clic exitoso
            max_attempts: Número máximo de intentos completos
            retry_delay: Tiempo entre reintentos
            
        Returns:
            True si logró hacer clic, False en caso contrario
        """
        
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
            _try_click_selectors,            description,
            max_attempts=max_attempts,
            delay_seconds=retry_delay
        )

    async def verify_element_value_equals(
        self, 
        selector: str, 
        expected_value: str, 
        property_name: str = "value",
        description: str = ""
    ) -> bool:
        """
        Verifica que un elemento tenga un valor específico.
        
        Args:
            selector: Selector CSS del elemento
            expected_value: Valor esperado
            property_name: Propiedad a verificar
            description: Descripción para logging
            
        Returns:
            True si el valor coincide, False en caso contrario
        """
        try:
            # Usar locator().first para obtener el primer elemento que coincida
            current_value = await self.page.locator(selector).first.input_value()
            is_equal = current_value == expected_value
            
            if description:
                status = "✅ MATCH" if is_equal else "⚠️ DIFF"
                self.logger.info(f"{status} {description}: Esperado='{expected_value}' | Actual='{current_value}'")
            
            return is_equal
        except Exception as e:
            self.logger.error(f"❌ Error verificando valor de '{selector}': {e}")
            return False

    async def execute_js_with_validation(
        self,
        script: str,
        validation_func: Optional[Callable] = None,
        description: str = "",
        max_attempts: int = 3,
        retry_delay: float = 0.5
    ) -> Any:
        """
        Ejecuta JavaScript con validación opcional y reintentos.
        
        Args:
            script: Script de JavaScript a ejecutar
            validation_func: Función para validar el resultado (opcional)
            description: Descripción para logging
            max_attempts: Número máximo de intentos
            retry_delay: Tiempo entre reintentos
            
        Returns:
            Resultado del script si es válido, None en caso contrario
        """
        for attempt in range(1, max_attempts + 1):
            try:
                result = await self.page.evaluate(script)
                
                if validation_func is None or validation_func(result):
                    if description:
                        self.logger.info(f"✅ {description} - JS ejecutado exitosamente: {result}")
                    return result
                    
                if attempt < max_attempts:
                    self.logger.warning(f"⚠️ {description} - Intento {attempt} falló, reintentando...")
                    await asyncio.sleep(retry_delay)
                    
            except Exception as e:
                self.logger.warning(f"⚠️ {description} - Error en intento {attempt}: {e}")
                if attempt < max_attempts:
                    await asyncio.sleep(retry_delay)        
        self.logger.error(f"❌ {description} - Falló después de {max_attempts} intentos")
        return None

    async def wait_for_page_navigation(
        self,
        expected_url_parts: List[str] = None,
        timeout: int = 20000,  # Incrementado de 10 a 20 segundos
        description: str = "navegación",
        retry_attempts: int = 3
    ) -> bool:
        """
        Espera a que la página navegue a una nueva URL de manera eficiente con reintentos.
        
        Args:
            expected_url_parts: Partes que deberían estar en la nueva URL
            timeout: Timeout en milisegundos por intento
            description: Descripción para logging
            retry_attempts: Número de intentos de navegación
            
        Returns:
            True si la navegación fue exitosa, False en caso contrario
        """
        for attempt in range(retry_attempts):
            if attempt > 0:
                self.logger.info(f"🔄 Reintentando {description} - Intento {attempt + 1}/{retry_attempts}")
            else:
                self.logger.info(f"⏳ Esperando {description}...")
            
            try:
                current_url = self.page.url
                self.logger.info(f"📍 URL actual: {current_url}")
                
                # Verificación rápida cada 500ms en lugar de esperar todo el timeout
                max_checks = timeout // 500  # Verificar cada 500ms
                
                for check in range(max_checks):
                    await asyncio.sleep(0.5)  # Esperar 500ms
                    
                    new_url = self.page.url
                    
                    # Verificar si cambió la URL
                    if new_url != current_url:
                        self.logger.info(f"📍 Nueva URL: {new_url}")
                        self.logger.info(f"✅ {description} - URL cambió exitosamente en {(check + 1) * 0.5:.1f}s")
                        
                        # Si se especificaron partes esperadas, verificarlas
                        if expected_url_parts:
                            for part in expected_url_parts:
                                if part.lower() in new_url.lower():
                                    self.logger.info(f"✅ {description} - Encontrada parte esperada: {part}")
                                    return True
                            
                            self.logger.warning(f"⚠️ {description} - URL cambió pero no contiene partes esperadas")
                            return True  # Aún consideramos exitoso el cambio de URL
                        
                        return True
                
                # Si llegamos aquí, no hubo cambio de URL en el tiempo especificado
                final_url = self.page.url
                self.logger.info(f"📍 URL final: {final_url}")
                self.logger.warning(f"⚠️ {description} - No se detectó cambio de URL después de {timeout/1000}s")
                
                # Si es el último intento, fallamos
                if attempt == retry_attempts - 1:
                    return False
                
                # Esperar un poco antes del siguiente intento
                await asyncio.sleep(2)
                    
            except Exception as e:
                self.logger.error(f"❌ Error esperando {description} (intento {attempt + 1}): {e}")
                if attempt == retry_attempts - 1:
                    return False
                await asyncio.sleep(2)
        
        return False

    async def wait_for_critical_navigation(
        self,
        expected_url_parts: List[str] = None,
        timeout: int = 45000,  # 45 segundos para navegación crítica
        description: str = "navegación crítica",
        retry_attempts: int = 3,
        check_interval: float = 0.5
    ) -> bool:
        """
        Espera navegación crítica con timeouts y reintentos extendidos.
        Útil para navegaciones que pueden tardar más tiempo debido a procesamiento del servidor.
        
        Args:
            expected_url_parts: Partes que deberían estar en la nueva URL
            timeout: Timeout en milisegundos por intento (por defecto 45s)
            description: Descripción para logging
            retry_attempts: Número de intentos de navegación (por defecto 3)
            check_interval: Intervalo entre verificaciones en segundos
            
        Returns:
            True si la navegación fue exitosa, False en caso contrario
        """
        self.logger.info(f"🔥 Iniciando {description} con timeout extendido de {timeout/1000}s")
        
        for attempt in range(retry_attempts):
            if attempt > 0:
                self.logger.info(f"🔄 Reintentando {description} - Intento {attempt + 1}/{retry_attempts}")
                # Actualizar la página antes del reintento
                try:
                    await self.page.reload(wait_until="domcontentloaded", timeout=10000)
                    self.logger.info("🔄 Página recargada antes del reintento")
                except Exception as e:
                    self.logger.warning(f"⚠️ No se pudo recargar la página: {e}")
            else:
                self.logger.info(f"⏳ Esperando {description}...")
            
            try:
                current_url = self.page.url
                self.logger.info(f"📍 URL actual: {current_url}")
                
                # Verificación con intervalo configurable
                max_checks = int(timeout // (check_interval * 1000))
                
                for check in range(max_checks):
                    await asyncio.sleep(check_interval)
                    
                    new_url = self.page.url
                    
                    # Verificar si cambió la URL
                    if new_url != current_url:
                        self.logger.info(f"📍 Nueva URL: {new_url}")
                        elapsed_time = (check + 1) * check_interval
                        self.logger.info(f"✅ {description} - URL cambió exitosamente en {elapsed_time:.1f}s")
                        
                        # Si se especificaron partes esperadas, verificarlas
                        if expected_url_parts:
                            for part in expected_url_parts:
                                if part.lower() in new_url.lower():
                                    self.logger.info(f"✅ {description} - Encontrada parte esperada: {part}")
                                    return True
                            
                            self.logger.warning(f"⚠️ {description} - URL cambió pero no contiene partes esperadas")
                            return True  # Aún consideramos exitoso el cambio de URL
                        
                        return True
                
                # Si llegamos aquí, no hubo cambio de URL en el tiempo especificado
                final_url = self.page.url
                self.logger.info(f"📍 URL final: {final_url}")
                self.logger.warning(f"⚠️ {description} - No se detectó cambio de URL después de {timeout/1000}s")
                
                # Si es el último intento, fallamos
                if attempt == retry_attempts - 1:
                    return False
                
                # Esperar antes del siguiente intento
                wait_before_retry = 3 + (attempt * 2)  # Espera progresiva
                self.logger.info(f"⏸️ Esperando {wait_before_retry}s antes del siguiente intento...")
                await asyncio.sleep(wait_before_retry)
                    
            except Exception as e:
                self.logger.error(f"❌ Error esperando {description} (intento {attempt + 1}): {e}")
                if attempt == retry_attempts - 1:
                    return False
                await asyncio.sleep(3)
        
        return False

    async def click_and_wait_navigation(
        self,
        selector: str,
        expected_url_parts: List[str] = None,
        click_timeout: int = 10000,
        navigation_timeout: int = 30000,
        description: str = "clic y navegación",
        retry_attempts: int = 2
    ) -> bool:
        """
        Realiza un clic y espera a que ocurra navegación con reintentos robustos.
        
        Args:
            selector: Selector del elemento a hacer clic
            expected_url_parts: Partes esperadas en la nueva URL
            click_timeout: Timeout para el clic en milisegundos
            navigation_timeout: Timeout para la navegación en milisegundos
            description: Descripción para logging
            retry_attempts: Número de intentos completos
            
        Returns:
            True si el clic y navegación fueron exitosos, False en caso contrario
        """
        for attempt in range(retry_attempts):
            if attempt > 0:
                self.logger.info(f"🔄 Reintentando {description} - Intento {attempt + 1}/{retry_attempts}")
                # Esperar un poco antes del reintento
                await asyncio.sleep(2)
            
            try:
                # Guardar URL actual antes del clic
                current_url = self.page.url
                self.logger.info(f"📍 URL antes del clic: {current_url}")
                
                # Esperar a que el elemento sea visible y clicable
                element = self.page.locator(selector)
                await element.wait_for(state="visible", timeout=click_timeout)
                await element.wait_for(state="attached", timeout=click_timeout)
                
                # Hacer clic
                await element.click(timeout=click_timeout)
                self.logger.info(f"✅ Clic en {description} exitoso")
                
                # Esperar navegación usando el método mejorado
                navigation_success = await self.wait_for_page_navigation(
                    expected_url_parts=expected_url_parts,
                    timeout=navigation_timeout,
                    description=f"navegación después de {description}",
                    retry_attempts=1  # Ya estamos en un bucle de reintentos
                )
                
                if navigation_success:
                    return True
                
                # Si la navegación falló y no es el último intento, continuar
                if attempt < retry_attempts - 1:
                    self.logger.warning(f"⚠️ Navegación falló para {description}, reintentando...")
                    continue
                
                return False
                
            except Exception as e:
                self.logger.error(f"❌ Error en {description} (intento {attempt + 1}): {e}")
                if attempt == retry_attempts - 1:
                    return False
                await asyncio.sleep(2)
        
        return False

    async def select_from_material_dropdown(
        self,
        dropdown_selector: str,
        option_text: str,
        description: str = "",
        timeout: int = 10000
    ) -> bool:
        """
        Selecciona una opción de un dropdown de Material Design.
        
        Args:
            dropdown_selector: Selector del dropdown (mat-select)
            option_text: Texto de la opción a seleccionar
            description: Descripción para logging
            timeout: Timeout en milisegundos
            
        Returns:
            True si la selección fue exitosa, False en caso contrario
        """
        try:
            desc = description or f"dropdown con opción '{option_text}'"
            self.logger.info(f"🔽 Seleccionando {desc}...")
            
            # Abrir dropdown
            await self.page.click(dropdown_selector, timeout=timeout)
            await asyncio.sleep(0.5)  # Esperar que se abra
            
            # Seleccionar opción
            option_selector = f'mat-option:has-text("{option_text}")'
            await self.page.click(option_selector, timeout=timeout)
            await asyncio.sleep(0.3)  # Esperar que se cierre
            
            self.logger.info(f"✅ {desc} seleccionado exitosamente")
            return True            
        except Exception as e:
            self.logger.error(f"❌ Error seleccionando {desc}: {e}")
            return False

    async def fill_multiple_fields(
        self,
        field_map: Dict[str, str],
        description: str = "campos",
        timeout: int = 5000,
        delay_between_fields: float = 0.3
    ) -> bool:
        """
        Llena múltiples campos de formulario.
        
        Args:
            field_map: Diccionario {selector: valor} de campos a llenar
            description: Descripción para logging
            timeout: Timeout para cada campo
            delay_between_fields: Tiempo de espera entre campos
            
        Returns:
            True si todos los campos se llenaron exitosamente, False en caso contrario
        """
        self.logger.info(f"📝 Llenando {description}...")
        
        try:
            for selector, value in field_map.items():
                try:
                    # Usar locator().first para evitar problemas con selectores CSS
                    await self.page.locator(selector).first.fill(str(value), timeout=timeout)
                    self.logger.info(f"✅ Campo '{selector}' llenado con '{value}'")
                except Exception as e:
                    self.logger.error(f"❌ Error llenando campo '{selector}' con valor '{value}': {e}")
                    return False
                
                if delay_between_fields:
                    await asyncio.sleep(delay_between_fields)
            
            self.logger.info(f"✅ {description} llenados exitosamente")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error llenando {description}: {e}")
            return False

    async def retry_action(
        self,
        action_func: Callable,
        description: str,
        max_attempts: int = 5,
        delay_seconds: float = 1.0,
        *args,
        **kwargs
    ) -> bool:
        """
        Ejecuta una acción con reintentos automáticos.
        
        Args:
            action_func: Función async a ejecutar (ej: self.safe_click, self.is_visible_safe)
            description: Descripción de la acción para logging
            max_attempts: Número máximo de intentos
            delay_seconds: Segundos de espera entre intentos
            *args, **kwargs: Argumentos para la función
            
        Returns:
            bool: True si la acción fue exitosa, False en caso contrario
        """
        
        for attempt in range(1, max_attempts + 1):
            try:
                self.logger.info(f"🔄 [{description}] Intento {attempt}/{max_attempts}...")
                
                # Ejecutar la acción
                result = await action_func(*args, **kwargs)
                
                if result:
                    self.logger.info(f"✅ [{description}] Exitoso en intento {attempt}")
                    return True
                    
                # Si no es el último intento, esperar
                if attempt < max_attempts:
                    self.logger.warning(f"⚠️ [{description}] Intento {attempt} fallido. Esperando {delay_seconds}s...")
                    await asyncio.sleep(delay_seconds)
                    
            except Exception as e:
                self.logger.warning(f"⚠️ [{description}] Error en intento {attempt}: {e}")
                if attempt < max_attempts:
                    await asyncio.sleep(delay_seconds)
                else:
                    self.logger.error(f"❌ [{description}] Falló después de {max_attempts} intentos")
                    
        self.logger.error(f"❌ [{description}] No se pudo completar después de {max_attempts} intentos")
        return False
    
    
    async def fill_and_verify_field_flexible(
        self, 
        selector: str, 
        value: str, 
        field_name: str = "",
        max_attempts: int = 3,
        timeout: int = 5000
    ) -> bool:
        """
        Llena un campo y verifica que el valor se haya establecido correctamente.
        Incluye validación flexible para campos de fecha.
        
        Args:
            selector: Selector CSS del campo
            value: Valor a insertar
            field_name: Nombre del campo para logging
            max_attempts: Número máximo de intentos
            timeout: Timeout en milisegundos
            
        Returns:
            True si el campo se llenó y verificó correctamente
        """
        field_desc = field_name or f"campo '{selector}'"
        
        for attempt in range(1, max_attempts + 1):
            try:
                self.logger.info(f"📝 {field_desc} - Intento {attempt}/{max_attempts}")
                
                # Limpiar y llenar el campo
                await self.page.fill(selector, "", timeout=timeout)
                await self.page.wait_for_timeout(200)
                await self.page.fill(selector, value, timeout=timeout)
                await self.page.wait_for_timeout(300)
                
                # Verificar el valor
                actual_value = await self.page.input_value(selector)
                  # Detectar si es campo de fecha
                is_date_field = (
                    "placeholder='DD/MM/YYYY'" in selector or 
                    "aria-labelledby='paper-input-label-27'" in selector or
                    ("aria-labelledby" in selector and "fecha" in selector.lower()) or
                    "vigencia" in field_name.lower() or
                    "fecha" in field_name.lower()
                )
                
                if is_date_field:
                    # Validación flexible para fechas
                    if self._validate_date_field(value, actual_value):
                        self.logger.info(f"✅ {field_desc} verificado: '{actual_value}' (formato de fecha aceptado)")
                        return True
                else:
                    # Validación exacta para otros campos
                    if actual_value == value:
                        self.logger.info(f"✅ {field_desc} verificado: '{actual_value}'")
                        return True
                
                self.logger.warning(f"⚠️ {field_desc} - Esperado: '{value}', Actual: '{actual_value}'")
                
                if attempt < max_attempts:
                    self.logger.info(f"🔄 {field_desc} - Reintentando...")
                    await self.page.wait_for_timeout(500)
                        
            except Exception as e:
                self.logger.warning(f"⚠️ {field_desc} - Error en intento {attempt}: {e}")
                if attempt < max_attempts:
                    await self.page.wait_for_timeout(500)
        
        self.logger.error(f"❌ {field_desc} - No se pudo llenar después de {max_attempts} intentos")
        return False

    def _validate_date_field(self, expected: str, actual: str) -> bool:
        """
        Valida campos de fecha con múltiples formatos aceptados.
        
        Args:
            expected: Valor esperado (puede ser DDMMYYYY o DD/MM/YYYY)
            actual: Valor actual del campo
            
        Returns:
            True si los valores coinciden en cualquier formato válido
        """
        # Normalizar valores removiendo espacios
        expected_clean = expected.strip()
        actual_clean = actual.strip()
        
        # Verificación directa
        if actual_clean == expected_clean:
            return True
          # Si el expected es formato DDMMYYYY (8 dígitos)
        if len(expected_clean) == 8 and expected_clean.isdigit():
            # Formato con barras: DD/MM/YYYY
            expected_formatted = f"{expected_clean[:2]}/{expected_clean[2:4]}/{expected_clean[4:]}"
            if actual_clean == expected_formatted:
                return True
        
        # Verificación flexible: comparar solo números
        actual_numbers = ''.join(filter(str.isdigit, actual_clean))
        expected_numbers = ''.join(filter(str.isdigit, expected_clean))
        
        return actual_numbers == expected_numbers

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # FUNCIONES PARA ALLIANZ
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    async def wait_for_element_with_text(self, text: str, timeout: Optional[int] = None) -> bool:
        """Espera un texto en el main o en el iframe."""
        lower = text.lower()
        timeout = timeout or Constants.DEFAULT_TIMEOUT
        self.logger.info(f"⏳ Esperando texto '{text}' (<= {timeout/1000}s)...")
        fn = f"""
        () => {{
            const t = '{lower}';
            const exists = doc => Array.from(doc.querySelectorAll('*'))
                .some(el => el.textContent?.toLowerCase().includes(t) && el.offsetParent);
            return exists(document) || (() => {{
                const f = document.querySelector('{self.IFRAME_SELECTOR}');
                return f?.contentDocument && exists(f.contentDocument);
            }})();
        }}"""
        try:
            await self.page.wait_for_function(fn, timeout=timeout)
            self.logger.info(f"✅ Texto '{text}' encontrado")
            return True
        except Exception as e:
            self.logger.error(f"❌ Timeout buscando texto '{text}': {e}")
            return False

    async def wait_for_iframe_content(self, timeout: Optional[int] = None) -> bool:
        """Espera a que el iframe tenga hijos en su body."""
        timeout = timeout or Constants.DEFAULT_TIMEOUT
        self.logger.info(f"⏳ Esperando contenido de iframe (<= {timeout/1000}s)...")
        try:
            await self.page.wait_for_function(
                f"() => document.querySelector('{self.IFRAME_SELECTOR}')?.contentDocument?.body?.children.length > 0",
                timeout=timeout
            )
            self.logger.info("✅ Contenido de iframe cargado")
            return True
        except Exception as e:
            self.logger.error(f"❌ Timeout cargando iframe: {e}")
            return False

    async def wait_for_element_by_id_in_iframe(self, element_id: str, timeout: Optional[int] = None) -> bool:
        """Espera un elemento por ID dentro del iframe."""
        timeout = timeout or Constants.DEFAULT_TIMEOUT
        sel = f"#{element_id}"
        self.logger.info(f"⏳ Esperando '{sel}' en iframe (<= {timeout/1000}s)...")
        try:
            await self.page.wait_for_function(
                f"() => !!document.querySelector('{self.IFRAME_SELECTOR}')"
                f"?.contentDocument.querySelector('{sel}')?.offsetParent",
                timeout=timeout
            )
            self.logger.info(f"✅ Elemento '{sel}' en iframe encontrado")
            return True
        except Exception as e:
            self.logger.error(f"❌ Timeout esperando '{sel}' en iframe: {e}")
            return False

    async def evaluate(self, script: str) -> Any:
        """Ejecuta un script en el contexto de la página."""
        try:
            return await self.page.evaluate(script)
        except Exception as e:
            self.logger.error(f"❌ Error evaluate(): {e}")
            return False
        
    async def _retry_evaluate(
        self,
        script: str,
        validate: Callable[[Any], bool],
        attempts: int = 5,
        interval_ms: int = 1000,
        log_tag: str = ""
    ) -> Any:
        """
        Ejecuta `script` en la página hasta que `validate(result)` sea True,
        esperando `interval_ms` milisegundos entre intentos, hasta `attempts` veces.
        Devuelve el resultado válido o None si no se logra.
        """
        for i in range(attempts):
            result = await self.evaluate(script)
            if validate(result):
                self.logger.info(f"✅ [{log_tag}] validado en intento {i+1}: {result}")
                return result
            self.logger.info(f"⏳ [{log_tag}] intento {i+1}/{attempts} sin éxito: {result}")
            await self.page.wait_for_timeout(interval_ms)
        self.logger.error(f"❌ [{log_tag}] fallo tras {attempts} intentos")
        return None

    async def click_with_js(self, script: str, success_msg: str) -> bool:
        """Click via JS y log."""
        result = await self.evaluate(script)
        if result:
            self.logger.info(success_msg)
            return True
        return False

    async def wait_for_load_state_with_retry(self, state: str = "networkidle", timeout: int = 30000):
        """Espera load_state con retry silencioso."""
        try:
            await self.page.wait_for_load_state(state, timeout=timeout)
        except PlaywrightTimeout:
            self.logger.warning(f"⚠️ Timeout load_state='{state}', continuando...")

    async def safe_click(self, selector: str, timeout: int = 10000) -> bool:
        """Click normal con manejo de error."""
        try:
            await self.page.click(selector, timeout=timeout)
            return True
        except Exception as e:
            self.logger.error(f"❌ safe_click('{selector}'): {e}")
            return False

    async def safe_fill(self, selector: str, value: str, timeout: int = 10000) -> bool:
        """Fill normal con manejo de error."""
        try:
            await self.page.fill(selector, value, timeout=timeout)
            return True
        except Exception as e:
            self.logger.error(f"❌ safe_fill('{selector}'): {e}")
            return False

    async def wait_for_selector_safe(self, selector: str, state: str = "visible", timeout: int = 15000) -> bool:
        """Wait for selector con manejo de error."""
        self.logger.info(f"⏳ Esperando selector '{selector}' ({state}) <={timeout/1000}s...")
        try:
            await self.page.wait_for_selector(selector, state=state, timeout=timeout)
            self.logger.info(f"✅ Selector '{selector}' {state}")
            return True
        except Exception as e:
            self.logger.error(f"❌ wait_for_selector_safe('{selector}'): {e}")
            return False

    async def is_visible_safe(self, selector: str, timeout: int = 5000) -> bool:
        """Comprueba visibilidad con manejo de error."""
        try:
            return await self.page.is_visible(selector, timeout=timeout)
        except Exception:
            return False

    # ————————————————
    # Métodos genéricos para iframe:
    # ————————————————

    async def click_in_frame(self, selector: str, description: str, timeout: int = 15000) -> bool:
        """Espera y hace clic en un selector dentro del iframe."""
        self.logger.info(f"⏳ Esperando {description} en iframe...")
        try:
            el = self._frame.locator(selector)
            await el.wait_for(timeout=timeout)
            await el.click()
            self.logger.info(f"✅ Clic en {description} exitoso!")
            return True
        except Exception as e:
            self.logger.error(f"❌ click_in_frame('{selector}'): {e}")
            return False

    async def fill_in_frame(self, selector: str, value: str, description: str, timeout: int = 15000) -> bool:
        """Espera y rellena un input dentro del iframe."""
        self.logger.info(f"⏳ Esperando campo {description} en iframe...")
        try:
            el = self._frame.locator(selector)
            await el.wait_for(timeout=timeout)
            await el.fill(value)
            self.logger.info(f"✅ Campo {description} = '{value}'")
            return True
        except Exception as e:
            self.logger.error(f"❌ fill_in_frame('{selector}'): {e}")
            return False

    async def select_in_frame(self, selector: str, value: str, description: str, timeout: int = 15000) -> bool:
        """Espera y selecciona un valor de dropdown dentro del iframe."""
        self.logger.info(f"⏳ Esperando dropdown {description} en iframe...")
        try:
            el = self._frame.locator(selector)
            await el.wait_for(timeout=timeout)
            await el.select_option(value)
            # disparamos change
            await el.evaluate("e => e.dispatchEvent(new Event('change',{bubbles:true}))")
            self.logger.info(f"✅ {description} seleccionado: {value}")
            return True
        except Exception as e:
            self.logger.error(f"❌ select_in_frame('{selector}'): {e}")
            return False

    async def select_by_text_in_frame(self, selector: str, text: str, description: str, timeout: int = 15000) -> bool:
        """Espera y selecciona un valor de dropdown por texto dentro del iframe."""
        self.logger.info(f"⏳ Esperando dropdown {description} en iframe...")
        try:
            el = self._frame.locator(selector)
            await el.wait_for(timeout=timeout)
            await el.select_option(label=text)
            # disparamos change
            await el.evaluate("e => e.dispatchEvent(new Event('change',{bubbles:true}))")
            self.logger.info(f"✅ {description} seleccionado: {text}")
            return True
        except Exception as e:
            self.logger.error(f"❌ select_by_text_in_frame('{selector}'): {e}")
            return False

    async def click_by_text_in_frame(self, text: str, description: str, timeout: int = 15000) -> bool:
        """Espera y hace clic en un elemento por texto exacto dentro del iframe."""
        self.logger.info(f"⏳ Esperando texto exacto '{text}' en iframe...")
        try:
            # Usar exact=True para coincidir exactamente con el texto
            el = self._frame.get_by_text(text, exact=True)
            await el.wait_for(timeout=timeout)
            await el.click()
            self.logger.info(f"✅ Clic en {description} exitoso!")
            return True
        except Exception as e:
            self.logger.error(f"❌ click_by_text_in_frame('{text}'): {e}")
            return False

    async def verify_element_value_in_frame(
        self, 
        selector: str, 
        description: str, 
        condition: str = "value_not_empty",
        attempts: int = 5,
        interval_ms: int = 1000,
        immediate_check: bool = True
    ) -> bool:
        """
        Verifica que un elemento dentro del iframe cumpla una condición específica.
        
        Args:
            selector (str): Selector CSS del elemento a verificar
            description (str): Descripción para logging
            condition (str): Tipo de condición - "value_not_empty", "has_method", "is_visible", etc.
            attempts (int): Número de intentos
            interval_ms (int): Intervalo entre intentos en ms
            immediate_check (bool): Si hacer verificación inmediata antes de retry
            
        Returns:
            bool: True si la verificación fue exitosa
        """
        self.logger.info(f"🔍 Verificando {description}...")
        
        # Script base que busca el elemento en iframe
        base_script = f"""
        (() => {{
            const iframe = document.querySelector('{self.IFRAME_SELECTOR}');
            if (!iframe) return null;
            const element = iframe.contentDocument.querySelector('{selector}');
            if (!element) return null;
        """
        
        # Diferentes condiciones de verificación
        if condition == "value_not_empty":
            condition_script = """
            if (element.value && element.value.trim() !== '' && element.value !== '0') {
                return element.value;
            }
            return null;
            """
        elif condition == "has_method_getValue":
            condition_script = """
            return {
                hasGetValue: typeof element.getValue === 'function',
                ready: element.offsetParent !== null
            };
            """
        elif condition == "is_visible":
            condition_script = """
            return element.offsetParent !== null;
            """
        else:
            # Condición personalizada
            condition_script = f"""
            {condition}
            """
        
        script = base_script + condition_script + "\n})();"
        
        # Verificación inmediata si está habilitada
        if immediate_check:
            immediate = await self.evaluate(script)
            if self._validate_verification_result(immediate, condition):
                self.logger.info(f"✅ {description} verificado inmediatamente: {immediate}")
                return True
        
        # Retry con _retry_evaluate
        result = await self._retry_evaluate(
            script,
            validate=lambda r: self._validate_verification_result(r, condition),
            attempts=attempts,
            interval_ms=interval_ms,
            log_tag=description
        )
        return bool(result)
    
    def _validate_verification_result(self, result, condition: str) -> bool:
        """Valida el resultado de la verificación según la condición."""
        if condition == "value_not_empty":
            return bool(result)
        elif condition == "has_method_getValue":
            return bool(result and result.get('hasGetValue') and result.get('ready'))
        elif condition == "is_visible":
            return bool(result)
        else:
            return bool(result)