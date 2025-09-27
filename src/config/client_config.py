"""Configuración unificada del cliente para todas las aseguradoras."""

from typing import Dict
import os

class ClientConfig:
    """Configuración común del cliente que se usa en todas las aseguradoras."""
    
    # ==========================================
    # DATOS QUE SE CAMBIAN FRECUENTEMENTE
    # ==========================================
    
    VEHICLE_STATE: str = 'Nuevo'  # Opciones: "Nuevo", "Usado"
    
    # DATOS DINÁMICOS DEL CLIENTE (ahora se cargan desde GUI/historial)
    _current_client_data = None
    
    # VALORES POR DEFECTO (usados cuando no hay datos cargados)
    _DEFAULT_CLIENT_DATA = {
        'client_document_number': '71750823',
        'client_first_name': 'SERGIO',
        'client_second_name': 'ALEXIS',
        'client_first_lastname': 'AREIZA',
        'client_second_lastname': 'LOAIZA',
        'client_birth_date': '1974-07-06',
        'client_gender': 'M',
        'client_city': 'MEDELLIN',
        'client_department': 'ANTIOQUIA',
        'vehicle_plate': 'GEN294',
        'vehicle_model_year': '2026',
        'vehicle_brand': 'Mazda',
        'vehicle_reference': 'Cx50 - utilitario deportivo 4x4',
        'vehicle_full_reference': 'MAZDA CX-50 GRAND TOURING',
        'vehicle_state': 'Nuevo',
        'vehicle_insured_value': '',  # Nuevo campo para valor asegurado
        'manual_cf_code': '20900024001',
        'manual_ch_code': '20900024001',
        'policy_number': '040007325677',
        'policy_number_allianz': '23541048',
        'selected_fondo': ''  # Campo obligatorio, vacío por defecto
    }
    
    # CONFIGURACIÓN DE FASECOLDA
    ENABLE_FASECOLDA_SEARCH: bool = True  # Habilitar/deshabilitar búsqueda automática de códigos Fasecolda
    
    # ==========================================
    # MÉTODOS PARA ACCEDER A DATOS DINÁMICOS
    # ==========================================
    
    @classmethod
    def _get_current_data(cls):
        """Obtiene los datos actuales del cliente (desde GUI o valores por defecto)."""
        if cls._current_client_data is not None:
            return cls._current_client_data
        return cls._DEFAULT_CLIENT_DATA
    
    @classmethod
    def load_client_data(cls, client_data: Dict[str, str]) -> None:
        """Carga nuevos datos del cliente y configura variables de entorno para compatibilidad."""
        cls._current_client_data = client_data.copy()
        cls._update_class_variables()
        
        # También configurar variables de entorno para compatibilidad con _load_gui_overrides()
        cls._set_environment_variables(client_data)
    
    @classmethod
    def clear_client_data(cls) -> None:
        """Limpia los datos del cliente (vuelve a valores por defecto)."""
        cls._current_client_data = None
        cls._update_class_variables()
    
    # Propiedades dinámicas para mantener compatibilidad (usando variables de clase que se actualizan)
    CLIENT_DOCUMENT_NUMBER = '71750823'
    CLIENT_FIRST_NAME = 'SERGIO'
    CLIENT_SECOND_NAME = 'ALEXIS'
    CLIENT_FIRST_LASTNAME = 'AREIZA'
    CLIENT_SECOND_LASTNAME = 'LOAIZA'
    CLIENT_BIRTH_DATE = '1974-07-06'
    CLIENT_GENDER = 'M'
    CLIENT_CITY = 'MEDELLIN'
    CLIENT_DEPARTMENT = 'ANTIOQUIA'
    VEHICLE_PLATE = 'GEN294'
    VEHICLE_MODEL_YEAR = '2026'
    VEHICLE_BRAND = 'Mazda'
    VEHICLE_REFERENCE = 'Cx50 - utilitario deportivo 4x4'
    VEHICLE_FULL_REFERENCE = 'MAZDA CX-50 GRAND TOURING'
    VEHICLE_INSURED_VALUE = ''  # Nuevo campo para valor asegurado
    MANUAL_CF_CODE = '20900024001'
    MANUAL_CH_CODE = '20900024001'
    POLICY_NUMBER = '040007325677'
    POLICY_NUMBER_ALLIANZ = '23541048'
    SELECTED_FONDO = ''  # Campo obligatorio, vacío por defecto
    
    @classmethod
    def _update_class_variables(cls):
        """Actualiza las variables de clase con los datos actuales."""
        data = cls._get_current_data()
        cls._update_class_variables_direct()
    
    @classmethod 
    def _update_class_variables_direct(cls):
        """Actualiza las variables de clase directamente sin llamar _load_gui_overrides()."""
        data = cls._get_current_data()
        cls.CLIENT_DOCUMENT_NUMBER = data.get('client_document_number', cls._DEFAULT_CLIENT_DATA['client_document_number'])
        cls.CLIENT_FIRST_NAME = data.get('client_first_name', cls._DEFAULT_CLIENT_DATA['client_first_name'])
        cls.CLIENT_SECOND_NAME = data.get('client_second_name', cls._DEFAULT_CLIENT_DATA['client_second_name'])
        cls.CLIENT_FIRST_LASTNAME = data.get('client_first_lastname', cls._DEFAULT_CLIENT_DATA['client_first_lastname'])
        cls.CLIENT_SECOND_LASTNAME = data.get('client_second_lastname', cls._DEFAULT_CLIENT_DATA['client_second_lastname'])
        cls.CLIENT_BIRTH_DATE = data.get('client_birth_date', cls._DEFAULT_CLIENT_DATA['client_birth_date'])
        cls.CLIENT_GENDER = data.get('client_gender', cls._DEFAULT_CLIENT_DATA['client_gender'])
        cls.CLIENT_CITY = data.get('client_city', cls._DEFAULT_CLIENT_DATA['client_city'])
        cls.CLIENT_DEPARTMENT = data.get('client_department', cls._DEFAULT_CLIENT_DATA['client_department'])
        cls.VEHICLE_PLATE = data.get('vehicle_plate') if 'vehicle_plate' in data else cls._DEFAULT_CLIENT_DATA['vehicle_plate']
        cls.VEHICLE_MODEL_YEAR = data.get('vehicle_model_year', cls._DEFAULT_CLIENT_DATA['vehicle_model_year'])
        cls.VEHICLE_BRAND = data.get('vehicle_brand', cls._DEFAULT_CLIENT_DATA['vehicle_brand'])
        cls.VEHICLE_REFERENCE = data.get('vehicle_reference', cls._DEFAULT_CLIENT_DATA['vehicle_reference'])
        cls.VEHICLE_FULL_REFERENCE = data.get('vehicle_full_reference', cls._DEFAULT_CLIENT_DATA['vehicle_full_reference'])
        cls.VEHICLE_STATE = data.get('vehicle_state', cls._DEFAULT_CLIENT_DATA['vehicle_state'])
        cls.VEHICLE_INSURED_VALUE = data.get('vehicle_insured_value', cls._DEFAULT_CLIENT_DATA['vehicle_insured_value'])
        cls.MANUAL_CF_CODE = data.get('manual_cf_code', cls._DEFAULT_CLIENT_DATA['manual_cf_code'])
        cls.MANUAL_CH_CODE = data.get('manual_ch_code', cls._DEFAULT_CLIENT_DATA['manual_ch_code'])
        cls.POLICY_NUMBER = data.get('policy_number', cls._DEFAULT_CLIENT_DATA['policy_number'])
        cls.POLICY_NUMBER_ALLIANZ = data.get('policy_number_allianz', cls._DEFAULT_CLIENT_DATA['policy_number_allianz'])
        cls.SELECTED_FONDO = data.get('selected_fondo', cls._DEFAULT_CLIENT_DATA['selected_fondo'])
    
    @classmethod
    def _set_environment_variables(cls, client_data: Dict[str, str]) -> None:
        """Configura variables de entorno GUI_* desde los datos del cliente."""
        import os
        
        # Mapeo de keys de client_data a variables de entorno
        env_mapping = {
            'client_document_number': 'GUI_CLIENT_DOCUMENT_NUMBER',
            'client_first_name': 'GUI_CLIENT_FIRST_NAME',
            'client_second_name': 'GUI_CLIENT_SECOND_NAME',
            'client_first_lastname': 'GUI_CLIENT_FIRST_LASTNAME',
            'client_second_lastname': 'GUI_CLIENT_SECOND_LASTNAME',
            'client_birth_date': 'GUI_CLIENT_BIRTH_DATE',
            'client_gender': 'GUI_CLIENT_GENDER',
            'client_city': 'GUI_CLIENT_CITY',
            'client_department': 'GUI_CLIENT_DEPARTMENT',
            'vehicle_plate': 'GUI_VEHICLE_PLATE',
            'vehicle_model_year': 'GUI_VEHICLE_MODEL_YEAR',
            'vehicle_brand': 'GUI_VEHICLE_BRAND',
            'vehicle_reference': 'GUI_VEHICLE_REFERENCE',
            'vehicle_full_reference': 'GUI_VEHICLE_FULL_REFERENCE',
            'vehicle_state': 'GUI_VEHICLE_STATE',
            'vehicle_insured_value': 'GUI_VEHICLE_INSURED_VALUE',
            'manual_cf_code': 'GUI_MANUAL_CF_CODE',
            'manual_ch_code': 'GUI_MANUAL_CH_CODE',
            'policy_number': 'GUI_POLICY_NUMBER',
            'policy_number_allianz': 'GUI_POLICY_NUMBER_ALLIANZ',
            'selected_fondo': 'GUI_SELECTED_FONDO'
        }
        
        # Configurar variables de entorno
        for data_key, env_var in env_mapping.items():
            if data_key in client_data:  # Si la key existe en client_data, usar ese valor (incluso si es vacío)
                value = client_data[data_key]
                os.environ[env_var] = str(value) if value is not None else ""
            elif env_var in os.environ:
                # Limpiar variable si la key no existe en client_data
                del os.environ[env_var]

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
            # Obtener la fecha desde los datos dinámicos
            birth_date = cls.CLIENT_BIRTH_DATE
            # Parsear la fecha en formato YYYY-MM-DD
            date_obj = datetime.strptime(birth_date, '%Y-%m-%d')
            
            if company.lower() == 'allianz':
                # Formato DD/MM/YYYY para Allianz
                return date_obj.strftime('%d/%m/%Y')
            else:
                # Formato YYYY-MM-DD para Sura (y por defecto)
                return birth_date
                
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
        Aplica overrides de GUI si están disponibles.
        
        Returns:
            bool: True si está habilitada, False si no
        """
        # Cargar overrides de la GUI
        cls._load_gui_overrides()
        return cls.ENABLE_FASECOLDA_SEARCH
    
    @classmethod
    def get_vehicle_state(cls) -> str:
        """
        Obtiene el estado del vehículo con overrides de GUI.
        
        Returns:
            str: Estado del vehículo ('Nuevo' o 'Usado')
        """
        # Cargar overrides de la GUI
        cls._load_gui_overrides()
        return cls.VEHICLE_STATE
    
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

    # ==========================================
    # MÉTODOS PARA ACTUALIZACIÓN DINÁMICA (GUI)
    # ==========================================
    
    @classmethod
    def _load_gui_overrides(cls):
        """Carga configuraciones desde variables de entorno (GUI tiene prioridad)."""
        import os
        
        # Override del estado del vehículo desde la GUI
        gui_vehicle_state = os.environ.get('GUI_VEHICLE_STATE')
        if gui_vehicle_state and gui_vehicle_state in ['Nuevo', 'Usado']:
            cls.VEHICLE_STATE = gui_vehicle_state
        
        # Override de Fasecolda desde la GUI
        gui_fasecolda = os.environ.get('GUI_FASECOLDA_ENABLED')
        if gui_fasecolda is not None:
            cls.ENABLE_FASECOLDA_SEARCH = gui_fasecolda.lower() == 'true'
        
        # CRÍTICO: Cargar TODOS los datos del cliente desde variables de entorno de GUI
        gui_client_data = {}
        
        # Mapeo de variables de entorno a keys del diccionario
        env_mapping = {
            'GUI_CLIENT_DOCUMENT_NUMBER': 'client_document_number',
            'GUI_CLIENT_FIRST_NAME': 'client_first_name',
            'GUI_CLIENT_SECOND_NAME': 'client_second_name',
            'GUI_CLIENT_FIRST_LASTNAME': 'client_first_lastname',
            'GUI_CLIENT_SECOND_LASTNAME': 'client_second_lastname',
            'GUI_CLIENT_BIRTH_DATE': 'client_birth_date',
            'GUI_CLIENT_GENDER': 'client_gender',
            'GUI_CLIENT_CITY': 'client_city',
            'GUI_CLIENT_DEPARTMENT': 'client_department',
            'GUI_VEHICLE_PLATE': 'vehicle_plate',
            'GUI_VEHICLE_MODEL_YEAR': 'vehicle_model_year',
            'GUI_VEHICLE_BRAND': 'vehicle_brand',
            'GUI_VEHICLE_REFERENCE': 'vehicle_reference',
            'GUI_VEHICLE_FULL_REFERENCE': 'vehicle_full_reference',
            'GUI_VEHICLE_STATE': 'vehicle_state',
            'GUI_VEHICLE_INSURED_VALUE': 'vehicle_insured_value',
            'GUI_MANUAL_CF_CODE': 'manual_cf_code',
            'GUI_MANUAL_CH_CODE': 'manual_ch_code',
            'GUI_POLICY_NUMBER': 'policy_number',
            'GUI_POLICY_NUMBER_ALLIANZ': 'policy_number_allianz',
            'GUI_SELECTED_FONDO': 'selected_fondo'
        }
        
        # Cargar datos desde variables de entorno
        for env_var, data_key in env_mapping.items():
            value = os.environ.get(env_var)
            if value is not None:  # Solo aplicar si la variable existe (incluso si está vacía)
                print(f"🔍 DEBUG ClientConfig - Cargando {env_var}={value} -> {data_key}")
                # Normalizar ciertos campos a mayúsculas para consistencia
                if data_key in ['client_first_name', 'client_second_name', 'client_first_lastname', 
                               'client_second_lastname', 'client_city', 'client_department', 
                               'vehicle_brand', 'vehicle_reference', 'vehicle_full_reference']:
                    value = value.upper()
                gui_client_data[data_key] = value
        
        # Si se encontraron datos de GUI, cargarlos directamente en _current_client_data
        if gui_client_data:
            # Si ya hay datos cargados, actualizarlos con los datos de GUI
            if cls._current_client_data:
                cls._current_client_data.update(gui_client_data)
            else:
                cls._current_client_data = gui_client_data.copy()
            # Actualizar variables de clase sin llamar _load_gui_overrides otra vez
            cls._update_class_variables_direct()
    
    @classmethod
    def update_vehicle_state(cls, state: str) -> None:
        """Actualiza el estado del vehículo."""
        if state in ['Nuevo', 'Usado']:
            cls.VEHICLE_STATE = state
        else:
            raise ValueError(f"Estado inválido: {state}. Debe ser 'Nuevo' o 'Usado'")
    
    @classmethod
    def update_fasecolda_search(cls, enabled: bool) -> None:
        """Actualiza la configuración de búsqueda automática de Fasecolda."""
        cls.ENABLE_FASECOLDA_SEARCH = enabled
    
    @classmethod
    def get_current_config(cls) -> Dict[str, any]:
        """Obtiene la configuración actual (con overrides de GUI si aplican)."""
        # Cargar overrides de la GUI antes de devolver la configuración
        cls._load_gui_overrides()
        
        return {
            'vehicle_state': cls.VEHICLE_STATE,
            'fasecolda_enabled': cls.ENABLE_FASECOLDA_SEARCH,
            'vehicle_brand': cls.VEHICLE_BRAND,
            'vehicle_reference': cls.VEHICLE_REFERENCE,
            'vehicle_year': cls.VEHICLE_MODEL_YEAR,
            'client_name': f"{cls.CLIENT_FIRST_NAME} {cls.CLIENT_FIRST_LASTNAME}",
            'vehicle_plate': cls.VEHICLE_PLATE,
            'vehicle_insured_value': cls.VEHICLE_INSURED_VALUE
        }
    
    @classmethod
    def get_vehicle_insured_value(cls) -> str:
        """
        Obtiene el valor asegurado del vehículo.
        
        Returns:
            str: Valor asegurado (solo números, ej: "95000000")
        """
        cls._load_gui_overrides()
        print(f"🔍 DEBUG ClientConfig - Valor asegurado actual: '{cls.VEHICLE_INSURED_VALUE}'")
        return cls.VEHICLE_INSURED_VALUE
    
    @classmethod
    def get_selected_fondo(cls) -> str:
        """
        Obtiene el fondo seleccionado.
        
        Returns:
            str: Fondo seleccionado (ej: "EPM", "FEPEP")
        """
        cls._load_gui_overrides()
        return cls.SELECTED_FONDO
    
    @classmethod
    def ensure_vehicle_insured_value(cls) -> bool:
        """
        Verifica que exista valor asegurado y lo solicita al usuario si no está disponible.
        
        Returns:
            bool: True si hay valor asegurado disponible, False si usuario canceló
        """
        try:
            # Cargar configuraciones actuales
            cls._load_gui_overrides()
            
            # Verificar si ya tenemos valor asegurado
            current_value = cls.VEHICLE_INSURED_VALUE
            if current_value and current_value.strip():
                print(f"💰 Valor asegurado ya configurado: {current_value}")
                return True
            
            # Si no hay valor, pedirlo al usuario
            print("⚠️ Valor asegurado no encontrado, solicitando al usuario...")
            
            import tkinter as tk
            from tkinter import simpledialog, messagebox
            
            # Crear ventana principal oculta
            root = tk.Tk()
            root.withdraw()  # Ocultar ventana principal
            root.attributes('-topmost', True)  # Mantener ventana al frente
            
            # Determinar mensaje según estado del vehículo
            if cls.VEHICLE_STATE.lower() == 'nuevo':
                mensaje = ("No se encontró valor asegurado configurado.\n"
                          "Por favor ingrese el valor asegurado para el vehículo NUEVO:")
            else:
                mensaje = ("Valor asegurado no disponible para vehículo USADO.\n"
                          "Por favor ingrese el valor asegurado manualmente:")
            
            # Mostrar diálogo para ingresar valor
            valor_usuario = simpledialog.askstring(
                "Valor Asegurado Requerido",
                mensaje,
                parent=root
            )
            
            # Cerrar ventana
            root.destroy()
            
            if valor_usuario:
                # Limpiar el valor (remover comas, puntos, símbolos)
                valor_limpio = valor_usuario.replace(",", "").replace(".", "").replace("$", "").strip()
                
                # Validar que sea numérico
                if valor_limpio.isdigit():
                    print(f"💰 Usuario ingresó valor asegurado: {valor_limpio}")
                    # Actualizar el config con el nuevo valor
                    cls.VEHICLE_INSURED_VALUE = valor_limpio
                    # CRÍTICO: También actualizar la variable de entorno para evitar sobrescritura
                    import os
                    os.environ['GUI_VEHICLE_INSURED_VALUE'] = valor_limpio
                    print(f"🔒 Variable de entorno GUI actualizada: GUI_VEHICLE_INSURED_VALUE={valor_limpio}")
                    return True
                else:
                    print(f"❌ Valor ingresado no es válido: '{valor_usuario}'")
                    messagebox.showerror("Error", f"El valor '{valor_usuario}' no es válido. Debe contener solo números.")
                    return False
            else:
                print("⚠️ Usuario canceló ingreso de valor asegurado")
                return False
                
        except Exception as e:
            print(f"❌ Error verificando valor asegurado: {e}")
            return False
    
    