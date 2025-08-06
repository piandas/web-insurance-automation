"""
Consolidador de cotizaciones de seguros.

Este módulo se encarga de crear un archivo Excel consolidado con los resultados
de las cotizaciones de Sura y Allianz una vez que ambas automatizaciones han finalizado.
"""

import os
import re
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
import PyPDF2
import pandas as pd

from ..config.sura_config import SuraConfig
from ..core.logger_factory import LoggerFactory


class CotizacionConsolidator:
    """Consolidador de cotizaciones de Sura y Allianz."""
    
    def __init__(self):
        self.logger = LoggerFactory.create_logger('consolidator')
        self.base_path = Path(__file__).parent.parent.parent
        self.consolidados_path = self.base_path / "Consolidados"
        self.downloads_path = self.base_path / "downloads"
        
        # Crear directorio si no existe
        self.consolidados_path.mkdir(exist_ok=True)
        
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
    
    def extract_sura_data(self) -> Dict[str, Any]:
        """Extrae los datos de configuración de Sura."""
        self.logger.info("Extrayendo datos de configuración de Sura...")
        
        config = SuraConfig()
        
        sura_data = {
            'CLIENT_DOCUMENT_NUMBER': config.CLIENT_DOCUMENT_NUMBER,
            'CLIENT_DOCUMENT_TYPE': config.CLIENT_DOCUMENT_TYPE,
            'CLIENT_FIRST_NAME': config.CLIENT_FIRST_NAME,
            'CLIENT_SECOND_NAME': config.CLIENT_SECOND_NAME,
            'CLIENT_FIRST_LASTNAME': config.CLIENT_FIRST_LASTNAME,
            'CLIENT_SECOND_LASTNAME': config.CLIENT_SECOND_LASTNAME,
            'CLIENT_BIRTH_DATE': config.CLIENT_BIRTH_DATE,
            'CLIENT_GENDER': config.CLIENT_GENDER,
            'CLIENT_PHONE': config.CLIENT_PHONE,
            'CLIENT_EMAIL': config.CLIENT_EMAIL,
            'CLIENT_EMAIL_TYPE': config.CLIENT_EMAIL_TYPE,
            'CLIENT_OCCUPATION': config.CLIENT_OCCUPATION,
            'CLIENT_ADDRESS': config.CLIENT_ADDRESS,
            'CLIENT_PHONE_WORK': config.CLIENT_PHONE_WORK,
            'CLIENT_CITY': config.CLIENT_CITY,
            'POLIZA_NUMBER': config.POLIZA_NUMBER,
            'VEHICLE_CATEGORY': config.VEHICLE_CATEGORY,
            'VEHICLE_STATE': config.VEHICLE_STATE,
            'VEHICLE_MODEL_YEAR': config.VEHICLE_MODEL_YEAR,
            'VEHICLE_BRAND': config.VEHICLE_BRAND,
            'VEHICLE_REFERENCE': config.VEHICLE_REFERENCE,
            'VEHICLE_FULL_REFERENCE': config.VEHICLE_FULL_REFERENCE,
        }
        
        return sura_data
    
    def get_latest_sura_pdf(self) -> Optional[Path]:
        """Obtiene el PDF más reciente de Sura."""
        sura_downloads = self.downloads_path / "sura"
        
        if not sura_downloads.exists():
            self.logger.warning("Directorio de descargas de Sura no encontrado")
            return None
            
        # Buscar archivos PDF de Sura
        pdf_files = list(sura_downloads.glob("Cotizacion_Sura_*.pdf"))
        
        if not pdf_files:
            self.logger.warning("No se encontraron PDFs de Sura")
            return None
            
        # Ordenar por fecha de modificación (más reciente primero)
        pdf_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        self.logger.info(f"PDF más reciente de Sura: {pdf_files[0].name}")
        return pdf_files[0]
    
    def get_latest_allianz_pdf(self) -> Optional[Path]:
        """Obtiene el PDF más reciente de Allianz."""
        allianz_downloads = self.downloads_path / "allianz"
        
        if not allianz_downloads.exists():
            self.logger.warning("Directorio de descargas de Allianz no encontrado")
            return None
            
        # Buscar archivos PDF de Allianz
        pdf_files = list(allianz_downloads.glob("Cotizacion_Allianz_*.pdf"))
        
        if not pdf_files:
            self.logger.warning("No se encontraron PDFs de Allianz")
            return None
            
        # Ordenar por fecha de modificación (más reciente primero)
        pdf_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        self.logger.info(f"PDF más reciente de Allianz: {pdf_files[0].name}")
        return pdf_files[0]
    
    def extract_text_from_pdf(self, pdf_path: Path) -> str:
        """Extrae texto de un archivo PDF."""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text()
                return text
        except Exception as e:
            self.logger.error(f"Error extrayendo texto del PDF {pdf_path}: {e}")
            return ""
    
    def extract_sura_plans_from_logs(self) -> Dict[str, str]:
        """Extrae los valores de los planes de Sura desde los logs de la automatización."""
        self.logger.info("📊 Extrayendo valores de planes de Sura desde logs...")
        
        plans = {
            'Plan Autos Global': 'No encontrado',
            'Plan Autos Clasico': 'No encontrado'
        }
        
        try:
            # Buscar en el log más reciente de Sura
            sura_log_path = self.base_path / "LOGS" / "sura" / "sura.log"
            
            if not sura_log_path.exists():
                self.logger.warning("No se encontró el archivo de log de Sura")
                return plans
            
            # Leer las últimas líneas del log (más eficiente para logs grandes)
            with open(sura_log_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Buscar desde las últimas líneas hacia atrás (últimas 500 líneas)
            recent_lines = lines[-500:] if len(lines) > 500 else lines
            
            # Patrones para buscar los valores en los logs
            patterns = {
                'Plan Autos Global': [
                    r'Prima Plan Global:\s*\$([0-9,]+)',
                    r'prima_global[\'\"]\s*:\s*([0-9,]+)',
                    r'Global:\s*\$?\s*([0-9,]+)'
                ],
                'Plan Autos Clasico': [
                    r'Prima Plan Autos Clásico:\s*\$([0-9,]+)',
                    r'prima_clasico[\'\"]\s*:\s*([0-9,]+)',
                    r'Clásico:\s*\$?\s*([0-9,]+)'
                ]
            }
            
            for plan_name, plan_patterns in patterns.items():
                for line in reversed(recent_lines):
                    for pattern in plan_patterns:
                        match = re.search(pattern, line, re.IGNORECASE)
                        if match:
                            value = match.group(1).replace(',', '')
                            if value.isdigit():
                                plans[plan_name] = f"{int(value):,}"
                                self.logger.info(f"✅ Encontrado {plan_name}: ${plans[plan_name]}")
                                break
                    if plans[plan_name] != 'No encontrado':
                        break
            
            return plans
            
        except Exception as e:
            self.logger.error(f"Error extrayendo valores de Sura desde logs: {e}")
            return plans

    def extract_sura_plans_from_pdf(self, pdf_path: Path) -> Dict[str, str]:
        """Extrae los valores de los planes de Sura del PDF (método de respaldo)."""
        self.logger.info("📄 Extrayendo valores de Sura desde PDF (método de respaldo)...")
        text = self.extract_text_from_pdf(pdf_path)
        
        plans = {
            'Plan Autos Global': 'No encontrado',
            'Plan Autos Clasico': 'No encontrado'
        }
        
        # Patrones para buscar los valores de los planes
        patterns = {
            'Plan Autos Global': [
                r'Plan\s+Autos\s+Global[:\s]*\$?\s*([0-9.,]+)',
                r'Global[:\s]*\$?\s*([0-9.,]+)',
                r'GLOBAL[:\s]*\$?\s*([0-9.,]+)'
            ],
            'Plan Autos Clasico': [
                r'Plan\s+Autos\s+Cl[aá]sico[:\s]*\$?\s*([0-9.,]+)',
                r'Cl[aá]sico[:\s]*\$?\s*([0-9.,]+)',
                r'CLASICO[:\s]*\$?\s*([0-9.,]+)'
            ]
        }
        
        for plan_name, plan_patterns in patterns.items():
            for pattern in plan_patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    value = match.group(1).replace(',', '').replace('.', '')
                    if value.isdigit() and len(value) >= 3:
                        plans[plan_name] = f"{int(value):,}"
                        break
            if plans[plan_name] != 'No encontrado':
                break
        
        return plans
    
    def extract_allianz_plans_from_pdf(self, pdf_path: Path) -> Dict[str, str]:
        """Extrae los valores de los planes de Allianz del PDF."""
        text = self.extract_text_from_pdf(pdf_path)
        
        plans = {
            'Autos Esencial': 'No encontrado',
            'Autos Esencial + Totales': 'No encontrado', 
            'Autos Plus': 'No encontrado',
            'Autos Llave en Mano': 'No encontrado'
        }
        
        self.logger.info("🔍 Buscando tabla de valores de Allianz en PDF...")
        
        # Buscar la tabla con los valores anuales - patrón mejorado
        anual_patterns = [
            r'Anual\s*-?\s*Prima\s*Total\s*Vigencia\s*([\d.,]+)\s*([\d.,]+)\s*([\d.,]+)\s*([\d.,]+)',
            r'Prima\s*Total\s*Vigencia\s*Anual[:\s]*([\d.,]+)\s*([\d.,]+)\s*([\d.,]+)\s*([\d.,]+)',
            r'ANUAL.*?PRIMA.*?TOTAL.*?VIGENCIA[:\s]*([\d.,]+)\s*([\d.,]+)\s*([\d.,]+)\s*([\d.,]+)'
        ]
        
        # Intentar encontrar la tabla completa
        found_table = False
        for pattern in anual_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                self.logger.info("✅ Tabla de valores encontrada en PDF")
                values = [match.group(i) for i in range(1, 5)]
                plan_names = list(plans.keys())
                
                for i, value in enumerate(values):
                    if i < len(plan_names):
                        # Limpiar el valor (formato colombiano: 311.572,10)
                        clean_value = value.replace('.', '').replace(',', '.')
                        try:
                            # Convertir a número y formatear
                            numeric_value = float(clean_value)
                            plans[plan_names[i]] = f"{int(numeric_value):,}"
                            self.logger.info(f"✅ {plan_names[i]}: ${plans[plan_names[i]]}")
                        except ValueError:
                            self.logger.warning(f"⚠️ No se pudo convertir valor: {value}")
                            plans[plan_names[i]] = value
                found_table = True
                break
        
        # Si no se encuentra la tabla completa, buscar valores individuales
        if not found_table:
            self.logger.info("🔍 Tabla completa no encontrada, buscando valores individuales...")
            individual_patterns = {
                'Autos Esencial': [
                    r'Autos\s+Esencial(?!\s*\+)[^0-9]*?([0-9.,]+)',
                    r'Esencial(?!\s*\+)[^0-9]*?([0-9.,]+)',
                    r'ESENCIAL(?!\s*\+)[^0-9]*?([0-9.,]+)'
                ],
                'Autos Esencial + Totales': [
                    r'Autos\s+Esencial\s*\+\s*Totales[^0-9]*?([0-9.,]+)',
                    r'Esencial\s*\+\s*Totales[^0-9]*?([0-9.,]+)',
                    r'ESENCIAL\s*\+\s*TOTALES[^0-9]*?([0-9.,]+)'
                ],
                'Autos Plus': [
                    r'Autos\s+Plus[^0-9]*?([0-9.,]+)',
                    r'Plus[^0-9]*?([0-9.,]+)',
                    r'PLUS[^0-9]*?([0-9.,]+)'
                ],
                'Autos Llave en Mano': [
                    r'Autos\s+Llave\s+en\s+Mano[^0-9]*?([0-9.,]+)',
                    r'Llave\s+en\s+Mano[^0-9]*?([0-9.,]+)',
                    r'LLAVE\s+EN\s+MANO[^0-9]*?([0-9.,]+)'
                ]
            }
            
            for plan_name, plan_patterns in individual_patterns.items():
                for pattern in plan_patterns:
                    matches = re.finditer(pattern, text, re.IGNORECASE)
                    for match in matches:
                        value = match.group(1)
                        # Limpiar y validar valor
                        clean_value = value.replace('.', '').replace(',', '.')
                        try:
                            if '.' in clean_value:
                                numeric_value = float(clean_value)
                                plans[plan_name] = f"{int(numeric_value):,}"
                                self.logger.info(f"✅ {plan_name}: ${plans[plan_name]}")
                                break
                        except ValueError:
                            continue
                if plans[plan_name] != 'No encontrado':
                    break
        
        self.logger.info(f"Planes extraídos de Allianz: {plans}")
        return plans
    
    def create_excel_report(self, sura_data: Dict[str, Any], sura_plans: Dict[str, str], 
                          allianz_plans: Dict[str, str]) -> str:
        """Crea el reporte Excel consolidado con estructura mejorada."""
        filename = self.generate_filename()
        file_path = self.consolidados_path / filename
        
        self.logger.info(f"📊 Creando reporte Excel: {filename}")
        
        # Crear el DataFrame para Sura con estructura clara
        sura_rows = []
        
        # Sección 1: Datos del Cliente
        sura_rows.append({'Categoría': 'DATOS DEL CLIENTE', 'Campo': '', 'Valor': ''})
        client_fields = [
            ('Número de Documento', 'CLIENT_DOCUMENT_NUMBER'),
            ('Tipo de Documento', 'CLIENT_DOCUMENT_TYPE'),
            ('Primer Nombre', 'CLIENT_FIRST_NAME'),
            ('Segundo Nombre', 'CLIENT_SECOND_NAME'),
            ('Primer Apellido', 'CLIENT_FIRST_LASTNAME'),
            ('Segundo Apellido', 'CLIENT_SECOND_LASTNAME'),
            ('Fecha de Nacimiento', 'CLIENT_BIRTH_DATE'),
            ('Género', 'CLIENT_GENDER'),
            ('Ocupación', 'CLIENT_OCCUPATION'),
            ('Teléfono', 'CLIENT_PHONE'),
            ('Email', 'CLIENT_EMAIL')
        ]
        
        for display_name, config_key in client_fields:
            value = sura_data.get(config_key, 'No disponible')
            sura_rows.append({'Categoría': '', 'Campo': display_name, 'Valor': value})
        
        # Sección 2: Datos de Dirección
        sura_rows.append({'Categoría': '', 'Campo': '', 'Valor': ''})
        sura_rows.append({'Categoría': 'DATOS DE DIRECCIÓN', 'Campo': '', 'Valor': ''})
        address_fields = [
            ('Dirección', 'CLIENT_ADDRESS'),
            ('Teléfono de Trabajo', 'CLIENT_PHONE_WORK'),
            ('Ciudad', 'CLIENT_CITY')
        ]
        
        for display_name, config_key in address_fields:
            value = sura_data.get(config_key, 'No disponible')
            sura_rows.append({'Categoría': '', 'Campo': display_name, 'Valor': value})
        
        # Sección 3: Datos del Vehículo
        sura_rows.append({'Categoría': '', 'Campo': '', 'Valor': ''})
        sura_rows.append({'Categoría': 'DATOS DEL VEHÍCULO', 'Campo': '', 'Valor': ''})
        vehicle_fields = [
            ('Categoría', 'VEHICLE_CATEGORY'),
            ('Estado', 'VEHICLE_STATE'),
            ('Año del Modelo', 'VEHICLE_MODEL_YEAR'),
            ('Marca', 'VEHICLE_BRAND'),
            ('Referencia', 'VEHICLE_REFERENCE'),
            ('Referencia Completa', 'VEHICLE_FULL_REFERENCE')
        ]
        
        for display_name, config_key in vehicle_fields:
            value = sura_data.get(config_key, 'No disponible')
            sura_rows.append({'Categoría': '', 'Campo': display_name, 'Valor': value})
        
        # Sección 4: Valores de Planes Sura
        sura_rows.append({'Categoría': '', 'Campo': '', 'Valor': ''})
        sura_rows.append({'Categoría': 'COTIZACIONES SURA', 'Campo': '', 'Valor': ''})
        for plan_name, plan_value in sura_plans.items():
            formatted_value = f"${plan_value}" if plan_value != 'No encontrado' else plan_value
            sura_rows.append({'Categoría': '', 'Campo': plan_name, 'Valor': formatted_value})
        
        sura_df = pd.DataFrame(sura_rows)
        
        # Crear el DataFrame para Allianz con estructura clara
        allianz_rows = []
        allianz_rows.append({'Categoría': 'COTIZACIONES ALLIANZ', 'Plan': '', 'Valor': ''})
        
        for plan_name, plan_value in allianz_plans.items():
            formatted_value = f"${plan_value}" if plan_value != 'No encontrado' else plan_value
            allianz_rows.append({'Categoría': '', 'Plan': plan_name, 'Valor': formatted_value})
        
        allianz_df = pd.DataFrame(allianz_rows)
        
        # Escribir a Excel con múltiples hojas
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            # Hoja de Sura (más completa)
            sura_df.to_excel(writer, sheet_name='SURA_COMPLETO', index=False)
            
            # Hoja de Allianz
            allianz_df.to_excel(writer, sheet_name='ALLIANZ', index=False)
            
            # Hoja resumen solo con cotizaciones
            summary_rows = []
            summary_rows.append({'Aseguradora': 'SURA', 'Plan': '', 'Valor': ''})
            for plan_name, plan_value in sura_plans.items():
                formatted_value = f"${plan_value}" if plan_value != 'No encontrado' else plan_value
                summary_rows.append({'Aseguradora': '', 'Plan': plan_name, 'Valor': formatted_value})
            
            summary_rows.append({'Aseguradora': '', 'Plan': '', 'Valor': ''})
            summary_rows.append({'Aseguradora': 'ALLIANZ', 'Plan': '', 'Valor': ''})
            for plan_name, plan_value in allianz_plans.items():
                formatted_value = f"${plan_value}" if plan_value != 'No encontrado' else plan_value
                summary_rows.append({'Aseguradora': '', 'Plan': plan_name, 'Valor': formatted_value})
            
            summary_df = pd.DataFrame(summary_rows)
            summary_df.to_excel(writer, sheet_name='RESUMEN_COTIZACIONES', index=False)
        
        self.logger.info(f"📊 Reporte Excel creado exitosamente: {filename}")
        return str(file_path)
    
    def consolidate(self) -> bool:
        """Ejecuta el proceso de consolidación completo."""
        try:
            self.logger.info("Iniciando proceso de consolidación...")
            
            # 1. Extraer datos de configuración de Sura
            sura_data = self.extract_sura_data()
            
            # 2. Obtener PDFs más recientes
            sura_pdf = self.get_latest_sura_pdf()
            allianz_pdf = self.get_latest_allianz_pdf()
            
            # 3. Extraer planes de Sura (primero desde logs, luego PDF como respaldo)
            sura_plans = self.extract_sura_plans_from_logs()
            
            # Si no se encontraron en logs, intentar desde PDF
            if all(plan == 'No encontrado' for plan in sura_plans.values()) and sura_pdf:
                self.logger.info("📄 No se encontraron valores en logs, intentando desde PDF...")
                sura_plans = self.extract_sura_plans_from_pdf(sura_pdf)
            elif sura_pdf is None:
                self.logger.warning("No se encontró PDF de Sura para extracción")
            
            self.logger.info(f"Planes de Sura: {sura_plans}")
            
            # 4. Extraer planes de Allianz
            allianz_plans = {}
            if allianz_pdf:
                allianz_plans = self.extract_allianz_plans_from_pdf(allianz_pdf)
            else:
                self.logger.warning("No se pudo extraer información de planes de Allianz")
                allianz_plans = {
                    'Autos Esencial': 'PDF no encontrado',
                    'Autos Esencial + Totales': 'PDF no encontrado',
                    'Autos Plus': 'PDF no encontrado',
                    'Autos Llave en Mano': 'PDF no encontrado'
                }
            
            # 5. Crear reporte Excel
            excel_path = self.create_excel_report(sura_data, sura_plans, allianz_plans)
            
            self.logger.info(f"Consolidación completada exitosamente. Archivo: {excel_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error durante la consolidación: {e}")
            return False


def main():
    """Función principal para ejecutar la consolidación."""
    consolidator = CotizacionConsolidator()
    success = consolidator.consolidate()
    
    if success:
        print("✅ Consolidación completada exitosamente")
        return 0
    else:
        print("❌ Error durante la consolidación")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
