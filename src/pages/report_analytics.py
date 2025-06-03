"""
Advanced Reporting and Analytics
File: /src/pages/report_analytics.py
"""

import streamlit as st
from datetime import datetime, date
from typing import Dict, Any, List
import sys
import os

# Add src to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.supabase_client import get_supabase


def show_analytics_page(user: Dict[str, Any]):
    """Advanced analytics and reporting - System admin only"""
    
    # Verify system admin access
    if not is_system_admin(user):
        st.error("🚫 Ingen tilgang til avanserte rapporter")
        st.info("Kun system-administratorer har tilgang til denne siden")
        return
    
    st.title("📊 Avanserte Rapporter og Analyser")
    st.markdown(f"System administrasjon for **{user['full_name']}**")
    st.warning("⚠️ Du har system administrator-tilgang. Vær forsiktig med endringer.")
    st.markdown("---")
    
    # System admin tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🏢 Bedrifter",
        "👥 Alle Brukere", 
        "🏃 Aktiviteter",
        "📊 System-statistikk",
        "⚙️ System-innstillinger"
    ])
    
    with tab1:
        show_company_management(user)
    
    with tab2:
        show_all_users_management(user)
    
    with tab3:
        show_activity_management(user)
    
    with tab4:
        show_system_statistics(user)
    
    with tab5:
        show_system_settings(user)


def is_system_admin(user: Dict[str, Any]) -> bool:
    """Verify if user is system admin"""
    try:
        supabase = get_supabase()
        user_response = supabase.table('users').select('user_role').eq('id', user['id']).execute()
        if user_response.data:
            return user_response.data[0].get('user_role') == 'system_admin'
        return False
    except Exception as e:
        st.error(f"Kunne ikke verifisere tilgang: {e}")
        return False


def show_company_management(user: Dict[str, Any]):
    """Manage all companies in the system"""
    st.subheader("🏢 Bedriftsadministrasjon")
    st.info("System admin kan opprette og administrere alle bedrifter")
    st.write("🚧 Denne funksjonen kommer snart...")


def show_all_users_management(user: Dict[str, Any]):
    """Manage all users across all companies"""
    st.subheader("👥 Global brukeradministrasjon")
    st.info("System admin kan administrere alle brukere på tvers av bedrifter")
    st.write("🚧 Denne funksjonen kommer snart...")


def show_activity_management(user: Dict[str, Any]):
    """Manage system activities"""
    st.subheader("🏃 Aktivitetsadministrasjon")
    st.info("System admin kan legge til, redigere og deaktivere aktiviteter")
    st.write("🚧 Denne funksjonen kommer snart...")


def show_system_statistics(user: Dict[str, Any]):
    """Show system-wide statistics"""
    st.subheader("📊 System-statistikk")
    
    try:
        supabase = get_supabase()
        
        # Get basic stats
        companies = supabase.table('companies').select('*').execute().data or []
        users = supabase.table('users').select('*').execute().data or []
        activities = supabase.table('activities').select('*').execute().data or []
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("🏢 Totale bedrifter", len(companies))
        
        with col2:
            st.metric("👥 Totale brukere", len(users))
        
        with col3:
            st.metric("🏃 Aktiviteter", len(activities))
        
        st.markdown("---")
        st.info("Detaljert statistikk kommer snart...")
        
    except Exception as e:
        st.error(f"Kunne ikke laste statistikk: {e}")


def show_system_settings(user: Dict[str, Any]):
    """System settings and configuration"""
    st.subheader("⚙️ System-innstillinger")
    
    # System information
    st.markdown("### ℹ️ System-informasjon")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info(f"""
        **System Administrator:** {user['full_name']}
        **Siste pålogging:** {datetime.now().strftime('%Y-%m-%d %H:%M')}
        **Bruker-ID:** `{user['id']}`
        """)
    
    with col2:
        st.info(f"""
        **System versjon:** 1.0.0
        **Database:** Supabase
        **Hosting:** Streamlit Cloud
        **Sist oppdatert:** {datetime.now().strftime('%Y-%m-%d')}
        """)
    
    st.markdown("---")
    st.info("System-innstillinger kommer snart...")


if __name__ == "__main__":
    # This page should only be accessed through the main app
    st.error("❌ Denne siden kan kun åpnes gjennom hovedapplikasjonen")
    st.info("Gå til hovedsiden og logg inn som system administrator")
