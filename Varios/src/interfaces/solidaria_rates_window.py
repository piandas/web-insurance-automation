"""
Ventana de configuración de tasas de Solidaria por departamento y antigüedad.

Esta ventana permite configurar las tasas específicas de Solidaria
basadas en el departamento y la antigüedad del vehículo.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any, Optional, Callable
import sys
from pathlib import Path

# Manejo de imports con múltiples fallbacks
try:
    from ..config.formulas_config import FormulasConfig
except ImportError:
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from config.formulas_config import FormulasConfig
    except ImportError:
        project_root = Path(__file__).parent.parent.parent
        sys.path.insert(0, str(project_root))
        from src.config.formulas_config import FormulasConfig


class SolidariaRatesWindow:
    """Ventana de configuración de tasas de Solidaria por departamento."""
    
    def __init__(self, parent: tk.Tk, callback: Optional[Callable] = None):
        """
        Inicializa la ventana de configuración de tasas.
        
        Args:
            parent: Ventana padre
            callback: Función a llamar cuando se guarde la configuración
        """
        self.parent = parent
        self.callback = callback
        self.formulas_config = FormulasConfig()
        
        # Variable para la compañía seleccionada
        self.selected_company = tk.StringVar()
        
        # Crear la ventana
        self.window = tk.Toplevel(parent)
        self.window.title("📊 Configuración de Tasas Solidaria por Departamento")
        self.window.geometry("800x650")
        self.window.resizable(True, True)
        self.window.minsize(750, 600)
        
        # Centrar la ventana
        self.center_window()
        
        # Configurar el comportamiento de cierre
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.window.transient(parent)
        self.window.grab_set()
        
        # Diccionario para almacenar las variables de los campos
        self.rate_vars = {}
        
        # Crear la interfaz
        self.setup_ui()
        
        # Cargar configuración actual
        self.load_current_rates()
    
    def center_window(self):
        """Centra la ventana en la pantalla."""
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f"{width}x{height}+{x}+{y}")
    
    def setup_ui(self):
        """Configura la interfaz de usuario."""
        # Frame principal con padding más controlado
        main_frame = ttk.Frame(self.window, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título principal
        title_label = ttk.Label(
            main_frame,
            text="Configuración de Tasas Solidaria por Departamento y Antigüedad",
            font=("Arial", 14, "bold")
        )
        title_label.pack(pady=(0, 15))
        
        # Frame de selección de compañía
        company_frame = ttk.LabelFrame(main_frame, text="🏢 Seleccionar Compañía", padding="10")
        company_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Obtener compañías disponibles
        companias_disponibles = self.formulas_config.get_companias_disponibles('tasas_solidaria')
        if not companias_disponibles:
            companias_disponibles = ['EPM', 'FEPEP', 'CHEC', 'EMVARIAS', 'CONFAMILIA', 'FECORA', 'FODELSA', 'MANPOWER']
        
        # Configurar valor inicial
        compania_actual = self.formulas_config._get_compania_actual('solidaria')
        if compania_actual not in companias_disponibles:
            compania_actual = companias_disponibles[0]
        
        self.selected_company.set(compania_actual)
        
        # ComboBox para seleccionar compañía
        ttk.Label(company_frame, text="Compañía:", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=(0, 10))
        company_combo = ttk.Combobox(
            company_frame, 
            textvariable=self.selected_company,
            values=companias_disponibles,
            state="readonly",
            width=15
        )
        company_combo.pack(side=tk.LEFT, padx=(0, 10))
        
        # Botón para cargar tasas de la compañía seleccionada
        load_button = ttk.Button(
            company_frame,
            text="🔄 Cargar Tasas",
            command=self.load_company_rates
        )
        load_button.pack(side=tk.LEFT, padx=(10, 0))
        
        # Evento para cambio de compañía
        company_combo.bind('<<ComboboxSelected>>', self.on_company_changed)
        
        # Frame de información compacto
        info_frame = ttk.LabelFrame(main_frame, text="ℹ️ Información", padding="10")
        info_frame.pack(fill=tk.X, pady=(0, 15))
        
        info_text = """Configure las tasas de Solidaria específicas para cada compañía según el departamento y la antigüedad del vehículo.
Rangos: 0-1 años • 2-6 años • 7-10 años • 11-15 años • 16-30 años
💡 Estas tasas se usarán automáticamente cuando deje la tasa vacía en la configuración de Solidaria."""
        
        ttk.Label(info_frame, text=info_text, justify=tk.LEFT, font=("Arial", 9)).pack(anchor=tk.W)
        
        # Frame para la tabla de tasas - sin scroll interno, más compacto
        rates_frame = ttk.LabelFrame(main_frame, text="📊 Tasas por Departamento (%)", padding="10")
        rates_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # Crear tabla directamente sin scroll
        self.create_rates_table(rates_frame)
        
        # Frame de botones con mejor distribución
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Botones centrados horizontalmente
        center_buttons_frame = ttk.Frame(buttons_frame)
        center_buttons_frame.pack(anchor=tk.CENTER)
        
        ttk.Button(
            center_buttons_frame,
            text="💾 Guardar Configuración",
            command=self.save_rates,
            width=24
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(
            center_buttons_frame,
            text="🔄 Restaurar por Defecto",
            command=self.restore_defaults,
            width=24
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(
            center_buttons_frame,
            text="❌ Cancelar",
            command=self.on_closing,
            width=15
        ).pack(side=tk.LEFT)
    
    def create_rates_table(self, parent):
        """Crea la tabla de configuración de tasas."""
        # Departamentos disponibles
        departamentos = [
            "Cundinamarca",
            "Antioquia", 
            "Valle",
            "Quindio, Caldas y Risaralda",
            "Nariño, Meta, Boyacá y Cauca",
            "Córdoba, Cesar, Bolívar y Atlántico",
            "Tolima, Huila, Santander y Norte de Santander"
        ]
        
        # Rangos de antigüedad
        rangos = [
            ("0-1 años", "0_1"),
            ("2-6 años", "2_6"), 
            ("7-10 años", "7_10"),
            ("11-15 años", "11_15"),
            ("16-30 años", "16_30")
        ]
        
        # Crear un frame contenedor para toda la tabla
        table_container = ttk.Frame(parent)
        table_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Header de la tabla con mejor espaciado
        header_frame = ttk.Frame(table_container)
        header_frame.pack(fill=tk.X, pady=(0, 8))
        
        # Configure grid weights para mejor distribución
        header_frame.grid_columnconfigure(0, weight=2, minsize=280)
        for i in range(1, 6):
            header_frame.grid_columnconfigure(i, weight=1, minsize=90)
        
        # Primera columna (departamentos)
        dept_header = ttk.Label(header_frame, text="Departamento", font=("Arial", 10, "bold"))
        dept_header.grid(row=0, column=0, padx=(0, 10), sticky="w")
        
        # Columnas de rangos
        for col, (rango_text, _) in enumerate(rangos, 1):
            range_header = ttk.Label(header_frame, text=rango_text, font=("Arial", 10, "bold"))
            range_header.grid(row=0, column=col, padx=3, sticky="ew")
        
        # Separador visual
        separator = ttk.Separator(table_container, orient='horizontal')
        separator.pack(fill=tk.X, pady=(0, 8))
        
        # Frame para las filas de datos
        data_frame = ttk.Frame(table_container)
        data_frame.pack(fill=tk.BOTH, expand=True)
        
        # Configure grid weights para las filas de datos
        data_frame.grid_columnconfigure(0, weight=2, minsize=280)
        for i in range(1, 6):
            data_frame.grid_columnconfigure(i, weight=1, minsize=90)
        
        # Filas de departamentos con mejor espaciado
        for row, departamento in enumerate(departamentos):
            # Label del departamento con texto más compacto
            dept_text = departamento
            if len(dept_text) > 35:
                dept_text = dept_text[:32] + "..."
            
            dept_label = ttk.Label(data_frame, text=dept_text, font=("Arial", 9))
            dept_label.grid(row=row, column=0, padx=(0, 10), sticky="w", pady=3)
            
            # Inicializar diccionario para este departamento
            if departamento not in self.rate_vars:
                self.rate_vars[departamento] = {}
            
            # Campos de entrada para cada rango con mejor tamaño
            for col, (_, rango_key) in enumerate(rangos, 1):
                var = tk.StringVar()
                self.rate_vars[departamento][rango_key] = var
                
                entry = ttk.Entry(data_frame, textvariable=var, width=8, justify='center', font=("Arial", 9))
                entry.grid(row=row, column=col, padx=3, pady=3, sticky="ew")
                
                # Validar que solo se ingresen números
                entry.configure(validate='key', validatecommand=(self.window.register(self.validate_number), '%P'))
    
    def validate_number(self, value):
        """Valida que el valor ingresado sea un número válido."""
        if value == "":
            return True
        try:
            float(value)
            return True
        except ValueError:
            return False
    
    def load_current_rates(self):
        """Carga las tasas actuales desde la configuración."""
        self.load_company_rates()
    
    def load_company_rates(self):
        """Carga las tasas de la compañía seleccionada."""
        try:
            selected_company = self.selected_company.get()
            if not selected_company:
                return
            
            # Obtener tasas específicas de la compañía
            tasas_departamentos = self.formulas_config._get_tasas_solidaria_por_compania(selected_company)
            
            for departamento, vars_dict in self.rate_vars.items():
                if departamento in tasas_departamentos:
                    for rango, var in vars_dict.items():
                        tasa = tasas_departamentos[departamento].get(rango, 0.0)
                        var.set(str(tasa))
                else:
                    # Si no hay tasas para este departamento, limpiar los campos
                    for rango, var in vars_dict.items():
                        var.set("0.0")
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar tasas: {str(e)}")
    
    def on_company_changed(self, event=None):
        """Maneja el cambio de compañía seleccionada."""
        self.load_company_rates()
    
    def save_rates(self):
        """Guarda las tasas configuradas para la compañía seleccionada."""
        try:
            selected_company = self.selected_company.get()
            if not selected_company:
                messagebox.showerror("Error", "Debe seleccionar una compañía")
                return
            
            # Validar que todos los campos tengan valores válidos
            for departamento, vars_dict in self.rate_vars.items():
                for rango, var in vars_dict.items():
                    value = var.get().strip()
                    if not value:
                        messagebox.showerror("Error", f"El campo {departamento} - {rango} está vacío")
                        return
                    try:
                        float(value)
                    except ValueError:
                        messagebox.showerror("Error", f"El valor '{value}' en {departamento} - {rango} no es válido")
                        return
            
            # Preparar configuración actualizada para la compañía específica
            tasas_departamentos = {}
            
            for departamento, vars_dict in self.rate_vars.items():
                tasas_departamentos[departamento] = {}
                for rango, var in vars_dict.items():
                    tasas_departamentos[departamento][rango] = float(var.get().strip())
            
            # Actualizar configuración de tasas para la compañía específica
            self.formulas_config.update_tasas_solidaria_compania(selected_company, tasas_departamentos)
            
            messagebox.showinfo("Éxito", f"Tasas de {selected_company} guardadas correctamente")
            
            # Llamar callback si existe
            if self.callback:
                self.callback()
            
            self.window.destroy()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar tasas: {str(e)}")
    
    def restore_defaults(self):
        """Restaura los valores por defecto para la compañía seleccionada."""
        selected_company = self.selected_company.get()
        if not selected_company:
            messagebox.showerror("Error", "Debe seleccionar una compañía")
            return
            
        if messagebox.askyesno("Confirmar", f"¿Está seguro de que desea restaurar los valores por defecto para {selected_company}?"):
            try:
                # Obtener valores por defecto de la compañía desde FormulasConfig
                default_tasas = self.formulas_config._default_config.get('tasas_solidaria', {}).get(selected_company, {})
                
                # Si no hay valores por defecto específicos, usar los de EPM como base
                if not default_tasas:
                    default_tasas = self.formulas_config._default_config.get('tasas_solidaria', {}).get('EPM', {})
                
                # Cargar valores por defecto en los campos
                for departamento, tasas in default_tasas.items():
                    if departamento in self.rate_vars:
                        for rango, tasa in tasas.items():
                            if rango in self.rate_vars[departamento]:
                                self.rate_vars[departamento][rango].set(str(tasa))
                
                messagebox.showinfo("Éxito", f"Valores por defecto de {selected_company} restaurados")
                
            except Exception as e:
                messagebox.showerror("Error", f"Error al restaurar valores por defecto: {str(e)}")
    
    def on_closing(self):
        """Maneja el evento de cierre de la ventana."""
        self.window.destroy()
