"""Página de login específica para Sura."""

from playwright.async_api import Page
from ....shared.base_page import BasePage
from ....config.sura_config import SuraConfig
from ....core.constants import Constants

class LoginPage(BasePage):
    """Página de login con sus selectores y métodos específicos para Sura."""
    
    # Selectores específicos de Sura
    TIPO_DOCUMENTO_SELECT = "select[name='ctl00$ContentMain$suraType']"
    NUMERO_DOCUMENTO_INPUT = "input[name='suraName']"
    CONTRASENA_INPUT = "input[name='suraPassword']"
    SUBMIT_BUTTON = "input[type='button'][id='session-internet']"
    
    # Selectores del teclado virtual
    VIRTUAL_KEYBOARD = ".ui-keyboard"
    KEYBOARD_ACCEPT = "button[data-value='✔']"
    KEYBOARD_BACKSPACE = "button[data-value='⌫']"
    
    # JavaScript optimizado para hacer clic en dígitos del teclado virtual
    _CLICK_DIGIT_JS = """
    (digit) => {
        const keyboard = document.querySelector('.ui-keyboard');
        const button = keyboard ? keyboard.querySelector(`button[data-value="${digit}"]`) : null;
        
        if (button) {
            const mouseDownEvent = new MouseEvent('mousedown', { bubbles: true, cancelable: true, view: window });
            const mouseUpEvent = new MouseEvent('mouseup', { bubbles: true, cancelable: true, view: window });
            const clickEvent = new MouseEvent('click', { bubbles: true, cancelable: true, view: window });
            
            button.dispatchEvent(mouseDownEvent);
            setTimeout(() => {
                button.dispatchEvent(mouseUpEvent);
                button.dispatchEvent(clickEvent);
            }, 50);
            
            return true;
        }
        return false;
    }
    """
    
    # JavaScript para verificar el valor actual en el teclado virtual
    _GET_KEYBOARD_VALUE_JS = """
    () => {
        const keyboard = document.querySelector('.ui-keyboard');
        const inputInKeyboard = keyboard ? keyboard.querySelector('input[name="suraPassword"]') : null;
        return inputInKeyboard ? inputInKeyboard.value : '';
    }
    """

    def __init__(self, page: Page):
        super().__init__(page, 'sura')
        self.config = SuraConfig()    
        
    # ────────────────────────────────────────────────

    async def _get_value(self, selector: str) -> str:
        """Devuelve el .value de un elemento dado su selector CSS."""
        return await self.get_element_value(selector, "value")

    async def _is_password_entered(self) -> bool:
        """Comprueba si el campo de contraseña ya tiene valor."""
        value = await self._get_value(self.CONTRASENA_INPUT)
        return bool(value)
    
    # ────────────────────────────────────────────────

    async def navigate_to_login(self) -> bool:
        """Navega a la página de login de Sura o detecta si ya está logueado."""
        self.logger.info("🌐 Navegando a página de login Sura...")
        try:
            await self.page.goto(self.config.LOGIN_URL)
            
            # Esperar un poco para que la página cargue completamente
            await self.page.wait_for_timeout(2000)
            current_url = self.page.url
            
            # Verificar si ya está logueado (perfil persistente)
            if "asesores.segurossura.com.co" in current_url:
                self.logger.info("✅ ¡Ya estás logueado! (sesión activa desde perfil persistente)")
                self.logger.info(f"📍 URL actual: {current_url}")
                return True
            
            # Si no está logueado, esperar a que aparezcan los elementos de login
            await self.page.wait_for_selector(self.TIPO_DOCUMENTO_SELECT, timeout=10000)
            self.logger.info("✅ Página de login Sura cargada correctamente")
            return True
            
        except Exception as e:
            # Verificar una vez más si ya está logueado por si hay un redirect lento
            current_url = self.page.url
            if "asesores.segurossura.com.co" in current_url:
                self.logger.info("✅ ¡Ya estás logueado! (detectado después de error inicial)")
                self.logger.info(f"📍 URL actual: {current_url}")
                return True
            
            self.logger.exception(f"❌ Error navegando a login Sura: {e}")
            return False

    async def select_tipo_documento(self, tipo: str = None) -> bool:
        """Selecciona el tipo de documento con reintentos automáticos."""
        tipo_doc = tipo or self.config.TIPO_DOCUMENTO_LOGIN
        self.logger.info(f"📋 Seleccionando tipo de documento: {tipo_doc}")
        max_intentos = 5

        for intento in range(1, max_intentos + 1):
            try:
                self.logger.info(f"🔄 Intento {intento}/{max_intentos} - Seleccionando tipo de documento")
                await self.page.select_option(self.TIPO_DOCUMENTO_SELECT, tipo_doc)
                await self.page.wait_for_timeout(500)
                if await self._verify_tipo_documento_selected(tipo_doc):
                    self.logger.info(f"✅ Tipo de documento seleccionado correctamente: {tipo_doc}")
                    return True
                self.logger.warning(f"⚠️ Intento {intento} falló")
                if intento < max_intentos:
                    await self.page.wait_for_timeout(1000)
            except Exception as e:
                self.logger.warning(f"⚠️ Error en intento {intento}: {e}")
                if intento < max_intentos:                    
                    await self.page.wait_for_timeout(1000)
                else:
                    self.logger.exception(f"❌ Error final seleccionando tipo de documento: {e}")

        self.logger.error(f"❌ No se pudo seleccionar el tipo de documento después de {max_intentos} intentos")
        return False

    async def _verify_tipo_documento_selected(self, expected_tipo: str) -> bool:
        """Verifica que el tipo de documento se haya seleccionado correctamente."""
        try:
            # Usar función optimizada de la clase base
            return await self.verify_element_value_equals(
                selector=self.TIPO_DOCUMENTO_SELECT,
                expected_value=expected_tipo,
                property_name="value",
                description=f"Tipo de documento ({expected_tipo})"
            )
        except Exception as e:
            self.logger.error(f"❌ Error verificando tipo de documento: {e}")
            return False

    async def fill_virtual_keyboard_password(self, contrasena: str) -> bool:
        """Llena la contraseña usando el teclado virtual de Sura."""
        self.logger.info("🔐 Llenando contraseña con teclado virtual...")
        try:
            await self.page.click(self.CONTRASENA_INPUT)
            self.logger.info("📱 Campo de contraseña activado")
            await self.page.wait_for_selector(self.VIRTUAL_KEYBOARD, timeout=Constants.SURA_KEYBOARD_APPEAR_TIMEOUT)
            self.logger.info("⌨️ Teclado virtual detectado")
            self.logger.info("🔧 Usando método JavaScript para teclado virtual...")
            if not await self._try_javascript_clicks(contrasena):
                self.logger.error("❌ Método JavaScript falló")
                return False
            if not await self._verify_password_length(contrasena):
                return False
            self.logger.info(f"✅ Contraseña completa ingresada: {len(contrasena)} dígitos")
            await self.page.click(self.KEYBOARD_ACCEPT)
            try:
                await self.page.wait_for_selector(self.VIRTUAL_KEYBOARD, state='hidden', timeout=Constants.SURA_KEYBOARD_HIDE_TIMEOUT)
            except:
                self.logger.warning("⚠️ Teclado virtual no se ocultó, continuando...")
            self.logger.info("🎉 Contraseña ingresada exitosamente")
            return True
        except Exception as e:
            self.logger.exception(f"❌ Error usando teclado virtual: {e}")
            return False

    async def _try_javascript_clicks(self, contrasena: str) -> bool:
        """Intenta hacer clic usando JavaScript con eventos completos de mouse (fallback)."""
        try:
            for i, digito in enumerate(contrasena):
                if not digito.isdigit():
                    self.logger.error("❌ Carácter inválido en contraseña (solo números permitidos)")
                    return False
                self.logger.info(f"🔢 Haciendo clic JS {i+1}/{len(contrasena)}")
                result = await self.page.evaluate(self._CLICK_DIGIT_JS, digito)
                if not result:
                    self.logger.error("❌ No se pudo hacer clic en el botón del teclado")
                    return False
                await self.page.wait_for_timeout(Constants.SURA_CLICK_DELAY)
            return True
        except Exception as e:
            self.logger.error(f"❌ Método JavaScript falló: {e}")
            return False

    async def _verify_password_length(self, expected_password: str) -> bool:
        """Verifica que la contraseña tenga la longitud correcta."""
        try:
            current_value = await self._get_value(self.CONTRASENA_INPUT)
            if len(current_value) == len(expected_password):
                return True
            # Fallback: usar JS si fuera necesario
            current_value = await self.page.evaluate(self._GET_KEYBOARD_VALUE_JS)
            if len(current_value) != len(expected_password):
                self.logger.error(f"❌ Contraseña no coincide: esperado {len(expected_password)}, actual {len(current_value)}")
                return False
            return True
        except Exception as e:
            self.logger.error(f"❌ Error verificando longitud de contraseña: {e}")
            return False

    async def fill_credentials(self, usuario: str, contrasena: str) -> bool:
        """Llena las credenciales de login."""
        self.logger.info("📝 Llenando credenciales...")
        try:
            if not await self.safe_fill(self.NUMERO_DOCUMENTO_INPUT, usuario):
                self.logger.error("❌ Error llenando número de documento")
                return False
            if not await self.fill_virtual_keyboard_password(contrasena):
                self.logger.error("❌ Error llenando contraseña")
                return False
            self.logger.info("✅ Credenciales llenadas correctamente")
            return True
        except Exception as e:
            self.logger.exception(f"❌ Error llenando credenciales: {e}")
            return False

    async def verify_and_complete_form(self, usuario: str = None, contrasena: str = None) -> bool:
        """Verifica y completa automáticamente los campos del formulario que estén vacíos."""
        self.logger.info("🔍 Verificando y completando campos del formulario...")
        usuario = usuario or self.config.NUMERO_DOCUMENTO_LOGIN
        contrasena = contrasena or self.config.CONTRASENA_LOGIN
        form_complete = True
        try:
            # Tipo de documento
            tipo_actual = await self._get_value(self.TIPO_DOCUMENTO_SELECT)
            if not tipo_actual:
                self.logger.warning("⚠️ Tipo de documento no seleccionado, completando...")
                if not await self.select_tipo_documento():
                    form_complete = False
            else:
                self.logger.info(f"✅ Tipo de documento ya seleccionado: {tipo_actual}")
            # Número de documento
            num_actual = await self.page.input_value(self.NUMERO_DOCUMENTO_INPUT)
            if not num_actual.strip():
                self.logger.warning("⚠️ Número de documento vacío, completando...")
                if not await self.safe_fill(self.NUMERO_DOCUMENTO_INPUT, usuario):
                    form_complete = False
            else:
                self.logger.info(f"✅ Número de documento ya ingresado: {num_actual}")
            # Contraseña
            if not await self._is_password_entered():
                self.logger.warning("⚠️ Contraseña no ingresada, completando...")
                if not await self.fill_virtual_keyboard_password(contrasena):
                    form_complete = False
            else:
                self.logger.info("✅ Contraseña ya ingresada")
            return form_complete
        except Exception as e:
            self.logger.exception(f"❌ Error verificando formulario: {e}")
            return False

    async def complete_login_with_retries(self, usuario: str, contrasena: str, max_attempts: int = 3) -> bool:
        """Completa el login con reintentos automáticos si el formulario está incompleto."""
        self.logger.info("🔄 Iniciando login con reintentos automáticos...")
        for attempt in range(1, max_attempts + 1):
            self.logger.info(f"🔄 Intento de login {attempt}/{max_attempts}")
            try:
                if await self.verify_and_complete_form(usuario, contrasena):
                    if await self.safe_click(self.SUBMIT_BUTTON):
                        self.logger.info(f"✅ Login enviado en intento {attempt}")
                        await self.page.wait_for_timeout(500)
                        return True
                    else:
                        self.logger.warning(f"⚠️ Error haciendo clic en submit (intento {attempt})")
                if attempt < max_attempts:
                    await self.page.wait_for_timeout(2000)
            except Exception as e:
                self.logger.warning(f"⚠️ Error en intento {attempt}: {e}")
                if attempt < max_attempts:
                    await self.page.wait_for_timeout(2000)
        self.logger.error(f"❌ No se pudo completar el login después de {max_attempts} intentos")
        return False

    async def verify_form_completion(self) -> bool:
        """Verifica que todos los campos del formulario estén completos antes de enviar."""
        self.logger.info("🔍 Verificando que todos los campos estén completos...")
        try:
            if not await self._get_value(self.TIPO_DOCUMENTO_SELECT):
                self.logger.error("❌ Tipo de documento no seleccionado")
                return False
            if not (await self.page.input_value(self.NUMERO_DOCUMENTO_INPUT)).strip():
                self.logger.error("❌ Número de documento vacío")
                return False
            if not await self._is_password_entered():
                self.logger.error("❌ Contraseña no ingresada")
                return False
            self.logger.info("🎯 Todos los campos verificados correctamente")
            return True
        except Exception as e:
            self.logger.exception(f"❌ Error verificando campos del formulario: {e}")
            return False

    async def submit_login(self, usuario: str = None, contrasena: str = None) -> bool:
        """Envía el formulario de login, verificando y completando campos si es necesario."""
        self.logger.info("🚀 Enviando formulario de login...")
        try:
            if not await self.verify_and_complete_form(usuario, contrasena):
                self.logger.error("❌ No se pudieron completar todos los campos")
                return False
            if not await self.safe_click(self.SUBMIT_BUTTON):
                self.logger.error("❌ Error haciendo clic en submit")
                return False
            await self.page.wait_for_timeout(500)
            self.logger.info("✅ Formulario de login enviado")
            return True
        except Exception as e:
            self.logger.exception(f"❌ Error enviando formulario: {e}")
            return False

    async def verify_login_success(self) -> bool:
        """Verifica si el login fue exitoso, manejando MFA si es necesario."""
        self.logger.info("🔍 Verificando login exitoso...")
        try:
            await self.page.wait_for_timeout(1000)
            current_url = self.page.url
            self.logger.info(f"📍 URL actual después del login: {current_url}")
            
            # Verificar si es login exitoso directo
            if "asesores.segurossura.com.co" in current_url:
                self.logger.info("✅ Login verificado exitosamente")
                return True
            
            # Verificar si requiere MFA (autenticación de dos factores)
            if "mfa/process" in current_url:
                self.logger.info("🔐 Detectado MFA (autenticación de dos factores)")
                return await self._handle_mfa()
            
            # Si no redirigió, esperar 3 segundos más y volver a verificar
            self.logger.info("⏳ Aún cargando, esperando 3 segundos más...")
            await self.page.wait_for_timeout(3000)
            current_url = self.page.url
            self.logger.info(f"📍 URL después de espera adicional: {current_url}")
            
            if "asesores.segurossura.com.co" in current_url:
                self.logger.info("✅ Login verificado exitosamente tras espera adicional")
                return True
            elif "mfa/process" in current_url:
                self.logger.info("🔐 Detectado MFA tras espera adicional")
                return await self._handle_mfa()
                
            self.logger.error("❌ Login no exitoso - no se redirigió correctamente")
            return False
        except Exception as e:
            self.logger.exception(f"❌ Error verificando login: {e}")
            return False

    async def _handle_mfa(self) -> bool:
        """Maneja el proceso de autenticación de dos factores con intervención manual."""
        self.logger.info("📱 Iniciando proceso de MFA...")
        self.logger.info("⏸️ PAUSA PARA INTERVENCIÓN MANUAL")
        self.logger.info("=" * 70)
        self.logger.info("🔔 ACCIÓN REQUERIDA:")
        self.logger.info("   1. Ingresa manualmente el código MFA en el navegador")
        self.logger.info("   2. ¡IMPORTANTE! Marca 'Recordar este dispositivo por 8 días'")
        self.logger.info("   3. Haz clic en 'Continuar' o 'Siguiente'")
        self.logger.info("   4. La automatización continuará automáticamente")
        self.logger.info("")
        self.logger.info("💡 Esto evitará que se pida MFA en próximas ejecuciones")
        self.logger.info("=" * 70)
        
        try:
            # Esperar hasta que la URL cambie o hasta 5 minutos máximo
            max_wait_time = 300000  # 5 minutos
            check_interval = 2000   # Revisar cada 2 segundos
            elapsed_time = 0
            
            while elapsed_time < max_wait_time:
                await self.page.wait_for_timeout(check_interval)
                elapsed_time += check_interval
                current_url = self.page.url
                
                # Si ya no está en la página de MFA, verificar si llegó al dashboard
                if "mfa/process" not in current_url:
                    self.logger.info(f"📍 URL cambió a: {current_url}")
                    if "asesores.segurossura.com.co" in current_url:
                        self.logger.info("✅ MFA completado exitosamente")
                        self.logger.info("🎉 Si marcaste 'recordar dispositivo', no volverá a pedirse por 8 días")
                        return True
                    else:
                        self.logger.warning(f"⚠️ URL inesperada después de MFA: {current_url}")
                        # Dar una oportunidad más
                        await self.page.wait_for_timeout(3000)
                        final_url = self.page.url
                        if "asesores.segurossura.com.co" in final_url:
                            self.logger.info("✅ MFA completado exitosamente tras verificación adicional")
                            self.logger.info("🎉 Si marcaste 'recordar dispositivo', no volverá a pedirse por 8 días")
                            return True
                
                # Mostrar progreso cada 30 segundos
                if elapsed_time % 30000 == 0:
                    minutes_elapsed = elapsed_time // 60000
                    self.logger.info(f"⏳ Esperando intervención manual... ({minutes_elapsed} min transcurridos)")
            
            self.logger.error("❌ Tiempo de espera agotado para MFA (5 minutos)")
            return False
            
        except Exception as e:
            self.logger.exception(f"❌ Error durante el proceso de MFA: {e}")
            return False

    async def login(self, usuario: str, contrasena: str) -> bool:
        """Realiza el proceso completo de login en Sura."""
        self.logger.info("🔑 Iniciando proceso de login en Sura...")
        try:
            if not await self.navigate_to_login():
                return False
            
            # Verificar si ya está logueado después de navegar
            current_url = self.page.url
            if "asesores.segurossura.com.co" in current_url:
                self.logger.info("🎉 Ya estás logueado - omitiendo pasos de login")
                return True
            
            # Si no está logueado, proceder con el login normal
            if not await self.select_tipo_documento():
                return False
            if not await self.fill_credentials(usuario, contrasena):
                return False
            if not await self.submit_login(usuario, contrasena):
                self.logger.warning("⚠️ Fallo en submit_login, usando método con reintentos...")
                if not await self.complete_login_with_retries(usuario, contrasena):
                    return False
            if not await self.verify_login_success():
                return False
            self.logger.info("🎉 Login en Sura completado exitosamente")
            return True
        except Exception as e:
            self.logger.exception(f"❌ Error en proceso de login Sura: {e}")
            return False
