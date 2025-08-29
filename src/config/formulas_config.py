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
                "tasa": "4.89",
                "formula": "((VALORASEGURADO*TASA/100)+(246000)+(93600)+(13200))*1.19"
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
    
    def calculate_cotizacion(self, company: str, valor_asegurado: str) -> Optional[float]:
        """
        Calcula la cotización usando la fórmula configurada desde la interfaz.
        
        Args:
            company: 'bolivar' o 'solidaria'
            valor_asegurado: Valor asegurado como string
            
        Returns:
            Valor calculado o None si hay error
        """
        try:
            config = self.get_formula_config(company)
            tasa = float(config.get('tasa', '0'))
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
