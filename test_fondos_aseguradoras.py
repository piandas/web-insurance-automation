#!/usr/bin/env python3
"""
Script para probar el sistema de restricciones de aseguradoras por fondo.
"""

import sys
import os
from pathlib import Path

# Añadir la carpeta src al path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from src.consolidation.template_handler import TemplateHandler
from src.config.client_config import ClientConfig

def test_fondo_aseguradoras():
    """Prueba las restricciones de aseguradoras por fondo."""
    print("🧪 PRUEBAS DE RESTRICCIONES FONDO-ASEGURADORAS")
    print("=" * 60)
    
    # Crear handler
    handler = TemplateHandler()
    
    # Probar diferentes fondos
    fondos_test = [
        ('FEPEP', ['SURA', 'ALLIANZ', 'BOLIVAR']),
        ('FECORA', ['ALLIANZ', 'SOLIDARIA']),
        ('FEMFUTURO', ['SBS', 'SOLIDARIA']),
        ('FODELSA', ['SOLIDARIA']),
        ('MANPOWER', ['SOLIDARIA', 'ALLIANZ', 'BOLIVAR']),
        ('EPM', ['SURA', 'ALLIANZ', 'BOLIVAR']),
        ('CONFAMILIA', ['SURA', 'SOLIDARIA', 'BOLIVAR']),
        ('CHEC', ['SURA', 'ALLIANZ', 'BOLIVAR']),
        ('EMVARIAS', ['SURA', 'BOLIVAR']),
        ('FONDO_NO_EXISTE', ['SURA', 'ALLIANZ', 'BOLIVAR'])  # Default
    ]
    
    for fondo, expected in fondos_test:
        actual = handler.get_fondo_aseguradoras(fondo)
        status = "✅" if actual == expected else "❌"
        
        print(f"{status} {fondo}:")
        print(f"  Esperado: {expected}")
        print(f"  Obtenido: {actual}")
        print()

def test_template_generation_with_restrictions():
    """Prueba la generación de plantillas con restricciones."""
    print("\n🏗️ PRUEBA DE GENERACIÓN CON RESTRICCIONES")
    print("=" * 60)
    
    # Configurar datos de prueba
    ClientConfig.CLIENT_NAME = "EMPRESA TEST FONDOS"
    ClientConfig.CLIENT_NIT = "900123456-7"
    ClientConfig.CLIENT_PHONE = "555-1234"
    ClientConfig.CLIENT_EMAIL = "test@fondos.com"
    ClientConfig.CLIENT_CITY = "MEDELLÍN"
    
    ClientConfig.VEHICLE_TYPE = "AUTOMOVIL"
    ClientConfig.VEHICLE_BRAND = "TOYOTA"
    ClientConfig.VEHICLE_LINE = "COROLLA"
    ClientConfig.VEHICLE_MODEL = "2024"
    ClientConfig.VEHICLE_VALUE = "85000000"
    ClientConfig.VEHICLE_STATE = "Nuevo"
    ClientConfig.VEHICLE_FASECOLDA = "123456"
    
    # Datos de cotización simulados
    sura_data = {
        'NombreAsegurado': ClientConfig.CLIENT_NAME,
        'Nit': ClientConfig.CLIENT_NIT,
        'Telefono': ClientConfig.CLIENT_PHONE,
        'Email': ClientConfig.CLIENT_EMAIL,
        'Ciudad': ClientConfig.CLIENT_CITY,
        'TipoVehiculo': ClientConfig.VEHICLE_TYPE,
        'Marca': ClientConfig.VEHICLE_BRAND,
        'Linea': ClientConfig.VEHICLE_LINE,
        'Modelo': ClientConfig.VEHICLE_MODEL,
        'ValorComercial': ClientConfig.VEHICLE_VALUE,
        'CodigoFasecolda': ClientConfig.VEHICLE_FASECOLDA,
        'DiasCotizacion': '365'
    }
    
    sura_plans = {
        'Plan Autos Global': '$2,450,000',
        'Plan Autos Clasico': '$1,850,000'
    }
    
    allianz_plans = {
        'Autos Esencial': '$2,200,000',
        'Autos Esencial + Total': '$2,800,000',
        'Autos Plus': '$3,100,000',
        'Autos llave en mano': '$3,500,000'
    }
    
    bolivar_solidaria_plans = {
        'Bolívar': '$2,300,000',
        'Solidaria': '$2,100,000',
        'SBS': '$2,000,000'
    }
    
    # Probar con diferentes fondos
    fondos_prueba = ['FEPEP', 'FECORA', 'FEMFUTURO', 'FODELSA']
    
    handler = TemplateHandler()
    
    for fondo in fondos_prueba:
        try:
            print(f"\n📋 Procesando fondo: {fondo}")
            aseguradoras = handler.get_fondo_aseguradoras(fondo)
            print(f"🔒 Aseguradoras permitidas: {aseguradoras}")
            
            # Intentar crear consolidado
            result = handler.create_consolidado_from_template(
                fondo, sura_data, sura_plans, allianz_plans, bolivar_solidaria_plans
            )
            
            if result:
                print(f"✅ Consolidado creado: {result}")
            else:
                print(f"❌ Error creando consolidado para {fondo}")
                
        except Exception as e:
            print(f"❌ Error con fondo {fondo}: {e}")

if __name__ == "__main__":
    # Ejecutar pruebas
    test_fondo_aseguradoras()
    test_template_generation_with_restrictions()
    
    print("\n🎯 PRUEBAS COMPLETADAS")
    print("=" * 60)