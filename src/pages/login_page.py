from playwright.async_api import Page
from .base_functions import BasePage

class LoginPage(BasePage):
    """Página de login con sus selectores y métodos específicos."""
    
    # URLs
    LOGIN_URL = "https://www.allia2net.com.co/ngx-epac/private/home"
    
    # Selectores
    USERNAME_INPUT = "input[name='username']"
    PASSWORD_INPUT = "input[name='password']"
    SUBMIT_BUTTON = "button[type='submit']"
    
    def __init__(self, page: Page):
        super().__init__(page)

    async def navigate_to_login(self):
        """Navega a la página de login."""
        print("🌐 Navegando a página de login...")
        await self.page.goto(self.LOGIN_URL)

    async def login(self, usuario: str, contrasena: str) -> bool:
        """Realiza el proceso de login."""
        print("🔑 Iniciando login...")
        
        try:
            await self.navigate_to_login()
            
            # Llenar campos
            if not await self.safe_fill(self.USERNAME_INPUT, usuario):
                print("❌ Error llenando usuario")
                return False
                
            if not await self.safe_fill(self.PASSWORD_INPUT, contrasena):
                print("❌ Error llenando contraseña")
                return False
            
            # Hacer clic en submit
            if not await self.safe_click(self.SUBMIT_BUTTON):
                print("❌ Error haciendo clic en submit")
                return False
            
            # Esperar a que cargue
            await self.wait_for_load_state_with_retry("networkidle")
            print("✅ Login completado")
            return True
            
        except Exception as e:
            print(f"❌ Error en login: {e}")
            return False
