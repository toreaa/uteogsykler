"""
Login and User Management Test App
Simple authentication testing without complex imports
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
    page_title="Konkurranseapp - Login Test",
    page_icon="👤",
    layout="wide"
)

def main():
    st.title("👤 Konkurranseapp - Login & User Test")
    st.markdown("---")
    
    # Initialize session state
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'current_user' not in st.session_state:
        st.session_state.current_user = None
    
    # Show appropriate view
    if st.session_state.logged_in:
        render_user_dashboard()
    else:
        render_welcome_page()


def render_welcome_page():
    """Show welcome page with login/signup options"""
    st.subheader("Velkommen til Konkurranseapp! 🎉")
    st.write("Test brukerregistrering og pålogging")
    
    tab1, tab2 = st.tabs(["🔐 Logg inn", "📝 Registrer deg"])
    
    with tab1:
        render_login_section()
    
    with tab2:
        render_signup_section()


def render_login_section():
    """Login form"""
    st.subheader("Logg inn med din konto")
    
    with st.form("login_form", clear_on_submit=False):
        email = st.text_input("📧 E-post", placeholder="din@bedrift.no")
        password = st.text_input("🔒 Passord", type="password")
        
        col1, col2 = st.columns([2, 1])
        with col1:
            login_btn = st.form_submit_button("🚀 Logg inn", type="primary", use_container_width=True)
        with col2:
            forgot_btn = st.form_submit_button("🤔 Glemt passord?", use_container_width=True)
    
    if login_btn:
        if not email or not password:
            st.error("⚠️ Fyll inn både e-post og passord")
            return
        
        login_success = perform_login(email, password)
        if login_success:
            st.rerun()  # Only rerun if login was successful
    
    if forgot_btn:
        if email:
            st.info("📧 Funksjonalitet for passord-reset kommer snart!")
        else:
            st.warning("Skriv inn e-posten din først")


def render_signup_section():
    """Signup form"""
    st.subheader("Opprett ny konto")
    
    with st.form("signup_form", clear_on_submit=False):
        # User info
        st.markdown("**👤 Din informasjon**")
        full_name = st.text_input("Fullt navn", placeholder="Ola Nordmann")
        email = st.text_input("E-post", placeholder="ola@bedrift.no")
        
        # Password
        col1, col2 = st.columns(2)
        with col1:
            password = st.text_input("Passord", type="password", help="Minst 6 tegn")
        with col2:
            password_confirm = st.text_input("Bekreft passord", type="password")
        
        st.markdown("---")
        
        # Company selection
        st.markdown("**🏢 Bedrift**")
        company_option = st.radio(
            "Hva vil du gjøre?",
            [
                "🆕 Registrere min bedrift (jeg blir admin)",
                "🤝 Bli med i eksisterende bedrift"
            ]
        )
        
        # Conditional inputs based on selection
        company_name = None
        company_code = None
        
        if "Registrere min bedrift" in company_option:
            company_name = st.text_input(
                "🏢 Bedriftsnavn", 
                placeholder="Acme AS",
                help="Navnet på bedriften din"
            )
        else:
            company_code = st.text_input(
                "🔑 Bedriftskode", 
                placeholder="AB12C3",
                help="6-tegns kode du har fått fra din bedrift",
                max_chars=6
            ).upper()
        
        # Submit button
        signup_btn = st.form_submit_button("✨ Opprett konto", type="primary", use_container_width=True)
    
    if signup_btn:
        perform_signup(full_name, email, password, password_confirm, company_option, company_name, company_code)


def perform_login(email: str, password: str):
    """Handle login logic"""
    try:
        supabase = get_supabase()
        
        # Attempt login
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        
        if response.user:
            # Get user profile from database
            db = get_db_helper()
            user_profile = db.get_user_by_id(response.user.id)
            
            if user_profile:
                # Login successful
                st.session_state.logged_in = True
                st.session_state.current_user = {
                    'id': response.user.id,
                    'email': response.user.email,
                    'full_name': user_profile['full_name'],
                    'company_id': user_profile['company_id'],
                    'is_admin': user_profile['is_admin'],
                    'created_at': user_profile['created_at'],
                    'email_confirmed': response.user.email_confirmed_at is not None
                }
                
                st.success(f"🎉 Velkommen tilbake, {user_profile['full_name']}!")
                st.balloons()
                # Move rerun outside the try-catch
                return True  # Signal successful login
            else:
                st.error("❌ Brukerregistrering ikke fullført. Kontakt support.")
                return False
        else:
            st.error("❌ Ugyldig e-post eller passord")
            return False
            
    except Exception as auth_error:
        error_msg = str(auth_error)
        st.error(f"❌ Pålogging feilet: {error_msg}")
        
        # Handle specific error cases
        if "not confirmed" in error_msg.lower():
            st.warning("📧 E-posten din er ikke bekreftet ennå")
            st.info("💡 Sjekk innboksen din og klikk på bekreftelseslenken")
            
            # Offer to resend confirmation
            if st.button("📤 Send ny bekreftelses-e-post"):
                try:
                    supabase.auth.resend(type="signup", email=email)
                    st.success("✅ Ny bekreftelses-e-post sendt!")
                except Exception as e:
                    st.error(f"Kunne ikke sende e-post: {e}")
                    
        elif "invalid" in error_msg.lower():
            st.info("💡 Sjekk at e-post og passord er riktig")
        elif "too many" in error_msg.lower():
            st.info("💡 For mange forsøk. Vent litt og prøv igjen")
        
        return False


def perform_signup(full_name: str, email: str, password: str, password_confirm: str, 
                  company_option: str, company_name: str = None, company_code: str = None):
    """Handle signup logic"""
    
    # Validation
    if not all([full_name, email, password, password_confirm]):
        st.error("⚠️ Fyll inn alle påkrevde felter")
        return
    
    if password != password_confirm:
        st.error("❌ Passordene stemmer ikke overens")
        return
    
    if not validate_email(email):
        st.error("❌ Ugyldig e-postadresse")
        return
    
    if len(password) < 6:
        st.error("❌ Passord må være minst 6 tegn")
        return
    
    if len(full_name.strip()) < 2:
        st.error("❌ Fullt navn må være minst 2 tegn")
        return
    
    # Company validation
    if "Registrere min bedrift" in company_option:
        if not company_name or len(company_name.strip()) < 2:
            st.error("❌ Bedriftsnavn må være minst 2 tegn")
            return
    else:
        if not company_code or len(company_code) != 6:
            st.error("❌ Bedriftskode må være 6 tegn")
            return
    
    with StreamlitErrorHandler(context="User Signup"):
        supabase = get_supabase()
        db = get_db_helper()
        
        # Handle company setup
        target_company_id = None
        is_admin = False
        
        if "Registrere min bedrift" in company_option:
            # Create new company
            company = db.create_company(company_name.strip())
            target_company_id = company['id']
            is_admin = True
            
            st.info(f"🎉 Bedrift opprettet! Bedriftskode: **{company['company_code']}**")
            st.info("💡 Del denne koden med dine ansatte så de kan registrere seg")
        else:
            # Validate existing company code
            company = db.get_company_by_code(company_code)
            if not company:
                st.error("❌ Ugyldig bedriftskode. Sjekk med din bedrift.")
                return
            
            target_company_id = company['id']
            st.success(f"✅ Gyldig bedriftskode! Du blir med i: **{company['name']}**")
        
        # Create user account
        try:
            response = supabase.auth.sign_up({
                "email": email,
                "password": password
            })
            
            if response.user:
                # Success - create user profile
                user_profile = db.create_user(
                    user_id=response.user.id,
                    email=email,
                    full_name=full_name.strip(),
                    company_id=target_company_id,
                    is_admin=is_admin
                )
                
                st.success("🎉 Konto opprettet!")
                
                if response.user.email_confirmed_at:
                    st.success("✅ Du kan nå logge inn med din nye konto")
                else:
                    st.info("📧 Sjekk e-posten din for å bekrefte kontoen før du logger inn")
            else:
                st.error("❌ Kunne ikke opprette konto. Ukjent feil.")
                
        except Exception as auth_error:
            error_msg = str(auth_error)
            st.error(f"❌ Signup feil: {error_msg}")
            
            # Give specific guidance based on error
            if "invalid" in error_msg.lower():
                st.info("💡 Prøv en annen e-postadresse")
            elif "already" in error_msg.lower():
                st.info("💡 Denne e-posten er allerede registrert. Prøv å logge inn i stedet.")
            elif "weak" in error_msg.lower():
                st.info("💡 Prøv et sterkere passord")


def render_user_dashboard():
    """Show dashboard for logged in users"""
    user = st.session_state.current_user
    
    # Sidebar user info
    with st.sidebar:
        st.markdown("### 👤 Du er logget inn som:")
        st.write(f"**{user['full_name']}**")
        st.write(f"📧 {user['email']}")
        
        if user.get('is_admin'):
            st.write("👑 **Rolle:** Administrator")
        else:
            st.write("👤 **Rolle:** Vanlig bruker")
        
        st.markdown("---")
        
        if st.button("🚪 Logg ut", type="secondary", use_container_width=True):
            logout_user()
    
    # Main dashboard content
    st.success(f"🎉 Velkommen til dashboard, {user['full_name']}!")
    
    # User info section
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("👤 Din informasjon")
        st.write(f"**Bruker-ID:** `{user['id']}`")
        st.write(f"**E-post:** {user['email']}")
        st.write(f"**Fullt navn:** {user['full_name']}")
        st.write(f"**Registrert:** {user['created_at'][:10]}")
    
    with col2:
        st.subheader("🏢 Bedriftsinformasjon")
        
        if user.get('company_id'):
            # Get company details
            try:
                db = get_db_helper()
                company = db.get_company_by_id(user['company_id'])
                
                if company:
                    st.write(f"**Bedrift:** {company['name']}")
                    st.write(f"**Bedriftskode:** `{company['company_code']}`")
                    st.write(f"**Opprettet:** {company['created_at'][:10]}")
                else:
                    st.write("❌ Bedriftsinfo ikke funnet")
            except Exception as e:
                st.error(f"Feil ved henting av bedrift: {e}")
        else:
            st.write("❌ Ikke tilknyttet noen bedrift")
    
    st.markdown("---")
    
    # Access level testing
    st.subheader("🧪 Test tilgangsnivåer")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔓 Test vanlig bruker-tilgang", use_container_width=True):
            st.success("✅ Du har vanlig bruker-tilgang!")
    
    with col2:
        if st.button("👑 Test admin-tilgang", use_container_width=True):
            if user.get('is_admin'):
                st.success("✅ Du har administrator-tilgang!")
            else:
                st.error("❌ Du har ikke administrator-tilgang")
    
    # Admin section
    if user.get('is_admin') and user.get('company_id'):
        render_admin_section(user['company_id'])


def render_admin_section(company_id: str):
    """Show admin-only features"""
    st.markdown("---")
    st.subheader("👑 Administrator-funksjoner")
    
    try:
        db = get_db_helper()
        company_users = db.get_users_by_company(company_id)
        
        st.write(f"**Antall brukere i bedriften:** {len(company_users)}")
        
        if company_users:
            st.markdown("**Bedriftens brukere:**")
            
            for idx, company_user in enumerate(company_users, 1):
                with st.container():
                    col1, col2, col3 = st.columns([3, 1, 1])
                    
                    with col1:
                        st.write(f"**{idx}. {company_user['full_name']}**")
                        st.caption(f"📧 {company_user['email']}")
                    
                    with col2:
                        if company_user['is_admin']:
                            st.write("👑 Admin")
                        else:
                            st.write("👤 Bruker")
                    
                    with col3:
                        st.caption(f"Reg: {company_user['created_at'][:10]}")
                
                if idx < len(company_users):
                    st.divider()
        else:
            st.info("Ingen andre brukere i bedriften ennå")
            
    except Exception as e:
        st.error(f"Kunne ikke hente brukerliste: {e}")


def logout_user():
    """Handle user logout"""
    try:
        supabase = get_supabase()
        supabase.auth.sign_out()
    except Exception as e:
        st.warning(f"Advarsel ved utlogging: {e}")
    
    # Clear session
    st.session_state.logged_in = False
    st.session_state.current_user = None
    
    st.success("👋 Du er nå logget ut")
    st.rerun()


if __name__ == "__main__":
    main()
