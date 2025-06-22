"""Clase base abstracta para todas las automatizaciones."""

import os
import logging
from abc import ABC, abstractmethod
from typing import Optional
from playwright.async_api import async_playwright, Browser, Page, Playwright

from .logger_factory import LoggerFactory

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
        self.headless = headless if headless is not None else True
        
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
    async def launch(self) -> bool:
        """Inicializa Playwright y abre el navegador."""
        try:
            self.logger.info(f"🚀 Lanzando navegador para {self.company.upper()}...")
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(headless=self.headless)
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
