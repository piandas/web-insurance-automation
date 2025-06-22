"""Recursos compartidos entre todas las aseguradoras."""

from .base_page import BasePage
from .utils import Utils
from .exceptions import AutomationError, LoginError, NavigationError, QuoteError

__all__ = ['BasePage', 'Utils', 'AutomationError', 'LoginError', 'NavigationError', 'QuoteError']
