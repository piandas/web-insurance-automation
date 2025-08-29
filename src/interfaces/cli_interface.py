"""Interfaz de línea de comandos para el sistema."""

import argparse
import asyncio
import sys
from typing import List, Optional

from ..core.automation_manager import AutomationManager
from ..factory.automation_factory import AutomationFactory
from ..consolidation.cotizacion_consolidator import CotizacionConsolidator

class CLIInterface:
    """Interfaz de línea de comandos para ejecutar automatizaciones."""
    
    def __init__(self):
        self.manager = AutomationManager()
    
    def create_parser(self) -> argparse.ArgumentParser:
        """Crea el parser de argumentos de línea de comandos."""
        parser = argparse.ArgumentParser(
            description='Sistema de automatización de cotizaciones de seguros',
            formatter_class=argparse.RawDescriptionHelpFormatter,            epilog="""
Ejemplos de uso:
  # Ejecutar solo Allianz
  python -m src.interfaces.cli_interface --companies allianz
  python -m src.interfaces.cli_interface --companies sura
  
  # Ejecutar ambas compañías en paralelo
  python -m src.interfaces.cli_interface --companies allianz sura --parallel
  
  # Ejecutar en modo headless
  python -m src.interfaces.cli_interface --companies allianz --headless
  
  # Ejecutar con credenciales específicas
  python -m src.interfaces.cli_interface --companies sura --user mi_usuario --password mi_pass
            """
        )
          # Compañías a ejecutar
        parser.add_argument(
            '--companies', 
            nargs='+', 
            choices=AutomationFactory.get_supported_companies(),
            help='Compañías a ejecutar'
        )
        
        # Modo de ejecución
        parser.add_argument(
            '--parallel', 
            action='store_true',
            help='Ejecutar compañías en paralelo en lugar de secuencial'
        )
        
        # Configuraciones opcionales
        parser.add_argument(
            '--headless',
            action='store_true',
            help='Ejecutar navegadores en modo headless (sin ventana)'
        )
        
        parser.add_argument(
            '--user',
            type=str,
            help='Usuario personalizado (sobrescribe configuración)'
        )
        
        parser.add_argument(
            '--password',
            type=str,
            help='Contraseña personalizada (sobrescribe configuración)'
        )
        
        # Configuraciones de logging
        parser.add_argument(
            '--verbose', '-v',
            action='store_true',
            help='Habilitar logging verbose'
        )
        
        # Lista compañías disponibles
        parser.add_argument(
            '--list-companies',
            action='store_true',
            help='Listar compañías disponibles y salir'
        )
        
        return parser
    
    async def run(self, args: Optional[List[str]] = None) -> int:
        """
        Ejecuta la interfaz CLI.
        
        Args:
            args: Argumentos opcionales (si no se pasan, se usan sys.argv)
            
        Returns:
            Código de salida (0 = éxito, 1 = error)
        """
        parser = self.create_parser()
        
        if args is None:
            args = sys.argv[1:]
        
        # Parse argumentos
        parsed_args = parser.parse_args(args)
          # Manejar comando de listar compañías
        if parsed_args.list_companies:
            print("Compañías disponibles:")
            for company in AutomationFactory.get_supported_companies():
                print(f"  - {company}")
            return 0
        
        # Verificar que se especificaron compañías
        if not parsed_args.companies:
            parser.print_help()
            print("\nError: Debe especificar al menos una compañía usando --companies")
            return 1
        
        # Preparar argumentos para las automatizaciones
        automation_kwargs = {}
        if parsed_args.user:
            automation_kwargs['usuario'] = parsed_args.user
        if parsed_args.password:
            automation_kwargs['contrasena'] = parsed_args.password
        if parsed_args.headless:
            automation_kwargs['headless'] = True  # Modo oculto/minimizado, no verdadero headless
        
        try:
            print(f"🚀 Iniciando automatización para: {', '.join(parsed_args.companies)}")
            print(f"📋 Modo: {'Paralelo' if parsed_args.parallel else 'Secuencial'}")
            
            # Ejecutar automatizaciones
            if parsed_args.parallel:
                results = await self.manager.run_parallel(
                    parsed_args.companies, 
                    **automation_kwargs
                )
            else:
                results = await self.manager.run_sequential(
                    parsed_args.companies, 
                    **automation_kwargs
                )
            
            # Mostrar resultados
            print("\n" + "="*50)
            print("📊 RESULTADOS FINALES:")
            print("="*50)
            
            all_success = True
            for company, success in results.items():
                status = "✅ ÉXITO" if success else "❌ FALLÓ"
                print(f"  {company.upper()}: {status}")
                if not success:
                    all_success = False
            
            if all_success:
                print("\n🎉 ¡TODAS LAS AUTOMATIZACIONES COMPLETADAS EXITOSAMENTE!")
            else:
                print("\n⚠️ Algunas automatizaciones fallaron. Revisa los logs para más detalles.")
                
            # Ejecutar consolidación si se solicitaron ambas compañías (exitosas o no)
            if len(parsed_args.companies) >= 2 and 'sura' in parsed_args.companies and 'allianz' in parsed_args.companies:
                print("\n" + "="*50)
                print("📋 INICIANDO CONSOLIDACIÓN DE COTIZACIONES...")
                if not all_success:
                    print("⚠️  Generando consolidado con datos parciales (fallos marcados como 'FALLÓ')")
                print("="*50)
                
                try:
                    consolidator = CotizacionConsolidator()
                    consolidation_success = consolidator.consolidate_with_failures(results)
                    
                    if consolidation_success:
                        print("\n✅ ¡CONSOLIDACIÓN COMPLETADA EXITOSAMENTE!")
                        print("📄 El archivo Excel consolidado ha sido creado en la carpeta 'Consolidados'")
                        if not all_success:
                            print("⚠️  Nota: Algunas aseguradoras aparecen como 'FALLÓ' debido a errores en sus automatizaciones")
                    else:
                        print("\n⚠️ Error durante la consolidación. Revisa los logs para más detalles.")
                        
                except Exception as e:
                    print(f"\n❌ Error inesperado durante la consolidación: {e}")
            
            return 0 if all_success else 1
                
        except KeyboardInterrupt:
            print("\n⚠️ Proceso interrumpido por el usuario")
            await self.manager.stop_all()
            return 1
        except Exception as e:
            print(f"\n❌ Error inesperado: {e}")
            await self.manager.stop_all()
            return 1

async def main():
    """Función principal para la interfaz CLI."""
    cli = CLIInterface()
    exit_code = await cli.run()
    sys.exit(exit_code)

if __name__ == "__main__":
    asyncio.run(main())
