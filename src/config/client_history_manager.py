"""
Gestor del historial de clientes para el sistema de cotizaciones.
Maneja la carga, guardado y gestión del historial de datos de clientes.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

class ClientHistoryManager:
    """Gestiona el historial de datos de clientes."""
    
    def __init__(self):
        """Inicializa el gestor del historial."""
        # Ruta base del proyecto
        self.base_path = Path(__file__).parent.parent.parent
        self.history_dir = self.base_path / "client_history"
        
        # Crear directorio si no existe
        self.history_dir.mkdir(exist_ok=True)
        
        # Archivo principal de historial
        self.history_file = self.history_dir / "client_history.json"
        
        # Valores por defecto (los que están actualmente en client_config.py)
        self.default_values = {
            # DATOS PERSONALES DEL CLIENTE
            'client_document_number': '71750823',
            'client_first_name': 'SERGIO',
            'client_second_name': 'ALEXIS',
            'client_first_lastname': 'AREIZA',
            'client_second_lastname': 'LOAIZA',
            'client_birth_date': '1974-07-06',
            'client_gender': 'M',
            'client_city': 'MEDELLIN',
            'client_department': 'ANTIOQUIA',
            
            # DATOS DEL VEHÍCULO
            'vehicle_plate': 'GEN294',
            'vehicle_model_year': '2026',
            'vehicle_brand': 'Mazda',
            'vehicle_reference': 'Cx50 - utilitario deportivo 4x4',
            'vehicle_full_reference': 'MAZDA CX-50 GRAND TOURING',
            'vehicle_state': 'Nuevo',
            
            # CÓDIGOS FASECOLDA
            'manual_cf_code': '20900024001',
            'manual_ch_code': '20900024001',
            
            # PÓLIZAS
            'policy_number': '040007325677',
            'policy_number_allianz': '23541048'
        }
    
    def load_history(self) -> List[Dict[str, Any]]:
        """
        Carga el historial de clientes desde el archivo JSON.
        
        Returns:
            Lista de diccionarios con datos de clientes
        """
        try:
            if self.history_file.exists():
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
                    return history.get('clients', [])
            return []
        except Exception as e:
            print(f"Error cargando historial: {e}")
            return []
    
    def save_client(self, client_data: Dict[str, Any], client_name: str = None) -> bool:
        """
        Guarda un cliente en el historial.
        
        Args:
            client_data: Datos del cliente
            client_name: Nombre personalizado para identificar al cliente
            
        Returns:
            True si se guardó correctamente, False si no
        """
        try:
            # Cargar historial existente
            history = self.load_history()
            
            # Agregar metadata
            client_entry = {
                'id': datetime.now().strftime('%Y%m%d_%H%M%S'),
                'name': client_name or f"{client_data.get('client_first_name', '')} {client_data.get('client_first_lastname', '')}".strip(),
                'created_at': datetime.now().isoformat(),
                'data': client_data
            }
            
            # Agregar al inicio de la lista (más reciente primero)
            history.insert(0, client_entry)
            
            # Limitar a máximo 50 registros
            if len(history) > 50:
                history = history[:50]
            
            # Guardar
            history_data = {
                'last_updated': datetime.now().isoformat(),
                'clients': history
            }
            
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(history_data, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            print(f"Error guardando cliente: {e}")
            return False
    
    def update_client(self, client_id: str, client_data: Dict[str, Any], client_name: str = None) -> bool:
        """
        Actualiza un cliente existente en el historial.
        
        Args:
            client_id: ID del cliente a actualizar
            client_data: Nuevos datos del cliente
            client_name: Nuevo nombre para el cliente (opcional)
            
        Returns:
            True si se actualizó correctamente, False si no
        """
        try:
            history = self.load_history()
            
            # Buscar el cliente por ID
            for i, client in enumerate(history):
                if client.get('id') == client_id:
                    # Actualizar datos manteniendo ID y fecha de creación original
                    history[i]['data'] = client_data
                    history[i]['updated_at'] = datetime.now().isoformat()
                    
                    # Actualizar nombre si se proporciona
                    if client_name:
                        history[i]['name'] = client_name
                    
                    # Guardar historial actualizado
                    history_data = {
                        'last_updated': datetime.now().isoformat(),
                        'clients': history
                    }
                    
                    with open(self.history_file, 'w', encoding='utf-8') as f:
                        json.dump(history_data, f, indent=2, ensure_ascii=False)
                    
                    return True
            
            # Cliente no encontrado
            return False
            
        except Exception as e:
            print(f"Error actualizando cliente: {e}")
            return False
    
    def get_client_by_id(self, client_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene un cliente específico por su ID.
        
        Args:
            client_id: ID del cliente
            
        Returns:
            Datos del cliente o None si no se encuentra
        """
        history = self.load_history()
        for client in history:
            if client.get('id') == client_id:
                return client.get('data', {})
        return None
    
    def delete_client(self, client_id: str) -> bool:
        """
        Elimina un cliente del historial.
        
        Args:
            client_id: ID del cliente a eliminar
            
        Returns:
            True si se eliminó correctamente, False si no
        """
        try:
            history = self.load_history()
            history = [client for client in history if client.get('id') != client_id]
            
            history_data = {
                'last_updated': datetime.now().isoformat(),
                'clients': history
            }
            
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(history_data, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            print(f"Error eliminando cliente: {e}")
            return False
    
    def get_default_values(self) -> Dict[str, Any]:
        """
        Obtiene los valores por defecto.
        
        Returns:
            Diccionario con valores por defecto
        """
        return self.default_values.copy()
    
    def validate_client_data(self, data: Dict[str, Any]) -> Dict[str, str]:
        """
        Valida los datos del cliente.
        
        Args:
            data: Datos del cliente a validar
            
        Returns:
            Diccionario con errores de validación (vacío si no hay errores)
        """
        errors = {}
        
        # Validar campos requeridos
        required_fields = [
            'client_document_number', 'client_first_name', 'client_first_lastname',
            'client_birth_date', 'client_gender', 'client_city', 'client_department',
            'vehicle_model_year', 'vehicle_brand'
        ]
        
        # Solo requerir placa si el vehículo es usado
        vehicle_state = data.get('vehicle_state', 'Nuevo')
        if vehicle_state == 'Usado':
            required_fields.append('vehicle_plate')
        
        for field in required_fields:
            if not data.get(field, '').strip():
                errors[field] = 'Campo requerido'
        
        # Validar número de documento (solo números)
        doc_number = data.get('client_document_number', '')
        if doc_number and not doc_number.isdigit():
            errors['client_document_number'] = 'Solo se permiten números'
        
        # Validar fecha de nacimiento (formato YYYY-MM-DD)
        birth_date = data.get('client_birth_date', '')
        if birth_date:
            try:
                datetime.strptime(birth_date, '%Y-%m-%d')
            except ValueError:
                errors['client_birth_date'] = 'Formato inválido (YYYY-MM-DD)'
        
        # Validar género
        gender = data.get('client_gender', '')
        if gender and gender not in ['M', 'F']:
            errors['client_gender'] = 'Debe ser M o F'
        
        # Validar año del vehículo
        year = data.get('vehicle_model_year', '')
        if year:
            try:
                year_int = int(year)
                current_year = datetime.now().year
                if year_int < 1900 or year_int > current_year + 2:
                    errors['vehicle_model_year'] = f'Año debe estar entre 1900 y {current_year + 2}'
            except ValueError:
                errors['vehicle_model_year'] = 'Debe ser un número válido'
        
        # Validar valor asegurado (solo números)
        insured_value = data.get('vehicle_insured_value_received', '')
        if insured_value and not insured_value.isdigit():
            errors['vehicle_insured_value_received'] = 'Solo se permiten números'
        
        # Validar códigos Fasecolda (solo números)
        cf_code = data.get('manual_cf_code', '')
        if cf_code and not cf_code.isdigit():
            errors['manual_cf_code'] = 'Solo se permiten números'
            
        ch_code = data.get('manual_ch_code', '')
        if ch_code and not ch_code.isdigit():
            errors['manual_ch_code'] = 'Solo se permiten números'
        
        return errors
    
    def search_clients(self, search_term: str) -> List[Dict[str, Any]]:
        """
        Busca clientes por nombre o documento.
        
        Args:
            search_term: Término de búsqueda
            
        Returns:
            Lista de clientes que coinciden con la búsqueda
        """
        if not search_term:
            return self.load_history()
        
        history = self.load_history()
        results = []
        
        search_term = search_term.lower()
        
        for client in history:
            data = client.get('data', {})
            name = client.get('name', '').lower()
            document = data.get('client_document_number', '').lower()
            plate = data.get('vehicle_plate', '').lower()
            
            if (search_term in name or 
                search_term in document or 
                search_term in plate):
                results.append(client)
        
        return results
