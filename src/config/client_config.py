"""Configuración unificada del cliente para todas las aseguradoras."""

class ClientConfig:
    """Configuración común del cliente que se usa en todas las aseguradoras."""
    
    # ==========================================
    # DATOS QUE SE CAMBIAN FRECUENTEMENTE
    # ==========================================
    
    VEHICLE_STATE: str = 'Nuevo'  # Opciones: "Nuevo", "Usado"
    
    # DATOS PERSONALES DEL CLIENTE (cambiar para cada cliente)
    CLIENT_DOCUMENT_NUMBER: str = '1020422674'  # Número de documento del cliente
    CLIENT_FIRST_NAME: str = 'SERGIO'
    CLIENT_SECOND_NAME: str = 'ALEXIS'
    CLIENT_FIRST_LASTNAME: str = 'AREIZA'
    CLIENT_SECOND_LASTNAME: str = 'LOAIZA'
    CLIENT_BIRTH_DATE: str = '1989-06-01'  # Formato YYYY-MM-DD 
    CLIENT_GENDER: str = 'M'  # M = Masculino, F = Femenino
  
    CLIENT_CITY: str = 'MEDELLIN'           # Ciudad del cliente 
    CLIENT_DEPARTMENT: str = 'ANTIOQUIA'    # Departamento
    
    # DATOS DEL VEHÍCULO (cambiar para cada vehículo)
    VEHICLE_PLATE: str = 'IOS190'  # Placa del vehículo
    VEHICLE_MODEL_YEAR: str = '2025'  # Año del modelo
    VEHICLE_BRAND: str = 'Chevrolet'  # Marca del vehículo
    VEHICLE_REFERENCE: str = 'Tracker [2] - utilitario deportivo 4x2'  # Referencia específica
    VEHICLE_FULL_REFERENCE: str = 'CHEVROLET TRACKER [2] LS TP 1200CC T'  # Referencia completa para Fasecolda
    
    # PÓLIZA
    POLICY_NUMBER: str = '040007325677'  # Número de póliza común (principalmente para Sura)
    POLICY_NUMBER_ALLIANZ: str = '23541048'  # Número de póliza específico para Allianz
    
    
    
    
    
    # ==========================================
    # ⚙️ CONFIGURACIONES POR DEFECTO (rara vez se cambian)
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
        'auto_fetch_fasecolda': True,  # Buscar código Fasecolda automáticamente
    }
    
    ALLIANZ_SPECIFIC = {
        'ramo_seguro': 'Livianos Particulares',  # Ramo de seguro
        'auto_fetch_fasecolda': True,  # Buscar código Fasecolda automáticamente
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
