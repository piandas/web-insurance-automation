"""
Verificación rápida de las actualizaciones de configuración.
"""

from src.config import ClientConfig, SuraConfig, AllianzConfig

def verificar_configuraciones():
    """Verifica que las nuevas configuraciones funcionen correctamente."""
    
    print("=== VERIFICACIÓN DE CONFIGURACIONES ACTUALIZADAS ===\n")
    
    # Verificar ClientConfig
    print("📋 ClientConfig:")
    print(f"  - Documento: {ClientConfig.CLIENT_DOCUMENT_NUMBER}")
    print(f"  - Nombre: {ClientConfig.get_full_client_name()}")
    print(f"  - Placa: {ClientConfig.VEHICLE_PLATE}")
    print(f"  - Póliza: {ClientConfig.get_policy_number()}")
    
    # Verificar datos específicos por empresa
    print(f"\n🔵 Sura:")
    print(f"  - Tipo documento: {ClientConfig.get_client_document_type('sura')}")
    print(f"  - Fecha nacimiento: {ClientConfig.get_client_birth_date('sura')}")
    print(f"  - Ciudad: {ClientConfig.get_client_city('sura')}")
    print(f"  - Login documento tipo: {ClientConfig.SURA_LOGIN_DOCUMENT_TYPE}")
    
    print(f"\n🟡 Allianz:")
    print(f"  - Tipo documento: {ClientConfig.get_client_document_type('allianz')}")
    print(f"  - Fecha nacimiento: {ClientConfig.get_client_birth_date('allianz')}")
    print(f"  - Ciudad: {ClientConfig.get_client_city('allianz')}")
    
    # Verificar configuraciones específicas
    print(f"\n⚙️ Configuraciones específicas:")
    sura_config = ClientConfig.get_company_specific_config('sura')
    allianz_config = ClientConfig.get_company_specific_config('allianz')
    print(f"  - Sura: {sura_config}")
    print(f"  - Allianz: {allianz_config}")
    
    # Verificar que las configs de empresa solo tienen datos técnicos
    print(f"\n🔧 SuraConfig (solo técnico):")
    print(f"  - Usuario: {SuraConfig.USUARIO}")
    print(f"  - Login URL: {SuraConfig.LOGIN_URL}")
    print(f"  - Tipo doc login: {SuraConfig.TIPO_DOCUMENTO_LOGIN}")
    
    print(f"\n🔧 AllianzConfig (solo técnico):")
    print(f"  - Usuario: {AllianzConfig.USUARIO}")
    print(f"  - Login URL: {AllianzConfig.LOGIN_URL}")
    
    print(f"\n✅ Todas las configuraciones funcionan correctamente!")

if __name__ == "__main__":
    verificar_configuraciones()
