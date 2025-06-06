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
from pages import (
    show_leaderboard_page,
    show_activities_page, 
    show_dashboard_page,
    show_profile_page,
    show_admin_page,
    show_analytics_page
)

st.set_page_config(
    page_title="Konkurranseapp",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="expanded"
)

# SKJUL STREAMLIT SIN EGEN NAVIGASJON
st.markdown("""
    <style>
    /* Skjul Streamlit sin øverste navigasjon */
    [data-testid="stAppViewContainer"] > .main > div > div > div > div.stAppViewBlockContainer > div > section > div > div:first-child {
        display: none;
    }
    
    /* Skjul multipage navigasjon */
    .stSelectbox > div > div > div {
        display: none;
    }
    
    /* Skjul page selector */
    .stSelectbox[data-baseweb="select"] {
        display: none;
    }
    
    /* Skjul hovedmeny */
    #MainMenu {
        visibility: hidden;
    }
    
    /* Skjul Streamlit header og footer */
    header[data-testid="stHeader"] {
        display: none;
    }
    
    footer {
        visibility: hidden;
    }
    
    /* Skjul "Made with Streamlit" */
    .viewerBadge_container__1QSob {
        display: none;
    }
    
    /* Skjul eventuell page navigation */
    [data-testid="stSidebarNav"] {
        display: none;
    }
    
    /* Skjul page selector i sidebar */
    .stSelectbox {
        display: none;
    }
    
    /* Alternative selectors for hiding navigation */
    div[data-testid="stSidebarNav"] {
        display: none;
    }
    
    ul[data-testid="stSidebarNavItems"] {
        display: none;
    }
    
    /* Fjern navigation fra toppen */
    .css-18ni7ap {
        display: none;
    }
    
    /* Streamlit multipage navigation */
    section[data-testid="stSidebar"] > div > div:first-child {
        display: none;
    }
    </style>
    """, unsafe_allow_html=True)

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
    """Registration form - only join existing companies"""
    st.markdown("### Opprett ny konto")
    st.info("💡 **Du trenger en bedriftskode fra din arbeidsgiver for å registrere deg**")
    
    with st.form("main_registration_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            full_name = st.text_input("👤 Fullt navn", placeholder="Ola Nordmann")
            email = st.text_input("📧 E-post", placeholder="ola@bedrift.no")
        
        with col2:
            password = st.text_input("🔒 Passord", type="password", placeholder="Minst 6 tegn")
            password_confirm = st.text_input("🔒 Bekreft passord", type="password")
        
        st.markdown("**🏢 Bedriftstilknytning**")
        
        company_code = st.text_input(
            "🔑 Bedriftskode (6 tegn)", 
            placeholder="AB12C3",
            help="Skriv inn bedriftskoden du har fått fra din arbeidsgiver eller HR-avdeling",
            max_chars=6
        ).upper()
        
        st.caption("📞 Kontakt din arbeidsgiver eller HR-avdeling for å få bedriftskoden")
        
        register_btn = st.form_submit_button("✨ Opprett konto", type="primary", use_container_width=True)
    
    if register_btn:
        if perform_registration(full_name, email, password, password_confirm, company_code):
            st.success("🎉 Konto opprettet! Du kan nå logge inn.")

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

def perform_registration(full_name: str, email: str, password: str, password_confirm: str, company_code: str) -> bool:
    """Handle registration - only join existing companies"""
    # Validation
    if not all([full_name, email, password, password_confirm, company_code]):
        st.error("Fyll inn alle feltene")
        return False
    
    if password != password_confirm:
        st.error("Passordene stemmer ikke overens")
        return False
    
    if not validate_email(email):
        st.error("Ugyldig e-postadresse")
        return False
    
    if len(company_code) != 6 or not company_code.isalnum():
        st.error("Bedriftskode må være 6 alfanumeriske tegn")
        return False
    
    try:
        supabase = get_supabase()
        db = get_db_helper()
        
        # Validate company code
        company = db.get_company_by_code(company_code)
        if not company:
            st.error("❌ Ugyldig bedriftskode. Sjekk med din arbeidsgiver at koden er riktig.")
            st.info("💡 Bedriftskoder er 6 tegn lange og består av bokstaver og tall")
            return False
        
        st.success(f"✅ Gyldig bedriftskode! Du blir med i: **{company['name']}**")
        
        # Create user account
        response = supabase.auth.sign_up({
            "email": email,
            "password": password
        })
        
        if response.user:
            # Create user profile as regular user (not admin)
            db.create_user(
                user_id=response.user.id,
                email=email,
                full_name=full_name,
                company_id=company['id'],
                is_admin=False  # New users are always regular users
            )
            
            st.info(f"👤 Du er registrert som vanlig bruker i {company['name']}")
            st.info("👑 Kontakt din bedrifts-administrator hvis du trenger admin-rettigheter")
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
        if user.get('user_role') == 'system_admin' and show_analytics_page:
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
