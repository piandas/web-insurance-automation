# Automatización Allianz - Estructura Modular

## 📁 Estructura del Proyecto

```
src/
├── pages/
│   ├── __init__.py              # Exports de todas las páginas
│   ├── base_page.py             # Métodos genéricos (esperas, clicks JS, evaluate, etc.)
│   ├── login_page.py            # LoginPage: URL, selectores y método login()
│   ├── dashboard_page.py        # DashboardPage: navegación a Flotas Autos
│   └── flotas_page.py           # FlotasPage: formulario, click_cell, click_livianos, click_aceptar
├── allianz_automation.py        # 🎯 CLASE PRINCIPAL - Orquesta todas las páginas
├── allianz_fixed.py             # ⚠️ Versión original (mantener como backup)
└── test_automation.py           # Script de prueba básica
```

## 🚀 Cómo Ejecutar

### Ejecutar Automatización Completa
```bash
cd src
python allianz_automation.py
```

### Ejecutar Prueba Básica
```bash
cd src
python test_automation.py
```

## 📋 Funcionalidades por Módulo

### 🏗️ BasePage (`base_page.py`)
- `wait_for_element_with_text()` - Espera elementos con texto específico
- `evaluate_iframe()` - Ejecuta JavaScript en iframe/main page
- `click_with_js()` - Clicks con JavaScript y logging
- `wait_for_load_state_with_retry()` - Esperas con reintentos
- `safe_click()`, `safe_fill()` - Métodos seguros con timeouts
- `wait_for_selector_safe()` - Espera selectores de forma segura

### 🔐 LoginPage (`login_page.py`)
- Gestiona el proceso de login completo
- Manejo de errores y timeouts
- URLs y selectores centralizados

### 🧭 DashboardPage (`dashboard_page.py`) 
- Navegación a "Nueva Póliza"
- Expansión de sección "Autos"
- Click en "Flotas Autos"
- Envío de formularios automático

### 🚗 FlotasPage (`flotas_page.py`)
- `click_cell_23541048()` - Busca y hace click en celda específica
- `click_livianos_particulares()` - Selecciona tipo de vehículo
- `click_aceptar()` - Confirma selección
- `execute_flotas_flow()` - Ejecuta flujo completo de flotas

### 🎛️ AllianzAutomation (`allianz_automation.py`)
**Clase principal que orquesta todo el proceso:**
- `execute_login_flow()` - Maneja login
- `execute_navigation_flow()` - Maneja navegación
- `execute_flotas_flow()` - Maneja flujo de flotas
- `run_complete_flow()` - **🎯 MÉTODO PRINCIPAL** - Ejecuta todo el proceso

## ⚙️ Configuración

### Credenciales
```python
usuario = "CA031800"
contrasena = "Infondo2025*"
headless = False  # True para ejecutar sin ventana del navegador
```

### Timeouts Configurables
- Login: 30 segundos
- Navegación: 30 segundos  
- Elementos de texto: 20 segundos
- Botones específicos: 15 segundos

## 🔧 Características Técnicas

### ✅ Esperas Dinámicas
- Espera elementos con texto específico
- Manejo de iframes automático
- Reintentos automáticos en fallos

### 🎯 Clicks Inteligentes
- Primero intenta con JavaScript en iframe
- Fallback a selectores directos de Playwright
- Logging detallado de cada intento

### 🛡️ Manejo de Errores Robusto
- Try-catch en cada operación crítica
- Logging detallado con emojis para fácil identificación
- Timeouts configurables por operación

### 📱 Responsivo
- Detecta automáticamente elementos en iframe o página principal
- Adapta estrategias de click según disponibilidad
- Esperas inteligentes según el estado de la página

## 🚨 Puntos Importantes

1. **🔄 Ejecuta exactamente igual que el original** - Toda la lógica se mantiene intacta
2. **📦 Modular y escalable** - Fácil agregar nuevas páginas o funcionalidades  
3. **🐛 Debugging mejorado** - Cada módulo loggea su estado independientemente
4. **🔧 Mantenible** - Cambios en una página no afectan las otras
5. **⚡ Reutilizable** - Los métodos base se pueden usar en otras automatizaciones

## 📈 Próximos Pasos

- Agregar más páginas específicas según necesidades
- Implementar configuración desde archivo externo
- Agregar tests unitarios por módulo
- Métricas de tiempo de ejecución por flujo
