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
from config.client_history_manager import ClientHistoryManager
from interfaces.client_edit_window import ClientEditWindow


class AutomationGUI:
    """Interfaz gráfica principal para las automatizaciones."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Sistema de Automatización de Cotizaciones")
        
        # Configurar tamaño y centrar ventana
        window_width = 600
        window_height = 750  # Aumentado para acomodar consola más larga
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Calcular posición para centrar
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.root.resizable(True, True)
        
        # Variables de configuración
        self.fasecolda_automatico = tk.BooleanVar(value=ClientConfig.ENABLE_FASECOLDA_SEARCH)
        self.mostrar_ventanas = tk.BooleanVar(value=False)
        self.modo_debug = tk.BooleanVar(value=False)
        
        # Variables de control
        self.proceso_activo = False
        self.proceso_thread = None
        self.loading_animation = None
        self.animation_frame = 0
        self.proceso_subprocess = None  # Referencia al proceso subprocess
        
        # Lista para rastrear procesos específicos de la aplicación
        self.app_processes = []  # PIDs de procesos creados por la app
        
        # Cola para comunicación entre hilos
        self.message_queue = queue.Queue()
        self.response_queue = queue.Queue()  # Cola para respuestas del usuario
        
        # Crear la interfaz
        self.setup_ui()
        
        # Configurar manejo de cierre
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Configurar manejo de señales del sistema
        self._setup_signal_handlers()
        
        # Iniciar el monitoreo de mensajes
        self.check_message_queue()
        
        # Cargar automáticamente el último cliente editado del historial
        self.cargar_ultimo_cliente_editado()
    
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
        
        # Botones de cliente
        buttons_frame = ttk.Frame(info_frame)
        buttons_frame.grid(row=0, column=2, rowspan=3, padx=(20, 0), sticky=tk.N)
        
        self.editar_cliente_btn = ttk.Button(
            buttons_frame,
            text="✏️ Editar Cliente",
            command=self.abrir_editor_cliente,
            width=18
        )
        self.editar_cliente_btn.pack(pady=(0, 5))
        
        self.actualizar_cliente_btn = ttk.Button(
            buttons_frame,
            text="🔄 Actualizar",
            command=self.actualizar_informacion_cliente,
            width=18
        )
        self.actualizar_cliente_btn.pack()
        
        # Crear campos de información del cliente
        self.crear_campos_cliente(info_frame)
        
        # Frame de configuración
        config_frame = ttk.LabelFrame(main_frame, text="Configuración", padding="10")
        config_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        config_frame.columnconfigure(1, weight=1)
        
        # Opción: Búsqueda automática de Fasecolda
        fasecolda_check = ttk.Checkbutton(
            config_frame,
            text="Activar búsqueda automática de códigos Fasecolda",
            variable=self.fasecolda_automatico
        )
        fasecolda_check.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # Opción: Mostrar ventanas del navegador
        ventanas_check = ttk.Checkbutton(
            config_frame,
            text="Mostrar ventanas del navegador (por defecto están ocultas)",
            variable=self.mostrar_ventanas
        )
        ventanas_check.grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # Opción: Modo debug
        debug_check = ttk.Checkbutton(
            config_frame,
            text="🔧 Modo Debug (mostrar todos los logs en consola)",
            variable=self.modo_debug,
            command=self.toggle_debug_mode
        )
        debug_check.grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=5)
        
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
        
        # Área de texto con scroll (más larga)
        self.console_text = scrolledtext.ScrolledText(
            self.console_frame,
            height=18,  # Aumentado de 15 a 18
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
            # Obtener configuración actual directamente
            config = ClientConfig.get_current_config()
        except Exception:
            # Fallback si hay error
            config = {
                'client_name': f"{ClientConfig.CLIENT_FIRST_NAME} {ClientConfig.CLIENT_FIRST_LASTNAME}",
                'vehicle_brand': ClientConfig.VEHICLE_BRAND,
                'vehicle_reference': ClientConfig.VEHICLE_REFERENCE,
                'vehicle_year': ClientConfig.VEHICLE_MODEL_YEAR,
                'vehicle_plate': ClientConfig.VEHICLE_PLATE
            }
        
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
    
    def _setup_signal_handlers(self):
        """Configura los manejadores de señales del sistema."""
        try:
            import signal
            
            def signal_handler(signum, frame):
                """Maneja las señales del sistema para cerrar correctamente."""
                print(f"Señal {signum} recibida, cerrando aplicación...")
                self.on_closing()
            
            # Configurar manejadores para Windows
            if sys.platform.startswith('win'):
                try:
                    signal.signal(signal.SIGINT, signal_handler)
                    signal.signal(signal.SIGTERM, signal_handler)
                except ValueError:
                    # Algunas señales pueden no estar disponibles en Windows
                    pass
            else:
                # Configurar manejadores para Unix/Linux
                signal.signal(signal.SIGINT, signal_handler)
                signal.signal(signal.SIGTERM, signal_handler)
                
        except Exception as e:
            print(f"Error configurando manejadores de señales: {e}")
    
    def actualizar_informacion_cliente(self):
        """Actualiza la información del cliente desde la configuración."""
        if self.proceso_activo:
            messagebox.showwarning("Proceso en ejecución", "No se puede actualizar la información mientras hay un proceso ejecutándose.")
            return
            
        try:
            # Obtener la configuración actualizada directamente (sin recargar módulo)
            config = ClientConfig.get_current_config()
            
            # Actualizar las etiquetas
            self.cliente_label.config(text=config['client_name'])
            vehicle_info = f"{config['vehicle_brand']} {config['vehicle_reference']} ({config['vehicle_year']})"
            self.vehiculo_label.config(text=vehicle_info)
            self.placa_label.config(text=config['vehicle_plate'])
            
            # Actualizar variables de configuración
            self.fasecolda_automatico.set(ClientConfig.ENABLE_FASECOLDA_SEARCH)
            
            self.agregar_mensaje("✅ Información del cliente actualizada correctamente", "success")
            self.agregar_mensaje(f"👤 Cliente: {config['client_name']}", "info")
            self.agregar_mensaje(f"🚗 Vehículo: {config['vehicle_brand']} {config['vehicle_reference']} ({config['vehicle_year']})", "info")
            self.agregar_mensaje(f"🔖 Placa: {config['vehicle_plate']}", "info")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error actualizando información del cliente: {e}")
            self.agregar_mensaje(f"❌ Error actualizando información: {e}", "error")
    
    def abrir_editor_cliente(self):
        """Abre la ventana de edición de cliente."""
        if self.proceso_activo:
            messagebox.showwarning("Proceso Activo", "No se puede editar la información del cliente mientras el proceso está ejecutándose.")
            return
        
        try:
            # Callback para cuando se guarden los datos
            def on_client_updated(client_data):
                # Forzar actualización de ClientConfig con los nuevos datos
                ClientConfig.load_client_data(client_data)
                ClientConfig.update_vehicle_state(client_data.get('vehicle_state', 'Nuevo'))
                
                # Actualizar la información mostrada
                self.actualizar_informacion_cliente()
                self.agregar_mensaje("✅ Datos del cliente actualizados desde el editor", "success")
            
            # Abrir ventana de edición
            editor = ClientEditWindow(parent_window=self.root, callback=on_client_updated)
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir el editor de cliente: {e}")
            self.agregar_mensaje(f"❌ Error abriendo editor: {e}", "error")
    
    def cargar_ultimo_cliente_editado(self):
        """Carga automáticamente el último cliente editado del historial en la interfaz principal."""
        try:
            from config.client_history_manager import ClientHistoryManager
            history_manager = ClientHistoryManager()
            
            # Obtener el historial
            history = history_manager.load_history()
            
            if history and len(history) > 0:
                # Obtener el último cliente editado (el primero en la lista ya que están ordenados por fecha descendente)
                ultimo_cliente = history[0]
                client_data = ultimo_cliente.get('data', {})
                
                if client_data:
                    # Cargar los datos en ClientConfig
                    ClientConfig.load_client_data(client_data)
                    ClientConfig.update_vehicle_state(client_data.get('vehicle_state', 'Nuevo'))
                    
                    # Actualizar la información mostrada en la interfaz
                    self.actualizar_informacion_cliente()
                    
                    # Mostrar mensaje informativo
                    nombre_cliente = ultimo_cliente.get('name', 'Sin nombre')
                    self.agregar_mensaje(f"📋 Cliente cargado automáticamente: {nombre_cliente}", "info")
                else:
                    self.agregar_mensaje("⚠️ No se encontraron datos válidos en el último cliente del historial", "warning")
            else:
                self.agregar_mensaje("📂 Historial de clientes vacío - usando configuración por defecto", "info")
                
        except Exception as e:
            print(f"Error cargando último cliente: {e}")
            self.agregar_mensaje("⚠️ No se pudo cargar el último cliente del historial", "warning")
    
    def guardar_cliente_automatico(self):
        """Guarda automáticamente el cliente actual en el historial antes de ejecutar."""
        try:
            # Inicializar el gestor de historial
            history_manager = ClientHistoryManager()
            
            # Obtener los datos actuales del cliente
            client_data = {
                'client_document_number': ClientConfig.CLIENT_DOCUMENT_NUMBER,
                'client_first_name': ClientConfig.CLIENT_FIRST_NAME,
                'client_second_name': ClientConfig.CLIENT_SECOND_NAME,
                'client_first_lastname': ClientConfig.CLIENT_FIRST_LASTNAME,
                'client_second_lastname': ClientConfig.CLIENT_SECOND_LASTNAME,
                'client_birth_date': ClientConfig.CLIENT_BIRTH_DATE,
                'client_gender': ClientConfig.CLIENT_GENDER,
                'client_city': ClientConfig.CLIENT_CITY,
                'client_department': ClientConfig.CLIENT_DEPARTMENT,
                'vehicle_plate': ClientConfig.VEHICLE_PLATE,
                'vehicle_model_year': ClientConfig.VEHICLE_MODEL_YEAR,
                'vehicle_brand': ClientConfig.VEHICLE_BRAND,
                'vehicle_reference': ClientConfig.VEHICLE_REFERENCE,
                'vehicle_full_reference': ClientConfig.VEHICLE_FULL_REFERENCE,
                'vehicle_state': ClientConfig.VEHICLE_STATE,
                'manual_cf_code': ClientConfig.MANUAL_CF_CODE,
                'manual_ch_code': ClientConfig.MANUAL_CH_CODE,
                'policy_number': ClientConfig.POLICY_NUMBER,
                'policy_number_allianz': ClientConfig.POLICY_NUMBER_ALLIANZ
            }
            
            # Verificar si ya existe un cliente similar reciente (evitar duplicados)
            history = history_manager.load_history()
            client_name = f"{ClientConfig.CLIENT_FIRST_NAME} {ClientConfig.CLIENT_FIRST_LASTNAME}".strip()
            document = ClientConfig.CLIENT_DOCUMENT_NUMBER
            plate = ClientConfig.VEHICLE_PLATE
            
            # Buscar cliente similar en las últimas 3 entradas
            duplicate_found = False
            for recent_client in history[:3]:
                recent_data = recent_client.get('data', {})
                if (recent_data.get('client_document_number') == document and 
                    recent_data.get('vehicle_plate') == plate):
                    duplicate_found = True
                    break
            
            if duplicate_found:
                self.agregar_mensaje(f"💡 Cliente {client_name} ya existe en historial reciente", "info")
                return
            
            # Crear nombre para el historial con timestamp
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            history_name = f"{client_name} - Ejecución {timestamp}"
            
            # Validar los datos antes de guardar
            errors = history_manager.validate_client_data(client_data)
            if not errors:
                # Guardar en el historial
                if history_manager.save_client(client_data, history_name):
                    self.agregar_mensaje(f"💾 Cliente guardado automáticamente: {client_name}", "success")
                else:
                    self.agregar_mensaje("⚠️ No se pudo guardar el cliente en el historial", "warning")
            else:
                # Si hay errores de validación, aún intentar guardar pero con advertencia
                if history_manager.save_client(client_data, f"{history_name} (Con errores)"):
                    self.agregar_mensaje(f"💾 Cliente guardado con advertencias: {client_name}", "warning")
                    if self.modo_debug.get():
                        for field, error in errors.items():
                            self.agregar_mensaje(f"   ⚠️ {field}: {error}", "warning")
                else:
                    self.agregar_mensaje("❌ Error guardando cliente en historial", "error")
                    
        except Exception as e:
            self.agregar_mensaje(f"⚠️ Error guardando cliente automáticamente: {e}", "warning")
            # No bloquear la ejecución por este error
    
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
            ClientConfig.update_fasecolda_search(self.fasecolda_automatico.get())
            
            # GUARDAR AUTOMÁTICAMENTE EL CLIENTE ACTUAL EN EL HISTORIAL
            self.guardar_cliente_automatico()
            
            # Agregar mensaje confirmando la configuración aplicada solo en debug
            if self.modo_debug.get():
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
        self.editar_cliente_btn.config(state=tk.DISABLED)
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
        
        # Usar la función mejorada de detener forzado
        self._force_stop_automation()
        
        # Resetear estado de la interfaz
        self.proceso_finalizado_manual()
    
    def ejecutar_proceso(self):
        """Ejecuta el proceso de automatización en un hilo separado."""
        try:
            # Obtener el directorio del proyecto
            project_dir = Path(__file__).parent.parent.parent
            
            # Comando a ejecutar
            cmd = [
                sys.executable,
                str(project_dir / "scripts" / "ejecutar_automatizaciones.py"),
                "--companies", "allianz", "sura",
                "--parallel"
            ]
            
            self.message_queue.put(("loading", "Iniciando procesos..."))
            
            # Configurar el entorno para UTF-8 y pasar configuración de la GUI
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            
            # Pasar configuración de la GUI como variables de entorno (prioridad sobre archivo)
            env['GUI_FASECOLDA_ENABLED'] = str(self.fasecolda_automatico.get())
            env['GUI_SHOW_BROWSER'] = str(self.mostrar_ventanas.get())
            
            # CRÍTICO: Pasar TODOS los datos del cliente actual como variables de entorno
            current_client_data = ClientConfig._get_current_data()
            if current_client_data:
                env['GUI_CLIENT_DOCUMENT_NUMBER'] = current_client_data.get('client_document_number', '')
                env['GUI_CLIENT_FIRST_NAME'] = current_client_data.get('client_first_name', '')
                env['GUI_CLIENT_SECOND_NAME'] = current_client_data.get('client_second_name', '')
                env['GUI_CLIENT_FIRST_LASTNAME'] = current_client_data.get('client_first_lastname', '')
                env['GUI_CLIENT_SECOND_LASTNAME'] = current_client_data.get('client_second_lastname', '')
                env['GUI_CLIENT_BIRTH_DATE'] = current_client_data.get('client_birth_date', '')
                env['GUI_CLIENT_GENDER'] = current_client_data.get('client_gender', '')
                env['GUI_CLIENT_CITY'] = current_client_data.get('client_city', '')
                env['GUI_CLIENT_DEPARTMENT'] = current_client_data.get('client_department', '')
                env['GUI_VEHICLE_PLATE'] = current_client_data.get('vehicle_plate', '')
                env['GUI_VEHICLE_MODEL_YEAR'] = current_client_data.get('vehicle_model_year', '')
                env['GUI_VEHICLE_BRAND'] = current_client_data.get('vehicle_brand', '')
                env['GUI_VEHICLE_REFERENCE'] = current_client_data.get('vehicle_reference', '')
                env['GUI_VEHICLE_FULL_REFERENCE'] = current_client_data.get('vehicle_full_reference', '')
                env['GUI_VEHICLE_STATE'] = current_client_data.get('vehicle_state', '')
                env['GUI_MANUAL_CF_CODE'] = current_client_data.get('manual_cf_code', '')
                env['GUI_MANUAL_CH_CODE'] = current_client_data.get('manual_ch_code', '')
                env['GUI_POLICY_NUMBER'] = current_client_data.get('policy_number', '')
                env['GUI_POLICY_NUMBER_ALLIANZ'] = current_client_data.get('policy_number_allianz', '')
            else:
                self.message_queue.put(("message", ("warning", "⚠️ WARNING: No hay datos de cliente actuales, usando valores por defecto")))
            
            # Mensaje de debug para confirmar valores
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
            
            # Iniciar rastreo de procesos de navegador después de un breve delay
            threading.Timer(3.0, self._start_browser_tracking).start()
            
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
        
        # Filtrar errores esperados al detener la automatización
        errores_esperados_al_detener = [
            "Target page, context or browser has been closed",
            "Page.fill: Target page, context or browser has been closed",
            "Page.goto: Target page, context or browser has been closed",
            "BrowserContext.close: Target page, context or browser has been closed",
            "Error cerrando navegador",
            "Error en el flujo de login",
            "Error llenando usuario",
            "Error navegando a login"
        ]
        
        # Si contiene errores esperados de cierre, no mostrar en modo normal
        if any(error in linea for error in errores_esperados_al_detener):
            return False
        
        # En modo normal, SOLO mostrar opciones de Fasecolda, MFA y errores críticos
        palabras_fasecolda_mfa_y_criticas = [
            # Nuevos mensajes de Fasecolda limpios
            "🔍 SELECCIÓN DE CÓDIGO FASECOLDA",
            "Opción ", "Vehículo:", "Score:", 
            ">> Seleccionado:", "Valor:",
            
            # Opciones tradicionales de Fasecolda que requieren selección del usuario
            "Selecciona el código a usar",
            "👆 Seleccione una opción", 
            "CF:", "CH:",
            
            # Mensajes MFA que requieren input del usuario
            "código MFA", "Por favor, ingresa el código MFA que recibiste",
            "👉 Tu respuesta:", "Ingresa el código MFA", "autenticación de dos factores",
            
            # Solo errores críticos que requieren atención inmediata (no los de cierre)
            "Error crítico", "Fallo crítico", "FATAL", "Error de configuración"
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
        self.editar_cliente_btn.config(state=tk.NORMAL)  # Rehabilitar botón de editar
        
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
        self.editar_cliente_btn.config(state=tk.NORMAL)  # Rehabilitar botón de editar
        
        # Limpiar referencia al proceso y cerrar stdin si existe
        if self.proceso_subprocess:
            try:
                if self.proceso_subprocess.stdin:
                    self.proceso_subprocess.stdin.close()
            except:
                pass
            self.proceso_subprocess = None
        
        # Ocultar input si está visible
        self.ocultar_input()
        
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
                # Detener el proceso PRIMERO y de forma forzada
                self._force_stop_automation()
            else:
                return  # No cerrar si el usuario cancela
        
        # Cerrar todos los navegadores Chrome que puedan estar abiertos
        self._close_all_browsers()
        
        # Crear archivo de señal para indicar que la aplicación se está cerrando
        self._create_exit_signal()
        
        # Destruir la ventana
        self.root.destroy()
        
        # Asegurar que el proceso Python termine completamente
        import sys
        sys.exit(0)
    
    def _force_stop_automation(self):
        """Detiene forzadamente la automatización y todos sus procesos."""
        try:
            # Marcar como no activo inmediatamente
            self.proceso_activo = False
            
            # Cerrar navegadores PRIMERO
            self.agregar_mensaje("🔒 Cerrando navegadores...", "info")
            self._close_all_browsers()
            
            # Terminar el subprocess principal si existe
            if self.proceso_subprocess:
                try:
                    self.agregar_mensaje("🔄 Terminando proceso principal...", "info")
                    
                    # Cerrar stdin para evitar errores de EOF
                    try:
                        if self.proceso_subprocess.stdin:
                            self.proceso_subprocess.stdin.close()
                    except:
                        pass
                    
                    # Intentar terminación suave primero
                    self.proceso_subprocess.terminate()
                    try:
                        self.proceso_subprocess.wait(timeout=3)
                        self.agregar_mensaje("✅ Proceso principal terminado correctamente", "success")
                    except subprocess.TimeoutExpired:
                        # Si no responde, forzar terminación
                        self.proceso_subprocess.kill()
                        self.proceso_subprocess.wait()
                        self.agregar_mensaje("⚡ Proceso principal terminado forzosamente", "warning")
                except Exception as e:
                    self.agregar_mensaje(f"⚠️ Error terminando proceso: {e}", "warning")
                finally:
                    self.proceso_subprocess = None
            
            # Detener el hilo si existe
            if self.proceso_thread and self.proceso_thread.is_alive():
                # El hilo se detendrá automáticamente cuando termine el subprocess
                pass
            
            # Hacer una segunda pasada para asegurar que todos los navegadores estén cerrados
            self.agregar_mensaje("🔒 Verificación final de navegadores...", "info")
            self._close_all_browsers()
            
            # Ocultar indicador de carga
            self.ocultar_carga()
            
            self.agregar_mensaje("⏹️ Automatización detenida completamente", "success")
            
        except Exception as e:
            self.agregar_mensaje(f"❌ Error deteniendo automatización: {e}", "error")
    
    def _close_all_browsers(self):
        """Cierra solo los procesos de navegador creados por la aplicación."""
        try:
            import subprocess
            import platform
            import time
            
            closed_processes = False
            
            # SIEMPRE intentar cerrar chromedriver primero (es específico de automatización)
            if platform.system() == "Windows":
                try:
                    result = subprocess.run(
                        ["taskkill", "/F", "/IM", "chromedriver.exe"], 
                        capture_output=True, 
                        check=False,
                        timeout=10
                    )
                    if result.returncode == 0:
                        closed_processes = True
                        self.agregar_mensaje("🔒 ChromeDriver cerrado", "info")
                except Exception:
                    pass
            
            # Si tenemos PIDs específicos, cerrarlos
            if self.app_processes and self.app_processes != ["TRACKING_ACTIVE"]:
                for pid in self.app_processes[:]:  # Copia la lista
                    if pid == "TRACKING_ACTIVE":
                        continue
                        
                    try:
                        if platform.system() == "Windows":
                            result = subprocess.run(
                                ["taskkill", "/F", "/PID", str(pid)], 
                                capture_output=True, 
                                check=False,
                                timeout=5
                            )
                        else:
                            result = subprocess.run(
                                ["kill", "-9", str(pid)], 
                                capture_output=True, 
                                check=False,
                                timeout=5
                            )
                        
                        if result.returncode == 0:
                            closed_processes = True
                            self.agregar_mensaje(f"🔒 Cerrado proceso ID: {pid}", "info")
                        
                        self.app_processes.remove(pid)
                        
                    except Exception as e:
                        if pid in self.app_processes:
                            self.app_processes.remove(pid)
            
            # Método adicional: cerrar Chrome con ventanas específicas de automatización
            if platform.system() == "Windows":
                automation_patterns = [
                    "WINDOWTITLE eq *about:blank*",
                    "WINDOWTITLE eq *data:*",
                    "WINDOWTITLE eq *chrome-extension:*"
                ]
                
                for pattern in automation_patterns:
                    try:
                        result = subprocess.run(
                            ["taskkill", "/F", "/FI", pattern], 
                            capture_output=True, 
                            check=False,
                            timeout=5
                        )
                        if result.returncode == 0:
                            closed_processes = True
                    except Exception:
                        pass
            
            # Limpiar la lista de procesos
            self.app_processes.clear()
            
            if closed_processes:
                time.sleep(1)
                self.agregar_mensaje("✅ Navegadores de automatización cerrados", "success")
            else:
                self.agregar_mensaje("ℹ️ No se encontraron procesos de automatización", "info")
                    
        except Exception as e:
            self.agregar_mensaje(f"⚠️ Error cerrando navegadores: {e}", "warning")
    
    def _conservative_browser_cleanup(self):
        """Método conservador para limpiar navegadores sin afectar Chrome personal."""
        try:
            import subprocess
            import platform
            
            if platform.system() == "Windows":
                # Solo cerrar chromedriver, que es específico de automatización
                try:
                    result = subprocess.run(
                        ["taskkill", "/F", "/IM", "chromedriver.exe"], 
                        capture_output=True, 
                        check=False,
                        timeout=10
                    )
                    if result.returncode == 0:
                        self.agregar_mensaje("🔒 ChromeDriver cerrado", "info")
                except Exception:
                    pass
                
                # Intentar cerrar solo Chrome con títulos específicos de automatización
                try:
                    result = subprocess.run(
                        ["taskkill", "/F", "/FI", "WINDOWTITLE eq *about:blank*"], 
                        capture_output=True, 
                        check=False,
                        timeout=10
                    )
                    if result.returncode == 0:
                        self.agregar_mensaje("🔒 Ventanas de automatización cerradas", "info")
                except Exception:
                    pass
            
            self.agregar_mensaje("✅ Limpieza conservadora completada", "success")
            self.agregar_mensaje("🛡️ Tu Chrome personal no fue afectado", "info")
                
        except Exception as e:
            self.agregar_mensaje(f"⚠️ Error en limpieza conservadora: {e}", "warning")
    
    def _create_exit_signal(self):
        """Crea un archivo de señal para indicar que la aplicación se está cerrando."""
        try:
            signal_file = Path("temp_exit_signal.txt")
            with open(signal_file, 'w', encoding='utf-8') as f:
                f.write("EXIT_REQUESTED")
            self.agregar_mensaje("🔄 Señal de cierre enviada", "info")
        except Exception as e:
            print(f"Error creando señal de salida: {e}")
    
    def _start_browser_tracking(self):
        """Inicia el rastreo de procesos de navegador creados por la aplicación."""
        try:
            import psutil
            import platform
            
            # Obtener procesos actuales de Chrome/Chromium
            current_processes = []
            
            if platform.system() == "Windows":
                process_names = ["chrome.exe", "chromedriver.exe"]
            else:
                process_names = ["chrome", "chromium", "chromedriver"]
            
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    if proc.info['name'].lower() in [name.lower() for name in process_names]:
                        # Verificar si es un proceso hijo de nuestra aplicación
                        if self._is_child_process(proc.info['pid']):
                            current_processes.append(proc.info['pid'])
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Agregar los PIDs encontrados a nuestra lista de rastreo
            if current_processes:
                self.app_processes.extend(current_processes)
                self.agregar_mensaje(f"🎯 Rastreando {len(current_processes)} procesos de navegador", "info")
            
        except ImportError:
            # Si psutil no está disponible, usar método alternativo más simple
            self._simple_browser_tracking()
        except Exception as e:
            self.agregar_mensaje(f"⚠️ Error iniciando rastreo de navegadores: {e}", "warning")
    
    def _is_child_process(self, pid):
        """Verifica si un proceso es hijo del proceso de automatización."""
        try:
            import psutil
            
            if not self.proceso_subprocess:
                return False
                
            parent_pid = self.proceso_subprocess.pid
            proc = psutil.Process(pid)
            
            # Verificar si es hijo directo o indirecto
            while proc.parent():
                if proc.parent().pid == parent_pid:
                    return True
                proc = proc.parent()
                
        except Exception:
            pass
        return False
    
    def _simple_browser_tracking(self):
        """Método alternativo simple para rastrear navegadores sin psutil."""
        try:
            import subprocess
            import platform
            import time
            
            # Esperar un poco más para que los navegadores se inicien
            time.sleep(2)
            
            if platform.system() == "Windows":
                # Método más simple: solo rastrear Chrome que se abra después de iniciar la app
                # En lugar de intentar identificar procesos específicos, 
                # simplemente evitamos cerrar TODOS los Chrome
                self.agregar_mensaje("🎯 Rastreo simplificado activado", "info")
                self.agregar_mensaje("ℹ️ Solo se cerrarán navegadores relacionados con la app", "info")
                
                # Marcar que el rastreo está activo pero sin PIDs específicos
                # Esto hará que _close_all_browsers use un método más conservador
                self.app_processes = ["TRACKING_ACTIVE"]
                
        except Exception as e:
            self.agregar_mensaje(f"⚠️ Error en rastreo simple: {e}", "warning")
    
    def run(self):
        """Inicia la interfaz gráfica."""
        self.root.mainloop()


def main():
    """Función principal para la GUI."""
    try:
        app = AutomationGUI()
        app.run()
        # Si llegamos aquí, la aplicación se cerró normalmente
        return 0
    except KeyboardInterrupt:
        print("🔄 Aplicación interrumpida por el usuario")
        return 0
    except Exception as e:
        print(f"Error iniciando la GUI: {e}")
        messagebox.showerror("Error", f"Error iniciando la aplicación: {e}")
        return 1
    finally:
        # Asegurar que se crea la señal de salida
        try:
            signal_file = Path("temp_exit_signal.txt")
            with open(signal_file, 'w', encoding='utf-8') as f:
                f.write("EXIT_REQUESTED")
        except Exception:
            pass
        print("🔄 Aplicación finalizada")


if __name__ == "__main__":
    import sys
    exit_code = main()
    sys.exit(exit_code)
