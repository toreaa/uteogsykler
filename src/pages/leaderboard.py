"""
Leaderboard page for Konkurranseapp
Shows company rankings and statistics
"""

import streamlit as st
from datetime import datetime, date
import sys
import os

# Add src to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.database_helpers import get_db_helper


def show_leaderboard_page(user):
    """Leaderboard page - show company rankings"""
    st.title("🏆 Leaderboard")
    
    try:
        db = get_db_helper()
        
        # Get available competitions for company
        competitions = db.get_competitions_for_company(user['company_id'], limit=12)
        
        if not competitions:
            st.info("Ingen konkurranser funnet for din bedrift ennå.")
            return
        
        # Competition selector
        competition_options = []
        current_month = date.today().replace(day=1)
        
        for comp in competitions:
            comp_date = datetime.strptime(comp['year_month'], '%Y-%m-%d').date()
            month_name = comp_date.strftime("%B %Y")
            
            if comp_date == current_month:
                month_name += " (Pågående)"
                
            competition_options.append((month_name, comp))
        
        # Default to current month
        default_index = 0
        
        selected_display, selected_competition = st.selectbox(
            "📅 Velg måned:",
            competition_options,
            index=default_index,
            format_func=lambda x: x[0]
        )
        
        # Show leaderboard for selected competition
        show_competition_leaderboard(user, selected_competition, db)
        
        # Show additional stats
        st.markdown("---")
        show_leaderboard_stats(user, selected_competition, db)
        
    except Exception as e:
        st.error(f"Feil ved lasting av leaderboard: {e}")


def show_competition_leaderboard(user, competition, db):
    """Show leaderboard for specific competition"""
    try:
        # Get leaderboard data
        leaderboard = db.get_leaderboard_for_competition(competition['id'])
        
        if not leaderboard:
            st.info("Ingen deltakere i denne konkurranseperioden ennå.")
            return
        
        comp_date = datetime.strptime(competition['year_month'], '%Y-%m-%d').date()
        month_name = comp_date.strftime("%B %Y")
        current_month = date.today().replace(day=1)
        
        # Header
        st.subheader(f"🥇 Leaderboard for {month_name}")
        
        if comp_date == current_month:
            st.info("🔄 Dette er den pågående konkurranseperioden")
        
        # Find user's position
        user_rank = None
        user_points = 0
        for entry in leaderboard:
            if entry['user_id'] == user['id']:
                user_rank = entry['rank']
                user_points = entry['total_points']
                break
        
        # Show user's position prominently
        if user_rank:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("🏅 Din plassering", f"#{user_rank}")
            with col2:
                st.metric("🎯 Dine poeng", user_points)
            with col3:
                if len(leaderboard) > 1:
                    if user_rank == 1:
                        st.metric("📊 Status", "🥇 Leder!")
                    else:
                        leader_points = leaderboard[0]['total_points']
                        points_behind = leader_points - user_points
                        st.metric("📊 Bak ledelsen", f"{points_behind} poeng")
                else:
                    st.metric("📊 Status", "Eneste deltaker")
        
        st.markdown("---")
        
        # Leaderboard table
        st.subheader("📋 Fullstendig rangering")
        
        # Create medals for top 3
        def get_medal(rank):
            if rank == 1:
                return "🥇"
            elif rank == 2:
                return "🥈"
            elif rank == 3:
                return "🥉"
            else:
                return f"#{rank}"
        
        # Display leaderboard
        for entry in leaderboard:
            rank = entry['rank']
            name = entry['full_name']
            points = entry['total_points']
            entries_count = entry['entries_count']
            
            # Highlight current user
            if entry['user_id'] == user['id']:
                # Use Streamlit's built-in highlighting instead of custom HTML
                st.info(f"{get_medal(rank)} **{name} (Du)** - {points} poeng • {entries_count} aktiviteter")
            else:
                col1, col2, col3 = st.columns([1, 3, 2])
                with col1:
                    st.write(get_medal(rank))
                with col2:
                    st.write(f"**{name}**")
                with col3:
                    st.write(f"{points} poeng • {entries_count} aktiviteter")
        
        # Show participation stats
        total_participants = len(leaderboard)
        st.caption(f"👥 {total_participants} deltaker{'e' if total_participants != 1 else ''} denne måneden")
        
    except Exception as e:
        st.error(f"Feil ved visning av leaderboard: {e}")


def show_leaderboard_stats(user, competition, db):
    """Show additional statistics for the leaderboard"""
    try:
        st.subheader("📊 Statistikk")
        
        # Get all entries for this competition
        leaderboard = db.get_leaderboard_for_competition(competition['id'])
        
        if not leaderboard:
            return
        
        # Calculate stats
        total_participants = len(leaderboard)
        total_points = sum(entry['total_points'] for entry in leaderboard)
        avg_points = total_points / total_participants if total_participants > 0 else 0
        
        # Find top performer
        top_performer = leaderboard[0] if leaderboard else None
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**🏆 Konkurransestatistikk:**")
            st.write(f"• **Totalt deltakere:** {total_participants}")
            st.write(f"• **Totale poeng:** {total_points}")
            st.write(f"• **Gjennomsnitt:** {avg_points:.1f} poeng")
            
            if top_performer:
                st.write(f"• **Topp ytelse:** {top_performer['total_points']} poeng ({top_performer['full_name']})")
        
        with col2:
            # Show activity breakdown if user has entries
            user_entries = db.get_user_entries_for_competition(user['id'], competition['id'])
            
            if user_entries:
                st.markdown("**🏃 Dine aktiviteter:**")
                for entry in user_entries:
                    activity = entry.get('activities', {})
                    activity_name = activity.get('name', 'Ukjent')
                    activity_unit = activity.get('unit', '')
                    
                    st.write(f"• **{activity_name}:** {entry['value']} {activity_unit} ({entry['points']} poeng)")
            else:
                st.info("Du har ikke registrert aktiviteter denne måneden")
        
        # Show progress chart if there are multiple months
        st.markdown("---")
        show_progress_chart(user, db)
        
    except Exception as e:
        st.error(f"Feil ved visning av statistikk: {e}")


def show_progress_chart(user, db):
    """Show user's progress over time"""
    try:
        st.subheader("📈 Din utvikling over tid")
        
        # Get user's competition history
        competitions = db.get_competitions_for_company(user['company_id'], limit=6)
        
        if len(competitions) < 2:
            st.info("Trenger minst 2 måneder med data for å vise utvikling")
            return
        
        # Collect user's points for each month
        months = []
        points = []
        
        for comp in reversed(competitions):  # Oldest first
            comp_date = datetime.strptime(comp['year_month'], '%Y-%m-%d').date()
            month_name = comp_date.strftime("%b %Y")
            
            user_entries = db.get_user_entries_for_competition(user['id'], comp['id'])
            total_points = sum(entry['points'] for entry in user_entries)
            
            months.append(month_name)
            points.append(total_points)
        
        # Create simple text-based chart
        if months and points:
            max_points = max(points) if points else 1
            
            st.markdown("**Poengutvikling:**")
            for i, (month, point) in enumerate(zip(months, points)):
                # Simple bar representation
                bar_length = int((point / max_points) * 20) if max_points > 0 else 0
                bar = "█" * bar_length + "░" * (20 - bar_length)
                
                # Mark current month
                marker = "👈" if i == len(months) - 1 else ""
                st.write(f"`{month:8}` {bar} {point:3d} poeng {marker}")
        
        # Show trend
        if len(points) >= 2:
            if points[-1] > points[-2]:
                st.success("📈 Du er på vei oppover! Fortsett sånn!")
            elif points[-1] < points[-2]:
                st.warning("📉 Litt nedgang fra forrige måned. Du klarer å komme tilbake!")
            else:
                st.info("➡️ Samme nivå som forrige måned. Kanskje tid for å pushe litt ekstra?")
        
    except Exception as e:
        st.error(f"Feil ved visning av utviklingsgraf: {e}")
