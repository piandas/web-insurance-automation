"""Configuración unificada del cliente para todas las aseguradoras."""

from typing import Dict

class ClientConfig:
    """Configuración común del cliente que se usa en todas las aseguradoras."""
    
    # ==========================================
    # DATOS QUE SE CAMBIAN FRECUENTEMENTE
    # ==========================================
    
    VEHICLE_STATE: str = 'Nuevo'  # Opciones: "Nuevo", "Usado"
    
    # DATOS PERSONALES DEL CLIENTE (cambiar para cada cliente)
    CLIENT_DOCUMENT_NUMBER: str = '71750823'  # Número de documento del cliente
    CLIENT_FIRST_NAME: str = 'SERGIO'
    CLIENT_SECOND_NAME: str = 'ALEXIS'
    CLIENT_FIRST_LASTNAME: str = 'AREIZA'
    CLIENT_SECOND_LASTNAME: str = 'LOAIZA'
    CLIENT_BIRTH_DATE: str = '1974-07-06'  # Formato YYYY-DD-MM
    CLIENT_GENDER: str = 'M'  # M = Masculino, F = Femenino
  
    CLIENT_CITY: str = 'MEDELLIN'           # Ciudad del cliente 
    CLIENT_DEPARTMENT: str = 'ANTIOQUIA'    # Departamento
    
    # DATOS DEL VEHÍCULO (cambiar para cada vehículo)
    VEHICLE_PLATE: str = 'GEN294'  # Placa del vehículo
    VEHICLE_MODEL_YEAR: str = '2026'  # Año del modelo
    VEHICLE_BRAND: str = 'Mazda'  # Marca del vehículo
    VEHICLE_REFERENCE: str = 'Cx50 - utilitario deportivo 4x4'  # Referencia específica
    VEHICLE_FULL_REFERENCE: str = 'MAZDA CX-50 GRAND TOURING'  # Referencia completa para Fasecolda

    # Valor asegurado recibido (para Allianz, llenar en el input correspondiente)
    VEHICLE_INSURED_VALUE_RECEIVED: str = '30000000'  # Valor asegurado recibido, formato string como lo espera el input
    
    # CONFIGURACIÓN DE FASECOLDA
    ENABLE_FASECOLDA_SEARCH: bool = True  # Habilitar/deshabilitar búsqueda automática de códigos Fasecolda
    
    # Códigos Fasecolda manuales (usados cuando la búsqueda automática está deshabilitada)
    MANUAL_CF_CODE: str = '20900024001'  # Código CF manual
    MANUAL_CH_CODE: str = '20900024001'  # Código CH manual (puede ser diferente al CF)
    
    # PÓLIZA
    POLICY_NUMBER: str = '040007325677'  # Número de póliza común (principalmente para Sura)
    POLICY_NUMBER_ALLIANZ: str = '23541048'  # Número de póliza específico para Allianz
    
    
    
    
    
    # ==========================================
    # ⚙️ CONFIGURACIONES POR DEFECTO
    # ==========================================
    
    # Tipos de documento (formatos diferentes por aseguradora)
    CLIENT_DOCUMENT_TYPE_SURA: str = 'C'  # Para Sura: C = CEDULA DE CIUDADANIA
    CLIENT_DOCUMENT_TYPE_ALLIANZ: str = 'CEDULA_CIUDADANIA'  # Para Allianz: formato completo
    
    # Datos de dirección (por defecto)
    CLIENT_ADDRESS: str = 'CRA 58 42-125'  # Dirección del cliente
    CLIENT_PHONE_WORK: str = '3807400'      # Teléfono de trabajo
    CLIENT_OCCUPATION: str = 'ABOGADO'      # Ocupación del cliente
    
    # Configuración del vehículo (por defecto)
    VEHICLE_CATEGORY: str = 'Liviano pasajeros'  # Opciones: "Liviano pasajeros", "Motos"
    
    # Configuración de login para Sura (tipo de documento del asesor/agente)
    SURA_LOGIN_DOCUMENT_TYPE: str = 'C'  # C = CEDULA DE CIUDADANIA para el asesor
    
    # URLs y configuraciones técnicas
    FASECOLDA_URL: str = 'https://www.fasecolda.com/guia-de-valores-old/'
    
    # Configuraciones específicas por aseguradora
    SURA_SPECIFIC = {
        'selected_plan': 'Plan Autos Global',  # Plan seleccionado por defecto
        'auto_fetch_fasecolda': True,  # Buscar código Fasecolda automáticamente (respeta configuración global)
    }
    
    ALLIANZ_SPECIFIC = {
        'ramo_seguro': 'Livianos Particulares',  # Ramo de seguro
        'auto_fetch_fasecolda': True,  # Buscar código Fasecolda automáticamente (respeta configuración global)
    }
    
    # ==========================================
    # MÉTODOS HELPER PARA OBTENER DATOS ESPECÍFICOS
    # ==========================================
    
    @classmethod
    def get_client_document_type(cls, company: str) -> str:
        """Obtiene el tipo de documento según la aseguradora."""
        if company.lower() == 'sura':
            return cls.CLIENT_DOCUMENT_TYPE_SURA
        elif company.lower() == 'allianz':
            return cls.CLIENT_DOCUMENT_TYPE_ALLIANZ
        return cls.CLIENT_DOCUMENT_TYPE_SURA
    
    @classmethod
    def get_client_birth_date(cls, company: str) -> str:
        """
        Obtiene la fecha de nacimiento en el formato correcto según la aseguradora.
        
        Entrada: '1989-06-01' (formato YYYY-MM-DD)
        - Para Sura: devuelve '1989-06-01' (YYYY-MM-DD)
        - Para Allianz: devuelve '01/06/1989' (DD/MM/YYYY)
        """
        from datetime import datetime
        
        try:
            # Parsear la fecha en formato YYYY-MM-DD
            date_obj = datetime.strptime(cls.CLIENT_BIRTH_DATE, '%Y-%m-%d')
            
            if company.lower() == 'allianz':
                # Formato DD/MM/YYYY para Allianz
                return date_obj.strftime('%d/%m/%Y')
            else:
                # Formato YYYY-MM-DD para Sura (y por defecto)
                return cls.CLIENT_BIRTH_DATE
                
        except ValueError:
            # Si hay error en el formato, devolver tal como está
            return cls.CLIENT_BIRTH_DATE
    
    @classmethod
    def get_client_city(cls, company: str) -> str:
        """Obtiene la ciudad (ahora es la misma para ambas aseguradoras)."""
        return cls.CLIENT_CITY
    
    @classmethod
    def get_company_specific_config(cls, company: str) -> dict:
        """Obtiene configuración específica de la aseguradora."""
        if company.lower() == 'sura':
            return cls.SURA_SPECIFIC
        elif company.lower() == 'allianz':
            return cls.ALLIANZ_SPECIFIC
        return {}
    
    @classmethod
    def get_policy_number(cls, company: str = 'sura') -> str:
        """
        Obtiene el número de póliza según la aseguradora.
        
        - Para Sura: usa POLICY_NUMBER (040007325677)
        - Para Allianz: usa POLICY_NUMBER_ALLIANZ (23541048)
        """
        if company.lower() == 'allianz':
            return cls.POLICY_NUMBER_ALLIANZ
        return cls.POLICY_NUMBER
    
    @classmethod
    def get_full_client_name(cls) -> str:
        """Obtiene el nombre completo del cliente."""
        names = [cls.CLIENT_FIRST_NAME, cls.CLIENT_SECOND_NAME]
        lastnames = [cls.CLIENT_FIRST_LASTNAME, cls.CLIENT_SECOND_LASTNAME]
        
        full_name = ' '.join(filter(None, names + lastnames))
        return full_name.strip()
    
    @classmethod
    def is_fasecolda_enabled(cls) -> bool:
        """
        Verifica si la búsqueda de códigos Fasecolda está habilitada.
        
        Returns:
            bool: True si está habilitada, False si no
        """
        return cls.ENABLE_FASECOLDA_SEARCH
    
    @classmethod
    def get_default_fasecolda_code(cls) -> str:
        """
        Obtiene el código CF manual (método mantenido por compatibilidad).
        
        Returns:
            str: Código CF manual
        """
        return cls.MANUAL_CF_CODE
    
    @classmethod
    def get_manual_cf_code(cls) -> str:
        """
        Obtiene el código CF manual configurado.
        
        Returns:
            str: Código CF manual
        """
        return cls.MANUAL_CF_CODE
    
    @classmethod
    def get_manual_ch_code(cls) -> str:
        """
        Obtiene el código CH manual configurado.
        
        Returns:
            str: Código CH manual
        """
        return cls.MANUAL_CH_CODE
    
    @classmethod
    def get_manual_fasecolda_codes(cls) -> Dict[str, str]:
        """
        Obtiene ambos códigos Fasecolda manuales en el formato esperado por el sistema.
        
        Returns:
            Dict[str, str]: Diccionario con códigos CF y CH manuales
        """
        return {
            'cf_code': cls.MANUAL_CF_CODE,
            'ch_code': cls.MANUAL_CH_CODE
        }
    
    @classmethod
    def should_use_fasecolda_for_company(cls, company: str) -> bool:
        """
        Determina si se debe usar Fasecolda para una compañía específica.
        Combina la configuración global con la configuración específica de la compañía.
        
        Args:
            company: Nombre de la compañía ('sura', 'allianz')
            
        Returns:
            bool: True si se debe usar Fasecolda, False si no
        """
        # Primero verificar la configuración global
        if not cls.is_fasecolda_enabled():
            return False
            
        # Luego verificar la configuración específica de la compañía
        company_config = cls.get_company_specific_config(company)
        return company_config.get('auto_fetch_fasecolda', True)
    
    @classmethod
    def get_fasecolda_code_for_company(cls, company: str) -> Dict[str, str]:
        """
        Obtiene los códigos Fasecolda a usar para una compañía.
        Si Fasecolda está deshabilitado, devuelve los códigos manuales.
        
        Args:
            company: Nombre de la compañía ('sura', 'allianz')
            
        Returns:
            Dict[str, str]: Códigos Fasecolda a usar (manuales si está deshabilitado, None si debe buscar automáticamente)
        """
        if not cls.should_use_fasecolda_for_company(company):
            return cls.get_manual_fasecolda_codes()
        
        # Si está habilitado, devolver None para indicar que se debe buscar automáticamente
        return None
