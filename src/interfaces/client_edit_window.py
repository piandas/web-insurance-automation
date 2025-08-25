"""
Ventana de edición de datos del cliente con historial.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.ttk import Combobox
import json
from datetime import datetime, date
from typing import Dict, Any, Optional
import re
from pathlib import Path

# Importar el gestor de historial
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from config.client_history_manager import ClientHistoryManager
from config.client_config import ClientConfig


class ClientEditWindow:
    """Ventana para editar datos del cliente con historial."""
    
    # Lista completa de departamentos de Colombia
    DEPARTAMENTOS = [
        "AMAZONAS", "ANTIOQUIA", "ARAUCA", "ATLANTICO", "BOGOTA D.C.", 
        "BOLIVAR", "BOYACA", "CALDAS", "CAQUETA", "CASANARE", "CAUCA", 
        "CESAR", "CHOCO", "CORDOBA", "CUNDINAMARCA", "GUAINIA", "GUAVIARE", 
        "HUILA", "LA GUAJIRA", "MAGDALENA", "META", "NARIÑO", "NORTE DE SANTANDER", 
        "PUTUMAYO", "QUINDIO", "RISARALDA", "SAN ANDRES, PROVIDENCIA Y STA CATALINA", 
        "SANTANDER", "SUCRE", "TOLIMA", "VALLE DEL CAUCA", "VAUPES", "VICHADA"
    ]
    
    def __init__(self, parent_window=None, callback=None):
        """
        Inicializa la ventana de edición.
        
        Args:
            parent_window: Ventana padre
            callback: Función a llamar cuando se guarden los datos
        """
        self.parent_window = parent_window
        self.callback = callback
        self.history_manager = ClientHistoryManager()
        
        # Diccionarios para almacenar labels de error
        self.error_labels = {}
        
        # Crear ventana
        self.window = tk.Toplevel() if parent_window else tk.Tk()
        self.window.title("Editor de Datos del Cliente")
        self.window.geometry("850x1000")  # Aumentar tamaño para mejor visibilidad sin scroll
        self.window.resizable(True, True)
        
        # Configurar ventana para mantenerse al frente cuando sea necesario
        if parent_window:
            self.window.transient(parent_window)
            self.window.grab_set()
        
        # Centrar ventana
        self.center_window()
        
        # Variables para los campos
        self.setup_variables()
        
        # Crear la interfaz
        self.setup_ui()
        
        # Dejar campos vacíos por defecto (no cargar valores predeterminados)
        self.clear_all_fields()
        
        # Configurar cierre
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def center_window(self):
        """Centra la ventana en la pantalla."""
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f"+{x}+{y}")
    
    def setup_variables(self):
        """Configura las variables de tkinter para los campos."""
        # Variables del cliente
        self.client_document_number = tk.StringVar()
        self.client_first_name = tk.StringVar()
        self.client_second_name = tk.StringVar()
        self.client_first_lastname = tk.StringVar()
        self.client_second_lastname = tk.StringVar()
        self.client_birth_date = tk.StringVar()
        self.client_gender = tk.StringVar()
        self.client_city = tk.StringVar()
        self.client_department = tk.StringVar()
        
        # Variables del vehículo
        self.vehicle_plate = tk.StringVar()
        self.vehicle_model_year = tk.StringVar()
        self.vehicle_brand = tk.StringVar()
        self.vehicle_reference = tk.StringVar()
        self.vehicle_full_reference = tk.StringVar()
        self.vehicle_state = tk.StringVar(value="Nuevo")
        # Eliminamos vehicle_insured_value_received ya que no es necesario
        
        # Variables de códigos Fasecolda
        self.manual_cf_code = tk.StringVar()
        self.manual_ch_code = tk.StringVar()
        # Búsqueda comprehensiva siempre habilitada (sin interfaz visual)
        
        # Variables de pólizas
        self.policy_number = tk.StringVar()
        self.policy_number_allianz = tk.StringVar()
        
        # Variable para historial
        self.selected_history_item = tk.StringVar()
        
        # Variable para rastrear el cliente actualmente cargado desde historial
        self.current_client_id = None
    
    def validate_field(self, event, field_type):
        """
        Valida un campo basado en el evento y muestra mensaje de error si es necesario.
        
        Args:
            event: Evento del widget
            field_type: Tipo de validación ("text", "placa", "documento", "year", "numeric", "referencia")
        """
        widget = event.widget
        value = widget.get()
        error_msg = ""
        
        # Mapear widget a field_name basado en las variables de texto asociadas
        field_name = "unknown"
        widget_var = None
        
        try:
            widget_var = widget.cget('textvariable')
        except:
            pass
        
        # Mapeo de variables a nombres de campos para mensajes de error
        var_mapping = {
            str(self.client_first_name): 'first_name',
            str(self.client_second_name): 'second_name', 
            str(self.client_first_lastname): 'first_lastname',
            str(self.client_second_lastname): 'second_lastname',
            str(self.client_city): 'city',
            str(self.client_document_number): 'document',
            str(self.vehicle_plate): 'placa',
            str(self.vehicle_model_year): 'year',
            str(self.manual_cf_code): 'cf_code',
            str(self.manual_ch_code): 'ch_code',
            str(self.policy_number): 'poliza_sura',
            str(self.policy_number_allianz): 'poliza_allianz'
        }
        
        if widget_var and widget_var in var_mapping:
            field_name = var_mapping[widget_var]
        
        if field_type == "text":
            # Validar que solo contenga letras y espacios
            if value and not re.match(r'^[A-ZÁÉÍÓÚÑÜ\s]+$', value.upper()):
                error_msg = "Solo se permiten letras y espacios"
        
        elif field_type == "placa":
            # Validar formato de placa (3 letras + 3 números o similar)
            if value and not re.match(r'^[A-Z]{3}[0-9]{3}$|^[A-Z]{3}[0-9]{2}[A-Z]$', value.upper()):
                error_msg = "Formato inválido (ej: ABC123 o ABC12D)"
        
        elif field_type == "documento":
            # Validar que solo contenga números
            if value and not re.match(r'^[0-9]+$', value):
                error_msg = "Solo se permiten números"
                # Limpiar caracteres no numéricos
                new_value = re.sub(r'[^0-9]', '', value)
                widget.delete(0, tk.END)
                widget.insert(0, new_value)
        
        elif field_type == "year":
            # Validar año (4 dígitos, rango razonable)
            if value and not value.isdigit():
                # Limpiar caracteres no numéricos
                new_value = re.sub(r'[^0-9]', '', value)
                widget.delete(0, tk.END)
                widget.insert(0, new_value)
                value = new_value
            
            if value and len(value) >= 4:
                try:
                    year_val = int(value)
                    if not (1900 <= year_val <= 2030):
                        error_msg = "Año inválido (1900-2030)"
                except ValueError:
                    error_msg = "Año inválido"
        
        elif field_type == "numeric":
            # Validar que solo contenga números
            if value and not value.isdigit():
                # Limpiar caracteres no numéricos
                new_value = re.sub(r'[^0-9]', '', value)
                widget.delete(0, tk.END)
                widget.insert(0, new_value)
        
        elif field_type == "referencia":
            # Validar referencia de vehículo (letras, números, espacios, guiones)
            if value and not re.match(r'^[A-ZÁÉÍÓÚÑÜ0-9\s\-]+$', value.upper()):
                error_msg = "Solo letras, números, espacios y guiones"
        
        elif field_type == "poliza_sura":
            # Validar póliza Sura (debe tener exactamente 12 dígitos)
            if value and not value.isdigit():
                # Limpiar caracteres no numéricos
                new_value = re.sub(r'[^0-9]', '', value)
                widget.delete(0, tk.END)
                widget.insert(0, new_value)
                value = new_value
            
            if value and len(value) != 12:
                error_msg = "Debe tener exactamente 12 dígitos"
            elif value and not value.isdigit():
                error_msg = "Solo se permiten números"
        
        elif field_type == "poliza_allianz":
            # Validar póliza Allianz (debe tener exactamente 8 dígitos)
            if value and not value.isdigit():
                # Limpiar caracteres no numéricos
                new_value = re.sub(r'[^0-9]', '', value)
                widget.delete(0, tk.END)
                widget.insert(0, new_value)
                value = new_value
            
            if value and len(value) != 8:
                error_msg = "Debe tener exactamente 8 dígitos"
            elif value and not value.isdigit():
                error_msg = "Solo se permiten números"
        
        # Mostrar o quitar mensaje de error
        self.show_error_message(field_name, error_msg)
        
        return error_msg == ""

    def show_error_message(self, field_name, message):
        """Muestra u oculta mensaje de error debajo de un campo sin mover el layout."""
        if field_name in self.error_labels:
            label = self.error_labels[field_name]
            if message:
                # Solo cambiar a rojo si es realmente un error y no es el campo de placa con mensaje informativo
                if field_name == 'placa' and self.vehicle_state.get() == "Nuevo":
                    # Mantener el color azul para el mensaje informativo
                    pass
                else:
                    label.config(foreground="red")
                label.config(text=f"⚠️ {message}")
            else:
                # Solo limpiar si no es un vehículo nuevo (que tiene mensaje informativo)
                if not (field_name == 'placa' and self.vehicle_state.get() == "Nuevo"):
                    label.config(text="")
                    label.config(foreground="red")

    def normalize_text(self, event):
        """Normaliza texto a mayúsculas al perder el foco."""
        widget = event.widget
        value = widget.get().upper()
        widget.delete(0, tk.END)
        widget.insert(0, value)
    
    def on_vehicle_state_change(self, event=None):
        """Maneja el cambio del estado del vehículo para bloquear/desbloquear la placa."""
        if hasattr(self, 'plate_entry') and hasattr(self, 'plate_info_label'):
            if self.vehicle_state.get() == "Nuevo":
                # Bloquear el campo de placa y mostrar mensaje
                self.plate_entry.config(state="readonly")  # readonly en lugar de disabled para mantener el color
                # Configurar color de fondo gris
                self.plate_entry.config(background="#e8e8e8", foreground="#666666")
                self.plate_info_label.config(
                    text="ℹ️ Placa no es necesaria porque es nuevo",
                    foreground="blue"
                )
                # Limpiar el campo de placa
                self.vehicle_plate.set("")
            else:
                # Desbloquear el campo de placa y quitar mensaje
                self.plate_entry.config(state="normal")
                # Restaurar color de fondo normal
                self.plate_entry.config(background="white", foreground="black")
                self.plate_info_label.config(text="", foreground="red")
    
    def setup_ui(self):
        """Configura la interfaz de usuario."""
        # Frame principal sin padding
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Frame de scroll
        canvas = tk.Canvas(main_frame, borderwidth=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        # Crea la ventana interna y guárdala con una tag para referenciarla
        inner_id = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", tags=("inner",))
        canvas.configure(yscrollcommand=scrollbar.set)

        def update_layout(event=None):
            """Ajusta ancho y bloquea scroll si no hay overflow vertical."""
            # 1) Mantener el ancho del inner igual al del canvas
            canvas.itemconfig("inner", width=canvas.winfo_width())
            # 2) Recalcular región de scroll
            bbox = canvas.bbox("inner")
            if not bbox:
                return
            content_h = bbox[3] - bbox[1]
            viewport_h = canvas.winfo_height()
            if content_h <= viewport_h:
                # Sin overflow: fija la región al viewport y vuelve al top
                canvas.yview_moveto(0)
                canvas.configure(scrollregion=(0, 0, bbox[2], viewport_h))
            else:
                # Con overflow: región normal al contenido
                canvas.configure(scrollregion=bbox)

        # Un solo set de binds limpio
        scrollable_frame.bind("<Configure>", update_layout)
        canvas.bind("<Configure>", update_layout)
        
        # Crear contenido con padding interno
        content_frame = ttk.Frame(scrollable_frame)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(15, 35))
        
        # Frame de historial
        self.create_history_section(content_frame)
        
        # Frame de datos personales
        self.create_personal_data_section(content_frame)
        
        # Frame de datos del vehículo
        self.create_vehicle_data_section(content_frame)
        
        # Frame de códigos Fasecolda
        self.create_fasecolda_section(content_frame)
        
        # Frame de pólizas
        self.create_policy_section(content_frame)
        
        # Frame de botones
        self.create_buttons_section(content_frame)
        
        # Configurar el canvas
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Bind mousewheel
        def _on_mousewheel(event):
            bbox = canvas.bbox("inner")
            if not bbox:
                return
            content_h = bbox[3] - bbox[1]
            if content_h <= canvas.winfo_height():
                return  # no hay nada que desplazar
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")

        canvas.bind("<MouseWheel>", _on_mousewheel)
    
    def create_history_section(self, parent):
        """Crea la sección de historial."""
        history_frame = ttk.LabelFrame(parent, text="📋 Historial de Clientes", padding="10")
        history_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Combo para seleccionar del historial
        ttk.Label(history_frame, text="Seleccionar cliente del historial:").pack(anchor=tk.W, pady=(0, 5))
        
        # Etiqueta de ayuda
        help_label = ttk.Label(
            history_frame, 
            text="💡 Los campos se actualizan automáticamente al seleccionar un cliente",
            font=("Arial", 8),
            foreground="gray"
        )
        help_label.pack(anchor=tk.W, pady=(0, 5))
        
        history_combo_frame = ttk.Frame(history_frame)
        history_combo_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.history_combo = ttk.Combobox(
            history_combo_frame,
            textvariable=self.selected_history_item,
            state="readonly",
            width=35
        )
        self.history_combo.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))
        
        # Bind para actualización automática al seleccionar
        self.history_combo.bind('<<ComboboxSelected>>', self.on_history_selection_changed)
        
        ttk.Button(
            history_combo_frame,
            text="🔄 Actualizar Historial",
            command=self.refresh_history,
            width=22
        ).pack(side=tk.RIGHT, padx=(5, 0))
        
        # Botones de acción del historial
        buttons_frame = ttk.Frame(history_frame)
        buttons_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(
            buttons_frame,
            text="🧹 Limpiar Campos",
            command=self.clear_all_fields,
            width=18
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            buttons_frame,
            text="🗑️Eliminar Seleccionado",
            command=self.delete_from_history,
            width=25
        ).pack(side=tk.LEFT, padx=(5, 0))
        
        # Cargar historial inicial
        self.refresh_history()
    
    def create_personal_data_section(self, parent):
        """Crea la sección de datos personales."""
        personal_frame = ttk.LabelFrame(parent, text="👤 Datos Personales del Cliente", padding="10")
        personal_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Configurar grid
        personal_frame.columnconfigure(1, weight=1)
        personal_frame.columnconfigure(3, weight=1)
        
        row = 0
        
        # Número de documento
        ttk.Label(personal_frame, text="Número de documento:").grid(row=row, column=0, sticky=tk.W, pady=5, padx=(0, 5))
        doc_frame = ttk.Frame(personal_frame)
        doc_frame.grid(row=row, column=1, sticky=tk.W+tk.E, pady=5, padx=(0, 15))
        doc_frame.columnconfigure(0, weight=1)
        
        doc_entry = ttk.Entry(doc_frame, textvariable=self.client_document_number, width=20)
        doc_entry.grid(row=0, column=0, sticky=tk.W+tk.E)
        doc_entry.bind('<KeyRelease>', lambda event: self.validate_field(event, 'documento'))
        doc_entry.bind('<FocusOut>', lambda event: self.normalize_text(event))
        
        # Error label para documento
        self.error_labels['document'] = ttk.Label(doc_frame, text="", foreground="red", font=("TkDefaultFont", 8))
        self.error_labels['document'].grid(row=1, column=0, sticky=tk.W, pady=(2, 0))
        
        # Género
        ttk.Label(personal_frame, text="Género:").grid(row=row, column=2, sticky=tk.W, pady=5, padx=(0, 5))
        gender_combo = ttk.Combobox(
            personal_frame,
            textvariable=self.client_gender,
            values=["M", "F"],
            state="readonly",
            width=5
        )
        gender_combo.grid(row=row, column=3, sticky=tk.W, pady=5)
        row += 1
        
        # Primer nombre
        ttk.Label(personal_frame, text="Primer nombre:").grid(row=row, column=0, sticky=tk.W, pady=5, padx=(0, 5))
        fname_frame = ttk.Frame(personal_frame)
        fname_frame.grid(row=row, column=1, sticky=tk.W+tk.E, pady=5, padx=(0, 15))
        fname_frame.columnconfigure(0, weight=1)
        
        fname_entry = ttk.Entry(fname_frame, textvariable=self.client_first_name, width=20)
        fname_entry.grid(row=0, column=0, sticky=tk.W+tk.E)
        fname_entry.bind('<KeyRelease>', lambda event: self.validate_field(event, 'text'))
        fname_entry.bind('<FocusOut>', lambda event: self.normalize_text(event))
        
        # Error label para primer nombre
        self.error_labels['first_name'] = ttk.Label(fname_frame, text="", foreground="red", font=("TkDefaultFont", 8))
        self.error_labels['first_name'].grid(row=1, column=0, sticky=tk.W, pady=(2, 0))
        
        # Segundo nombre
        ttk.Label(personal_frame, text="Segundo nombre:").grid(row=row, column=2, sticky=tk.W, pady=5, padx=(0, 5))
        sname_frame = ttk.Frame(personal_frame)
        sname_frame.grid(row=row, column=3, sticky=tk.W+tk.E, pady=5)
        sname_frame.columnconfigure(0, weight=1)
        
        sname_entry = ttk.Entry(sname_frame, textvariable=self.client_second_name, width=20)
        sname_entry.grid(row=0, column=0, sticky=tk.W+tk.E)
        sname_entry.bind('<KeyRelease>', lambda event: self.validate_field(event, 'text'))
        sname_entry.bind('<FocusOut>', lambda event: self.normalize_text(event))
        
        # Error label para segundo nombre  
        self.error_labels['second_name'] = ttk.Label(sname_frame, text="", foreground="red", font=("TkDefaultFont", 8))
        self.error_labels['second_name'].grid(row=1, column=0, sticky=tk.W, pady=(2, 0))
        row += 1
        
        # Primer apellido
        ttk.Label(personal_frame, text="Primer apellido:").grid(row=row, column=0, sticky=tk.W, pady=5, padx=(0, 5))
        lname1_frame = ttk.Frame(personal_frame)
        lname1_frame.grid(row=row, column=1, sticky=tk.W+tk.E, pady=5, padx=(0, 15))
        lname1_frame.columnconfigure(0, weight=1)
        
        lname1_entry = ttk.Entry(lname1_frame, textvariable=self.client_first_lastname, width=20)
        lname1_entry.grid(row=0, column=0, sticky=tk.W+tk.E)
        lname1_entry.bind('<KeyRelease>', lambda event: self.validate_field(event, 'text'))
        lname1_entry.bind('<FocusOut>', lambda event: self.normalize_text(event))
        
        # Error label para primer apellido
        self.error_labels['first_lastname'] = ttk.Label(lname1_frame, text="", foreground="red", font=("TkDefaultFont", 8))
        self.error_labels['first_lastname'].grid(row=1, column=0, sticky=tk.W, pady=(2, 0))
        
        # Segundo apellido
        ttk.Label(personal_frame, text="Segundo apellido:").grid(row=row, column=2, sticky=tk.W, pady=5, padx=(0, 5))
        lname2_frame = ttk.Frame(personal_frame)
        lname2_frame.grid(row=row, column=3, sticky=tk.W+tk.E, pady=5)
        lname2_frame.columnconfigure(0, weight=1)
        
        lname2_entry = ttk.Entry(lname2_frame, textvariable=self.client_second_lastname, width=20)
        lname2_entry.grid(row=0, column=0, sticky=tk.W+tk.E)
        lname2_entry.bind('<KeyRelease>', lambda event: self.validate_field(event, 'text'))
        lname2_entry.bind('<FocusOut>', lambda event: self.normalize_text(event))
        
        # Error label para segundo apellido
        self.error_labels['second_lastname'] = ttk.Label(lname2_frame, text="", foreground="red", font=("TkDefaultFont", 8))
        self.error_labels['second_lastname'].grid(row=1, column=0, sticky=tk.W, pady=(2, 0))
        row += 1
        
        # Fecha de nacimiento
        ttk.Label(personal_frame, text="Fecha de nacimiento (YYYY-MM-DD):").grid(row=row, column=0, sticky=tk.W, pady=5, padx=(0, 5))
        birth_frame = ttk.Frame(personal_frame)
        birth_frame.grid(row=row, column=1, sticky=tk.W+tk.E, pady=5, padx=(0, 15))
        
        ttk.Entry(birth_frame, textvariable=self.client_birth_date, width=15).pack(side=tk.LEFT)
        ttk.Button(
            birth_frame,
            text="📅",
            command=self.show_date_picker,
            width=3
        ).pack(side=tk.LEFT, padx=(5, 0))
        row += 1
        
        # Departamento (Combobox)
        ttk.Label(personal_frame, text="Departamento:").grid(row=row, column=0, sticky=tk.W, pady=5, padx=(0, 5))
        dept_frame = ttk.Frame(personal_frame)
        dept_frame.grid(row=row, column=1, sticky=tk.W+tk.E, pady=5, padx=(0, 15))
        dept_frame.columnconfigure(0, weight=1)
        
        dept_combo = ttk.Combobox(
            dept_frame,
            textvariable=self.client_department,
            values=self.DEPARTAMENTOS,
            state="readonly",
            width=25
        )
        dept_combo.grid(row=0, column=0, sticky=tk.W+tk.E)
        
        # Espacio vacío para alinear con error label de ciudad
        ttk.Label(dept_frame, text="").grid(row=1, column=0, sticky=tk.W, pady=(2, 0))
        
        # Ciudad
        ttk.Label(personal_frame, text="Ciudad:").grid(row=row, column=2, sticky=tk.W, pady=5, padx=(0, 5))
        city_frame = ttk.Frame(personal_frame)
        city_frame.grid(row=row, column=3, sticky=tk.W+tk.E, pady=5)
        city_frame.columnconfigure(0, weight=1)
        
        city_entry = ttk.Entry(city_frame, textvariable=self.client_city, width=20)
        city_entry.grid(row=0, column=0, sticky=tk.W+tk.E)
        city_entry.bind('<KeyRelease>', lambda event: self.validate_field(event, 'text'))
        city_entry.bind('<FocusOut>', lambda event: self.normalize_text(event))
        
        # Error label para ciudad
        self.error_labels['city'] = ttk.Label(city_frame, text="", foreground="red", font=("TkDefaultFont", 8))
        self.error_labels['city'].grid(row=1, column=0, sticky=tk.W, pady=(2, 0))
    
    def create_vehicle_data_section(self, parent):
        """Crea la sección de datos del vehículo con validación."""
        vehicle_frame = ttk.LabelFrame(parent, text="🚗 Datos del Vehículo", padding="10")
        vehicle_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Configurar grid
        vehicle_frame.columnconfigure(1, weight=1)
        vehicle_frame.columnconfigure(3, weight=1)
        
        row = 0
        
        # Estado del vehículo (MOVIDO AL INICIO)
        ttk.Label(vehicle_frame, text="Estado del vehículo:").grid(row=row, column=0, sticky=tk.W, pady=5, padx=(0, 5))
        self.state_combo = ttk.Combobox(
            vehicle_frame,
            textvariable=self.vehicle_state,
            values=["Nuevo", "Usado"],
            state="readonly",
            width=15
        )
        self.state_combo.grid(row=row, column=1, sticky=tk.W, pady=5, padx=(0, 15))
        self.state_combo.bind('<<ComboboxSelected>>', self.on_vehicle_state_change)
        row += 1
        
        # Placa
        ttk.Label(vehicle_frame, text="Placa:").grid(row=row, column=0, sticky=tk.W, pady=5, padx=(0, 5))
        self.plate_entry = ttk.Entry(vehicle_frame, textvariable=self.vehicle_plate, width=15)
        self.plate_entry.grid(row=row, column=1, sticky=tk.W, pady=5, padx=(0, 15))
        self.plate_entry.bind('<KeyRelease>', lambda event: self.validate_field(event, 'placa'))
        self.plate_entry.bind('<FocusOut>', lambda event: self.normalize_text(event))
        
        # Error/Info label para placa
        self.plate_info_label = ttk.Label(vehicle_frame, text="", foreground="blue", font=("Arial", 8))
        self.plate_info_label.grid(row=row+1, column=1, sticky=tk.W, padx=(0, 15))
        self.error_labels['placa'] = self.plate_info_label
        
        # Año del modelo
        ttk.Label(vehicle_frame, text="Año del modelo:").grid(row=row, column=2, sticky=tk.W, pady=5, padx=(0, 5))
        year_entry = ttk.Entry(vehicle_frame, textvariable=self.vehicle_model_year, width=10)
        year_entry.grid(row=row, column=3, sticky=tk.W, pady=5)
        year_entry.bind('<KeyRelease>', lambda event: self.validate_field(event, 'year'))
        
        # Error label para año
        year_error = ttk.Label(vehicle_frame, text="", foreground="red", font=("Arial", 8))
        year_error.grid(row=row+1, column=3, sticky=tk.W)
        self.error_labels['year'] = year_error
        
        row += 2
        
        # Marca
        ttk.Label(vehicle_frame, text="Marca:").grid(row=row, column=0, sticky=tk.W, pady=5, padx=(0, 5))
        
        # Lista de marcas de Fasecolda
        marcas_fasecolda = [
            'AUDI', 'BAIC', 'BMW', 'BRENSON', 'BYD', 'CHANGAN', 'CHERY', 'CHEVROLET',
            'CITROEN', 'CUPRA', 'DFSK', 'DFM', 'DFZL', 'DS', 'FAW AMI', 'FIAT', 'FORD',
            'FOTON', 'GAC', 'GREAT WALL', 'HONDA', 'HYUNDAI', 'JAC', 'JAGUAR', 'JEEP',
            'JETOUR', 'JMC', 'KIA', 'KYC', 'LAND ROVER', 'MAXUS', 'MAZDA', 'MERCEDES BENZ',
            'MG', 'MINI', 'MITSUBISHI', 'NISSAN', 'OPEL', 'PEUGEOT', 'PORSCHE', 'RAYSINCE',
            'RENAULT', 'SEAT', 'SHINERAY', 'SMART', 'SSANGYONG', 'SUBARU', 'SUZUKI',
            'TOYOTA', 'VOLKSWAGEN', 'VOLVO', 'ZEEKR'
        ]
        
        self.brand_combo = ttk.Combobox(
            vehicle_frame, 
            textvariable=self.vehicle_brand, 
            values=marcas_fasecolda,
            state="readonly",
            width=20
        )
        self.brand_combo.grid(row=row, column=1, columnspan=3, sticky=tk.W+tk.E, pady=5, padx=(0, 15))
        self.brand_combo.bind('<<ComboboxSelected>>', self.update_full_reference)
        row += 1
        
        # Referencia
        ttk.Label(vehicle_frame, text="Referencia:").grid(row=row, column=0, sticky=tk.W, pady=5, padx=(0, 5))
        self.reference_entry = ttk.Entry(vehicle_frame, textvariable=self.vehicle_reference, width=40)
        self.reference_entry.grid(row=row, column=1, columnspan=3, sticky=tk.W+tk.E, pady=5)
        self.reference_entry.bind('<KeyRelease>', self.update_full_reference)
        self.reference_entry.bind('<FocusOut>', lambda event: self.normalize_text(event))
        row += 1
        
        # Referencia completa Fasecolda
        ttk.Label(vehicle_frame, text="Referencia completa Fasecolda:").grid(row=row, column=0, sticky=tk.W, pady=5, padx=(0, 5))
        ttk.Entry(vehicle_frame, textvariable=self.vehicle_full_reference, width=40).grid(row=row, column=1, columnspan=3, sticky=tk.W+tk.E, pady=5)
    
    def create_fasecolda_section(self, parent):
        """Crea la sección de códigos Fasecolda con validación."""
        fasecolda_frame = ttk.LabelFrame(parent, text="🔍 Códigos Fasecolda Manuales (Solo llenar si se necesita, sino dejar vacio)", padding="10")
        fasecolda_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Configurar grid
        fasecolda_frame.columnconfigure(1, weight=1)
        fasecolda_frame.columnconfigure(3, weight=1)
        
        row = 0
        
        # Código CF
        ttk.Label(fasecolda_frame, text="Código CF:").grid(row=row, column=0, sticky=tk.W, pady=5, padx=(0, 5))
        cf_entry = ttk.Entry(fasecolda_frame, textvariable=self.manual_cf_code, width=15)
        cf_entry.grid(row=row, column=1, sticky=tk.W, pady=5, padx=(0, 15))
        cf_entry.bind('<KeyRelease>', lambda event: self.validate_field(event, 'numeric'))
        
        # Error label para CF
        cf_error = ttk.Label(fasecolda_frame, text="", foreground="red", font=("Arial", 8))
        cf_error.grid(row=row+1, column=1, sticky=tk.W, padx=(0, 15))
        self.error_labels['cf_code'] = cf_error
        
        # Código CH
        ttk.Label(fasecolda_frame, text="Código CH:").grid(row=row, column=2, sticky=tk.W, pady=5, padx=(0, 5))
        ch_entry = ttk.Entry(fasecolda_frame, textvariable=self.manual_ch_code, width=15)
        ch_entry.grid(row=row, column=3, sticky=tk.W, pady=5)
        ch_entry.bind('<KeyRelease>', lambda event: self.validate_field(event, 'numeric'))
        
        # Error label para CH
        ch_error = ttk.Label(fasecolda_frame, text="", foreground="red", font=("Arial", 8))
        ch_error.grid(row=row+1, column=3, sticky=tk.W)
        self.error_labels['ch_code'] = ch_error
    
    def create_policy_section(self, parent):
        """Crea la sección de pólizas."""
        policy_frame = ttk.LabelFrame(parent, text="📋 Números de Póliza", padding="10")
        policy_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Configurar grid
        policy_frame.columnconfigure(1, weight=1)
        policy_frame.columnconfigure(3, weight=1)
        
        row = 0
        
        # Póliza Sura
        ttk.Label(policy_frame, text="Póliza Sura (12 dígitos):").grid(row=row, column=0, sticky=tk.W, pady=5, padx=(0, 5))
        sura_frame = ttk.Frame(policy_frame)
        sura_frame.grid(row=row, column=1, sticky=tk.W+tk.E, pady=5, padx=(0, 15))
        sura_frame.columnconfigure(0, weight=1)
        
        sura_entry = ttk.Entry(sura_frame, textvariable=self.policy_number, width=20)
        sura_entry.grid(row=0, column=0, sticky=tk.W+tk.E)
        sura_entry.bind('<KeyRelease>', lambda event: self.validate_field(event, 'poliza_sura'))
        
        # Error label para póliza Sura
        sura_error = ttk.Label(sura_frame, text="", foreground="red", font=("Arial", 8))
        sura_error.grid(row=1, column=0, sticky=tk.W, pady=(2, 0))
        self.error_labels['poliza_sura'] = sura_error
        
        # Póliza Allianz
        ttk.Label(policy_frame, text="Póliza Allianz (8 dígitos):").grid(row=row, column=2, sticky=tk.W, pady=5, padx=(0, 5))
        allianz_frame = ttk.Frame(policy_frame)
        allianz_frame.grid(row=row, column=3, sticky=tk.W+tk.E, pady=5)
        allianz_frame.columnconfigure(0, weight=1)
        
        allianz_entry = ttk.Entry(allianz_frame, textvariable=self.policy_number_allianz, width=20)
        allianz_entry.grid(row=0, column=0, sticky=tk.W+tk.E)
        allianz_entry.bind('<KeyRelease>', lambda event: self.validate_field(event, 'poliza_allianz'))
        
        # Error label para póliza Allianz
        allianz_error = ttk.Label(allianz_frame, text="", foreground="red", font=("Arial", 8))
        allianz_error.grid(row=1, column=0, sticky=tk.W, pady=(2, 0))
        self.error_labels['poliza_allianz'] = allianz_error
    
    def create_buttons_section(self, parent):
        """Crea la sección de botones."""
        buttons_frame = ttk.Frame(parent)
        buttons_frame.pack(fill=tk.X, pady=(15, 0))
        
        # Centrar botones
        center_frame = ttk.Frame(buttons_frame)
        center_frame.pack(anchor=tk.CENTER)
        
        ttk.Button(
            center_frame,
            text="💾 Guardar y Aplicar",
            command=self.save_and_apply,
            width=18
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(
            center_frame,
            text="📁 Guardar en Historial",
            command=self.save_to_history,
            width=22
        ).pack(side=tk.LEFT, padx=(5, 10))
        
        ttk.Button(
            center_frame,
            text="❌ Cancelar",
            command=self.on_closing,
            width=12
        ).pack(side=tk.LEFT, padx=(10, 0))
    
    def show_date_picker(self):
        """Muestra un selector de fecha simple."""
        date_window = tk.Toplevel(self.window)
        date_window.title("Seleccionar Fecha")
        date_window.geometry("300x200")
        date_window.resizable(False, False)
        
        # Centrar en pantalla
        date_window.update_idletasks()
        x = (date_window.winfo_screenwidth() // 2) - (300 // 2)
        y = (date_window.winfo_screenheight() // 2) - (200 // 2)
        date_window.geometry(f"300x200+{x}+{y}")
        
        date_window.transient(self.window)
        date_window.grab_set()
        
        frame = ttk.Frame(date_window, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Seleccionar fecha de nacimiento:", font=("Arial", 12, "bold")).pack(pady=(0, 20))
        
        # Variables para fecha
        year_var = tk.StringVar()
        month_var = tk.StringVar()
        day_var = tk.StringVar()
        
        # Obtener fecha actual si existe
        current_date = self.client_birth_date.get()
        if current_date:
            try:
                date_obj = datetime.strptime(current_date, '%Y-%m-%d')
                year_var.set(str(date_obj.year))
                month_var.set(f"{date_obj.month:02d}")
                day_var.set(f"{date_obj.day:02d}")
            except ValueError:
                pass
        
        # Frame para selectores
        selectors_frame = ttk.Frame(frame)
        selectors_frame.pack(pady=(0, 20))
        
        # Año
        ttk.Label(selectors_frame, text="Año:").grid(row=0, column=0, padx=(0, 5))
        year_combo = ttk.Combobox(
            selectors_frame,
            textvariable=year_var,
            values=[str(y) for y in range(1920, datetime.now().year + 1)],
            width=8,
            state="readonly"
        )
        year_combo.grid(row=1, column=0, padx=(0, 5))
        
        # Mes
        ttk.Label(selectors_frame, text="Mes:").grid(row=0, column=1, padx=5)
        month_combo = ttk.Combobox(
            selectors_frame,
            textvariable=month_var,
            values=[f"{m:02d}" for m in range(1, 13)],
            width=5,
            state="readonly"
        )
        month_combo.grid(row=1, column=1, padx=5)
        
        # Día
        ttk.Label(selectors_frame, text="Día:").grid(row=0, column=2, padx=(5, 0))
        day_combo = ttk.Combobox(
            selectors_frame,
            textvariable=day_var,
            values=[f"{d:02d}" for d in range(1, 32)],
            width=5,
            state="readonly"
        )
        day_combo.grid(row=1, column=2, padx=(5, 0))
        
        # Botones
        buttons_frame = ttk.Frame(frame)
        buttons_frame.pack()
        
        def apply_date():
            try:
                year = year_var.get()
                month = month_var.get()
                day = day_var.get()
                
                if year and month and day:
                    date_str = f"{year}-{month}-{day}"
                    # Validar fecha
                    datetime.strptime(date_str, '%Y-%m-%d')
                    self.client_birth_date.set(date_str)
                    date_window.destroy()
                else:
                    messagebox.showwarning("Error", "Debe seleccionar año, mes y día")
            except ValueError:
                messagebox.showerror("Error", "Fecha inválida")
        
        ttk.Button(buttons_frame, text="Aplicar", command=apply_date).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(buttons_frame, text="Cancelar", command=date_window.destroy).pack(side=tk.LEFT)
    
    def refresh_history(self):
        """Actualiza la lista del historial."""
        history = self.history_manager.load_history()
        history_items = []
        
        for item in history:
            name = item.get('name', 'Sin nombre')
            created = item.get('created_at', '')
            if created:
                try:
                    date_obj = datetime.fromisoformat(created.replace('Z', '+00:00'))
                    date_str = date_obj.strftime('%Y-%m-%d %H:%M')
                except:
                    date_str = created[:10]  # Solo la fecha
            else:
                date_str = ''
            
            display_text = f"{name} ({date_str})"
            history_items.append(display_text)
        
        self.history_combo['values'] = history_items
        if history_items:
            self.history_combo.set('')
    
    def delete_from_history(self):
        """Elimina el cliente seleccionado del historial."""
        selection = self.selected_history_item.get()
        if not selection:
            messagebox.showwarning("Advertencia", "Debe seleccionar un cliente del historial")
            return
        
        if not messagebox.askyesno("Confirmar", "¿Está seguro de eliminar este cliente del historial?"):
            return
        
        try:
            index = self.history_combo.current()
            if index < 0:
                return
            
            history = self.history_manager.load_history()
            if index < len(history):
                client_id = history[index].get('id')
                if self.history_manager.delete_client(client_id):
                    messagebox.showinfo("Éxito", "Cliente eliminado del historial")
                    self.refresh_history()
                else:
                    messagebox.showerror("Error", "No se pudo eliminar el cliente")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error eliminando cliente: {e}")
    
    def load_default_values(self):
        """Carga los valores por defecto."""
        defaults = self.history_manager.get_default_values()
        self.load_data_to_fields(defaults)
    
    def clear_all_error_messages(self):
        """Limpia todos los mensajes de error de la interfaz."""
        for field_name in self.error_labels:
            self.show_error_message(field_name, "")

    def load_data_to_fields(self, data: Dict[str, Any]):
        """Carga datos en los campos de la interfaz."""
        # Limpiar todos los mensajes de error antes de cargar nuevos datos
        self.clear_all_error_messages()
        
        self.client_document_number.set(data.get('client_document_number', ''))
        self.client_first_name.set(data.get('client_first_name', ''))
        self.client_second_name.set(data.get('client_second_name', ''))
        self.client_first_lastname.set(data.get('client_first_lastname', ''))
        self.client_second_lastname.set(data.get('client_second_lastname', ''))
        self.client_birth_date.set(data.get('client_birth_date', ''))
        self.client_gender.set(data.get('client_gender', ''))
        self.client_city.set(data.get('client_city', ''))
        self.client_department.set(data.get('client_department', ''))
        
        self.vehicle_plate.set(data.get('vehicle_plate', ''))
        self.vehicle_model_year.set(data.get('vehicle_model_year', ''))
        self.vehicle_brand.set(data.get('vehicle_brand', ''))
        self.vehicle_reference.set(data.get('vehicle_reference', ''))
        self.vehicle_full_reference.set(data.get('vehicle_full_reference', ''))
        self.vehicle_state.set(data.get('vehicle_state', 'Nuevo'))
        # Eliminamos vehicle_insured_value_received ya que no es necesario
        
        self.manual_cf_code.set(data.get('manual_cf_code', ''))
        self.manual_ch_code.set(data.get('manual_ch_code', ''))
        
        self.policy_number.set(data.get('policy_number', ''))
        self.policy_number_allianz.set(data.get('policy_number_allianz', ''))
        
        # Configurar estado del vehículo después de cargar datos
        self.on_vehicle_state_change()
    
    def get_data_from_fields(self) -> Dict[str, str]:
        """Obtiene los datos de los campos de la interfaz."""
        return {
            'client_document_number': self.client_document_number.get(),
            'client_first_name': self.client_first_name.get(),
            'client_second_name': self.client_second_name.get(),
            'client_first_lastname': self.client_first_lastname.get(),
            'client_second_lastname': self.client_second_lastname.get(),
            'client_birth_date': self.client_birth_date.get(),
            'client_gender': self.client_gender.get(),
            'client_city': self.client_city.get(),
            'client_department': self.client_department.get(),
            
            'vehicle_plate': self.vehicle_plate.get(),
            'vehicle_model_year': self.vehicle_model_year.get(),
            'vehicle_brand': self.vehicle_brand.get(),
            'vehicle_reference': self.vehicle_reference.get(),
            'vehicle_full_reference': self.vehicle_full_reference.get(),
            'vehicle_state': self.vehicle_state.get(),
            # Eliminamos vehicle_insured_value_received ya que no es necesario
            
            'manual_cf_code': self.manual_cf_code.get(),
            'manual_ch_code': self.manual_ch_code.get(),
            
            'policy_number': self.policy_number.get(),
            'policy_number_allianz': self.policy_number_allianz.get()
        }
    
    def validate_data(self) -> bool:
        """Valida los datos antes de guardar."""
        data = self.get_data_from_fields()
        errors = self.history_manager.validate_client_data(data)
        
        if errors:
            error_message = "Se encontraron los siguientes errores:\n\n"
            for field, error in errors.items():
                field_name = field.replace('_', ' ').title()
                error_message += f"• {field_name}: {error}\n"
            
            # Asegurar que la ventana esté al frente antes de mostrar el error
            self.window.lift()
            self.window.focus_force()
            messagebox.showerror("Errores de Validación", error_message, parent=self.window)
            # Mantener la ventana al frente después del mensaje
            self.window.lift()
            return False
        
        return True
    
    def save_to_history(self):
        """Guarda los datos en el historial."""
        if not self.validate_data():
            return
        
        data = self.get_data_from_fields()
        
        # Preguntar por nombre personalizado
        name_window = tk.Toplevel(self.window)
        name_window.title("Nombre del Cliente")
        name_window.geometry("400x150")
        name_window.resizable(False, False)
        name_window.transient(self.window)
        name_window.grab_set()
        
        frame = ttk.Frame(name_window, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Nombre para identificar en el historial:").pack(pady=(0, 10))
        
        name_var = tk.StringVar()
        # Nombre por defecto
        default_name = f"{data.get('client_first_name', '')} {data.get('client_first_lastname', '')}".strip()
        name_var.set(default_name)
        
        name_entry = ttk.Entry(frame, textvariable=name_var, width=40)
        name_entry.pack(pady=(0, 15))
        name_entry.focus_set()
        name_entry.select_range(0, tk.END)
        
        buttons_frame = ttk.Frame(frame)
        buttons_frame.pack()
        
        def save_with_name():
            name = name_var.get().strip()
            if not name:
                messagebox.showwarning("Advertencia", "Debe ingresar un nombre")
                return
            
            if self.history_manager.save_client(data, name):
                messagebox.showinfo("Éxito", "Cliente guardado en el historial")
                self.refresh_history()
                name_window.destroy()
            else:
                messagebox.showerror("Error", "No se pudo guardar el cliente")
        
        ttk.Button(buttons_frame, text="Guardar", command=save_with_name).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(buttons_frame, text="Cancelar", command=name_window.destroy).pack(side=tk.LEFT)
        
        # Bind Enter
        name_entry.bind('<Return>', lambda e: save_with_name())
    
    def save_and_apply(self):
        """Guarda los datos en el historial y los aplica al sistema."""
        if not self.validate_data():
            return
        
        data = self.get_data_from_fields()
        
        # Guardar en el historial automáticamente
        try:
            if self.current_client_id:
                # Actualizar cliente existente
                nombre_completo = f"{data.get('client_first_name', '')} {data.get('client_first_lastname', '')}"
                resultado = self.history_manager.update_client(self.current_client_id, data, nombre_completo.strip())
                if resultado:
                    self.refresh_history()
                else:
                    print("Error: No se pudo actualizar el cliente en historial")
            else:
                # Crear nuevo cliente
                nombre_completo = f"{data.get('client_first_name', '')} {data.get('client_first_lastname', '')}"
                from datetime import datetime
                fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M")
                nombre_cliente = f"{nombre_completo.strip()} - {fecha_actual}"
                
                resultado = self.history_manager.save_client(data, nombre_cliente)
                if resultado:
                    self.refresh_history()
                else:
                    print("Error: No se pudo guardar el cliente en historial")
        except Exception as e:
            print(f"Error al guardar en historial: {e}")
        
        # Aplicar los datos al ClientConfig
        ClientConfig.load_client_data(data)
        ClientConfig.update_vehicle_state(data.get('vehicle_state', 'Nuevo'))
        
        # Configurar búsqueda comprehensiva de Fasecolda (siempre habilitada)
        import os
        os.environ['FASECOLDA_COMPREHENSIVE_SEARCH'] = 'True'
        
        # Llamar callback si existe (esto actualiza la ventana principal)
        if self.callback:
            self.callback(data)
        
        messagebox.showinfo("Éxito", "Datos guardados en historial y aplicados al sistema correctamente")
        self.window.destroy()
    
    def clear_all_fields(self):
        """Limpia todos los campos de la interfaz."""
        # Limpiar todos los mensajes de error
        self.clear_all_error_messages()
        
        # Limpiar datos personales
        self.client_document_number.set('')
        self.client_first_name.set('')
        self.client_second_name.set('')
        self.client_first_lastname.set('')
        self.client_second_lastname.set('')
        self.client_birth_date.set('')
        self.client_gender.set('')
        self.client_city.set('')
        self.client_department.set('')
        
        # Limpiar datos del vehículo
        self.vehicle_plate.set('')
        self.vehicle_model_year.set('')
        self.vehicle_brand.set('')
        self.vehicle_reference.set('')
        self.vehicle_full_reference.set('')
        self.vehicle_state.set('Nuevo')
        
        # Limpiar códigos Fasecolda
        self.manual_cf_code.set('')
        self.manual_ch_code.set('')
        
        # Limpiar pólizas
        self.policy_number.set('')
        self.policy_number_allianz.set('')
        
        # Limpiar selección del historial
        self.selected_history_item.set('')
        self.current_client_id = None
        if hasattr(self, 'history_combo'):
            self.history_combo.set('')
            
        # Configurar estado inicial del vehículo (bloquear placa si es nuevo)
        self.on_vehicle_state_change()
    
    def update_full_reference(self, event=None):
        """Actualiza la referencia completa automáticamente."""
        marca = self.vehicle_brand.get().strip()
        referencia = self.vehicle_reference.get().strip()
        
        if marca and referencia:
            full_ref = f"{marca.upper()} {referencia}"
            self.vehicle_full_reference.set(full_ref)
        elif marca:
            self.vehicle_full_reference.set(marca.upper())
        else:
            self.vehicle_full_reference.set("")
    
    def on_history_selection_changed(self, event=None):
        """Se ejecuta cuando se selecciona un elemento del historial."""
        selection = self.selected_history_item.get()
        if not selection:
            return
        
        try:
            index = self.history_combo.current()
            if index < 0:
                return
            
            history = self.history_manager.load_history()
            if index < len(history):
                client_data = history[index].get('data', {})
                # Guardar el ID del cliente seleccionado
                self.current_client_id = history[index].get('id')
                self.load_data_to_fields(client_data)
            
        except Exception as e:
            print(f"Error cargando datos automáticamente: {e}")
    
    def on_closing(self):
        """Maneja el cierre de la ventana."""
        self.window.destroy()
    
    def run(self):
        """Ejecuta la ventana."""
        self.window.mainloop()


def main():
    """Función principal para pruebas."""
    app = ClientEditWindow()
    app.run()


if __name__ == "__main__":
    main()
