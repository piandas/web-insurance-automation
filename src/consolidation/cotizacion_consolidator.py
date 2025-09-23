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
from .template_handler import TemplateHandler


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
            # Leer solo las últimas 120 líneas en lugar de 500
            recent_lines = lines[-120:] if len(lines) > 120 else lines
            
            self.logger.info(f"🔍 Analizando las últimas {len(recent_lines)} líneas del log de Allianz...")
            
            patterns = {
                'Autos Esencial': r'\[EXTRACCIÓN\] Autos Esencial: ([0-9.,]+)',
                'Autos Plus': r'\[EXTRACCIÓN\] Autos Plus: ([0-9.,]+)',
                'Autos Llave en Mano': r'\[EXTRACCIÓN\] Autos Llave en Mano: ([0-9.,]+)',
                'Autos Esencial + Totales': r'\[EXTRACCIÓN\] Autos Esencial \+ Totales: ([0-9.,]+)'
            }
            
            # Buscar cada plan en el log (desde las líneas más recientes hacia atrás)
            for plan_name, pattern in patterns.items():
                for line in reversed(recent_lines):
                    match = re.search(pattern, line)
                    if match:
                        value = match.group(1).replace('.', '').replace(',', '.')
                        try:
                            numeric_value = float(value)
                            plans[plan_name] = f"{numeric_value:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")
                            self.logger.info(f"✅ Encontrado {plan_name}: {plans[plan_name]} (línea: {match.group(1)})")
                        except Exception:
                            plans[plan_name] = match.group(1)
                            self.logger.info(f"✅ Encontrado {plan_name}: {plans[plan_name]} (valor original)")
                        break
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
        
        # Inicializar manejador de plantillas
        self.template_handler = TemplateHandler()
        
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
            'Bolívar Prorrateado': 'No calculado',
            'Solidaria': 'No calculado',
            'Solidaria Prorrateado': 'No calculado'
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
                
                # Calcular valor prorrateado de Bolívar
                bolivar_prorrateado = self.formulas_config.calculate_valor_prorrateado('bolivar', bolivar_result)
                if bolivar_prorrateado is not None:
                    plans['Bolívar Prorrateado'] = f"{bolivar_prorrateado:,.0f}".replace(",", ".")
                    self.logger.info(f"📅 Bolívar prorrateado: ${plans['Bolívar Prorrateado']}")
                    
                    # Log del cálculo detallado
                    config_bolivar = self.formulas_config.get_formula_config('bolivar')
                    fecha_vigencia = config_bolivar.get('fecha_fin_vigencia', '')
                    from datetime import datetime, date
                    try:
                        fecha_vig = datetime.strptime(fecha_vigencia, '%Y-%m-%d').date()
                        dias = (fecha_vig - date.today()).days
                        self.logger.info(f"📊 Cálculo Bolívar: ({bolivar_result:,.0f}/365)*{dias} = {bolivar_prorrateado:,.0f}")
                    except:
                        pass
                else:
                    self.logger.warning("⚠️ Error calculando Bolívar prorrateado")
            else:
                self.logger.warning("⚠️ Error calculando cotización de Bolívar")
        except Exception as e:
            self.logger.error(f"❌ Error calculando Bolívar: {e}")
        
        # Calcular Solidaria con tasa automática
        try:
            # Obtener información del cliente para tasa automática
            # Usar client_department si está disponible, sino usar client_city como fallback
            departamento = getattr(ClientConfig, 'CLIENT_DEPARTMENT', None) or getattr(ClientConfig, 'CLIENT_CITY', None)
            año_vehiculo = getattr(ClientConfig, 'VEHICLE_MODEL_YEAR', None)
            
            # Intentar usar tasa automática si tenemos la información necesaria
            if departamento and año_vehiculo:
                try:
                    año_vehiculo_int = int(año_vehiculo)
                    solidaria_result = self.formulas_config.calculate_cotizacion('solidaria', valor_asegurado, departamento, año_vehiculo_int)
                    
                    # Obtener la tasa que se usó para el log
                    tasa_usada = self.formulas_config.get_tasa_solidaria_automatica(departamento, año_vehiculo_int)
                    self.logger.info(f"🎯 Solidaria usando tasa automática: {tasa_usada}% para {departamento}, vehículo {año_vehiculo}")
                    
                except (ValueError, TypeError):
                    # Fallback a tasa manual si hay error en la conversión
                    solidaria_result = self.formulas_config.calculate_cotizacion('solidaria', valor_asegurado)
                    self.logger.warning(f"⚠️ Error procesando datos automáticos, usando tasa manual para Solidaria")
            else:
                # Usar tasa manual si no tenemos la información necesaria
                solidaria_result = self.formulas_config.calculate_cotizacion('solidaria', valor_asegurado)
                falta_info = []
                if not departamento:
                    falta_info.append("departamento")
                if not año_vehiculo:
                    falta_info.append("año del vehículo")
                self.logger.warning(f"⚠️ Información faltante para tasa automática ({', '.join(falta_info)}), usando tasa manual para Solidaria")
            
            if solidaria_result is not None:
                plans['Solidaria'] = f"{solidaria_result:,.0f}".replace(",", ".")
                self.logger.info(f"✅ Solidaria calculado: ${plans['Solidaria']}")
                
                # Calcular valor prorrateado de Solidaria
                solidaria_prorrateado = self.formulas_config.calculate_valor_prorrateado('solidaria', solidaria_result)
                if solidaria_prorrateado is not None:
                    plans['Solidaria Prorrateado'] = f"{solidaria_prorrateado:,.0f}".replace(",", ".")
                    self.logger.info(f"📅 Solidaria prorrateado: ${plans['Solidaria Prorrateado']}")
                    
                    # Log del cálculo detallado
                    config_solidaria = self.formulas_config.get_formula_config('solidaria')
                    fecha_vigencia = config_solidaria.get('fecha_fin_vigencia', '')
                    from datetime import datetime, date
                    try:
                        fecha_vig = datetime.strptime(fecha_vigencia, '%Y-%m-%d').date()
                        dias = (fecha_vig - date.today()).days
                        self.logger.info(f"📊 Cálculo Solidaria: ({solidaria_result:,.0f}/365)*{dias} = {solidaria_prorrateado:,.0f}")
                    except:
                        pass
                else:
                    self.logger.warning("⚠️ Error calculando Solidaria prorrateado")
            else:
                self.logger.warning("⚠️ Error calculando cotización de Solidaria")
        except Exception as e:
            self.logger.error(f"❌ Error calculando Solidaria: {e}")
        
        return plans
    
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


    

    
    def create_excel_report(self, sura_data: Dict[str, Any], sura_plans: Dict[str, str], 
                          allianz_plans: Dict[str, str], bolivar_solidaria_plans: Dict[str, str]) -> str:
        """Crea el reporte Excel consolidado. Si hay un fondo seleccionado, usa plantilla, sino usa el formato anterior."""
        
        # Verificar si hay un fondo seleccionado
        selected_fondo = ClientConfig.get_selected_fondo()
        
        if selected_fondo and selected_fondo in self.template_handler.get_available_fondos():
            # Usar plantilla del fondo
            self.logger.info(f"📋 Usando plantilla de {selected_fondo}")
            return self.template_handler.create_consolidado_from_template(
                selected_fondo, sura_data, sura_plans, allianz_plans, bolivar_solidaria_plans
            )
        else:
            # Usar formato anterior (consolidado estándar)
            if selected_fondo:
                self.logger.warning(f"⚠️ Fondo '{selected_fondo}' no disponible, usando formato estándar")
            else:
                self.logger.info("📊 No hay fondo seleccionado, usando formato estándar")
            
            return self._create_standard_excel_report(sura_data, sura_plans, allianz_plans, bolivar_solidaria_plans)
    
    def _create_standard_excel_report(self, sura_data: Dict[str, Any], sura_plans: Dict[str, str], 
                          allianz_plans: Dict[str, str], bolivar_solidaria_plans: Dict[str, str]) -> str:
        """Crea el reporte Excel consolidado con estructura estándar (formato anterior)."""
        filename = self.generate_filename()
        file_path = self.consolidados_path / filename
        
        self.logger.info(f"📊 Creando reporte Excel consolidado estándar: {filename}")
        
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
        
        # Bolívar - Cotización normal
        bolivar_value = bolivar_solidaria_plans.get('Bolívar', 'No calculado')
        formatted_bolivar = f"${bolivar_value}" if bolivar_value != 'No calculado' else bolivar_value
        rows.append({'Categoría': '', 'Campo': 'Cotización Calculada', 'Valor': formatted_bolivar})
        
        # Bolívar - Valor prorrateado
        bolivar_prorrateado_value = bolivar_solidaria_plans.get('Bolívar Prorrateado', 'No calculado')
        formatted_bolivar_prorrateado = f"${bolivar_prorrateado_value}" if bolivar_prorrateado_value != 'No calculado' else bolivar_prorrateado_value
        rows.append({'Categoría': '', 'Campo': 'Valor Prorrateado', 'Valor': formatted_bolivar_prorrateado})
        
        rows.append({'Categoría': '', 'Campo': '', 'Valor': ''})
        rows.append({'Categoría': 'SOLIDARIA', 'Campo': '', 'Valor': ''})
        
        # Solidaria - Cotización normal
        solidaria_value = bolivar_solidaria_plans.get('Solidaria', 'No calculado')
        formatted_solidaria = f"${solidaria_value}" if solidaria_value != 'No calculado' else solidaria_value
        rows.append({'Categoría': '', 'Campo': 'Cotización Calculada', 'Valor': formatted_solidaria})
        
        # Solidaria - Valor prorrateado
        solidaria_prorrateado_value = bolivar_solidaria_plans.get('Solidaria Prorrateado', 'No calculado')
        formatted_solidaria_prorrateado = f"${solidaria_prorrateado_value}" if solidaria_prorrateado_value != 'No calculado' else solidaria_prorrateado_value
        rows.append({'Categoría': '', 'Campo': 'Valor Prorrateado', 'Valor': formatted_solidaria_prorrateado})
        
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
            
            # 2. Extraer planes según el éxito de cada automatización
            if automation_results.get('sura', False):
                # Sura exitosa: extraer desde logs
                sura_plans = self.extract_sura_plans_from_logs()
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
            
            # 2. Extraer planes de Sura desde logs únicamente
            sura_plans = self.extract_sura_plans_from_logs()
            self.logger.info(f"Planes de Sura: {sura_plans}")
            
            # 3. Extraer planes de Allianz desde logs únicamente
            allianz_plans = self.extract_allianz_plans_from_logs()
            
            # 4. Calcular cotizaciones de Bolívar y Solidaria
            bolivar_solidaria_plans = self.calculate_bolivar_solidaria_plans()
            
            # 5. Crear reporte Excel consolidado
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
