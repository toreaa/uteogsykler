"""
Konkurranseapp - Main Application
Internal competition platform for companies
"""

import streamlit as st
import sys
import os
from datetime import datetime, date

# Add src to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.supabase_client import get_supabase
from utils.database_helpers import get_db_helper
from utils.error_handler import StreamlitErrorHandler, validate_email
from pages.leaderboard import show_leaderboard_page
from pages.activities import show_activities_page
from pages.dashboard import show_dashboard_page
from pages.profile import show_profile_page
from pages.admin import show_admin_page

# Import system admin page with innocent name
try:
    from pages.report_analytics import show_analytics_page
    ANALYTICS_AVAILABLE = True
except ImportError:
    ANALYTICS_AVAILABLE = False

st.set_page_config(
    page_title="Konkurranseapp",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    """Main application entry point"""
    # Initialize session state
    initialize_session_state()
    
    # Check authentication
    if not is_authenticated():
        show_login_page()
    else:
        show_main_app()

def initialize_session_state():
    """Initialize all session state variables"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'dashboard'

def is_authenticated():
    """Check if user is authenticated"""
    return st.session_state.get('authenticated', False)

def show_login_page():
    """Show login/registration page"""
    # Clear any existing sidebar content
    st.sidebar.empty()
    
    # Hide sidebar completely for login page
    st.markdown("""
        <style>
        .css-1d391kg {display: none}
        [data-testid="stSidebar"] {display: none}
        section[data-testid="stSidebar"] {display: none}
        </style>
        """, unsafe_allow_html=True)
    
    st.title("🏆 Konkurranseapp")
    st.subheader("Intern konkurranseplattform for bedrifter")
    
    st.markdown("---")
    
    tab1, tab2 = st.tabs(["🔐 Logg inn", "📝 Registrer deg"])
    
    with tab1:
        show_login_form()
    
    with tab2:
        show_registration_form()

def show_login_form():
    """Login form"""
    st.markdown("### Logg inn med din konto")
    
    with st.form("main_login_form"):
        email = st.text_input("📧 E-post")
        password = st.text_input("🔒 Passord", type="password")
        
        login_btn = st.form_submit_button("🚀 Logg inn", type="primary", use_container_width=True)
    
    if login_btn:
        if email and password:
            if perform_login(email, password):
                st.rerun()
        else:
            st.error("Fyll inn både e-post og passord")

def show_registration_form():
    """Registration form"""
    st.markdown("### Opprett ny konto")
    
    with st.form("main_registration_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            full_name = st.text_input("👤 Fullt navn")
            email = st.text_input("📧 E-post")
        
        with col2:
            password = st.text_input("🔒 Passord", type="password")
            password_confirm = st.text_input("🔒 Bekreft passord", type="password")
        
        st.markdown("**🏢 Bedriftstilknytning**")
        
        company_option = st.radio(
            "Hva vil du gjøre?",
            ["🆕 Registrere min bedrift", "🤝 Bli med i eksisterende bedrift"]
        )
        
        if company_option == "🆕 Registrere min bedrift":
            company_name = st.text_input("🏢 Bedriftsnavn")
            company_code = None
        else:
            company_name = None
            company_code = st.text_input("🔑 Bedriftskode (6 tegn)").upper()
        
        register_btn = st.form_submit_button("✨ Opprett konto", type="primary", use_container_width=True)
    
    if register_btn:
        if perform_registration(full_name, email, password, password_confirm, 
                              company_option, company_name, company_code):
            st.success("Konto opprettet! Du kan nå logge inn.")

def perform_login(email: str, password: str) -> bool:
    """Handle login"""
    try:
        supabase = get_supabase()
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        
        if response.user:
            db = get_db_helper()
            user_profile = db.get_user_by_id(response.user.id)
            
            if user_profile:
                st.session_state.authenticated = True
                st.session_state.user = {
                    'id': response.user.id,
                    'email': response.user.email,
                    'full_name': user_profile['full_name'],
                    'company_id': user_profile['company_id'],
                    'is_admin': user_profile['is_admin'],
                    'user_role': user_profile.get('user_role', 'user')
                }
                return True
        
        st.error("Ugyldig e-post eller passord")
        return False
        
    except Exception as e:
        st.error(f"Pålogging feilet: {e}")
        return False

def perform_registration(full_name: str, email: str, password: str, password_confirm: str,
                        company_option: str, company_name: str = None, company_code: str = None) -> bool:
    """Handle registration"""
    # Validation
    if not all([full_name, email, password, password_confirm]):
        st.error("Fyll inn alle feltene")
        return False
    
    if password != password_confirm:
        st.error("Passordene stemmer ikke overens")
        return False
    
    if not validate_email(email):
        st.error("Ugyldig e-postadresse")
        return False
    
    try:
        supabase = get_supabase()
        db = get_db_helper()
        
        # Handle company
        target_company_id = None
        is_admin = False
        
        if company_option == "🆕 Registrere min bedrift":
            if not company_name:
                st.error("Skriv inn bedriftsnavn")
                return False
            
            company = db.create_company(company_name)
            target_company_id = company['id']
            is_admin = True
            st.info(f"Bedriftskode: **{company['company_code']}**")
        else:
            if not company_code:
                st.error("Skriv inn bedriftskode")
                return False
            
            company = db.get_company_by_code(company_code)
            if not company:
                st.error("Ugyldig bedriftskode")
                return False
            
            target_company_id = company['id']
        
        # Create user
        response = supabase.auth.sign_up({
            "email": email,
            "password": password
        })
        
        if response.user:
            db.create_user(
                user_id=response.user.id,
                email=email,
                full_name=full_name,
                company_id=target_company_id,
                is_admin=is_admin
            )
            return True
        
        st.error("Kunne ikke opprette konto")
        return False
        
    except Exception as e:
        st.error(f"Registrering feilet: {e}")
        return False

def show_main_app():
    """Show main authenticated application"""
    # Re-enable sidebar for authenticated users
    st.markdown("""
        <style>
        .css-1d391kg {display: block}
        [data-testid="stSidebar"] {display: block}
        section[data-testid="stSidebar"] {display: block}
        </style>
        """, unsafe_allow_html=True)
    
    user = st.session_state.user
    
    # Sidebar navigation
    show_sidebar(user)
    
    # Main content area
    page = st.session_state.current_page
    
    if page == 'dashboard':
        show_dashboard_page(user)
    elif page == 'activities':
        show_activities_page(user)
    elif page == 'leaderboard':
        show_leaderboard_page(user)
    elif page == 'profile':
        show_profile_page(user)
    elif page == 'admin':
        if user.get('user_role') in ['company_admin', 'system_admin']:
            show_admin_page(user)
        else:
            st.error("Du har ikke tilgang til admin-området")
    elif page == 'report_analytics':
        # System admin analytics page - only accessible to system admins
        if user.get('user_role') == 'system_admin' and ANALYTICS_AVAILABLE:
            show_analytics_page(user)
        else:
            st.error("🚫 Ingen tilgang til avanserte rapporter")
            st.info("Kun system-administratorer har tilgang til denne siden")

def show_sidebar(user):
    """Show sidebar navigation"""
    with st.sidebar:
        st.title("🏆 Konkurranseapp")
        st.markdown("---")
        
        # User info
        st.markdown("### 👤 Innlogget som:")
        st.write(f"**{user['full_name']}**")
        
        # Show role
        user_role = user.get('user_role', 'user')
        if user_role == 'system_admin':
            st.write("🔧 System Administrator")
        elif user_role == 'company_admin':
            st.write("👑 Bedrifts-administrator")
        else:
            st.write("👤 Bruker")
        
        st.markdown("---")
        
        # Navigation
        st.markdown("### 📋 Meny")
        
        # Standard navigation buttons
        if st.button("🏠 Dashboard", use_container_width=True, 
                    type="primary" if st.session_state.current_page == 'dashboard' else "secondary"):
            st.session_state.current_page = 'dashboard'
            st.rerun()
        
        if st.button("🏃 Aktiviteter", use_container_width=True,
                    type="primary" if st.session_state.current_page == 'activities' else "secondary"):
            st.session_state.current_page = 'activities'
            st.rerun()
        
        if st.button("🏆 Leaderboard", use_container_width=True,
                    type="primary" if st.session_state.current_page == 'leaderboard' else "secondary"):
            st.session_state.current_page = 'leaderboard'
            st.rerun()
        
        if st.button("👤 Profil", use_container_width=True,
                    type="primary" if st.session_state.current_page == 'profile' else "secondary"):
            st.session_state.current_page = 'profile'
            st.rerun()
        
        # Company admin button (for company_admin and system_admin)
        if user_role in ['company_admin', 'system_admin']:
            if st.button("👑 Bedrifts-admin", use_container_width=True,
                        type="primary" if st.session_state.current_page == 'admin' else "secondary"):
                st.session_state.current_page = 'admin'
                st.rerun()
        
        st.markdown("---")
        
        # Logout
        if st.button("🚪 Logg ut", use_container_width=True):
            logout_user()

def logout_user():
    """Handle logout"""
    try:
        supabase = get_supabase()
        supabase.auth.sign_out()
    except:
        pass
    
    st.session_state.authenticated = False
    st.session_state.user = None
    st.session_state.current_page = 'dashboard'
    st.rerun()

if __name__ == "__main__":
    main()
