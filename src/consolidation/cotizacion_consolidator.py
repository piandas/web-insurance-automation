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
import pandas as pd

from ..config.client_config import ClientConfig
from ..config.formulas_config import FormulasConfig
from ..core.logger_factory import LoggerFactory


class CotizacionConsolidator:
    def extract_allianz_plans_from_logs(self) -> Dict[str, str]:
        """Extrae los valores de los planes de Allianz desde los logs de la automatización."""
        self.logger.info("📊 Extrayendo valores de planes de Allianz desde logs...")
        plans = {
            'Autos Esencial': 'No encontrado',
            'Autos Plus': 'No encontrado',
            'Autos Llave en Mano': 'No encontrado',
            'Autos Esencial + Totales': 'No encontrado'
        }
        try:
            allianz_log_path = self.base_path / "LOGS" / "allianz" / "allianz.log"
            if not allianz_log_path.exists():
                self.logger.warning("No se encontró el archivo de log de Allianz")
                return plans
            with open(allianz_log_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            recent_lines = lines[-500:] if len(lines) > 500 else lines
            patterns = {
                'Autos Esencial': r'\[EXTRACCIÓN\] Autos Esencial: ([0-9.,]+)',
                'Autos Plus': r'\[EXTRACCIÓN\] Autos Plus: ([0-9.,]+)',
                'Autos Llave en Mano': r'\[EXTRACCIÓN\] Autos Llave en Mano: ([0-9.,]+)'
            }
            for plan_name, pattern in patterns.items():
                for line in reversed(recent_lines):
                    match = re.search(pattern, line)
                    if match:
                        value = match.group(1).replace('.', '').replace(',', '.')
                        try:
                            numeric_value = float(value)
                            plans[plan_name] = f"{numeric_value:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")
                        except Exception:
                            plans[plan_name] = match.group(1)
                        break
            # Autos Esencial + Totales: suma de los otros tres si todos existen
            try:
                if all(plans[k] != 'No encontrado' for k in ['Autos Esencial', 'Autos Plus', 'Autos Llave en Mano']):
                    total = sum(float(plans[k].replace('.', '').replace(',', '.')) for k in ['Autos Esencial', 'Autos Plus', 'Autos Llave en Mano'])
                    plans['Autos Esencial + Totales'] = f"{total:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")
            except Exception:
                pass
            return plans
        except Exception as e:
            self.logger.error(f"Error extrayendo valores de Allianz desde logs: {e}")
            return plans
    """Consolidador de cotizaciones de Sura y Allianz."""
    
    def __init__(self):
        self.logger = LoggerFactory.create_logger('consolidator')
        self.base_path = Path(__file__).parent.parent.parent
        self.consolidados_path = self.base_path / "Consolidados"
        self.downloads_path = self.base_path / "downloads"
        
        # Inicializar configuración de fórmulas
        self.formulas_config = FormulasConfig()
        
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
        
        sura_data = {
            'CLIENT_DOCUMENT_NUMBER': ClientConfig.CLIENT_DOCUMENT_NUMBER,
            'CLIENT_DOCUMENT_TYPE': ClientConfig.get_client_document_type('sura'),
            'CLIENT_FIRST_NAME': ClientConfig.CLIENT_FIRST_NAME,
            'CLIENT_SECOND_NAME': ClientConfig.CLIENT_SECOND_NAME,
            'CLIENT_FIRST_LASTNAME': ClientConfig.CLIENT_FIRST_LASTNAME,
            'CLIENT_SECOND_LASTNAME': ClientConfig.CLIENT_SECOND_LASTNAME,
            'CLIENT_BIRTH_DATE': ClientConfig.get_client_birth_date('sura'),
            'CLIENT_GENDER': ClientConfig.CLIENT_GENDER,
            'CLIENT_PHONE': getattr(ClientConfig, 'CLIENT_PHONE', ''),
            'CLIENT_EMAIL': getattr(ClientConfig, 'CLIENT_EMAIL', ''),
            'CLIENT_EMAIL_TYPE': getattr(ClientConfig, 'CLIENT_EMAIL_TYPE', ''),
            'CLIENT_OCCUPATION': ClientConfig.CLIENT_OCCUPATION,
            'CLIENT_ADDRESS': ClientConfig.CLIENT_ADDRESS,
            'CLIENT_PHONE_WORK': ClientConfig.CLIENT_PHONE_WORK,
            'CLIENT_CITY': ClientConfig.get_client_city('sura'),
            'POLIZA_NUMBER': ClientConfig.get_policy_number('sura'),
            'VEHICLE_CATEGORY': ClientConfig.VEHICLE_CATEGORY,
            'VEHICLE_STATE': ClientConfig.VEHICLE_STATE,
            'VEHICLE_MODEL_YEAR': ClientConfig.VEHICLE_MODEL_YEAR,
            'VEHICLE_BRAND': ClientConfig.VEHICLE_BRAND,
            'VEHICLE_REFERENCE': ClientConfig.VEHICLE_REFERENCE,
            'VEHICLE_FULL_REFERENCE': ClientConfig.VEHICLE_FULL_REFERENCE,
        }
        
        return sura_data
    
    def get_valor_asegurado(self) -> Optional[str]:
        """
        Obtiene el valor asegurado según el tipo de cliente.
        Para clientes nuevos: desde ClientConfig
        Para clientes usados: desde ClientConfig (ya extraído por Allianz)
        """
        try:
            # Obtener valor desde ClientConfig (ya sea ingresado manualmente o extraído)
            valor = ClientConfig.get_vehicle_insured_value()
            
            if valor and valor.strip():
                # Limpiar el valor (quitar caracteres no numéricos excepto comas y puntos)
                valor_limpio = ''.join(c for c in valor if c.isdigit() or c in '.,')
                return valor_limpio
            else:
                self.logger.warning("⚠️ No se encontró valor asegurado en la configuración")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Error obteniendo valor asegurado: {e}")
            return None
    
    def calculate_bolivar_solidaria_plans(self) -> Dict[str, str]:
        """Calcula las cotizaciones de Bolívar y Solidaria usando las fórmulas configuradas."""
        self.logger.info("💰 Calculando cotizaciones de Bolívar y Solidaria...")
        
        plans = {
            'Bolívar': 'No calculado',
            'Solidaria': 'No calculado'
        }
        
        # Obtener valor asegurado
        valor_asegurado = self.get_valor_asegurado()
        if not valor_asegurado:
            self.logger.warning("⚠️ No se puede calcular Bolívar y Solidaria: valor asegurado no disponible")
            return plans
        
        self.logger.info(f"💰 Calculando con valor asegurado: {valor_asegurado}")
        
        # Calcular Bolívar
        try:
            bolivar_result = self.formulas_config.calculate_cotizacion('bolivar', valor_asegurado)
            if bolivar_result is not None:
                plans['Bolívar'] = f"{bolivar_result:,.0f}".replace(",", ".")
                self.logger.info(f"✅ Bolívar calculado: ${plans['Bolívar']}")
            else:
                self.logger.warning("⚠️ Error calculando cotización de Bolívar")
        except Exception as e:
            self.logger.error(f"❌ Error calculando Bolívar: {e}")
        
        # Calcular Solidaria
        try:
            solidaria_result = self.formulas_config.calculate_cotizacion('solidaria', valor_asegurado)
            if solidaria_result is not None:
                plans['Solidaria'] = f"{solidaria_result:,.0f}".replace(",", ".")
                self.logger.info(f"✅ Solidaria calculado: ${plans['Solidaria']}")
            else:
                self.logger.warning("⚠️ Error calculando cotización de Solidaria")
        except Exception as e:
            self.logger.error(f"❌ Error calculando Solidaria: {e}")
        
        return plans
    
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
    
    def extract_sura_plans_from_logs(self) -> Dict[str, str]:
        """Extrae los valores de los planes de Sura desde los logs de la automatización, incluyendo Pérdida Parcial 10-1 SMLMV."""
        self.logger.info("📊 Extrayendo valores de planes de Sura desde logs...")
        plans = {
            'Plan Autos Global': 'No encontrado',
            'Pérdida Parcial 10-1 SMLMV': 'No encontrado',
            'Plan Autos Clasico': 'No encontrado'
        }
        try:
            sura_log_path = self.base_path / "LOGS" / "sura" / "sura.log"
            if not sura_log_path.exists():
                self.logger.warning("No se encontró el archivo de log de Sura")
                return plans
            with open(sura_log_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            recent_lines = lines[-500:] if len(lines) > 500 else lines
            # Patrones para buscar los valores en los logs
            patterns = {
                'Plan Autos Global': [
                    r'Global:\s*\$([0-9,.]+)',
                    r'Prima Plan Global:\s*\$([0-9,.]+)',
                    r'prima_global[\'\"]\s*:\s*([0-9,.]+)'
                ],
                'Pérdida Parcial 10-1 SMLMV': [
                    r'tras 10-1 SMLMV:\s*\$([0-9,.]+)',
                    r'Pérdida Parcial 10-1 SMLMV:\s*\$([0-9,.]+)',
                    r'prima_10_1[\'\"]\s*:\s*([0-9,.]+)'
                ],
                'Plan Autos Clasico': [
                    r'Clásico:\s*\$([0-9,.]+)',
                    r'Prima Plan Autos Clásico:\s*\$([0-9,.]+)',
                    r'prima_clasico[\'\"]\s*:\s*([0-9,.]+)'
                ]
            }
            for plan_name, plan_patterns in patterns.items():
                for line in reversed(recent_lines):
                    for pattern in plan_patterns:
                        match = re.search(pattern, line, re.IGNORECASE)
                        if match:
                            value = match.group(1).replace(',', '').replace('.', '')
                            if value.isdigit():
                                plans[plan_name] = f"{int(value):,}".replace(",", ".")
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
                          allianz_plans: Dict[str, str], bolivar_solidaria_plans: Dict[str, str]) -> str:
        """Crea el reporte Excel consolidado con estructura mejorada en una sola hoja."""
        filename = self.generate_filename()
        file_path = self.consolidados_path / filename
        
        self.logger.info(f"📊 Creando reporte Excel consolidado: {filename}")
        
        # Obtener valor asegurado
        valor_asegurado = self.get_valor_asegurado()
        valor_asegurado_formatted = f"${valor_asegurado}" if valor_asegurado else "No disponible"
        
        # Crear lista de filas para el Excel consolidado
        rows = []
        
        # === SECCIÓN 1: DATOS DEL CLIENTE ===
        rows.append({'Categoría': 'DATOS DEL CLIENTE', 'Campo': '', 'Valor': ''})
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
            rows.append({'Categoría': '', 'Campo': display_name, 'Valor': value})
        
        # === SECCIÓN 2: DATOS DE DIRECCIÓN ===
        rows.append({'Categoría': '', 'Campo': '', 'Valor': ''})
        rows.append({'Categoría': 'DATOS DE DIRECCIÓN', 'Campo': '', 'Valor': ''})
        address_fields = [
            ('Dirección', 'CLIENT_ADDRESS'),
            ('Teléfono de Trabajo', 'CLIENT_PHONE_WORK'),
            ('Ciudad', 'CLIENT_CITY')
        ]
        
        for display_name, config_key in address_fields:
            value = sura_data.get(config_key, 'No disponible')
            rows.append({'Categoría': '', 'Campo': display_name, 'Valor': value})
        
        # === SECCIÓN 3: DATOS DEL VEHÍCULO ===
        rows.append({'Categoría': '', 'Campo': '', 'Valor': ''})
        rows.append({'Categoría': 'DATOS DEL VEHÍCULO', 'Campo': '', 'Valor': ''})
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
            rows.append({'Categoría': '', 'Campo': display_name, 'Valor': value})
        
        # Añadir valor asegurado
        rows.append({'Categoría': '', 'Campo': 'Valor Asegurado', 'Valor': valor_asegurado_formatted})
        
        # === SECCIÓN 4: COTIZACIONES ===
        rows.append({'Categoría': '', 'Campo': '', 'Valor': ''})
        rows.append({'Categoría': 'COTIZACIONES POR ASEGURADORA', 'Campo': '', 'Valor': ''})
        
        # SURA
        rows.append({'Categoría': '', 'Campo': '', 'Valor': ''})
        rows.append({'Categoría': 'SURA', 'Campo': '', 'Valor': ''})
        
        # Exportar según tipo de vehículo
        if sura_data.get('VEHICLE_STATE', '').lower() == 'usado':
            # Usado: mostrar los 3 valores
            sura_plan_map = [
                ("Plan Autos Global", sura_plans.get("Plan Autos Global")),
                ("Pérdida Parcial 10-1 SMLMV", sura_plans.get("Pérdida Parcial 10-1 SMLMV")),
                ("Plan Autos Clásico", sura_plans.get("Plan Autos Clasico")),
            ]
        else:
            # Nuevo: solo global y clásico
            sura_plan_map = [
                ("Plan Autos Global", sura_plans.get("Plan Autos Global")),
                ("Plan Autos Clásico", sura_plans.get("Plan Autos Clasico")),
            ]
        
        for plan_name, plan_value in sura_plan_map:
            formatted_value = f"${plan_value}" if plan_value not in [None, 'No encontrado'] else (plan_value if plan_value is not None else 'No encontrado')
            rows.append({'Categoría': '', 'Campo': plan_name, 'Valor': formatted_value})
        
        # ALLIANZ
        rows.append({'Categoría': '', 'Campo': '', 'Valor': ''})
        rows.append({'Categoría': 'ALLIANZ', 'Campo': '', 'Valor': ''})
        allianz_plan_names = [
            'Autos Esencial',
            'Autos Esencial + Totales',
            'Autos Plus',
            'Autos Llave en Mano'
        ]
        
        for plan_name in allianz_plan_names:
            plan_value = allianz_plans.get(plan_name, 'No encontrado')
            formatted_value = f"${plan_value}" if plan_value != 'No encontrado' else plan_value
            rows.append({'Categoría': '', 'Campo': plan_name, 'Valor': formatted_value})
        
        # BOLÍVAR Y SOLIDARIA
        rows.append({'Categoría': '', 'Campo': '', 'Valor': ''})
        rows.append({'Categoría': 'BOLÍVAR', 'Campo': '', 'Valor': ''})
        bolivar_value = bolivar_solidaria_plans.get('Bolívar', 'No calculado')
        formatted_bolivar = f"${bolivar_value}" if bolivar_value != 'No calculado' else bolivar_value
        rows.append({'Categoría': '', 'Campo': 'Cotización Calculada', 'Valor': formatted_bolivar})
        
        rows.append({'Categoría': '', 'Campo': '', 'Valor': ''})
        rows.append({'Categoría': 'SOLIDARIA', 'Campo': '', 'Valor': ''})
        solidaria_value = bolivar_solidaria_plans.get('Solidaria', 'No calculado')
        formatted_solidaria = f"${solidaria_value}" if solidaria_value != 'No calculado' else solidaria_value
        rows.append({'Categoría': '', 'Campo': 'Cotización Calculada', 'Valor': formatted_solidaria})
        
        # Crear DataFrame
        df = pd.DataFrame(rows)
        
        # Escribir a Excel con una sola hoja
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='COTIZACION_CONSOLIDADA', index=False)
        
        self.logger.info(f"📊 Reporte Excel consolidado creado exitosamente: {filename}")
        return str(file_path)
    
    def consolidate_with_failures(self, automation_results: Dict[str, bool]) -> bool:
        """
        Ejecuta el proceso de consolidación incluso si algunas automatizaciones fallaron.
        
        Args:
            automation_results: Dict con resultados de automatizaciones {'allianz': True/False, 'sura': True/False}
        """
        try:
            self.logger.info("Iniciando proceso de consolidación con posibles fallos...")
            self.logger.info(f"Resultados de automatización: {automation_results}")
            
            # 1. Extraer datos de configuración de Sura (siempre intentar)
            sura_data = self.extract_sura_data()
            
            # 2. Obtener PDFs más recientes
            sura_pdf = self.get_latest_sura_pdf()
            allianz_pdf = self.get_latest_allianz_pdf()
            
            # 3. Extraer planes según el éxito de cada automatización
            if automation_results.get('sura', False):
                # Sura exitosa: extraer normalmente
                sura_plans = self.extract_sura_plans_from_logs()
                
                # Si no se encontraron en logs, intentar desde PDF
                if all(plan == 'No encontrado' for plan in sura_plans.values()) and sura_pdf:
                    self.logger.info("📄 No se encontraron valores en logs, intentando desde PDF...")
                    sura_plans = self.extract_sura_plans_from_pdf(sura_pdf)
            else:
                # Sura falló: llenar con "FALLÓ"
                self.logger.warning("❌ Sura falló, llenando planes con 'FALLÓ'")
                sura_plans = {
                    'A TODO RIESGO C/D 15%': 'FALLÓ',
                    'A TODO RIESGO C/D 10%': 'FALLÓ',
                    'RESPONSABILIDAD CIVIL + PT + HU': 'FALLÓ'
                }
            
            if automation_results.get('allianz', False):
                # Allianz exitosa: extraer normalmente
                allianz_plans = self.extract_allianz_plans_from_logs()
            else:
                # Allianz falló: llenar con "FALLÓ"
                self.logger.warning("❌ Allianz falló, llenando planes con 'FALLÓ'")
                allianz_plans = {
                    'Autos Esencial': 'FALLÓ',
                    'Autos Plus': 'FALLÓ',
                    'Autos Llave en Mano': 'FALLÓ',
                    'Autos Esencial + Totales': 'FALLÓ'
                }
            
            self.logger.info(f"Planes de Sura: {sura_plans}")
            self.logger.info(f"Planes de Allianz: {allianz_plans}")
            
            # 4. Calcular cotizaciones de Bolívar y Solidaria (siempre posible)
            bolivar_solidaria_plans = self.calculate_bolivar_solidaria_plans()
            
            # 5. Crear reporte Excel consolidado
            excel_path = self.create_excel_report(sura_data, sura_plans, allianz_plans, bolivar_solidaria_plans)
            
            self.logger.info(f"Consolidación con fallos completada. Archivo: {excel_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error durante la consolidación con fallos: {e}")
            return False

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
            
            # 4. Extraer planes de Allianz desde logs (no PDF)
            allianz_plans = self.extract_allianz_plans_from_logs()
            
            # 5. Calcular cotizaciones de Bolívar y Solidaria
            bolivar_solidaria_plans = self.calculate_bolivar_solidaria_plans()
            
            # 6. Crear reporte Excel consolidado
            excel_path = self.create_excel_report(sura_data, sura_plans, allianz_plans, bolivar_solidaria_plans)
            
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
