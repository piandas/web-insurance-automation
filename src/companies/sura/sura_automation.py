"""Automatización específica para Sura."""

import asyncio
from typing import Optional

from ...core.base_automation import BaseAutomation
from ...config.sura_config import SuraConfig
from .pages import LoginPage, DashboardPage

class SuraAutomation(BaseAutomation):
    """Automatización específica para Sura."""
    
    def __init__(
        self, 
        usuario: Optional[str] = None, 
        contrasena: Optional[str] = None, 
        headless: Optional[bool] = None
    ):
        super().__init__('sura', usuario, contrasena, headless)
        
        # Configuración específica de Sura
        self.config = SuraConfig()
        self.usuario = usuario or self.config.USUARIO
        self.contrasena = contrasena or self.config.CONTRASENA
        self.headless = headless if headless is not None else self.config.HEADLESS
          # Páginas específicas de Sura
        self.login_page = None
        self.dashboard_page = None
        self.quote_page = None

    async def launch(self) -> bool:
        """Inicializa Playwright y abre el navegador."""
        if not await super().launch():
            return False
        
        # Inicializar páginas específicas de Sura
        self.login_page = LoginPage(self.page)
        self.dashboard_page = DashboardPage(self.page)
        
        self.logger.info("✅ Páginas de Sura inicializadas")
        return True

    async def execute_login_flow(self) -> bool:
        """Ejecuta el flujo de login específico de Sura."""
        self.logger.info("🔐 Ejecutando flujo de login Sura...")
        
        if not self.usuario or not self.contrasena:
            self.logger.error("❌ Credenciales de Sura no configuradas")
            return False
        
        return await self.login_page.login(self.usuario, self.contrasena)

    async def execute_navigation_flow(self) -> bool:
        """Ejecuta el flujo de navegación específico de Sura."""
        self.logger.info("🧭 Ejecutando flujo de navegación Sura...")
        
        try:
            # Usar los valores desde la configuración
            document_number = getattr(self.config, 'CLIENT_DOCUMENT_NUMBER', '1020422674')
            document_type = getattr(self.config, 'CLIENT_DOCUMENT_TYPE', 'C')
            
            # Ejecutar flujo completo de navegación
            success = await self.dashboard_page.complete_navigation_flow(document_number, document_type)
            
            if success:
                self.logger.info("✅ Flujo de navegación Sura completado exitosamente")
                return True
            else:
                self.logger.error("❌ Error en el flujo de navegación Sura")
                return False
                
        except Exception as e:
            self.logger.exception(f"❌ Error ejecutando navegación Sura: {e}")
            return False

    async def execute_quote_flow(self) -> bool:
        """Ejecuta el flujo de cotización específico de Sura."""
        self.logger.info("💰 Ejecutando flujo de cotización Sura...")
        self.logger.warning("⚠️ Cotización de Sura pendiente de implementación")
        
        # Placeholder - en desarrollo
        await asyncio.sleep(2)
        return True


# Función principal para compatibilidad
async def main():
    """Función principal para ejecutar la automatización de Sura."""
    automation = SuraAutomation()
    
    try:
        await automation.launch()
        success = await automation.run_complete_flow()
        
        if success:
            automation.logger.info("✅ ¡AUTOMATIZACIÓN DE SURA COMPLETADA!")
            await asyncio.sleep(15)  # Tiempo para revisar resultados
        else:
            automation.logger.error("❌ La automatización de Sura falló")
            await asyncio.sleep(15)
            
    except Exception as e:
        automation.logger.exception(f"❌ Error general en Sura: {e}")
    finally:
        await automation.close()

if __name__ == "__main__":
    asyncio.run(main())
