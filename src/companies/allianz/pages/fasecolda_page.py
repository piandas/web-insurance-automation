"""Página de manejo de código Fasecolda específica para Allianz"""

import asyncio
from typing import Optional, Dict
from playwright.async_api import Page
from ....shared.base_page import BasePage
from ....config.allianz_config import AllianzConfig
from ....config.client_config import ClientConfig
from ....shared.fasecolda_extractor import get_global_fasecolda_codes


class FasecoldaPage(BasePage):
    """Página de manejo de código Fasecolda para Allianz."""
    
    def __init__(self, page: Page):
        super().__init__(page, 'allianz')
        self.config = AllianzConfig()

    async def get_fasecolda_code(self) -> Optional[dict]:
        """Obtiene los códigos Fasecolda desde el extractor global o usa el código por defecto."""
        self.logger.info("🔍 Obteniendo códigos Fasecolda...")
        
        # CRÍTICO: Cargar datos de GUI antes de usar ClientConfig
        ClientConfig._load_gui_overrides()
        
        try:
            # Verificar si Fasecolda está habilitado globalmente
            if not ClientConfig.is_fasecolda_enabled():
                manual_codes = ClientConfig.get_manual_fasecolda_codes()
                self.logger.info(f"📋 Fasecolda deshabilitado - usando códigos manuales - CF: {manual_codes['cf_code']}, CH: {manual_codes['ch_code']}")
                return manual_codes
            
            # Verificar configuración específica de Allianz
            if not ClientConfig.should_use_fasecolda_for_company('allianz'):
                self.logger.info("⏭️ Búsqueda automática de Fasecolda deshabilitada para Allianz")
                return None
            
            if ClientConfig.VEHICLE_STATE != 'Nuevo':
                self.logger.info(f"⏭️ Vehículo '{ClientConfig.VEHICLE_STATE}' - no requiere código Fasecolda")
                return None
            
            # Obtener códigos del extractor global
            codes = await get_global_fasecolda_codes(timeout=30)
            
            if codes and codes.get('cf_code'):
                ch_info = f" - CH: {codes.get('ch_code')}" if codes.get('ch_code') else ""
                self.logger.info(f"✅ Códigos Fasecolda obtenidos del extractor global - CF: {codes['cf_code']}{ch_info}")
                return codes
            else:
                self.logger.warning("⚠️ No se pudieron obtener códigos Fasecolda del extractor global")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Error obteniendo códigos Fasecolda: {e}")
            return None

    async def fill_fasecolda_code(self, cf_code: str) -> bool:
        """Llena el campo del código Fasecolda en Allianz."""
        self.logger.info(f"📋 Llenando código Fasecolda en Allianz: {cf_code}")
        
        try:
            # Por ahora solo registramos que tenemos el código disponible
            self.logger.info(f"📝 Código Fasecolda disponible para usar en Allianz: {cf_code}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error llenando código Fasecolda en Allianz: {e}")
            return False

    async def use_fasecolda_codes_in_flow(self, codes: dict) -> bool:
        """Utiliza los códigos Fasecolda en el flujo específico de Allianz."""
        if not codes:
            self.logger.warning("⚠️ No hay códigos Fasecolda disponibles")
            return False
        
        cf_code = codes.get('cf_code')
        ch_code = codes.get('ch_code')
        
        if cf_code:
            self.logger.info(f"📋 Código CF disponible para Allianz: {cf_code}")
        
        if ch_code:
            self.logger.info(f"📋 Código CH disponible para Allianz: {ch_code}")
        
        # cuando se determine exactamente dónde y cómo se utilizan
        
        return True
