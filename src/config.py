"""
Sentralisert konfigurasjonshåndtering for Konkurranseapp
Cloud-native versjon for Streamlit Cloud deployment
"""

import os

class Config:
    """Konfigurasjonsklass som håndterer Streamlit Cloud secrets"""
    
    def __init__(self):
        # Supabase konfigurasjon fra Streamlit secrets
        self.supabase_url = self._get_secret("SUPABASE_URL", "supabase", "url")
        self.supabase_anon_key = self._get_secret("SUPABASE_ANON_KEY", "supabase", "anon_key")
        
        # App konfigurasjon
        self.app_name = self._get_secret("APP_NAME", "app", "name", "Konkurranseapp")
        self.app_version = self._get_secret("APP_VERSION", "app", "version", "1.0.0")
        self.debug_mode = self._get_secret("DEBUG_MODE", "app", "debug_mode", "false").lower() == "true"
        self.secret_key = self._get_secret("SECRET_KEY", "app", "secret_key", "streamlit-cloud-secret")
    
    def _get_secret(self, env_name: str, streamlit_section: str = None, streamlit_key: str = None, default: str = None) -> str:
        """
        Hent secret fra Streamlit Cloud secrets med fallback til miljøvariabler
        
        Args:
            env_name: Navn på miljøvariabel (fallback)
            streamlit_section: Streamlit secrets section
            streamlit_key: Streamlit secrets key
            default: Default verdi hvis secret ikke finnes
            
        Returns:
            Verdien av secret
            
        Raises:
            ValueError: Hvis påkrevd secret mangler
        """
        value = None
        
        # Prøv Streamlit secrets først (primary method for cloud)
        if streamlit_section and streamlit_key:
            try:
                import streamlit as st
                value = st.secrets[streamlit_section][streamlit_key]
            except (KeyError, AttributeError, ImportError):
                pass
        
        # Fallback til miljøvariabel (for GitHub Actions eller andre cloud services)
        if value is None:
            value = os.getenv(env_name, default)
        
        if value is None:
            raise ValueError(f"Påkrevd secret mangler: {env_name} (eller {streamlit_section}.{streamlit_key})")
        
        return value
    
    def get_streamlit_secrets(self):
        """
        Hent alle secrets for Streamlit Cloud deployment
        """
        return {
            'supabase_url': self.supabase_url,
            'supabase_anon_key': self.supabase_anon_key,
            'secret_key': self.secret_key
        }
    
    def validate_config(self) -> bool:
        """
        Valider at alle påkrevde konfigurasjoner er satt
        
        Returns:
            True hvis alle påkrevde verdier er satt
        """
        required_vars = [
            self.supabase_url,
            self.supabase_anon_key
        ]
        
        return all(var is not None and var.strip() != "" for var in required_vars)
    
    def print_config_status(self):
        """Print konfigurasjonsstatus for debugging (uten å eksponere secrets)"""
        print(f"App Name: {self.app_name}")
        print(f"App Version: {self.app_version}")
        print(f"Debug Mode: {self.debug_mode}")
        print(f"Supabase URL: {'✓ Satt' if self.supabase_url else '✗ Mangler'}")
        print(f"Supabase Key: {'✓ Satt' if self.supabase_anon_key else '✗ Mangler'}")
        print(f"Config Valid: {'✓' if self.validate_config() else '✗'}")


# Global config instance
config = Config()

# Convenience functions
def get_supabase_config():
    """Returner Supabase konfigurasjon"""
    return {
        'url': config.supabase_url,
        'anon_key': config.supabase_anon_key
    }

def is_debug_mode():
    """Sjekk om debug mode er aktivert"""
    return config.debug_mode

def get_app_info():
    """Returner app informasjon"""
    return {
        'name': config.app_name,
        'version': config.app_version
    }
