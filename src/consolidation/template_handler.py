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
import shutil
import unicodedata

from ..config.client_config import ClientConfig
from ..core.logger_factory import LoggerFactory


class TemplateHandler:
    """Manejador de plantillas Excel para diferentes fondos."""
    
    def __init__(self):
        self.logger = LoggerFactory.create_logger('template_handler')
        self.base_path = Path(__file__).parent.parent.parent
        self.templates_path = self.base_path / "Bases Consolidados"
        self.consolidados_path = self.base_path / "Consolidados"
        
        # Mapeo de fondos a archivos de plantilla (dinámico)
        self.template_files = self._discover_template_files()
        
        # Mapeo de fondos a aseguradoras que cotizan
        self.fondo_aseguradoras_map = {
            'FEPEP': ['SURA', 'ALLIANZ', 'BOLIVAR'],
            'CHEC': ['SURA', 'ALLIANZ', 'BOLIVAR'], 
            'EMVARIAS': ['SURA', 'BOLIVAR'],
            'EPM': ['SURA', 'ALLIANZ', 'BOLIVAR'],
            'CONFAMILIA': ['SURA', 'SOLIDARIA', 'BOLIVAR'],
            'FECORA': ['ALLIANZ', 'SOLIDARIA'],
            'FEMFUTURO': ['SBS', 'SOLIDARIA'],
            'FODELSA': ['SOLIDARIA'],
            'MANPOWER': ['SOLIDARIA', 'ALLIANZ', 'BOLIVAR']
        }
        
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
                    # Formato esperado: "PANTILLA FONDO N.xlsx" o "PLANTILLA FONDO U.xlsx"
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
    
    def _normalize_text(self, text: str) -> str:
        """
        Normaliza texto removiendo tildes, acentos y convirtiendo a minúsculas.
        
        Args:
            text: Texto a normalizar
            
        Returns:
            str: Texto normalizado sin tildes en minúsculas
        """
        if not text:
            return ""
        
        # Convertir a string por si acaso
        text = str(text)
        
        # Remover tildes y acentos usando unicodedata
        text_normalized = unicodedata.normalize('NFD', text)
        text_without_accents = ''.join(c for c in text_normalized if unicodedata.category(c) != 'Mn')
        
        # Convertir a minúsculas
        return text_without_accents.lower()
    
    def _write_to_cell_safe(self, worksheet, row: int, column: int, value):
        """
        Escribe un valor en una celda de forma segura, manejando celdas fusionadas.
        
        Args:
            worksheet: Hoja de Excel
            row: Número de fila
            column: Número de columna
            value: Valor a escribir
        """
        try:
            cell = worksheet.cell(row=row, column=column)
            
            # Verificar si la celda está fusionada
            if hasattr(cell, 'coordinate'):
                for merged_range in worksheet.merged_cells.ranges:
                    if cell.coordinate in merged_range:
                        # Es una celda fusionada, escribir en la celda principal (top-left)
                        top_left_cell = worksheet.cell(row=merged_range.min_row, column=merged_range.min_col)
                        top_left_cell.value = value
                        self.logger.debug(f"📝 Escribiendo en celda fusionada {merged_range}: {value}")
                        return
            
            # No es una celda fusionada, escribir normalmente
            cell.value = value
            self.logger.debug(f"📝 Escribiendo en celda {cell.coordinate}: {value}")
            
        except Exception as e:
            self.logger.warning(f"❌ Error escribiendo en celda ({row}, {column}): {e}")
            # Intentar escribir directamente como fallback
            try:
                worksheet.cell(row=row, column=column).value = value
            except:
                self.logger.error(f"❌ Fallback también falló para celda ({row}, {column})")
    
    def _find_best_plan_match(self, target_plan: str, available_plans: Dict[str, str]) -> Optional[str]:
        """
        Encuentra la mejor coincidencia para un plan objetivo en la lista de planes disponibles.
        
        Args:
            target_plan: Nombre del plan objetivo (de la plantilla)
            available_plans: Diccionario de planes disponibles {nombre: valor}
            
        Returns:
            str: Valor del plan que mejor coincide, o None si no encuentra coincidencia
        """
        if not target_plan or not available_plans:
            return None
        
        # Normalizar el plan objetivo
        target_normalized = self._normalize_text(target_plan)
        
        # Primero buscar coincidencia exacta normalizada
        for plan_name, plan_value in available_plans.items():
            if self._normalize_text(plan_name) == target_normalized:
                return plan_value
        
        # Buscar coincidencias parciales inteligentes
        # Definir mapeos específicos conocidos
        known_mappings = {
            'autos esencial + total': ['autos esencial + totales'],
            'autos llave en mano': ['autos llave en mano'],
            'autos esencial': ['autos esencial'],
            'autos plus': ['autos plus']
        }
        
        # Buscar en mapeos conocidos
        for pattern, variations in known_mappings.items():
            if target_normalized == pattern:
                for variation in variations:
                    for plan_name, plan_value in available_plans.items():
                        if self._normalize_text(plan_name) == variation:
                            return plan_value
        
        # Buscar coincidencias por palabras clave
        target_keywords = set(target_normalized.split())
        best_match = None
        best_score = 0
        
        for plan_name, plan_value in available_plans.items():
            plan_keywords = set(self._normalize_text(plan_name).split())
            
            # Calcular intersección de palabras clave
            common_keywords = target_keywords.intersection(plan_keywords)
            score = len(common_keywords)
            
            # Requiere al menos 2 palabras en común para considerarlo válido
            if score >= 2 and score > best_score:
                best_match = plan_value
                best_score = score
        
        return best_match
    
    
    def get_available_fondos(self) -> List[str]:
        """Obtiene la lista de fondos disponibles basada en las plantillas existentes."""
        available_fondos = []
        processed_fondos = set()
        
        for fondo, template_file in self.template_files.items():
            template_path = self.templates_path / template_file
            if template_path.exists():
                # Extraer el fondo base (sin N o U)
                base_fondo = fondo
                if fondo.endswith(' N') or fondo.endswith(' U'):
                    base_fondo = fondo[:-2].strip()
                
                if base_fondo not in processed_fondos:
                    available_fondos.append(base_fondo)
                    processed_fondos.add(base_fondo)
            else:
                self.logger.warning(f"Plantilla no encontrada para {fondo}: {template_path}")
        
        return available_fondos
    
    def get_fondo_aseguradoras(self, fondo: str) -> List[str]:
        """
        Obtiene las aseguradoras que cotiza un fondo específico.
        
        Args:
            fondo: Nombre del fondo
            
        Returns:
            List[str]: Lista de aseguradoras que cotiza el fondo
        """
        return self.fondo_aseguradoras_map.get(fondo, ['SURA', 'ALLIANZ', 'BOLIVAR'])  # Default para fondos no mapeados
    
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
        
        # Determinar la plantilla correcta según el estado del vehículo
        vehicle_state = ClientConfig.VEHICLE_STATE.lower()
        template_key = None
        
        if vehicle_state == 'nuevo':
            template_key = f"{fondo} N"  # EPM N para nuevos
        elif vehicle_state == 'usado':
            template_key = f"{fondo} U"  # EPM U para usados
        else:
            # Fallback: buscar plantilla sin sufijo
            template_key = fondo
        
        # Verificar que la plantilla existe
        if template_key not in self.template_files:
            # Intentar fallback
            if fondo in self.template_files:
                template_key = fondo
                self.logger.warning(f"Plantilla específica '{template_key}' no encontrada, usando '{fondo}'")
            else:
                raise ValueError(f"Plantilla no encontrada para fondo: {fondo} (estado: {vehicle_state})")
        
        template_file = self.template_files[template_key]
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
        
        Nueva estructura:
        - Datos del cliente: celdas merged de la C a la I
        - Valores cotizados: sistema de intersección basado en "VALOR A PAGAR (IVA INCLUIDO)"
        """
        try:
            self.logger.info(f"📝 Llenando datos en plantilla de {fondo}")
            
            # === PARTE 1: LLENAR DATOS DEL CLIENTE ===
            # Los datos van en las celdas merged de la C a la I (columna 3)
            self._fill_client_data(worksheet, sura_data)
            
            # === PARTE 2: LLENAR VALORES COTIZADOS ===
            # Usar sistema de intersección para valores cotizados
            self._fill_quoted_values(worksheet, fondo, sura_plans, allianz_plans, bolivar_solidaria_plans)
            
            self.logger.info(f"✅ Datos llenados en plantilla de {fondo}")
            
        except Exception as e:
            self.logger.error(f"❌ Error llenando datos en plantilla: {e}")
            raise
    
    def _fill_client_data(self, worksheet, sura_data: Dict[str, Any]):
        """Llena los datos del cliente en las celdas merged (C-I)."""
        self.logger.info("📝 Llenando datos del cliente...")
        
        # 1. Fecha De Cotización
        fecha_row = self._find_cell_with_text(worksheet, 'fecha de cotización', 'fecha cotización')
        if fecha_row:
            fecha_actual = datetime.now().strftime('%d/%m/%Y')
            self._write_to_cell_safe(worksheet, fecha_row, 3, fecha_actual)  # Columna C
            self.logger.info(f"✅ Fecha de cotización: {fecha_actual}")
        
        # 2. Nombre Funcionario o asociado (dejar vacío por ahora)
        funcionario_row = self._find_cell_with_text(worksheet, 'nombre funcionario', 'funcionario o asociado')
        if funcionario_row:
            self._write_to_cell_safe(worksheet, funcionario_row, 3, "")
            self.logger.info(f"✅ Nombre funcionario (vacío)")
        
        # 3. C.C. Funcionario o asociado (dejar vacío por ahora)
        cc_funcionario_row = self._find_cell_with_text(worksheet, 'c.c. funcionario', 'cc funcionario')
        if cc_funcionario_row:
            self._write_to_cell_safe(worksheet, cc_funcionario_row, 3, "")
            self.logger.info(f"✅ CC funcionario (vacío)")
        
        # 4. Nombre Asegurado
        nombre_row = self._find_cell_with_text(worksheet, 'nombre asegurado')
        if nombre_row:
            nombre_completo = f"{sura_data.get('CLIENT_FIRST_NAME', '')} {sura_data.get('CLIENT_SECOND_NAME', '')} {sura_data.get('CLIENT_FIRST_LASTNAME', '')} {sura_data.get('CLIENT_SECOND_LASTNAME', '')}"
            self._write_to_cell_safe(worksheet, nombre_row, 3, nombre_completo.strip())
            self.logger.info(f"✅ Nombre asegurado: {nombre_completo.strip()}")
        
        # 5. C.C. Asegurado
        cc_asegurado_row = self._find_cell_with_text(worksheet, 'c.c. asegurado', 'cc asegurado')
        if cc_asegurado_row:
            cc_asegurado = sura_data.get('CLIENT_DOCUMENT_NUMBER', '')
            self._write_to_cell_safe(worksheet, cc_asegurado_row, 3, cc_asegurado)
            self.logger.info(f"✅ CC asegurado: {cc_asegurado}")
        
        # 6. Placa
        placa_row = self._find_cell_with_text(worksheet, 'placa')
        if placa_row:
            placa = ClientConfig.VEHICLE_PLATE
            self._write_to_cell_safe(worksheet, placa_row, 3, placa)
            self.logger.info(f"✅ Placa: {placa}")
        
        # 7. Modelo
        modelo_row = self._find_cell_with_text(worksheet, 'modelo')
        if modelo_row:
            modelo = ClientConfig.VEHICLE_MODEL_YEAR
            self._write_to_cell_safe(worksheet, modelo_row, 3, modelo)
            self.logger.info(f"✅ Modelo: {modelo}")
        
        # 8. Marca Y Tipo
        marca_row = self._find_cell_with_text(worksheet, 'marca y tipo', 'marca tipo')
        if marca_row:
            marca_tipo = f"{ClientConfig.VEHICLE_BRAND} - {ClientConfig.VEHICLE_REFERENCE}"
            self._write_to_cell_safe(worksheet, marca_row, 3, marca_tipo)
            self.logger.info(f"✅ Marca y tipo: {marca_tipo}")
        
        # 9. Clase (referencia escogida en fasecolda)
        clase_row = self._find_cell_with_text(worksheet, 'clase')
        if clase_row:
            clase = ClientConfig.VEHICLE_REFERENCE
            self._write_to_cell_safe(worksheet, clase_row, 3, clase)
            self.logger.info(f"✅ Clase: {clase}")
        
        # 10. Código Fasecolda (ambos códigos CF y CH)
        codigo_row = self._find_cell_with_text(worksheet, 'codigo fasecolda', 'fasecolda')
        if codigo_row:
            cf_code = ClientConfig.MANUAL_CF_CODE
            ch_code = ClientConfig.MANUAL_CH_CODE
            codigo_completo = f"CF: {cf_code} / CH: {ch_code}"
            self._write_to_cell_safe(worksheet, codigo_row, 3, codigo_completo)
            self.logger.info(f"✅ Código Fasecolda: {codigo_completo}")
        
        # 11. Ciudad de circulación
        ciudad_row = self._find_cell_with_text(worksheet, 'ciudad de circulación', 'ciudad circulación')
        if ciudad_row:
            ciudad = ClientConfig.CLIENT_CITY
            self._write_to_cell_safe(worksheet, ciudad_row, 3, ciudad)
            self.logger.info(f"✅ Ciudad de circulación: {ciudad}")
        
        # 12. Valor asegurado
        valor_row = self._find_cell_with_text(worksheet, 'valor asegurado')
        if valor_row:
            valor_asegurado = self._get_valor_asegurado()
            if valor_asegurado:
                valor_formateado = self._format_currency(valor_asegurado)
                self._write_to_cell_safe(worksheet, valor_row, 3, valor_formateado)
                self.logger.info(f"✅ Valor asegurado: {valor_formateado}")
        
        # 13. Valor accesorios (dejar vacío por ahora)
        accesorios_row = self._find_cell_with_text(worksheet, 'valor accesorios', 'accesorios')
        if accesorios_row:
            self._write_to_cell_safe(worksheet, accesorios_row, 3, "")
            self.logger.info(f"✅ Valor accesorios (vacío)")
        
        # 14. Valor asegurado total
        valor_total_row = self._find_cell_with_text(worksheet, 'valor asegurado total', 'total asegurado')
        if valor_total_row:
            valor_asegurado = self._get_valor_asegurado()
            if valor_asegurado:
                valor_formateado = self._format_currency(valor_asegurado)
                self._write_to_cell_safe(worksheet, valor_total_row, 3, valor_formateado)
                self.logger.info(f"✅ Valor asegurado total: {valor_formateado}")
    
    def _fill_quoted_values(self, worksheet, fondo: str, sura_plans: Dict[str, str], 
                          allianz_plans: Dict[str, str], bolivar_solidaria_plans: Dict[str, str]):
        """
        Llena los valores cotizados usando el sistema de intersección.
        
        Busca la fila "VALOR A PAGAR (IVA INCLUIDO)" y las columnas de las aseguradoras
        para crear intersecciones donde colocar los valores.
        Solo llena aseguradoras que el fondo tiene permitidas.
        """
        self.logger.info(f"💰 Llenando valores cotizados para fondo {fondo} usando sistema de intersección...")
        
        # Obtener aseguradoras permitidas para el fondo
        aseguradoras_permitidas = self.get_fondo_aseguradoras(fondo)
        self.logger.info(f"🔒 Aseguradoras permitidas para {fondo}: {aseguradoras_permitidas}")
        
        # 1. Buscar la fila "VALOR A PAGAR (IVA INCLUIDO)"
        valor_pagar_row = self._find_cell_with_text_in_any_column(worksheet, 'valor a pagar', 'iva incluido')
        if not valor_pagar_row:
            self.logger.warning("❌ No se encontró la fila 'VALOR A PAGAR (IVA INCLUIDO)'")
            return
        
        self.logger.info(f"✅ Fila 'VALOR A PAGAR' encontrada: {valor_pagar_row}")
        
        # 2. Determinar mapeo de planes según el estado del vehículo
        vehicle_state = ClientConfig.VEHICLE_STATE.lower()
        if vehicle_state == 'nuevo':
            # Para nuevos: Sura (Autos Global, Autos Clasico), Allianz (4 planes)
            plan_mapping = {
                'sura': ['Autos Global', 'Autos Clasico'],
                'allianz': ['Autos Esencial', 'Autos Esencial + Total', 'Autos Plus', 'Autos llave en mano']
            }
            sura_plan_map = {
                'Autos Global': sura_plans.get('Plan Autos Global', 'No encontrado'),
                'Autos Clasico': sura_plans.get('Plan Autos Clasico', 'No encontrado')
            }
        else:
            # Para usados: Sura (Autos Global, Autos Parcial, Autos Clasico), Allianz (3 planes)
            plan_mapping = {
                'sura': ['Autos Global', 'Autos Parcial', 'Autos Clasico'],
                'allianz': ['Autos Esencial', 'Autos Esencial + Total', 'Autos Plus']
            }
            sura_plan_map = {
                'Autos Global': sura_plans.get('Plan Autos Global', 'No encontrado'),
                'Autos Parcial': sura_plans.get('Pérdida Parcial 10-1 SMLMV', 'No encontrado'),
                'Autos Clasico': sura_plans.get('Plan Autos Clasico', 'No encontrado')
            }
        
        # 3. Buscar columnas de SURA y llenar valores (si está permitida)
        if 'SURA' in aseguradoras_permitidas:
            self._fill_sura_values(worksheet, valor_pagar_row, sura_plan_map, plan_mapping['sura'])
        else:
            self.logger.info(f"⚠️ SURA omitida para fondo {fondo} (no permitida)")
        
        # 4. Buscar columnas de ALLIANZ y llenar valores (si está permitida)
        if 'ALLIANZ' in aseguradoras_permitidas:
            self._fill_allianz_values(worksheet, valor_pagar_row, allianz_plans, plan_mapping['allianz'])
        else:
            self.logger.info(f"⚠️ ALLIANZ omitida para fondo {fondo} (no permitida)")
        
        # 5. Llenar Bolívar y Solidaria si están permitidas
        self._fill_other_values(worksheet, valor_pagar_row, bolivar_solidaria_plans, aseguradoras_permitidas, fondo)
        
        # 6. Calcular y llenar valores anualizados (PRIMA ANUAL IVA INCLUIDO)
        self._fill_annualized_values(worksheet, valor_pagar_row)
    
    def _fill_sura_values(self, worksheet, valor_pagar_row: int, sura_plan_map: Dict[str, str], 
                         expected_plans: List[str]):
        """Llena los valores de Sura en las columnas correspondientes."""
        self.logger.info("📊 Llenando valores de SURA...")
        
        # Buscar columnas de SURA
        sura_columns = self._find_company_columns(worksheet, 'sura')
        if not sura_columns:
            self.logger.warning("❌ No se encontraron columnas de SURA")
            return
        
        self.logger.info(f"✅ Columnas de SURA encontradas: {sura_columns}")
        
        # Mapear planes a columnas
        for i, plan_name in enumerate(expected_plans):
            if i < len(sura_columns):
                column = sura_columns[i]
                plan_value = sura_plan_map.get(plan_name, 'No encontrado')
                
                # Formatear valor
                if plan_value != 'No encontrado':
                    formatted_value = self._format_currency_from_string(plan_value)
                else:
                    formatted_value = plan_value
                
                # Colocar en intersección
                self._write_to_cell_safe(worksheet, valor_pagar_row, column, formatted_value)
                self.logger.info(f"✅ SURA {plan_name}: {formatted_value} en columna {column}")
    
    def _fill_allianz_values(self, worksheet, valor_pagar_row: int, allianz_plans: Dict[str, str], 
                           expected_plans: List[str]):
        """Llena los valores de Allianz en las columnas correspondientes."""
        self.logger.info("📊 Llenando valores de ALLIANZ...")
        
        # Buscar columnas de ALLIANZ
        allianz_columns = self._find_company_columns(worksheet, 'allianz')
        if not allianz_columns:
            self.logger.warning("❌ No se encontraron columnas de ALLIANZ")
            return
        
        self.logger.info(f"✅ Columnas de ALLIANZ encontradas: {allianz_columns}")
        
        # Mapear planes a columnas usando mapeo inteligente
        for i, plan_name in enumerate(expected_plans):
            if i < len(allianz_columns):
                column = allianz_columns[i]
                
                # Usar mapeo inteligente para encontrar la mejor coincidencia
                plan_value = self._find_best_plan_match(plan_name, allianz_plans)
                
                if plan_value is None:
                    # Fallback al método anterior
                    plan_value = allianz_plans.get(plan_name, 'No encontrado')
                
                # Formatear valor
                if plan_value and plan_value != 'No encontrado':
                    formatted_value = self._format_currency_from_string(plan_value)
                    # Log de éxito con detalles del mapeo
                    matched_key = None
                    for key, val in allianz_plans.items():
                        if val == plan_value:
                            matched_key = key
                            break
                    self.logger.info(f"✅ ALLIANZ {plan_name} -> {matched_key}: {formatted_value} en columna {column}")
                else:
                    formatted_value = 'No encontrado'
                    self.logger.warning(f"⚠️ ALLIANZ {plan_name}: No encontrado en columna {column}")
                
                # Colocar en intersección
                self._write_to_cell_safe(worksheet, valor_pagar_row, column, formatted_value)
    
    def _fill_other_values(self, worksheet, valor_pagar_row: int, bolivar_solidaria_plans: Dict[str, str], 
                         aseguradoras_permitidas: List[str], fondo: str):
        """Llena valores de otras aseguradoras si están permitidas para el fondo."""
        self.logger.info(f"📊 Intentando llenar valores de otras aseguradoras para fondo {fondo}...")
        
        # Buscar columnas de BOLIVAR (solo si está permitida)
        if 'BOLIVAR' in aseguradoras_permitidas:
            bolivar_columns = self._find_company_columns(worksheet, 'bolivar')
            if bolivar_columns:
                bolivar_value = bolivar_solidaria_plans.get('Bolívar', 'No calculado')
                if bolivar_value != 'No calculado':
                    formatted_value = self._format_currency_from_string(bolivar_value)
                    self._write_to_cell_safe(worksheet, valor_pagar_row, bolivar_columns[0], formatted_value)
                    self.logger.info(f"✅ BOLIVAR: {formatted_value}")
        else:
            self.logger.info(f"⚠️ BOLIVAR omitida para fondo {fondo} (no permitida)")
        
        # Buscar columnas de SOLIDARIA (solo si está permitida)
        if 'SOLIDARIA' in aseguradoras_permitidas:
            solidaria_columns = self._find_company_columns(worksheet, 'solidaria')
            if solidaria_columns:
                solidaria_value = bolivar_solidaria_plans.get('Solidaria', 'No calculado')
                if solidaria_value != 'No calculado':
                    formatted_value = self._format_currency_from_string(solidaria_value)
                    self._write_to_cell_safe(worksheet, valor_pagar_row, solidaria_columns[0], formatted_value)
                    self.logger.info(f"✅ SOLIDARIA: {formatted_value}")
        else:
            self.logger.info(f"⚠️ SOLIDARIA omitida para fondo {fondo} (no permitida)")
        
        # Buscar columnas de SBS (solo si está permitida)
        if 'SBS' in aseguradoras_permitidas:
            sbs_columns = self._find_company_columns(worksheet, 'sbs')
            if sbs_columns:
                sbs_value = bolivar_solidaria_plans.get('SBS', 'No calculado')
                if sbs_value != 'No calculado':
                    formatted_value = self._format_currency_from_string(sbs_value)
                    self._write_to_cell_safe(worksheet, valor_pagar_row, sbs_columns[0], formatted_value)
                    self.logger.info(f"✅ SBS: {formatted_value}")
        else:
            self.logger.info(f"⚠️ SBS omitida para fondo {fondo} (no permitida)")
    
    def _fill_annualized_values(self, worksheet, valor_pagar_row: int):
        """
        Calcula y llena los valores anualizados usando la fórmula:
        (Valor a pagar) / (Días de cobertura) * 365
        """
        self.logger.info("📊 Calculando valores anualizados...")
        
        # 1. Buscar la fila "Días de Cobertura"
        dias_cobertura_row = self._find_cell_with_text_in_any_column(worksheet, 'días de cobertura', 'dias de cobertura')
        if not dias_cobertura_row:
            self.logger.warning("❌ No se encontró la fila 'Días de Cobertura'")
            return
        
        # 2. Buscar la fila "PRIMA ANUAL IVA INCLUIDO"
        prima_anual_row = self._find_cell_with_text_in_any_column(worksheet, 'prima anual', 'iva incluido')
        if not prima_anual_row:
            self.logger.warning("❌ No se encontró la fila 'PRIMA ANUAL IVA INCLUIDO'")
            return
        
        self.logger.info(f"✅ Fila 'Días de Cobertura': {dias_cobertura_row}")
        self.logger.info(f"✅ Fila 'PRIMA ANUAL IVA INCLUIDO': {prima_anual_row}")
        
        # 3. Recorrer las columnas y calcular valores anualizados
        for col in range(2, 20):  # Columnas B hasta S
            try:
                # Obtener valor a pagar de la fila correspondiente
                valor_pagar_cell = worksheet.cell(row=valor_pagar_row, column=col)
                valor_pagar = valor_pagar_cell.value
                
                # Obtener días de cobertura
                dias_cobertura_cell = worksheet.cell(row=dias_cobertura_row, column=col)
                dias_cobertura = dias_cobertura_cell.value
                
                # Solo calcular si ambos valores existen y son válidos
                if valor_pagar and dias_cobertura and str(valor_pagar).strip() != "":
                    # Limpiar valor a pagar (quitar $ y puntos)
                    valor_numerico = self._extract_numeric_value(str(valor_pagar))
                    dias_numerico = self._extract_numeric_value(str(dias_cobertura))
                    
                    if valor_numerico > 0 and dias_numerico > 0:
                        # Calcular valor anualizado: (Valor a pagar) / (Días de cobertura) * 365
                        valor_anualizado = (valor_numerico / dias_numerico) * 365
                        
                        # Formatear como moneda
                        valor_formateado = f"${valor_anualizado:,.0f}".replace(",", ".")
                        
                        # Colocar en la fila PRIMA ANUAL
                        self._write_to_cell_safe(worksheet, prima_anual_row, col, valor_formateado)
                        
                        self.logger.info(f"✅ Columna {col}: ${valor_numerico:,.0f} ÷ {dias_numerico} × 365 = {valor_formateado}")
                
            except Exception as e:
                self.logger.warning(f"⚠️ Error calculando valor anualizado en columna {col}: {e}")
                continue
    
    def _extract_numeric_value(self, value_str: str) -> float:
        """Extrae el valor numérico de una string, removiendo caracteres no numéricos."""
        try:
            if not value_str or not value_str.strip():
                return 0.0
            
            # Quitar símbolos de moneda y separadores
            clean_value = str(value_str).replace("$", "").replace(".", "").replace(",", "").strip()
            
            # Convertir a float
            if clean_value.isdigit():
                return float(clean_value)
            else:
                return 0.0
                
        except Exception:
            return 0.0
    
    def _find_cell_with_text_in_any_column(self, worksheet, *search_terms) -> Optional[int]:
        """
        Busca una celda que contenga alguno de los términos especificados en cualquier columna.
        Usa normalización de texto para ignorar tildes y acentos.
        
        Returns:
            int: Número de fila si se encuentra, None si no se encuentra
        """
        try:
            # Normalizar términos de búsqueda
            normalized_terms = [self._normalize_text(term) for term in search_terms]
            
            for row in range(1, 100):  # Buscar en las primeras 100 filas
                for col in range(1, 20):  # Buscar en las primeras 20 columnas
                    cell_value = worksheet.cell(row=row, column=col).value
                    if cell_value:
                        cell_text_normalized = self._normalize_text(str(cell_value))
                        # Verificar si TODOS los términos están en el texto de la celda
                        if all(term in cell_text_normalized for term in normalized_terms):
                            return row
            return None
        except Exception:
            return None
    
    def _find_company_columns(self, worksheet, company_name: str) -> List[int]:
        """
        Busca las columnas de una aseguradora específica.
        Usa normalización de texto para ignorar tildes y acentos.
        
        Returns:
            List[int]: Lista de números de columna donde aparece la aseguradora
        """
        columns = []
        try:
            company_name_normalized = self._normalize_text(company_name)
            
            for row in range(1, 50):  # Buscar en las primeras 50 filas
                for col in range(1, 20):  # Buscar en las primeras 20 columnas
                    cell_value = worksheet.cell(row=row, column=col).value
                    if cell_value:
                        cell_text_normalized = self._normalize_text(str(cell_value))
                        if company_name_normalized in cell_text_normalized:
                            if col not in columns:
                                columns.append(col)
            
            return sorted(columns)
        except Exception:
            return []
    
    def _format_currency_from_string(self, value: str) -> str:
        """Formatea un valor string como moneda colombiana."""
        try:
            if not value or not value.strip() or value == 'No encontrado':
                return value
            
            # Limpiar el valor (quitar caracteres no numéricos excepto puntos)
            clean_value = ''.join(c for c in value if c.isdigit() or c == '.')
            if not clean_value:
                return value
            
            # Si ya tiene puntos como separadores de miles, convertir a número
            if '.' in clean_value:
                # Asumir que el último punto es decimal si hay más de 3 dígitos después
                parts = clean_value.split('.')
                if len(parts) > 1 and len(parts[-1]) <= 2:
                    # El último punto es decimal
                    integer_part = ''.join(parts[:-1])
                    decimal_part = parts[-1]
                    clean_value = integer_part + decimal_part
                else:
                    # Todos los puntos son separadores de miles
                    clean_value = clean_value.replace('.', '')
            
            # Convertir a número y formatear
            num = int(clean_value)
            formatted = f"{num:,}".replace(",", ".")
            return f"${formatted}"
            
        except Exception:
            return value
    
    def _find_cell_with_text(self, worksheet, *search_terms) -> Optional[int]:
        """
        Busca una celda que contenga alguno de los términos especificados en la columna A.
        Usa normalización de texto para ignorar tildes y acentos.
        
        Returns:
            int: Número de fila si se encuentra, None si no se encuentra
        """
        try:
            # Normalizar términos de búsqueda
            normalized_terms = [self._normalize_text(term) for term in search_terms]
            
            for row in range(1, 50):  # Buscar en las primeras 50 filas
                cell_value = worksheet.cell(row=row, column=1).value
                if cell_value:
                    cell_text_normalized = self._normalize_text(str(cell_value))
                    for normalized_term in normalized_terms:
                        if normalized_term in cell_text_normalized:
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
