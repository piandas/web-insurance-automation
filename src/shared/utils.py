"""Utilidades generales compartidas."""

import os
import datetime
from typing import Optional

class Utils:
    """Utilidades generales para el sistema."""
    
    @staticmethod
    def clean_date(date_str: str) -> str:
        """
        Limpia una fecha removiendo caracteres especiales.
        
        Args:
            date_str: Fecha en formato dd/mm/yyyy o similar
            
        Returns:
            Fecha limpia en formato ddmmyyyy
        """
        return date_str.replace('/', '').replace('-', '').replace(' ', '')
    
    @staticmethod
    def generate_filename(company: str, prefix: str = "Cotizacion", extension: str = "pdf") -> str:
        """
        Genera un nombre de archivo único.
        
        Args:
            company: Nombre de la compañía
            prefix: Prefijo del archivo
            extension: Extensión del archivo
            
        Returns:
            Nombre de archivo único
        """
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"{prefix}_{company.title()}_{timestamp}.{extension}"
    
    @staticmethod
    def ensure_directory(path: str) -> str:
        """
        Asegura que un directorio exista.
        
        Args:
            path: Ruta del directorio
            
        Returns:
            Ruta del directorio creado
        """
        os.makedirs(path, exist_ok=True)
        return path
    
    @staticmethod
    def validate_placa(placa: str) -> bool:
        """
        Valida el formato de una placa colombiana.
        
        Args:
            placa: Placa a validar
            
        Returns:
            True si es válida, False en caso contrario
        """
        if not placa or len(placa) != 6:
            return False
        
        # Formato: 3 letras + 3 números o 3 letras + 2 números + 1 letra
        return (
            (placa[:3].isalpha() and placa[3:].isdigit()) or
            (placa[:3].isalpha() and placa[3:5].isdigit() and placa[5].isalpha())
        )
    
    @staticmethod
    def validate_documento(documento: str) -> bool:
        """
        Valida que un documento sea numérico.
        
        Args:
            documento: Número de documento
            
        Returns:
            True si es válido, False en caso contrario
        """
        return documento.isdigit() and len(documento) >= 6

    @staticmethod
    def get_formatted_today(format_type: str = "dd/mm/yyyy") -> str:
        """
        Obtiene la fecha de hoy en el formato especificado.
        
        Args:
            format_type: Formato de fecha deseado
                - "dd/mm/yyyy": Formato con separadores (por defecto)
                - "ddmmyyyy": Formato sin separadores
                
        Returns:
            Fecha de hoy en el formato especificado
        """
        today = datetime.datetime.now()
        
        if format_type == "ddmmyyyy":
            return today.strftime("%d%m%Y")
        else:  # dd/mm/yyyy por defecto
            return today.strftime("%d/%m/%Y")
