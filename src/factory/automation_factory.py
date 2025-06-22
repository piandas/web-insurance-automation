"""Factory para crear automatizaciones específicas por compañía."""

from typing import Optional, Any
from ..core.base_automation import BaseAutomation
from ..shared.exceptions import ConfigurationError

class AutomationFactory:
    """Factory para crear automatizaciones específicas por compañía."""
    
    @classmethod
    def create(
        cls, 
        company: str, 
        usuario: Optional[str] = None,
        contrasena: Optional[str] = None,
        headless: Optional[bool] = None,
        **kwargs
    ) -> BaseAutomation:
        """
        Crea una instancia de automatización para la compañía especificada.
        
        Args:
            company: Nombre de la compañía ('allianz', 'sura')
            usuario: Usuario opcional (si no se pasa, se toma de config)
            contrasena: Contraseña opcional (si no se pasa, se toma de config)
            headless: Modo headless opcional (si no se pasa, se toma de config)
            **kwargs: Argumentos adicionales
            
        Returns:
            Instancia de automatización específica
            
        Raises:
            ConfigurationError: Si la compañía no está soportada
        """
        company_lower = company.lower()
        
        if company_lower == 'allianz':
            from ..companies.allianz.allianz_automation import AllianzAutomation
            return AllianzAutomation(
                usuario=usuario,
                contrasena=contrasena,
                headless=headless,
                **kwargs
            )
        elif company_lower == 'sura':
            from ..companies.sura.sura_automation import SuraAutomation
            return SuraAutomation(
                usuario=usuario,
                contrasena=contrasena,
                headless=headless,
                **kwargs
            )
        else:
            available = ['allianz', 'sura']
            raise ConfigurationError(
                f"Compañía '{company}' no soportada. "
                f"Compañías disponibles: {', '.join(available)}"
            )
    
    @classmethod
    def get_supported_companies(cls) -> list:
        """Retorna la lista de compañías soportadas."""
        return ['allianz', 'sura']
