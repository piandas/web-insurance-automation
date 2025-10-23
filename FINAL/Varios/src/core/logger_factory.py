"""Factory para crear y configurar loggers por compañía."""

import os
import logging
from typing import Optional
from .constants import Constants

class LoggerFactory:
    """Factory para crear loggers específicos por compañía."""
    
    @staticmethod
    def create_logger(
        company: str, 
        name: Optional[str] = None,
        log_level: int = logging.INFO,
        base_dir: Optional[str] = None
    ) -> logging.Logger:
        """
        Crea un logger específico para una compañía.
        
        Args:
            company: Nombre de la compañía ('allianz', 'sura', etc.)
            name: Nombre específico del logger (opcional)
            log_level: Nivel de logging
            base_dir: Directorio base del proyecto
            
        Returns:
            Logger configurado
        """
        if not base_dir:
            # Subir 4 niveles: core -> src -> Varios -> raíz del proyecto
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        
        logger_name = f"{company}.{name}" if name else company
        logger = logging.getLogger(logger_name)
        
        # Evitar duplicar handlers
        if logger.handlers:
            return logger
            
        logger.setLevel(log_level)
        
        # Crear formatter
        formatter = logging.Formatter(
            Constants.LOG_FORMAT,
            datefmt=Constants.LOG_DATE_FORMAT
        )
        
        # Handler para consola
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # Handler para archivo
        log_dir = os.path.join(base_dir, 'Varios', 'LOGS', company)
        os.makedirs(log_dir, exist_ok=True)
        
        log_file = os.path.join(log_dir, f'{company}.log')
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # Evitar propagación para evitar logs duplicados
        logger.propagate = False
        
        return logger
    
    @staticmethod
    def clear_all_handlers():
        """Limpia todos los handlers de logging para evitar duplicaciones."""
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)
