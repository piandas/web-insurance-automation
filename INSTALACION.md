# Guía de Instalación - Sistema de Cotizaciones

## Índice

- [Instalación Rápida (3 pasos)](#instalación-rápida-3-pasos)
- [Requisitos Previos](#requisitos-previos)
- [Guía de Uso](#guía-de-uso)
  - [Interfaz Principal](#interfaz-principal)
  - [1. Editar Cliente](#1-editar-cliente)
  - [2. Configuración de Login MFA Sura](#2-configuración-de-login-mfa-sura-requerido-primera-vez-al-dia)
  - [3. Opciones de Configuración](#3-opciones-de-configuración)
  - [4. Configuración de Fórmulas](#4-configuración-de-fórmulas)
  - [5. Resultados](#5-resultados)
  - [6. Ver Historial](#6-ver-historial)
  - [7. Botón Actualizar](#7-botón-actualizar)
  - [8. Detener Automatización](#8-detener-automatización)
- [Solución de Problemas](#solución-de-problemas)
- [Soporte](#soporte)
---

## Instalación Rápida (3 pasos)

### 1. Copiar la Carpeta
Copiar toda la carpeta **MCP** al computador (por ejemplo en el Escritorio o Documentos).

### 2. Configurar Credenciales
1. Abrir el archivo **`.env`** con el **Bloc de notas**
2. Editar las credenciales de las aseguradoras:

```
# CREDENCIALES SURA
SURA_USERNAME=tu_usuario_sura
SURA_PASSWORD=tu_contraseña_sura

# CREDENCIALES ALLIANZ  
ALLIANZ_USERNAME=tu_usuario_allianz
ALLIANZ_PASSWORD=tu_contraseña_allianz
```

3. Guardar y cerrar el archivo

### 3. Ejecutar el Sistema
Hacer **doble clic** en el archivo **`COTIZADOR.bat`**

El sistema automáticamente:
- Verificará Python (te pedirá instalarlo si no lo tienes)
- Creará el entorno virtual
- Instalará todas las dependencias
- Abrirá la interfaz gráfica

**¡Listo para usar!**

---

## Requisitos Previos

### Python 3.10 o superior
Si no se tiene Python instalado:
1. Descargar desde: https://www.python.org/downloads/
2. Durante la instalación, **marcar la casilla**: **"Add Python to PATH"**
3. Instalar normalmente

---

## Guía de Uso

### Interfaz Principal

Al ejecutar `COTIZADOR.bat`, se abre una ventana con estas opciones:

```
┌──────────────────────────────────────────┐
│   SISTEMA DE COTIZACIONES AUTOMATIZADO   │
├──────────────────────────────────────────┤
│                                          │
│  Editar Cliente                          │
│  Ejecutar Cotización                     │
│  Ver Historial                           │
│  Configuración                           │
│  Salir                                   │
│                                          │
└──────────────────────────────────────────┘
```

---

### 1. Editar Cliente

**¿Qué hace?** Crear o editar la información del cliente para cotizar.

**Pasos:**
1. Hacer clic en **"Editar Cliente"**
2. Se abre una ventana con campos para llenar:

#### Datos del Vehículo
- **Placa**: Placa del vehículo (ABC123)
- **Marca**: Selecciona de la lista desplegable (Chevrolet, Renault, Mazda, etc.)
- **Referencia**: Modelo específico del vehículo (Spark GT, Logan, CX-5, etc.)
- **Referencia completa Fasecolda**: Se genera automáticamente combinando Marca + Referencia
- **Modelo**: Año del vehículo (2020, 2021, 2022, etc.)
- **Valor Asegurado**: Valor comercial del vehículo en pesos
- **Clase**: Automóvil, Camioneta, Campero, etc.
- **Línea**: Tipo de vehículo (Particular, Carga, etc.)

#### Códigos FASECOLDA (Automático)
**¡IMPORTANTE!** Los códigos FASECOLDA se buscan **AUTOMÁTICAMENTE** cuando ejecutas la cotización.

- **Búsqueda automática**: El sistema busca los códigos usando Marca, Referencia y Modelo
- **Ingreso manual (opcional)**: Solo si la búsqueda automática falla, puedes llenar:
  - **Código CF**: Código de clase FASECOLDA de SURA
  - **Código CH**: Código de chasis FASECOLDA de ALLIANZ
- **Dejar vacío**: Si no conoces los códigos, déjalos vacíos y el sistema los buscará automáticamente

#### Datos del Cliente
- **Número de documento**: Cédula de ciudadanía
- **Primer nombre**: Primer nombre del cliente
- **Segundo nombre** (opcional): Segundo nombre del cliente
- **Primer apellido**: Primer apellido del cliente
- **Segundo apellido** (opcional): Segundo apellido del cliente
- **Fecha de nacimiento**: En formato DD/MM/AAAA
- **Género**: Masculino o Femenino
- **Teléfono celular**: Número de contacto
- **Ciudad**: Ciudad de residencia
- **Departamento**: 

#### Números de Póliza
- **Número de póliza Sura**
- **Número de póliza Allianz**
- **Fondo**

3. **Guardar** los cambios

**Nota:** Después de guardar, la información se actualizará automáticamente en la ventana principal.

---

### 2. Configuración de Login MFA Sura (Requerido Primera Vez al dia)

**¿Qué hace?** Configura el perfil de Sura para evitar solicitar MFA cada vez.

**¿Cuándo usarlo?**
- **Primera vez** que se usa el sistema con Sura
- Cada vez que **Sura solicite verificación** (aproximadamente cada 7-8 días)
- Si el perfil de Sura se ha **limpiado o eliminado**

**Pasos:**
1. Hacer clic en **"Login MFA Sura"** (botón con candado)
2. Confirmar que desea continuar
3. Se abrirá un navegador automáticamente:
   - Ingresará las credenciales de Sura
   - Si Sura pide MFA, se abrirá una ventana para ingresar el código
   - Marcar automáticamente "Recordar por 8 días"
4. Ingresar el código que llegue al correo o celular
5. El sistema completará el proceso automáticamente
6. Al finalizar, el perfil queda guardado

**Importante:**
- Este proceso debe hacerse **antes de cotizar con Sura por primera vez**
- El perfil guardado permite cotizar sin MFA durante aproximadamente 7-8 días
- Después de ese tiempo, repetir el proceso

---

### 3. Opciones de Configuración

Antes de ejecutar una cotización, configurar las siguientes opciones:

#### ☑️ Activar búsqueda automática de códigos Fasecolda
- **Marcado (recomendado)**: El sistema busca automáticamente los códigos CF y CH
- **Desmarcado**: Requiere ingresar manualmente los códigos en "Editar Cliente"

#### ☑️ Mostrar ventanas del navegador
- **Marcado**: Los navegadores se abren visibles (útil para ver el proceso)
- **Desmarcado (recomendado)**: Los navegadores se ejecutan ocultos (más rápido)

#### ☑️ Modo Debug
- **Marcado**: Muestra todos los logs detallados en consola (para diagnóstico)
- **Desmarcado (recomendado)**: Muestra solo mensajes importantes

---

### 4. Configuración de Fórmulas

**¿Qué hace?** Permite ajustar las fórmulas de cálculo para Bolívar y Solidaria.

**Opciones disponibles:**

#### Fórmulas Bolívar
- Configura los porcentajes y ajustes para cálculos de Bolívar
- Útil si cambian las comisiones o cálculos de la aseguradora

#### Fórmulas Solidaria
- Configura los porcentajes y ajustes para cálculos de Solidaria
- Permite ajustar descuentos y recargos

#### Tasas Solidaria
- Configura las tasas base por clase y línea de vehículo
- Solo modificar si Solidaria actualiza sus tarifas

**Nota:** Estas opciones son avanzadas y normalmente no requieren modificación.

---


### 5. Resultados

Después de ejecutar la cotización, se encontrarán:

#### Carpeta `Descargas/`
PDFs individuales organizados por aseguradora:
```
Descargas/
├── allianz/
│   └── Cotizacion_Allianz_ABC123_20231023.pdf
├── sura/
│   └── Cotizacion_Sura_ABC123_20231023.pdf
├── bolivar/
│   └── Cotizacion_Bolivar_ABC123_20231023.pdf
└── solidaria/
    └── Cotizacion_Solidaria_ABC123_20231023.pdf
```

#### Carpeta `Consolidados/`
Excel unificado con todas las cotizaciones:
```
Consolidados/
└── Cotizacion_ABC123_JuanPerez_20231023_001.xlsx
```

El Excel contiene:
- Datos del vehículo
- Datos del cliente
- Todas las cotizaciones consolidadas
- Comparativa de precios por plan
- Coberturas de cada plan

---

### 6. Ver Historial

**¿Qué hace?** Mostrar todas las cotizaciones previas realizadas.

**Pasos:**
1. Hacer clic en **"Ver Historial"**
2. Se verá una lista con:
   - Fecha de cotización
   - Cliente
   - Placa del vehículo
   - Aseguradoras cotizadas
   - Estado (Exitosa/Fallida)

3. Opciones disponibles:
   - **Ver detalles** de una cotización anterior
   - **Volver a cotizar** con los mismos datos
   - **Eliminar** registros antiguos

---

### 7. Botón Actualizar

**¿Qué hace?** Recarga la información del último cliente guardado.

**Cuándo usarlo:**
- Si se editó el archivo de historial manualmente
- Para verificar que los cambios se guardaron correctamente
- Para recargar datos después de un error

---

### 8. Detener Automatización

**¿Qué hace?** Detiene un proceso de cotización en ejecución.

**Pasos:**
1. Durante una cotización, hacer clic en **"Detener Automatización"**
2. Confirmar que desea detener el proceso
3. El sistema cerrará los navegadores y limpiará los recursos

**Nota:** Los PDFs ya descargados se conservan, pero el Excel consolidado puede quedar incompleto.

---

## Solución de Problemas

### "Python no está instalado"
**Solución**: Instalar Python desde https://python.org y marcar "Add to PATH"

### "Error instalando dependencias"
**Solución**: 
1. Cerrar el programa
2. Eliminar la carpeta `.venv` si existe
3. Volver a ejecutar `COTIZADOR.bat`

### "No se pudo iniciar sesión en Sura" o "Sura pide MFA"
**Solución**: 
1. Hacer clic en **"Login MFA Sura"** en la interfaz principal
2. Seguir el proceso de autenticación
3. El perfil se guardará por 7-8 días
4. Repetir este proceso cada vez que Sura solicite verificación

### "No se pudo iniciar sesión en [Aseguradora]"
**Solución**: 
1. Verificar las credenciales en el archivo `.env`
2. Verificar que las credenciales sean correctas en el sitio web
3. Para Allianz, Bolívar y Solidaria: Verificar que el usuario no esté bloqueado

### "El Excel no tiene valores" o muestra "No encontrado"
**Solución**:
1. Verificar que los PDFs se hayan descargado en `Descargas/`
2. Revisar los logs en `Varios/LOGS/` para ver errores específicos
3. Intentar cotizar solo una aseguradora a la vez
4. Verificar que los datos del vehículo sean correctos (especialmente Marca y Referencia)

### "No se encontró la referencia FASECOLDA"
**Solución**:
1. Verificar que la **Marca** esté seleccionada correctamente de la lista
2. Verificar que la **Referencia** esté escrita exactamente como aparece en FASECOLDA
3. Ejemplo correcto:
   - Marca: `CHEVROLET`
   - Referencia: `SPARK GT 1.2L MT`
   - Referencia completa: `CHEVROLET SPARK GT 1.2L MT`
4. Si el error persiste, ingresar manualmente los **Códigos CF y CH** en la sección "Códigos Fasecolda Manuales"

### "Los navegadores no se ven"
**Solución**: 
1. Marcar la opción **"Mostrar ventanas del navegador"** en la configuración
2. Esto permite ver el proceso en tiempo real
3. Útil para diagnóstico de problemas

### "El proceso se queda pegado"
**Solución**:
1. Hacer clic en **"Detener Automatización"**
2. Esperar a que cierre los navegadores
3. Si no responde, cerrar y volver a abrir el programa
4. Marcar **"Modo Debug"** para ver dónde falla el proceso

---

## Soporte

En caso de problemas:
1. Revisar la carpeta `Varios/LOGS/` para ver errores detallados
2. Verificar que la conexión a internet esté funcionando
3. Asegurarse de que las credenciales sean correctas

---

