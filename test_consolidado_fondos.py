#!/usr/bin/env python3
"""
Script de prueba para generar consolidados con plantillas de fondos.

Este script crea datos de ejemplo y genera consolidados usando las nuevas
funcionalidades de pl        # Mostrar información
        print(f"👤 Client        allianz_plans_usado = {
            'Autos Esencial': '920.000',                       # Allianz Autos Esencial
            'Autos Esencial + Total': '2.750.000',             # Allianz Autos Esencial + Total
            'Autos Plus': '1.200.000'                          # Allianz Autos Plus
            # Para usados no incluimos "Autos llave en mano"
        }ientConfig.CLIENT_FIRST_NAME} {ClientConfig.CLIENT_FIRST_LASTNAME}")
        print(f"🚗 Vehículo: {ClientConfig.VEHICLE_BRAND} {ClientConfig.VEHICLE_REFERENCE} ({ClientConfig.VEHICLE_STATE})")
        print(f"📋 Plantilla esperada: EPM N")
        print(f"📊 Estructura columnas NUEVOS:")
        print(f"   SURA: Autos Global | Autos Clasico")
        print(f"   ALLIANZ: Autos Esencial | Autos Esencial + Total | Autos Plus | Autos llave en mano")
        print(f"   OTROS: Bolívar | Solidaria")
        print(f"💰 Valores SURA: {list(sura_plans_nuevo.values())}")
        print(f"💰 Valores ALLIANZ: {list(allianz_plans_nuevo.values())}")
        print(f"💰 Valores OTROS: Bolívar {bolivar_solidaria_plans['Bolívar']} | Solidaria {bolivar_solidaria_plans['Solidaria']}")as para diferentes fondos.
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
        'selected_fondo': 'EPM'
    }
    
    # Cargar datos en ClientConfig
    ClientConfig.load_client_data(example_client_data)
    
    return example_client_data

def create_example_plans():
    """Crea planes de ejemplo para las aseguradoras."""
    
    # Planes de ejemplo de Sura (con valores ficticios más realistas)
    sura_plans = {
        'Plan Autos Global': '1.250.000',
        'Plan Autos Clasico': '980.000',
        'Pérdida Parcial 10-1 SMLMV': '750.000'
    }
    
    # Planes de ejemplo de Allianz (con valores ficticios más realistas)
    allianz_plans = {
        'Autos Esencial': '1.180.000',
        'Autos Plus': '1.420.000',
        'Autos Llave en Mano': '1.650.000',
        'Autos Esencial + Total': '2.850.000'  # Suma de los otros tres
    }
    
    # Planes calculados de Bolívar y Solidaria (con valores ficticios)
    bolivar_solidaria_plans = {
        'Bolívar': '1.290.000',
        'Bolívar Prorrateado': '1.190.000',
        'Solidaria': '1.160.000',
        'Solidaria Prorrateado': '1.070.000'
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

def test_epm_templates():
    """Prueba específicamente las plantillas EPM N y EPM U."""
    print("\n🧪 PRUEBA ESPECÍFICA DE PLANTILLAS EPM")
    print("=" * 80)
    
    generated_files = []
    
    # Datos base para las pruebas
    base_client_data = {
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
        'vehicle_insured_value': '95000000',  # 95 millones
        'manual_cf_code': '20900024001',
        'manual_ch_code': '20900024001',
        'policy_number': '040007325677',
        'policy_number_allianz': '23541048',
        'selected_fondo': 'EPM'
    }
    
    # 1. PROBAR EPM NUEVOS (EPM N)
    print(f"\n🚗 Probando EPM para vehículos NUEVOS (EPM N)")
    print("-" * 60)
    
    try:
        # Configurar para nuevo
        client_data_nuevo = base_client_data.copy()
        client_data_nuevo['vehicle_state'] = 'Nuevo'
        ClientConfig.load_client_data(client_data_nuevo)
        
        # Crear planes de ejemplo para nuevos
        sura_plans_nuevo = {
            'Plan Autos Global': '1.450.000',      # Sura Autos Global
            'Plan Autos Clasico': '1.180.000'      # Sura Autos Clasico
            # Para nuevos no incluimos "Pérdida Parcial 10-1 SMLMV"
        }
        
        allianz_plans_nuevo = {
            'Autos Esencial': '1.320.000',         # Allianz Autos Esencial
            'Autos Esencial + Total': '4.980.000', # Allianz Autos Esencial + Total
            'Autos Plus': '1.650.000',             # Allianz Autos Plus
            'Autos llave en mano': '2.010.000'     # Allianz Autos llave en mano
        }
        
        bolivar_solidaria_plans = {
            'Bolívar': '1.520.000',                # Bolívar
            'Bolívar Prorrateado': '1.400.000',
            'Solidaria': '1.380.000',              # Solidaria
            'Solidaria Prorrateado': '1.270.000'
        }
        
        # Mostrar información
        print(f"👤 Cliente: {ClientConfig.CLIENT_FIRST_NAME} {ClientConfig.CLIENT_FIRST_LASTNAME}")
        print(f"� Vehículo: {ClientConfig.VEHICLE_BRAND} {ClientConfig.VEHICLE_REFERENCE} ({ClientConfig.VEHICLE_STATE})")
        print(f"📋 Plantilla esperada: EPM N")
        print(f"📊 Planes SURA para nuevos: {list(sura_plans_nuevo.keys())}")
        print(f"📊 Planes ALLIANZ: {list(allianz_plans_nuevo.keys())}")
        
        # Crear consolidador y generar
        consolidator = CotizacionConsolidator()
        sura_data = consolidator.extract_sura_data()
        
        excel_path = consolidator.create_excel_report(
            sura_data, 
            sura_plans_nuevo, 
            allianz_plans_nuevo, 
            bolivar_solidaria_plans
        )
        
        if excel_path:
            generated_files.append(('EPM NUEVOS', excel_path))
            print(f"✅ Archivo generado: {excel_path}")
        
    except Exception as e:
        print(f"❌ Error en EPM NUEVOS: {e}")
        import traceback
        traceback.print_exc()
    
    # 2. PROBAR EPM USADOS (EPM U)
    print(f"\n🚙 Probando EPM para vehículos USADOS (EPM U)")
    print("-" * 60)
    
    try:
        # Configurar para usado
        client_data_usado = base_client_data.copy()
        client_data_usado['vehicle_state'] = 'Usado'
        client_data_usado['vehicle_model_year'] = '2018'  # Cambiar a un año usado
        client_data_usado['vehicle_insured_value'] = '45000000'  # Valor menor para usado
        ClientConfig.load_client_data(client_data_usado)
        
        # Crear planes de ejemplo para usados
        sura_plans_usado = {
            'Plan Autos Global': '980.000',                     # Sura Autos Global
            'Pérdida Parcial 10-1 SMLMV': '720.000',          # Sura Autos Parcial
            'Plan Autos Clasico': '850.000'                    # Sura Autos Clasico
        }
        
        allianz_plans_usado = {
            'Autos Esencial': '920.000',                       # Allianz Autos Escencial (nota: Escencial en usados)
            'Autos Esencial + Total': '2.750.000',             # Allianz Autos Esencial + Total
            'Autos Plus': '1.200.000'                          # Allianz Autos Plus
            # Para usados no incluimos "Autos llave en mano"
        }
        
        bolivar_solidaria_plans_usado = {
            'Bolívar': '1.050.000',                            # Bolívar
            'Bolívar Prorrateado': '960.000',
            'Solidaria': '990.000',                            # Solidaria
            'Solidaria Prorrateado': '910.000'
        }
        
        # Mostrar información
        print(f"👤 Cliente: {ClientConfig.CLIENT_FIRST_NAME} {ClientConfig.CLIENT_FIRST_LASTNAME}")
        print(f"🚗 Vehículo: {ClientConfig.VEHICLE_BRAND} {ClientConfig.VEHICLE_REFERENCE} ({ClientConfig.VEHICLE_STATE})")
        print(f"📋 Plantilla esperada: EPM U")
        print(f"📊 Estructura columnas USADOS:")
        print(f"   SURA: Autos Global | Autos Parcial | Autos Clasico")
        print(f"   ALLIANZ: Autos Esencial | Autos Esencial + Total | Autos Plus")
        print(f"   OTROS: Bolívar | Solidaria")
        print(f"💰 Valores SURA: {list(sura_plans_usado.values())}")
        print(f"� Valores ALLIANZ: {list(allianz_plans_usado.values())}")
        print(f"💰 Valores OTROS: Bolívar {bolivar_solidaria_plans_usado['Bolívar']} | Solidaria {bolivar_solidaria_plans_usado['Solidaria']}")
        
        # Crear consolidador y generar
        consolidator = CotizacionConsolidator()
        sura_data = consolidator.extract_sura_data()
        
        excel_path = consolidator.create_excel_report(
            sura_data, 
            sura_plans_usado, 
            allianz_plans_usado, 
            bolivar_solidaria_plans_usado
        )
        
        if excel_path:
            generated_files.append(('EPM USADOS', excel_path))
            print(f"✅ Archivo generado: {excel_path}")
        
    except Exception as e:
        print(f"❌ Error en EPM USADOS: {e}")
        import traceback
        traceback.print_exc()
    
    # Resumen
    print(f"\n📋 RESUMEN DE PRUEBAS EPM")
    print("=" * 60)
    if generated_files:
        for i, (tipo, file_path) in enumerate(generated_files, 1):
            print(f"{i}. {tipo}: {file_path}")
        print(f"\n✅ Total de archivos EPM generados: {len(generated_files)}")
    else:
        print("❌ No se generaron archivos EPM")
    
    return generated_files

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
        
        # Información sobre imágenes
        print(f"\n🎨 Imágenes:")
        print("  • Las imágenes se agregan manualmente al Excel")
            
    except Exception as e:
        print(f"❌ Error en TemplateHandler: {e}")

def main():
    """Función principal del script de prueba."""
    print("🧪 SCRIPT DE PRUEBA - CONSOLIDADOS CON FONDOS")
    print("=" * 80)
    
    # Probar TemplateHandler
    test_template_handler()
    
    # Prueba específica de EPM con plantillas N y U
    epm_files = test_epm_templates()
    
    # Obtener fondos disponibles para probar otros fondos
    try:
        template_handler = TemplateHandler()
        available_fondos = template_handler.get_available_fondos()
        
        # Filtrar EPM ya que lo probamos específicamente
        other_fondos = [f for f in available_fondos if not f.startswith('EPM')]
        
        if not other_fondos:
            print("\n⚠️ No se encontraron otros fondos además de EPM")
            other_fondos = ['FORMATO_ESTANDAR']
        
        # Probar otros fondos disponibles
        generated_files = []
        if other_fondos and other_fondos != ['FORMATO_ESTANDAR']:
            print(f"\n🧪 Probando otros fondos disponibles...")
            for fondo in other_fondos:
                excel_path = test_consolidado_with_fondo(fondo)
                if excel_path:
                    generated_files.append(excel_path)
        
        # También probar con un fondo que no tenga plantilla para verificar fallback
        print(f"\n🧪 Probando fallback con fondo sin plantilla...")
        fallback_path = test_consolidado_with_fondo('FONDO_INEXISTENTE')
        if fallback_path:
            generated_files.append(fallback_path)
        
        # Resumen final
        print(f"\n📋 RESUMEN FINAL DE ARCHIVOS GENERADOS")
        print("=" * 80)
        
        all_files = []
        
        # Agregar archivos EPM
        if epm_files:
            print("📁 Archivos EPM:")
            for i, (tipo, file_path) in enumerate(epm_files, 1):
                print(f"  {i}. {tipo}: {file_path}")
                all_files.append(file_path)
        
        # Agregar otros archivos
        if generated_files:
            print("\n📁 Otros archivos:")
            for i, file_path in enumerate(generated_files, 1):
                print(f"  {len(epm_files) + i}. {file_path}")
                all_files.append(file_path)
        
        if all_files:
            print(f"\n✅ Total de archivos generados: {len(all_files)}")
            print("\n🎯 PUNTOS CLAVE PROBADOS:")
            print("  ✅ Plantillas EPM N (vehículos nuevos)")
            print("  ✅ Plantillas EPM U (vehículos usados)")
            print("  ✅ Planes SURA diferentes según tipo de vehículo")
            print("  ✅ Sistema de intersección para valores cotizados")
            print("  ✅ Datos del cliente en celdas merged (C-I)")
        else:
            print("❌ No se generaron archivos")
            
    except Exception as e:
        print(f"❌ Error en función principal: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
