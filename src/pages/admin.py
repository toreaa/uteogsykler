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

from utils.database_helpers import get_db_helper
from utils.supabase_client import get_supabase


def show_admin_page(user):
    """Admin page - administrative functions"""
    if not user['is_admin']:
        st.error("❌ Du har ikke tilgang til admin-området")
        st.info("Kun administratorer kan se denne siden")
        return
    
    st.title("👑 Administrasjon")
    st.markdown(f"Administrator-panel for **{user['full_name']}**")
    
    # Admin tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "👥 Brukere", 
        "📊 Statistikk", 
        "🏆 Konkurranser",
        "⚙️ Innstillinger"
    ])
    
    with tab1:
        show_user_management(user)
    
    with tab2:
        show_company_statistics(user)
    
    with tab3:
        show_competition_management(user)
    
    with tab4:
        show_admin_settings(user)


def show_user_management(user):
    """User management section"""
    st.subheader("👥 Brukeradministrasjon")
    
    try:
        db = get_db_helper()
        company_users = db.get_users_by_company(user['company_id'])
        
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
        
        # User list with admin functions
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
        st.subheader("🔑 Bedriftskode")
        
        company = db.get_company_by_id(user['company_id'])
        if company:
            st.info(f"""
            **Bedriftskode:** `{company['company_code']}`
            
            💡 Del denne koden med nye ansatte så de kan registrere seg i systemet
            """)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📋 Kopier kode", help="Kopierer bedriftskoden"):
                    st.code(company['company_code'])
                    st.success("✅ Kode vist over - kopier den manuelt")
            
            with col2:
                if st.button("🔄 Generer ny bedriftskode", help="Lager ny kode (den gamle slutter å virke)"):
                    generate_new_company_code(user, company)
        
    except Exception as e:
        st.error(f"Kunne ikke laste brukere: {e}")


def show_user_admin_actions(target_user, admin_user):
    """Show admin actions for a specific user"""
    
    # Create a unique key for this user's actions
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
            'is_admin': True
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
        # Check if this would leave no admins
        db = get_db_helper()
        company_users = db.get_users_by_company(admin_user['company_id'])
        admin_count = sum(1 for u in company_users if u['is_admin'])
        
        if admin_count <= 1:
            st.error("❌ Kan ikke fjerne siste administrator. Bedriften må ha minst én admin.")
            return
        
        supabase = get_supabase()
        
        # Update user admin status
        response = supabase.table('users').update({
            'is_admin': False
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
        db = get_db_helper()
        current_month = date.today().replace(day=1)
        competition = db.get_or_create_monthly_competition(target_user['company_id'], current_month)
        
        user_entries = db.get_user_entries_for_competition(target_user['id'], competition['id'])
        
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


def generate_new_company_code(user, company):
    """Generate new company code"""
    if st.button("⚠️ Bekreft ny kode", type="secondary", help="Dette vil gjøre den gamle koden ugyldig"):
        try:
            supabase = get_supabase()
            
            # Generate new code using database function
            code_response = supabase.rpc('generate_company_code').execute()
            new_code = code_response.data
            
            # Update company with new code
            response = supabase.table('companies').update({
                'company_code': new_code
            }).eq('id', company['id']).execute()
            
            if response.data:
                st.success(f"✅ Ny bedriftskode generert: **{new_code}**")
                st.warning("⚠️ Den gamle koden fungerer ikke lenger")
                st.rerun()
            else:
                st.error("❌ Kunne ikke generere ny kode")
                
        except Exception as e:
            st.error(f"Feil ved generering av ny kode: {e}")


def show_company_statistics(user):
    """Company statistics section"""
    st.subheader("📊 Bedriftsstatistikk")
    
    try:
        db = get_db_helper()
        
        # Get current month competition
        current_month = date.today().replace(day=1)
        competition = db.get_or_create_monthly_competition(user['company_id'], current_month)
        
        # Overall company stats
        company_users = db.get_users_by_company(user['company_id'])
        leaderboard = db.get_leaderboard_for_competition(competition['id'])
        
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
        
        # Monthly breakdown
        st.markdown("---")
        st.subheader("📅 Månedlig oversikt")
        
        competitions = db.get_competitions_for_company(user['company_id'], limit=6)
        
        for comp in competitions[:3]:  # Show last 3 months
            comp_date = datetime.strptime(comp['year_month'], '%Y-%m-%d').date()
            month_name = comp_date.strftime("%B %Y")
            
            comp_leaderboard = db.get_leaderboard_for_competition(comp['id'])
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
        
        # Activity statistics
        st.markdown("---")
        show_activity_statistics(user, current_month)
        
    except Exception as e:
        st.error(f"Kunne ikke laste statistikk: {e}")


def show_activity_statistics(user, current_month):
    """Show activity statistics for the company"""
    st.subheader("🏃 Aktivitetsstatistikk")
    
    try:
        db = get_db_helper()
        competition = db.get_or_create_monthly_competition(user['company_id'], current_month)
        
        # Get all activities
        activities = db.get_active_activities()
        
        if not activities:
            st.info("Ingen aktiviteter tilgjengelig")
            return
        
        activity_stats = {}
        
        # Get all entries for current month
        company_users = db.get_users_by_company(user['company_id'])
        
        for company_user in company_users:
            user_entries = db.get_user_entries_for_competition(company_user['id'], competition['id'])
            
            for entry in user_entries:
                activity = entry.get('activities', {})
                activity_name = activity.get('name', 'Ukjent')
                
                if activity_name not in activity_stats:
                    activity_stats[activity_name] = {
                        'users': set(),
                        'total_value': 0,
                        'total_points': 0,
                        'unit': activity.get('unit', '')
                    }
                
                activity_stats[activity_name]['users'].add(company_user['id'])
                activity_stats[activity_name]['total_value'] += entry['value']
                activity_stats[activity_name]['total_points'] += entry['points']
        
        # Display activity stats
        for activity_name, stats in activity_stats.items():
            with st.expander(f"🏃 {activity_name}"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Aktive brukere", len(stats['users']))
                
                with col2:
                    st.metric(f"Total {stats['unit']}", f"{stats['total_value']:.1f}")
                
                with col3:
                    st.metric("Totale poeng", stats['total_points'])
        
        if not activity_stats:
            st.info("Ingen aktiviteter registrert denne måneden")
    
    except Exception as e:
        st.error(f"Kunne ikke laste aktivitetsstatistikk: {e}")


def show_competition_management(user):
    """Competition management section"""
    st.subheader("🏆 Konkurranseadministrasjon")
    
    try:
        db = get_db_helper()
        competitions = db.get_competitions_for_company(user['company_id'], limit=12)
        
        if not competitions:
            st.info("Ingen konkurranser funnet")
            return
        
        current_month = date.today().replace(day=1)
        
        st.markdown("### 📅 Konkurranseoversikt")
        
        for comp in competitions:
            comp_date = datetime.strptime(comp['year_month'], '%Y-%m-%d').date()
            month_name = comp_date.strftime("%B %Y")
            
            is_current = comp_date == current_month
            
            with st.expander(f"{'🔄 ' if is_current else '📅 '}{month_name}"):
                leaderboard = db.get_leaderboard_for_competition(comp['id'])
                
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
                        st.write(f"**🏆 Vinner:** {winner['full_name']}")
                        st.write(f"**Poeng:** {winner['total_points']}")
                    else:
                        st.write("**Ingen deltakere**")
                
                # Show full leaderboard for this competition
                if leaderboard:
                    st.markdown("**📊 Full leaderboard:**")
                    for i, entry in enumerate(leaderboard, 1):
                        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                        st.write(f"{medal} {entry['full_name']} - {entry['total_points']} poeng ({entry['entries_count']} aktiviteter)")
                
                # Competition actions
                if is_current:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if st.button("📊 Eksporter data", key=f"export_{comp['id']}"):
                            export_competition_data(comp, leaderboard)
                    
                    with col2:
                        if st.button("🔄 Nullstill konkuranse", key=f"reset_{comp['id']}", type="secondary"):
                            st.warning("⚠️ Nullstilling av konkurranser er ikke implementert ennå")
        
    except Exception as e:
        st.error(f"Kunne ikke laste konkurranser: {e}")


def export_competition_data(competition, leaderboard):
    """Export competition data"""
    try:
        comp_date = datetime.strptime(competition['year_month'], '%Y-%m-%d').date()
        month_name = comp_date.strftime("%B %Y")
        
        st.success(f"📊 **Konkurransedata for {month_name}:**")
        st.write(f"**Deltakere:** {len(leaderboard)}")
        
        if leaderboard:
            total_points = sum(entry['total_points'] for entry in leaderboard)
            total_entries = sum(entry['entries_count'] for entry in leaderboard)
            
            st.write(f"**Totale poeng:** {total_points}")
            st.write(f"**Totale aktivitetsregistreringer:** {total_entries}")
            
            # Create exportable text
            export_text = f"Konkurranseresultater - {month_name}\n"
            export_text += "=" * 40 + "\n\n"
            
            for i, entry in enumerate(leaderboard, 1):
                export_text += f"{i}. {entry['full_name']} - {entry['total_points']} poeng ({entry['entries_count']} aktiviteter)\n"
            
            st.text_area("📋 Kopier dataene under:", export_text, height=200)
            st.info("💡 Merk teksten over og kopier den for å eksportere dataene")
        else:
            st.write("Ingen data å eksportere")
            
    except Exception as e:
        st.error(f"Kunne ikke eksportere data: {e}")


def show_admin_settings(user):
    """Admin settings section"""
    st.subheader("⚙️ Administrasjonsinnstillinger")
    
    # Company settings
    st.markdown("### 🏢 Bedriftsinnstillinger")
    
    try:
        db = get_db_helper()
        company = db.get_company_by_id(user['company_id'])
        
        if company:
            st.info(f"""
            **Bedriftsnavn:** {company['name']}
            **Bedriftskode:** {company['company_code']}
            **Opprettet:** {company['created_at'][:10]}
            """)
            
            # Company name editing (placeholder for now)
            st.markdown("#### Endre bedriftsnavn")
            new_company_name = st.text_input(
                "Nytt bedriftsnavn",
                placeholder=company['name'],
                help="Skriv inn nytt navn for bedriften"
            )
            
            if st.button("💾 Oppdater bedriftsnavn", disabled=not new_company_name):
                if new_company_name and new_company_name != company['name']:
                    update_company_name(company, new_company_name)
                else:
                    st.warning("Skriv inn et nytt navn som er forskjellig fra det nåværende")
        
        st.markdown("---")
        
        # Activity management
        st.markdown("### 🏃 Aktivitetsinnstillinger")
        
        activities = db.get_active_activities()
        
        st.write("**Tilgjengelige aktiviteter:**")
        for activity in activities:
            with st.expander(f"🏃 {activity['name']} ({activity['unit']})"):
                st.write(f"**Beskrivelse:** {activity['description']}")
                st.write(f"**Enhet:** {activity['unit']}")
                st.write(f"**Status:** {'✅ Aktiv' if activity['is_active'] else '❌ Inaktiv'}")
                
                # Show scoring tiers
                scoring_tiers = activity['scoring_tiers']['tiers']
                st.write("**Poengskala:**")
                for tier in scoring_tiers:
                    min_val = tier['min']
                    max_val = tier.get('max', '∞')
                    points = tier['points']
                    st.write(f"  • {min_val} - {max_val} {activity['unit']} = {points} poeng")
        
        st.markdown("---")
        
        # Data management
        st.markdown("### 📊 Dataadministrasjon")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📄 Eksporter alle data", help="Eksporter all bedriftsdata"):
                export_company_data(user)
        
        with col2:
            if st.button("📊 Statistikkoversikt", help="Vis detaljert statistikk"):
                show_detailed_statistics(user)
        
        st.markdown("---")
        
        # System info
        st.markdown("### ℹ️ Systeminformasjon")
        
        st.info(f"""
        **Siste oppdatering:** {datetime.now().strftime('%Y-%m-%d %H:%M')}
        **Admin:** {user['full_name']}
        **Bedrifts-ID:** `{user['company_id']}`
        """)
        
    except Exception as e:
        st.error(f"Kunne ikke laste innstillinger: {e}")


def update_company_name(company, new_name):
    """Update company name"""
    try:
        supabase = get_supabase()
        
        response = supabase.table('companies').update({
            'name': new_name.strip()
        }).eq('id', company['id']).execute()
        
        if response.data:
            st.success(f"✅ Bedriftsnavn oppdatert til: **{new_name}**")
            st.rerun()
        else:
            st.error("❌ Kunne ikke oppdatere bedriftsnavn")
            
    except Exception as e:
        st.error(f"Feil ved oppdatering av bedriftsnavn: {e}")


def show_detailed_statistics(user):
    """Show detailed company statistics"""
    try:
        db = get_db_helper()
        
        st.markdown("**📊 Detaljert statistikk:**")
        
        # Get all competitions
        competitions = db.get_competitions_for_company(user['company_id'], limit=12)
        company_users = db.get_users_by_company(user['company_id'])
        
        total_competitions = len(competitions)
        total_users = len(company_users)
        
        # Calculate total activity across all time
        total_entries = 0
        total_points = 0
        
        for comp in competitions:
            leaderboard = db.get_leaderboard_for_competition(comp['id'])
            for entry in leaderboard:
                total_entries += entry['entries_count']
                total_points += entry['total_points']
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("🏆 Konkurranser", total_competitions)
        
        with col2:
            st.metric("👥 Brukere", total_users)
        
        with col3:
            st.metric("📊 Registreringer", total_entries)
        
        with col4:
            st.metric("🎯 Totale poeng", total_points)
        
        if total_users > 0:
            avg_entries = total_entries / total_users
            avg_points = total_points / total_users
            
            st.write(f"**📈 Gjennomsnitt per bruker:**")
            st.write(f"• {avg_entries:.1f} registreringer")
            st.write(f"• {avg_points:.1f} poeng")
        
    except Exception as e:
        st.error(f"Kunne ikke laste detaljert statistikk: {e}")


def export_company_data(user):
    """Export all company data"""
    try:
        db = get_db_helper()
        
        # Get all data for the company
        company = db.get_company_by_id(user['company_id'])
        company_users = db.get_users_by_company(user['company_id'])
        competitions = db.get_competitions_for_company(user['company_id'], limit=24)
        
        total_entries = 0
        
        for comp in competitions:
            for company_user in company_users:
                entries = db.get_user_entries_for_competition(company_user['id'], comp['id'])
                total_entries += len(entries)
        
        st.success(f"✅ **Dataeksport for {company['name']}**")
        st.write(f"**Brukere:** {len(company_users)}")
        st.write(f"**Konkurranser:** {len(competitions)} måneder")
        st.write(f"**Aktivitetsregistreringer:** {total_entries}")
        
        # Create summary export text
        export_summary = f"Bedriftsdata - {company['name']}\n"
        export_summary += f"Bedriftskode: {company['company_code']}\n"
        export_summary += f"Eksportert: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        export_summary += "=" * 50 + "\n\n"
        
        export_summary += f"Brukere ({len(company_users)}):\n"
        for user_info in company_users:
            role = "Admin" if user_info['is_admin'] else "Bruker"
            export_summary += f"- {user_info['full_name']} ({user_info['email']}) - {role}\n"
        
        export_summary += f"\nKonkurranser ({len(competitions)}):\n"
        for comp in competitions:
            comp_date = datetime.strptime(comp['year_month'], '%Y-%m-%d').date()
            month_name = comp_date.strftime("%B %Y")
            leaderboard = db.get_leaderboard_for_competition(comp['id'])
            export_summary += f"- {month_name}: {len(leaderboard)} deltakere\n"
        
        st.text_area("📋 Sammendrag (kopier teksten):", export_summary, height=300)
        st.info("💡 Full data-eksport med detaljerte aktivitetsdata kommer snart")
        
    except Exception as e:
        st.error(f"Kunne ikke eksportere data: {e}")
