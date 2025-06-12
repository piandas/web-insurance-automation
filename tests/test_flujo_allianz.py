import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import asyncio
from src.allianz_automation import AllianzAutomation

# --- CONFIGURACIÓN DE TEST ---
USUARIO = "CA031800"
CONTRASENA = "Agenciainfondo**"
BASE_URL = "https://www.allia2net.com.co/ngx-epac/private/home"  # Cambia por la URL real

async def test_flujo_allianz():
    # Instancia la automatización con credenciales y headless=False para depuración visual
    automation = AllianzAutomation(usuario=USUARIO, contrasena=CONTRASENA, headless=False)
    await automation.launch()

    # 1. Login
    assert await automation.execute_login_flow(), "Fallo en login"

    # 2. Navegación a dashboard y flotas
    assert await automation.dashboard_page.navigate_to_flotas(), "Fallo en navegación a flotas"
    assert await automation.dashboard_page.submit_application_form(), "Fallo al enviar formulario de aplicación"

    # 3. Flujo de flotas paso a paso
    assert await automation.flotas_page.click_cell_23541048(), "Fallo al seleccionar celda flota"
    assert await automation.flotas_page.click_livianos_particulares(), "Fallo al seleccionar 'Livianos Particulares'"
    assert await automation.flotas_page.click_aceptar(), "Fallo al hacer clic en 'Aceptar'"
    assert await automation.flotas_page.click_radio_no_asegurado(), "Fallo al seleccionar radio 'No' asegurado"
    assert await automation.flotas_page.select_tipo_documento("CEDULA_CIUDADANIA"), "Fallo al seleccionar tipo de documento"
    assert await automation.flotas_page.fill_numero_documento("1026258710"), "Fallo al llenar número de documento"
    assert await automation.flotas_page.select_categoria_riesgo_liviano(), "Fallo al seleccionar categoría de riesgo"
    assert await automation.flotas_page.click_btn_aceptar_final(), "Fallo al hacer clic en botón aceptar final"

    # 4. Interacción con placa
    assert await automation.placa_page.esperar_y_llenar_placa("IOS190"), "Fallo llenando placa"
    assert await automation.placa_page.click_comprobar_placa(), "Fallo clic en 'Comprobar'"

    print("\n✅ Flujo Allianz ejecutado correctamente hasta la sección de placa.")
    # Mantener navegador abierto para inspección manual
    await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(test_flujo_allianz())
