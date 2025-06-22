"""Automatización específica para Allianz."""

import asyncio
from typing import Optional

from ...core.base_automation import BaseAutomation
from ...config.allianz_config import AllianzConfig
from .pages import LoginPage, DashboardPage, FlotasPage, PlacaPage

class AllianzAutomation(BaseAutomation):
    """Automatización específica para Allianz."""
    
    def __init__(
        self, 
        usuario: Optional[str] = None, 
        contrasena: Optional[str] = None, 
        headless: Optional[bool] = None
    ):
        super().__init__('allianz', usuario, contrasena, headless)
        
        # Configuración específica de Allianz
        self.config = AllianzConfig()
        self.usuario = usuario or self.config.USUARIO
        self.contrasena = contrasena or self.config.CONTRASENA
        self.headless = headless if headless is not None else self.config.HEADLESS
        
        # Páginas específicas de Allianz
        self.login_page = None
        self.dashboard_page = None
        self.flotas_page = None
        self.placa_page = None

    async def launch(self) -> bool:
        """Inicializa Playwright y abre el navegador."""
        if not await super().launch():
            return False
        
        # Inicializar páginas específicas de Allianz
        self.login_page = LoginPage(self.page)
        self.dashboard_page = DashboardPage(self.page)
        self.flotas_page = FlotasPage(self.page)
        self.placa_page = PlacaPage(self.page)
        
        self.logger.info("✅ Páginas de Allianz inicializadas")
        return True

    async def execute_login_flow(self) -> bool:
        """Ejecuta el flujo de login específico de Allianz."""
        self.logger.info("🔐 Ejecutando flujo de login Allianz...")
        return await self.login_page.login(self.usuario, self.contrasena)

    async def execute_navigation_flow(self) -> bool:
        """Ejecuta el flujo de navegación específico de Allianz."""
        self.logger.info("🧭 Ejecutando flujo de navegación Allianz...")
        
        # Navegar a flotas
        if not await self.dashboard_page.navigate_to_flotas():
            self.logger.error("❌ Error navegando a flotas")
            return False
        
        # Enviar formulario si existe
        await self.dashboard_page.submit_application_form()
        return True

    async def execute_quote_flow(self) -> bool:
        """Ejecuta el flujo de cotización específico de Allianz."""
        self.logger.info("💰 Ejecutando flujo de cotización Allianz...")
        
        # Paso 1: Flujo de flotas
        if not await self.flotas_page.execute_flotas_flow():
            self.logger.error("❌ Falló el flujo de flotas")
            return False
        
        # Paso 2: Flujo de placa
        if not await self.placa_page.execute_placa_flow():
            self.logger.error("❌ Falló el flujo de placa")
            return False
        
        return True

    # Métodos específicos de Allianz (compatibilidad con código existente)
    async def execute_flotas_flow(self) -> bool:
        """Ejecuta el flujo específico de flotas."""
        self.logger.info("🚗 Ejecutando flujo de flotas...")
        return await self.flotas_page.execute_flotas_flow()

    async def execute_placa_flow(self) -> bool:
        """Ejecuta el flujo específico de placa."""
        self.logger.info("🔎 Ejecutando flujo de placa...")
        return await self.placa_page.execute_placa_flow()

# Función principal para compatibilidad
async def main():
    """Función principal para ejecutar la automatización de Allianz."""
    automation = AllianzAutomation()
    
    try:
        await automation.launch()
        success = await automation.run_complete_flow()
        
        if success:
            automation.logger.info("✅ ¡AUTOMATIZACIÓN DE ALLIANZ COMPLETADA!")
            await asyncio.sleep(15)  # Tiempo para revisar resultados
        else:
            automation.logger.error("❌ La automatización de Allianz falló")
            await asyncio.sleep(15)
            
    except Exception as e:
        automation.logger.exception(f"❌ Error general en Allianz: {e}")
    finally:
        await automation.close()

if __name__ == "__main__":
    asyncio.run(main())
