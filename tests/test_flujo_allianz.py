import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import asyncio
from playwright.async_api import async_playwright

USUARIO = "CA031800"
CONTRASENA = "Agenciainfondo**"
BASE_URL = "https://www.allia2net.com.co/ngx-epac/private/home"

async def test_flujo_allianz_playwright():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        await page.goto(BASE_URL)

        # 1. Login
        await page.fill('input[name="username"]', USUARIO)
        await page.fill('input[name="password"]', CONTRASENA)
        await page.click('button[type="submit"]')
        await page.wait_for_load_state('networkidle')

        # 2. Navegación a dashboard y flotas
        await page.click('text=Dashboard')  # Ajusta el selector según corresponda
        await page.click('text=Flotas')     # Ajusta el selector según corresponda
        await page.click('button:has-text("Enviar")')  # Ajusta el selector

        # 3. Flujo de flotas paso a paso
        await page.click('td:has-text("23541048")')  # Ajusta el selector
        await page.click('text=Livianos Particulares')
        await page.click('button:has-text("Aceptar")')
        await page.click('input[type="radio"][value="no"]')
        await page.select_option('select[name="tipo_documento"]', 'CEDULA_CIUDADANIA')
        await page.fill('input[name="numero_documento"]', '1026258710')
        await page.select_option('select[name="categoria_riesgo"]', 'LIVIANO')
        await page.click('button:has-text("Aceptar")')

        # 4. Interacción con placa
        await page.fill('input[name="placa"]', 'IOS190')
        await page.click('button:has-text("Comprobar")')

        print("\n✅ Flujo Allianz ejecutado correctamente hasta la sección de placa (Playwright).")
        await asyncio.sleep(60)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_flujo_allianz_playwright())
