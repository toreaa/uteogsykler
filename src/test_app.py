"""
Simple Authentication Test App
Minimal version without complex imports
"""

import streamlit as st
import sys
import os

# Add src to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.supabase_client import get_supabase
from utils.database_helpers import get_db_helper
from utils.error_handler import StreamlitErrorHandler, validate_email

st.set_page_config(
    page_title="Konkurranseapp - Simple Auth Test",
    page_icon="🔐",
    layout="wide"
)

def main():
    st.title("🔐 Konkurranseapp - Simple Auth Test")
    st.markdown("---")
    
    # Initialize session state
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user' not in st.session_state:
        st.session_state.user = None
    
    # Check authentication
    if st.session_state.authenticated:
        render_authenticated_view()
    else:
        render_unauthenticated_view()


def render_unauthenticated_view():
    """Show login/signup forms"""
    st.subheader("Velkommen til Konkurranseapp!")
    st.write("Test autentiseringsfunksjonalitet")
    
    tab1, tab2 = st.tabs(["Logg inn", "Registrer"])
    
    with tab1:
        render_login_form()
    
    with tab2:
        render_signup_form()


def render_login_form():
    """Simple login form"""
    st.subheader("🔐 Logg inn")
    
    with st.form("login_form"):
        email = st.text_input("E-post")
        password = st.text_input("Passord", type="password")
        submitted = st.form_submit_button("Logg inn", type="primary")
    
    if submitted:
        if not email or not password:
            st.error("Fyll inn både e-post og passord")
            return
        
        with StreamlitErrorHandler(context="Login"):
            supabase = get_supabase()
            
            # Try to sign in
            response = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if response.user:
                # Get user profile from database
                db = get_db_helper()
                user_profile = db.get_user_by_id(response.user.id)
                
                if user_profile:
                    # Success!
                    st.session_state.authenticated = True
                    st.session_state.user = {
                        'id': response.user.id,
                        'email': response.user.email,
                        'full_name': user_profile['full_name'],
                        'company_id': user_profile['company_id'],
                        'is_admin': user_profile['is_admin']
                    }
                    st.success(f"Velkommen, {user_profile['full_name']}!")
                    st.rerun()
                else:
                    st.error("Brukerregistrering ikke fullført")
            else:
                st.error("Ugyldig e-post eller passord")


def render_signup_form():
    """Simple signup form"""
    st.subheader("📝 Registrer ny bruker")
    
    with st.form("signup_form"):
        full_name = st.text_input("Fullt navn")
        email = st.text_input("E-post")
        password = st.text_input("Passord", type="password")
        password_confirm = st.text_input("Bekreft passord", type="password")
        
        st.markdown("**Bedrift**")
        company_choice = st.radio(
            "Velg:",
            ["Opprett ny bedrift (bli admin)", "Bli med i eksisterende bedrift"]
        )
        
        company_code = None
        company_name = None
        
        if company_choice == "Bli med i eksisterende bedrift":
            company_code = st.text_input("Bedriftskode (6 tegn)").upper()
        else:
            company_name = st.text_input("Bedriftsnavn")
        
        submitted = st.form_submit_button("Registrer", type="primary")
    
    if submitted:
        # Validation
        if not all([full_name, email, password, password_confirm]):
            st.error("Fyll inn alle feltene")
            return
        
        if password != password_confirm:
            st.error("Passordene stemmer ikke overens")
            return
        
        if not validate_email(email):
            st.error("Ugyldig e-postadresse")
            return
        
        if len(password) < 6:
            st.error("Passord må være minst 6 tegn")
            return
        
        with StreamlitErrorHandler(context="Signup"):
            supabase = get_supabase()
            db = get_db_helper()
            
            # Handle company
            company_id = None
            is_admin = False
            
            if company_choice == "Bli med i eksisterende bedrift":
                if not company_code:
                    st.error("Skriv inn bedriftskode")
                    return
                
                company = db.get_company_by_code(company_code)
                if not company:
                    st.error("Ugyldig bedriftskode")
                    return
                
                company_id = company['id']
            else:
                if not company_name:
                    st.error("Skriv inn bedriftsnavn")
                    return
                
                # Create new company
                company = db.create_company(company_name)
                company_id = company['id']
                is_admin = True
                st.info(f"Bedriftskode: {company['company_code']}")
            
            # Sign up user
            response = supabase.auth.sign_up({
                "email": email,
                "password": password
            })
            
            if response.user:
                # Create user profile
                user_profile = db.create_user(
                    user_id=response.user.id,
                    email=email,
                    full_name=full_name,
                    company_id=company_id,
                    is_admin=is_admin
                )
                
                st.success("Bruker opprettet!")
                
                if response.user.email_confirmed_at:
                    st.success("Du kan nå logge inn")
                else:
                    st.info("Sjekk e-post for å bekrefte kontoen")


def render_authenticated_view():
    """Show authenticated user interface"""
    user = st.session_state.user
    
    # Sidebar
    with st.sidebar:
        st.subheader("👤 Brukerinfo")
        st.write(f"**Navn:** {user['full_name']}")
        st.write(f"**E-post:** {user['email']}")
        
        if user.get('is_admin'):
            st.write("**Rolle:** 👑 Admin")
        else:
            st.write("**Rolle:** 👤 Bruker")
        
        st.markdown("---")
        if st.button("🚪 Logg ut"):
            supabase = get_supabase()
            supabase.auth.sign_out()
            st.session_state.authenticated = False
            st.session_state.user = None
            st.rerun()
    
    # Main content
    st.success(f"🎉 Velkommen, {user['full_name']}!")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("👤 Din informasjon")
        st.write(f"**Bruker-ID:** {user['id']}")
        st.write(f"**E-post:** {user['email']}")
        st.write(f"**Navn:** {user['full_name']}")
    
    with col2:
        st.subheader("🏢 Bedriftsinformasjon")
        
        if user.get('company_id'):
            try:
                db = get_db_helper()
                company = db.get_company_by_id(user['company_id'])
                
                if company:
                    st.write(f"**Bedrift:** {company['name']}")
                    st.write(f"**Kode:** {company['company_code']}")
                else:
                    st.write("Bedriftsinfo ikke funnet")
            except Exception as e:
                st.error(f"Feil ved henting av bedrift: {e}")
        else:
            st.write("Ikke tilknyttet bedrift")
    
    st.markdown("---")
    
    # Test access levels
    st.subheader("🧪 Test tilgangsnivåer")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Test bruker-tilgang"):
            st.success("✅ Du har bruker-tilgang")
    
    with col2:
        if st.button("Test admin-tilgang"):
            if user.get('is_admin'):
                st.success("✅ Du har admin-tilgang")
            else:
                st.error("❌ Du har ikke admin-tilgang")
    
    # Show company users if admin
    if user.get('is_admin') and user.get('company_id'):
        st.markdown("---")
        st.subheader("👥 Bedriftens brukere")
        
        try:
            db = get_db_helper()
            users = db.get_users_by_company(user['company_id'])
            
            if users:
                for company_user in users:
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.write(f"**{company_user['full_name']}** ({company_user['email']})")
                    
                    with col2:
                        if company_user['is_admin']:
                            st.write("👑 Admin")
                        else:
                            st.write("👤 Bruker")
            else:
                st.info("Ingen andre brukere i bedriften")
                
        except Exception as e:
            st.error(f"Kunne ikke hente brukere: {e}")


if __name__ == "__main__":
    main()
