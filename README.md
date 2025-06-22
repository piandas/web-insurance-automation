# 🚗 Sistema de Automatización Multi-Compañía - Cotizaciones de Seguros

## 📋 Descripción del Proyecto

Sistema modular y escalable para automatizar procesos de cotización en múltiples aseguradoras. Actualmente soporta **Allianz** (completamente implementado) y **Sura** (estructura base preparada). Utiliza **Playwright** para automatización web y sigue patrones de diseño escalables.

## 🏗️ Estructura del Proyecto (Nueva Arquitectura)

```
MCP/
├── main.py                          # 🎯 Punto de entrada principal
├── requirements.txt                 # � Dependencias
├── .env                            # � Variables de entorno
├── downloads/                      # � PDFs generados
│   ├── allianz/                   # PDFs de Allianz
│   └── sura/                      # PDFs de Sura
├── LOGS/                          # � Logs del sistema
│   ├── allianz/                   # Logs de Allianz
│   └── sura/                      # Logs de Sura
└── src/
    ├── __init__.py                # Módulo principal
    ├── core/                      # 🏛️ Núcleo del sistema
    │   ├── base_automation.py     # Clase base abstracta
    │   ├── automation_manager.py  # Orquestador principal
    │   ├── logger_factory.py      # Factory de loggers
    │   └── constants.py           # Constantes globales
    ├── config/                    # ⚙️ Configuraciones
    │   ├── base_config.py         # Configuración base
    │   ├── allianz_config.py      # Config específica Allianz
    │   └── sura_config.py         # Config específica Sura
    ├── shared/                    # 🔄 Recursos compartidos
    │   ├── base_page.py           # Página base común
    │   ├── utils.py               # Utilidades generales
    │   └── exceptions.py          # Excepciones personalizadas
    ├── companies/                 # 🏢 Módulos por compañía
    │   ├── allianz/              # Implementación Allianz
    │   │   ├── allianz_automation.py
    │   │   └── pages/            # Páginas específicas
    │   │       ├── login_page.py
    │   │       ├── dashboard_page.py
    │   │       ├── flotas_page.py
    │   │       └── placa_page.py
    │   └── sura/                 # Implementación Sura (base)
    │       ├── sura_automation.py
    │       └── pages/            # Páginas específicas
    │           ├── login_page.py
    │           ├── dashboard_page.py
    │           └── quote_page.py
    ├── factory/                  # 🏭 Factories
    │   ├── automation_factory.py # Factory de automatizaciones
    │   └── config_factory.py     # Factory de configuraciones
    └── interfaces/               # 🖥️ Interfaces de usuario
        └── cli_interface.py      # Interfaz línea de comandos
```

## ✨ Características Destacadas

### 🎯 **Arquitectura Modular**
- **Separación por compañías**: Cada aseguradora en su propio módulo
- **Código reutilizable**: Clases base compartidas
- **Fácil extensión**: Agregar nuevas aseguradoras sin afectar código existente

### ⚡ **Ejecución Flexible**
- **Secuencial**: Una compañía tras otra
- **Paralelo**: Múltiples compañías simultáneamente
- **Selectiva**: Elegir qué compañías ejecutar

### � **Configuración Avanzada**
- **Variables por compañía**: Configuraciones independientes
- **Compatibilidad hacia atrás**: Mantiene configuración original de Allianz
- **Fácil personalización**: Sobrescribir configuraciones via CLI

### 📊 **Logging Inteligente**
- **Logs separados**: Cada compañía tiene su propio log
- **Dual output**: Consola + archivo
- **Factory pattern**: Gestión centralizada de loggers

## 🚀 Instalación y Configuración

### 1. Dependencias
```bash
# Instalar dependencias
pip install -r requirements.txt

# Instalar navegadores de Playwright
playwright install
```

### 2. Configuración de Variables
Edita el archivo `.env` con tus credenciales:

```env
# Configuración Allianz
ALLIANZ_USUARIO=tu_usuario_allianz
ALLIANZ_CONTRASENA=tu_contraseña_allianz

# Configuración Sura (cuando esté disponible)
SURA_USUARIO=tu_usuario_sura
SURA_CONTRASENA=tu_contraseña_sura

# Configuración general
HEADLESS=False  # True para ejecutar sin ventana
```

## 🎯 Uso del Sistema

### Interfaz de Línea de Comandos

#### Comandos Básicos
```bash
# Ejecutar solo Allianz
python -m src.interfaces.cli_interface --companies allianz

# Ejecutar en paralelo (cuando Sura esté listo)
python -m src.interfaces.cli_interface --companies allianz sura --parallel

# Ejecutar en modo headless
python -m src.interfaces.cli_interface --companies allianz --headless

# Ver compañías disponibles
python -m src.interfaces.cli_interface --list-companies
```

#### Configuraciones Personalizadas
```bash
# Con credenciales específicas
python -m src.interfaces.cli_interface --companies allianz --user mi_usuario --password mi_pass

# Modo verbose
python -m src.interfaces.cli_interface --companies allianz --verbose
```

### Uso Programático

```python
from src.factory.automation_factory import AutomationFactory
from src.core.automation_manager import AutomationManager

# Crear automatización específica
automation = AutomationFactory.create('allianz')
await automation.launch()
success = await automation.run_complete_flow()
await automation.close()

# Usar el manager para múltiples compañías
manager = AutomationManager()
results = await manager.run_parallel(['allianz', 'sura'])
```

## 🏢 Estado de las Compañías

### ✅ Allianz - COMPLETAMENTE FUNCIONAL
- **Login**: ✅ Implementado
- **Navegación**: ✅ Dashboard → Flotas
- **Flotas**: ✅ Selección de póliza, ramo, documentos
- **Placa**: ✅ Verificación, datos asegurado, ubicación
- **Cotización**: ✅ Generación y descarga de PDF
- **Logs**: ✅ Separados en `LOGS/allianz/`
- **Descargas**: ✅ Separadas en `downloads/allianz/`

### � Sura - ESTRUCTURA BASE PREPARADA
- **Arquitectura**: ✅ Estructura modular creada
- **Configuración**: ✅ Variables de entorno preparadas
- **Logging**: ✅ Logger específico configurado
- **Páginas**: ⏳ Esqueleto básico (pendiente implementación real)
- **Implementación**: ⏳ Pendiente según especificaciones de Sura

## � Migración desde Versión Anterior

### Cambios Principales
1. **Estructura modular**: Código reorganizado por compañías
2. **Configuración expandida**: Variables específicas por aseguradora
3. **Logging mejorado**: Logs separados por compañía
4. **Interfaces múltiples**: CLI preparada para futuras interfaces web

### Compatibilidad
- **Variables originales**: Mantenidas para compatibilidad
- **Funcionalidad Allianz**: 100% funcional
- **Configuraciones**: Se mantienen valores por defecto

## 🛠️ Desarrollo y Extensión

### Agregar Nueva Compañía

1. **Crear estructura**:
```bash
src/companies/nueva_compania/
├── __init__.py
├── nueva_automation.py
└── pages/
    ├── __init__.py
    ├── login_page.py
    └── quote_page.py
```

2. **Configuración**:
```python
# src/config/nueva_config.py
class NuevaConfig(BaseConfig):
    USUARIO = os.getenv('NUEVA_USUARIO', '')
    # ... otras configuraciones
```

3. **Registrar en factory**:
```python
# src/factory/automation_factory.py
elif company_lower == 'nueva':
    from ..companies.nueva.nueva_automation import NuevaAutomation
    return NuevaAutomation(...)
```

### Personalizar Flujos

Cada compañía implementa los métodos base:
- `execute_login_flow()`
- `execute_navigation_flow()`
- `execute_quote_flow()`

## � Comandos Útiles

```bash
# Ver ayuda completa
python main.py --help

# Ejecutar con máximo detalle
python main.py --companies allianz --verbose

# Verificar configuración
python -c "from src.config.allianz_config import AllianzConfig; print(AllianzConfig.USUARIO)"

# Probar factory
python -c "from src.factory.automation_factory import AutomationFactory; print(AutomationFactory.get_supported_companies())"
```

## 🎯 Flujo de Automatización Allianz

1. **🔧 Inicialización**: Configurar navegador específico para Allianz
2. **🔐 Login**: Autenticación en portal Allianz
3. **🧭 Navegación**: Dashboard → Nueva Póliza → Autos → Flotas
4. **🚗 Flotas**: Seleccionar póliza, ramo, tipo documento
5. **🔍 Placa**: Verificar vehículo, datos asegurado, ubicación
6. **💰 Cotización**: Generar y descargar PDF
7. **📁 Archivo**: Guardar en `downloads/allianz/`

## 🔮 Roadmap

---

### 🌟 **Sistema Modular de Automatización Multi-Compañía**

**Desarrollado para Infondo Agencias de Seguros por el Ingeniero Santiago Bustos usando Playwright + Python**

*Arquitectura escalable • Logging avanzado • Configuración flexible • Ejecución paralela*
