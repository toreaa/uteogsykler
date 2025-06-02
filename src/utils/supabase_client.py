"""
Supabase client setup og connection handling
"""

import os
import sys
from typing import Optional
from supabase import create_client, Client
import streamlit as st

# Legg til src-mappen til Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import get_supabase_config

class SupabaseClient:
    """Singleton class for Supabase client management"""
    
    _instance: Optional['SupabaseClient'] = None
    _client: Optional[Client] = None
    
    def __new__(cls) -> 'SupabaseClient':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._client is None:
            self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Supabase client"""
        try:
            # Hent konfigurasjon
            config = get_supabase_config()
            
            if not config['url'] or not config['anon_key']:
                raise ValueError("Supabase URL og anon_key må være satt")
            
            # Opprett client
            self._client = create_client(
                supabase_url=config['url'],
                supabase_key=config['anon_key']
            )
            
            print("✅ Supabase client initialisert")
            
        except Exception as e:
            print(f"❌ Feil ved initialisering av Supabase client: {e}")
            raise
    
    @property
    def client(self) -> Client:
        """Returner Supabase client instance"""
        if self._client is None:
            raise RuntimeError("Supabase client er ikke initialisert")
        return self._client
    
    def test_connection(self) -> bool:
        """Test database-tilkobling"""
        try:
            # Test ved å hente aktiviteter (read-only operasjon)
            response = self._client.table('activities').select('id').limit(1).execute()
            
            if hasattr(response, 'data'):
                print("✅ Database-tilkobling fungerer")
                return True
            else:
                print("❌ Uventet response format")
                return False
                
        except Exception as e:
            print(f"❌ Database-tilkobling feilet: {e}")
            return False
    
    def get_auth(self):
        """Returner auth client for autentisering"""
        return self._client.auth
    
    def get_table(self, table_name: str):
        """Returner table client for spesifikk tabell"""
        return self._client.table(table_name)


# Global client instance
_supabase_client = None

def get_supabase_client() -> SupabaseClient:
    """
    Get global Supabase client instance
    Bruker singleton pattern for å unngå multiple connections
    """
    global _supabase_client
    
    if _supabase_client is None:
        _supabase_client = SupabaseClient()
    
    return _supabase_client

def get_supabase() -> Client:
    """Convenience function for å få Supabase client direkte"""
    return get_supabase_client().client

# Streamlit-spesifikk client (for caching)
@st.cache_resource
def get_cached_supabase_client():
    """
    Cached Supabase client for Streamlit
    Brukes når vi integrerer med Streamlit senere
    """
    return get_supabase_client()

def test_supabase_connection():
    """Test function for database connection"""
    try:
        client = get_supabase_client()
        return client.test_connection()
    except Exception as e:
        print(f"Connection test failed: {e}")
        return False
