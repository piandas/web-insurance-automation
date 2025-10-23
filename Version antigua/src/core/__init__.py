"""Módulo core del sistema de automatización de seguros."""

from .base_automation import BaseAutomation
from .automation_manager import AutomationManager
from .logger_factory import LoggerFactory
from .constants import Constants

__all__ = ['BaseAutomation', 'AutomationManager', 'LoggerFactory', 'Constants']
