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
                    'is_admin': user_profile['is_admin']
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
        if user['is_admin']:
            show_admin_page(user)
        else:
            st.error("Du har ikke tilgang til admin-området")

def show_sidebar(user):
    """Show sidebar navigation"""
    with st.sidebar:
        st.title("🏆 Konkurranseapp")
        st.markdown("---")
        
        # User info
        st.markdown("### 👤 Innlogget som:")
        st.write(f"**{user['full_name']}**")
        if user['is_admin']:
            st.write("👑 Administrator")
        else:
            st.write("👤 Bruker")
        
        st.markdown("---")
        
        # Navigation
        st.markdown("### 📋 Meny")
        
        # Navigation buttons
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
        
        if user['is_admin']:
            if st.button("👑 Admin", use_container_width=True,
                        type="primary" if st.session_state.current_page == 'admin' else "secondary"):
                st.session_state.current_page = 'admin'
                st.rerun()
        
        st.markdown("---")
        
        # Logout
        if st.button("🚪 Logg ut", use_container_width=True):
            logout_user()

def show_dashboard_page(user):
    """Dashboard page"""
    st.title("🏠 Dashboard")
    st.markdown(f"Velkommen tilbake, **{user['full_name']}**! 🎉")
    
    # Quick stats
    col1, col2, col3 = st.columns(3)
    
    try:
        db = get_db_helper()
        
        # Get current month competition
        current_month = date.today().replace(day=1)
        competition = db.get_or_create_monthly_competition(user['company_id'], current_month)
        
        # Get user's entries for this month
        user_entries = db.get_user_entries_for_competition(user['id'], competition['id'])
        
        # Get company info
        company = db.get_company_by_id(user['company_id'])
        
        with col1:
            st.metric("🏢 Bedrift", company['name'] if company else "Ukjent")
        
        with col2:
            st.metric("📊 Dine registreringer", len(user_entries))
        
        with col3:
            total_points = sum(entry['points'] for entry in user_entries)
            st.metric("🎯 Totale poeng", total_points)
        
        st.markdown("---")
        
        # Recent activity
        st.subheader("📈 Din aktivitet denne måneden")
        
        if user_entries:
            for entry in user_entries:
                activity = entry.get('activities', {})
                activity_name = activity.get('name', 'Ukjent aktivitet')
                activity_unit = activity.get('unit', '')
                
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    st.write(f"**{activity_name}**")
                with col2:
                    st.write(f"{entry['value']} {activity_unit}")
                with col3:
                    st.write(f"{entry['points']} poeng")
        else:
            st.info("Du har ikke registrert noen aktiviteter ennå denne måneden. Gå til 'Aktiviteter' for å komme i gang!")
        
        # Quick actions
        st.markdown("---")
        st.subheader("⚡ Hurtighandlinger")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🏃 Registrer aktivitet", type="primary", use_container_width=True):
                st.session_state.current_page = 'activities'
                st.rerun()
        
        with col2:
            if st.button("🏆 Se leaderboard", use_container_width=True):
                st.session_state.current_page = 'leaderboard'
                st.rerun()
        
    except Exception as e:
        st.error(f"Kunne ikke laste dashboard-data: {e}")

def show_activities_page(user):
    """Activities page - placeholder"""
    st.title("🏃 Aktiviteter")
    st.info("Aktivitetsregistrering kommer i neste steg (Step 4.2)")

def show_leaderboard_page(user):
    """Leaderboard page - placeholder"""
    st.title("🏆 Leaderboard")
    st.info("Leaderboard kommer i neste steg (Step 4.3)")

def show_profile_page(user):
    """Profile page"""
    st.title("👤 Min profil")
    
    st.write(f"**Navn:** {user['full_name']}")
    st.write(f"**E-post:** {user['email']}")
    st.write(f"**Rolle:** {'👑 Administrator' if user['is_admin'] else '👤 Vanlig bruker'}")
    
    # Get company info
    try:
        db = get_db_helper()
        company = db.get_company_by_id(user['company_id'])
        if company:
            st.write(f"**Bedrift:** {company['name']}")
            st.write(f"**Bedriftskode:** {company['company_code']}")
    except Exception as e:
        st.error(f"Kunne ikke hente bedriftsinformasjon: {e}")

def show_admin_page(user):
    """Admin page - placeholder"""
    st.title("👑 Administrasjon")
    st.info("Admin-funksjoner kommer snart")

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
