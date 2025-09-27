#!/usr/bin/env python3
"""
Script de prueba para verificar la nueva nomenclatura de Sura.
"""

from src.consolidation.cotizacion_consolidator import CotizacionConsolidator
from src.consolidation.template_handler import TemplateHandler

def test_sura_extraction():
    """Prueba la extracción de planes de Sura con nueva nomenclatura."""
    print("🧪 Probando extracción de planes de Sura...")
    
    consolidator = CotizacionConsolidator()
    sura_plans = consolidator.extract_sura_plans_from_logs()
    
    print("\n📊 Planes extraídos de Sura:")
    for plan, value in sura_plans.items():
        print(f"   {plan}: {value}")
    
    return sura_plans

def test_allianz_extraction():
    """Prueba la extracción de planes de Allianz."""
    print("\n🧪 Probando extracción de planes de Allianz...")
    
    consolidator = CotizacionConsolidator()
    allianz_plans = consolidator.extract_allianz_plans_from_logs()
    
    print("\n📊 Planes extraídos de Allianz:")
    for plan, value in allianz_plans.items():
        print(f"   {plan}: {value}")
    
    return allianz_plans

def test_template_mapping():
    """Prueba el mapeo de planes en el template handler."""
    print("\n🧪 Probando mapeos de template handler...")
    
    template_handler = TemplateHandler()
    
    # Simular planes extraídos con nueva nomenclatura
    sura_plans = {
        'Global Franquicia': '4360918',
        'Autos Global': '3887744', 
        'Autos Clásico': '3272132'
    }
    
    allianz_plans = {
        'Autos Esencial': '320040',
        'Autos Plus': '2333122',
        'Autos Llave en Mano': '3035656',
        'Autos Esencial + Totales': '1357764'
    }
    
    # Probar coincidencias
    test_targets = [
        'Global Franquicia',
        'Autos Global', 
        'Autos Clásico',
        'Plan Autos Global',  # Legacy
        'Pérdida Parcial',    # Legacy
        'Autos Esencial',
        'Autos Plus'
    ]
    
    print("\n🎯 Probando coincidencias de mapeo:")
    all_plans = {**sura_plans, **allianz_plans}
    
    for target in test_targets:
        match = template_handler._find_best_plan_match(target, all_plans)
        print(f"   '{target}' -> {match if match else 'No encontrado'}")

def main():
    """Función principal del test."""
    print("🚀 Iniciando pruebas de nueva nomenclatura de Sura\n")
    
    # Pruebas de extracción
    sura_plans = test_sura_extraction()
    allianz_plans = test_allianz_extraction()
    
    # Pruebas de mapeo
    test_template_mapping()
    
    print("\n✅ Resumen de cambios implementados:")
    print("   📝 Nueva nomenclatura de Sura:")
    print("      1. Global Franquicia - Prima anual inicial")
    print("      2. Autos Global - Prima tras seleccionar 1 SMLMV")
    print("      3. Autos Clásico - Prima del plan clásico")
    print("   🔄 SIEMPRE calcula las 3 opciones (nuevos y usados)")
    print("   🎯 Consolidador actualizado para nueva nomenclatura")
    print("   📋 Template handler actualizado con mapeos")
    
    print("\n🎉 Pruebas completadas!")

if __name__ == "__main__":
    main()