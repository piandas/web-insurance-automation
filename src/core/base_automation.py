"""Clase base abstracta para todas las automatizaciones."""

import os
import logging
from abc import ABC, abstractmethod
from typing import Optional
from playwright.async_api import async_playwright, Browser, Page, Playwright

from .logger_factory import LoggerFactory
from ..config.base_config import BaseConfig

class BaseAutomation(ABC):
    """Clase base abstracta que define la interfaz común para todas las automatizaciones."""
    
    def __init__(
        self, 
        company: str,
        usuario: Optional[str] = None, 
        contrasena: Optional[str] = None, 
        headless: Optional[bool] = None
    ):
        self.company = company.lower()
        self.usuario = usuario
        self.contrasena = contrasena
        self.headless = headless if headless is not None else False  # Por defecto False para evitar problemas
        
        # Playwright
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        
        # Logger específico por compañía
        LoggerFactory.clear_all_handlers()  # Limpiar handlers previos
        self.logger = LoggerFactory.create_logger(self.company)
        
        # Configurar download path por compañía
        self.downloads_dir = self._get_downloads_dir()
    
    def _get_downloads_dir(self) -> str:
        """Obtiene el directorio de descargas específico para la compañía."""
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        downloads_dir = os.path.join(base_dir, 'downloads', self.company)
        os.makedirs(downloads_dir, exist_ok=True)
        return downloads_dir
    
    def _get_user_data_dir(self) -> str:
        """Obtiene el directorio de datos de usuario específico para la compañía."""
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        user_data_dir = os.path.join(base_dir, 'browser_profiles', self.company)
        os.makedirs(user_data_dir, exist_ok=True)
        return user_data_dir
    
    def _clean_browser_profile(self, user_data_dir: str) -> None:
        """Limpia archivos innecesarios del perfil del navegador manteniendo la sesión."""
        try:
            import shutil
            
            # Archivos y carpetas a limpiar (mantener sesión pero limpiar cache/logs)
            items_to_clean = [
                'GraphiteDawnCache',
                'GrShaderCache', 
                'ShaderCache',
                'component_crx_cache',
                'extensions_crx_cache',
                'Crashpad',
                'Safe Browsing',
                'segmentation_platform'
            ]
            
            for item in items_to_clean:
                item_path = os.path.join(user_data_dir, item)
                if os.path.exists(item_path):
                    if os.path.isdir(item_path):
                        shutil.rmtree(item_path, ignore_errors=True)
                    else:
                        os.remove(item_path)
                        
            # Limpiar archivos de logs específicos en Default
            default_dir = os.path.join(user_data_dir, 'Default')
            if os.path.exists(default_dir):
                log_files = ['LOG', 'LOG.old', 'MANIFEST*']
                for pattern in log_files:
                    import glob
                    for file in glob.glob(os.path.join(default_dir, pattern)):
                        try:
                            os.remove(file)
                        except:
                            pass
                            
            self.logger.info("🧹 Perfil del navegador limpiado")
            
        except Exception as e:
            self.logger.warning(f"⚠️ Error limpiando perfil: {e}")
    
    async def launch(self) -> bool:
        """Inicializa Playwright y abre el navegador."""
        try:
            self.logger.info(f"🚀 Lanzando navegador para {self.company.upper()}...")
            self.playwright = await async_playwright().start()
            
            # Para Sura y Allianz, usar perfil persistente para mantener las cookies/sesiones
            if self.company in ['sura', 'allianz']:
                self.logger.info(f"📁 Usando perfil persistente para {self.company.upper()}...")
                user_data_dir = self._get_user_data_dir()
                self.logger.info(f"📂 Directorio de perfil: {user_data_dir}")
                
                # Limpiar archivos innecesarios del perfil
                self._clean_browser_profile(user_data_dir)
                
                # Crear contexto persistente en lugar de navegador temporal
                # Usar ventanas minimizadas en lugar de headless para evitar problemas
                browser_args = [
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox'
                ]
                
                # Si debe estar oculto, usar ventana minimizada en lugar de headless
                if self.headless:
                    browser_args.extend([
                        '--start-minimized',
                        '--window-position=-32000,-32000',  # Mover fuera de la pantalla
                        '--window-size=1,1',  # Tamaño mínimo
                        '--disable-background-timer-throttling',  # Evita que se ralenticen los timers
                        '--disable-renderer-backgrounding',  # Evita que el renderer se pause
                        '--disable-backgrounding-occluded-windows'  # No pausar ventanas ocultas
                    ])
                    headless_mode = False  # No usar headless real para evitar problemas
                else:
                    # Ventanas visibles: centrar en pantalla con tamaño razonable
                    browser_args.extend([
                        '--window-position=100,50',  # Posición centrada (primera ventana)
                        '--window-size=1200,800',  # Tamaño razonable
                        '--disable-background-timer-throttling',
                        '--disable-renderer-backgrounding'
                    ])
                    headless_mode = False
                
                self.browser = await self.playwright.chromium.launch_persistent_context(
                    user_data_dir=user_data_dir,
                    headless=headless_mode,
                    args=browser_args
                )
                # En contexto persistente, la página ya está disponible
                if len(self.browser.pages) > 0:
                    self.page = self.browser.pages[0]
                else:
                    self.page = await self.browser.new_page()
                    
            else:
                # Para otras compañías, usar navegador temporal normal
                browser_args = [
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox'
                ]
                
                # Si debe estar oculto, usar ventana minimizada en lugar de headless
                if self.headless:
                    browser_args.extend([
                        '--start-minimized',
                        '--window-position=-32000,-32000',  # Mover fuera de la pantalla
                        '--window-size=1,1',  # Tamaño mínimo
                        '--disable-background-timer-throttling',  # Evita que se ralenticen los timers
                        '--disable-renderer-backgrounding',  # Evita que el renderer se pause
                        '--disable-backgrounding-occluded-windows'  # No pausar ventanas ocultas
                    ])
                    headless_mode = False  # No usar headless real para evitar problemas
                else:
                    # Ventanas visibles: centrar en pantalla con tamaño razonable  
                    browser_args.extend([
                        '--window-position=350,100',  # Posición centrada (segunda ventana, más desplazada)
                        '--window-size=1200,800',  # Tamaño razonable
                        '--disable-background-timer-throttling',
                        '--disable-renderer-backgrounding'
                    ])
                    headless_mode = False
                
                self.browser = await self.playwright.chromium.launch(
                    headless=headless_mode,
                    args=browser_args
                )
                self.page = await self.browser.new_page()
            
            self.logger.info("✅ Navegador lanzado exitosamente")
            return True
        except Exception as e:
            self.logger.error(f"❌ Error lanzando navegador: {e}")
            return False
    
    async def close(self):
        """Cierra el navegador y limpia recursos."""
        try:
            self.logger.info(f"🔒 Cerrando navegador {self.company.upper()}...")
            if self.browser:
                if self.company in ['sura', 'allianz']:
                    # Para Sura y Allianz (contexto persistente), cerrar contexto
                    await self.browser.close()
                    self.logger.info(f"📁 Perfil persistente de {self.company.upper()} guardado")
                else:
                    # Para otras compañías, cerrar navegador normal
                    await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            self.logger.info("✅ Recursos liberados")
        except Exception as e:
            self.logger.error(f"❌ Error cerrando navegador: {e}")
    
    # Métodos abstractos que deben implementar las subclases
    @abstractmethod
    async def execute_login_flow(self) -> bool:
        """Ejecuta el flujo de login específico de la compañía."""
        pass
    
    @abstractmethod
    async def execute_navigation_flow(self) -> bool:
        """Ejecuta el flujo de navegación específico de la compañía."""
        pass
    
    @abstractmethod
    async def execute_quote_flow(self) -> bool:
        """Ejecuta el flujo de cotización específico de la compañía."""
        pass
    
    async def run_complete_flow(self) -> bool:
        """Ejecuta el flujo completo de automatización."""
        self.logger.info(f"🎬 Iniciando flujo completo para {self.company.upper()}...")
        
        try:
            # Paso 1: Login
            if not await self.execute_login_flow():
                self.logger.error("❌ Falló el flujo de login")
                return False
            
            # Paso 2: Navegación
            if not await self.execute_navigation_flow():
                self.logger.error("❌ Falló el flujo de navegación")
                return False
            
            # Paso 3: Cotización
            if not await self.execute_quote_flow():
                self.logger.error("❌ Falló el flujo de cotización")
                return False
            
            self.logger.info(f"🎉 ¡PROCESO COMPLETO DE {self.company.upper()} EJECUTADO EXITOSAMENTE!")
            return True
            
        except Exception as e:
            self.logger.exception(f"❌ Error en flujo completo: {e}")
            return False
