"""Automatización específica para Sura."""

import asyncio
from typing import Optional

from ...core.base_automation import BaseAutomation
from ...config.sura_config import SuraConfig
from ...shared.global_pause_coordinator import wait_for_global_resume
from .pages import LoginPage, DashboardPage, QuotePage, PolicyPage, FasecoldaPage

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
        self.policy_page = None

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
        """Ejecuta el flujo de login específico de Sura con reintentos."""
        self.logger.info("🔐 Ejecutando flujo de login Sura...")
        
        if not self.usuario or not self.contrasena:
            self.logger.error("❌ Credenciales de Sura no configuradas")
            return False
        
        max_intentos = 3
        for intento in range(1, max_intentos + 1):
            try:
                self.logger.info(f"🔄 Intento de login {intento}/{max_intentos}")
                
                # Intentar login
                result = await self.login_page.login(self.usuario, self.contrasena)
                if result:
                    self.logger.info("✅ Login exitoso")
                    return True
                    
                # Si falló, esperar antes del siguiente intento
                if intento < max_intentos:
                    self.logger.warning(f"⚠️ Intento {intento} falló, esperando antes del siguiente...")
                    await asyncio.sleep(3)
                    
                    # Intentar navegar de nuevo a la página de login
                    try:
                        await self.login_page.navigate_to_login()
                    except Exception as nav_error:
                        self.logger.warning(f"⚠️ Error re-navegando al login: {nav_error}")
                        
            except Exception as e:
                self.logger.error(f"❌ Error en intento de login {intento}: {e}")
                if intento < max_intentos:
                    await asyncio.sleep(3)
        
        self.logger.error(f"❌ Login falló después de {max_intentos} intentos")
        return False

    async def execute_navigation_flow(self) -> bool:
        """Ejecuta el flujo de navegación específico de Sura con reintentos."""
        self.logger.info("🧭 Ejecutando flujo de navegación Sura...")
        
        max_intentos = 3
        for intento in range(1, max_intentos + 1):
            try:
                self.logger.info(f"🔄 Intento de navegación {intento}/{max_intentos}")
                
                # Usar los valores desde la configuración
                document_number = getattr(self.config, 'CLIENT_DOCUMENT_NUMBER', '1020422674')
                document_type = getattr(self.config, 'CLIENT_DOCUMENT_TYPE', 'C')
                
                # Ejecutar flujo completo de navegación
                success, new_page = await self.dashboard_page.complete_navigation_flow(document_number, document_type)
                
                if success and new_page:
                    # Actualizar la referencia de la página en la automatización
                    self.page = new_page
                    self.logger.info(f"✅ Página actualizada en SuraAutomation: {new_page.url}")
                    self.logger.info("✅ Flujo de navegación Sura completado exitosamente")
                    return True            
                else:
                    self.logger.warning(f"⚠️ Intento {intento} de navegación falló")
                    if intento < max_intentos:
                        await asyncio.sleep(5)  # Esperar antes del siguiente intento
                        
            except Exception as e:
                self.logger.error(f"❌ Error en intento de navegación {intento}: {e}")
                if intento < max_intentos:
                    await asyncio.sleep(5)
        
        self.logger.error(f"❌ Navegación falló después de {max_intentos} intentos")
        return False

    async def execute_quote_flow(self) -> bool:
        """Ejecuta el flujo de cotización específico de Sura."""
        self.logger.info("💰 Ejecutando flujo de cotización Sura...")
        
        try:
            self.logger.info("📊 Procesando página de cotización...")
            quote_page = QuotePage(self.page)
            
            if not await quote_page.process_quote_page():
                self.logger.error("❌ Error procesando página de cotización")
                return False
            
            self.logger.info("✅ Flujo de cotización Sura completado exitosamente")
            return True
            
        except Exception as e:
            self.logger.exception(f"❌ Error ejecutando cotización Sura: {e}")
            return False

    async def execute_policy_flow(self) -> bool:
        """Ejecuta el flujo de consulta de póliza específico de Sura."""
        self.logger.info("📄 Ejecutando flujo completo de Sura...")
        
        try:
            # 1. Procesar página de póliza hasta fecha de vigencia
            self.logger.info("🔍 Procesando página de consulta de póliza...")
            policy_page = PolicyPage(self.page)
            
            if not await policy_page.process_policy_page():
                self.logger.error("❌ Error procesando página de consulta de póliza")
                return False
            
            # 2. Procesar código Fasecolda y extraer primas
            self.logger.info("🔍 Procesando código Fasecolda, extrayendo primas y descargando PDF...")
            fasecolda_page = FasecoldaPage(self.page)
            
            results = await fasecolda_page.process_fasecolda_filling()
            
            if results['success']:
                self.logger.info(f"✅ Primas extraídas - Global: ${results['prima_global']:,.0f}, Clásico: ${results['prima_clasico']:,.0f}")
                
                if results.get('pdf_downloaded', False):
                    self.logger.info("📥 PDF descargado exitosamente")
                else:
                    self.logger.warning("⚠️ Primas extraídas pero PDF no se pudo descargar")
            else:
                self.logger.warning("⚠️ No se pudo procesar completamente el código Fasecolda y extracción de primas")
                # No retornamos False porque el proceso puede continuar
            
            self.logger.info("✅ Flujo completo de Sura completado exitosamente")
            return True
            
        except Exception as e:
            self.logger.exception(f"❌ Error ejecutando flujo completo de Sura: {e}")
            return False

    async def run_complete_flow(self) -> bool:
        """Ejecuta el flujo completo de automatización de Sura con soporte de pausas globales."""
        self.logger.info("🚀 Iniciando flujo completo de Sura...")
        
        try:
            # Verificar pausa global antes de iniciar
            await wait_for_global_resume('sura')
            
            # 1. Ejecutar login
            self.logger.info("🔐 Iniciando flujo de login...")
            await wait_for_global_resume('sura')
            if not await self.execute_login_flow():
                self.logger.error("❌ Error en el flujo de login")
                return False
            
            # 2. Ejecutar navegación
            self.logger.info("🧭 Iniciando flujo de navegación...")
            await wait_for_global_resume('sura')
            if not await self.execute_navigation_flow():
                self.logger.error("❌ Error en el flujo de navegación")
                return False
            
            # 3. Ejecutar cotización
            self.logger.info("💰 Iniciando flujo de cotización...")
            await wait_for_global_resume('sura')
            if not await self.execute_quote_flow():
                self.logger.error("❌ Error en el flujo de cotización")
                return False
            
            # 4. Ejecutar consulta de póliza
            self.logger.info("📋 Iniciando flujo de consulta de póliza...")
            await wait_for_global_resume('sura')
            if not await self.execute_policy_flow():
                self.logger.error("❌ Error en el flujo de consulta de póliza")
                return False
            
            self.logger.info("🎉 ¡Flujo completo de Sura completado exitosamente!")
            return True
            
        except Exception as e:
            self.logger.exception(f"❌ Error en el flujo completo de Sura: {e}")
            return False


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
