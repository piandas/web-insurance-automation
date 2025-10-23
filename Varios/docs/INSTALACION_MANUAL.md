# 🔧 Instalación Manual (Solo si falla la automática)

## 📋 Pasos de Instalación Manual

### 1️⃣ Verificar Python
```cmd
python --version
```
- Debe mostrar Python 3.8 o superior
- Si no funciona, instalar desde [python.org](https://python.org)

### 2️⃣ Crear Entorno Virtual
```cmd
cd ruta\del\proyecto\MCP
python -m venv .venv
```

### 3️⃣ Activar Entorno Virtual
```cmd
.venv\Scripts\activate
```

### 4️⃣ Instalar Dependencias
```cmd
pip install -r Varios\requirements.txt
```

### 5️⃣ Ejecutar Sistema
```cmd
python scripts\ejecutar_gui.py
```

## ⚠️ Si hay problemas con caracteres
```cmd
python scripts\ejecutar_gui_ascii.py
```

## 🗂️ Estructura de Archivos Importantes

- `ejecutar_cotizaciones.bat` - Ejecutable principal
- `scripts/ejecutar_gui.py` - Interfaz gráfica
- `src/` - Código fuente del sistema
- `requirements.txt` - Lista de dependencias

## 🚨 Problemas Comunes

### Python no reconocido
- Reinstalar Python marcando "Add to PATH"
- Reiniciar CMD después de instalar

### Error de permisos
- Ejecutar CMD como administrador
- Verificar permisos de escritura en la carpeta

### Dependencias fallan
- Verificar conexión a internet
- Actualizar pip: `python -m pip install --upgrade pip`
