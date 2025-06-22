"""Excepciones personalizadas para el sistema de automatización."""

class AutomationError(Exception):
    """Excepción base para errores de automatización."""
    pass

class LoginError(AutomationError):
    """Error específico de login."""
    pass

class NavigationError(AutomationError):
    """Error específico de navegación."""
    pass

class QuoteError(AutomationError):
    """Error específico de cotización."""
    pass

class ConfigurationError(AutomationError):
    """Error de configuración."""
    pass

class TimeoutError(AutomationError):
    """Error de timeout."""
    pass
