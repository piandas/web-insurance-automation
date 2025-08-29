"""
Configuración para las fórmulas de Bolívar y Solidaria.

Este módulo maneja la configuración persistente de las fórmulas de cálculo
para las cotizaciones de Bolívar y Solidaria.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional


class FormulasConfig:
    """Maneja la configuración de las fórmulas de Bolívar y Solidaria."""
    
    def __init__(self):
        self.config_path = Path(__file__).parent.parent.parent / "client_history" / "config_formulas.json"
        self._default_config = {
            "bolivar": {
                "compania": "EPM",
                "fecha_fin_vigencia": "2025-10-01",  # Fecha de vigencia para cálculo prorrateado
                "tasa": "3.3",
                "formula": "((VALORASEGURADO*TASA/100)+(279890)+(104910))*1.19"
            },
            "solidaria": {
                "compania": "EPM",
                "fecha_fin_vigencia": "2025-10-01",  # Fecha de vigencia para cálculo prorrateado
                "tasa": "",  # Vacío para usar tasas automáticas por departamento
                "formula": "((VALORASEGURADO*TASA/100)+(246000)+(93600)+(13200))*1.19",
                "tasas_por_departamento": {
                    "Cundinamarca": {
                        "0_1": 3.56, "2_6": 3.76, "7_10": 4.63, "11_15": 5.70, "16_30": 5.70
                    },
                    "Antioquia": {
                        "0_1": 4.63, "2_6": 4.89, "7_10": 6.02, "11_15": 7.41, "16_30": 7.41
                    },
                    "Valle": {
                        "0_1": 4.15, "2_6": 4.38, "7_10": 5.39, "11_15": 6.64, "16_30": 6.64
                    },
                    "Quindio, Caldas y Risaralda": {
                        "0_1": 3.70, "2_6": 3.91, "7_10": 4.81, "11_15": 5.92, "16_30": 5.92
                    },
                    "Tolima, Nariño, Meta, Boyacá y Cauca": {
                        "0_1": 3.18, "2_6": 3.36, "7_10": 4.14, "11_15": 5.09, "16_30": 5.09
                    },
                    "Córdoba, Cesar, Bolívar y Atlántico": {
                        "0_1": 3.39, "2_6": 3.58, "7_10": 4.41, "11_15": 5.42, "16_30": 5.42
                    },
                    "Huila, Santander y Norte de Santander": {
                        "0_1": 3.29, "2_6": 3.47, "7_10": 4.27, "11_15": 5.26, "16_30": 5.26
                    }
                }
            }
        }
        self._config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Carga la configuración desde el archivo JSON."""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                # Si no existe, crear con configuración por defecto
                self._save_config(self._default_config)
                return self._default_config.copy()
        except Exception:
            # En caso de error, usar configuración por defecto
            return self._default_config.copy()
    
    def _save_config(self, config: Dict[str, Any]) -> None:
        """Guarda la configuración en el archivo JSON."""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception:
            pass  # Falla silenciosamente si no puede guardar
    
    def get_formula_config(self, company: str) -> Dict[str, str]:
        """
        Obtiene la configuración de fórmula para una compañía.
        
        Args:
            company: 'bolivar' o 'solidaria'
            
        Returns:
            Dict con configuración de la fórmula
        """
        return self._config.get(company, self._default_config.get(company, {})).copy()
    
    def update_formula_config(self, company: str, config: Dict[str, str]) -> None:
        """
        Actualiza la configuración de fórmula para una compañía.
        
        Args:
            company: 'bolivar' o 'solidaria'
            config: Dict con nueva configuración
        """
        if company in ['bolivar', 'solidaria']:
            self._config[company] = config.copy()
            self._save_config(self._config)
    
    def get_tasa_solidaria_automatica(self, departamento: str, año_vehiculo: int) -> float:
        """
        Obtiene la tasa de Solidaria automáticamente basada en departamento y antigüedad del vehículo.
        
        Args:
            departamento: Nombre del departamento
            año_vehiculo: Año del modelo del vehículo
            
        Returns:
            Tasa correspondiente o tasa por defecto si no se encuentra
        """
        try:
            from datetime import datetime
            
            config = self.get_formula_config('solidaria')
            tasas_departamentos = config.get('tasas_por_departamento', {})
            
            # Calcular antigüedad del vehículo
            año_actual = datetime.now().year
            antiguedad = año_actual - año_vehiculo
            
            # Para vehículos futuros (año mayor al actual), considerarlos como 0 años
            if antiguedad < 0:
                antiguedad = 0
            
            # Determinar rango de antigüedad
            if antiguedad <= 1:
                rango = "0_1"
            elif 2 <= antiguedad <= 6:
                rango = "2_6"
            elif 7 <= antiguedad <= 10:
                rango = "7_10"
            elif 11 <= antiguedad <= 15:
                rango = "11_15"
            else:  # 16 años o más
                rango = "16_30"
            
            # Normalizar nombre del departamento
            departamento_normalizado = departamento.upper().strip()
            
            print(f"DEBUG Solidaria - Año vehículo: {año_vehiculo}, Año actual: {año_actual}, Antigüedad: {antiguedad}, Rango: {rango}")
            print(f"DEBUG Solidaria - Departamento original: '{departamento}', Normalizado: '{departamento_normalizado}'")
            
            # Mapeo de departamentos desde ClientConfig a grupos de Solidaria
            mapeo_departamentos = {
                'CUNDINAMARCA': 'Cundinamarca',
                'BOGOTA D.C.': 'Cundinamarca',
                'ANTIOQUIA': 'Antioquia',
                'VALLE DEL CAUCA': 'Valle',
                'VALLE': 'Valle',
                'QUINDIO': 'Quindio, Caldas y Risaralda',
                'CALDAS': 'Quindio, Caldas y Risaralda',
                'RISARALDA': 'Quindio, Caldas y Risaralda',
                'TOLIMA': 'Tolima, Nariño, Meta, Boyacá y Cauca',
                'NARIÑO': 'Tolima, Nariño, Meta, Boyacá y Cauca',
                'META': 'Tolima, Nariño, Meta, Boyacá y Cauca',
                'BOYACA': 'Tolima, Nariño, Meta, Boyacá y Cauca',
                'CAUCA': 'Tolima, Nariño, Meta, Boyacá y Cauca',
                'CORDOBA': 'Córdoba, Cesar, Bolívar y Atlántico',
                'CÓRDOBA': 'Córdoba, Cesar, Bolívar y Atlántico',
                'CESAR': 'Córdoba, Cesar, Bolívar y Atlántico',
                'BOLIVAR': 'Córdoba, Cesar, Bolívar y Atlántico',
                'BOLÍVAR': 'Córdoba, Cesar, Bolívar y Atlántico',
                'ATLANTICO': 'Córdoba, Cesar, Bolívar y Atlántico',
                'ATLÁNTICO': 'Córdoba, Cesar, Bolívar y Atlántico',
                'HUILA': 'Huila, Santander y Norte de Santander',
                'SANTANDER': 'Huila, Santander y Norte de Santander',
                'NORTE DE SANTANDER': 'Huila, Santander y Norte de Santander'
            }
            
            # Buscar en el mapeo
            if departamento_normalizado in mapeo_departamentos:
                grupo_solidaria = mapeo_departamentos[departamento_normalizado]
                print(f"DEBUG Solidaria - Departamento '{departamento_normalizado}' mapeado a grupo '{grupo_solidaria}'")
                if grupo_solidaria in tasas_departamentos:
                    tasa_valor = tasas_departamentos[grupo_solidaria].get(rango)
                    if tasa_valor is not None:
                        tasa_encontrada = float(tasa_valor)
                    else:
                        # Si no existe el rango, usar tasa por defecto
                        default_tasa = config.get('tasa', '4.89')
                        tasa_encontrada = float(default_tasa) if default_tasa else 4.89
                    print(f"DEBUG Solidaria - ✅ TASA ENCONTRADA: {tasa_encontrada} para grupo '{grupo_solidaria}' rango '{rango}'")
                    print(f"DEBUG Solidaria - Tasas disponibles para el grupo: {tasas_departamentos[grupo_solidaria]}")
                    return tasa_encontrada
                else:
                    print(f"DEBUG Solidaria - ❌ Grupo '{grupo_solidaria}' no encontrado en tasas_departamentos")
            else:
                print(f"DEBUG Solidaria - Departamento '{departamento_normalizado}' no encontrado en mapeo directo")
            
            # Búsqueda exacta en grupos de Solidaria
            print(f"DEBUG Solidaria - Intentando búsqueda exacta en grupos...")
            for grupo, tasas in tasas_departamentos.items():
                if departamento_normalizado == grupo.upper():
                    tasa_valor = tasas.get(rango)
                    if tasa_valor is not None:
                        tasa_encontrada = float(tasa_valor)
                    else:
                        default_tasa = config.get('tasa', '4.89')
                        tasa_encontrada = float(default_tasa) if default_tasa else 4.89
                    print(f"DEBUG Solidaria - ✅ TASA ENCONTRADA (búsqueda exacta): {tasa_encontrada} para grupo '{grupo}' rango '{rango}'")
                    return tasa_encontrada
            
            # Búsqueda parcial en grupos (si el departamento está mencionado en el grupo)
            print(f"DEBUG Solidaria - Intentando búsqueda parcial en grupos...")
            departamento_lower = departamento_normalizado.lower()
            for grupo, tasas in tasas_departamentos.items():
                grupo_lower = grupo.lower()
                # Verificar si el departamento está mencionado en el grupo
                if departamento_lower in grupo_lower or any(dept.strip().lower() == departamento_lower for dept in grupo.split(',')):
                    tasa_valor = tasas.get(rango)
                    if tasa_valor is not None:
                        tasa_encontrada = float(tasa_valor)
                    else:
                        default_tasa = config.get('tasa', '4.89')
                        tasa_encontrada = float(default_tasa) if default_tasa else 4.89
                    print(f"DEBUG Solidaria - ✅ TASA ENCONTRADA (búsqueda parcial): {tasa_encontrada} para grupo '{grupo}' rango '{rango}'")
                    return tasa_encontrada
            
            # Si no se encuentra, usar tasa por defecto
            default_tasa = config.get('tasa', '4.89')
            tasa_default = float(default_tasa) if default_tasa else 4.89
            print(f"DEBUG Solidaria - ❌ NO SE ENCONTRÓ TASA - Usando tasa por defecto: {tasa_default}")
            print(f"DEBUG Solidaria - Grupos disponibles: {list(tasas_departamentos.keys())}")
            return tasa_default
            
        except Exception as e:
            # En caso de error, usar tasa por defecto
            print(f"DEBUG Solidaria - ❌ ERROR en get_tasa_solidaria_automatica: {e}")
            print(f"DEBUG Solidaria - Usando tasa por defecto: 4.89")
            return 4.89
    
    def get_departamentos_disponibles(self) -> list:
        """Obtiene la lista de departamentos configurados para Solidaria."""
        try:
            config = self.get_formula_config('solidaria')
            tasas_departamentos = config.get('tasas_por_departamento', {})
            return list(tasas_departamentos.keys())
        except Exception:
            return []
    
    def update_tasa_departamento(self, departamento: str, rango_antiguedad: str, nueva_tasa: float) -> None:
        """
        Actualiza la tasa para un departamento y rango de antigüedad específico.
        
        Args:
            departamento: Nombre del departamento
            rango_antiguedad: Rango de antigüedad (0_1, 2_6, 7_10, 11_15, 16_30)
            nueva_tasa: Nueva tasa a aplicar
        """
        try:
            if 'solidaria' not in self._config:
                self._config['solidaria'] = self._default_config['solidaria'].copy()
            
            if 'tasas_por_departamento' not in self._config['solidaria']:
                self._config['solidaria']['tasas_por_departamento'] = {}
            
            if departamento not in self._config['solidaria']['tasas_por_departamento']:
                self._config['solidaria']['tasas_por_departamento'][departamento] = {}
            
            self._config['solidaria']['tasas_por_departamento'][departamento][rango_antiguedad] = nueva_tasa
            self._save_config(self._config)
            
        except Exception:
            pass  # Falla silenciosamente

    def calculate_cotizacion(self, company: str, valor_asegurado: str, departamento: str = None, año_vehiculo: int = None) -> Optional[float]:
        """
        Calcula la cotización usando la fórmula configurada desde la interfaz.
        Para Solidaria, puede usar tasa automática basada en departamento y año del vehículo.
        
        Args:
            company: 'bolivar' o 'solidaria'
            valor_asegurado: Valor asegurado como string
            departamento: Departamento del vehículo (opcional, para tasa automática de Solidaria)
            año_vehiculo: Año del modelo del vehículo (opcional, para tasa automática de Solidaria)
            
        Returns:
            Valor calculado o None si hay error
        """
        try:
            config = self.get_formula_config(company)
            
            # Para Solidaria, determinar si usar tasa automática o manual
            if company == 'solidaria':
                tasa_config = config.get('tasa', '').strip()
                print(f"DEBUG Solidaria - Tasa en config: '{tasa_config}'")
                
                # Si la tasa está vacía o es "0", usar tasa automática
                if not tasa_config or tasa_config == '0':
                    print(f"DEBUG Solidaria - MODO AUTOMÁTICO activado (tasa vacía)")
                    if departamento and año_vehiculo:
                        try:
                            año_vehiculo_int = int(año_vehiculo)
                            print(f"DEBUG Solidaria - Calculando tasa automática para {departamento}, año {año_vehiculo_int}")
                            tasa = self.get_tasa_solidaria_automatica(departamento, año_vehiculo_int)
                            print(f"DEBUG Solidaria - ✅ TASA AUTOMÁTICA CALCULADA: {tasa}")
                        except (ValueError, TypeError) as e:
                            # Fallback a tasa por defecto si hay error
                            print(f"DEBUG Solidaria - ❌ Error convertir año: {e}")
                            tasa = float(config.get('tasa', '4.89'))
                            print(f"DEBUG Solidaria - Usando tasa fallback: {tasa}")
                    else:
                        # Si no hay información para automático, usar tasa por defecto
                        print(f"DEBUG Solidaria - ❌ No hay departamento o año para automático")
                        tasa = float(config.get('tasa', '4.89'))
                        print(f"DEBUG Solidaria - Usando tasa por defecto: {tasa}")
                else:
                    # Usar tasa manual configurada
                    tasa = float(tasa_config)
                    print(f"DEBUG Solidaria - MODO MANUAL: usando tasa configurada {tasa}")
            else:
                # Para Bolívar, siempre usar tasa configurada
                tasa = float(config.get('tasa', '0'))
                print(f"DEBUG {company} - Usando tasa: {tasa}")
            
            valor = float(valor_asegurado.replace(',', '').replace('.', ''))
            formula = config.get('formula', '')
            
            # Si hay una fórmula personalizada, intentar evaluarla
            if formula and 'VALORASEGURADO' in formula.upper() and 'TASA' in formula.upper():
                # Preparar variables para la fórmula
                formula_evaluable = formula.upper()
                formula_evaluable = formula_evaluable.replace('VALORASEGURADO', str(valor))
                formula_evaluable = formula_evaluable.replace('TASA', str(tasa))
                
                # Evaluar la fórmula de forma segura
                try:
                    # Solo permitir operaciones matemáticas básicas
                    allowed_chars = set('0123456789+-*/.() ')
                    if all(c in allowed_chars for c in formula_evaluable.replace(',', '').replace('E', '').replace('e', '')):
                        result = eval(formula_evaluable)
                        return result
                except:
                    pass
            
            # Fallback: usar fórmulas predeterminadas si la personalizada falla
            if company == 'bolivar':
                # ((VALORASEGURADO*TASA/100)+(279890)+(104910))*1.19
                result = ((valor * tasa / 100) + 279890 + 104910) * 1.19
            elif company == 'solidaria':
                # ((VALORASEGURADO*TASA/100)+(246000)+(93600)+(13200))*1.19
                result = ((valor * tasa / 100) + 246000 + 93600 + 13200) * 1.19
                print(f"DEBUG Solidaria - RESULTADO FINAL: {result} (valor: {valor}, tasa: {tasa})")
            else:
                return None
                
            return result
            
        except (ValueError, TypeError):
            return None
    
    def calculate_valor_prorrateado(self, company: str, valor_cotizacion: float) -> Optional[float]:
        """
        Calcula el valor prorrateado basado en los días hasta la fecha de vigencia.
        
        Fórmula: (VALOR_COTIZACION / 365) * (DIAS_VIGENCIA - DIAS_HOY)
        
        Args:
            company: 'bolivar' o 'solidaria'
            valor_cotizacion: Valor de la cotización calculada
            
        Returns:
            Valor prorrateado o None si hay error
        """
        try:
            from datetime import datetime, date
            
            config = self.get_formula_config(company)
            fecha_vigencia_str = config.get('fecha_fin_vigencia', '')
            
            if not fecha_vigencia_str:
                return None
            
            # Parsear fecha de vigencia (formato: YYYY-MM-DD)
            try:
                fecha_vigencia = datetime.strptime(fecha_vigencia_str, '%Y-%m-%d').date()
            except ValueError:
                # Intentar formato DD/MM/YYYY
                try:
                    fecha_vigencia = datetime.strptime(fecha_vigencia_str, '%d/%m/%Y').date()
                except ValueError:
                    return None
            
            # Fecha actual
            fecha_hoy = date.today()
            
            # Calcular días de diferencia
            dias_diferencia = (fecha_vigencia - fecha_hoy).days
            
            # Si la fecha ya pasó, devolver 0
            if dias_diferencia <= 0:
                return 0.0
            
            # Calcular valor prorrateado: (VALOR_COTIZACION / 365) * DIAS_DIFERENCIA
            valor_prorrateado = (valor_cotizacion / 365) * dias_diferencia
            
            return valor_prorrateado
            
        except Exception:
            return None
    
    def get_all_configs(self) -> Dict[str, Dict[str, str]]:
        """Obtiene todas las configuraciones."""
        return self._config.copy()
