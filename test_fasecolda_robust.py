"""Script de prueba avanzado para validar el sistema de scoring de Fasecolda."""

import asyncio
import logging
from playwright.async_api import async_playwright

from src.shared.fasecolda_service import FasecoldaService
from src.config.sura_config import SuraConfig

# Configurar logging más detallado
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

async def test_fasecolda_robust_matching():
    """Prueba el sistema robusto de matching con scoring."""
    logger = logging.getLogger(__name__)
    
    async with async_playwright() as p:
        # Iniciar el navegador
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        try:
            # Crear instancia del servicio
            fasecolda_service = FasecoldaService(page, logger)
            
            # Obtener configuración de Sura
            config = SuraConfig()
            
            # Prueba 1: Con referencia completa exacta
            logger.info("🚀 === PRUEBA 1: Referencia completa exacta ===")
            
            cf_code = await fasecolda_service.get_cf_code(
                category=config.VEHICLE_CATEGORY,
                state=config.VEHICLE_STATE,
                model_year=config.VEHICLE_MODEL_YEAR,
                brand=config.VEHICLE_BRAND,
                reference=config.VEHICLE_REFERENCE,
                full_reference=config.VEHICLE_FULL_REFERENCE
            )
            
            if cf_code:
                logger.info(f"🎉 ¡Éxito! Código CF obtenido: {cf_code}")
                
                # Validar que coincide con el esperado para CHEVROLET TRACKER [2] LS TP 1200CC T
                if cf_code == "01635023":
                    logger.info("✅ El código CF coincide perfectamente con el esperado (01635023)")
                else:
                    logger.warning(f"⚠️ El código CF obtenido ({cf_code}) no coincide con el esperado (01635023)")
            else:
                logger.error("❌ No se pudo obtener el código CF")
            
            # Prueba 2: Con referencia parcialmente incorrecta (para probar robustez)
            logger.info("\n🚀 === PRUEBA 2: Referencia con pequeñas diferencias ===")
            
            # Simular una referencia ligeramente diferente
            modified_reference = "CHEVROLET TRACKER [2] LS TP 1200CC"  # Sin la 'T' final
            
            cf_code_2 = await fasecolda_service.get_cf_code(
                category=config.VEHICLE_CATEGORY,
                state=config.VEHICLE_STATE,
                model_year=config.VEHICLE_MODEL_YEAR,
                brand=config.VEHICLE_BRAND,
                reference=config.VEHICLE_REFERENCE,
                full_reference=modified_reference
            )
            
            if cf_code_2:
                logger.info(f"🎉 ¡Éxito con referencia modificada! Código CF: {cf_code_2}")
                if cf_code_2 == "01635023":
                    logger.info("✅ El sistema robusto funcionó correctamente - encontró la mejor coincidencia")
                else:
                    logger.info(f"📊 El sistema eligió otro resultado: {cf_code_2}")
            else:
                logger.error("❌ No se pudo obtener el código CF con referencia modificada")
            
            # Prueba 3: Sin referencia completa (fallback al primero)
            logger.info("\n🚀 === PRUEBA 3: Sin referencia completa (fallback) ===")
            
            cf_code_3 = await fasecolda_service.get_cf_code(
                category=config.VEHICLE_CATEGORY,
                state=config.VEHICLE_STATE,
                model_year=config.VEHICLE_MODEL_YEAR,
                brand=config.VEHICLE_BRAND,
                reference=config.VEHICLE_REFERENCE,
                full_reference=None  # Sin referencia completa
            )
            
            if cf_code_3:
                logger.info(f"🎉 ¡Fallback exitoso! Código CF: {cf_code_3}")
            else:
                logger.error("❌ No se pudo obtener el código CF sin referencia completa")
                
        except Exception as e:
            logger.error(f"❌ Error durante la prueba: {e}")
            import traceback
            traceback.print_exc()
            
        finally:
            await browser.close()

async def test_similarity_scoring():
    """Prueba unitaria del sistema de scoring."""
    logger = logging.getLogger(__name__)
    logger.info("\n🧪 === PRUEBAS UNITARIAS DE SCORING ===")
    
    # Crear instancia temporal para acceso al método
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        service = FasecoldaService(page, logger)
        
        # Casos de prueba
        test_cases = [
            {
                'reference': 'CHEVROLET TRACKER [2] LS TP 1200CC T',
                'candidate': 'CHEVROLET TRACKER [2] LS TP 1200CC T',
                'expected_score': 1.0,
                'description': 'Coincidencia exacta'
            },
            {
                'reference': 'CHEVROLET TRACKER [2] LS TP 1200CC T',
                'candidate': 'CHEVROLET TRACKER [2] LTZ TP 1200CC T',
                'expected_score': 0.8,
                'description': 'Solo diferencia en versión (LS vs LTZ)'
            },
            {
                'reference': 'CHEVROLET TRACKER [2] LS TP 1200CC T',
                'candidate': 'CHEVROLET TRACKER [2] LS TP 1200CC',
                'expected_score': 0.9,
                'description': 'Falta una letra al final'
            },
            {
                'reference': 'CHEVROLET TRACKER [2] LS TP 1200CC T',
                'candidate': 'TOYOTA COROLLA SEDAN',
                'expected_score': 0.1,
                'description': 'Completamente diferente'
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            score = service._calculate_similarity_score(
                test_case['reference'], 
                test_case['candidate']
            )
            
            logger.info(f"🔍 Prueba {i}: {test_case['description']}")
            logger.info(f"   Referencia: {test_case['reference']}")
            logger.info(f"   Candidato:  {test_case['candidate']}")
            logger.info(f"   Score obtenido: {score:.3f} (esperado: ~{test_case['expected_score']:.1f})")
            
            if abs(score - test_case['expected_score']) <= 0.2:
                logger.info("   ✅ Score dentro del rango esperado")
            else:
                logger.warning("   ⚠️ Score fuera del rango esperado")
            
            logger.info("")
        
        await browser.close()

if __name__ == "__main__":
    async def run_all_tests():
        await test_similarity_scoring()
        await test_fasecolda_robust_matching()
    
    asyncio.run(run_all_tests())
