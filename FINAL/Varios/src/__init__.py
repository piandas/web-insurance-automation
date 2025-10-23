"""Sistema de automatización de cotizaciones de seguros."""

# Versión del sistema
__version__ = "2.0.0"

# Módulos principales
from .core import BaseAutomation, AutomationManager, LoggerFactory, Constants
from .shared import BasePage, Utils
from .factory import AutomationFactory, ConfigFactory

__all__ = [
    'BaseAutomation', 
    'AutomationManager', 
    'LoggerFactory', 
    'Constants',
    'BasePage', 
    'Utils',
    'AutomationFactory', 
    'ConfigFactory'
]
