"""
Dashboard page for Konkurranseapp
Main overview and quick actions for users
"""

import streamlit as st
from datetime import date
import sys
import os

# Add src to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.database_helpers import get_db_helper


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
        
        # Show monthly summary if we have data
        if user_entries:
            st.markdown("---")
            show_monthly_summary(user, competition, user_entries, db)
        
    except Exception as e:
        st.error(f"Kunne ikke laste dashboard-data: {e}")


def show_monthly_summary(user, competition, user_entries, db):
    """Show monthly summary statistics"""
    st.subheader("📊 Månedens sammendrag")
    
    try:
        # Calculate user's total points
        user_total_points = sum(entry['points'] for entry in user_entries)
        
        # Get leaderboard to see position
        leaderboard = db.get_leaderboard_for_competition(competition['id'])
        
        user_rank = None
        total_participants = len(leaderboard)
        
        for i, entry in enumerate(leaderboard, 1):
            if entry['user_id'] == user['id']:
                user_rank = i
                break
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "🏅 Din plassering", 
                f"#{user_rank}" if user_rank else "Ikke rangert",
                delta=f"av {total_participants} deltakere"
            )
        
        with col2:
            # Calculate average points
            if total_participants > 0:
                total_all_points = sum(entry['total_points'] for entry in leaderboard)
                avg_points = total_all_points / total_participants
                delta_from_avg = user_total_points - avg_points
                st.metric(
                    "📊 Vs. snitt",
                    f"{user_total_points} poeng",
                    delta=f"{delta_from_avg:+.1f} poeng"
                )
            else:
                st.metric("📊 Dine poeng", f"{user_total_points} poeng")
        
        with col3:
            # Show progress to next tier (if applicable)
            if user_entries:
                # Find activity with most potential for improvement
                best_improvement = None
                best_activity = None
                
                for entry in user_entries:
                    activity = entry.get('activities', {})
                    if activity:
                        current_points = entry['points']
                        scoring_tiers = activity['scoring_tiers']['tiers']
                        
                        # Check if user can get to next tier
                        for tier in scoring_tiers:
                            if tier['points'] > current_points:
                                points_to_gain = tier['points'] - current_points
                                if best_improvement is None or points_to_gain < best_improvement:
                                    best_improvement = points_to_gain
                                    best_activity = activity['name']
                                break
                
                if best_improvement:
                    st.metric(
                        "🎯 Neste nivå",
                        f"+{best_improvement} poeng",
                        delta=f"i {best_activity}"
                    )
                else:
                    st.metric("🎯 Status", "Alle nivåer nådd! 🏆")
        
        # Show encouragement message
        if user_rank:
            if user_rank == 1:
                st.success("🥇 Du leder! Fortsett det gode arbeidet!")
            elif user_rank <= 3:
                st.success(f"🥉 Flott jobb! Du er på plass {user_rank}!")
            elif user_rank <= total_participants // 2:
                st.info(f"📈 Du er i øvre halvdel (plass {user_rank})! Fortsett så kommer du høyere!")
            else:
                st.info(f"💪 Du er med i konkurransen! Hver aktivitet teller!")
    
    except Exception as e:
        st.warning("Kunne ikke laste månedssammendrag")
