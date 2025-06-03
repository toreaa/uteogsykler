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


# Remove these functions since company admin can't generate new codes anymore:
# - show_generate_new_code_section()
# - generate_new_company_code()


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
        
        activities_response = supabase.table('activities').select('*').eq('is_active', True).order('name').execute()
        activities = activities_response.data or []
        
        st.write("**Tilgjengelige aktiviteter for dine ansatte:**")
        
        if activities:
            activity_summary = []
            for activity in activities:
                scoring_tiers = activity['scoring_tiers']['tiers']
                max_points = max(tier['points'] for tier in scoring_tiers)
                activity_summary.append(f"• **{activity['name']}** ({activity['unit']}) - maks {max_points} poeng")
            
            for summary in activity_summary:
                st.write(summary)
        else:
            st.info("Ingen aktiviteter tilgjengelig")
        
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
