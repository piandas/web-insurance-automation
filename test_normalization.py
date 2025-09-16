#!/usr/bin/env python3
"""
Script rápido para probar la normalización de texto.
"""

import unicodedata

def normalize_text(text: str) -> str:
    """
    Normaliza texto removiendo tildes, acentos y convirtiendo a minúsculas.
    """
    if not text:
        return ""
    
    # Convertir a string por si acaso
    text = str(text)
    
    # Remover tildes y acentos usando unicodedata
    text_normalized = unicodedata.normalize('NFD', text)
    text_without_accents = ''.join(c for c in text_normalized if unicodedata.category(c) != 'Mn')
    
    # Convertir a minúsculas
    return text_without_accents.lower()

def test_normalization():
    """Prueba la normalización con varios textos."""
    test_cases = [
        "Días de Cobertura",
        "dias de cobertura", 
        "DÍAS DE COBERTURA",
        "Días",
        "dias",
        "cobertura",
        "COBERTURA"
    ]
    
    print("🧪 Pruebas de normalización:")
    print("-" * 50)
    
    for text in test_cases:
        normalized = normalize_text(text)
        print(f"'{text}' -> '{normalized}'")
    
    print("\n🔍 Pruebas de búsqueda:")
    print("-" * 50)
    
    # Simular búsqueda de "días de cobertura"
    search_terms = ['días', 'cobertura']
    normalized_search = [normalize_text(term) for term in search_terms]
    
    test_cells = [
        "Días de Cobertura",
        "dias de cobertura",
        "DÍAS DE COBERTURA", 
        "Días",
        "Cobertura",
        "Otro texto",
        "dias cobertura algo más"
    ]
    
    for cell_text in test_cells:
        cell_normalized = normalize_text(cell_text)
        match = all(term in cell_normalized for term in normalized_search)
        status = "✅" if match else "❌"
        print(f"{status} '{cell_text}' -> '{cell_normalized}' (Match: {match})")

if __name__ == "__main__":
    test_normalization()
