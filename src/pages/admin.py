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
        
        st.write(f"**Totalt antall brukere:** {len(company_users)}")
        
        # User list
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
                    # Admin actions (placeholder)
                    if company_user['id'] != user['id']:  # Can't modify yourself
                        if st.button("⚙️", key=f"admin_{company_user['id']}", help="Administrer bruker"):
                            show_user_admin_options(company_user, user)
                
                st.divider()
        
        # Company code sharing
        st.markdown("---")
        st.subheader("🔑 Bedriftskode")
        
        company = db.get_company_by_id(user['company_id'])
        if company:
            st.info(f"**Bedriftskode:** `{company['company_code']}`")
            st.caption("Del denne koden med nye ansatte så de kan registrere seg")
            
            if st.button("🔄 Generer ny bedriftskode", help="Lager ny kode (den gamle slutter å virke)"):
                st.warning("🚧 Funksjonalitet for å endre bedriftskode kommer snart")
        
    except Exception as e:
        st.error(f"Kunne ikke laste brukere: {e}")


def show_user_admin_options(target_user, admin_user):
    """Show admin options for a specific user"""
    st.markdown(f"**Administrer: {target_user['full_name']}**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if target_user['is_admin']:
            if st.button("👤 Fjern admin-rettigheter", key=f"demote_{target_user['id']}"):
                st.warning("🚧 Funksjonalitet kommer snart")
        else:
            if st.button("👑 Gi admin-rettigheter", key=f"promote_{target_user['id']}"):
                st.warning("🚧 Funksjonalitet kommer snart")
    
    with col2:
        if st.button("🗑️ Fjern bruker", key=f"remove_{target_user['id']}", type="secondary"):
            st.error("🚧 Brukersletting er ikke implementert ennå")


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
                    st.write(f"**
