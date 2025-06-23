#!/usr/bin/env python3
"""Script de prueba para verificar la funcionalidad de reintentos."""

import asyncio
import sys
sys.path.append('src')

from playwright.async_api import async_playwright
from src.shared.base_page import BasePage

async def test_retry_functionality():
    """Prueba básica de la función retry_action."""
    print("🧪 Iniciando prueba de funcionalidad de reintentos...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("about:blank")
        
        # Crear instancia de BasePage
        base_page = BasePage(page, "test")
        
        # Función de prueba que falla las primeras 2 veces
        attempt_count = 0
        
        async def failing_action():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count <= 2:
                print(f"  🔄 Intento {attempt_count}: Simulando fallo...")
                return False
            print(f"  ✅ Intento {attempt_count}: ¡Éxito!")
            return True
        
        # Probar con reintentos
        result = await base_page.retry_action(
            failing_action,
            "función de prueba",
            max_attempts=5,
            delay_seconds=0.5
        )
        
        print(f"🎯 Resultado final: {'✅ ÉXITO' if result else '❌ FALLO'}")
        print(f"📊 Intentos realizados: {attempt_count}")
        
        await browser.close()
        return result

if __name__ == "__main__":
    result = asyncio.run(test_retry_functionality())
    print(f"\n🏁 Prueba completada: {'✅ EXITOSA' if result else '❌ FALLIDA'}")
