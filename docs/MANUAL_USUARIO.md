# 🚗 Sistema de Automatización de Cotizaciones - Agencia Infondo

## 📋 Descripción del Proyecto

Sistema automatizado para generar cotizaciones de seguros vehiculares en múltiples aseguradoras de forma simultánea. Actualmente soporta **Allianz** y **Sura** con capacidad de expansión a otras compañías.

## 🎯 Características Principales

- ✅ **Automatización completa** de cotizaciones vehiculares
- 🏢 **Multi-compañía**: Allianz y Sura
- 📊 **Consolidación automática** en Excel
- 🖥️ **Interfaz gráfica** intuitiva
- 📄 **Generación de PDFs** automática
- 📝 **Sistema de logs** detallado
- 🔄 **Procesamiento paralelo** para mayor velocidad

## 🚀 Instalación y Uso Rápido

### ⚡ Instalación Automática (Recomendada)

1. **Descarga** toda la carpeta del proyecto
2. **Asegúrate** de tener Python instalado (con "Add to PATH")
3. **Doble clic** en `ejecutar_cotizaciones.bat`
4. **¡Listo!** - Todo se instala y ejecuta automáticamente

### 📋 Requisitos del Sistema

- **Windows** 7/8/10/11
- **Python** 3.8 o superior
- **Conexión a internet** (para instalación de dependencias)
- **Chrome/Edge** (se instala automáticamente si no existe)

## 📁 Estructura del Proyecto

```
MCP/
├── ejecutar_cotizaciones.bat    # 🎯 EJECUTAR AQUÍ (Doble clic)
├── requirements.txt             # 📦 Dependencias Python
├── README.md                   # 📖 Este archivo
├── scripts/                    # 🔧 Scripts ejecutables
│   ├── ejecutar_gui.py         # Interfaz gráfica principal
│   ├── ejecutar_gui_ascii.py   # Interfaz compatible
│   └── ejecutar_automatizaciones.py  # Script de automatización
├── docs/                       # 📚 Documentación
│   └── Notas.txt              # Notas del desarrollo
├── src/                        # 💻 Código fuente
│   ├── companies/             # Módulos por aseguradora
│   ├── core/                  # Núcleo del sistema
│   ├── config/                # Configuraciones
│   └── shared/                # Recursos compartidos
├── Consolidados/              # 📊 Reportes Excel generados
├── downloads/                 # 📄 PDFs de cotizaciones
│   ├── allianz/              # PDFs de Allianz
│   └── sura/                 # PDFs de Sura
├── LOGS/                     # 📝 Logs del sistema
└── browser_profiles/         # 🌐 Perfiles de navegador
```

## 🔧 Modo de Uso

### 1️⃣ Ejecución Simple
- Doble clic en `ejecutar_cotizaciones.bat`
- Se abre la interfaz gráfica
- Llenar datos del vehículo
- Clic en "Ejecutar Automatización"

### 2️⃣ Datos Requeridos
- **Placa**: AAA000 o AAA00A
- **Cédula**: Sin puntos ni espacios
- **Año del vehículo**: 2010-2025
- **Ciudad**: Seleccionar de la lista

### 3️⃣ Resultados
- **PDFs**: Se guardan en `downloads/[aseguradora]/`
- **Excel consolidado**: Se guarda en `Consolidados/`
- **Logs**: Se guardan en `LOGS/` para troubleshooting

## 🏢 Aseguradoras Soportadas

### ✅ Allianz (Completamente Funcional)
- Automatización 100% implementada
- Manejo de errores avanzado
- Descarga automática de PDFs

### ⚠️ Sura (En Desarrollo)
- Estructura base implementada
- Requiere ajustes específicos
- Expandible fácilmente

## 🆘 Solución de Problemas

### ❌ "Python no está instalado"
- Instalar Python desde [python.org](https://python.org)
- ✅ **IMPORTANTE**: Marcar "Add Python to PATH"

### ❌ Error de caracteres raros
- El sistema automáticamente usa modo compatibilidad
- Se ejecuta la versión ASCII como respaldo

### ❌ El navegador no abre
- Verificar conexión a internet
- El sistema instala Chrome automáticamente si es necesario

## 📧 Soporte y Contacto

Para soporte técnico o consultas:
- **Desarrollador**: [Tu nombre/contacto]
- **Empresa**: Agencia Infondo
- **Fecha**: Agosto 2025

---

**© 2025 Agencia Infondo - Sistema de Automatización de Cotizaciones**
