"""
Coordinador de pausas globales para automatizaciones en paralelo.

Este módulo maneja las pausas globales que afectan a todas las automatizaciones
cuando se requiere intervención manual (MFA, selección de códigos Fasecolda, etc.).
"""

import asyncio
import threading
from typing import Optional, Dict, Any
from enum import Enum


class PauseReason(Enum):
    """Razones por las que se puede pausar el sistema."""
    MFA_REQUIRED = "mfa_required"
    FASECOLDA_SELECTION = "fasecolda_selection"
    MANUAL_INTERVENTION = "manual_intervention"


class GlobalPauseCoordinator:
    """Coordinador de pausas globales para todas las automatizaciones."""
    
    _instance: Optional['GlobalPauseCoordinator'] = None
    _lock = threading.Lock()
    
    def __new__(cls) -> 'GlobalPauseCoordinator':
        """Singleton pattern para asegurar una sola instancia."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Inicializa el coordinador de pausas."""
        if hasattr(self, '_initialized'):
            return
            
        self._pause_event = asyncio.Event()
        self._pause_event.set()  # Inicialmente no pausado
        
        self._pause_reason: Optional[PauseReason] = None
        self._pause_data: Dict[str, Any] = {}
        self._requesting_company: Optional[str] = None
        
        self._initialized = True
    
    async def request_global_pause(
        self, 
        reason: PauseReason, 
        requesting_company: str,
        data: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Solicita una pausa global que afecta a todas las automatizaciones.
        
        Args:
            reason: Razón de la pausa
            requesting_company: Compañía que solicita la pausa
            data: Datos adicionales relacionados con la pausa
        """
        self._pause_reason = reason
        self._requesting_company = requesting_company
        self._pause_data = data or {}
        
        # Limpiar el evento para pausar todo
        self._pause_event.clear()
        
        print(f"\n🔴 PAUSA GLOBAL ACTIVADA")
        print(f"📋 Razón: {reason.value}")
        print(f"🏢 Solicitada por: {requesting_company}")
        print(f"⏸️ Todas las automatizaciones están pausadas")
        print(f"{'='*60}")
    
    async def resume_global_operations(self) -> None:
        """Reanuda todas las operaciones pausadas."""
        requesting_company = self._requesting_company
        reason = self._pause_reason
        
        # Limpiar datos de pausa
        self._pause_reason = None
        self._requesting_company = None
        self._pause_data = {}
        
        # Establecer el evento para reanudar todo
        self._pause_event.set()
        
        print(f"\n🟢 PAUSA GLOBAL DESACTIVADA")
        print(f"📋 Resuelto por: {requesting_company}")
        print(f"🚀 Todas las automatizaciones continúan")
        print(f"{'='*60}\n")
    
    async def wait_for_resume(self, company: str) -> None:
        """
        Espera hasta que se resuelva la pausa global.
        
        Args:
            company: Nombre de la compañía que está esperando
        """
        if not self._pause_event.is_set():
            requesting_company = self._requesting_company
            reason = self._pause_reason
            
            if company != requesting_company:
                print(f"⏸️ {company.upper()}: Pausado esperando resolución de {reason.value} por {requesting_company}")
            
            await self._pause_event.wait()
            
            if company != requesting_company:
                print(f"▶️ {company.upper()}: Continuando operaciones...")
    
    def is_paused(self) -> bool:
        """Verifica si el sistema está pausado."""
        return not self._pause_event.is_set()
    
    def get_pause_info(self) -> Dict[str, Any]:
        """Obtiene información sobre la pausa actual."""
        return {
            'is_paused': self.is_paused(),
            'reason': self._pause_reason.value if self._pause_reason else None,
            'requesting_company': self._requesting_company,
            'data': self._pause_data.copy()
        }
    
    async def wait_for_user_input(
        self, 
        prompt: str, 
        valid_options: Optional[list] = None,
        timeout: Optional[int] = None
    ) -> str:
        """
        Espera input del usuario con validación opcional.
        
        Args:
            prompt: Mensaje a mostrar al usuario
            valid_options: Lista de opciones válidas (opcional)
            timeout: Timeout en segundos (opcional)
            
        Returns:
            Input del usuario validado
        """
        print(f"\n{prompt}")
        
        if valid_options:
            print(f"Opciones válidas: {', '.join(map(str, valid_options))}")
        
        while True:
            try:
                if timeout:
                    print(f"⏰ Timeout: {timeout} segundos")
                
                # En un entorno real, aquí usarías input() con timeout
                # Por simplicidad, usamos input() normal
                response = input("👉 Tu respuesta: ").strip()
                
                if valid_options and response not in map(str, valid_options):
                    print(f"❌ Opción inválida. Opciones válidas: {', '.join(map(str, valid_options))}")
                    continue
                
                return response
                
            except KeyboardInterrupt:
                print("\n⚠️ Operación cancelada por el usuario")
                raise
            except Exception as e:
                print(f"❌ Error capturando input: {e}")
                continue


# Instancia global del coordinador
global_pause_coordinator = GlobalPauseCoordinator()


async def request_pause_for_mfa(company: str) -> None:
    """Helper para solicitar pausa por MFA."""
    await global_pause_coordinator.request_global_pause(
        reason=PauseReason.MFA_REQUIRED,
        requesting_company=company,
        data={'message': f'MFA requerido para {company}'}
    )


async def request_pause_for_fasecolda_selection(
    company: str, 
    options: list,
    results: list
) -> int:
    """
    Helper para solicitar pausa por selección de códigos Fasecolda.
    
    Args:
        company: Compañía que solicita la pausa
        options: Lista de opciones numeradas
        results: Lista de resultados de Fasecolda
        
    Returns:
        Índice seleccionado por el usuario
    """
    await global_pause_coordinator.request_global_pause(
        reason=PauseReason.FASECOLDA_SELECTION,
        requesting_company=company,
        data={
            'options': options,
            'results': results,
            'message': f'Selección de código Fasecolda requerida para {company}'
        }
    )
    
    # Mostrar opciones al usuario
    print(f"\n🔍 SELECCIÓN DE CÓDIGO FASECOLDA - {company.upper()}")
    print("="*50)
    
    for i, result in enumerate(results, 1):
        cf_code = result.get('cf_code', 'N/A')
        ch_code = result.get('ch_code', 'N/A')
        description = result.get('description', 'N/A')
        insured_value = result.get('insured_value', 'No disponible')
        score = result.get('score', 0)
        
        print(f"{i}. CF: {cf_code} - CH: {ch_code}")
        print(f"   📝 {description}")
        print(f"   💰 Valor Asegurado: {insured_value}")
        print(f"   📊 Score: {score:.2f}")
        print()
    
    # Solicitar selección del usuario
    valid_options = list(range(1, len(results) + 1))
    response = await global_pause_coordinator.wait_for_user_input(
        prompt=f"Selecciona el código a usar (1-{len(results)}):",
        valid_options=valid_options
    )
    
    selected_index = int(response) - 1
    selected_result = results[selected_index]
    
    selected_cf = selected_result.get('cf_code', 'N/A')
    selected_ch = selected_result.get('ch_code', 'N/A')
    selected_value = selected_result.get('insured_value', 'No disponible')
    
    print(f"✅ Seleccionado: CF: {selected_cf} - CH: {selected_ch}")
    print(f"   💰 Valor Asegurado: {selected_value}")
    print()
    await global_pause_coordinator.resume_global_operations()
    
    return selected_index


async def resume_after_mfa(company: str) -> None:
    """Helper para reanudar después de resolver MFA."""
    await global_pause_coordinator.resume_global_operations()


async def wait_for_global_resume(company: str) -> None:
    """Helper para que una compañía espere a que se resuelva una pausa global."""
    await global_pause_coordinator.wait_for_resume(company)
