"""Automatización específica para Allianz."""

import asyncio
import os
from typing import Optional

from ...core.base_automation import BaseAutomation
from ...config.allianz_config import AllianzConfig
from ...shared.global_pause_coordinator import wait_for_global_resume
from .pages import LoginPage, DashboardPage, FlotasPage, PlacaPage, FasecoldaPage

class AllianzAutomation(BaseAutomation):
    """Automatización específica para Allianz."""
    
    def __init__(
        self, 
        usuario: Optional[str] = None, 
        contrasena: Optional[str] = None, 
        headless: Optional[bool] = None
    ):
        # Determinar el valor de headless basado en variables de entorno de la GUI
        if headless is None:
            # Verificar si la GUI está controlando la visibilidad
            gui_show_browser = os.getenv('GUI_SHOW_BROWSER', 'False').lower() == 'true'
            if gui_show_browser:
                # Si la GUI dice que muestre las ventanas, mostrar normalmente
                headless = False
            else:
                # Si la GUI dice que las oculte, usar modo "oculto" (no verdadero headless)
                headless = True  # Esto activa el modo minimizado/oculto, no headless real
        
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
        self.fasecolda_page = None

    async def launch(self) -> bool:
        """Inicializa Playwright y abre el navegador."""
        if not await super().launch():
            return False
        
        # Inicializar páginas específicas de Allianz
        self.login_page = LoginPage(self.page)
        self.dashboard_page = DashboardPage(self.page)
        self.flotas_page = FlotasPage(self.page)
        self.placa_page = PlacaPage(self.page)
        self.fasecolda_page = FasecoldaPage(self.page)
        
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
        
        # Obtener códigos FASECOLDA si están disponibles
        fasecolda_codes = await self.fasecolda_page.get_fasecolda_code()
        if fasecolda_codes:
            self.logger.info("📋 Códigos FASECOLDA disponibles para Allianz")
            await self.fasecolda_page.use_fasecolda_codes_in_flow(fasecolda_codes)
        
        # Paso 1: Flujo de flotas
        if not await self.flotas_page.execute_flotas_flow():
            self.logger.error("❌ Falló el flujo de flotas")
            return False
        
        # Paso 2: Flujo de placa
        if not await self.placa_page.execute_placa_flow():
            self.logger.error("❌ Falló el flujo de placa")
            return False
        
        return True

    async def run_complete_flow(self) -> bool:
        """Ejecuta el flujo completo de automatización de Allianz con soporte de pausas globales."""
        self.logger.info("🚀 Iniciando flujo completo de Allianz...")
        
        try:
            # Verificar pausa global antes de iniciar
            await wait_for_global_resume('allianz')
            
            # 1. Ejecutar login
            self.logger.info("🔐 Iniciando flujo de login...")
            await wait_for_global_resume('allianz')
            if not await self.execute_login_flow():
                self.logger.error("❌ Error en el flujo de login")
                return False
            
            # 2. Ejecutar navegación
            self.logger.info("🧭 Iniciando flujo de navegación...")
            await wait_for_global_resume('allianz')
            if not await self.execute_navigation_flow():
                self.logger.error("❌ Error en el flujo de navegación")
                return False
            
            # 3. Ejecutar cotización
            self.logger.info("💰 Iniciando flujo de cotización...")
            await wait_for_global_resume('allianz')
            if not await self.execute_quote_flow():
                self.logger.error("❌ Error en el flujo de cotización")
                return False
            
            self.logger.info("🎉 ¡Flujo completo de Allianz completado exitosamente!")
            return True
            
        except Exception as e:
            self.logger.exception(f"❌ Error en el flujo completo de Allianz: {e}")
            return False

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
