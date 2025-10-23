"""Factory para crear configuraciones específicas por compañía."""

from typing import Any, Dict
from ..config.base_config import BaseConfig
from ..config.allianz_config import AllianzConfig
from ..config.sura_config import SuraConfig
from ..shared.exceptions import ConfigurationError

class ConfigFactory:
    """Factory para crear configuraciones específicas por compañía."""
    
    _configs = {
        'allianz': AllianzConfig,
        'sura': SuraConfig
    }
    
    @classmethod
    def create(cls, company: str) -> BaseConfig:
        """
        Crea una instancia de configuración para la compañía especificada.
        
        Args:
            company: Nombre de la compañía
            
        Returns:
            Instancia de configuración específica
            
        Raises:
            ConfigurationError: Si la compañía no está soportada
        """
        company_lower = company.lower()
        
        if company_lower not in cls._configs:
            available = ', '.join(cls._configs.keys())
            raise ConfigurationError(
                f"Compañía '{company}' no soportada. "
                f"Compañías disponibles: {available}"
            )
        
        return cls._configs[company_lower]()
    
    @classmethod
    def get_supported_companies(cls) -> list:
        """Retorna la lista de compañías soportadas."""
        return list(cls._configs.keys())
    
    @classmethod
    def register_company(cls, company: str, config_class: type):
        """
        Registra una nueva compañía con su clase de configuración.
        
        Args:
            company: Nombre de la compañía
            config_class: Clase de configuración
        """
        cls._configs[company.lower()] = config_class
