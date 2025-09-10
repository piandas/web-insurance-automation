"""
Manejador de plantillas Excel para diferentes fondos.

Este módulo se encarga de leer las plantillas Excel de los diferentes fondos
(EPM, FEPEP, etc.) y llenarlas con la información de cotizaciones.
"""

import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path
import openpyxl
from openpyxl.drawing.image import Image
import shutil

from ..config.client_config import ClientConfig
from ..core.logger_factory import LoggerFactory


class TemplateHandler:
    """Manejador de plantillas Excel para diferentes fondos."""
    
    def __init__(self):
        self.logger = LoggerFactory.create_logger('template_handler')
        self.base_path = Path(__file__).parent.parent.parent
        self.templates_path = self.base_path / "Bases Consolidados"
        self.logos_path = self.base_path / "docs" / "IMAGENES FONDOS"
        self.consolidados_path = self.base_path / "Consolidados"
        
        # Mapeo de fondos a archivos de plantilla (dinámico)
        self.template_files = self._discover_template_files()
        
        # Mapeo de fondos a archivos de logo (dinámico)
        self.logo_files = self._discover_logo_files()
        
        # Crear directorio si no existe
        self.consolidados_path.mkdir(exist_ok=True)
    
    def _discover_template_files(self) -> Dict[str, str]:
        """Descubre automáticamente las plantillas disponibles."""
        templates = {}
        try:
            if self.templates_path.exists():
                # Buscar archivos que empiecen con "PANTILLA" o "PLANTILLA"
                for file_path in self.templates_path.glob("*ANTILLA*.xlsx"):
                    file_name = file_path.name
                    
                    # Filtrar archivos temporales de Excel (que empiecen con ~$)
                    if file_name.startswith("~$"):
                        continue
                    
                    # Extraer nombre del fondo del nombre del archivo
                    # Formato esperado: "PANTILLA FONDO.xlsx" o "PLANTILLA FONDO.xlsx"
                    if "PANTILLA" in file_name or "PLANTILLA" in file_name:
                        # Dividir por espacios y tomar la parte después de PANTILLA/PLANTILLA
                        parts = file_name.replace("PANTILLA", "").replace("PLANTILLA", "").strip()
                        fondo_name = parts.replace(".xlsx", "").strip()
                        if fondo_name:
                            templates[fondo_name] = file_name
                            self.logger.info(f"📋 Plantilla encontrada: {fondo_name} -> {file_name}")
        except Exception as e:
            self.logger.error(f"Error descubriendo plantillas: {e}")
        
        return templates
    
    def _discover_logo_files(self) -> Dict[str, str]:
        """Descubre automáticamente los logos disponibles."""
        logos = {}
        try:
            if self.logos_path.exists():
                # Buscar todos los archivos .png
                for file_path in self.logos_path.glob("*.png"):
                    file_name = file_path.name
                    fondo_name = file_path.stem  # Nombre sin extensión
                    # Filtrar algunos logos que no son fondos
                    if fondo_name not in ['INFONDO']:  # Puedes añadir más exclusiones aquí
                        logos[fondo_name] = file_name
                        self.logger.info(f"🎨 Logo encontrado: {fondo_name} -> {file_name}")
        except Exception as e:
            self.logger.error(f"Error descubriendo logos: {e}")
        
        return logos
    
    def get_available_fondos(self) -> List[str]:
        """Obtiene la lista de fondos disponibles basada en las plantillas existentes."""
        available_fondos = []
        for fondo, template_file in self.template_files.items():
            template_path = self.templates_path / template_file
            if template_path.exists():
                available_fondos.append(fondo)
            else:
                self.logger.warning(f"Plantilla no encontrada para {fondo}: {template_path}")
        
        return available_fondos
    
    def generate_filename(self) -> str:
        """Genera un nombre único para el archivo basado en la fecha actual."""
        today = datetime.now()
        base_name = f"Cotizacion{today.strftime('%d-%m-%y')}"
        extension = ".xlsx"
        
        # Verificar si el archivo ya existe y generar nombre único
        counter = 0
        filename = f"{base_name}{extension}"
        full_path = self.consolidados_path / filename
        
        while full_path.exists():
            counter += 1
            filename = f"{base_name}({counter}){extension}"
            full_path = self.consolidados_path / filename
            
        return filename
    
    def create_consolidado_from_template(self, fondo: str, sura_data: Dict[str, Any], 
                                       sura_plans: Dict[str, str], allianz_plans: Dict[str, str], 
                                       bolivar_solidaria_plans: Dict[str, str]) -> str:
        """
        Crea un consolidado usando la plantilla del fondo especificado.
        
        Args:
            fondo: Nombre del fondo (EPM, FEPEP, etc.)
            sura_data: Datos del cliente de Sura
            sura_plans: Planes de Sura
            allianz_plans: Planes de Allianz
            bolivar_solidaria_plans: Planes calculados de Bolívar y Solidaria
            
        Returns:
            str: Ruta del archivo Excel creado
        """
        self.logger.info(f"📊 Creando consolidado usando plantilla de {fondo}")
        
        # Verificar que el fondo existe
        if fondo not in self.template_files:
            raise ValueError(f"Fondo no soportado: {fondo}")
        
        template_file = self.template_files[fondo]
        template_path = self.templates_path / template_file
        
        if not template_path.exists():
            raise FileNotFoundError(f"Plantilla no encontrada: {template_path}")
        
        # Generar nombre del archivo de salida
        output_filename = self.generate_filename()
        output_path = self.consolidados_path / output_filename
        
        # Copiar plantilla como base
        shutil.copy2(template_path, output_path)
        self.logger.info(f"📋 Plantilla copiada a: {output_path}")
        
        # Abrir el archivo Excel
        try:
            workbook = openpyxl.load_workbook(output_path)
            worksheet = workbook.active  # Usar la primera hoja
            
            # Llenar datos según la estructura de la plantilla
            self._fill_template_data(worksheet, fondo, sura_data, sura_plans, allianz_plans, bolivar_solidaria_plans)
            
            # Añadir logo si existe
            self._add_logo_to_template(worksheet, fondo)
            
            # Guardar el archivo
            workbook.save(output_path)
            workbook.close()
            
            self.logger.info(f"✅ Consolidado creado exitosamente: {output_filename}")
            return str(output_path)
            
        except Exception as e:
            self.logger.error(f"❌ Error creando consolidado desde plantilla: {e}")
            # Si hay error, intentar limpiar el archivo parcial
            try:
                if output_path.exists():
                    output_path.unlink()
            except:
                pass
            raise
    
    def _fill_template_data(self, worksheet, fondo: str, sura_data: Dict[str, Any], 
                          sura_plans: Dict[str, str], allianz_plans: Dict[str, str], 
                          bolivar_solidaria_plans: Dict[str, str]):
        """
        Llena los datos en la plantilla Excel.
        
        Esta función mapea los datos a las celdas específicas según la estructura
        que mencionaste en tu requerimiento.
        """
        try:
            # Fecha de cotización (A3 -> B3)
            if worksheet['A3'].value and 'fecha' in str(worksheet['A3'].value).lower():
                worksheet['B3'] = datetime.now().strftime('%d/%m/%Y')
            
            # Nombre funcionario o asociado (dejar vacío por ahora)
            # CC funcionario (dejar vacío por ahora)
            
            # Nombre asegurado (A6 -> B6)
            if worksheet['A6'].value and 'nombre' in str(worksheet['A6'].value).lower():
                nombre_completo = f"{sura_data.get('CLIENT_FIRST_NAME', '')} {sura_data.get('CLIENT_SECOND_NAME', '')} {sura_data.get('CLIENT_FIRST_LASTNAME', '')} {sura_data.get('CLIENT_SECOND_LASTNAME', '')}"
                worksheet['B6'] = nombre_completo.strip()
            
            # CC Asegurado
            cc_row = self._find_cell_with_text(worksheet, 'c.c', 'cedula', 'documento')
            if cc_row:
                worksheet.cell(row=cc_row, column=2).value = sura_data.get('CLIENT_DOCUMENT_NUMBER', '')
            
            # Placa
            placa_row = self._find_cell_with_text(worksheet, 'placa')
            if placa_row:
                worksheet.cell(row=placa_row, column=2).value = ClientConfig.VEHICLE_PLATE
            
            # Modelo
            modelo_row = self._find_cell_with_text(worksheet, 'modelo')
            if modelo_row:
                worksheet.cell(row=modelo_row, column=2).value = ClientConfig.VEHICLE_MODEL_YEAR
            
            # Marca Y Tipo
            marca_row = self._find_cell_with_text(worksheet, 'marca')
            if marca_row:
                worksheet.cell(row=marca_row, column=2).value = f"{ClientConfig.VEHICLE_BRAND} - {ClientConfig.VEHICLE_REFERENCE}"
            
            # Clase (referencia escogida en fasecolda)
            clase_row = self._find_cell_with_text(worksheet, 'clase')
            if clase_row:
                worksheet.cell(row=clase_row, column=2).value = ClientConfig.VEHICLE_REFERENCE
            
            # Código Fasecolda (ambos códigos CF y CH)
            codigo_row = self._find_cell_with_text(worksheet, 'codigo fasecolda', 'fasecolda')
            if codigo_row:
                cf_code = ClientConfig.MANUAL_CF_CODE
                ch_code = ClientConfig.MANUAL_CH_CODE
                worksheet.cell(row=codigo_row, column=2).value = f"CF: {cf_code} / CH: {ch_code}"
            
            # Ciudad de circulación
            ciudad_row = self._find_cell_with_text(worksheet, 'ciudad')
            if ciudad_row:
                worksheet.cell(row=ciudad_row, column=2).value = ClientConfig.CLIENT_CITY
            
            # Valor asegurado
            valor_row = self._find_cell_with_text(worksheet, 'valor asegurado')
            if valor_row:
                valor_asegurado = self._get_valor_asegurado()
                if valor_asegurado:
                    worksheet.cell(row=valor_row, column=2).value = self._format_currency(valor_asegurado)
            
            # Valor accesorios (dejar vacío por ahora)
            
            # Valor asegurado total
            valor_total_row = self._find_cell_with_text(worksheet, 'valor asegurado total', 'total asegurado')
            if valor_total_row:
                valor_asegurado = self._get_valor_asegurado()
                if valor_asegurado:
                    worksheet.cell(row=valor_total_row, column=2).value = self._format_currency(valor_asegurado)
            
            self.logger.info(f"✅ Datos básicos llenados en plantilla de {fondo}")
            
        except Exception as e:
            self.logger.error(f"❌ Error llenando datos en plantilla: {e}")
            raise
    
    def _find_cell_with_text(self, worksheet, *search_terms) -> Optional[int]:
        """
        Busca una celda que contenga alguno de los términos especificados en la columna A.
        
        Returns:
            int: Número de fila si se encuentra, None si no se encuentra
        """
        try:
            for row in range(1, 50):  # Buscar en las primeras 50 filas
                cell_value = worksheet.cell(row=row, column=1).value
                if cell_value:
                    cell_text = str(cell_value).lower()
                    for term in search_terms:
                        if term.lower() in cell_text:
                            return row
            return None
        except Exception:
            return None
    
    def _get_valor_asegurado(self) -> Optional[str]:
        """Obtiene el valor asegurado desde la configuración."""
        try:
            # Para vehículos nuevos: usar valor desde interfaz
            if ClientConfig.VEHICLE_STATE.lower() == 'nuevo':
                return ClientConfig.get_vehicle_insured_value()
            else:
                # Para vehículos usados: usar valor extraído de Allianz
                return ClientConfig.get_vehicle_insured_value()
        except Exception as e:
            self.logger.error(f"Error obteniendo valor asegurado: {e}")
            return None
    
    def _format_currency(self, value: str) -> str:
        """Formatea un valor como moneda colombiana."""
        try:
            if not value or not value.strip():
                return ""
            
            # Limpiar el valor (quitar caracteres no numéricos)
            clean_value = ''.join(c for c in value if c.isdigit())
            if not clean_value:
                return ""
            
            # Convertir a número y formatear
            num = int(clean_value)
            formatted = f"{num:,}".replace(",", ".")
            return f"${formatted}"
            
        except Exception:
            return value
    
    def _add_logo_to_template(self, worksheet, fondo: str):
        """Añade el logo del fondo a la esquina superior izquierda."""
        try:
            if fondo not in self.logo_files:
                self.logger.warning(f"No hay logo configurado para {fondo}")
                return
            
            logo_file = self.logo_files[fondo]
            logo_path = self.logos_path / logo_file
            
            if not logo_path.exists():
                self.logger.warning(f"Logo no encontrado: {logo_path}")
                return
            
            # Crear objeto imagen
            img = Image(logo_path)
            
            # Redimensionar logo (ajusta según necesidades)
            img.width = 100  # pixels
            img.height = 50  # pixels
            
            # Posicionar en la esquina superior izquierda (A1)
            worksheet.add_image(img, 'A1')
            
            self.logger.info(f"✅ Logo de {fondo} añadido a la plantilla")
            
        except Exception as e:
            self.logger.error(f"❌ Error añadiendo logo de {fondo}: {e}")
            # No fallar si no se puede añadir el logo
