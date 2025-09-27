"""Automatización de cálculo automático para Solidaria."""

import asyncio
import logging
from typing import Optional, Dict, Any
from ...core.logger_factory import LoggerFactory
from ...config.client_config import ClientConfig
from ...config.formulas_config import FormulasConfig


class SolidariaAutomation:
    """Automatización de cálculo automático para Solidaria (sin navegador)."""
    
    def __init__(
        self, 
        usuario: Optional[str] = None, 
        contrasena: Optional[str] = None, 
        headless: Optional[bool] = None,
        **kwargs
    ):
        self.company = 'solidaria'
        self.logger = LoggerFactory.create_logger('solidaria')
        self.usuario = usuario
        self.contrasena = contrasena
        self.headless = headless
        
        # Inicializar configuración de fórmulas
        self.formulas_config = FormulasConfig()
        
        # Variables para control del flujo
        self._is_launched = False
        self._is_closed = False
        self.results = {}
        
    async def launch(self) -> bool:
        """Simula el lanzamiento (no requiere navegador)."""
        try:
            self.logger.info("🧮 Iniciando cálculo automático para SOLIDARIA...")
            await asyncio.sleep(0.5)  # Simular tiempo de inicialización
            self._is_launched = True
            self.logger.info("✅ Cálculo automático SOLIDARIA listo")
            return True
        except Exception as e:
            self.logger.error(f"❌ Error iniciando cálculo SOLIDARIA: {e}")
            return False
    
    async def run_complete_flow(self) -> bool:
        """Ejecuta el flujo completo de cálculo automático usando las fórmulas configuradas."""
        try:
            if not self._is_launched:
                self.logger.error("❌ Cálculo no inicializado. Llama a launch() primero.")
                return False
            
            self.logger.info("💰 Ejecutando cálculo automático para SOLIDARIA...")
            
            # Obtener datos del cliente
            client_data = ClientConfig._get_current_data()
            client_name = f"{client_data.get('client_first_name', '')} {client_data.get('client_first_lastname', '')}".strip()
            vehicle_info = f"{client_data.get('vehicle_brand', '')} {client_data.get('vehicle_reference', '')}".strip()
            departamento = client_data.get('client_department', '') or client_data.get('client_city', '')
            año_vehiculo = client_data.get('vehicle_model_year', '')
            
            self.logger.info(f"👤 Cliente: {client_name}")
            self.logger.info(f"🚗 Vehículo: {vehicle_info} ({año_vehiculo})")
            if departamento:
                self.logger.info(f"📍 Ubicación: {departamento}")
            
            # Obtener valor asegurado
            valor_asegurado = self._get_valor_asegurado()
            if not valor_asegurado:
                self.logger.error("❌ No se puede calcular Solidaria: valor asegurado no disponible")
                return False
            
            self.logger.info(f"� Calculando con valor asegurado: ${valor_asegurado}")
            
            # Calcular cotización de Solidaria usando las fórmulas configuradas
            self.logger.info("📊 Aplicando fórmulas de SOLIDARIA...")
            await asyncio.sleep(0.8)  # Simular tiempo de cálculo
            
            # Intentar usar tasa automática si tenemos la información necesaria
            solidaria_result = None
            if departamento and año_vehiculo:
                try:
                    año_vehiculo_int = int(año_vehiculo)
                    solidaria_result = self.formulas_config.calculate_cotizacion('solidaria', valor_asegurado, departamento, año_vehiculo_int)
                    
                    # Obtener la tasa que se usó para el log
                    tasa_usada = self.formulas_config.get_tasa_solidaria_automatica(departamento, año_vehiculo_int)
                    self.logger.info(f"🎯 Usando tasa automática: {tasa_usada}% para {departamento}, vehículo {año_vehiculo}")
                    
                except (ValueError, TypeError):
                    # Fallback a tasa manual si hay error en la conversión
                    solidaria_result = self.formulas_config.calculate_cotizacion('solidaria', valor_asegurado)
                    self.logger.warning("⚠️ Error procesando datos automáticos, usando tasa manual")
            else:
                # Usar tasa manual si no tenemos la información necesaria
                solidaria_result = self.formulas_config.calculate_cotizacion('solidaria', valor_asegurado)
                falta_info = []
                if not departamento:
                    falta_info.append("departamento")
                if not año_vehiculo:
                    falta_info.append("año del vehículo")
                self.logger.warning(f"⚠️ Información faltante para tasa automática ({', '.join(falta_info)}), usando tasa manual")
            
            if solidaria_result is None:
                self.logger.error("❌ Error calculando cotización de Solidaria")
                return False
            
            # Formatear resultado
            solidaria_formatted = f"{solidaria_result:,.0f}".replace(",", ".")
            self.results['solidaria_cotizacion'] = solidaria_formatted
            self.logger.info(f"✅ SOLIDARIA - Cotización calculada: ${solidaria_formatted}")
            
            # Calcular valor prorrateado
            self.logger.info("📅 Calculando valor prorrateado...")
            await asyncio.sleep(0.5)
            
            solidaria_prorrateado = self.formulas_config.calculate_valor_prorrateado('solidaria', solidaria_result)
            if solidaria_prorrateado is not None:
                solidaria_prorrateado_formatted = f"{solidaria_prorrateado:,.0f}".replace(",", ".")
                self.results['solidaria_prorrateado'] = solidaria_prorrateado_formatted
                self.logger.info(f"📅 SOLIDARIA - Valor prorrateado: ${solidaria_prorrateado_formatted}")
                
                # Log del cálculo detallado
                config_solidaria = self.formulas_config.get_formula_config('solidaria')
                fecha_vigencia = config_solidaria.get('fecha_fin_vigencia', '')
                try:
                    from datetime import datetime, date
                    if fecha_vigencia:
                        if isinstance(fecha_vigencia, str):
                            fecha_fin = datetime.strptime(fecha_vigencia, '%Y-%m-%d').date()
                        else:
                            fecha_fin = fecha_vigencia
                        
                        fecha_actual = date.today()
                        dias_restantes = (fecha_fin - fecha_actual).days
                        self.logger.info(f"� Prorrateo calculado: {dias_restantes} días restantes hasta {fecha_fin}")
                except Exception as e:
                    self.logger.warning(f"⚠️ Error calculando días restantes: {e}")
            else:
                self.logger.warning("⚠️ Error calculando valor prorrateado de Solidaria")
            
            self.logger.info("🎉 Cálculos de SOLIDARIA completados exitosamente")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error en cálculo SOLIDARIA: {e}")
            return False
    
    def _get_valor_asegurado(self) -> Optional[str]:
        """
        Obtiene el valor asegurado desde la configuración.
        
        Returns:
            Optional[str]: Valor asegurado limpio o None si no está disponible
        """
        try:
            # Usar directamente VEHICLE_INSURED_VALUE para evitar _load_gui_overrides()
            # que podría sobrescribir el valor manual ingresado
            valor = ClientConfig.VEHICLE_INSURED_VALUE
            self.logger.info(f"💰 Obteniendo valor asegurado para Solidaria: {valor}")
            
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
    
    def get_results(self) -> Dict[str, Any]:
        """
        Obtiene los resultados de los cálculos.
        
        Returns:
            Dict[str, Any]: Diccionario con los resultados calculados
        """
        return self.results.copy()
    
    async def close(self) -> None:
        """Cierra la automatización (no hay navegador que cerrar)."""
        try:
            if not self._is_closed:
                self.logger.info("🔒 Finalizando cálculo automático SOLIDARIA...")
                await asyncio.sleep(0.2)
                self._is_closed = True
                self.logger.info("✅ Cálculo SOLIDARIA finalizado")
        except Exception as e:
            self.logger.error(f"❌ Error cerrando SOLIDARIA: {e}")