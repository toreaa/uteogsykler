"""
Test script for å verifisere konfigurasjon
Kjør: python src/test_config.py
"""

from config import config, get_supabase_config, get_app_info

def test_configuration():
    """Test at konfigurasjon lastes korrekt"""
    print("=== Konkurranseapp Configuration Test ===\n")
    
    # Print konfigurasjonsstatus
    config.print_config_status()
    
    print("\n=== Detailed Config ===")
    
    # Test Supabase config
    supabase_config = get_supabase_config()
    print(f"Supabase URL starts with https://: {supabase_config['url'].startswith('https://')}")
    print(f"Supabase Key length: {len(supabase_config['anon_key'])} characters")
    
    # Test app info
    app_info = get_app_info()
    print(f"App: {app_info['name']} v{app_info['version']}")
    
    # Valider konfigurasjon
    is_valid = config.validate_config()
    print(f"\n=== Validation Result ===")
    print(f"Configuration is valid: {'✓ YES' if is_valid else '✗ NO'}")
    
    if not is_valid:
        print("\n❌ Konfigurasjon er ikke komplett!")
        print("Sjekk at følgende miljøvariabler er satt:")
        print("- SUPABASE_URL")
        print("- SUPABASE_ANON_KEY")
        print("\nOpprett .env fil basert på .env.example")
        return False
    
    print("\n✅ Konfigurasjon er klar for bruk!")
    return True

if __name__ == "__main__":
    test_configuration()
