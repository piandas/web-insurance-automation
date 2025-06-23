"""Configuración específica para Sura."""

import os
from .base_config import BaseConfig

class SuraConfig(BaseConfig):
    """Configuración específica para Sura."""
      # Credenciales (desde .env)
    USUARIO: str = os.getenv('SURA_USUARIO', '')
    CONTRASENA: str = os.getenv('SURA_CONTRASENA', '')
    
    # URLs específicas
    LOGIN_URL: str = 'https://login.sura.com/sso/servicelogin.aspx?continueTo=https%3A%2F%2Fasesores.segurossura.com.co&service=portaluasesores'
    BASE_URL: str = 'https://asesores.segurossura.com.co'
    
    # ==========================================
    # CONFIGURACIÓN DE DOCUMENTOS PARA LOGIN (Asesor/Agente)
    # ==========================================
    TIPO_DOCUMENTO_LOGIN: str = 'C'  # Tipo de documento para iniciar sesión
    
    # Tipos de documento disponibles para LOGIN:
    # C = CEDULA DE CIUDADANIA
    # E = CEDULA DE EXTRANJERIA  
    # P = PASAPORTE
    # N = NIT (Para empresas/agencias)
    
    # ==========================================
    # CONFIGURACIÓN DE DOCUMENTOS PARA CLIENTE
    # ==========================================
    CLIENT_DOCUMENT_NUMBER: str = '1020422674'  # Número de documento del cliente para desarrollo
    CLIENT_DOCUMENT_TYPE: str = 'C'  # Tipo de documento del cliente
    
    # Tipos de documento disponibles para CLIENTES (según el select del sistema):
    # C = CEDULA
    # E = CEDULA EXTRANJERIA  
    # D = DIPLOMATICO
    # X = DOC.IDENT. DE EXTRANJEROS
    # F = IDENT. FISCAL PARA EXT.
    # A = NIT
    # CA = NIT PERSONAS NATURALES
    # N = NUIP
    # P = PASAPORTE
    # R = REGISTRO CIVIL
    # T = TARJ.IDENTIDAD
    # TC = CERTIFICADO NACIDO VIVO
    # TP = PASAPORTE ONU
    # TE = PERMISO ESPECIAL PERMANENCIA
    # TS = SALVOCONDUCTO DE PERMANENCIA    # TF = PERMISO ESPECIAL FORMACN PEPFF
    # TT = PERMISO POR PROTECCION TEMPORL
    
    # ==========================================
    # DATOS DEL CLIENTE PARA COTIZACIÓN
    # ==========================================
    CLIENT_FIRST_NAME: str = 'SERGIO'
    CLIENT_SECOND_NAME: str = 'ALEXIS'
    CLIENT_FIRST_LASTNAME: str = 'AREIZA'
    CLIENT_SECOND_LASTNAME: str = 'LOAIZA'
    CLIENT_BIRTH_DATE: str = '1989-06-01'  # Formato YYYY-MM-DD
    CLIENT_GENDER: str = 'M'  # M = Masculino, F = Femenino
    CLIENT_PHONE: str = ''  # Opcional
    CLIENT_EMAIL: str = ''  # Opcional
    CLIENT_EMAIL_TYPE: str = ''  # TR = Trabajo, RS = Residencia
    CLIENT_OCCUPATION: str = 'ABOGADO'  # Ocupación del cliente

    # ==========================================
    # DATOS DE DIRECCIÓN PARA COTIZACIÓN
    # ==========================================
    CLIENT_ADDRESS: str = 'CRA 58 42-125'  # Dirección del cliente
    CLIENT_PHONE_WORK: str = '3807400'      # Teléfono de trabajo
    CLIENT_CITY: str = 'MEDELLIN'           # Ciudad del cliente
