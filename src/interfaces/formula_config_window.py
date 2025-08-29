"""
Ventana de configuración de fórmulas para Bolívar y Solidaria.

Esta ventana permite configurar los parámetros de las fórmulas de cálculo
para las cotizaciones de Bolívar y Solidaria.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any, Optional, Callable
from datetime import datetime
import re
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


class FormulaConfigWindow:
    """Ventana de configuración de fórmulas."""
    
    def __init__(self, parent: tk.Tk, company: str, callback: Optional[Callable] = None):
        """
        Inicializa la ventana de configuración.
        
        Args:
            parent: Ventana padre
            company: 'bolivar' o 'solidaria'
            callback: Función a llamar cuando se guarde la configuración
        """
        self.parent = parent
        self.company = company
        self.callback = callback
        self.formulas_config = FormulasConfig()
        
        # Crear la ventana
        self.window = tk.Toplevel(parent)
        self.window.title(f"🔧 Configuración de Fórmulas - {company.capitalize()}")
        self.window.geometry("500x600")
        self.window.resizable(False, False)
        
        # Centrar la ventana
        self.center_window()
        
        # Configurar el comportamiento de cierre
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.window.transient(parent)
        self.window.grab_set()
        
        # Variables de los campos
        self.compania_var = tk.StringVar()
        self.fecha_fin_var = tk.StringVar()
        self.tasa_var = tk.StringVar()
        self.formula_var = tk.StringVar()
        
        # Crear la interfaz
        self.setup_ui()
        
        # Cargar configuración actual
        self.load_current_config()
    
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
        # Frame principal
        main_frame = ttk.Frame(self.window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        title_label = ttk.Label(
            main_frame,
            text=f"Configuración de Fórmulas - {self.company.capitalize()}",
            font=("Arial", 14, "bold")
        )
        title_label.pack(pady=(0, 20))
        
        # Frame de campos
        fields_frame = ttk.Frame(main_frame)
        fields_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Campo 1: Compañía
        ttk.Label(fields_frame, text="Compañía:", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
        compania_combo = ttk.Combobox(
            fields_frame,
            textvariable=self.compania_var,
            values=["EPM", "CHEK", "EMVARIAS"],
            state="readonly",
            width=40
        )
        compania_combo.pack(fill=tk.X, pady=(0, 15))
        
        # Campo 2: Fecha de fin de vigencia
        ttk.Label(fields_frame, text="Fecha de fin de vigencia:", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
        fecha_frame = ttk.Frame(fields_frame)
        fecha_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.fecha_entry = ttk.Entry(fecha_frame, textvariable=self.fecha_fin_var, width=40)
        self.fecha_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Label(fecha_frame, text="(AAAA-MM-DD)", foreground="gray").pack(side=tk.RIGHT, padx=(5, 0))
        
        # Campo 3: Tasa
        ttk.Label(fields_frame, text="Tasa (%):", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
        tasa_frame = ttk.Frame(fields_frame)
        tasa_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.tasa_entry = ttk.Entry(tasa_frame, textvariable=self.tasa_var, width=40)
        self.tasa_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Label(tasa_frame, text="(ej: 4.5)", foreground="gray").pack(side=tk.RIGHT, padx=(5, 0))
        
        # Campo 4: Fórmula (editable)
        ttk.Label(fields_frame, text="Fórmula:", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
        
        # Frame para fórmula con scroll
        formula_frame = ttk.Frame(fields_frame)
        formula_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.formula_text = tk.Text(
            formula_frame,
            height=3,
            width=50,
            wrap=tk.WORD,
            font=("Courier", 9),
            bg="white"
        )
        self.formula_text.pack(fill=tk.X)
        
        # Información adicional
        info_frame = ttk.LabelFrame(main_frame, text="Información", padding="10")
        info_frame.pack(fill=tk.X, pady=(0, 20))
        
        info_text = """• La configuración se guarda automáticamente y es persistente
• La tasa se puede modificar según las necesidades del mercado
• La fecha de vigencia es informativa y editable
• La fórmula es fija según la compañía seleccionada"""
        
        ttk.Label(info_frame, text=info_text, font=("Arial", 9)).pack(anchor=tk.W)
        
        # Botones - SIEMPRE VISIBLES
        buttons_container = ttk.Frame(main_frame)
        buttons_container.pack(fill=tk.X, side=tk.BOTTOM)
        
        # Separador
        ttk.Separator(buttons_container, orient='horizontal').pack(fill=tk.X, pady=(10, 10))
        
        # Botones principales en línea horizontal
        buttons_row = ttk.Frame(buttons_container)
        buttons_row.pack(expand=True)
        
        # Botón Aceptar
        btn_aceptar = ttk.Button(
            buttons_row,
            text="✅ Aceptar",
            command=self.save_config
        )
        btn_aceptar.pack(side=tk.LEFT, padx=10, pady=10)
        
        # Botón Cerrar
        btn_cerrar = ttk.Button(
            buttons_row,
            text="❌ Cerrar",
            command=self.on_closing
        )
        btn_cerrar.pack(side=tk.LEFT, padx=10, pady=10)
        
        # Vincular cambios en compañía para actualizar fórmula
        compania_combo.bind('<<ComboboxSelected>>', self.on_company_change)
    
    def load_current_config(self):
        """Carga la configuración actual."""
        config = self.formulas_config.get_formula_config(self.company)
        
        self.compania_var.set(config.get('compania', 'EPM'))
        self.fecha_fin_var.set(config.get('fecha_fin_vigencia', '2025-12-31'))
        self.tasa_var.set(config.get('tasa', '4.0'))
        
        # Cargar fórmula guardada o usar por defecto
        formula_guardada = config.get('formula', '')
        if formula_guardada:
            self.formula_text.delete(1.0, tk.END)
            self.formula_text.insert(1.0, formula_guardada)
        else:
            # Actualizar con fórmula por defecto
            self.update_formula_display()
    
    def on_company_change(self, event=None):
        """Maneja el cambio de compañía."""
        self.update_formula_display()
    
    def update_formula_display(self):
        """Actualiza la visualización de la fórmula."""
        # Obtener la fórmula según la compañía
        if self.company == 'bolivar':
            formula = "((VALORASEGURADO*TASA/100)+(279890)+(104910))*1.19"
        elif self.company == 'solidaria':
            formula = "((VALORASEGURADO*TASA/100)+(246000)+(93600)+(13200))*1.19"
        else:
            formula = "Fórmula no definida"
        
        # Actualizar el campo de texto (ahora editable)
        self.formula_text.delete(1.0, tk.END)
        self.formula_text.insert(1.0, formula)
    
    def validate_data(self) -> bool:
        """Valida los datos ingresados."""
        # Validar compañía
        if not self.compania_var.get():
            messagebox.showerror("Error", "Debe seleccionar una compañía")
            return False
        
        # Validar fecha
        fecha = self.fecha_fin_var.get().strip()
        if fecha:
            if not re.match(r'^\d{4}-\d{2}-\d{2}$', fecha):
                messagebox.showerror("Error", "La fecha debe tener el formato AAAA-MM-DD")
                return False
            
            try:
                datetime.strptime(fecha, '%Y-%m-%d')
            except ValueError:
                messagebox.showerror("Error", "Fecha inválida")
                return False
        
        # Validar tasa
        tasa = self.tasa_var.get().strip()
        if not tasa:
            messagebox.showerror("Error", "La tasa es obligatoria")
            return False
        
        try:
            tasa_float = float(tasa)
            if tasa_float < 0 or tasa_float > 100:
                messagebox.showerror("Error", "La tasa debe estar entre 0 y 100")
                return False
        except ValueError:
            messagebox.showerror("Error", "La tasa debe ser un número válido")
            return False
        
        return True
    
    def save_config(self):
        """Guarda la configuración."""
        if not self.validate_data():
            return
        
        # Crear configuración
        config = {
            'compania': self.compania_var.get(),
            'fecha_fin_vigencia': self.fecha_fin_var.get().strip(),
            'tasa': self.tasa_var.get().strip(),
            'formula': self.get_current_formula()
        }
        
        # Guardar
        self.formulas_config.update_formula_config(self.company, config)
        
        # Mostrar confirmación con la compañía seleccionada
        company_name = self.company.capitalize()
        selected_company = self.compania_var.get()
        messagebox.showinfo(
            "Configuración Guardada", 
            f"✅ {company_name} configurado exitosamente\n\n"
            f"📋 Compañía seleccionada: {selected_company}\n"
            f"📅 Vigencia: {self.fecha_fin_var.get().strip()}\n"
            f"📊 Tasa: {self.tasa_var.get().strip()}%\n\n"
            f"Esta configuración se aplicará en los cálculos."
        )
        
        # Llamar callback si existe
        if self.callback:
            self.callback()
        
        # Cerrar ventana
        self.on_closing()
    
    def get_current_formula(self) -> str:
        """Obtiene la fórmula actual del campo de texto."""
        return self.formula_text.get(1.0, tk.END).strip()
    
    def restore_defaults(self):
        """Restaura los valores por defecto."""
        if messagebox.askyesno("Confirmar", "¿Está seguro de restaurar los valores por defecto?"):
            if self.company == 'bolivar':
                self.compania_var.set('EPM')
                self.fecha_fin_var.set('2025-12-31')
                self.tasa_var.set('4.5')
            elif self.company == 'solidaria':
                self.compania_var.set('EPM')
                self.fecha_fin_var.set('2025-12-31')
                self.tasa_var.set('4.0')
            
            self.update_formula_display()
    
    def on_closing(self):
        """Maneja el cierre de la ventana."""
        self.window.destroy()
