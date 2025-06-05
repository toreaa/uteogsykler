"""
Admin page for Konkurranseapp
Administrative functions for company admins
"""

import streamlit as st
from datetime import datetime, date
import sys
import os

# Add src to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.supabase_client import get_supabase
from utils.database_helpers import get_db_helper


def show_admin_page(user):
    """Admin page - administrative functions"""
    if not user['is_admin']:
        st.error("❌ Du har ikke tilgang til admin-området")
        st.info("Kun administratorer kan se denne siden")
        return
    
    st.title("👑 Bedrifts-administrasjon")
    st.markdown(f"Administrator-panel for **{user['full_name']}**")
    
    try:
        supabase = get_supabase()
        company = supabase.table('companies').select('*').eq('id', user['company_id']).execute()
        company_info = company.data[0] if company.data else None
        
        if company_info:
            st.info(f"🏢 **{company_info['name']}** (Kode: {company_info['company_code']})")
    except:
        st.warning("Kunne ikke laste bedriftsinformasjon")
    
    # Admin tabs - OPPDATERT: Lagt til Aktiviteter-tab
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "👥 Brukere", 
        "🏃 Aktiviteter",  # NY TAB
        "📊 Statistikk", 
        "🏆 Konkurranser",
        "⚙️ Innstillinger"
    ])
    
    with tab1:
        show_user_management(user)
    
    with tab2:
        show_activity_management(user)  # NY FUNKSJON
    
    with tab3:
        show_company_statistics(user)
    
    with tab4:
        show_competition_management(user)
    
    with tab5:
        show_admin_settings(user)


# ============= NY FUNKSJON: AKTIVITETSADMINISTRASJON =============

def show_activity_management(user):
    """Activity management section for company admin"""
    st.subheader("🏃 Aktivitetsadministrasjon")
    
    try:
        db = get_db_helper()
        
        # Get all activities for this company
        company_activities = db.get_active_activities(company_id=user['company_id'])
        
        # Summary stats
        total_activities = len(company_activities)
        global_activities = [a for a in company_activities if a.get('company_id') is None]
        custom_activities = [a for a in company_activities if a.get('company_id') == user['company_id']]
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("🏃 Totale aktiviteter", total_activities)
        with col2:
            st.metric("🌐 Standard aktiviteter", len(global_activities))
        with col3:
            st.metric("🏢 Bedriftsspesifikke", len(custom_activities))
        
        st.markdown("---")
        
        # Action buttons
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("➕ Opprett ny aktivitet", type="primary", use_container_width=True):
                st.session_state.show_create_activity = True
        
        with col2:
            if st.button("📋 Kopier standardaktiviteter", use_container_width=True):
                copy_standard_activities_to_company(user, db)
        
        with col3:
            if st.button("🔄 Oppdater aktivitetsliste", use_container_width=True):
                st.rerun()
        
        # Create new activity form
        if st.session_state.get('show_create_activity', False):
            show_create_activity_form(user, db)
        
        st.markdown("---")
        
        # Activities list with management options
        st.markdown("### 📋 Aktivitetsliste")
        
        if not company_activities:
            st.info("Ingen aktiviteter funnet for bedriften")
            st.info("💡 Klikk 'Kopier standardaktiviteter' for å få de grunnleggende aktivitetene")
            return
        
        # Display activities with edit options
        for activity in company_activities:
            with st.container():
                show_activity_card(activity, user, db)
                st.divider()
        
    except Exception as e:
        st.error(f"Kunne ikke laste aktiviteter: {e}")


def show_create_activity_form(user, db):
    """Show form for creating new activity"""
    with st.expander("➕ Opprett ny aktivitet", expanded=True):
        with st.form("create_activity_form"):
            st.markdown("### Ny bedriftsspesifikk aktivitet")
            
            col1, col2 = st.columns(2)
            
            with col1:
                activity_name = st.text_input("🏃 Aktivitetsnavn", placeholder="F.eks. Svømming")
                activity_unit = st.selectbox("📏 Måleenhet", ["km", "timer", "repetisjoner", "poeng", "k steps"])
            
            with col2:
                activity_description = st.text_area("📝 Beskrivelse", placeholder="Beskriv aktiviteten og hvordan den utføres")
            
            st.markdown("### 🎯 Poengskala")
            st.info("💡 Definer 3 nivåer: Lavt, medium og høyt")
            
            # Simple 3-tier system
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("**Nivå 1 (Grunnleggende)**")
                tier1_min = st.number_input("Fra", min_value=0.0, value=0.0, key="tier1_min")
                tier1_max = st.number_input("Til", min_value=0.1, value=50.0, key="tier1_max")
                tier1_points = st.number_input("Poeng", min_value=1, value=1, key="tier1_points")
            
            with col2:
                st.markdown("**Nivå 2 (Middels)**")
                tier2_min = st.number_input("Fra", min_value=0.1, value=50.0, key="tier2_min")
                tier2_max = st.number_input("Til", min_value=0.1, value=100.0, key="tier2_max")
                tier2_points = st.number_input("Poeng", min_value=1, value=2, key="tier2_points")
            
            with col3:
                st.markdown("**Nivå 3 (Høyt)**")
                tier3_min = st.number_input("Fra", min_value=0.1, value=100.0, key="tier3_min")
                st.write("Til: ∞ (ubegrenset)")
                tier3_points = st.number_input("Poeng", min_value=1, value=3, key="tier3_points")
            
            # Submit buttons
            col1, col2 = st.columns(2)
            with col1:
                submitted = st.form_submit_button("✅ Opprett aktivitet", type="primary", use_container_width=True)
            with col2:
                cancel = st.form_submit_button("❌ Avbryt", use_container_width=True)
        
        if cancel:
            st.session_state.show_create_activity = False
            st.rerun()
        
        if submitted:
            create_new_activity(user, db, activity_name, activity_description, activity_unit, 
                              tier1_min, tier1_max, tier1_points,
                              tier2_min, tier2_max, tier2_points,
                              tier3_min, tier3_points)


def create_new_activity(user, db, name, description, unit, 
                       t1_min, t1_max, t1_points, t2_min, t2_max, t2_points, t3_min, t3_points):
    """Create new company-specific activity"""
    try:
        # Validate inputs
        if not name or not description:
            st.error("Navn og beskrivelse er påkrevd")
            return
        
        # Build scoring tiers
        scoring_tiers = {
            "tiers": [
                {"min": t1_min, "max": t1_max, "points": t1_points},
                {"min": t2_min, "max": t2_max, "points": t2_points},
                {"min": t3_min, "max": None, "points": t3_points}  # Top tier has no max
            ]
        }
        
        # Create activity
        activity = db.create_activity(
            name=name,
            description=description,
            unit=unit,
            scoring_tiers=scoring_tiers,
            company_id=user['company_id']
        )
        
        st.success(f"✅ Aktivitet '{name}' ble opprettet!")
        st.balloons()
        
        # Clear form and refresh
        st.session_state.show_create_activity = False
        st.rerun()
        
    except Exception as e:
        st.error(f"Feil ved opprettelse av aktivitet: {e}")


def show_activity_card(activity, user, db):
    """Display activity card with edit options"""
    is_company_specific = activity.get('company_id') == user['company_id']
    is_global = activity.get('company_id') is None
    
    col1, col2, col3 = st.columns([3, 1, 1])
    
    with col1:
        # Activity name and type
        activity_header = f"🏃 **{activity['name']}**"
        if is_company_specific:
            activity_header += " 🏢"
        elif is_global:
            activity_header += " 🌐"
        
        st.markdown(activity_header)
        st.caption(f"📏 {activity['unit']} | {activity['description']}")
        
        # Show scoring tiers
        scoring_tiers = activity['scoring_tiers']['tiers']
        tier_text = " | ".join([
            f"{tier['min']}-{tier.get('max', '∞')} = {tier['points']}p"
            for tier in scoring_tiers
        ])
        st.caption(f"🎯 **Poengskala:** {tier_text}")
    
    with col2:
        if is_global:
            st.caption("🌐 Standard aktivitet")
            st.caption("(Kan ikke redigeres)")
        elif is_company_specific:
            st.caption("🏢 Bedriftsspesifikk")
            st.caption("(Kan redigeres)")
    
    with col3:
        if is_company_specific:
            # Edit and delete buttons for company-specific activities
            edit_key = f"edit_{activity['id']}"
            delete_key = f"delete_{activity['id']}"
            
            if st.button("✏️ Rediger", key=edit_key, help="Rediger aktivitet"):
                st.session_state[f"editing_{activity['id']}"] = True
                st.rerun()
            
            if st.button("🗑️ Slett", key=delete_key, help="Slett aktivitet"):
                delete_activity(activity, user, db)
        
        elif is_global:
            # Option to create company-specific copy
            copy_key = f"copy_{activity['id']}"
            if st.button("📋 Kopier", key=copy_key, help="Lag bedriftsspesifikk kopi"):
                copy_global_activity_to_company(activity, user, db)
    
    # Show edit form if editing
    if st.session_state.get(f"editing_{activity['id']}", False):
        show_edit_activity_form(activity, user, db)


def show_edit_activity_form(activity, user, db):
    """Show form for editing existing activity"""
    with st.expander(f"✏️ Rediger: {activity['name']}", expanded=True):
        with st.form(f"edit_form_{activity['id']}"):
            col1, col2 = st.columns(2)
            
            with col1:
                new_name = st.text_input("Aktivitetsnavn", value=activity['name'])
                new_unit = st.selectbox("Måleenhet", ["km", "timer", "repetisjoner", "poeng", "k steps"], 
                                       index=["km", "timer", "repetisjoner", "poeng", "k steps"].index(activity['unit']) 
                                       if activity['unit'] in ["km", "timer", "repetisjoner", "poeng", "k steps"] else 0)
            
            with col2:
                new_description = st.text_area("Beskrivelse", value=activity['description'])
            
            # Edit scoring tiers
            st.markdown("### 🎯 Rediger poengskala")
            current_tiers = activity['scoring_tiers']['tiers']
            
            col1, col2, col3 = st.columns(3)
            
            # Tier 1
            with col1:
                st.markdown("**Nivå 1**")
                new_t1_min = st.number_input("Fra", value=float(current_tiers[0]['min']), key=f"edit_t1_min_{activity['id']}")
                new_t1_max = st.number_input("Til", value=float(current_tiers[0]['max']) if current_tiers[0]['max'] else 50.0, key=f"edit_t1_max_{activity['id']}")
                new_t1_points = st.number_input("Poeng", value=current_tiers[0]['points'], key=f"edit_t1_points_{activity['id']}")
            
            # Tier 2
            with col2:
                st.markdown("**Nivå 2**")
                new_t2_min = st.number_input("Fra", value=float(current_tiers[1]['min']), key=f"edit_t2_min_{activity['id']}")
                new_t2_max = st.number_input("Til", value=float(current_tiers[1]['max']) if current_tiers[1]['max'] else 100.0, key=f"edit_t2_max_{activity['id']}")
                new_t2_points = st.number_input("Poeng", value=current_tiers[1]['points'], key=f"edit_t2_points_{activity['id']}")
            
            # Tier 3
            with col3:
                st.markdown("**Nivå 3**")
                new_t3_min = st.number_input("Fra", value=float(current_tiers[2]['min']), key=f"edit_t3_min_{activity['id']}")
                st.write("Til: ∞")
                new_t3_points = st.number_input("Poeng", value=current_tiers[2]['points'], key=f"edit_t3_points_{activity['id']}")
            
            # Submit buttons
            col1, col2 = st.columns(2)
            with col1:
                save_changes = st.form_submit_button("💾 Lagre endringer", type="primary", use_container_width=True)
            with col2:
                cancel_edit = st.form_submit_button("❌ Avbryt", use_container_width=True)
        
        if cancel_edit:
            st.session_state[f"editing_{activity['id']}"] = False
            st.rerun()
        
        if save_changes:
            update_activity(activity, user, db, new_name, new_description, new_unit,
                          new_t1_min, new_t1_max, new_t1_points,
                          new_t2_min, new_t2_max, new_t2_points,
                          new_t3_min, new_t3_points)


def update_activity(activity, user, db, name, description, unit,
                   t1_min, t1_max, t1_points, t2_min, t2_max, t2_points, t3_min, t3_points):
    """Update existing activity"""
    try:
        # Check permissions
        if not db.can_user_modify_activity(user['company_id'], activity['id']):
            st.error("Du har ikke tilgang til å redigere denne aktiviteten")
            return
        
        # Build new scoring tiers
        scoring_tiers = {
            "tiers": [
                {"min": t1_min, "max": t1_max, "points": t1_points},
                {"min": t2_min, "max": t2_max, "points": t2_points},
                {"min": t3_min, "max": None, "points": t3_points}
            ]
        }
        
        # Update activity
        updates = {
            'name': name,
            'description': description,
            'unit': unit,
            'scoring_tiers': scoring_tiers
        }
        
        db.update_activity(activity['id'], updates)
        
        st.success(f"✅ Aktivitet '{name}' ble oppdatert!")
        
        # Clear edit state and refresh
        st.session_state[f"editing_{activity['id']}"] = False
        st.rerun()
        
    except Exception as e:
        st.error(f"Feil ved oppdatering: {e}")


def delete_activity(activity, user, db):
    """Delete (deactivate) activity"""
    try:
        # Check permissions
        if not db.can_user_modify_activity(user['company_id'], activity['id']):
            st.error("Du har ikke tilgang til å slette denne aktiviteten")
            return
        
        # Confirm deletion
        if st.button(f"⚠️ Bekreft sletting av '{activity['name']}'", 
                     key=f"confirm_delete_{activity['id']}", 
                     type="secondary"):
            
            db.delete_activity(activity['id'])
            st.success(f"✅ Aktivitet '{activity['name']}' ble slettet")
            st.rerun()
        
    except Exception as e:
        st.error(f"Feil ved sletting: {e}")


def copy_global_activity_to_company(activity, user, db):
    """Create company-specific copy of global activity"""
    try:
        # Create new activity based on global one
        new_activity = db.create_activity(
            name=f"{activity['name']} (Tilpasset)",
            description=f"Bedriftsspesifikk versjon av {activity['description']}",
            unit=activity['unit'],
            scoring_tiers=activity['scoring_tiers'],
            company_id=user['company_id']
        )
        
        st.success(f"✅ Opprettet bedriftsspesifikk kopi av '{activity['name']}'")
        st.info("💡 Du kan nå redigere denne kopien uavhengig av den opprinnelige aktiviteten")
        st.rerun()
        
    except Exception as e:
        st.error(f"Feil ved kopiering: {e}")


def copy_standard_activities_to_company(user, db):
    """Copy all standard activities to company if they don't exist"""
    try:
        # Get global activities
        global_activities = db.get_active_activities()  # Without company_id
        
        # Get existing company activities
        company_activities = db.get_active_activities(company_id=user['company_id'])
        existing_names = [a['name'] for a in company_activities]
        
        copied_count = 0
        
        for global_activity in global_activities:
            # Skip if company already has this activity
            if global_activity['name'] in existing_names:
                continue
            
            # Copy to company
            db.create_activity(
                name=global_activity['name'],
                description=global_activity['description'],
                unit=global_activity['unit'],
                scoring_tiers=global_activity['scoring_tiers'],
                company_id=user['company_id']
            )
            copied_count += 1
        
        if copied_count > 0:
            st.success(f"✅ Kopierte {copied_count} standardaktiviteter til bedriften")
            st.balloons()
            st.rerun()
        else:
            st.info("ℹ️ Alle standardaktiviteter finnes allerede i bedriften")
        
    except Exception as e:
        st.error(f"Feil ved kopiering av standardaktiviteter: {e}")


# ============= EKSISTERENDE FUNKSJONER (Uendret) =============

def show_user_management(user):
    """User management section"""
    st.subheader("👥 Brukeradministrasjon")
    
    try:
        supabase = get_supabase()
        company_users_response = supabase.table('users').select('*').eq('company_id', user['company_id']).order('created_at').execute()
        company_users = company_users_response.data or []
        
        if not company_users:
            st.info("Ingen brukere funnet")
            return
        
        # Summary stats
        admin_count = sum(1 for u in company_users if u['is_admin'])
        regular_count = len(company_users) - admin_count
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("👥 Totale brukere", len(company_users))
        with col2:
            st.metric("👑 Administratorer", admin_count)
        with col3:
            st.metric("👤 Vanlige brukere", regular_count)
        
        st.markdown("---")
        
        # User list with admin actions
        st.markdown("### 📋 Brukerliste")
        
        for company_user in company_users:
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                
                with col1:
                    if company_user['id'] == user['id']:
                        st.write(f"**{company_user['full_name']}** (Deg)")
                    else:
                        st.write(f"**{company_user['full_name']}**")
                    st.caption(f"📧 {company_user['email']}")
                
                with col2:
                    if company_user['is_admin']:
                        st.write("👑 Admin")
                    else:
                        st.write("👤 Bruker")
                
                with col3:
                    reg_date = company_user['created_at'][:10]
                    st.caption(f"Reg: {reg_date}")
                
                with col4:
                    # Admin actions
                    if company_user['id'] != user['id']:  # Can't modify yourself
                        show_user_admin_actions(company_user, user)
                
                st.divider()
        
        # Company code sharing
        st.markdown("---")
        show_company_code_section(user)
        
    except Exception as e:
        st.error(f"Kunne ikke laste brukere: {e}")


def show_user_admin_actions(target_user, admin_user):
    """Show admin actions for a specific user"""
    user_key = target_user['id'][-8:]  # Use last 8 chars of ID for unique key
    
    col1, col2 = st.columns(2)
    
    with col1:
        if target_user['is_admin']:
            if st.button("👤 Fjern admin", key=f"demote_{user_key}", help="Fjern admin-rettigheter"):
                demote_user_from_admin(target_user, admin_user)
        else:
            if st.button("👑 Gi admin", key=f"promote_{user_key}", help="Gi admin-rettigheter"):
                promote_user_to_admin(target_user, admin_user)
    
    with col2:
        if st.button("📊 Se aktivitet", key=f"view_{user_key}", help="Se brukerens aktivitet"):
            show_user_activity_summary(target_user)


def promote_user_to_admin(target_user, admin_user):
    """Promote user to admin"""
    try:
        supabase = get_supabase()
        
        # Update user admin status
        response = supabase.table('users').update({
            'is_admin': True,
            'user_role': 'company_admin'
        }).eq('id', target_user['id']).execute()
        
        if response.data:
            st.success(f"✅ {target_user['full_name']} er nå administrator!")
            st.balloons()
            st.rerun()
        else:
            st.error("❌ Kunne ikke oppdatere brukerrettigheter")
            
    except Exception as e:
        st.error(f"Feil ved oppdatering av rettigheter: {e}")


def demote_user_from_admin(target_user, admin_user):
    """Demote user from admin"""
    try:
        supabase = get_supabase()
        
        # Check if this would leave no admins
        company_users_response = supabase.table('users').select('*').eq('company_id', admin_user['company_id']).execute()
        company_users = company_users_response.data or []
        admin_count = sum(1 for u in company_users if u['is_admin'])
        
        if admin_count <= 1:
            st.error("❌ Kan ikke fjerne siste administrator. Bedriften må ha minst én admin.")
            return
        
        # Update user admin status
        response = supabase.table('users').update({
            'is_admin': False,
            'user_role': 'user'
        }).eq('id', target_user['id']).execute()
        
        if response.data:
            st.success(f"✅ {target_user['full_name']} er ikke lenger administrator")
            st.rerun()
        else:
            st.error("❌ Kunne ikke oppdatere brukerrettigheter")
            
    except Exception as e:
        st.error(f"Feil ved oppdatering av rettigheter: {e}")


def show_user_activity_summary(target_user):
    """Show summary of user's activity"""
    try:
        supabase = get_supabase()
        current_month = date.today().replace(day=1)
        
        # Get or create current month competition
        competition_response = supabase.table('monthly_competitions').select('*').eq('company_id', target_user['company_id']).eq('year_month', current_month.isoformat()).execute()
        
        if not competition_response.data:
            st.write(f"**📊 Aktivitet for {target_user['full_name']} (denne måneden):**")
            st.write("Ingen konkurranser opprettet ennå denne måneden")
            return
        
        competition = competition_response.data[0]
        
        # Get user entries
        user_entries_response = supabase.table('user_entries').select('*, activities(*)').eq('user_id', target_user['id']).eq('competition_id', competition['id']).execute()
        user_entries = user_entries_response.data or []
        
        st.markdown(f"**📊 Aktivitet for {target_user['full_name']} (denne måneden):**")
        
        if user_entries:
            total_points = sum(entry['points'] for entry in user_entries)
            st.write(f"🎯 **Totale poeng:** {total_points}")
            
            for entry in user_entries:
                activity = entry.get('activities', {})
                activity_name = activity.get('name', 'Ukjent')
                activity_unit = activity.get('unit', '')
                st.write(f"• {activity_name}: {entry['value']} {activity_unit} ({entry['points']} poeng)")
        else:
            st.write("Ingen aktiviteter registrert denne måneden")
            
    except Exception as e:
        st.error(f"Kunne ikke laste brukeraktivitet: {e}")


def show_company_code_section(user):
    """Show company code management section - read only for company admin"""
    st.subheader("🔑 Bedriftskode")
    
    try:
        supabase = get_supabase()
        company_response = supabase.table('companies').select('*').eq('id', user['company_id']).execute()
        company = company_response.data[0] if company_response.data else None
        
        if company:
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.info(f"""
                **Bedriftskode:** `{company['company_code']}`
                
                💡 Del denne koden med nye ansatte så de kan registrere seg i systemet
                
                ⚠️ Kun system administrator kan generere ny bedriftskode
                """)
            
            with col2:
                if st.button("📋 Kopier kode", help="Viser koden så du kan kopiere den"):
                    st.code(company['company_code'])
                    st.success("✅ Kode vist over - kopier den manuelt")
                
                st.caption("🔒 Ny kode: Kun system admin")
                
    except Exception as e:
        st.error(f"Kunne ikke laste bedriftsinformasjon: {e}")


def show_company_statistics(user):
    """Company statistics section"""
    st.subheader("📊 Bedriftsstatistikk")
    
    try:
        supabase = get_supabase()
        
        # Get current month competition
        current_month = date.today().replace(day=1)
        competition_response = supabase.table('monthly_competitions').select('*').eq('company_id', user['company_id']).eq('year_month', current_month.isoformat()).execute()
        
        if not competition_response.data:
            # Create competition if it doesn't exist
            competition_create = supabase.table('monthly_competitions').insert({
                'company_id': user['company_id'],
                'year_month': current_month.isoformat(),
                'is_active': True
            }).execute()
            competition = competition_create.data[0] if competition_create.data else None
        else:
            competition = competition_response.data[0]
        
        if not competition:
            st.error("Kunne ikke laste eller opprette konkurransedata")
            return
        
        # Get company users and leaderboard
        company_users_response = supabase.table('users').select('*').eq('company_id', user['company_id']).execute()
        company_users = company_users_response.data or []
        
        leaderboard_response = supabase.rpc('get_competition_leaderboard', {'competition_id_param': competition['id']}).execute()
        leaderboard = leaderboard_response.data or []
        
        # Calculate stats
        total_users = len(company_users)
        active_users = len(leaderboard)
        participation_rate = (active_users / total_users * 100) if total_users > 0 else 0
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("👥 Totalt ansatte", total_users)
        
        with col2:
            st.metric("🏃 Aktive denne måneden", active_users)
        
        with col3:
            st.metric("📈 Deltakelse", f"{participation_rate:.1f}%")
        
        # Current month leaderboard preview
        st.markdown("---")
        st.subheader("🏆 Topp 5 denne måneden")
        
        if leaderboard:
            for i, entry in enumerate(leaderboard[:5], 1):
                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                st.write(f"{medal} **{entry['full_name']}** - {entry['total_points']} poeng ({entry['entries_count']} aktiviteter)")
        else:
            st.info("Ingen aktivitetsregistreringer ennå denne måneden")
        
        # Monthly breakdown
        st.markdown("---")
        show_monthly_breakdown(user)
        
    except Exception as e:
        st.error(f"Kunne ikke laste statistikk: {e}")


def show_monthly_breakdown(user):
    """Show monthly breakdown of competitions"""
    st.subheader("📅 Månedlig oversikt")
    
    try:
        supabase = get_supabase()
        competitions_response = supabase.table('monthly_competitions').select('*').eq('company_id', user['company_id']).order('year_month', desc=True).limit(6).execute()
        competitions = competitions_response.data or []
        
        if len(competitions) <= 1:
            st.info("Ikke nok historiske data ennå - trenger minst 2 måneder")
            return
        
        for comp in competitions[:3]:  # Show last 3 months
            comp_date = datetime.strptime(comp['year_month'], '%Y-%m-%d').date()
            month_name = comp_date.strftime("%B %Y")
            
            leaderboard_response = supabase.rpc('get_competition_leaderboard', {'competition_id_param': comp['id']}).execute()
            comp_leaderboard = leaderboard_response.data or []
            
            comp_active = len(comp_leaderboard)
            comp_total_points = sum(entry['total_points'] for entry in comp_leaderboard)
            
            with st.expander(f"📅 {month_name}"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Aktive brukere", comp_active)
                with col2:
                    st.metric("Totale poeng", comp_total_points)
                with col3:
                    avg_points = comp_total_points / comp_active if comp_active > 0 else 0
                    st.metric("Snitt poeng", f"{avg_points:.1f}")
                
                # Top 3 for this month
                if comp_leaderboard:
                    st.markdown("**🏆 Topp 3:**")
                    for i, entry in enumerate(comp_leaderboard[:3], 1):
                        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉"
                        st.write(f"{medal} {entry['full_name']} - {entry['total_points']} poeng")
        
    except Exception as e:
        st.error(f"Kunne ikke laste månedlig oversikt: {e}")


def show_competition_management(user):
    """Competition management section"""
    st.subheader("🏆 Konkurranseadministrasjon")
    
    try:
        supabase = get_supabase()
        competitions_response = supabase.table('monthly_competitions').select('*').eq('company_id', user['company_id']).order('year_month', desc=True).limit(12).execute()
        competitions = competitions_response.data or []
        
        if not competitions:
            st.info("Ingen konkurranser funnet for din bedrift ennå.")
            st.info("💡 Konkurranser opprettes automatisk når brukere begynner å registrere aktiviteter")
            return
        
        current_month = date.today().replace(day=1)
        
        st.markdown("### 📅 Konkurranseoversikt")
        
        for comp in competitions:
            comp_date = datetime.strptime(comp['year_month'], '%Y-%m-%d').date()
            month_name = comp_date.strftime("%B %Y")
            
            is_current = comp_date == current_month
            
            leaderboard_response = supabase.rpc('get_competition_leaderboard', {'competition_id_param': comp['id']}).execute()
            leaderboard = leaderboard_response.data or []
            
            with st.expander(f"{'🔄 ' if is_current else '📅 '}{month_name}"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write(f"**Status:** {'Pågående' if is_current else 'Fullført'}")
                    st.write(f"**Deltakere:** {len(leaderboard)}")
                
                with col2:
                    total_points = sum(entry['total_points'] for entry in leaderboard)
                    st.write(f"**Totale poeng:** {total_points}")
                    
                    avg_points = total_points / len(leaderboard) if leaderboard else 0
                    st.write(f"**Snitt poeng:** {avg_points:.1f}")
                
                with col3:
                    if leaderboard:
                        winner = leaderboard[0]
                        st.write(f"**🏆 Førsteplass:** {winner['full_name']}")
                        st.write(f"**Poeng:** {winner['total_points']}")
                    else:
                        st.write("**Ingen deltakere**")
                
                # Show full leaderboard
                if leaderboard:
                    st.markdown("**📊 Komplett leaderboard:**")
                    for i, entry in enumerate(leaderboard, 1):
                        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                        st.write(f"{medal} {entry['full_name']} - {entry['total_points']} poeng ({entry['entries_count']} aktiviteter)")
                
                # Export data for this competition
                if st.button("📊 Eksporter data", key=f"export_{comp['id']}"):
                    export_competition_data(comp, leaderboard, month_name)
        
    except Exception as e:
        st.error(f"Kunne ikke laste konkurranser: {e}")


def export_competition_data(competition, leaderboard, month_name):
    """Export competition data"""
    try:
        st.success(f"📊 **Konkurransedata for {month_name}:**")
        
        if leaderboard:
            total_points = sum(entry['total_points'] for entry in leaderboard)
            total_entries = sum(entry['entries_count'] for entry in leaderboard)
            
            # Create exportable text
            export_text = f"Konkurranseresultater - {month_name}\n"
            export_text += "=" * 40 + "\n\n"
            export_text += f"Totale deltakere: {len(leaderboard)}\n"
            export_text += f"Totale poeng: {total_points}\n"
            export_text += f"Totale aktivitetsregistreringer: {total_entries}\n\n"
            export_text += "LEADERBOARD:\n"
            export_text += "-" * 20 + "\n"
            
            for i, entry in enumerate(leaderboard, 1):
                export_text += f"{i}. {entry['full_name']} - {entry['total_points']} poeng ({entry['entries_count']} aktiviteter)\n"
            
            st.text_area("📋 Kopier dataene under:", export_text, height=200)
            st.info("💡 Merk teksten over og kopier den for å eksportere dataene")
        else:
            st.write("Ingen data å eksportere for denne måneden")
            
    except Exception as e:
        st.error(f"Kunne ikke eksportere data: {e}")


def show_admin_settings(user):
    """Admin settings section"""
    st.subheader("⚙️ Administrasjonsinnstillinger")
    
    try:
        supabase = get_supabase()
        company_response = supabase.table('companies').select('*').eq('id', user['company_id']).execute()
        company = company_response.data[0] if company_response.data else None
        
        if not company:
            st.error("Kunne ikke laste bedriftsinformasjon")
            return
        
        # Company info (read-only)
        st.markdown("### 🏢 Bedriftsinformasjon")
        
        st.info(f"""
        **Bedriftsnavn:** {company['name']}
        **Bedriftskode:** {company['company_code']}
        **Opprettet:** {company['created_at'][:10]}
        """)
        
        st.caption("💡 Kontakt system administrator for å endre bedriftsnavn")
        
        st.markdown("---")
        
        # Competition management tools
        st.markdown("### 🏆 Konkurranseadministrasjon")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🎯 Start ny månedlig konkuranse", help="Opprett konkurranseperiode for neste måned"):
                create_next_month_competition(user)
        
        with col2:
            if st.button("📊 Eksporter alle resultater", help="Last ned alle konkurranseresultater"):
                export_all_competition_data(user)
        
        st.markdown("---")
        
        # User management tools
        st.markdown("### 👥 Brukeradministrasjon")
        
        # Bulk admin operations
        st.markdown("#### Masseoppdateringer")
        
        company_users_response = supabase.table('users').select('*').eq('company_id', user['company_id']).execute()
        company_users = company_users_response.data or []
        
        # Filter non-admin users for bulk operations
        non_admin_users = [u for u in company_users if not u['is_admin'] and u['id'] != user['id']]
        
        if non_admin_users:
            st.write("**Gi admin-rettigheter til flere brukere:**")
            
            user_names = [f"{u['full_name']} ({u['email']})" for u in non_admin_users]
            selected_users = st.multiselect(
                "Velg brukere som skal bli administratorer:",
                user_names,
                help="Hold Ctrl/Cmd for å velge flere"
            )
            
            if selected_users and st.button("👑 Gi admin til valgte brukere"):
                promote_multiple_users(non_admin_users, selected_users, user)
        else:
            st.info("Alle ansatte er allerede administratorer")
        
        st.markdown("---")
        
        # Activity overview (read-only)
        st.markdown("### 🏃 Aktivitetsoversikt")
        
        # Get company activities
        db = get_db_helper()
        activities = db.get_active_activities(company_id=user['company_id'])
        
        st.write("**Tilgjengelige aktiviteter for dine ansatte:**")
        
        if activities:
            activity_summary = []
            for activity in activities:
                scoring_tiers = activity['scoring_tiers']['tiers']
                max_points = max(tier['points'] for tier in scoring_tiers)
                
                activity_type = ""
                if activity.get('company_id') == user['company_id']:
                    activity_type = " 🏢"
                elif activity.get('company_id') is None:
                    activity_type = " 🌐"
                
                activity_summary.append(f"• **{activity['name']}**{activity_type} ({activity['unit']}) - maks {max_points} poeng")
            
            for summary in activity_summary:
                st.write(summary)
        else:
            st.info("Ingen aktiviteter tilgjengelig")
            st.info("💡 Gå til 'Aktiviteter'-fanen for å legge til aktiviteter")
        
        st.markdown("---")
        
        # Admin info
        st.markdown("### ℹ️ Administrator-informasjon")
        
        admin_count = sum(1 for u in company_users if u['is_admin'])
        total_users = len(company_users)
        
        st.info(f"""
        **Din rolle:** Administrator
        **Totale administratorer:** {admin_count}
        **Totale ansatte:** {total_users}
        **Siste oppdatering:** {datetime.now().strftime('%Y-%m-%d %H:%M')}
        """)
        
    except Exception as e:
        st.error(f"Kunne ikke laste innstillinger: {e}")


def create_next_month_competition(user):
    """Create competition for next month"""
    try:
        supabase = get_supabase()
        
        # Calculate next month
        today = date.today()
        if today.month == 12:
            next_month = date(today.year + 1, 1, 1)
        else:
            next_month = date(today.year, today.month + 1, 1)
        
        # Check if competition already exists
        existing_comp = supabase.table('monthly_competitions').select('*').eq('company_id', user['company_id']).eq('year_month', next_month.isoformat()).execute()
        
        if existing_comp.data:
            st.warning(f"Konkurranseperiode for {next_month.strftime('%B %Y')} eksisterer allerede")
            return
        
        # Create new competition
        response = supabase.table('monthly_competitions').insert({
            'company_id': user['company_id'],
            'year_month': next_month.isoformat(),
            'is_active': True
        }).execute()
        
        if response.data:
            st.success(f"✅ Ny konkurranseperiode opprettet for {next_month.strftime('%B %Y')}")
            st.balloons()
        else:
            st.error("❌ Kunne ikke opprette konkurranseperiode")
            
    except Exception as e:
        st.error(f"Feil ved opprettelse av konkurranseperiode: {e}")


def export_all_competition_data(user):
    """Export all competition data for the company"""
    try:
        supabase = get_supabase()
        
        # Get all competitions
        competitions_response = supabase.table('monthly_competitions').select('*').eq('company_id', user['company_id']).order('year_month', desc=True).execute()
        competitions = competitions_response.data or []
        
        if not competitions:
            st.warning("Ingen konkurranser å eksportere")
            return
        
        # Get company info
        company_response = supabase.table('companies').select('*').eq('id', user['company_id']).execute()
        company = company_response.data[0] if company_response.data else {'name': 'Ukjent bedrift'}
        
        # Create comprehensive export
        export_text = f"KOMPLETT KONKURRANSEHISTORIKK - {company['name']}\n"
        export_text += f"Eksportert: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        export_text += "=" * 60 + "\n\n"
        
        for comp in competitions:
            comp_date = datetime.strptime(comp['year_month'], '%Y-%m-%d').date()
            month_name = comp_date.strftime("%B %Y")
            
            leaderboard_response = supabase.rpc('get_competition_leaderboard', {'competition_id_param': comp['id']}).execute()
            leaderboard = leaderboard_response.data or []
            
            export_text += f"MÅNED: {month_name}\n"
            export_text += "-" * 30 + "\n"
            
            if leaderboard:
                total_points = sum(entry['total_points'] for entry in leaderboard)
                export_text += f"Deltakere: {len(leaderboard)}\n"
                export_text += f"Totale poeng: {total_points}\n\n"
                
                for i, entry in enumerate(leaderboard, 1):
                    export_text += f"{i:2d}. {entry['full_name']:25} - {entry['total_points']:4d} poeng ({entry['entries_count']} aktiviteter)\n"
            else:
                export_text += "Ingen deltakere\n"
            
            export_text += "\n" + "=" * 60 + "\n\n"
        
        st.text_area("📋 Komplett konkurransehistorikk (kopier teksten):", export_text, height=400)
        st.success("✅ All konkurransedata eksportert")
        
    except Exception as e:
        st.error(f"Kunne ikke eksportere data: {e}")


def promote_multiple_users(all_users, selected_user_names, admin_user):
    """Promote multiple users to admin"""
    try:
        supabase = get_supabase()
        
        # Find users to promote
        users_to_promote = []
        for user_name in selected_user_names:
            for user in all_users:
                if f"{user['full_name']} ({user['email']})" == user_name:
                    users_to_promote.append(user)
                    break
        
        if not users_to_promote:
            st.error("Ingen brukere valgt")
            return
        
        # Promote each user
        success_count = 0
        for user in users_to_promote:
            response = supabase.table('users').update({
                'is_admin': True,
                'user_role': 'company_admin'
            }).eq('id', user['id']).execute()
            
            if response.data:
                success_count += 1
        
        if success_count > 0:
            st.success(f"✅ {success_count} brukere ble gjort til administratorer!")
            
            # Show who was promoted
            st.write("**Nye administratorer:**")
            for user in users_to_promote[:success_count]:
                st.write(f"• {user['full_name']}")
            
            st.balloons()
            st.rerun()
        else:
            st.error("❌ Kunne ikke oppdatere noen brukere")
            
    except Exception as e:
        st.error(f"Feil ved masseoppdatering: {e}")
