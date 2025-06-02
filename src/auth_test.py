"""
Authentication test app
Test complete authentication flow with Supabase
"""

import streamlit as st
import sys
import os

# Add src to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from auth import (
    check_authentication_status, is_authenticated, get_current_user,
    render_auth_tabs, render_user_info, require_auth
)
from utils.database_helpers import get_db_helper

st.set_page_config(
    page_title="Konkurranseapp - Auth Test",
    page_icon="🔐",
    layout="wide"
)

def main():
    st.title("🔐 Konkurranseapp - Authentication Test")
    
    # Initialize authentication
    check_authentication_status()
    
    # Check if user is authenticated
    if is_authenticated():
        render_authenticated_app()
    else:
        render_unauthenticated_app()


def render_unauthenticated_app():
    """Render app for unauthenticated users"""
    st.markdown("---")
    st.subheader("Velkommen til Konkurranseapp!")
    st.write("Du må logge inn eller opprette en konto for å fortsette.")
    
    # Render authentication tabs
    auth_success, user_data = render_auth_tabs()
    
    if auth_success and user_data:
        st.success("Autentisering vellykket!")
        st.rerun()


def render_authenticated_app():
    """Render app for authenticated users"""
    current_user = get_current_user()
    
    if not current_user:
        st.error("Brukerdata ikke tilgjengelig")
        return
    
    # Render user info in sidebar
    render_user_info(current_user)
    
    # Main content
    st.success(f"🎉 Velkommen, {current_user['full_name']}!")
    
    # Show user details
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("👤 Din informasjon")
        st.write(f"**Navn:** {current_user['full_name']}")
        st.write(f"**E-post:** {current_user['email']}")
        st.write(f"**Bruker-ID:** {current_user['id']}")
        
        if current_user.get('is_admin'):
            st.write("**Rolle:** 👑 Administrator")
        else:
            st.write("**Rolle:** 👤 Vanlig bruker")
    
    with col2:
        st.subheader("🏢 Bedriftsinformasjon")
        
        if current_user.get('company'):
            company = current_user['company']
            st.write(f"**Bedrift:** {company.get('name', 'Ukjent')}")
            st.write(f"**Bedriftskode:** {company.get('company_code', 'Ukjent')}")
        else:
            st.warning("⚠️ Du er ikke tilknyttet en bedrift ennå")
            
            if st.button("Velg bedrift", type="primary"):
                st.info("Bedriftstilknytning kommer i neste steg!")
    
    st.markdown("---")
    
    # Test different authentication levels
    st.subheader("🧪 Test autentiseringsnivåer")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Test vanlig bruker-tilgang", type="secondary"):
            test_user_access()
    
    with col2:
        if st.button("Test admin-tilgang", type="secondary"):
            test_admin_access()
    
    st.markdown("---")
    
    # Show company users (if admin)
    if current_user.get('is_admin') and current_user.get('company_id'):
        render_company_users(current_user['company_id'])
    
    # Debug info
    with st.expander("🐛 Debug informasjon"):
        st.json(current_user)


def test_user_access():
    """Test regular user access"""
    try:
        require_auth()
        st.success("✅ Vanlig bruker-tilgang OK")
    except Exception as e:
        st.error(f"❌ Feil: {e}")


def test_admin_access():
    """Test admin access"""
    try:
        require_auth(admin_required=True)
        st.success("✅ Admin-tilgang OK")
    except Exception as e:
        st.error(f"❌ Feil: {e}")


def render_company_users(company_id: str):
    """Render company users list for admins"""
    st.subheader("👥 Bedriftens brukere")
    
    try:
        db = get_db_helper()
        users = db.get_users_by_company(company_id)
        
        if users:
            st.write(f"**Antall brukere:** {len(users)}")
            
            for user in users:
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.write(f"**{user['full_name']}**")
                    st.caption(user['email'])
                
                with col2:
                    if user['is_admin']:
                        st.write("👑 Admin")
                    else:
                        st.write("👤 Bruker")
                
                with col3:
                    st.caption(f"Registrert: {user['created_at'][:10]}")
        else:
            st.info("Ingen brukere funnet")
            
    except Exception as e:
        st.error(f"Kunne ikke hente brukere: {e}")


if __name__ == "__main__":
    main()
