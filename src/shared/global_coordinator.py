"""
Coordinador global para manejar la pausa de procesos y búsqueda interactiva de Fasecolda.
"""

import asyncio
from typing import Optional, Dict, Set
from dataclasses import dataclass, field
from threading import Event, Lock

from ..config.client_config import ClientConfig
from ..core.logger_factory import LoggerFactory
from .interactive_fasecolda import get_interactive_fasecolda_codes


@dataclass
class ProcessStatus:
    """Estado de un proceso de cotización."""
    company: str
    status: str = "initializing"  # initializing, waiting_for_fasecolda, running, completed, error
    logged_in: bool = False
    fasecolda_codes: Optional[Dict[str, str]] = None
    ready_to_continue: bool = False


class GlobalFasecoldaCoordinator:
    """Coordinador global para procesos de cotización y búsqueda de Fasecolda."""
    
    def __init__(self):
        self.logger = LoggerFactory.create_logger('fasecolda_coordinator')
        
        # Estado de los procesos
        self.processes: Dict[str, ProcessStatus] = {}
        self.fasecolda_codes: Optional[Dict[str, str]] = None
        self.fasecolda_search_completed = False
        self.fasecolda_search_in_progress = False
        
        # Eventos de sincronización
        self.fasecolda_search_event = asyncio.Event()
        self.processes_lock = asyncio.Lock()
        
        # Configuración
        self.companies_waiting_for_login: Set[str] = set()
        self.all_processes_logged_in = False
    
    async def register_process(self, company: str) -> None:
        """
        Registra un proceso de cotización.
        
        Args:
            company: Nombre de la compañía (sura, allianz)
        """
        async with self.processes_lock:
            self.processes[company] = ProcessStatus(company=company)
            self.logger.info(f"📝 Proceso {company} registrado")
    
    async def report_login_completed(self, company: str) -> bool:
        """
        Reporta que un proceso completó el login.
        
        Args:
            company: Nombre de la compañía
            
        Returns:
            True si debe pausarse para esperar Fasecolda, False si debe continuar
        """
        async with self.processes_lock:
            if company in self.processes:
                self.processes[company].logged_in = True
                self.processes[company].status = "waiting_for_fasecolda"
                
                self.logger.info(f"✅ {company} completó login")
                
                # Verificar si todos los procesos han completado login
                all_logged_in = all(
                    process.logged_in 
                    for process in self.processes.values()
                )
                
                if all_logged_in and not self.all_processes_logged_in:
                    self.all_processes_logged_in = True
                    self.logger.info("🔄 Todos los procesos completaron login")
                    
                    # Si Fasecolda está habilitado, iniciar búsqueda interactiva
                    if ClientConfig.is_fasecolda_enabled():
                        await self._start_fasecolda_search()
                        return True  # Pausar para esperar Fasecolda
                    else:
                        # Usar códigos manuales
                        self.fasecolda_codes = ClientConfig.get_manual_fasecolda_codes()
                        self.fasecolda_search_completed = True
                        self.fasecolda_search_event.set()
                        self.logger.info("📋 Usando códigos Fasecolda manuales")
                        return False  # No pausar, continuar inmediatamente
                
                # Si no todos han terminado login, pausar
                return ClientConfig.is_fasecolda_enabled()
            
            return False
    
    async def _start_fasecolda_search(self) -> None:
        """Inicia la búsqueda interactiva de Fasecolda en una tarea separada."""
        if not self.fasecolda_search_in_progress:
            self.fasecolda_search_in_progress = True
            self.logger.info("🔍 Iniciando búsqueda interactiva de Fasecolda...")
            
            # Crear tarea asíncrona para la búsqueda
            asyncio.create_task(self._perform_interactive_search())
    
    async def _perform_interactive_search(self) -> None:
        """Realiza la búsqueda interactiva de Fasecolda."""
        try:
            self.logger.info("🌐 Iniciando selector interactivo de Fasecolda...")
            
            # Realizar búsqueda interactiva
            codes = await get_interactive_fasecolda_codes(headless=False)
            
            if codes:
                self.fasecolda_codes = codes
                self.logger.info(f"✅ Códigos Fasecolda obtenidos - CF: {codes['cf_code']}, CH: {codes['ch_code']}")
            else:
                # Si no se obtuvieron códigos, usar los manuales como fallback
                self.fasecolda_codes = ClientConfig.get_manual_fasecolda_codes()
                self.logger.warning(f"⚠️ Usando códigos manuales como fallback - CF: {self.fasecolda_codes['cf_code']}, CH: {self.fasecolda_codes['ch_code']}")
            
            # Marcar búsqueda como completada y despertar procesos esperando
            self.fasecolda_search_completed = True
            self.fasecolda_search_event.set()
            
            # Actualizar estado de todos los procesos
            async with self.processes_lock:
                for process in self.processes.values():
                    if process.status == "waiting_for_fasecolda":
                        process.fasecolda_codes = self.fasecolda_codes
                        process.ready_to_continue = True
                        process.status = "running"
            
            self.logger.info("🚀 Todos los procesos pueden continuar")
            
        except Exception as e:
            self.logger.error(f"❌ Error en búsqueda interactiva: {e}")
            
            # En caso de error, usar códigos manuales
            self.fasecolda_codes = ClientConfig.get_manual_fasecolda_codes()
            self.fasecolda_search_completed = True
            self.fasecolda_search_event.set()
            
            async with self.processes_lock:
                for process in self.processes.values():
                    if process.status == "waiting_for_fasecolda":
                        process.fasecolda_codes = self.fasecolda_codes
                        process.ready_to_continue = True
                        process.status = "running"
    
    async def wait_for_fasecolda_codes(self, company: str, timeout: int = 300) -> Optional[Dict[str, str]]:
        """
        Espera a que se completen los códigos Fasecolda.
        
        Args:
            company: Nombre de la compañía
            timeout: Timeout en segundos
            
        Returns:
            Dict con códigos CF y CH, o None si timeout
        """
        try:
            self.logger.info(f"⏳ {company} esperando códigos Fasecolda...")
            
            # Esperar a que la búsqueda se complete
            await asyncio.wait_for(self.fasecolda_search_event.wait(), timeout=timeout)
            
            # Obtener códigos
            async with self.processes_lock:
                if company in self.processes:
                    self.processes[company].status = "running"
                    codes = self.processes[company].fasecolda_codes or self.fasecolda_codes
                    
                    if codes:
                        self.logger.info(f"✅ {company} obtuvo códigos Fasecolda - CF: {codes['cf_code']}, CH: {codes['ch_code']}")
                        return codes
            
            self.logger.warning(f"⚠️ {company} no pudo obtener códigos Fasecolda")
            return None
            
        except asyncio.TimeoutError:
            self.logger.error(f"⏰ Timeout esperando códigos Fasecolda para {company}")
            
            # En caso de timeout, usar códigos manuales
            fallback_codes = ClientConfig.get_manual_fasecolda_codes()
            async with self.processes_lock:
                if company in self.processes:
                    self.processes[company].fasecolda_codes = fallback_codes
                    self.processes[company].status = "running"
            
            return fallback_codes
            
        except Exception as e:
            self.logger.error(f"❌ Error esperando códigos Fasecolda para {company}: {e}")
            return None
    
    async def report_process_completed(self, company: str, success: bool = True) -> None:
        """
        Reporta que un proceso ha terminado.
        
        Args:
            company: Nombre de la compañía
            success: Si el proceso terminó exitosamente
        """
        async with self.processes_lock:
            if company in self.processes:
                self.processes[company].status = "completed" if success else "error"
                self.logger.info(f"🏁 Proceso {company} {'completado' if success else 'terminó con error'}")
    
    def get_process_status(self, company: str) -> Optional[str]:
        """
        Obtiene el estado actual de un proceso.
        
        Args:
            company: Nombre de la compañía
            
        Returns:
            Estado del proceso o None si no existe
        """
        return self.processes.get(company, {}).status if company in self.processes else None
    
    def should_pause_after_login(self, company: str) -> bool:
        """
        Determina si un proceso debe pausarse después del login.
        
        Args:
            company: Nombre de la compañía
            
        Returns:
            True si debe pausarse, False si debe continuar
        """
        # Solo pausar si Fasecolda está habilitado y no se ha completado la búsqueda
        return (ClientConfig.is_fasecolda_enabled() and 
                not self.fasecolda_search_completed)


# Instancia global del coordinador
global_coordinator = GlobalFasecoldaCoordinator()
