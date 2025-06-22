"""Constantes globales del sistema."""

class Constants:
    """Constantes compartidas por todo el sistema."""
    
    # Compañías soportadas
    COMPANIES = {
        'ALLIANZ': 'allianz',
        'SURA': 'sura'
    }
    
    # Timeouts por defecto (milisegundos)
    DEFAULT_TIMEOUT = 30000
    SHORT_TIMEOUT = 10000
    LONG_TIMEOUT = 60000
    
    # Estados de carga
    LOAD_STATES = {
        'NETWORK_IDLE': 'networkidle',
        'DOM_LOADED': 'domcontentloaded',
        'LOADED': 'load'
    }
    
    # Tipos de documentos
    DOCUMENT_TYPES = {
        'CEDULA_CIUDADANIA': 'C',
        'CEDULA_EXTRANJERIA': 'X',
        'NIT': ' ',
        'PASAPORTE': 'P',
        'REG_CIVIL_NACIMIENTO': 'I',
        'NUIP': 'J',
        'TARJETA_IDENTIDAD': 'B',
        'IDENTIFICACION_EXTRANJEROS': 'L',
        'MENOR_SIN_IDENTIFICACION': 'Q',
        'PEP': 'E',
        'OTROS_DOCUMENTOS': 'S',
        'PPT': 'T',
        'SOCIEDAD_EXTRANJERA': 'W'
    }
    
    # Géneros
    GENDERS = {
        'MASCULINO': 'M',
        'FEMENINO': 'F',
        'JURIDICO': 'J'
    }
    
    # Configuraciones de logging
    LOG_FORMAT = '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
    
    # Configuraciones específicas de Sura
    SURA_KEYBOARD_APPEAR_TIMEOUT = 5000
    SURA_KEYBOARD_HIDE_TIMEOUT = 5000
    SURA_CLICK_DELAY = 300
    SURA_MOUSE_EVENT_DELAY = 50
