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
        elif company_lower == 'solidaria':
            from ..companies.solidaria.solidaria_automation import SolidariaAutomation
            return SolidariaAutomation(
                usuario=usuario,
                contrasena=contrasena,
                headless=headless,
                **kwargs
            )
        elif company_lower == 'bolivar':
            from ..companies.bolivar.bolivar_automation import BolivarAutomation
            return BolivarAutomation(
                usuario=usuario,
                contrasena=contrasena,
                headless=headless,
                **kwargs
            )
        else:
            available = ['allianz', 'sura', 'solidaria', 'bolivar']
            raise ConfigurationError(
                f"Compañía '{company}' no soportada. "
                f"Compañías disponibles: {', '.join(available)}"
            )
    
    @classmethod
    def get_supported_companies(cls) -> list:
        """Retorna la lista de compañías soportadas."""
        return ['allianz', 'sura', 'solidaria', 'bolivar']
    
    @classmethod
    def get_allowed_companies_for_fondo(cls, fondo: str = None) -> list:
        """
        Retorna las compañías permitidas para un fondo específico.
        
        Args:
            fondo: Nombre del fondo seleccionado. Si es None, retorna todas las compañías.
            
        Returns:
            Lista de compañías permitidas para el fondo
        """
        if not fondo:
            return cls.get_supported_companies()
        
        try:
            from ..consolidation.template_handler import TemplateHandler
            template_handler = TemplateHandler()
            allowed_companies = template_handler.get_fondo_aseguradoras(fondo)
            
            # Filtrar solo las compañías que están soportadas por el sistema
            supported_companies = cls.get_supported_companies()
            filtered_companies = [
                company.lower() for company in allowed_companies 
                if company.lower() in supported_companies
            ]
            
            return filtered_companies
            
        except Exception as e:
            # Si hay algún error, retornar todas las compañías soportadas
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Error obteniendo compañías para fondo '{fondo}': {e}")
            return cls.get_supported_companies()
