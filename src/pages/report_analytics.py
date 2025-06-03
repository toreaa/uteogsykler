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
    
    try:
        supabase = get_supabase()
        
        # Get all companies
        companies_response = supabase.table('companies').select('*').execute()
        companies = companies_response.data or []
        
        # Summary stats
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("🏢 Totale bedrifter", len(companies))
        
        with col2:
            total_users = 0
            for company in companies:
                users_response = supabase.table('users').select('id').eq('company_id', company['id']).execute()
                total_users += len(users_response.data or [])
            st.metric("👥 Totale brukere", total_users)
        
        with col3:
            active_companies = 0
            for company in companies:
                users_response = supabase.table('users').select('id').eq('company_id', company['id']).execute()
                if users_response.data:
                    active_companies += 1
            st.metric("✅ Aktive bedrifter", active_companies)
        
        st.markdown("---")
        
        # Add new company
        st.markdown("### ➕ Opprett ny bedrift")
        
        with st.form("create_company_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                new_company_name = st.text_input("Bedriftsnavn", placeholder="Acme AS")
            
            with col2:
                admin_email = st.text_input("Admin e-post", placeholder="admin@bedrift.no")
            
            admin_name = st.text_input("Admin fullt navn", placeholder="Ola Nordmann")
            admin_password = st.text_input("Midlertidig passord", type="password", placeholder="Minst 6 tegn")
            
            create_btn = st.form_submit_button("🏢 Opprett bedrift og admin", type="primary")
        
        if create_btn and all([new_company_name, admin_email, admin_name, admin_password]):
            create_new_company_with_admin(new_company_name, admin_email, admin_name, admin_password, user)
        
        st.markdown("---")
        
        # List all companies
        st.markdown("### 📋 Alle bedrifter")
        
        if not companies:
            st.info("Ingen bedrifter registrert ennå")
            return
        
        for company in companies:
            company_users_response = supabase.table('users').select('*').eq('company_id', company['id']).execute()
            company_users = company_users_response.data or []
            admin_count = sum(1 for u in company_users if u.get('user_role') == 'company_admin')
            
            with st.expander(f"🏢 {company['name']} ({len(company_users)} brukere)"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Bedriftskode:** `{company['company_code']}`")
                    st.write(f"**Opprettet:** {company['created_at'][:10]}")
                    st.write(f"**Brukere:** {len(company_users)} ({admin_count} admins)")
                
                with col2:
                    # Company actions
                    if st.button("👥 Se brukere", key=f"view_users_{company['id']}", help="Vis alle brukere i bedriften"):
                        show_company_users(company, company_users)
                    
                    if st.button("📊 Statistikk", key=f"stats_{company['id']}", help="Vis bedriftsstatistikk"):
                        show_company_stats(company, user)
                    
                    if st.button("🗑️ Slett bedrift", key=f"delete_{company['id']}", type="secondary", help="Slett hele bedriften"):
                        st.error("🚧 Bedriftssletting er ikke implementert ennå av sikkerhetshensyn")
        
    except Exception as e:
        st.error(f"Kunne ikke laste bedrifter: {e}")


def create_new_company_with_admin(company_name: str, admin_email: str, admin_name: str, 
                                 admin_password: str, creating_user: Dict[str, Any]):
    """Create new company with admin user"""
    try:
        supabase = get_supabase()
        
        # Generate company code using database function
        code_response = supabase.rpc('generate_company_code').execute()
        company_code = code_response.data
        
        # Create company
        company_response = supabase.table('companies').insert({
            'name': company_name.strip(),
            'company_code': company_code
        }).execute()
        
        if not company_response.data:
            st.error("❌ Kunne ikke opprette bedrift")
            return
            
        company = company_response.data[0]
        
        # Create admin user account
        auth_response = supabase.auth.sign_up({
            "email": admin_email,
            "password": admin_password
        })
        
        if auth_response.user:
            # Create user profile as company admin
            user_response = supabase.table('users').insert({
                'id': auth_response.user.id,
                'email': admin_email,
                'full_name': admin_name,
                'company_id': company['id'],
                'is_admin': True,
                'user_role': 'company_admin'
            }).execute()
            
            if user_response.data:
                st.success(f"✅ Bedrift '{company_name}' opprettet!")
                st.success(f"✅ Admin-bruker '{admin_name}' opprettet")
                st.info(f"🔑 Bedriftskode: **{company['company_code']}**")
                st.info(f"📧 Send påloggingsinfo til {admin_email}")
                st.rerun()
            else:
                st.error("❌ Kunne ikke opprette bruker-profil")
        else:
            st.error("❌ Kunne ikke opprette admin-bruker")
            
    except Exception as e:
        st.error(f"Feil ved opprettelse av bedrift: {e}")


def show_company_users(company: Dict[str, Any], users: List[Dict[str, Any]]):
    """Show all users in a company"""
    st.markdown(f"**👥 Brukere i {company['name']}:**")
    
    for user in users:
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.write(f"**{user['full_name']}**")
            st.caption(f"📧 {user['email']}")
        
        with col2:
            role = user.get('user_role', 'user')
            if role == 'system_admin':
                st.write("🔧 System Admin")
            elif role == 'company_admin':
                st.write("👑 Company Admin")
            else:
                st.write("👤 Bruker")
        
        with col3:
            st.caption(f"Reg: {user['created_at'][:10]}")


def show_company_stats(company: Dict[str, Any], user: Dict[str, Any]):
    """Show statistics for a specific company"""
    try:
        supabase = get_supabase()
        
        # Get company users and competitions
        users_response = supabase.table('users').select('*').eq('company_id', company['id']).execute()
        company_users = users_response.data or []
        
        competitions_response = supabase.table('monthly_competitions').select('*').eq('company_id', company['id']).limit(6).execute()
        competitions = competitions_response.data or []
        
        st.markdown(f"**📊 Statistikk for {company['name']}:**")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("👥 Brukere", len(company_users))
        
        with col2:
            st.metric("🏆 Konkurranser", len(competitions))
        
        with col3:
            # Calculate total activity
            total_entries = 0
            for comp in competitions:
                leaderboard_response = supabase.rpc('get_competition_leaderboard', {'competition_id_param': comp['id']}).execute()
                leaderboard = leaderboard_response.data or []
                total_entries += sum(entry['entries_count'] for entry in leaderboard)
            
            st.metric("📊 Aktiviteter", total_entries)
        
        # Recent activity
        if competitions:
            latest_comp = competitions[0]
            leaderboard_response = supabase.rpc('get_competition_leaderboard', {'competition_id_param': latest_comp['id']}).execute()
            latest_leaderboard = leaderboard_response.data or []
            
            if latest_leaderboard:
                st.write("**🏆 Siste måned topp 3:**")
                for i, entry in enumerate(latest_leaderboard[:3], 1):
                    medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉"
                    st.write(f"{medal} {entry['full_name']} - {entry['total_points']} poeng")
        
    except Exception as e:
        st.error(f"Kunne ikke laste statistikk: {e}")


def show_all_users_management(user: Dict[str, Any]):
    """Manage all users across all companies"""
    st.subheader("👥 Global brukeradministrasjon")
    
    try:
        supabase = get_supabase()
        
        # Get all users with company info
        users_response = supabase.table('users').select("""
            *, 
            companies(name, company_code)
        """).order('created_at', desc=True).execute()
        
        all_users = users_response.data or []
        
        # Summary stats
        system_admins = [u for u in all_users if u.get('user_role') == 'system_admin']
        company_admins = [u for u in all_users if u.get('user_role') == 'company_admin']
        regular_users = [u for u in all_users if u.get('user_role') == 'user']
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("👥 Totale brukere", len(all_users))
        
        with col2:
            st.metric("🔧 System admins", len(system_admins))
        
        with col3:
            st.metric("👑 Company admins", len(company_admins))
        
        with col4:
            st.metric("👤 Vanlige brukere", len(regular_users))
        
        st.markdown("---")
        
        # User search and filter
        search_term = st.text_input("🔍 Søk etter brukere", placeholder="Navn eller e-post")
        
        role_filter = st.selectbox(
            "Filtrer etter rolle",
            ["Alle", "System Admin", "Company Admin", "Vanlig bruker"]
        )
        
        # Filter users
        filtered_users = all_users
        
        if search_term:
            filtered_users = [
                u for u in filtered_users 
                if search_term.lower() in u['full_name'].lower() 
                or search_term.lower() in u['email'].lower()
            ]
        
        if role_filter != "Alle":
            role_map = {
                "System Admin": "system_admin",
                "Company Admin": "company_admin", 
                "Vanlig bruker": "user"
            }
            filtered_users = [
                u for u in filtered_users 
                if u.get('user_role') == role_map[role_filter]
            ]
        
        st.write(f"**Viser {len(filtered_users)} av {len(all_users)} brukere:**")
        
        # Display users
        for user_info in filtered_users:
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                
                with col1:
                    st.write(f"**{user_info['full_name']}**")
                    st.caption(f"📧 {user_info['email']}")
                    
                    company = user_info.get('companies')
                    if company:
                        st.caption(f"🏢 {company['name']} ({company['company_code']})")
                    else:
                        st.caption("🏢 Ingen bedrift")
                
                with col2:
                    role = user_info.get('user_role', 'user')
                    if role == 'system_admin':
                        st.write("🔧 System")
                    elif role == 'company_admin':
                        st.write("👑 Company")
                    else:
                        st.write("👤 Bruker")
                
                with col3:
                    reg_date = user_info['created_at'][:10]
                    st.caption(f"Reg: {reg_date}")
                
                with col4:
                    # User actions
                    if user_info['id'] != user['id']:  # Can't modify yourself
                        if st.button("⚙️", key=f"manage_{user_info['id'][-8:]}", help="Administrer bruker"):
                            show_user_management_actions(user_info, user)
                
                st.divider()
        
    except Exception as e:
        st.error(f"Kunne ikke laste brukere: {e}")


def show_user_management_actions(target_user: Dict[str, Any], admin_user: Dict[str, Any]):
    """Show management actions for a specific user"""
    st.markdown(f"**⚙️ Administrer: {target_user['full_name']}**")
    
    current_role = target_user.get('user_role', 'user')
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**Nåværende rolle:** {current_role}")
        
        # Role change options
        new_role = st.selectbox(
            "Endre rolle til:",
            ["user", "company_admin", "system_admin"],
            index=["user", "company_admin", "system_admin"].index(current_role),
            key=f"role_{target_user['id'][-8:]}"
        )
        
        if new_role != current_role:
            if st.button("💾 Oppdater rolle", key=f"update_role_{target_user['id'][-8:]}"):
                update_user_role(target_user, new_role, admin_user)
    
    with col2:
        st.write("**Farlige operasjoner:**")
        
        if st.button("🗑️ Slett bruker", key=f"delete_user_{target_user['id'][-8:]}", type="secondary"):
            st.error("🚧 Brukersletting er ikke implementert ennå")


def update_user_role(target_user: Dict[str, Any], new_role: str, admin_user: Dict[str, Any]):
    """Update user role"""
    try:
        supabase = get_supabase()
        
        # Update user role
        response = supabase.table('users').update({
            'user_role': new_role
        }).eq('id', target_user['id']).execute()
        
        if response.data:
            st.success(f"✅ Rolle oppdatert til {new_role} for {target_user['full_name']}")
            
            # If promoting to system_admin, add to system_admins table
            if new_role == 'system_admin':
                try:
                    supabase.table('system_admins').insert({
                        'user_id': target_user['id'],
                        'created_by': admin_user['id']
                    }).execute()
                except:
                    # Might already exist, ignore error
                    pass
            
            st.rerun()
        else:
            st.error("❌ Kunne ikke oppdatere rolle")
            
    except Exception as e:
        st.error(f"Feil ved oppdatering av rolle: {e}")


def show_activity_management(user: Dict[str, Any]):
    """Manage system activities"""
    st.subheader("🏃 Aktivitetsadministrasjon")
    
    try:
        supabase = get_supabase()
        activities_response = supabase.table('activities').select('*').order('name').execute()
        activities = activities_response.data or []
        
        # Add new activity
        st.markdown("### ➕ Legg til ny aktivitet")
        
        with st.form("add_activity_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                activity_name = st.text_input("Aktivitetsnavn", placeholder="Svømming")
                activity_unit = st.text_input("Enhet", placeholder="km")
            
            with col2:
                activity_description = st.text_area("Beskrivelse", placeholder="Registrer totalt antall kilometer svømt")
            
            st.markdown("**Poengskala (3 nivåer):**")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                tier1_max = st.number_input("Nivå 1 - Maks verdi", min_value=0.0, value=50.0)
                tier1_points = st.number_input("Nivå 1 - Poeng", min_value=1, value=1)
            
            with col2:
                tier2_max = st.number_input("Nivå 2 - Maks verdi", min_value=tier1_max, value=100.0)
                tier2_points = st.number_input("Nivå 2 - Poeng", min_value=tier1_points, value=2)
            
            with col3:
                tier3_points = st.number_input("Nivå 3 - Poeng (100+)", min_value=tier2_points, value=3)
            
            create_activity_btn = st.form_submit_button("➕ Opprett aktivitet", type="primary")
        
        if create_activity_btn and all([activity_name, activity_unit, activity_description]):
            create_new_activity(activity_name, activity_unit, activity_description, 
                              tier1_max, tier1_points, tier2_max, tier2_points, tier3_points)
        
        st.markdown("---")
        
        # List existing activities
        st.markdown("### 📋 Eksisterende aktiviteter")
        
        for activity in activities:
            with st.expander(f"🏃 {activity['name']} ({activity['unit']})"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Beskrivelse:** {activity['description']}")
                    st.write(f"**Status:** {'✅ Aktiv' if activity['is_active'] else '❌ Inaktiv'}")
                
                with col2:
                    st.write("**Poengskala:**")
                    tiers = activity['scoring_tiers']['tiers']
                    for tier in tiers:
                        min_val = tier['min']
                        max_val = tier.get('max', '∞')
                        points = tier['points']
                        st.write(f"• {min_val}-{max_val} {activity['unit']} = {points}p")
                
                # Activity actions
                col1, col2 = st.columns(2)
                
                with col1:
                    current_status = activity['is_active']
                    new_status = not current_status
                    action_text = "Deaktiver" if current_status else "Aktiver"
                    
                    if st.button(f"{'❌' if current_status else '✅'} {action_text}", 
                               key=f"toggle_{activity['id']}", 
                               help=f"{action_text} denne aktiviteten"):
                        toggle_activity_status(activity, new_status)
                
                with col2:
                    if st.button("🗑️ Slett", key=f"delete_activity_{activity['id']}", 
                               type="secondary", help="Slett aktiviteten permanent"):
                        st.error("🚧 Sletting av aktiviteter er ikke implementert ennå")
        
    except Exception as e:
        st.error(f"Kunne ikke laste aktiviteter: {e}")


def create_new_activity(name: str, unit: str, description: str, 
                       tier1_max: float, tier1_points: int,
                       tier2_max: float, tier2_points: int,
                       tier3_points: int):
    """Create new activity"""
    try:
        supabase = get_supabase()
        
        # Create scoring tiers JSON
        scoring_tiers = {
            "tiers": [
                {"min": 0, "max": tier1_max, "points": tier1_points},
                {"min": tier1_max, "max": tier2_max, "points": tier2_points},
                {"min": tier2_max, "max": None, "points": tier3_points}
            ]
        }
        
        # Insert new activity
        response = supabase.table('activities').insert({
            'name': name,
            'unit': unit,
            'description': description,
            'scoring_tiers': scoring_tiers,
            'is_active': True
        }).execute()
        
        if response.data:
            st.success(f"✅ Aktivitet '{name}' opprettet!")
            st.rerun()
        else:
            st.error("❌ Kunne ikke opprette aktivitet")
            
    except Exception as e:
        st.error(f"Feil ved opprettelse av aktivitet: {e}")


def toggle_activity_status(activity: Dict[str, Any], new_status: bool):
    """Toggle activity active status"""
    try:
        supabase = get_supabase()
        
        response = supabase.table('activities').update({
            'is_active': new_status
        }).eq('id', activity['id']).execute()
        
        if response.data:
            status_text = "aktivert" if new_status else "deaktivert"
            st.success(f"✅ Aktivitet '{activity['name']}' {status_text}")
            st.rerun()
        else:
            st.error("❌ Kunne ikke endre aktivitetsstatus")
            
    except Exception as e:
        st.error(f"Feil ved endring av aktivitetsstatus: {e}")


def show_system_statistics(user: Dict[str, Any]):
    """Show system-wide statistics"""
    st.subheader("📊 System-statistikk")
    
    try:
        supabase = get_supabase()
        
        # Get overall system stats
        companies_response = supabase.table('companies').select('*').execute()
        users_response = supabase.table('users').select('*').execute()
        activities_response = supabase.table('activities').select('*').execute()
        
        companies = companies_response.data or []
        all_users = users_response.data or []
        activities = activities_response.data or []
        
        # Overview metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("🏢 Bedrifter", len(companies))
        
        with col2:
            st.metric("👥 Brukere", len(all_users))
        
        with col3:
            st.metric("🏃 Aktiviteter", len(activities))
        
        with col4:
            # Calculate total competitions
            competitions_response = supabase.table('monthly_competitions').select('*').execute()
            total_competitions = len(competitions_response.data or [])
            st.metric("🏆 Konkurranser", total_competitions)
        
        st.markdown("---")
        
        # User role breakdown
        st.markdown("### 👥 Brukerfordeling")
        
        role_counts = {}
        for user_info in all_users:
            role = user_info.get('user_role', 'user')
            role_counts[role] = role_counts.get(role, 0) + 1
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("🔧 System Admins", role_counts.get('system_admin', 0))
        
        with col2:
            st.metric("👑 Company Admins", role_counts.get('company_admin', 0))
        
        with col3:
            st.metric("👤 Vanlige brukere", role_counts.get('user', 0))
        
        st.markdown("---")
        
        # Recent activity across system
        st.markdown("### 📈 Nylig aktivitet")
        
        # Get recent users (last 30 days)
        recent_users = [u for u in all_users if 
                       (datetime.now() - datetime.fromisoformat(u['created_at'].replace('Z', '+00:00'))).days <= 30]
        
        # Get recent companies
        recent_companies = [c for c in companies if 
                          (datetime.now() - datetime.fromisoformat(c['created_at'].replace('Z', '+00:00'))).days <= 30]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("👥 Nye brukere (30 dager)", len(recent_users))
            
            if recent_users:
                st.write("**Siste registreringer:**")
                for user_info in recent_users[-5:]:  # Last 5
                    reg_date = user_info['created_at'][:10]
                    st.write(f"• {user_info['full_name']} ({reg_date})")
        
        with col2:
            st.metric("🏢 Nye bedrifter (30 dager)", len(recent_companies))
            
            if recent_companies:
                st.write("**Siste bedrifter:**")
                for company in recent_companies[-5:]:  # Last 5
                    reg_date = company['created_at'][:10]
                    st.write(f"• {company['name']} ({reg_date})")
        
    except Exception as e:
        st.error(f"Kunne ikke laste system-statistikk: {e}")


def show_system_settings(user: Dict[str, Any]):
    """System settings and configuration"""
    st.subheader("⚙️ System-innstillinger")
    
    try:
        # System information
        st.markdown("### ℹ️ System-informasjon")
        
        col1, col2 = st.columns(2)
        
        with col1:
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
        
        # System administration
        st.markdown("### 👑 System Administrator-administrasjon")
        
        # Get all system admins
        supabase = get_supabase()
        system_admins_response = supabase.table('system_admins').select("""
            *, 
            users(full_name, email, created_at)
        """).eq('is_active', True).execute()
        
        system_admins = system_admins_response.data or []
        
        st.write(f"**System Administratorer ({len(system_admins)}):**")
        
        for admin in system_admins:
            admin_user = admin['users']
            with st.container():
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.write(f"**{admin_user['full_name']}**")
                    st.caption(f"📧 {admin_user['email']}")
                
                with col2:
                    created_date = admin['created_at'][:10]
                    st.caption(f"Admin siden: {created_date}")
                
                with col3:
                    if admin['user_id'] != user['id']:  # Can't remove yourself
                        if st.button("🗑️ Fjern", key=f"remove_sysadmin_{admin['id']}", 
                                   type="secondary", help="Fjern system admin-tilgang"):
                            remove_system_admin_confirmation(admin, admin_user)
                
                st.divider()
        
        # Add new system admin
        st.markdown("#### ➕ Legg til ny System Administrator")
        
        with st.form("add_system_admin_form"):
            admin_email = st.text_input("E-post til bruker som skal bli system admin", 
                                      placeholder="bruker@bedrift.no")
            
            add_admin_btn = st.form_submit_button("👑 Gi system admin-tilgang", type="primary")
        
        if add_admin_btn and admin_email:
            add_new_system_admin(admin_email, user)
        
        st.markdown("---")
        
        # Export and maintenance
        st.markdown("### 📊 Data og vedlikehold")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📄 Eksporter systemdata", help="Eksporter sammendrag av all data"):
                export_system_data()
        
        with col2:
            if st.button("🔍 Sjekk system-helse", help="Kontroller database og system-tilstand"):
                check_system_health()
        
    except Exception as e:
        st.error(f"Kunne ikke laste system-innstillinger: {e}")


def remove_system_admin_confirmation(admin: Dict[str, Any], admin_user: Dict[str, Any]):
    """Show confirmation for removing system admin"""
    st.error(f"⚠️ **ADVARSEL:** Du er i ferd med å fjerne system admin-tilgang fra {admin_user['full_name']}")
    
    if st.button(f"🗑️ JA, FJERN TILGANG", key=f"confirm_remove_{admin['id']}", type="secondary"):
        remove_system_admin(admin, admin_user)


def remove_system_admin(admin: Dict[str, Any], admin_user: Dict[str, Any]):
    """Remove system admin access"""
    try:
        supabase = get_supabase()
        
        # Check if this would leave no system admins
        remaining_admins = supabase.table('system_admins').select('*').eq('is_active', True).execute()
        
        if len(remaining_admins.data or []) <= 1:
            st.error("❌ Kan ikke fjerne siste system administrator")
            return
        
        # Deactivate system admin record
        supabase.table('system_admins').update({
            'is_active': False
        }).eq('id', admin['id']).execute()
        
        # Update user role to company_admin if they have a company, otherwise user
        user_data = supabase.table('users').select('company_id').eq('id', admin['user_id']).execute()
        new_role = 'company_admin' if user_data.data and user_data.data[0].get('company_id') else 'user'
        
        supabase.table('users').update({
            'user_role': new_role
        }).eq('id', admin['user_id']).execute()
        
        st.success(f"✅ System admin-tilgang fjernet fra {admin_user['full_name']}")
        st.rerun()
        
    except Exception as e:
        st.error(f"Feil ved fjerning av system admin: {e}")


def add_new_system_admin(email: str, creating_user: Dict[str, Any]):
    """Add new system admin by email"""
    try:
        supabase = get_supabase()
        
        # Find user by email
        user_response = supabase.table('users').select('*').eq('email', email).execute()
        
        if not user_response.data:
            st.error(f"❌ Fant ikke bruker med e-post: {email}")
            return
        
        target_user = user_response.data[0]
        
        # Check if already system admin
        if target_user.get('user_role') == 'system_admin':
            st.warning(f"⚠️ {target_user['full_name']} er allerede system administrator")
            return
        
        # Update user role to system_admin
        supabase.table('users').update({
            'user_role': 'system_admin'
        }).eq('id', target_user['id']).execute()
        
        # Add to system_admins table
        supabase.table('system_admins').insert({
            'user_id': target_user['id'],
            'created_by': creating_user['id'],
            'is_active': True
        }).execute()
        
        st.success(f"✅ {target_user['full_name']} er nå system administrator!")
        st.rerun()
        
    except Exception as e:
        st.error(f"Feil ved opprettelse av system admin: {e}")


def export_system_data():
    """Export system data summary"""
    try:
        supabase = get_supabase()
        
        st.write("**📤 Eksporterer systemdata...**")
        
        # Get all data
        companies = supabase.table('companies').select('*').execute().data or []
        users = supabase.table('users').select('*').execute().data or []
        activities = supabase.table('activities').select('*').execute().data or []
        
        # Create export summary
        export_data = f"SYSTEM DATA EXPORT\n"
        export_data += f"Eksportert: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        export_data += "=" * 50 + "\n\n"
        
        export_data += f"OVERSIKT:\n"
        export_data += f"Bedrifter: {len(companies)}\n"
        export_data += f"Brukere: {len(users)}\n"
        export_data += f"Aktiviteter: {len(activities)}\n\n"
        
        export_data += "BEDRIFTER:\n"
        for company in companies:
            export_data += f"- {company['name']} ({company['company_code']}) - {company['created_at'][:10]}\n"
        
        export_data += f"\nBRUKERE:\n"
        for user in users:
            role = user.get('user_role', 'user')
            export_data += f"- {user['full_name']} ({user['email']}) - {role} - {user['created_at'][:10]}\n"
        
        export_data += f"\nAKTIVITETER:\n"
        for activity in activities:
            status = "Aktiv" if activity['is_active'] else "Inaktiv"
            export_data += f"- {activity['name']} ({activity['unit']}) - {status}\n"
        
        st.text_area("📋 System-data (kopier teksten):", export_data, height=400)
        st.success("✅ System-data eksportert")
        
    except Exception as e:
        st.error(f"Kunne ikke eksportere system-data: {e}")


def check_system_health():
    """Check system health and database status"""
    try:
        supabase = get_supabase()
        
        st.write("**🔍 Sjekker system-helse...**")
        
        # Test basic connectivity
        companies_test = supabase.table('companies').select('count').execute()
        users_test = supabase.table('users').select('count').execute()
        activities_test = supabase.table('activities').select('count').execute()
        
        st.success("✅ Database-tilkobling: OK")
        st.success("✅ Tabeller tilgjengelige: OK")
        
        # Test data integrity
        st.write("**🔍 Sjekker data-integritet...**")
        
        # Check for orphaned users (users without companies)
        orphaned_users = supabase.table('users').select('*').is_('company_id', 'null').execute()
        orphaned_count = len(orphaned_users.data or [])
        
        if orphaned_count > 0:
            st.warning(f"⚠️ Fant {orphaned_count} brukere uten bedrift")
        else:
            st.success("✅ Alle brukere har gyldig bedrift")
        
        # Check for companies without users
        all_companies = supabase.table('companies').select('*').execute()
        companies_without_users = 0
        
        for company in all_companies.data or []:
            users_in_company = supabase.table('users').select('id').eq('company_id', company['id']).execute()
            if not users_in_company.data:
                companies_without_users += 1
        
        if companies_without_users > 0:
            st.info(f"ℹ️ {companies_without_users} bedrifter har ingen brukere")
        else:
            st.success("✅ Alle bedrifter har minst én bruker")
        
        st.success("🎉 System-helse: God tilstand")
        
    except Exception as e:
        st.error(f"❌ System-helse-sjekk feilet: {e}")


if __name__ == "__main__":
    # This page should only be accessed through the main app
    st.error("❌ Denne siden kan kun åpnes gjennom hovedapplikasjonen")
    st.info("Gå til hovedsiden og logg inn som system administrator")
        
        st.markdown("---")
        
        # System administration
        st.markdown("### 👑 System Administrator-administrasjon")
        
        # Get all system admins
        supabase = get_supabase()
        system_admins_response = supabase.table('system_admins').select("""
            *, 
            users(full_name, email, created_at)
        """).eq('is_active', True).execute()
        
        system_admins = system_admins_response.data or []
        
        st.write(f"**System Administratorer ({len(system_admins)}):**")
        
        for admin in system_admins:
            admin_user = admin['users']
            with st.container():
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.write(f"**{admin_user['full_name']}**")
                    st.caption(f"📧 {admin_user['email']}")
                
                with col2:
                    created_date = admin['created_at'][:10]
                    st.caption(f"Admin siden: {created_date}")
                
                with col3:
                    if admin['user_id'] != user['id']:  # Can't remove yourself
                        if st.button("🗑️ Fjern", key=f"remove_sysadmin_{admin['id']}", 
                                   type="secondary", help="Fjern system admin-tilgang"):
                            remove_system_admin_confirmation(admin, admin_user)
                
                st.divider()
        
        # Add new system admin
        st.markdown("#### ➕ Legg til ny System Administrator")
        
        with st.form("add_system_admin_form"):
            admin_email = st.text_input("E-post til bruker som skal bli system admin", 
                                      placeholder="bruker@bedrift.no")
            
            add_admin_btn = st.form_submit_button("👑 Gi system admin-tilgang", type="primary")
        
        if add_admin_btn and admin_email:
            add_new_system_admin(admin_email, user)
        
        st.markdown("---")
        
        # Export and maintenance
        st.markdown("### 📊 Data og vedlikehold")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📄 Eksporter systemdata", help="Eksporter sammendrag av all data"):
                export_system_data()
        
        with col2:
            if st.button("🔍 Sjekk system-helse", help="Kontroller database og system-tilstand"):
                check_system_health()
        
    except Exception as e:
        st.error(f"Kunne ikke laste system-innstillinger: {e}")


def remove_system_admin_confirmation(admin: Dict[str, Any], admin_user: Dict[str, Any]):
    """Show confirmation for removing system admin"""
    st.error(f"⚠️ **ADVARSEL:** Du er i ferd med å fjerne system admin-tilgang fra {admin_user['full_name']}")
    
    if st.button(f"🗑️ JA, FJERN TILGANG", key=f"confirm_remove_{admin['id']}", type="secondary"):
        remove_system_admin(admin, admin_user)


def remove_system_admin(admin: Dict[str, Any], admin_user: Dict[str, Any]):
    """Remove system admin access"""
    try:
        supabase = get_supabase()
        
        # Check if this would leave no system admins
        remaining_admins = supabase.table('system_admins').select('*').eq('is_active', True).execute()
        
        if len(remaining_admins.data or []) <= 1:
            st.error("❌ Kan ikke fjerne siste system administrator")
            return
        
        # Deactivate system admin record
        supabase.table('system_admins').update({
            'is_active': False
        }).eq('id', admin['id']).execute()
        
        # Update user role to company_admin if they have a company, otherwise user
        user_data = supabase.table('users').select('company_id').eq('id', admin['user_id']).execute()
        new_role = 'company_admin' if user_data.data and user_data.data[0].get('company_id') else 'user'
        
        supabase.table('users').update({
            'user_role': new_role
        }).eq('id', admin['user_id']).execute()
        
        st.success(f"✅ System admin-tilgang fjernet fra {admin_user['full_name']}")
        st.rerun()
        
    except Exception as e:
        st.error(f"Feil ved fjerning av system admin: {e}")


def add_new_system_admin(email: str, creating_user: Dict[str, Any]):
    """Add new system admin by email"""
    try:
        supabase = get_supabase()
        
        # Find user by email
        user_response = supabase.table('users').select('*').eq('email', email).execute()
        
        if not user_response.data:
            st.error(f"❌ Fant ikke bruker med e-post: {email}")
            return
        
        target_user = user_response.data[0]
        
        # Check if already system admin
        if target_user.get('user_role') == 'system_admin':
            st.warning(f"⚠️ {target_user['full_name']} er allerede system administrator")
            return
        
        # Update user role to system_admin
        supabase.table('users').update({
            'user_role': 'system_admin'
        }).eq('id', target_user['id']).execute()
        
        # Add to system_admins table
        supabase.table('system_admins').insert({
            'user_id': target_user['id'],
            'created_by': creating_user['id'],
            'is_active': True
        }).execute()
        
        st.success(f"✅ {target_user['full_name']} er nå system administrator!")
        st.rerun()
        
    except Exception as e:
        st.error(f"Feil ved opprettelse av system admin: {e}")


def export_system_data():
    """Export system data summary"""
    try:
        supabase = get_supabase()
        
        st.write("**📤 Eksporterer systemdata...**")
        
        # Get all data
        companies = supabase.table('companies').select('*').execute().data or []
        users = supabase.table('users').select('*').execute().data or []
        activities = supabase.table('activities').select('*').execute().data or []
        
        # Create export summary
        export_data = f"SYSTEM DATA EXPORT\n"
        export_data += f"Eksportert: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        export_data += "=" * 50 + "\n\n"
        
        export_data += f"OVERSIKT:\n"
        export_data += f"Bedrifter: {len(companies)}\n"
        export_data += f"Brukere: {len(users)}\n"
        export_data += f"Aktiviteter: {len(activities)}\n\n"
        
        export_data += "BEDRIFTER:\n"
        for company in companies:
            export_data += f"- {company['name']} ({company['company_code']}) - {company['created_at'][:10]}\n"
        
        export_data += f"\nBRUKERE:\n"
        for user in users:
            role = user.get('user_role', 'user')
            export_data += f"- {user['full_name']} ({user['email']}) - {role} - {user['created_at'][:10]}\n"
        
        export_data += f"\nAKTIVITETER:\n"
        for activity in activities:
            status = "Aktiv" if activity['is_active'] else "Inaktiv"
            export_data += f"- {activity['name']} ({activity['unit']}) - {status}\n"
        
        st.text_area("📋 System-data (kopier teksten):", export_data, height=400)
        st.success("✅ System-data eksportert")
        
    except Exception as e:
        st.error(f"Kunne ikke eksportere system-data: {e}")


def check_system_health():
    """Check system health and database status"""
    try:
        supabase = get_supabase()
        
        st.write("**🔍 Sjekker system-helse...**")
        
        # Test basic connectivity
        companies_test = supabase.table('companies').select('count').execute()
        users_test = supabase.table('users').select('count').execute()
        activities_test = supabase.table('activities').select('count').execute()
        
        st.success("✅ Database-tilkobling: OK")
        st.success("✅ Tabeller tilgjengelige: OK")
        
        # Test data integrity
        st.write("**🔍 Sjekker data-integritet...**")
        
        # Check for orphaned users (users without companies)
        orphaned_users = supabase.table('users').select('*').is_('company_id', 'null').execute()
        orphaned_count = len(orphaned_users.data or [])
        
        if orphaned_count > 0:
            st.warning(f"⚠️ Fant {orphaned_count} brukere uten bedrift")
        else:
            st.success("✅ Alle brukere har gyldig bedrift")
        
        # Check for companies without users
        all_companies = supabase.table('companies').select('*').execute()
        companies_without_users = 0
        
        for company in all_companies.data or []:
            users_in_company = supabase.table('users').select('id').eq('company_id', company['id']).execute()
            if not users_in_company.data:
                companies_without_users += 1
        
        if companies_without_users > 0:
            st.info(f"ℹ️ {companies_without_users} bedrifter har ingen brukere")
        else:
            st.success("✅ Alle bedrifter har minst én bruker")
        
        st.success("🎉 System-helse: God tilstand")
        
    except Exception as e:
        st.error(f"❌ System-helse-sjekk feilet: {e}")


if __name__ == "__main__":
    # This page should only be accessed through the main app
    st.error("❌ Denne siden kan kun åpnes gjennom hovedapplikasjonen")
    st.info("Gå til hovedsiden og logg inn som system administrator")
