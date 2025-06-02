"""
Streamlit components for authentication UI
"""

import streamlit as st
from typing import Optional, Tuple, Dict, Any
import sys
import os

# Add src to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth.auth_manager import get_auth_manager
from utils.error_handler import StreamlitErrorHandler, format_error_for_user
from utils.database_helpers import get_db_helper


def render_login_form() -> Optional[Dict[str, Any]]:
    """
    Render login form
    
    Returns:
        User data if login successful, None otherwise
    """
    st.subheader("🔐 Logg inn")
    
    with st.form("login_form"):
        email = st.text_input("E-post", placeholder="din@epost.no")
        password = st.text_input("Passord", type="password")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            submitted = st.form_submit_button("Logg inn", type="primary", use_container_width=True)
        
        with col2:
            forgot_password = st.form_submit_button("Glemt passord?", use_container_width=True)
    
    # Handle login
    if submitted:
        if not email or not password:
            st.error("Vennligst fyll inn både e-post og passord")
            return None
        
        with StreamlitErrorHandler(context="User Login"):
            auth = get_auth_manager()
            user_data = auth.sign_in(email, password)
            
            if user_data:
                auth.update_session(user_data)
                st.success(f"Velkommen tilbake, {user_data['full_name']}!")
                st.rerun()
                return user_data
    
    # Handle forgot password
    if forgot_password:
        if not email:
            st.error("Vennligst fyll inn e-post først")
        else:
            with StreamlitErrorHandler(context="Password Reset"):
                auth = get_auth_manager()
                auth.reset_password(email)
                st.success("Tilbakestillingslenke sendt til e-post!")
    
    return None


def render_signup_form() -> Optional[Dict[str, Any]]:
    """
    Render signup form
    
    Returns:
        User data if signup successful, None otherwise
    """
    st.subheader("📝 Opprett ny konto")
    
    with st.form("signup_form"):
        full_name = st.text_input("Fullt navn", placeholder="Ola Nordmann")
        email = st.text_input("E-post", placeholder="din@epost.no")
        password = st.text_input("Passord", type="password", help="Minst 6 tegn")
        password_confirm = st.text_input("Bekreft passord", type="password")
        
        st.markdown("---")
        
        # Company selection
        registration_type = st.radio(
            "Jeg vil:",
            ["Registrere min bedrift (bli admin)", "Bli med i eksisterende bedrift"],
            help="Velg hvordan du vil registrere deg"
        )
        
        company_code = None
        if registration_type == "Bli med i eksisterende bedrift":
            company_code = st.text_input(
                "Bedriftskode", 
                placeholder="AB12C3",
                help="6-tegns kode du har fått fra din bedrift",
                max_chars=6
            ).upper()
        
        submitted = st.form_submit_button("Opprett konto", type="primary", use_container_width=True)
    
    if submitted:
        # Validation
        if not all([full_name, email, password, password_confirm]):
            st.error("Vennligst fyll inn alle feltene")
            return None
        
        if password != password_confirm:
            st.error("Passordene stemmer ikke overens")
            return None
        
        if registration_type == "Bli med i eksisterende bedrift" and not company_code:
            st.error("Vennligst skriv inn bedriftskode")
            return None
        
        # Validate company code if provided
        if company_code:
            db = get_db_helper()
            company = db.get_company_by_code(company_code)
            if not company:
                st.error("Ugyldig bedriftskode")
                return None
        
        with StreamlitErrorHandler(context="User Registration"):
            auth = get_auth_manager()
            
            # Sign up user
            user_data = auth.sign_up(
                email=email,
                password=password,
                full_name=full_name,
                company_code=company_code
            )
            
            if user_data:
                if user_data.get('email_confirmed'):
                    st.success("Konto opprettet! Du kan nå logge inn.")
                    return user_data
                else:
                    st.success("Konto opprettet! Sjekk e-post for å bekrefte kontoen din.")
                    st.info("Du må bekrefte e-posten din før du kan logge inn.")
    
    return None


def render_logout_button():
    """Render logout button"""
    if st.button("🚪 Logg ut", key="logout_btn"):
        auth = get_auth_manager()
        auth.sign_out()
        st.success("Du er nå logget ut")
        st.rerun()


def render_user_info(user: Dict[str, Any]):
    """
    Render current user information
    
    Args:
        user: User data dictionary
    """
    with st.sidebar:
        st.markdown("---")
        st.subheader("👤 Brukerinfo")
        
        st.write(f"**Navn:** {user['full_name']}")
        st.write(f"**E-post:** {user['email']}")
        
        if user.get('company'):
            company = user['company']
            st.write(f"**Bedrift:** {company.get('name', 'Ikke tilknyttet')}")
            
            if user.get('is_admin'):
                st.write("**Rolle:** 👑 Admin")
            else:
                st.write("**Rolle:** 👤 Bruker")
        else:
            st.write("**Bedrift:** Ikke tilknyttet")
        
        st.markdown("---")
        render_logout_button()


def render_auth_tabs() -> Tuple[bool, Optional[Dict[str, Any]]]:
    """
    Render authentication tabs (login/signup)
    
    Returns:
        Tuple of (authentication_successful, user_data)
    """
    tab1, tab2 = st.tabs(["Logg inn", "Opprett konto"])
    
    user_data = None
    
    with tab1:
        user_data = render_login_form()
    
    with tab2:
        signup_data = render_signup_form()
        if signup_data and signup_data.get('email_confirmed'):
            user_data = signup_data
    
    return user_data is not None, user_data


def render_company_selection() -> Optional[str]:
    """
    Render company selection/creation for new users
    
    Returns:
        Company ID if selected/created, None otherwise
    """
    st.subheader("🏢 Bedriftstilknytning")
    
    choice = st.radio(
        "Hva vil du gjøre?",
        [
            "Registrere min bedrift (bli admin)", 
            "Bli med i eksisterende bedrift"
        ]
    )
    
    if choice == "Registrere min bedrift (bli admin)":
        return render_company_creation_form()
    else:
        return render_company_join_form()


def render_company_creation_form() -> Optional[str]:
    """
    Render company creation form
    
    Returns:
        Company ID if created, None otherwise
    """
    st.write("**Opprett ny bedrift**")
    
    with st.form("create_company_form"):
        company_name = st.text_input(
            "Bedriftsnavn", 
            placeholder="Acme AS",
            help="Navnet på bedriften din"
        )
        
        submitted = st.form_submit_button("Opprett bedrift", type="primary")
    
    if submitted:
        if not company_name:
            st.error("Vennligst skriv inn bedriftsnavn")
            return None
        
        with StreamlitErrorHandler(context="Company Creation"):
            db = get_db_helper()
            company = db.create_company(company_name)
            
            if company:
                st.success(f"Bedrift '{company_name}' opprettet!")
                st.info(f"**Bedriftskode:** `{company['company_code']}`")
                st.info("Del denne koden med dine ansatte så de kan registrere seg")
                return company['id']
    
    return None


def render_company_join_form() -> Optional[str]:
    """
    Render company join form
    
    Returns:
        Company ID if valid code, None otherwise
    """
    st.write("**Bli med i eksisterende bedrift**")
    
    with st.form("join_company_form"):
        company_code = st.text_input(
            "Bedriftskode", 
            placeholder="AB12C3",
            help="6-tegns kode du har fått fra din bedrift",
            max_chars=6
        ).upper()
        
        submitted = st.form_submit_button("Valider kode", type="primary")
    
    if submitted:
        if not company_code:
            st.error("Vennligst skriv inn bedriftskode")
            return None
        
        with StreamlitErrorHandler(context="Company Code Validation"):
            db = get_db_helper()
            company = db.get_company_by_code(company_code)
            
            if company:
                st.success(f"Gyldig kode! Du blir med i: **{company['name']}**")
                return company['id']
            else:
                st.error("Ugyldig bedriftskode")
    
    return None


def check_authentication_status():
    """
    Check and initialize authentication status
    Should be called at the start of every page
    """
    auth = get_auth_manager()
    auth.initialize_session()
    
    # Try to get current user from Supabase
    if not auth.is_authenticated():
        current_user = auth.get_current_user()
        if current_user:
            auth.update_session(current_user)
