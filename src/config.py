"""
Sentralisert konfigurasjonshåndtering for Konkurranseapp
Håndterer både lokale miljøvariabler og Streamlit Cloud secrets
"""

import os
from dotenv import load_dotenv

class Config:
    """Konfigurasjonsklass som håndterer miljøvariabler og secrets"""
    
    def __init__(self):
        # Last .env fil for lokal utvikling
        load_dotenv()
        
        # Supabase konfigurasjon
        self.supabase_url = self._get_env_var("SUPABASE_URL")
        self.supabase_anon_key = self._get_env_var("SUPABASE_ANON_KEY")
        
        # App konfigurasjon
        self.app_name = self._get_env_var("APP_NAME", default="Konkurranseapp")
        self.app_version = self._get_env_var("APP_VERSION", default="1.0.0")
        self.debug_mode = self._get_env_var("DEBUG_MODE", default="false").lower() == "true"
        self.secret_key = self._get_env_var("SECRET_KEY", default="dev-secret-key-change-in-prod")
        
        # Streamlit konfigurasjon
        self.streamlit_port = int(self._get_env_var("STREAMLIT_SERVER_PORT", default="8501"))
        self.streamlit_address = self._get_env_var("STREAMLIT_SERVER_ADDRESS", default="localhost")
    
    def _get_env_var(self, var_name: str, default: str = None) -> str:
        """
        Hent miljøvariabel med fallback til default
        
        Args:
            var_name: Navn på miljøvariabel
            default: Default verdi hvis variabel ikke finnes
            
        Returns:
            Verdien av miljøvariabelen
            
        Raises:
            ValueError: Hvis påkrevd variabel mangler
        """
        value = os.getenv(var_name, default)
        
        if value is None:
            raise ValueError(f"Påkrevd miljøvariabel mangler: {var_name}")
        
        return value
    
    def get_streamlit_secrets(self):
        """
        Hent secrets for Streamlit Cloud deployment
        Denne metoden vil bli utvidet når vi integrerer med Streamlit
        """
        try:
            import streamlit as st
            return {
                'supabase_url': st.secrets["supabase"]["url"],
                'supabase_anon_key': st.secrets["supabase"]["anon_key"],
                'secret_key': st.secrets["app"]["secret_key"]
            }
        except (ImportError, KeyError):
            # Fallback til miljøvariabler hvis Streamlit secrets ikke er tilgjengelig
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
