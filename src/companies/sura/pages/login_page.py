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

    async def navigate_to_login(self) -> bool:
        """Navega a la página de login de Sura."""
        self.logger.info("🌐 Navegando a página de login Sura...")
        try:
            await self.page.goto(self.config.LOGIN_URL)
            
            # Esperar a que el formulario de login esté disponible (no networkidle que es lento)
            await self.page.wait_for_selector(self.TIPO_DOCUMENTO_SELECT, timeout=10000)
            self.logger.info("✅ Página de login Sura cargada correctamente")
            return True
                
        except Exception as e:
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
                
                # Seleccionar la opción
                await self.page.select_option(self.TIPO_DOCUMENTO_SELECT, tipo_doc)
                
                # Esperar un momento para que se procese la selección
                await self.page.wait_for_timeout(500)
                
                # Verificar que la selección se realizó correctamente
                if await self._verify_tipo_documento_selected(tipo_doc):
                    self.logger.info(f"✅ Tipo de documento seleccionado correctamente: {tipo_doc}")
                    return True
                else:
                    self.logger.warning(f"⚠️ Intento {intento} falló - Tipo de documento no se seleccionó correctamente")
                    if intento < max_intentos:
                        self.logger.info(f"🔄 Reintentando en 1 segundo...")
                        await self.page.wait_for_timeout(1000)
                    
            except Exception as e:
                self.logger.warning(f"⚠️ Error en intento {intento}: {e}")
                if intento < max_intentos:
                    self.logger.info(f"🔄 Reintentando en 1 segundo...")
                    await self.page.wait_for_timeout(1000)
                else:
                    self.logger.exception(f"❌ Error final seleccionando tipo de documento después de {max_intentos} intentos: {e}")
        
        self.logger.error(f"❌ No se pudo seleccionar el tipo de documento después de {max_intentos} intentos")
        return False

    async def _verify_tipo_documento_selected(self, expected_tipo: str) -> bool:
        """Verifica que el tipo de documento se haya seleccionado correctamente."""
        try:
            # Obtener el valor actual del select - NO usar f-string con JavaScript
            current_value = await self.page.evaluate("""
                () => {
                    const select = document.querySelector('select[name="ctl00$ContentMain$suraType"]');
                    return select ? select.value : '';
                }
            """)
            
            # Verificar que el valor coincida con el esperado
            is_selected = current_value == expected_tipo
            
            if is_selected:
                self.logger.info(f"✅ Verificación exitosa - Tipo de documento: {current_value}")
            else:
                self.logger.warning(f"⚠️ Verificación falló - Esperado: {expected_tipo}, Actual: {current_value}")
            
            return is_selected
            
        except Exception as e:
            self.logger.error(f"❌ Error verificando tipo de documento: {e}")
            return False
    
    async def fill_virtual_keyboard_password(self, contrasena: str) -> bool:
        """Llena la contraseña usando el teclado virtual de Sura."""
        self.logger.info("🔐 Llenando contraseña con teclado virtual...")
        
        try:
            # Hacer clic en el campo de contraseña para activar el teclado virtual
            await self.page.click(self.CONTRASENA_INPUT)
            self.logger.info("📱 Campo de contraseña activado")            # Esperar a que aparezca el teclado virtual (usando constante)
            await self.page.wait_for_selector(self.VIRTUAL_KEYBOARD, timeout=Constants.SURA_KEYBOARD_APPEAR_TIMEOUT)
            self.logger.info("⌨️ Teclado virtual detectado")
            
            # Usar método JavaScript directamente (más confiable para Sura)
            self.logger.info("🔧 Usando método JavaScript para teclado virtual...")
            if not await self._try_javascript_clicks(contrasena):
                self.logger.error("❌ Método JavaScript falló")
                return False
            
            # Verificar que se hayan ingresado todos los dígitos
            if not await self._verify_password_length(contrasena):
                return False
            
            self.logger.info(f"✅ Contraseña completa ingresada: {len(contrasena)} dígitos")
            
            # Hacer clic en el botón de aceptar (✔)
            self.logger.info("✅ Confirmando contraseña...")
            await self.page.click(self.KEYBOARD_ACCEPT)
            
            # Esperar a que se cierre el teclado virtual (usando constante)
            try:
                await self.page.wait_for_selector(self.VIRTUAL_KEYBOARD, state='hidden', timeout=Constants.SURA_KEYBOARD_HIDE_TIMEOUT)
            except:
                self.logger.warning("⚠️ Teclado virtual no se ocultó completamente, continuando...")
            
            self.logger.info("🎉 Contraseña ingresada exitosamente con teclado virtual")
            return True
            
        except Exception as e:
            self.logger.exception(f"❌ Error usando teclado virtual: {e}")            
            return False

    async def _try_javascript_clicks(self, contrasena: str) -> bool:
        """Intenta hacer clic usando JavaScript con eventos completos de mouse (fallback)."""
        try:
            for i, digito in enumerate(contrasena):
                if not digito.isdigit():
                    self.logger.error(f"❌ Carácter inválido en contraseña (solo números permitidos)")
                    return False
                
                self.logger.info(f"🔢 Haciendo clic JS {i+1}/{len(contrasena)}")
                
                # Usar JavaScript optimizado (constante de clase)
                result = await self.page.evaluate(self._CLICK_DIGIT_JS, digito)
                if not result:
                    self.logger.error(f"❌ No se pudo hacer clic en el botón del teclado")
                    return False
                
                # Esperar entre clics (usando constante)
                await self.page.wait_for_timeout(Constants.SURA_CLICK_DELAY)
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Método JavaScript falló: {e}")
            return False

    async def _verify_password_length(self, expected_password: str) -> bool:
        """Verifica que la contraseña tenga la longitud correcta."""
        try:
            # Primero intentar leer del campo real (más directo)
            try:
                current_value = await self.page.input_value(self.CONTRASENA_INPUT)
                if current_value and len(current_value) == len(expected_password):
                    return True
            except:
                # Si falla, usar método JavaScript como fallback
                pass
            
            # Fallback: usar JavaScript para leer del teclado virtual
            current_value = await self.page.evaluate(self._GET_KEYBOARD_VALUE_JS)
            
            if len(current_value) != len(expected_password):
                self.logger.error(f"❌ Contraseña no coincide. Esperado: {len(expected_password)} dígitos, Actual: {len(current_value)} dígitos")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error verificando longitud de contraseña: {e}")
            return False

    async def fill_credentials(self, usuario: str, contrasena: str) -> bool:
        """Llena las credenciales de login."""
        self.logger.info("📝 Llenando credenciales...")
        
        try:
            # Llenar número de documento
            if not await self.safe_fill(self.NUMERO_DOCUMENTO_INPUT, usuario):
                self.logger.error("❌ Error llenando número de documento")
                return False
            
            # Llenar contraseña usando el teclado virtual
            if not await self.fill_virtual_keyboard_password(contrasena):
                self.logger.error("❌ Error llenando contraseña con teclado virtual")
                return False
            
            self.logger.info("✅ Credenciales llenadas correctamente")
            return True
            
        except Exception as e:
            self.logger.exception(f"❌ Error llenando credenciales: {e}")
            return False

    async def verify_form_completion(self) -> bool:
        """Verifica que todos los campos del formulario estén completos antes de enviar."""
        self.logger.info("🔍 Verificando que todos los campos estén completos...")
        
        try:
            # Verificar tipo de documento
            tipo_documento_value = await self.page.evaluate("""
                () => {
                    const select = document.querySelector('select[name="ctl00$ContentMain$suraType"]');
                    return select ? select.value : '';
                }
            """)
            if not tipo_documento_value or tipo_documento_value == "":
                self.logger.error("❌ Tipo de documento no seleccionado")
                return False
            self.logger.info(f"✅ Tipo de documento: {tipo_documento_value}")
            
            # Verificar número de documento
            numero_documento_value = await self.page.input_value(self.NUMERO_DOCUMENTO_INPUT)
            if not numero_documento_value or numero_documento_value.strip() == "":
                self.logger.error("❌ Número de documento vacío")
                return False
            self.logger.info(f"✅ Número de documento: {numero_documento_value}")
            
            # Verificar contraseña (verificar que el campo tenga valor)
            # Nota: no podemos leer el valor real de la contraseña por seguridad
            contrasena_filled = await self.page.evaluate("""
                () => {
                    const passwordField = document.querySelector('input[name="suraPassword"]');
                    return passwordField && passwordField.value && passwordField.value.length > 0;
                }
            """)
            if not contrasena_filled:
                self.logger.error("❌ Contraseña no ingresada")
                return False
            self.logger.info("✅ Contraseña ingresada")
            self.logger.info("🎯 Todos los campos verificados correctamente")
            return True
            
        except Exception as e:
            self.logger.exception(f"❌ Error verificando campos del formulario: {e}")
            return False

    async def submit_login(self) -> bool:
        """Envía el formulario de login."""
        self.logger.info("🚀 Enviando formulario de login...")
        try:
            # Verificar que todos los campos estén completos antes de enviar
            if not await self.verify_form_completion():
                self.logger.error("❌ Formulario incompleto, no se puede enviar")
                return False
            
            if not await self.safe_click(self.SUBMIT_BUTTON):
                self.logger.error("❌ Error haciendo clic en submit")
                return False
            
            # Esperar solo lo mínimo necesario para que se procese el clic
            await self.page.wait_for_timeout(500)
            self.logger.info("✅ Formulario de login enviado")
            return True
        except Exception as e:
            self.logger.exception(f"❌ Error enviando formulario: {e}")
            return False

    async def verify_login_success(self) -> bool:
        """Verifica si el login fue exitoso."""
        self.logger.info("🔍 Verificando login exitoso...")
        
        try:
            await self.page.wait_for_timeout(1000)  # Reducir espera a 1 segundo
            
            current_url = self.page.url
            self.logger.info(f"📍 URL actual después del login: {current_url}")
            
            # Verificar si estamos en la página de asesores (login exitoso)
            if "asesores.segurossura.com.co" in current_url:
                self.logger.info("✅ Login verificado exitosamente")
                return True
            else:
                self.logger.error("❌ Login no exitoso - no se redirigió correctamente")
                return False
                
        except Exception as e:
            self.logger.exception(f"❌ Error verificando login: {e}")
            return False

    async def login(self, usuario: str, contrasena: str) -> bool:
        """Realiza el proceso completo de login en Sura."""
        self.logger.info("🔑 Iniciando proceso de login en Sura...")
        
        try:
            # Paso 1: Navegar a la página de login
            if not await self.navigate_to_login():
                return False
            
            # Paso 2: Seleccionar tipo de documento
            if not await self.select_tipo_documento():
                return False
            
            # Paso 3: Llenar credenciales
            if not await self.fill_credentials(usuario, contrasena):
                return False
            
            # Paso 4: Enviar formulario (incluye verificación automática)
            if not await self.submit_login():
                return False
            
            # Paso 5: Verificar login exitoso
            if not await self.verify_login_success():
                return False
            
            self.logger.info("🎉 Login en Sura completado exitosamente")
            return True
            
        except Exception as e:
            self.logger.exception(f"❌ Error en proceso de login Sura: {e}")
            return False
