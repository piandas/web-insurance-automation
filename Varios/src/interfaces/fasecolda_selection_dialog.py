"""
Diálogo de selección de opciones Fasecolda para la interfaz GUI.
"""
import tkinter as tk
from tkinter import ttk
from typing import List, Dict, Optional


class FasecoldaSelectionDialog:
    """Diálogo para seleccionar una opción de múltiples resultados Fasecolda."""
    
    def __init__(self, options: List[Dict], brand: str, reference: str):
        """
        Inicializa el diálogo de selección.
        
        Args:
            options: Lista de opciones encontradas
            brand: Marca del vehículo
            reference: Referencia base del vehículo
        """
        self.options = options
        self.brand = brand
        self.reference = reference
        self.selected_option = None
        self.window = None
        
    def show(self) -> Optional[Dict]:
        """
        Muestra el diálogo y retorna la opción seleccionada.
        
        Returns:
            Diccionario con la opción seleccionada o None si se cancela
        """
        # Verificar si existe un root de tkinter, si no, crear uno oculto
        root_created = False
        try:
            # Intentar acceder al root existente
            if tk._default_root is None:
                root = tk.Tk()
                root.withdraw()  # Ocultar ventana root
                root_created = True
        except:
            root = tk.Tk()
            root.withdraw()  # Ocultar ventana root
            root_created = True
        
        try:
            self._create_window()
            self._setup_ui()
            
            # Mostrar ventana modal
            self.window.grab_set()
            self.window.focus_force()
            self.window.wait_window()
            
            return self.selected_option
            
        finally:
            # Limpiar root si lo creamos nosotros
            if root_created and 'root' in locals():
                try:
                    root.destroy()
                except:
                    pass
    
    def _create_window(self):
        """Crea la ventana principal del diálogo con tamaño dinámico y centrada."""
        # Crear ventana independiente SIN crear root extra
        self.window = tk.Toplevel()
        self.window.title("🔍 Seleccionar opción Fasecolda")
        
        # Calcular tamaño dinámico basado en número de opciones
        num_options = len(self.options)
        base_height = 250  # Altura base reducida (sin botones)
        row_height = 25    # Altura por fila
        max_height = 700   # Altura máxima reducida
        min_height = 350   # Altura mínima reducida
        
        calculated_height = base_height + (num_options * row_height)
        window_height = max(min_height, min(calculated_height, max_height))
        
        # Ancho dinámico pero más compacto
        window_width = 1100
        
        # Centrar la ventana en la pantalla
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)
        
        self.window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.window.resizable(True, True)
        
        # Configurar para que se cierre correctamente
        self.window.protocol("WM_DELETE_WINDOW", self._cancel)
        
        # Asegurar que la ventana esté en primer plano
        self.window.lift()
        self.window.attributes('-topmost', True)
        self.window.after(100, lambda: self.window.attributes('-topmost', False))
        
        # Configurar para cerrar con ESC
        self.window.bind('<Escape>', lambda e: self._cancel())
    
    def _setup_ui(self):
        """Configura la interfaz de usuario del diálogo con layout optimizado."""
        # Frame principal con padding reducido
        main_frame = ttk.Frame(self.window, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título más compacto
        title_label = ttk.Label(
            main_frame, 
            text=f"Referencias encontradas para {self.brand} {self.reference}",
            font=("Arial", 12, "bold")
        )
        title_label.pack(pady=(0, 10))
        
        # Información más compacta
        info_label = ttk.Label(
            main_frame,
            text=f"🎯 {len(self.options)} opciones disponibles. Doble clic para seleccionar:",
            font=("Arial", 9)
        )
        info_label.pack(pady=(0, 10))
        
        # Frame para la lista y scrollbar
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # Crear Treeview con columnas reordenadas
        columns = ('Num', 'Referencia', 'Descripción', 'Valor', 'CF', 'CH')
        
        # Ajustar altura dinámicamente
        num_options = len(self.options)
        tree_height = min(max(8, num_options + 2), 20)  # Entre 8 y 20 filas
        
        self.tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=tree_height)
        
        # Configurar encabezados
        self.tree.heading('Num', text='#')
        self.tree.heading('Referencia', text='Referencia')
        self.tree.heading('Descripción', text='Descripción Completa')
        self.tree.heading('Valor', text='💰 Valor Asegurado')
        self.tree.heading('CF', text='🏷️ CF')
        self.tree.heading('CH', text='🏷️ CH')
        
        # Anchos de columnas optimizados
        self.tree.column('Num', width=50, minwidth=40, anchor='center')
        self.tree.column('Referencia', width=180, minwidth=120)
        self.tree.column('Descripción', width=350, minwidth=250)
        self.tree.column('Valor', width=140, minwidth=120, anchor='e')
        self.tree.column('CF', width=90, minwidth=70, anchor='center')
        self.tree.column('CH', width=90, minwidth=70, anchor='center')
        
        # Scrollbar vertical
        v_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=v_scrollbar.set)
        
        # Scrollbar horizontal
        h_scrollbar = ttk.Scrollbar(list_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(xscrollcommand=h_scrollbar.set)
        
        # Pack treeview y scrollbars
        self.tree.grid(row=0, column=0, sticky='nsew')
        v_scrollbar.grid(row=0, column=1, sticky='ns')
        h_scrollbar.grid(row=1, column=0, sticky='ew')
        
        # Configurar expansión
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)
        
        # Bind para doble clic
        self.tree.bind('<Double-1>', self._on_double_click)
        
        # Llenar datos
        self._populate_tree()
        
        # Solo información sobre cómo usar (sin botones)
        info_frame = ttk.Frame(main_frame)
        info_frame.pack(fill=tk.X, pady=(15, 10))
        
        ttk.Label(
            info_frame,
            text="💡 Haga doble clic en una opción para seleccionarla • Presione ESC para cancelar",
            font=("Arial", 10, "italic"),
            foreground="blue",
            anchor="center"
        ).pack(expand=True)
    
    def _populate_tree(self):
        """Llena el TreeView con las opciones disponibles con mejor estilo y columnas reordenadas."""
        current_reference = ""
        
        for option in self.options:
            # Verificar si es una nueva referencia
            if option['reference_group'] != current_reference:
                current_reference = option['reference_group']
                # Insertar encabezado de referencia con estilo (SIN "REFERENCIA:")
                header_id = self.tree.insert('', 'end', values=(
                    '',
                    f"📁 {current_reference}",  # Solo la referencia, sin prefijo
                    '',
                    '',
                    '',
                    ''
                ), tags=('header',))
            
            # Insertar opción con columnas reordenadas: Num, Referencia, Descripción, Valor, CF, CH
            option_id = self.tree.insert('', 'end', values=(
                option['option_number'],
                "",  # Referencia vacía para las opciones individuales
                option['description'],
                option['insured_value'],  # Valor asegurado en 4ta posición
                option['cf_code'],        # CF en 5ta posición
                option['ch_code'] or 'N/A'  # CH en 6ta posición
            ), tags=('option',))
        
        # Configurar estilos para las filas
        self.tree.tag_configure('header', background='#E8F4FD', foreground='#1f5582', font=('Arial', 10, 'bold'))
        self.tree.tag_configure('option', background='white', foreground='black', font=('Arial', 9))
        
        # Configurar colores alternados para opciones
        for i, child in enumerate(self.tree.get_children()):
            if self.tree.item(child)['tags'] == ('option',):
                if i % 2 == 0:
                    self.tree.set(child, tags=('option_even',))
                else:
                    self.tree.set(child, tags=('option_odd',))
        
        self.tree.tag_configure('option_even', background='#F8F9FA', font=('Arial', 9))
        self.tree.tag_configure('option_odd', background='white', font=('Arial', 9))
    
    def _on_double_click(self, event):
        """Maneja el doble clic para seleccionar automáticamente."""
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            values = item['values']
            
            # Verificar que sea una opción válida (tiene número)
            if values and values[0] and str(values[0]).isdigit():
                option_num = int(values[0])
                
                # Buscar la opción seleccionada
                for option in self.options:
                    if option['option_number'] == option_num:
                        self.selected_option = option
                        self.window.destroy()
                        return
    
    def _cancel(self):
        """Cancela la selección."""
        self.selected_option = None
        self.window.destroy()


def main():
    """Función de prueba."""
    # Datos de ejemplo
    test_options = [
        {
            'option_number': 1,
            'cf_code': '09035028',
            'ch_code': '09006175',
            'description': 'TOYOTA FORTUNER [2] [FL] 2.7L SRV TP 2700CC 7AB 4X2 TC',
            'insured_value': '$243,500.000',
            'reference_group': 'Fortuner [2] [fl] - utilitario deportivo 4x2'
        },
        {
            'option_number': 2,
            'cf_code': '09035029',
            'ch_code': '09006176',
            'description': 'TOYOTA FORTUNER [2] [FL] 2.7L SR5 TP 2700CC 5AB 4X2 TC',
            'insured_value': '$235,200.000',
            'reference_group': 'Fortuner [2] [fl] - utilitario deportivo 4x2'
        },
        {
            'option_number': 3,
            'cf_code': '09035030',
            'ch_code': '09006177',
            'description': 'TOYOTA FORTUNER [3] 2.8L SRV TD 2800CC 7AB 4X2 TC',
            'insured_value': '$265,300.000',
            'reference_group': 'Fortuner [3] - utilitario deportivo 4x2'
        }
    ]
    
    root = tk.Tk()
    root.withdraw()  # Ocultar ventana principal
    
    dialog = FasecoldaSelectionDialog(test_options, "Toyota", "Fortuner")
    result = dialog.show()
    
    if result:
        print(f"Opción seleccionada: {result}")
    else:
        print("Selección cancelada")
    
    root.destroy()


if __name__ == "__main__":
    main()
