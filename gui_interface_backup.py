"""
Interfaz gráfica para el sistema de automatización de cotizaciones.

Esta interfaz proporciona una manera visual y sencilla de ejecutar
las automatizaciones con opciones configurables.
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import asyncio
import threading
import subprocess
import sys
import os
from pathlib import Path
from typing import Optional
import queue
import re

# Importar configuración del cliente
sys.path.insert(0, str(Path(__file__).parent.parent))
from config.client_config import ClientConfig


class AutomationGUI:
    """Interfaz gráfica principal para las automatizaciones."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Sistema de Automatización de Cotizaciones")
        self.root.geometry("600x500")
        self.root.resizable(True, True)
        
        # Variables de configuración
        self.estado_vehiculo = tk.StringVar(value=ClientConfig.VEHICLE_STATE)
        self.fasecolda_automatico = tk.BooleanVar(value=ClientConfig.ENABLE_FASECOLDA_SEARCH)
        self.mostrar_ventanas = tk.BooleanVar(value=False)  # Por defecto en segundo plano
        self.modo_debug = tk.BooleanVar(value=False)  # Modo debug desactivado por defecto
        
        # Variables de control
        self.proceso_activo = False
        self.proceso_thread = None
        self.loading_animation = None
        self.animation_frame = 0
        self.proceso_subprocess = None  # Referencia al proceso subprocess
        
        # Cola para comunicación entre hilos
        self.message_queue = queue.Queue()
        self.response_queue = queue.Queue()  # Cola para respuestas del usuario
        
        # Crear la interfaz
        self.setup_ui()
        
        # Configurar manejo de cierre
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Iniciar el monitoreo de mensajes
        self.check_message_queue()
    
    def setup_ui(self):
        """Configura todos los elementos de la interfaz."""
        # Estilo
        style = ttk.Style()
        style.theme_use('clam')
        
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configurar grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(4, weight=1)
        
        # Título
        title_label = ttk.Label(
            main_frame, 
            text="🚗 Sistema de Automatización de Cotizaciones",
            font=("Arial", 14, "bold")
        )
        title_label.grid(row=0, column=0, pady=(0, 10), sticky=tk.W+tk.E)
        
        # Frame de información del cliente
        info_frame = ttk.LabelFrame(main_frame, text="Información del Cliente", padding="10")
        info_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        info_frame.columnconfigure(1, weight=1)
        
        # Botón de actualizar cliente
        self.actualizar_cliente_btn = ttk.Button(
            info_frame,
            text="🔄 Actualizar Cliente",
            command=self.actualizar_informacion_cliente,
            width=20
        )
        self.actualizar_cliente_btn.grid(row=0, column=2, rowspan=3, padx=(20, 0), sticky=tk.N)
        
        # Crear campos de información del cliente
        self.crear_campos_cliente(info_frame)
        
        # Frame de configuración
        config_frame = ttk.LabelFrame(main_frame, text="Configuración", padding="10")
        config_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        config_frame.columnconfigure(1, weight=1)
        
        # Opción: Estado del vehículo
        ttk.Label(config_frame, text="Estado del vehículo:").grid(row=0, column=0, sticky=tk.W, pady=5)
        estado_combo = ttk.Combobox(
            config_frame, 
            textvariable=self.estado_vehiculo,
            values=["Nuevo", "Usado"],
            state="readonly",
            width=15
        )
        estado_combo.grid(row=0, column=1, sticky=tk.W, pady=5, padx=(10, 0))
        
        # Opción: Búsqueda automática de Fasecolda
        fasecolda_check = ttk.Checkbutton(
            config_frame,
            text="Activar búsqueda automática de códigos Fasecolda",
            variable=self.fasecolda_automatico
        )
        fasecolda_check.grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # Opción: Mostrar ventanas del navegador
        ventanas_check = ttk.Checkbutton(
            config_frame,
            text="Mostrar ventanas del navegador (por defecto están ocultas)",
            variable=self.mostrar_ventanas
        )
        ventanas_check.grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # Opción: Modo debug
        debug_check = ttk.Checkbutton(
            config_frame,
            text="🔧 Modo Debug (mostrar todos los logs en consola)",
            variable=self.modo_debug,
            command=self.toggle_debug_mode
        )
        debug_check.grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # Frame de controles
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        control_frame.columnconfigure(0, weight=1)
        
        # Botones
        button_frame = ttk.Frame(control_frame)
        button_frame.grid(row=0, column=0)
        
        self.ejecutar_btn = ttk.Button(
            button_frame,
            text="🚀 Ejecutar Automatización",
            command=self.ejecutar_automatizacion,
            width=25
        )
        self.ejecutar_btn.grid(row=0, column=0, padx=(0, 5))
        
        self.detener_btn = ttk.Button(
            button_frame,
            text="⏹️ Detener Cotización",
            command=self.detener_automatizacion,
            width=20,
            state=tk.DISABLED
        )
        self.detener_btn.grid(row=0, column=1, padx=(0, 5))
        
        self.cerrar_btn = ttk.Button(
            button_frame,
            text="❌ Cerrar",
            command=self.on_closing,
            width=15
        )
        self.cerrar_btn.grid(row=0, column=2)
        
        # Indicador de carga animado
        self.loading_frame = ttk.Frame(control_frame)
        self.loading_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        self.loading_frame.columnconfigure(0, weight=1)
        
        self.loading_label = ttk.Label(self.loading_frame, text="Listo para ejecutar", font=("Arial", 10))
        self.loading_icon = ttk.Label(self.loading_frame, text="", font=("Arial", 16))
        
        # Frame de consola
        self.console_frame = ttk.LabelFrame(main_frame, text="Consola de Estado", padding="5")
        self.console_frame.grid(row=4, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        self.console_frame.columnconfigure(0, weight=1)
        self.console_frame.rowconfigure(0, weight=1)
        
        # Área de texto con scroll
        self.console_text = scrolledtext.ScrolledText(
            self.console_frame,
            height=12,
            width=70,
            wrap=tk.WORD,
            state=tk.DISABLED,
            font=("Courier", 9)
        )
        self.console_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Input para respuestas (inicialmente oculto)
        self.input_frame = ttk.Frame(self.console_frame)
        self.input_var = tk.StringVar()
        self.input_entry = ttk.Entry(self.input_frame, textvariable=self.input_var, width=50)
        self.input_button = ttk.Button(self.input_frame, text="Enviar", command=self.enviar_respuesta)
        
        # Mensaje inicial
        self.agregar_mensaje("✅ Sistema listo. Configure las opciones y presione 'Ejecutar Automatización'.", "info")
        self.agregar_mensaje(" Active 'Modo Debug' para ver todos los logs del proceso.", "info")
    
    def crear_campos_cliente(self, parent_frame):
        """Crea los campos de información del cliente."""
        try:
            # Forzar recarga del módulo ClientConfig para obtener los valores más recientes
            import importlib
            from config import client_config
            importlib.reload(client_config)
            config = client_config.ClientConfig.get_current_config()
        except Exception:
            # Fallback si hay error
            config = ClientConfig.get_current_config()
        
        # Etiquetas para mostrar información
        ttk.Label(parent_frame, text="Cliente:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.cliente_label = ttk.Label(parent_frame, text=config['client_name'], font=("Arial", 9, "bold"))
        self.cliente_label.grid(row=0, column=1, sticky=tk.W, pady=2, padx=(10, 0))
        
        ttk.Label(parent_frame, text="Vehículo:").grid(row=1, column=0, sticky=tk.W, pady=2)
        vehicle_info = f"{config['vehicle_brand']} {config['vehicle_reference']} ({config['vehicle_year']})"
        self.vehiculo_label = ttk.Label(parent_frame, text=vehicle_info, font=("Arial", 9))
        self.vehiculo_label.grid(row=1, column=1, sticky=tk.W, pady=2, padx=(10, 0))
        
        ttk.Label(parent_frame, text="Placa:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.placa_label = ttk.Label(parent_frame, text=config['vehicle_plate'], font=("Arial", 9, "bold"))
        self.placa_label.grid(row=2, column=1, sticky=tk.W, pady=2, padx=(10, 0))
    
    def actualizar_informacion_cliente(self):
        """Actualiza la información del cliente desde la configuración."""
        if self.proceso_activo:
            messagebox.showwarning("Proceso en ejecución", "No se puede actualizar la información mientras hay un proceso ejecutándose.")
            return
            
        try:
            # Forzar recarga del módulo ClientConfig para obtener los valores más recientes
            import importlib
            from config import client_config
            importlib.reload(client_config)
            
            # Obtener la configuración actualizada
            config = client_config.ClientConfig.get_current_config()
            
            # Actualizar las etiquetas
            self.cliente_label.config(text=config['client_name'])
            vehicle_info = f"{config['vehicle_brand']} {config['vehicle_reference']} ({config['vehicle_year']})"
            self.vehiculo_label.config(text=vehicle_info)
            self.placa_label.config(text=config['vehicle_plate'])
            
            # Actualizar variables de configuración
            self.estado_vehiculo.set(client_config.ClientConfig.VEHICLE_STATE)
            self.fasecolda_automatico.set(client_config.ClientConfig.ENABLE_FASECOLDA_SEARCH)
            
            self.agregar_mensaje("✅ Información del cliente actualizada correctamente", "success")
            self.agregar_mensaje(f"👤 Cliente: {config['client_name']}", "info")
            self.agregar_mensaje(f"🚗 Vehículo: {config['vehicle_brand']} {config['vehicle_reference']} ({config['vehicle_year']})", "info")
            self.agregar_mensaje(f"🔖 Placa: {config['vehicle_plate']}", "info")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error actualizando información del cliente: {e}")
            self.agregar_mensaje(f"❌ Error actualizando información: {e}", "error")
    
    def toggle_debug_mode(self):
        """Maneja el cambio del modo debug."""
        if self.modo_debug.get():
            # Activar modo debug
            self.console_frame.config(text="🔧 Consola de Estado - MODO DEBUG (todos los logs)")
            self.agregar_mensaje("🔧 MODO DEBUG ACTIVADO - Se mostrarán todos los logs del proceso", "warning")
        else:
            # Desactivar modo debug
            self.console_frame.config(text="Consola de Estado")
            self.agregar_mensaje("💭 Modo normal - Solo se mostrarán opciones de Fasecolda", "info")
    
    def agregar_mensaje(self, mensaje: str, tipo: str = "info"):
        """Agrega un mensaje a la consola."""
        self.console_text.config(state=tk.NORMAL)
        
        # Configurar colores según el tipo
        if tipo == "error":
            tag = "error"
            self.console_text.tag_config(tag, foreground="red")
        elif tipo == "success":
            tag = "success"
            self.console_text.tag_config(tag, foreground="green")
        elif tipo == "warning":
            tag = "warning"
            self.console_text.tag_config(tag, foreground="orange")
        elif tipo == "input_request":
            tag = "input_request"
            self.console_text.tag_config(tag, foreground="blue", background="lightyellow")
        else:
            tag = "info"
            self.console_text.tag_config(tag, foreground="black")
        
        # Agregar timestamp
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        self.console_text.insert(tk.END, f"[{timestamp}] {mensaje}\n", tag)
        self.console_text.see(tk.END)
        self.console_text.config(state=tk.DISABLED)
    
    def mostrar_input(self, prompt: str):
        """Muestra el campo de input para respuestas del usuario."""
        self.agregar_mensaje(prompt, "input_request")
        
        self.input_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
        self.input_frame.columnconfigure(0, weight=1)
        
        self.input_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        self.input_button.grid(row=0, column=1)
        
        # Focus en el input
        self.input_entry.focus_set()
        
        # Bind Enter key
        self.input_entry.bind('<Return>', lambda e: self.enviar_respuesta())
    
    def ocultar_input(self):
        """Oculta el campo de input."""
        self.input_frame.grid_remove()
        self.input_var.set("")
    
    def enviar_respuesta(self):
        """Envía la respuesta del usuario."""
        respuesta = self.input_var.get().strip()
        if respuesta:
            self.agregar_mensaje(f"👉 Tu respuesta: {respuesta}", "info")
            
            # Detectar si es un código MFA para Sura
            if self._is_mfa_code(respuesta):
                self.agregar_mensaje("📱 Detectado código MFA - enviando a proceso Sura...", "info")
                if self._send_mfa_code_to_sura(respuesta):
                    self.agregar_mensaje("✅ Código MFA enviado correctamente", "success")
                else:
                    self.agregar_mensaje("❌ Error enviando código MFA", "error")
            else:
                # Enviar respuesta normal al proceso
                if self.proceso_subprocess and self.proceso_subprocess.poll() is None:
                    try:
                        self.proceso_subprocess.stdin.write(f"{respuesta}\n")
                        self.proceso_subprocess.stdin.flush()
                        self.agregar_mensaje(f"✅ Respuesta enviada al proceso", "success")
                    except Exception as e:
                        self.agregar_mensaje(f"❌ Error enviando respuesta: {e}", "error")
            
            self.ocultar_input()
    
    def _is_mfa_code(self, respuesta: str) -> bool:
        """Detecta si la respuesta es un código MFA (4-6 dígitos)."""
        return respuesta.isdigit() and 4 <= len(respuesta) <= 6
    
    def _send_mfa_code_to_sura(self, mfa_code: str) -> bool:
        """Envía el código MFA a Sura mediante archivo temporal."""
        try:
            import tempfile
            import os
            
            temp_dir = tempfile.gettempdir()
            mfa_file = os.path.join(temp_dir, "sura_mfa_input.txt")
            
            # Escribir el código MFA al archivo temporal
            with open(mfa_file, 'w') as f:
                f.write(mfa_code)
            
            return True
        except Exception as e:
            self.agregar_mensaje(f"❌ Error escribiendo código MFA: {e}", "error")
            return False
    
    def mostrar_carga(self, mensaje: str = "Procesando..."):
        """Muestra el indicador de carga animado."""
        self.loading_label.config(text=mensaje)
        self.loading_label.grid(row=0, column=0, pady=(0, 5))
        self.loading_icon.grid(row=1, column=0)
        self.iniciar_animacion_carga()
    
    def ocultar_carga(self):
        """Oculta el indicador de carga."""
        self.detener_animacion_carga()
        self.loading_label.grid_remove()
        self.loading_icon.grid_remove()
        self.loading_label.config(text="Listo para ejecutar")
    
    def iniciar_animacion_carga(self):
        """Inicia la animación de carga."""
        if self.loading_animation is None:
            self.animation_frame = 0
            self.animar_carga()
    
    def detener_animacion_carga(self):
        """Detiene la animación de carga."""
        if self.loading_animation:
            self.root.after_cancel(self.loading_animation)
            self.loading_animation = None
            self.loading_icon.config(text="")
    
    def animar_carga(self):
        """Anima el icono de carga."""
        frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.loading_icon.config(text=frames[self.animation_frame])
        self.animation_frame = (self.animation_frame + 1) % len(frames)
        self.loading_animation = self.root.after(100, self.animar_carga)
    
    def ejecutar_automatizacion(self):
        """Inicia la ejecución de la automatización."""
        if self.proceso_activo:
            messagebox.showwarning("Proceso en ejecución", "Ya hay un proceso en ejecución.")
            return
        
        # Confirmar ejecución
        if not messagebox.askyesno(
            "Confirmar ejecución",
            "¿Desea iniciar la automatización para Allianz y Sura en paralelo?"
        ):
            return
        
        # Actualizar configuraciones antes de ejecutar
        try:
            # Actualizar la configuración global
            ClientConfig.update_vehicle_state(self.estado_vehiculo.get())
            ClientConfig.update_fasecolda_search(self.fasecolda_automatico.get())
            
            # Agregar mensaje confirmando la configuración aplicada solo en debug
            if self.modo_debug.get():
                self.agregar_mensaje(f"⚙️ Configuración aplicada - Estado: {self.estado_vehiculo.get()}", "info")
                fasecolda_status = "Activada" if self.fasecolda_automatico.get() else "Desactivada"
                self.agregar_mensaje(f"🔍 Fasecolda: {fasecolda_status}", "info")
                debug_status = "Activado" if self.modo_debug.get() else "Desactivado"
                self.agregar_mensaje(f"🔧 Modo Debug: {debug_status}", "info")
            
        except Exception as e:
            messagebox.showerror("Error de configuración", f"Error actualizando configuración: {e}")
            return
        
        # Deshabilitar botones durante ejecución
        self.ejecutar_btn.config(state=tk.DISABLED, text="⏳ Ejecutando...")
        self.detener_btn.config(state=tk.NORMAL)  # Habilitar botón de detener
        self.actualizar_cliente_btn.config(state=tk.DISABLED)
        self.proceso_activo = True
        
        # Limpiar consola
        self.console_text.config(state=tk.NORMAL)
        self.console_text.delete(1.0, tk.END)
        self.console_text.config(state=tk.DISABLED)
        
        # Mostrar indicador de carga
        self.mostrar_carga("Iniciando automatización...")
        
        # Agregar mensajes iniciales solo en modo debug
        if self.modo_debug.get():
            self.agregar_mensaje("🚀 Iniciando automatización para Allianz y Sura...", "info")
            self.agregar_mensaje(f"⚙️ Estado del vehículo: {self.estado_vehiculo.get()}", "info")
            fasecolda_status = "Activada" if self.fasecolda_automatico.get() else "Desactivada"
            self.agregar_mensaje(f"🔍 Búsqueda automática Fasecolda: {fasecolda_status}", "info")
            ventanas_status = "Visibles" if self.mostrar_ventanas.get() else "Ocultas"
            self.agregar_mensaje(f"👁️ Ventanas del navegador: {ventanas_status}", "info")
            debug_status = "Activado (todos los logs)" if self.modo_debug.get() else "Desactivado (solo mensajes importantes)"
            self.agregar_mensaje(f"🔧 Modo Debug: {debug_status}", "info")
            
            # Mostrar información del vehículo solo en debug
            config = ClientConfig.get_current_config()
            self.agregar_mensaje(f"👤 Cliente: {config['client_name']}", "info")
            self.agregar_mensaje(f"🚗 Vehículo: {config['vehicle_brand']} {config['vehicle_reference']} ({config['vehicle_year']})", "info")
            self.agregar_mensaje(f"🔖 Placa: {config['vehicle_plate']}", "info")
        else:
            # En modo normal, solo mensaje mínimo
            self.agregar_mensaje("🚀 Ejecutando automatización...", "info")
            self.agregar_mensaje("💭 Esperando opciones de Fasecolda...", "info")
        
        # Ejecutar en hilo separado
        self.proceso_thread = threading.Thread(target=self.ejecutar_proceso, daemon=True)
        self.proceso_thread.start()
    
    def detener_automatizacion(self):
        """Detiene la automatización en curso."""
        if not self.proceso_activo:
            messagebox.showinfo("Sin proceso", "No hay automatización en ejecución.")
            return
        
        # Confirmar detención
        if not messagebox.askyesno(
            "Confirmar detención",
            "¿Desea detener la automatización en curso?\n\nEsto terminará todos los procesos de navegadores."
        ):
            return
        
        self.agregar_mensaje("⚠️ Deteniendo automatización...", "warning")
        
        try:
            # Terminar el proceso si está ejecutándose
            if self.proceso_subprocess:
                self.agregar_mensaje("🔄 Terminando procesos de navegadores...", "info")
                
                # Intentar terminación graceful primero
                self.proceso_subprocess.terminate()
                
                # Esperar un poco para terminación graceful
                try:
                    self.proceso_subprocess.wait(timeout=10)
                    self.agregar_mensaje("✅ Procesos terminados correctamente", "success")
                except subprocess.TimeoutExpired:
                    # Si no termina gracefully, forzar terminación
                    self.agregar_mensaje("⚡ Forzando terminación de procesos...", "warning")
                    self.proceso_subprocess.kill()
                    self.proceso_subprocess.wait()
                    self.agregar_mensaje("✅ Procesos terminados forzosamente", "success")
                
                self.proceso_subprocess = None
            
            # Resetear estado de la interfaz
            self.proceso_finalizado_manual()
            
        except Exception as e:
            self.agregar_mensaje(f"❌ Error deteniendo automatización: {e}", "error")
            # Aún así, resetear el estado
            self.proceso_finalizado_manual()
    
    def ejecutar_proceso(self):
        """Ejecuta el proceso de automatización en un hilo separado."""
        try:
            # Obtener el directorio del proyecto
            project_dir = Path(__file__).parent.parent.parent
            
            # Comando a ejecutar
            cmd = [
                sys.executable,
                str(project_dir / "ejecutar_automatizaciones.py"),
                "--companies", "allianz", "sura",
                "--parallel"
            ]
            
            self.message_queue.put(("loading", "Iniciando procesos..."))
            
            # Configurar el entorno para UTF-8 y pasar configuración de la GUI
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            
            # Pasar configuración de la GUI como variables de entorno (prioridad sobre archivo)
            env['GUI_VEHICLE_STATE'] = self.estado_vehiculo.get()
            env['GUI_FASECOLDA_ENABLED'] = str(self.fasecolda_automatico.get())
            env['GUI_SHOW_BROWSER'] = str(self.mostrar_ventanas.get())
            
            # Mensaje de debug para confirmar valores
            self.message_queue.put(("message", ("info", f"🔧 Estado vehículo (GUI): {self.estado_vehiculo.get()}")))
            self.message_queue.put(("message", ("info", f"🔧 Fasecolda (GUI): {self.fasecolda_automatico.get()}")))
            self.message_queue.put(("message", ("info", f"🔧 Mostrar ventanas (GUI): {self.mostrar_ventanas.get()}")))
            
            # Ejecutar el proceso con codificación UTF-8 y entrada habilitada
            self.proceso_subprocess = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.PIPE,  # Habilitar entrada para respuestas
                universal_newlines=True,
                encoding='utf-8',
                errors='replace',  # Reemplazar caracteres no válidos
                cwd=str(project_dir),
                bufsize=1,
                env=env
            )
            
            self.message_queue.put(("loading", "Procesos iniciados..."))
            
            # Leer output en tiempo real
            for line in iter(self.proceso_subprocess.stdout.readline, ''):
                line = line.strip()
                if line:
                    # Limpiar caracteres problemáticos antes de procesar
                    line = self.limpiar_texto_unicode(line)
                    
                    # Mostrar mensajes según el modo
                    if self.modo_debug.get():
                        # Modo debug: mostrar todo
                        self.message_queue.put(("message", ("info", line)))
                    else:
                        # Modo normal: filtrar mensajes importantes
                        if self.es_mensaje_importante(line):
                            self.message_queue.put(("message", ("info", line)))
                    
                    # Detectar solicitudes de input - Patrones mejorados
                    input_patterns = [
                        "Selecciona el código a usar",
                        "👉 Tu respuesta:",
                        "👆 Seleccione una opción",
                        "para cancelar:",
                        "Ingrese el código",
                        "código MFA",
                        "Por favor, ingresa el código MFA que recibiste",
                        "selecciona"
                    ]
                    
                    if any(pattern in line for pattern in input_patterns):
                        # Extraer opciones si están disponibles
                        if "Selecciona el código a usar" in line or "Seleccione una opción" in line:
                            opciones = self.extraer_opciones_fasecolda(line)
                            prompt = f"Selecciona una opción ({opciones}):"
                            self.message_queue.put(("input_request", prompt))
                        elif "MFA" in line or "autenticación" in line or "Tu respuesta:" in line:
                            prompt = "Ingresa tu respuesta:"
                            self.message_queue.put(("input_request", prompt))
                    
                    # Actualizar mensaje de carga basado en el contenido
                    if "Iniciando" in line:
                        self.message_queue.put(("loading", "Iniciando procesos..."))
                    elif "navegación" in line:
                        self.message_queue.put(("loading", "Navegando en sitios web..."))
                    elif "Fasecolda" in line:
                        self.message_queue.put(("loading", "Buscando códigos Fasecolda..."))
                    elif "cotización" in line:
                        self.message_queue.put(("loading", "Generando cotizaciones..."))
                    elif "consolidación" in line:
                        self.message_queue.put(("loading", "Consolidando resultados..."))
            
            # Esperar a que termine el proceso
            return_code = self.proceso_subprocess.wait()
            
            if return_code == 0:
                self.message_queue.put(("loading", "¡Completado exitosamente!"))
                self.message_queue.put(("message", ("success", "✅ ¡Automatización completada exitosamente!")))
            else:
                self.message_queue.put(("loading", "Completado con errores"))
                self.message_queue.put(("message", ("error", "❌ La automatización terminó con errores")))
                
        except Exception as e:
            error_msg = f"❌ Error ejecutando automatización: {str(e)}"
            self.message_queue.put(("message", ("error", error_msg)))
            self.message_queue.put(("loading", "Error en ejecución"))
        
        finally:
            self.message_queue.put(("process_finished", None))
    
    def limpiar_texto_unicode(self, texto: str) -> str:
        """Limpia el texto de caracteres Unicode problemáticos para Windows."""
        # Mapeo de emojis problemáticos a versiones compatibles
        emoji_map = {
            '🔄': '[RELOAD]',
            '🚀': '[START]',
            '✅': '[OK]',
            '❌': '[ERROR]',
            '⚠️': '[WARNING]',
            '🔍': '[SEARCH]',
            '📋': '[LIST]',
            '💰': '[MONEY]',
            '📊': '[CHART]',
            '⏳': '[LOADING]',
            '🎯': '[TARGET]',
            '🔖': '[TAG]',
            '👤': '[USER]',
            '🚗': '[CAR]',
            '⚙️': '[CONFIG]',
            '🏁': '[FINISH]',
            '🎉': '[CELEBRATION]'
        }
        
        # Reemplazar emojis problemáticos
        for emoji, replacement in emoji_map.items():
            texto = texto.replace(emoji, replacement)
        
        # Remover otros caracteres Unicode no imprimibles
        texto = ''.join(char if ord(char) < 65536 else '?' for char in texto)
        
        return texto
    
    def es_mensaje_importante(self, linea: str) -> bool:
        """Determina si una línea contiene información importante para mostrar en modo normal."""
        # En modo normal, SOLO mostrar opciones de Fasecolda, MFA y errores críticos
        palabras_fasecolda_mfa_y_criticas = [
            # Solo opciones de Fasecolda que requieren selección del usuario
            "Selecciona el código a usar",
            "👆 Seleccione una opción", 
            "CF:", "CH:",
            
            # Mensajes MFA que requieren input del usuario
            "código MFA", "Por favor, ingresa el código MFA que recibiste",
            "👉 Tu respuesta:", "Ingresa el código MFA", "autenticación de dos factores",
            
            # Solo errores críticos que requieren atención inmediata
            "❌", "[ERROR]", "Error crítico", "Fallo crítico", "FATAL"
        ]
        
        return any(palabra in linea for palabra in palabras_fasecolda_mfa_y_criticas)
    
    def extraer_opciones_fasecolda(self, linea: str) -> str:
        """Extrae el rango de opciones de una línea de Fasecolda."""
        # Buscar patrones como "(1-3)" o "1, 2, 3"
        import re
        
        # Buscar patrón (1-3)
        match = re.search(r'\((\d+-\d+)\)', linea)
        if match:
            return match.group(1)
        
        # Buscar patrón (1,2,3)
        match = re.search(r'\(([0-9,\s]+)\)', linea)
        if match:
            return match.group(1).strip()
        
        # Buscar números separados por comas
        match = re.search(r'(\d+(?:,\s*\d+)*)', linea)
        if match:
            return match.group(1)
        
        # Si contiene "Selecciona el código", asumir 1-3 por defecto
        if "Selecciona el código" in linea:
            return "1-3"
        
        return "1-3"  # Valor por defecto
    
    def check_message_queue(self):
        """Verifica la cola de mensajes periódicamente."""
        try:
            while True:
                msg_type, data = self.message_queue.get_nowait()
                
                if msg_type == "message":
                    tipo, mensaje = data
                    self.agregar_mensaje(mensaje, tipo)
                
                elif msg_type == "loading":
                    self.mostrar_carga(data)
                
                elif msg_type == "input_request":
                    self.mostrar_input(data)
                
                elif msg_type == "user_response":
                    # Aquí se manejaría el envío de la respuesta al proceso
                    # Por ahora solo registramos que se recibió
                    pass
                
                elif msg_type == "process_finished":
                    self.proceso_finalizado()
                
        except queue.Empty:
            pass
        
        # Programar la siguiente verificación
        self.root.after(100, self.check_message_queue)
    
    def proceso_finalizado(self):
        """Maneja la finalización natural del proceso."""
        self.proceso_activo = False
        self.ejecutar_btn.config(state=tk.NORMAL, text="🚀 Ejecutar Automatización")
        self.detener_btn.config(state=tk.DISABLED)  # Deshabilitar botón de detener
        self.actualizar_cliente_btn.config(state=tk.NORMAL)  # Rehabilitar botón de actualizar
        
        # Limpiar referencia al proceso
        if self.proceso_subprocess:
            try:
                self.proceso_subprocess.stdin.close()
            except:
                pass
            self.proceso_subprocess = None
        
        # Ocultar indicador de carga después de 3 segundos
        self.root.after(3000, self.ocultar_carga)
        
        # Mostrar mensaje final solo en debug
        if self.modo_debug.get():
            self.agregar_mensaje("🏁 Proceso finalizado.", "info")
        else:
            self.agregar_mensaje("✅ Automatización completada.", "info")
    
    def proceso_finalizado_manual(self):
        """Maneja la finalización manual del proceso (cuando se detiene manualmente)."""
        self.proceso_activo = False
        self.ejecutar_btn.config(state=tk.NORMAL, text="🚀 Ejecutar Automatización")
        self.detener_btn.config(state=tk.DISABLED)  # Deshabilitar botón de detener
        self.actualizar_cliente_btn.config(state=tk.NORMAL)  # Rehabilitar botón de actualizar
        
        # Ocultar indicador de carga inmediatamente
        self.ocultar_carga()
        
        self.agregar_mensaje("⏹️ Automatización detenida manualmente.", "warning")
        self.agregar_mensaje("✅ Interfaz lista para nueva ejecución.", "info")
    
    def on_closing(self):
        """Maneja el cierre de la aplicación."""
        if self.proceso_activo:
            if messagebox.askyesno(
                "Proceso en ejecución",
                "Hay una automatización en ejecución. ¿Desea detenerla y cerrar la aplicación?"
            ):
                # Detener el proceso primero
                try:
                    if self.proceso_subprocess:
                        self.proceso_subprocess.terminate()
                        try:
                            self.proceso_subprocess.wait(timeout=5)
                        except subprocess.TimeoutExpired:
                            self.proceso_subprocess.kill()
                            self.proceso_subprocess.wait()
                except Exception:
                    pass
            else:
                return  # No cerrar si el usuario cancela
        
        self.root.destroy()
    
    def run(self):
        """Inicia la interfaz gráfica."""
        self.root.mainloop()


def main():
    """Función principal para la GUI."""
    try:
        app = AutomationGUI()
        app.run()
    except Exception as e:
        print(f"Error iniciando la GUI: {e}")
        messagebox.showerror("Error", f"Error iniciando la aplicación: {e}")


if __name__ == "__main__":
    main()
