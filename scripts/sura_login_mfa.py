"""
Script independiente para manejo de login y MFA de Sura.

Este script se encarga únicamente de:
1. Abrir navegador y hacer login automáticamente
2. Si detecta MFA, marcar automáticamente los 8 días
3. Esperar indefinidamente hasta que el usuario meta el código
4. Completar automáticamente y cerrar

Al final queda el perfil guardado para usar en automatizaciones futuras.
"""

import asyncio
import sys
import os
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk

# Agregar la ruta del proyecto al path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.companies.sura.sura_automation import SuraAutomation
from src.config.sura_config import SuraConfig


class SuraMFAWindow:
    """Ventana simple para login MFA de Sura - Sin límites de tiempo."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Login MFA - Sura")
        self.root.geometry("400x200")
        self.root.resizable(False, False)
        
        # Mantener ventana al frente
        self.root.attributes("-topmost", True)
        
        # Centrar ventana
        self.center_window()
        
        # Variables
        self.automation = None
        self.processo_activo = False
        self.mfa_detectado = False
        
        # Configurar interfaz
        self.setup_ui()
        
        # Configurar cierre
        self.root.protocol("WM_DELETE_WINDOW", self.cancelar)
        
        # Iniciar automáticamente
        self.root.after(100, self.iniciar_automaticamente)
    
    def center_window(self):
        """Centra la ventana en la pantalla."""
        self.root.update_idletasks()
        width = 400
        height = 200
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
    
    def setup_ui(self):
        """Configura la interfaz de usuario."""
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configurar grid
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        
        # Título
        title_label = ttk.Label(
            main_frame, 
            text="🔐 Verificación MFA Sura", 
            font=('Arial', 14, 'bold')
        )
        title_label.grid(row=0, column=0, pady=(0, 20))
        
        # Estado actual
        self.status_label = ttk.Label(
            main_frame,
            text="Iniciando verificación...",
            font=('Arial', 10),
            foreground="blue"
        )
        self.status_label.grid(row=1, column=0, pady=(0, 20))
        
        # Botón cerrar
        self.cerrar_btn = ttk.Button(
            main_frame,
            text="❌ Cancelar",
            command=self.cancelar,
            width=15
        )
        self.cerrar_btn.grid(row=2, column=0)
    
    def iniciar_automaticamente(self):
        """Inicia automáticamente el proceso."""
        if self.processo_activo:
            return
        
        self.processo_activo = True
        self.actualizar_estado("🔄 Abriendo navegador...", "blue")
        
        # Ejecutar en hilo separado
        import threading
        thread = threading.Thread(target=self.ejecutar_login_thread, daemon=True)
        thread.start()
    
    def ejecutar_login_thread(self):
        """Ejecuta el login en un hilo separado."""
        try:
            # Crear nuevo loop para este hilo
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Ejecutar el proceso
            resultado = loop.run_until_complete(self.ejecutar_login_async())
            
            # Programar actualización de UI en el hilo principal
            self.root.after(0, lambda: self.login_completado(resultado))
            
        except Exception as e:
            self.root.after(0, lambda: self.error_en_login(str(e)))
    
    async def ejecutar_login_async(self):
        """Ejecuta el proceso de verificación completo."""
        try:
            # Crear instancia de automatización (con ventana visible)
            config = SuraConfig()
            self.automation = SuraAutomation(
                usuario=config.USUARIO,
                contrasena=config.CONTRASENA,
                headless=False  # Mostrar ventana siempre
            )
            
            # Lanzar navegador
            if not await self.automation.launch():
                return {"success": False, "message": "Error abriendo navegador"}
            
            self.root.after(0, lambda: self.actualizar_estado("🔍 Verificando estado...", "blue"))
            
            # Navegar a login
            if not await self.automation.login_page.navigate_to_login():
                return {"success": False, "message": "Error navegando a página de login"}
            
            # Verificar si ya está logueado
            current_url = self.automation.page.url
            if current_url.startswith("https://asesores.segurossura.com.co") and "login.sura.com" not in current_url:
                return {"success": True, "message": "Ya estaba logueado - perfil listo", "was_logged": True}
            
            # Si no está logueado, proceder con el login
            self.root.after(0, lambda: self.actualizar_estado("🔑 Haciendo login...", "blue"))
            
            if not await self.automation.login_page.select_tipo_documento():
                return {"success": False, "message": "Error seleccionando tipo de documento"}
            
            if not await self.automation.login_page.fill_credentials(config.USUARIO, config.CONTRASENA):
                return {"success": False, "message": "Error llenando credenciales"}
            
            if not await self.automation.login_page.submit_login(config.USUARIO, config.CONTRASENA):
                return {"success": False, "message": "Error enviando formulario de login"}
            
            # Verificar el resultado del login
            await self.automation.page.wait_for_timeout(3000)
            current_url = self.automation.page.url
            
            if "mfa/process" in current_url:
                # MFA detectado - marcar automáticamente los 8 días y esperar código
                self.mfa_detectado = True
                self.root.after(0, lambda: self.actualizar_estado("🔐 MFA detectado - Complete en el navegador", "orange"))
                
                # Marcar automáticamente "recordar dispositivo" sin esperar
                await self.marcar_recordar_dispositivo()
                
                # Esperar indefinidamente hasta que se complete el MFA
                mfa_completed = await self.esperar_mfa_indefinidamente()
                
                if mfa_completed:
                    return {"success": True, "message": "Perfil MFA configurado exitosamente"}
                else:
                    return {"success": False, "message": "Tiempo límite alcanzado o proceso cancelado", "timeout": True}
            
            elif current_url.startswith("https://asesores.segurossura.com.co"):
                return {"success": True, "message": "Login completado - perfil listo"}
            
            else:
                return {"success": False, "message": f"Login falló - URL inesperada"}
        
        except Exception as e:
            return {"success": False, "message": f"Error: {str(e)}"}
    
    async def marcar_recordar_dispositivo(self):
        """Marca automáticamente el checkbox de recordar dispositivo."""
        try:
            # Esperar a que aparezca el formulario MFA
            await self.automation.page.wait_for_selector('input[name="code"]', timeout=10000)
            
            # Buscar y marcar automáticamente el checkbox
            remember_checkbox = 'span.checkmark.checkmark-checkBox'
            try:
                await self.automation.page.click(remember_checkbox, timeout=3000)
                print("✅ Checkbox 'recordar dispositivo' marcado automáticamente")
            except:
                # Si no encuentra el checkbox específico, buscar alternativas
                checkbox_alternatives = [
                    'input[type="checkbox"]',
                    'label:has-text("recordar")',
                    'label:has-text("8 días")',
                    '.checkbox'
                ]
                
                for selector in checkbox_alternatives:
                    try:
                        await self.automation.page.click(selector, timeout=2000)
                        print(f"✅ Checkbox marcado con selector alternativo: {selector}")
                        break
                    except:
                        continue
        except Exception as e:
            print(f"⚠️ No se pudo marcar automáticamente el checkbox: {e}")
    
    async def esperar_mfa_indefinidamente(self):
        """Espera hasta 10 minutos para que el usuario complete el MFA."""
        print("🔐 Esperando que el usuario complete el MFA (máximo 10 minutos)...")
        
        max_time = 600  # 10 minutos en segundos
        check_interval = 2  # Verificar cada 2 segundos
        elapsed_time = 0
        
        while elapsed_time < max_time:
            try:
                # Verificar cada 2 segundos si el MFA fue completado
                await asyncio.sleep(check_interval)
                elapsed_time += check_interval
                
                # Verificar si la ventana fue cerrada (proceso cancelado)
                if not self.processo_activo:
                    return False
                
                current_url = self.automation.page.url
                
                # Si ya no está en la página de MFA, el proceso fue exitoso
                if "mfa/process" not in current_url and "asesores.segurossura.com.co" in current_url:
                    print("✅ MFA completado exitosamente")
                    return True
                
                # Verificar si hubo error o redirección inesperada
                if "login.sura.com" in current_url and "mfa" not in current_url:
                    print("⚠️ Redirigido de vuelta al login")
                    return False
                
                # Mostrar progreso cada 2 minutos
                if elapsed_time % 120 == 0 and elapsed_time > 0:
                    minutes_elapsed = elapsed_time // 60
                    remaining = (max_time - elapsed_time) // 60
                    print(f"⏳ MFA en progreso... {minutes_elapsed} min transcurridos, {remaining} min restantes")
                    self.root.after(0, lambda m=minutes_elapsed, r=remaining: 
                                   self.actualizar_estado(f"🔐 MFA en progreso... {m} min transcurridos", "orange"))
                
            except Exception as e:
                print(f"Error verificando MFA: {e}")
                await asyncio.sleep(5)  # Esperar más tiempo si hay error
                elapsed_time += 5
                continue
        
        # Si llegamos aquí, se cumplió el tiempo límite
        print("⏰ Tiempo límite de 10 minutos alcanzado")
        self.root.after(0, lambda: self.actualizar_estado("⏰ Tiempo límite alcanzado", "red"))
        return False
    
    def actualizar_estado(self, mensaje, color="black"):
        """Actualiza el estado mostrado."""
        self.status_label.config(text=mensaje, foreground=color)
    
    def login_completado(self, resultado):
        """Maneja la finalización del proceso."""
        self.processo_activo = False
        
        # Cerrar navegador
        if self.automation:
            try:
                import threading
                def cerrar_async():
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(self.automation.close())
                
                threading.Thread(target=cerrar_async, daemon=True).start()
            except:
                pass
        
        if resultado["success"]:
            if resultado.get("was_logged"):
                self.actualizar_estado("✅ Perfil ya está listo", "green")
                messagebox.showinfo("Información", 
                    "✅ La sesión ya estaba activa en Sura.\n\n"
                    "El perfil está listo para automatizaciones.")
            else:
                self.actualizar_estado("✅ Perfil MFA configurado", "green")
                messagebox.showinfo("Éxito", 
                    "✅ Perfil MFA configurado exitosamente.\n\n"
                    "Las automatizaciones funcionarán sin interrupciones.")
            
            # Cerrar ventana después de 1 segundo
            self.root.after(1000, self.root.destroy)
        else:
            # Verificar si fue por timeout
            if resultado.get("timeout"):
                self.actualizar_estado("⏰ Tiempo límite alcanzado - Cerrando...", "red")
                messagebox.showwarning("Tiempo agotado", 
                    "⏰ Se agotaron los 10 minutos para completar el MFA.\n\n"
                    "La aplicación se cerrará automáticamente.")
                # Cerrar inmediatamente por timeout
                self.root.after(2000, self.root.destroy)
            else:
                self.actualizar_estado("❌ Error en proceso", "red")
                messagebox.showerror("Error", f"❌ {resultado['message']}")
    
    def error_en_login(self, error):
        """Maneja errores durante el proceso."""
        self.processo_activo = False
        self.actualizar_estado(f"❌ Error", "red")
        
        # Cerrar navegador si existe
        if self.automation:
            try:
                import threading
                def cerrar_async():
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(self.automation.close())
                
                threading.Thread(target=cerrar_async, daemon=True).start()
            except:
                pass
        
        messagebox.showerror("Error", f"❌ Error durante el proceso:\n\n{error}")
    
    def cancelar(self):
        """Cancela el proceso y cierra todo."""
        self.processo_activo = False
        
        # Cerrar navegador si existe
        if self.automation:
            try:
                import threading
                def cerrar_async():
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(self.automation.close())
                
                threading.Thread(target=cerrar_async, daemon=True).start()
            except:
                pass
        
        self.root.destroy()
    
    def run(self):
        """Ejecuta la ventana."""
        self.root.mainloop()


def main():
    """Función principal."""
    try:
        app = SuraMFAWindow()
        app.run()
    except Exception as e:
        print(f"Error: {e}")
        messagebox.showerror("Error", f"Error iniciando aplicación: {e}")


if __name__ == "__main__":
    main()
