"""
Ventana de selección de referencias de Fasecolda
"""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Dict, Optional


class FasecoldaSelectionWindow:
    """Ventana para seleccionar una referencia específica de Fasecolda cuando hay múltiples opciones."""
    
    def __init__(self, parent=None):
        self.parent = parent
        self.selected_option = None
        self.window = None
        self.combo_var = tk.StringVar()
        
    def show_selection_dialog(self, options: List[Dict], grouped_by_reference: bool = True) -> Optional[int]:
        """
        Muestra el diálogo de selección y retorna el índice de la opción seleccionada.
        
        Args:
            options: Lista de diccionarios con información de cada opción
            grouped_by_reference: Si True, agrupa las opciones por referencia
            
        Returns:
            Índice de la opción seleccionada (0-based) o None si se canceló
        """
        self.window = tk.Toplevel() if self.parent else tk.Tk()
        self.window.title("Selección de Referencia Fasecolda")
        self.window.geometry("900x600")
        self.window.resizable(False, False)
        
        # Centrar ventana
        self._center_window()
        
        # Configurar como modal
        if self.parent:
            self.window.transient(self.parent)
            self.window.grab_set()
        
        # Variables
        self.selected_option = None
        self.options = options
        
        # Crear interfaz
        self._create_interface(grouped_by_reference)
        
        # Manejar cierre
        self.window.protocol("WM_DELETE_WINDOW", self._on_cancel)
        
        # Esperar a que se cierre la ventana
        self.window.wait_window()
        
        return self.selected_option
    
    def _center_window(self):
        """Centra la ventana en la pantalla."""
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f"+{x}+{y}")
    
    def _create_interface(self, grouped_by_reference: bool):
        """Crea la interfaz de la ventana de selección."""
        # Frame principal
        main_frame = ttk.Frame(self.window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        title_label = ttk.Label(
            main_frame,
            text="Referencias encontradas para el vehículo",
            font=("Arial", 14, "bold")
        )
        title_label.pack(pady=(0, 20))
        
        # Subtítulo informativo
        info_label = ttk.Label(
            main_frame,
            text="Se encontraron múltiples opciones. Seleccione la más apropiada:",
            font=("Arial", 10)
        )
        info_label.pack(pady=(0, 15))
        
        # Frame de opciones con scroll
        self._create_options_frame(main_frame, grouped_by_reference)
        
        # Frame de selección
        selection_frame = ttk.LabelFrame(main_frame, text="Selección", padding="10")
        selection_frame.pack(fill=tk.X, pady=(20, 0))
        
        # Combobox para selección
        ttk.Label(selection_frame, text="Opción seleccionada:").pack(anchor=tk.W)
        
        combo_frame = ttk.Frame(selection_frame)
        combo_frame.pack(fill=tk.X, pady=(5, 10))
        
        # Crear lista de valores para el combobox
        combo_values = [f"{i+1}" for i in range(len(self.options))]
        
        self.selection_combo = ttk.Combobox(
            combo_frame,
            textvariable=self.combo_var,
            values=combo_values,
            state="readonly",
            width=10
        )
        self.selection_combo.pack(side=tk.LEFT, padx=(0, 10))
        
        # Label para mostrar la descripción de la opción seleccionada
        self.selection_description = ttk.Label(
            combo_frame,
            text="Seleccione una opción del dropdown",
            font=("Arial", 9),
            foreground="gray"
        )
        self.selection_description.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Bind para actualizar descripción
        self.selection_combo.bind('<<ComboboxSelected>>', self._on_selection_changed)
        
        # Botones
        button_frame = ttk.Frame(selection_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(
            button_frame,
            text="Cancelar",
            command=self._on_cancel,
            width=15
        ).pack(side=tk.RIGHT, padx=(10, 0))
        
        ttk.Button(
            button_frame,
            text="Aceptar",
            command=self._on_accept,
            width=15
        ).pack(side=tk.RIGHT)
    
    def _create_options_frame(self, parent, grouped_by_reference: bool):
        """Crea el frame con las opciones disponibles."""
        # Frame con scroll
        options_frame = ttk.LabelFrame(parent, text="Opciones disponibles", padding="10")
        options_frame.pack(fill=tk.BOTH, expand=True)
        
        # Canvas y scrollbar
        canvas = tk.Canvas(options_frame, height=300)
        scrollbar = ttk.Scrollbar(options_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas_frame = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        
        # Mostrar opciones
        if grouped_by_reference:
            self._display_grouped_options(scrollable_frame)
        else:
            self._display_simple_options(scrollable_frame)
        
        # Configurar scroll
        def _configure_scroll(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            # Ajustar ancho del canvas
            canvas_width = event.width
            canvas.itemconfig(canvas_frame, width=canvas_width)
        
        scrollable_frame.bind("<Configure>", _configure_scroll)
        canvas.bind("<Configure>", _configure_scroll)
        
        # Bind mousewheel
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind("<MouseWheel>", _on_mousewheel)
        
        # Pack canvas y scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def _display_grouped_options(self, parent):
        """Muestra las opciones agrupadas por referencia."""
        current_reference = None
        reference_counter = 0
        
        for i, option in enumerate(self.options):
            option_reference = option.get('reference_name', f"Referencia {i+1}")
            
            # Si es una nueva referencia, mostrar encabezado
            if option_reference != current_reference:
                current_reference = option_reference
                reference_counter += 1
                
                # Separador si no es la primera referencia
                if reference_counter > 1:
                    ttk.Separator(parent, orient='horizontal').pack(fill=tk.X, pady=(15, 10))
                
                # Encabezado de referencia
                ref_frame = ttk.Frame(parent)
                ref_frame.pack(fill=tk.X, pady=(5, 10))
                
                ttk.Label(
                    ref_frame,
                    text=f"REFERENCIA {reference_counter}: {option_reference}",
                    font=("Arial", 11, "bold"),
                    foreground="navy"
                ).pack(anchor=tk.W)
            
            # Mostrar opción individual
            self._display_single_option(parent, option, i+1)
    
    def _display_simple_options(self, parent):
        """Muestra las opciones de forma simple, sin agrupación."""
        for i, option in enumerate(self.options):
            self._display_single_option(parent, option, i+1)
            
            # Separador entre opciones (excepto la última)
            if i < len(self.options) - 1:
                ttk.Separator(parent, orient='horizontal').pack(fill=tk.X, pady=(10, 10))
    
    def _display_single_option(self, parent, option: Dict, number: int):
        """Muestra una opción individual."""
        option_frame = ttk.Frame(parent)
        option_frame.pack(fill=tk.X, pady=(0, 8))
        
        # Número y descripción principal
        header_frame = ttk.Frame(option_frame)
        header_frame.pack(fill=tk.X)
        
        ttk.Label(
            header_frame,
            text=f"{number}.",
            font=("Arial", 10, "bold"),
            foreground="red"
        ).pack(side=tk.LEFT)
        
        ttk.Label(
            header_frame,
            text=option.get('description', 'Sin descripción'),
            font=("Arial", 10),
            wraplength=650
        ).pack(side=tk.LEFT, padx=(5, 0), fill=tk.X, expand=True)
        
        # Información detallada
        details_frame = ttk.Frame(option_frame)
        details_frame.pack(fill=tk.X, padx=(20, 0))
        
        # CF y CH
        codes_text = f"CF: {option.get('cf_code', 'N/A')}"
        if option.get('ch_code'):
            codes_text += f" - CH: {option.get('ch_code', 'N/A')}"
        
        ttk.Label(
            details_frame,
            text=codes_text,
            font=("Arial", 9),
            foreground="blue"
        ).pack(anchor=tk.W)
        
        # Valor asegurado
        if option.get('insured_value'):
            ttk.Label(
                details_frame,
                text=f"Valor: {option.get('insured_value')}",
                font=("Arial", 9),
                foreground="green"
            ).pack(anchor=tk.W)
    
    def _on_selection_changed(self, event=None):
        """Maneja el cambio de selección en el combobox."""
        try:
            selected_index = int(self.combo_var.get()) - 1  # Convertir a 0-based
            if 0 <= selected_index < len(self.options):
                option = self.options[selected_index]
                description = option.get('description', 'Sin descripción')
                # Truncar descripción si es muy larga
                if len(description) > 80:
                    description = description[:77] + "..."
                self.selection_description.config(text=description)
            else:
                self.selection_description.config(text="Selección inválida")
        except (ValueError, IndexError):
            self.selection_description.config(text="Seleccione una opción válida")
    
    def _on_accept(self):
        """Maneja el clic en el botón Aceptar."""
        try:
            if not self.combo_var.get():
                messagebox.showwarning("Advertencia", "Por favor seleccione una opción")
                return
            
            selected_index = int(self.combo_var.get()) - 1  # Convertir a 0-based
            if 0 <= selected_index < len(self.options):
                self.selected_option = selected_index
                self.window.destroy()
            else:
                messagebox.showerror("Error", "Selección inválida")
        except ValueError:
            messagebox.showerror("Error", "Selección inválida")
    
    def _on_cancel(self):
        """Maneja el clic en el botón Cancelar o cierre de ventana."""
        self.selected_option = None
        self.window.destroy()


def show_fasecolda_selection_dialog(options: List[Dict], parent=None, grouped_by_reference: bool = True) -> Optional[int]:
    """
    Función de conveniencia para mostrar el diálogo de selección.
    
    Args:
        options: Lista de opciones a mostrar
        parent: Ventana padre (opcional)
        grouped_by_reference: Si agrupar por referencia
        
    Returns:
        Índice de la opción seleccionada o None si se canceló
    """
    dialog = FasecoldaSelectionWindow(parent)
    return dialog.show_selection_dialog(options, grouped_by_reference)


if __name__ == "__main__":
    # Ejemplo de uso
    test_options = [
        {
            'reference_name': 'Fortuner [2] [fl] - utilitario deportivo 4x2',
            'description': 'TOYOTA FORTUNER [2] [FL] 2.7L SRV TP 2700CC 7AB 4X2 TC',
            'cf_code': '09035028',
            'ch_code': '09006175',
            'insured_value': '$243,500.000'
        },
        {
            'reference_name': 'Fortuner [2] [fl] - utilitario deportivo 4x2',
            'description': 'TOYOTA FORTUNER [2] [FL] 2.7L SR5 TP 2700CC 5AB 4X2 TC',
            'cf_code': '09035029',
            'ch_code': '09006176',
            'insured_value': '$235,200.000'
        },
        {
            'reference_name': 'Fortuner [3] - utilitario deportivo 4x2',
            'description': 'TOYOTA FORTUNER [3] 2.8L SRV TD 2800CC 7AB 4X2 TC',
            'cf_code': '09035030',
            'ch_code': '09006177',
            'insured_value': '$265,300.000'
        },
        {
            'reference_name': 'Fortuner [3] - utilitario deportivo 4x4',
            'description': 'TOYOTA FORTUNER [3] 2.8L SRV TD 2800CC 7AB 4X4 TC',
            'cf_code': '09035032',
            'ch_code': '09006179',
            'insured_value': '$285,100.000'
        }
    ]
    
    selected = show_fasecolda_selection_dialog(test_options)
    if selected is not None:
        print(f"Opción seleccionada: {selected + 1}")
        print(f"Datos: {test_options[selected]}")
    else:
        print("Selección cancelada")
