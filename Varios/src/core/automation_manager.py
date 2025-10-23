"""Orquestador principal para manejar múltiples automatizaciones."""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from .logger_factory import LoggerFactory
from ..shared.fasecolda_extractor import start_global_fasecolda_extraction, cleanup_global_fasecolda_extractor
from ..shared.global_pause_coordinator import wait_for_global_resume

class AutomationManager:
    """Orquestador principal que maneja múltiples automatizaciones."""
    
    def __init__(self):
        self.logger = LoggerFactory.create_logger('manager')
        self.active_automations: Dict[str, Any] = {}
    
    async def run_sequential(self, companies: List[str], **kwargs) -> Dict[str, bool]:
        """
        Ejecuta automatizaciones de forma secuencial.
        
        Args:
            companies: Lista de compañías a ejecutar
            **kwargs: Argumentos adicionales para las automatizaciones
            
        Returns:
            Diccionario con resultados por compañía
        """
        # Filtrar compañías según el fondo seleccionado
        filtered_companies = self._filter_companies_by_fondo(companies)
        
        self.logger.info(f"🔄 Ejecutando automatizaciones secuenciales: {filtered_companies}")
        if len(filtered_companies) != len(companies):
            self.logger.info(f"🔍 Compañías filtradas por fondo: {companies} → {filtered_companies}")
        
        # Detectar si se debe ejecutar en modo headless
        headless_mode = kwargs.get('headless', False)
        
        # Iniciar extracción de códigos FASECOLDA en paralelo
        fasecolda_task = await start_global_fasecolda_extraction(headless=headless_mode)
        
        results = {}
        
        # Esperar que termine la extracción de Fasecolda antes de proceder
        try:
            from ..shared.fasecolda_service import FasecoldaReferenceNotFoundError
            self.logger.info("🔍 Esperando resultado de extracción Fasecolda...")
            await fasecolda_task  # Esto puede lanzar FasecoldaReferenceNotFoundError
            self.logger.info("✅ Extracción Fasecolda completada - Iniciando cotizaciones")
        except FasecoldaReferenceNotFoundError as e:
            # Si falla Fasecolda, marcar todas las compañías como fallidas y salir
            self.logger.error(f"🚫 PROCESO COMPLETAMENTE DETENIDO - Error en Fasecolda: {e}")
            self.logger.info("🚫 Los navegadores de Allianz y Sura NO se abrirán")
            self.logger.info("📝 Verifique y actualice la referencia del vehículo en la edición del cliente")
            return {company: False for company in filtered_companies}
        
        try:
            for company in filtered_companies:
                self.logger.info(f"📋 Procesando {company.upper()}...")
                try:
                    # Importar dinámicamente la factory
                    from ..factory.automation_factory import AutomationFactory
                    from ..shared.fasecolda_service import FasecoldaReferenceNotFoundError
                    
                    automation = AutomationFactory.create(company, **kwargs)
                    await automation.launch()
                    
                    self.active_automations[company] = automation
                    result = await automation.run_complete_flow()
                    results[company] = result
                    
                    await automation.close()
                    del self.active_automations[company]
                    
                    if result:
                        self.logger.info(f"✅ {company.upper()} completado exitosamente")
                    else:
                        self.logger.error(f"❌ {company.upper()} falló")
                        
                except FasecoldaReferenceNotFoundError as e:
                    # Referencia Fasecolda no encontrada - detener todo el proceso
                    self.logger.error(f"🚫 PROCESO DETENIDO EN {company.upper()}: {e}")
                    self.logger.info(f"🚫 Cancelando apertura de navegadores restantes: {[c.upper() for c in filtered_companies if c not in results]}")
                    # Marcar todos los restantes como fallidos
                    for remaining_company in filtered_companies:
                        if remaining_company not in results:
                            results[remaining_company] = False
                            self.logger.info(f"❌ {remaining_company.upper()}: No iniciado debido a error Fasecolda")
                    # Detener el bucle
                    break
                        
                except Exception as e:
                    self.logger.error(f"❌ Error en {company.upper()}: {e}")
                    results[company] = False
        
        finally:
            # Limpiar extractor global
            await cleanup_global_fasecolda_extractor()
        
        return results
    
    async def run_parallel(self, companies: List[str], **kwargs) -> Dict[str, bool]:
        """
        Ejecuta automatizaciones en paralelo.
        
        Args:
            companies: Lista de compañías a ejecutar
            **kwargs: Argumentos adicionales para las automatizaciones
            
        Returns:
            Diccionario con resultados por compañía
        """
        # Filtrar compañías según el fondo seleccionado
        filtered_companies = self._filter_companies_by_fondo(companies)
        
        self.logger.info(f"⚡ Ejecutando automatizaciones en paralelo: {filtered_companies}")
        if len(filtered_companies) != len(companies):
            self.logger.info(f"🔍 Compañías filtradas por fondo: {companies} → {filtered_companies}")
        
        # Detectar si se debe ejecutar en modo headless
        headless_mode = kwargs.get('headless', False)
        
        # Iniciar extracción de códigos FASECOLDA en paralelo
        fasecolda_task = await start_global_fasecolda_extraction(headless=headless_mode)
        
        # Esperar que termine la extracción de Fasecolda antes de proceder
        try:
            from ..shared.fasecolda_service import FasecoldaReferenceNotFoundError
            self.logger.info("🔍 Esperando resultado de extracción Fasecolda...")
            await fasecolda_task  # Esto puede lanzar FasecoldaReferenceNotFoundError
            self.logger.info("✅ Extracción Fasecolda completada - Iniciando cotizaciones paralelas")
        except FasecoldaReferenceNotFoundError as e:
            # Si falla Fasecolda, marcar todas las compañías como fallidas y salir
            self.logger.error(f"🚫 PROCESO COMPLETAMENTE DETENIDO - Error en Fasecolda: {e}")
            self.logger.info("🚫 Los navegadores de Allianz y Sura NO se abrirán")
            self.logger.info("📝 Verifique y actualice la referencia del vehículo en la edición del cliente")
            return {company: False for company in filtered_companies}
        
        # Crear tasks
        tasks = []
        automations = {}
        
        try:
            # Importar dinámicamente la factory
            from ..factory.automation_factory import AutomationFactory
            
            for company in filtered_companies:
                automation = AutomationFactory.create(company, **kwargs)
                automations[company] = automation
                task = self._run_single_automation(company, automation)
                tasks.append(task)
            
            # Ejecutar en paralelo
            results_list = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Procesar resultados
            results = {}
            fasecolda_error_found = False
            
            for i, company in enumerate(filtered_companies):
                result = results_list[i]
                if isinstance(result, Exception):
                    # Verificar si es una excepción específica de Fasecolda
                    from ..shared.fasecolda_service import FasecoldaReferenceNotFoundError
                    if isinstance(result, FasecoldaReferenceNotFoundError):
                        self.logger.error(f"🚫 PROCESO DETENIDO - Referencia Fasecolda no encontrada: {result}")
                        fasecolda_error_found = True
                        # Marcar todas las compañías como fallidas cuando hay error de Fasecolda
                        for company_name in filtered_companies:
                            results[company_name] = False
                        break
                    else:
                        self.logger.error(f"❌ Excepción en {company.upper()}: {result}")
                        results[company] = False
                else:
                    results[company] = result
                    if result:
                        self.logger.info(f"✅ {company.upper()} completado exitosamente")
                    else:
                        self.logger.error(f"❌ {company.upper()} falló")
            
            return results
            
        except Exception as e:
            self.logger.error(f"❌ Error en ejecución paralela: {e}")
            return {company: False for company in filtered_companies}
        finally:
            # Limpiar recursos
            for company, automation in automations.items():
                try:
                    await automation.close()
                except Exception as e:
                    self.logger.error(f"❌ Error cerrando {company}: {e}")
            
            # Limpiar extractor global
            await cleanup_global_fasecolda_extractor()
    
    async def _run_single_automation(self, company: str, automation) -> bool:
        """Ejecuta una sola automatización con manejo de pausas globales."""
        try:
            from ..shared.fasecolda_service import FasecoldaReferenceNotFoundError
            
            await automation.launch()
            self.active_automations[company] = automation
            
            # Crear wrapper para el flujo que incluya pausas globales
            result = await self._run_automation_with_pause_support(company, automation)
            
            await automation.close()
            if company in self.active_automations:
                del self.active_automations[company]
            return result
            
        except FasecoldaReferenceNotFoundError as e:
            # Referencia Fasecolda no encontrada - propagar la excepción para detener todo
            self.logger.error(f"🚫 FASECOLDA ERROR en {company}: {e}")
            try:
                await automation.close()
            except:
                pass
            if company in self.active_automations:
                del self.active_automations[company]
            # Re-lanzar para que se maneje en el nivel superior
            raise e
            
        except Exception as e:
            self.logger.error(f"❌ Error en automatización {company}: {e}")
            try:
                await automation.close()
            except:
                pass
            if company in self.active_automations:
                del self.active_automations[company]
            return False
    
    async def _run_automation_with_pause_support(self, company: str, automation) -> bool:
        """Ejecuta la automatización con soporte para pausas globales."""
        class PauseAwareAutomation:
            """Wrapper que agrega soporte de pausas globales a cualquier automatización."""
            
            def __init__(self, automation_instance, company_name):
                self.automation = automation_instance
                self.company = company_name
                self.logger = LoggerFactory.create_logger(f'{company_name}_pause_aware')
            
            async def run_complete_flow(self):
                """Ejecuta el flujo completo con verificaciones de pausa global."""
                try:
                    # Verificar pausa antes de iniciar
                    await wait_for_global_resume(self.company)
                    
                    # Ejecutar el flujo original
                    return await self.automation.run_complete_flow()
                    
                except Exception as e:
                    self.logger.error(f"❌ Error en flujo de {self.company}: {e}")
                    return False
        
        # Crear el wrapper y ejecutar
        pause_aware_automation = PauseAwareAutomation(automation, company)
        return await pause_aware_automation.run_complete_flow()
    
    async def stop_all(self):
        """Detiene todas las automatizaciones activas."""
        self.logger.info("🛑 Deteniendo todas las automatizaciones...")
        for company, automation in self.active_automations.items():
            try:
                await automation.close()
                self.logger.info(f"✅ {company.upper()} detenido")
            except Exception as e:
                self.logger.error(f"❌ Error deteniendo {company}: {e}")
        
        self.active_automations.clear()
        
        # Limpiar extractor global
        await cleanup_global_fasecolda_extractor()
    
    def _filter_companies_by_fondo(self, companies: List[str]) -> List[str]:
        """
        Filtra las compañías según el fondo seleccionado en la configuración.
        
        Args:
            companies: Lista original de compañías
            
        Returns:
            Lista de compañías que deben ejecutarse para el fondo seleccionado
        """
        try:
            # Obtener el fondo seleccionado
            from ..config.client_config import ClientConfig
            selected_fondo = ClientConfig.get_selected_fondo()
            
            if not selected_fondo:
                self.logger.info("📋 No hay fondo seleccionado, ejecutando todas las compañías")
                return companies
            
            # Obtener compañías permitidas para el fondo
            from ..factory.automation_factory import AutomationFactory
            allowed_companies = AutomationFactory.get_allowed_companies_for_fondo(selected_fondo)
            
            # Si el fondo tiene restricciones, usar SOLO las compañías permitidas por el fondo
            # (no las de la lista original)
            self.logger.info(f"🏛️ Fondo '{selected_fondo}' requiere solo: {allowed_companies}")
            
            if companies != allowed_companies:
                original_companies = [company for company in companies if company.lower() not in allowed_companies]
                if original_companies:
                    self.logger.info(f"🔍 Fondo '{selected_fondo}' - Ignorando compañías no permitidas: {original_companies}")
                
                added_companies = [company for company in allowed_companies if company.lower() not in [c.lower() for c in companies]]
                if added_companies:
                    self.logger.info(f"➕ Fondo '{selected_fondo}' - Agregando compañías requeridas: {added_companies}")
            
            return allowed_companies
            
        except Exception as e:
            self.logger.warning(f"⚠️ Error filtrando compañías por fondo: {e}")
            return companies
        
        self.logger.info("✅ Todas las automatizaciones detenidas")
