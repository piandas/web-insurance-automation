# 🚗 Automatización Allianz - Sistema de Cotizaciones

## 📋 Descripción del Proyecto

Este proyecto automatiza el proceso completo de cotización de seguros en el sistema web de Allianz, desde el login hasta la generación y descarga del PDF de cotización. Utiliza **Playwright** para la automatización web y sigue el patrón **Page Object Model** para una estructura de código mantenible y escalable.

## 🏗️ Estructura del Proyecto

```
MCP/
├── src/
│   ├── pages/
│   │   ├── __init__.py           # Configuración del paquete
│   │   ├── login_page.py         # 🔐 Manejo de autenticación
│   │   ├── dashboard_page.py     # 🏠 Navegación en dashboard
│   │   ├── flotas_page.py        # 🚗 Gestión de flotas y documentos
│   │   └── placa_page.py         # 📋 Proceso de placa y cotización
│   ├── allianz_automation.py     # 🎯 Orquestador principal
│   ├── config.py                 # ⚙️ Configuraciones centralizadas
│   └── utils.py                  # 🛠️ Utilidades y clase base
├── tests/
│   └── test_flujo_allianz.py     # 🧪 Pruebas automatizadas
├── downloads/                    # 📁 PDFs generados
├── LOGS/                         # 📝 Logs del sistema
├── .env.example                  # 🔑 Plantilla de variables sensibles
├── requirements.txt              # 📦 Dependencias del proyecto
└── README.md                     # 📚 Documentación

## 🔧 Descripción de Componentes

### 📋 `config.py` - Configuración Centralizada
**Configuraciones sensibles** (desde variables de entorno):
- Credenciales de usuario y contraseña
- Configuración del navegador (headless, timeout)
- URL base del sistema

**Configuraciones de negocio** (valores directos):
```python
# Configuraciones de Flotas
POLICY_NUMBER = '123456'           # Número de póliza
RAMO_SEGURO = 'Livianos Particulares' # Tipo de seguro
TIPO_DOCUMENTO = 'CEDULA_CIUDADANIA' # Tipo de documento
NUMERO_DOCUMENTO = '123456'      # Número de documento

# Configuraciones de Placa
PLACA_VEHICULO = 'ABC123'           # Placa del vehículo
FECHA_NACIMIENTO = '01/01/1999'     # Fecha (se limpia automáticamente)
GENERO_ASEGURADO = 'M'              # M, F, J
DEPARTAMENTO = 'ANTIOQUIA'          # Departamento
CIUDAD = 'MEDELLIN'                    # Ciudad
```

### 🛠️ `utils.py` - Clase BasePage
Contiene métodos genéricos reutilizables:
- **Gestión de iframes**: `wait_for_iframe_content()`, `click_in_frame()`
- **Interacciones avanzadas**: `fill_in_frame()`, `select_in_frame()`, `click_by_text_in_frame()`
- **Verificaciones**: `verify_element_value_in_frame()` con múltiples condiciones
- **Utilidades**: `wait_for_element_with_text()`, manejo de timeouts

### 🔐 `pages/login_page.py` - LoginPage
Maneja todo el proceso de autenticación:
- Navegación a la URL de login
- Llenado de credenciales desde configuración
- Envío del formulario y validación
- Método `login()` que orquesta el proceso completo

### 🏠 `pages/dashboard_page.py` - DashboardPage
Navegación en el panel principal:
- Clic en "Nueva Póliza"
- Expansión de sección "Autos"
- Selección de "Flotas Autos"
- Transición a página de aplicación

### 🚗 `pages/flotas_page.py` - FlotasPage
Gestión completa del proceso de flotas:
- **`click_policy_cell()`**: Selecciona póliza configurada
- **`click_ramos_asociados()`**: Selecciona tipo de seguro
- **`select_tipo_documento()`**: Selecciona tipo de documento
- **`fill_numero_documento()`**: Llena número de documento
- **`execute_flotas_flow()`**: Ejecuta flujo completo automatizado

### 📋 `pages/placa_page.py` - PlacaPage
Proceso completo de cotización:
- **`esperar_y_llenar_placa()`**: Ingresa placa del vehículo
- **`llenar_datos_asegurado()`**: Fecha y género (limpia formato automáticamente)
- **`buscador_poblaciones()`**: Selecciona departamento y ciudad
- **`consultar_y_finalizar()`**: Genera y descarga PDF de cotización
- **`execute_placa_flow()`**: Orquesta proceso completo

### 🎯 `allianz_automation.py` - Orquestador Principal
Clase principal que coordina todo el flujo:
- Inicialización del navegador Playwright
- Configuración de logging (consola + archivo)
- Instanciación de todas las páginas
- Ejecución del flujo completo de automatización
- Manejo de errores y limpieza de recursos

## 🚀 Instalación y Configuración

### 1. Clonar e Instalar Dependencias
```bash
# Clonar el repositorio
git clone <tu-repositorio>
cd MCP

# Instalar dependencias de Python
pip install -r requirements.txt

# Instalar navegadores de Playwright
playwright install
```

### 2. Configurar Variables de Entorno
```bash
# Copiar plantilla de configuración
copy .env.example .env

# Editar .env con tus credenciales
USUARIO=tu_usuario_allianz
CONTRASENA=tu_contraseña_allianz
HEADLESS=False
BASE_URL=https://www.allia2net.com.co
TIMEOUT=30000
```

### 3. Personalizar Configuraciones
Edita `src/config.py` para ajustar valores según tus necesidades:
```python
# Cambiar datos de prueba
POLICY_NUMBER = '12345678'        # Tu número de póliza
RAMO_SEGURO = 'Motos'            # Tipo de seguro deseado
PLACA_VEHICULO = 'ABC123'        # Placa a cotizar
NUMERO_DOCUMENTO = '123456'   # Documento del asegurado
DEPARTAMENTO = 'CUNDINAMARCA'    # Tu departamento
CIUDAD = 'BOGOTA'                # Tu ciudad
```

## 🎯 Uso del Sistema

### Ejecución Básica
```bash
cd src
python allianz_automation.py
```

### Uso Programático
```python
from src.allianz_automation import AllianzAutomation

async def main():
    # Usar configuración por defecto
    automation = AllianzAutomation()
    
    # O personalizar parámetros
    automation = AllianzAutomation(
        usuario="mi_usuario",
        contrasena="mi_contraseña",
        headless=True  # Ejecutar sin ventana
    )
    
    await automation.launch()
    success = await automation.run_complete_automation()
    await automation.close()
    
    return success

# Ejecutar
import asyncio
result = asyncio.run(main())
```

### Ejecución de Pruebas
```bash
# Ejecutar pruebas automatizadas
cd tests
python test_flujo_allianz.py
```

## ✨ Características Destacadas

### 🎯 **Configuración Centralizada**
- **Datos sensibles**: Credenciales en `.env`
- **Configuraciones de negocio**: Valores directos en `config.py`
- **Flexibilidad**: Cambiar valores sin tocar código

### 🔄 **Automatización Inteligente**
- **Limpieza automática**: Fechas con formato `01/06/1989` → `01061989`
- **Manejo de iframes**: Detección y trabajo automático con frames
- **Verificaciones robustas**: Múltiples condiciones de validación
- **Timeouts configurables**: Esperas adaptables según necesidad

### 📊 **Logging Avanzado**
- **Dual output**: Consola + archivo de log
- **Niveles de detalle**: Info, errores, advertencias
- **Ubicación**: Logs guardados en `LOGS/log.log`
- **Formato**: Timestamp + nivel + mensaje

### 🛡️ **Manejo de Errores**
- **Recuperación automática**: Reintentos en operaciones críticas
- **Logging detallado**: Errores con contexto completo
- **Limpieza de recursos**: Cierre automático del navegador

### 📁 **Gestión de Archivos**
- **Descarga automática**: PDFs guardados en `downloads/`
- **Nomenclatura clara**: `Cotizacion_Allianz_YYYYMMDD_HHMMSS.pdf`
- **Verificación**: Validación de descarga exitosa

## 🔧 Ventajas de la Arquitectura

### 📐 **Patrón Page Object Model**
- **Separación clara**: Cada página maneja su responsabilidad
- **Reutilización**: Métodos genéricos en `BasePage`
- **Mantenibilidad**: Cambios localizados por página
- **Testabilidad**: Cada componente puede probarse independientemente

### 🔄 **Escalabilidad**
- **Nuevas páginas**: Fácil agregar siguiendo el patrón
- **Nuevas funciones**: Extensión sin afectar código existente
- **Configuraciones**: Agregar nuevos valores sin cambios de código

### 🎨 **Legibilidad**
- **Nombres descriptivos**: Funciones autoexplicativas
- **Documentación**: Docstrings detallados
- **Comentarios**: Explicaciones en código complejo
- **Estructura lógica**: Organización intuitive

## 🚀 Flujo de Automatización

### 1. **Inicialización**
```
🔧 Configurar navegador Playwright
📝 Configurar sistema de logging
🎯 Instanciar páginas (Login, Dashboard, Flotas, Placa)
```

### 2. **Autenticación**
```
🌐 Navegar a URL de login
🔐 Llenar credenciales desde config
✅ Validar acceso exitoso
```

### 3. **Navegación Dashboard**
```
🏠 Acceder a "Nueva Póliza"
🚗 Expandir sección "Autos"
📋 Seleccionar "Flotas Autos"
```

### 4. **Proceso de Flotas**
```
🔢 Seleccionar póliza configurada
🚗 Elegir tipo de seguro
📄 Configurar tipo de documento
✏️ Llenar número de documento
```

### 5. **Proceso de Placa**
```
🚗 Ingresar placa del vehículo
👤 Completar datos del asegurado
🏙️ Seleccionar ubicación
📋 Generar cotización
```

### 6. **Finalización**
```
📄 Generar PDF de cotización
💾 Descargar archivo automáticamente
🗂️ Guardar en carpeta downloads/
✅ Confirmar proceso exitoso
```

## 🛠️ Desarrollo y Contribución

### Estructura de Desarrollo
```bash
# Crear nueva página
src/pages/nueva_page.py     # Siguiendo patrón existente
# Agregar import en
src/pages/__init__.py       # Para exportar la nueva página
# Instanciar en
src/allianz_automation.py  # En el constructor
```

### Agregar Nueva Configuración
```python
# En config.py
NUEVA_CONFIG: str = 'valor_por_defecto'

# Usar en cualquier página
from src.config import Config
valor = Config.NUEVA_CONFIG
```

### Debugging
```python
# Para debugging, cambiar en config.py o al instanciar
HEADLESS = False  # Ver navegador en acción

# Logs detallados en
LOGS/log.log
```

## 📞 Soporte y Documentación

### Archivos de Referencia
- **`CAMBIOS_CONFIGURACION.md`**: Historial de cambios de configuración  
- **`.env.example`**: Plantilla de variables de entorno
- **`LOGS/log.log`**: Logs detallados de ejecución

### Solución de Problemas Comunes

**❌ Error de credenciales**
```bash
# Verificar archivo .env
USUARIO=tu_usuario_correcto
CONTRASENA=tu_contraseña_correcta
```

**❌ Timeout en elementos**
```python
# Aumentar timeout en config.py
TIMEOUT = 60000  # 60 segundos
```

**❌ Error de navegador**
```bash
# Reinstalar navegadores
playwright install
```

**❌ Placa/documento no válido**
```python
# Verificar configuraciones en config.py
PLACA_VEHICULO = 'ABC123'  # Formato válido
NUMERO_DOCUMENTO = '1234567890'  # Solo números
```

---

### 🌟 **¡Sistema de Automatización de Cotizaciones Allianz Listo!**

**Desarrollado con ❤️ usando Playwright + Python**

*Configuración centralizada • Arquitectura escalable • Logging avanzado • Manejo de errores robusto*
