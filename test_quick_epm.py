#!/usr/bin/env python3
"""
Script de prueba rápida para un solo consolidado EPM nuevos.
"""

import sys
from pathlib import Path

# Añadir el directorio del proyecto al path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Importar directamente desde src
from src.config.client_config import ClientConfig
from src.consolidation.cotizacion_consolidator import CotizacionConsolidator

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

def main():
    """Función principal del script de prueba."""
    print("🧪 PRUEBA RÁPIDA - EPM NUEVOS CON CÁLCULOS ANUALIZADOS")
    print("=" * 80)
    
    try:
        # Configurar datos de ejemplo
        client_data = setup_example_data()
        
        # Crear planes de ejemplo para nuevos
        sura_plans_nuevo = {
            'Plan Autos Global': '1.450.000',      # Sura Autos Global
            'Plan Autos Clasico': '1.180.000'      # Sura Autos Clasico
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
        print(f"🚗 Vehículo: {ClientConfig.VEHICLE_BRAND} {ClientConfig.VEHICLE_REFERENCE} ({ClientConfig.VEHICLE_STATE})")
        print(f"📋 Plantilla esperada: EPM N")
        
        # Crear consolidador
        consolidator = CotizacionConsolidator()
        
        # Extraer datos de Sura (configuración actual)
        sura_data = consolidator.extract_sura_data()
        
        # Generar consolidado
        print(f"\n📊 Generando consolidado...")
        excel_path = consolidator.create_excel_report(
            sura_data, 
            sura_plans_nuevo, 
            allianz_plans_nuevo, 
            bolivar_solidaria_plans
        )
        
        print(f"✅ Consolidado generado exitosamente:")
        print(f"📁 Archivo: {excel_path}")
        
        return excel_path
        
    except Exception as e:
        print(f"❌ Error generando consolidado: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    main()
