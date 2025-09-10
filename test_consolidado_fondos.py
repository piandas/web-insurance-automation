#!/usr/bin/env python3
"""
Script de prueba para generar consolidados con plantillas de fondos.

Este script crea datos de ejemplo y genera consolidados usando las nuevas
funcionalidades de plantillas para diferentes fondos.
"""

import sys
from pathlib import Path

# Añadir el directorio del proyecto al path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Importar directamente desde src
from src.config.client_config import ClientConfig
from src.consolidation.cotizacion_consolidator import CotizacionConsolidator
from src.consolidation.template_handler import TemplateHandler

def setup_example_data():
    """Configura datos de ejemplo para las pruebas."""
    
    # Datos de ejemplo del cliente
    example_client_data = {
        'client_document_number': '71750823',
        'client_first_name': 'SERGIO',
        'client_second_name': 'ALEXIS',
        'client_first_lastname': 'AREIZA',
        'client_second_lastname': 'LOAIZA',
        'client_birth_date': '1974-07-06',
        'client_gender': 'M',
        'client_city': 'MEDELLIN',
        'client_department': 'ANTIOQUIA',
        'vehicle_plate': 'GEN294',
        'vehicle_model_year': '2026',
        'vehicle_brand': 'MAZDA',
        'vehicle_reference': 'CX-50 GRAND TOURING',
        'vehicle_full_reference': 'MAZDA CX-50 GRAND TOURING',
        'vehicle_state': 'Nuevo',
        'vehicle_insured_value': '95000000',  # 95 millones
        'manual_cf_code': '20900024001',
        'manual_ch_code': '20900024001',
        'policy_number': '040007325677',
        'policy_number_allianz': '23541048',
        'selected_fondo': 'EPM'  # Cambiaremos este para probar diferentes fondos
    }
    
    # Cargar datos en ClientConfig
    ClientConfig.load_client_data(example_client_data)
    
    return example_client_data

def create_example_plans():
    """Crea planes de ejemplo para las aseguradoras."""
    
    # Planes de ejemplo de Sura
    sura_plans = {
        'Plan Autos Global': '850.000',
        'Plan Autos Clasico': '720.000',
        'Pérdida Parcial 10-1 SMLMV': '650.000'
    }
    
    # Planes de ejemplo de Allianz
    allianz_plans = {
        'Autos Esencial': '780.000',
        'Autos Plus': '920.000',
        'Autos Llave en Mano': '1.150.000',
        'Autos Esencial + Totales': '2.850.000'
    }
    
    # Planes calculados de Bolívar y Solidaria
    bolivar_solidaria_plans = {
        'Bolívar': '890.000',
        'Bolívar Prorrateado': '820.000',
        'Solidaria': '760.000',
        'Solidaria Prorrateado': '700.000'
    }
    
    return sura_plans, allianz_plans, bolivar_solidaria_plans

def test_consolidado_with_fondo(fondo_name):
    """
    Prueba la generación de consolidado con un fondo específico.
    
    Args:
        fondo_name (str): Nombre del fondo a probar
    """
    print(f"\n🧪 Probando consolidado con fondo: {fondo_name}")
    print("=" * 60)
    
    try:
        # Configurar datos de ejemplo
        client_data = setup_example_data()
        
        # Actualizar el fondo seleccionado
        client_data['selected_fondo'] = fondo_name
        ClientConfig.load_client_data(client_data)
        
        # Crear planes de ejemplo
        sura_plans, allianz_plans, bolivar_solidaria_plans = create_example_plans()
        
        # Mostrar información de configuración
        print(f"👤 Cliente: {ClientConfig.CLIENT_FIRST_NAME} {ClientConfig.CLIENT_FIRST_LASTNAME}")
        print(f"🚗 Vehículo: {ClientConfig.VEHICLE_BRAND} {ClientConfig.VEHICLE_REFERENCE}")
        print(f"📋 Placa: {ClientConfig.VEHICLE_PLATE}")
        print(f"💰 Valor Asegurado: ${ClientConfig.VEHICLE_INSURED_VALUE}")
        print(f"🏢 Fondo Seleccionado: {fondo_name}")
        
        # Crear consolidador
        consolidator = CotizacionConsolidator()
        
        # Extraer datos de Sura (configuración actual)
        sura_data = consolidator.extract_sura_data()
        
        # Generar consolidado
        print(f"\n📊 Generando consolidado...")
        excel_path = consolidator.create_excel_report(
            sura_data, 
            sura_plans, 
            allianz_plans, 
            bolivar_solidaria_plans
        )
        
        print(f"✅ Consolidado generado exitosamente:")
        print(f"📁 Archivo: {excel_path}")
        
        return excel_path
        
    except Exception as e:
        print(f"❌ Error generando consolidado para {fondo_name}: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_template_handler():
    """Prueba el TemplateHandler para mostrar información disponible."""
    print("\n🔍 Información del TemplateHandler")
    print("=" * 60)
    
    try:
        template_handler = TemplateHandler()
        
        # Mostrar fondos disponibles
        available_fondos = template_handler.get_available_fondos()
        print(f"📋 Fondos con plantillas disponibles: {available_fondos}")
        
        # Mostrar plantillas encontradas
        print(f"\n📄 Plantillas encontradas:")
        for fondo, template_file in template_handler.template_files.items():
            print(f"  • {fondo}: {template_file}")
        
        # Mostrar logos encontrados
        print(f"\n🎨 Logos encontrados:")
        for fondo, logo_file in template_handler.logo_files.items():
            print(f"  • {fondo}: {logo_file}")
            
    except Exception as e:
        print(f"❌ Error en TemplateHandler: {e}")

def main():
    """Función principal del script de prueba."""
    print("🧪 SCRIPT DE PRUEBA - CONSOLIDADOS CON FONDOS")
    print("=" * 80)
    
    # Probar TemplateHandler
    test_template_handler()
    
    # Obtener fondos disponibles para probar
    try:
        template_handler = TemplateHandler()
        available_fondos = template_handler.get_available_fondos()
        
        if not available_fondos:
            print("\n⚠️ No se encontraron fondos con plantillas disponibles")
            print("📝 Probando con formato estándar...")
            available_fondos = ['FORMATO_ESTANDAR']
        
        # Probar cada fondo disponible
        generated_files = []
        for fondo in available_fondos:
            excel_path = test_consolidado_with_fondo(fondo)
            if excel_path:
                generated_files.append(excel_path)
        
        # También probar con un fondo que no tenga plantilla para verificar fallback
        print(f"\n🧪 Probando fallback con fondo sin plantilla...")
        fallback_path = test_consolidado_with_fondo('FONDO_INEXISTENTE')
        if fallback_path:
            generated_files.append(fallback_path)
        
        # Resumen final
        print(f"\n📋 RESUMEN DE ARCHIVOS GENERADOS")
        print("=" * 60)
        if generated_files:
            for i, file_path in enumerate(generated_files, 1):
                print(f"{i}. {file_path}")
            print(f"\n✅ Total de archivos generados: {len(generated_files)}")
        else:
            print("❌ No se generaron archivos")
            
    except Exception as e:
        print(f"❌ Error en función principal: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
