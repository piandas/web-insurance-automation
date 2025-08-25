"""Clase base abstracta para todas las automatizaciones."""

import os
import logging
import asyncio
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
        """Limpia archivos innecesarios del perfil del navegador manteniendo la sesión pero asegurando inicio limpio."""
        try:
            import shutil
            import glob
            
            self.logger.info("🧹 Iniciando limpieza del perfil del navegador...")
            
            # Archivos y carpetas de cache a limpiar (mantener sesión pero limpiar cache/logs)
            cache_items_to_clean = [
                'GraphiteDawnCache',
                'GrShaderCache', 
                'ShaderCache',
                'component_crx_cache',
                'extensions_crx_cache',
                'Crashpad',
                'Safe Browsing',
                'segmentation_platform',
                'BrowserMetrics*.pma',  # Archivos de métricas
                'BrowserMetrics-spare.pma'
            ]
            
            cleaned_count = 0
            
            # Limpiar elementos de cache
            for item in cache_items_to_clean:
                if '*' in item:
                    # Manejar patrones con wildcards
                    for file_path in glob.glob(os.path.join(user_data_dir, item)):
                        try:
                            if os.path.isfile(file_path):
                                os.remove(file_path)
                                cleaned_count += 1
                        except:
                            pass
                else:
                    item_path = os.path.join(user_data_dir, item)
                    if os.path.exists(item_path):
                        try:
                            if os.path.isdir(item_path):
                                shutil.rmtree(item_path, ignore_errors=True)
                                cleaned_count += 1
                            else:
                                os.remove(item_path)
                                cleaned_count += 1
                        except:
                            pass
                        
            # Limpiar archivos temporales y de logs en Default
            default_dir = os.path.join(user_data_dir, 'Default')
            if os.path.exists(default_dir):
                temp_files_patterns = [
                    'LOG*', 'MANIFEST*', '*.tmp', '*.lock', 
                    'Network Action Predictor*', 'TransportSecurity*',
                    'Download Service/*', 'blob_storage/*',
                    'Service Worker/CacheStorage/*'
                ]
                
                for pattern in temp_files_patterns:
                    for file_path in glob.glob(os.path.join(default_dir, pattern)):
                        try:
                            if os.path.isfile(file_path):
                                os.remove(file_path)
                                cleaned_count += 1
                            elif os.path.isdir(file_path):
                                shutil.rmtree(file_path, ignore_errors=True)
                                cleaned_count += 1
                        except:
                            pass
            
            # Limpiar archivos de bloqueo del navegador que pueden quedar si se cerró mal
            lock_files = [
                'SingletonLock', 'SingletonSocket', 'SingletonCookie'
            ]
            
            for lock_file in lock_files:
                lock_path = os.path.join(user_data_dir, lock_file)
                if os.path.exists(lock_path):
                    try:
                        os.remove(lock_path)
                        cleaned_count += 1
                        self.logger.info(f"🔓 Eliminado archivo de bloqueo: {lock_file}")
                    except:
                        pass
            
            # Verificar y limpiar procesos de Chrome/Chromium huérfanos específicos del perfil
            self._kill_orphaned_browser_processes(user_data_dir)
                            
            if cleaned_count > 0:
                self.logger.info(f"🧹 Perfil limpiado: {cleaned_count} elementos eliminados")
            else:
                self.logger.info("✨ Perfil ya estaba limpio")
            
        except Exception as e:
            self.logger.warning(f"⚠️ Error limpiando perfil: {e}")

    def _kill_orphaned_browser_processes(self, user_data_dir: str) -> None:
        """Elimina procesos huérfanos de Chrome/Chromium que puedan estar usando el perfil."""
        try:
            import psutil
            import subprocess
            
            killed_count = 0
            
            # Buscar procesos de Chrome/Chromium que usen este user_data_dir
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['name'] and 'chrome' in proc.info['name'].lower():
                        cmdline = ' '.join(proc.info['cmdline'] or [])
                        if user_data_dir.replace('\\', '/') in cmdline.replace('\\', '/'):
                            self.logger.info(f"🔪 Eliminando proceso huérfano: PID {proc.info['pid']}")
                            proc.kill()
                            killed_count += 1
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
            
            if killed_count > 0:
                self.logger.info(f"🔪 Eliminados {killed_count} procesos huérfanos")
                # Esperar un momento para que los procesos terminen completamente
                import time
                time.sleep(1)
                
        except ImportError:
            # psutil no está disponible, usar método alternativo con taskkill (Windows)
            try:
                subprocess.run(['taskkill', '/f', '/im', 'chrome.exe'], 
                             capture_output=True, timeout=5)
                subprocess.run(['taskkill', '/f', '/im', 'chromium.exe'], 
                             capture_output=True, timeout=5)
                self.logger.info("🔪 Intentó limpiar procesos de navegador con taskkill")
            except:
                pass
        except Exception as e:
            self.logger.warning(f"⚠️ Error eliminando procesos huérfanos: {e}")
    
    async def launch(self) -> bool:
        """Inicializa Playwright y abre el navegador con limpieza completa previa."""
        try:
            self.logger.info(f"🚀 Lanzando navegador para {self.company.upper()}...")
            
            # Para Sura y Allianz, usar perfil persistente para mantener las cookies/sesiones
            if self.company in ['sura', 'allianz']:
                self.logger.info(f"📁 Usando perfil persistente para {self.company.upper()}...")
                user_data_dir = self._get_user_data_dir()
                self.logger.info(f"📂 Directorio de perfil: {user_data_dir}")
                
                # LIMPIEZA COMPLETA ANTES DE INICIAR
                self.logger.info("🧽 Realizando limpieza completa antes de iniciar...")
                
                # 1. Limpiar procesos huérfanos ANTES de limpiar archivos
                self._kill_orphaned_browser_processes(user_data_dir)
                
                # 2. Limpiar archivos innecesarios del perfil
                self._clean_browser_profile(user_data_dir)
                
                # 3. Pequeña pausa para asegurar que todo esté limpio
                await asyncio.sleep(1)
                
            self.playwright = await async_playwright().start()
            
            # Para Sura y Allianz, usar perfil persistente para mantener las cookies/sesiones
            if self.company in ['sura', 'allianz']:
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
        """Cierra el navegador y limpia recursos de forma completa."""
        try:
            self.logger.info(f"🔒 Cerrando navegador {self.company.upper()}...")
            
            if self.browser:
                if self.company in ['sura', 'allianz']:
                    # Para Sura y Allianz (contexto persistente), cerrar contexto
                    await self.browser.close()
                    self.logger.info(f"📁 Perfil persistente de {self.company.upper()} guardado")
                    
                    # Limpieza adicional post-cierre para perfiles persistentes
                    user_data_dir = self._get_user_data_dir()
                    
                    # Esperar un momento para que el navegador termine completamente
                    await asyncio.sleep(2)
                    
                    # Realizar limpieza post-cierre para próxima ejecución
                    self.logger.info("🧹 Realizando limpieza post-cierre...")
                    self._post_close_cleanup(user_data_dir)
                    
                else:
                    # Para otras compañías, cerrar navegador normal
                    await self.browser.close()
                    
            if self.playwright:
                await self.playwright.stop()
                
            self.logger.info("✅ Recursos liberados completamente")
            
        except Exception as e:
            self.logger.error(f"❌ Error cerrando navegador: {e}")

    def _post_close_cleanup(self, user_data_dir: str) -> None:
        """Limpieza adicional después del cierre para asegurar inicio limpio en próxima ejecución."""
        try:
            import glob
            import os
            
            cleanup_count = 0
            
            # Limpiar archivos de bloqueo que pueden quedar
            lock_files = [
                'SingletonLock', 'SingletonSocket', 'SingletonCookie',
                'lockfile', '.lock'
            ]
            
            for lock_file in lock_files:
                lock_path = os.path.join(user_data_dir, lock_file)
                if os.path.exists(lock_path):
                    try:
                        os.remove(lock_path)
                        cleanup_count += 1
                    except:
                        pass
            
            # Limpiar archivos temporales que se crean durante la sesión
            temp_patterns = [
                '*.tmp', '*.temp', '*.lock', 'Temp/*'
            ]
            
            for pattern in temp_patterns:
                for file_path in glob.glob(os.path.join(user_data_dir, pattern)):
                    try:
                        if os.path.isfile(file_path):
                            os.remove(file_path)
                            cleanup_count += 1
                    except:
                        pass
            
            if cleanup_count > 0:
                self.logger.info(f"🧹 Limpieza post-cierre: {cleanup_count} elementos eliminados")
            
        except Exception as e:
            self.logger.warning(f"⚠️ Error en limpieza post-cierre: {e}")
    
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
