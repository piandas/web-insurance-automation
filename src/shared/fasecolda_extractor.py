"""Extractor de códigos FASECOLDA que se ejecuta en paralelo al inicio."""

import os
import asyncio
from typing import Optional, Dict
from playwright.async_api import async_playwright, Playwright, Browser, Page

from .fasecolda_service import FasecoldaService
from ..config.client_config import ClientConfig
from ..config.base_config import BaseConfig
from ..core.logger_factory import LoggerFactory


class FasecoldaExtractor:
    """Extractor independiente de códigos FASECOLDA que funciona en paralelo."""
    
    def __init__(self, headless: bool = False):
        self.logger = LoggerFactory.create_logger('fasecolda_extractor')
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.codes: Optional[Dict[str, str]] = None
        self._extraction_task: Optional[asyncio.Task] = None
        self.headless = headless
    
    async def start_extraction(self) -> asyncio.Task:
        """
        Inicia la extracción de códigos FASECOLDA en paralelo.
        
        Returns:
            Task que puede ser awaiteado para obtener los códigos
        """
        self.logger.info("🚀 Iniciando extracción de códigos FASECOLDA en paralelo...")
        
        # Verificar si Fasecolda está habilitado globalmente
        if not ClientConfig.is_fasecolda_enabled():
            self.logger.info("⚙️ Fasecolda deshabilitado - usando código por defecto")
            return asyncio.create_task(self._return_default_codes())
        
        # Verificar si es necesario extraer códigos
        if not self._should_extract_codes():
            self.logger.info("⏭️ Extracción de códigos FASECOLDA no necesaria")
            return asyncio.create_task(self._return_empty_codes())
        
        # Crear task para extracción asíncrona
        self._extraction_task = asyncio.create_task(self._extract_codes_async())
        return self._extraction_task
    
    async def get_codes(self, timeout: int = 30) -> Optional[Dict[str, str]]:
        """
        Obtiene los códigos extraídos, esperando a que termine la extracción si es necesario.
        
        Args:
            timeout: Tiempo máximo de espera en segundos
            
        Returns:
            Diccionario con códigos CF y CH, o None si falló
        """
        if not self._extraction_task:
            self.logger.warning("⚠️ No hay task de extracción activa")
            return None
        
        try:
            self.logger.info("⏳ Esperando resultados de extracción FASECOLDA...")
            codes = await asyncio.wait_for(self._extraction_task, timeout=timeout)
            
            if codes and codes.get('cf_code'):
                ch_info = f" - CH: {codes.get('ch_code')}" if codes.get('ch_code') else ""
                self.logger.info(f"✅ Códigos FASECOLDA obtenidos - CF: {codes['cf_code']}{ch_info}")
            else:
                self.logger.warning("⚠️ No se pudieron obtener códigos FASECOLDA")
            
            return codes
            
        except asyncio.TimeoutError:
            self.logger.error(f"⏰ Timeout esperando extracción FASECOLDA ({timeout}s)")
            await self._cleanup_extraction()
            return None
        except Exception as e:
            self.logger.error(f"❌ Error obteniendo códigos FASECOLDA: {e}")
            await self._cleanup_extraction()
            return None
    
    def _should_extract_codes(self) -> bool:
        """Determina si es necesario extraer códigos FASECOLDA."""
        try:
            # CRÍTICO: Cargar datos de GUI antes de usar ClientConfig
            ClientConfig._load_gui_overrides()
            
            # Verificar configuración global de Fasecolda
            if not ClientConfig.is_fasecolda_enabled():
                self.logger.info("⏭️ Búsqueda de códigos FASECOLDA deshabilitada globalmente")
                return False
            
            # Verificar configuración general
            if ClientConfig.VEHICLE_STATE != 'Nuevo':
                self.logger.info(f"⏭️ Vehículo '{ClientConfig.VEHICLE_STATE}' - no requiere código FASECOLDA")
                return False
            
            # Verificar configuración específica de Sura
            sura_enabled = ClientConfig.should_use_fasecolda_for_company('sura')
            
            # Verificar configuración específica de Allianz
            allianz_enabled = ClientConfig.should_use_fasecolda_for_company('allianz')
            
            if not sura_enabled and not allianz_enabled:
                self.logger.info("⏭️ Búsqueda automática de FASECOLDA deshabilitada para todas las compañías")
                return False
            
            # Verificar que tengamos los datos mínimos necesarios
            required_fields = ['VEHICLE_CATEGORY', 'VEHICLE_BRAND', 'VEHICLE_REFERENCE']
            missing_fields = [field for field in required_fields if not getattr(ClientConfig, field, None)]
            
            if missing_fields:
                self.logger.warning(f"⚠️ Campos faltantes para extracción FASECOLDA: {missing_fields}")
                return False
            
            self.logger.info("✅ Condiciones cumplidas para extracción FASECOLDA")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error verificando condiciones para extracción: {e}")
            return False
    
    async def _return_empty_codes(self) -> Optional[Dict[str, str]]:
        """Retorna None para casos donde no se necesita extracción."""
        return None
    
    async def _return_default_codes(self) -> Dict[str, str]:
        """Retorna códigos manuales cuando Fasecolda está deshabilitado."""
        manual_codes = ClientConfig.get_manual_fasecolda_codes()
        self.logger.info(f"📋 Usando códigos Fasecolda manuales - CF: {manual_codes['cf_code']}, CH: {manual_codes['ch_code']}")
        return manual_codes
    
    async def _extract_codes_async(self) -> Optional[Dict[str, str]]:
        """Ejecuta la extracción de códigos de forma asíncrona."""
        try:
            # CRÍTICO: Cargar datos de GUI antes de usar ClientConfig
            ClientConfig._load_gui_overrides()
            
            self.logger.info("🌐 Iniciando navegador para extracción FASECOLDA...")
            
            # Inicializar Playwright
            self.playwright = await async_playwright().start()
            
            # Determinar configuración de headless
            gui_show_browser = os.getenv('GUI_SHOW_BROWSER', 'False').lower() == 'true'
            should_hide = not gui_show_browser  # Si GUI dice mostrar = False, ocultar = True
            
            # Configurar argumentos del navegador
            browser_args = [
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox'
            ]
            
            # Si debe estar oculto, usar ventana minimizada en lugar de headless
            if should_hide:
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
                    '--window-position=200,100',  # Posición centrada en pantalla
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
            
            # Crear servicio y extraer códigos
            fasecolda_service = FasecoldaService(self.page, self.logger)
            codes = await fasecolda_service.get_cf_code(
                category=ClientConfig.VEHICLE_CATEGORY,
                state=ClientConfig.VEHICLE_STATE,
                model_year=ClientConfig.VEHICLE_MODEL_YEAR,
                brand=ClientConfig.VEHICLE_BRAND,
                reference=ClientConfig.VEHICLE_REFERENCE,
                full_reference=ClientConfig.VEHICLE_FULL_REFERENCE
            )
            
            self.codes = codes
            return codes
            
        except Exception as e:
            self.logger.error(f"❌ Error en extracción asíncrona FASECOLDA: {e}")
            return None
        finally:
            await self._cleanup_extraction()
    
    async def _cleanup_extraction(self):
        """Limpia recursos del navegador de extracción."""
        try:
            if self.page:
                await self.page.close()
                self.page = None
            
            if self.browser:
                await self.browser.close()
                self.browser = None
            
            if self.playwright:
                await self.playwright.stop()
                self.playwright = None
                
            self.logger.info("🧹 Recursos de extracción FASECOLDA liberados")
            
        except Exception as e:
            self.logger.warning(f"⚠️ Error limpiando recursos de extracción: {e}")
    
    async def close(self):
        """Cierra el extractor y libera todos los recursos."""
        if self._extraction_task and not self._extraction_task.done():
            self._extraction_task.cancel()
            try:
                await self._extraction_task
            except asyncio.CancelledError:
                pass
        
        await self._cleanup_extraction()
        self.logger.info("🔒 Extractor FASECOLDA cerrado")


# Instancia global para compartir entre automatizaciones
_global_extractor: Optional[FasecoldaExtractor] = None
_extraction_task: Optional[asyncio.Task] = None


async def start_global_fasecolda_extraction(headless: bool = False) -> asyncio.Task:
    """
    Inicia la extracción global de códigos FASECOLDA.
    
    Args:
        headless: Si ejecutar en modo headless o no
    
    Returns:
        Task de la extracción que puede ser awaiteado
    """
    global _global_extractor, _extraction_task
    
    if _global_extractor is None:
        _global_extractor = FasecoldaExtractor(headless=headless)
    
    if _extraction_task is None or _extraction_task.done():
        _extraction_task = await _global_extractor.start_extraction()
    
    return _extraction_task


async def get_global_fasecolda_codes(timeout: int = 30) -> Optional[Dict[str, str]]:
    """
    Obtiene los códigos FASECOLDA de la extracción global.
    
    Args:
        timeout: Tiempo máximo de espera en segundos
        
    Returns:
        Diccionario con códigos CF y CH, o None si falló
    """
    global _global_extractor
    
    if _global_extractor is None:
        return None
    
    return await _global_extractor.get_codes(timeout)


async def cleanup_global_fasecolda_extractor():
    """Limpia el extractor global y libera recursos."""
    global _global_extractor, _extraction_task
    
    if _global_extractor:
        await _global_extractor.close()
        _global_extractor = None
    
    _extraction_task = None
