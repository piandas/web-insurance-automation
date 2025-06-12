import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


import asyncio
import logging
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
from src.config import Config
from typing import Optional

from pages import LoginPage, DashboardPage, FlotasPage

class AllianzAutomation:
    """Clase principal que orquesta todo el flujo de automatización de Allianz."""
    
    def __init__(self, usuario: Optional[str] = None, contrasena: Optional[str] = None, headless: Optional[bool] = None):
        self.usuario = usuario or Config.USUARIO
        self.contrasena = contrasena or Config.CONTRASENA
        self.headless = Config.HEADLESS if headless is None else headless
        self.browser = None
        self.page = None
        self.playwright = None
        
        # Páginas
        self.login_page = None
        self.dashboard_page = None
        self.flotas_page = None

        # Configuración de logging SOLO consola
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(logging.INFO)
        stream_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
        logging.root.addHandler(stream_handler)
        
        # Logging a archivo
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'LOGS')
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        log_file_path = os.path.join(log_dir, 'log.log')
        if not os.path.exists(log_file_path):
            with open(log_file_path, 'w', encoding='utf-8') as f:
                f.write('# Log de la automatización Allianz\n')
        file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
        logging.root.addHandler(file_handler)
        
        logging.root.setLevel(logging.INFO)
        self.logger = logging.getLogger('allianz')

    async def launch(self):
        """Inicializa Playwright y abre el navegador."""
        self.logger.info("🚀 Lanzando navegador...")
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=self.headless)
        self.page = await self.browser.new_page()
        
        # Inicializar páginas
        self.login_page = LoginPage(self.page)
        self.dashboard_page = DashboardPage(self.page)
        self.flotas_page = FlotasPage(self.page)
        
        self.logger.info("✅ Navegador lanzado y páginas inicializadas")

    async def execute_login_flow(self) -> bool:
        """Ejecuta el flujo de login."""
        self.logger.info("🔐 Ejecutando flujo de login...")
        return await self.login_page.login(self.usuario, self.contrasena)

    async def execute_navigation_flow(self) -> bool:
        """Ejecuta el flujo de navegación al dashboard y flotas."""
        self.logger.info("🧭 Ejecutando flujo de navegación...")
        
        # Navegar a flotas
        if not await self.dashboard_page.navigate_to_flotas():
            self.logger.error("❌ Error navegando a flotas")
            return False
        
        # Enviar formulario si existe
        await self.dashboard_page.submit_application_form()
        return True

    async def execute_flotas_flow(self) -> bool:
        """Ejecuta el flujo específico de flotas."""
        self.logger.info("🚗 Ejecutando flujo de flotas...")
        return await self.flotas_page.execute_flotas_flow()

    async def run_complete_flow(self) -> bool:
        """Ejecuta el flujo completo de automatización."""
        self.logger.info("🎬 Iniciando flujo completo de automatización...")
        
        try:
            # Paso 1: Login
            if not await self.execute_login_flow():
                self.logger.error("❌ Falló el flujo de login")
                return False

            # Paso 2: Navegación
            if not await self.execute_navigation_flow():
                self.logger.error("❌ Falló el flujo de navegación")
                return False

            # Paso 3: Flujo de flotas
            if not await self.execute_flotas_flow():
                self.logger.error("❌ Falló el flujo de flotas")
                return False

            self.logger.info("🎉 ¡PROCESO COMPLETO EJECUTADO EXITOSAMENTE!")
            return True

        except Exception as e:
            self.logger.exception(f"❌ Error en flujo completo: {e}")
            return False

    async def close(self):
        """Cierra el navegador y limpia recursos."""
        self.logger.info("🔒 Cerrando navegador...")
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        self.logger.info("✅ Recursos liberados")

async def main():
    """Función principal para ejecutar la automatización."""
    logging.info("🚀 Iniciando automatización Allianz optimizada y modular...")
    
    # Configuración
    usuario = None  # Se toma de .env/config
    contrasena = None
    headless = None
    
    # Crear instancia de automatización
    automation = AllianzAutomation(usuario, contrasena, headless)

    try:
        # Lanzar navegador
        await automation.launch()

        # Ejecutar flujo completo
        success = await automation.run_complete_flow()
        
        if success:
            logging.info("✅ ¡AUTOMATIZACIÓN COMPLETADA!")
            # Espera para revisar resultados
            logging.info("⏱️ Esperando 15 segundos para revisión...")
            await asyncio.sleep(15)
        else:
            logging.error("❌ La automatización falló")
            await asyncio.sleep(15)

    except Exception as e:
        logging.exception(f"❌ Error general: {e}")
    finally:
        # Siempre cerrar el navegador
        await automation.close()
        logging.info("✅ Proceso terminado")

if __name__ == "__main__":
    asyncio.run(main())
