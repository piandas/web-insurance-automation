# config.py
# Configuración global del proyecto
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Configuraciones de conexión (sensibles - desde .env)
    USUARIO: str = os.getenv('USUARIO', '')
    CONTRASENA: str = os.getenv('CONTRASENA', '')
    HEADLESS: bool = os.getenv('HEADLESS', 'False').lower() == 'true'
    BASE_URL: str = os.getenv('BASE_URL', 'https://www.allia2net.com.co')
    TIMEOUT: int = int(os.getenv('TIMEOUT', '30000'))
    
    # ==========================================
    # CONFIGURACIONES DE FLOTAS PAGE
    # ==========================================
    
    # Número de póliza para desarrollo (usado en click_policy_cell)
    POLICY_NUMBER: str = '23541048'
    
    # Tipo de ramo/seguro (usado en click_ramos_asociados)
    # Ejemplos: "Livianos Particulares", "Motos", etc.
    RAMO_SEGURO: str = 'Livianos Particulares'
    
    # Tipo de documento del asegurado
    # Opciones: NIT, REG_CIVIL_NACIMIENTO, NUIP, TARJETA_IDENTIDAD, 
    #          CEDULA_CIUDADANIA, CEDULA_EXTRANJERIA, PASAPORTE, 
    #          IDENTIFICACION_EXTRANJEROS, MENOR_SIN_IDENTIFICACION,
    #          PEP, OTROS_DOCUMENTOS, PPT, SOCIEDAD_EXTRANJERA
    TIPO_DOCUMENTO: str = 'CEDULA_CIUDADANIA'
    
    # Número de documento del asegurado
    NUMERO_DOCUMENTO: str = '1026258710'
    
    # ==========================================
    # CONFIGURACIONES DE PLACA PAGE
    # ==========================================
    
    # Placa del vehículo
    PLACA_VEHICULO: str = 'IOS190'
    
    # Datos del asegurado
    FECHA_NACIMIENTO: str = '01/06/1989'
    # Opciones de género: M (Masculino), F (Femenino), J (Jurídico)
    GENERO_ASEGURADO: str = 'M'
    
    # Ubicación del asegurado
    DEPARTAMENTO: str = 'ANTIOQUIA'
    CIUDAD: str = 'BELLO'
