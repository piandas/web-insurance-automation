# Automatización Allianz - Estructura Organizada

## Estructura del Proyecto

```
src/
├── pages/
│   ├── __init__.py           # Configuración del paquete
│   ├── base_page.py          # Métodos genéricos de espera, click JS, evaluate, etc.
│   ├── login_page.py         # LoginPage: url, selectores y método login()
│   ├── dashboard_page.py     # DashboardPage: navegación a Flotas Autos
│   └── flotas_page.py        # FlotasPage: envío de formulario, click_cell, click_livianos, click_aceptar
├── allianz_automation.py     # Clase principal que orquesta las páginas
├── allianz_fixed.py          # Archivo original (mantener como respaldo)
└── allianz.py               # Archivo original (mantener como respaldo)
```

## Descripción de Archivos

### `pages/base_page.py`
Contiene la clase `BasePage` con métodos genéricos que pueden ser utilizados por todas las páginas:
- `wait_for_element_with_text()`: Espera elementos con texto específico
- `evaluate_iframe()`: Ejecuta scripts en contexto de iframe/main
- `click_with_js()`: Realiza clics usando JavaScript
- `wait_for_network_idle()`: Espera que la red esté inactiva
- `is_element_visible()`: Verifica visibilidad de elementos

### `pages/login_page.py`
Clase `LoginPage` que maneja todo el proceso de autenticación:
- Navegación a la URL de login
- Llenado de credenciales
- Envío del formulario
- Método `login()` que orquesta todo el proceso

### `pages/dashboard_page.py`
Clase `DashboardPage` para navegación en el panel principal:
- Clic en "Nueva Póliza"
- Expansión de la sección "Autos"
- Selección de "Flotas Autos"
- Espera de navegación a la página de aplicación

### `pages/flotas_page.py`
Clase `FlotasPage` para todas las operaciones en la página de flotas:
- Envío del formulario de aplicación
- Clic en la celda específica (23541048)
- Selección de "Livianos Particulares"
- Clic en botón "Aceptar"
- Método `complete_flotas_flow()` que orquesta todo el proceso

### `allianz_automation.py`
Clase principal `AllianzAutomation` que:
- Inicializa el navegador Playwright
- Configura todas las páginas
- Orquesta el flujo completo de automatización
- Maneja errores y cierre de recursos

## Uso

```python
from allianz_automation import AllianzAutomation

async def main():
    automation = AllianzAutomation("usuario", "contraseña", headless=False)
    await automation.launch()
    success = await automation.run_complete_automation()
    await automation.close()
```

## Ejecución

Para ejecutar la automatización:

```bash
cd src
python allianz_automation.py
```

## Ventajas de esta Estructura

1. **Separación de Responsabilidades**: Cada página maneja solo su funcionalidad específica
2. **Reutilización**: Los métodos genéricos están en `BasePage`
3. **Mantenibilidad**: Fácil de modificar y extender
4. **Legibilidad**: Código más organizado y fácil de entender
5. **Testabilidad**: Cada página puede ser probada independientemente
6. **Escalabilidad**: Fácil agregar nuevas páginas siguiendo el mismo patrón

## Patrón Page Object Model

Esta implementación sigue el patrón Page Object Model (POM), donde:
- Cada página web es representada por una clase
- Los selectores y métodos específicos están encapsulados en cada página
- La lógica de negocio está separada de los detalles de implementación
- El código es más mantenible y reutilizable
