"""
Activities page for Konkurranseapp
Handles activity registration and history
"""

import streamlit as st
from datetime import datetime, date
import sys
import os

# Add src to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.database_helpers import get_db_helper
from utils.supabase_client import get_supabase


def show_activities_page(user):
    """Activities page - register and manage activities"""
    st.title("🏃 Aktivitetsregistrering")
    
    # Tabs for current month vs history
    tab1, tab2 = st.tabs(["📝 Denne måneden", "📈 Historikk"])
    
    with tab1:
        show_current_month_activities(user)
    
    with tab2:
        show_activity_history(user)


def show_current_month_activities(user):
    """Show current month activity registration"""
    try:
        db = get_db_helper()
        
        # Get current month competition
        current_month = date.today().replace(day=1)
        competition = db.get_or_create_monthly_competition(user['company_id'], current_month)
        
        # Show current month info
        month_name = current_month.strftime("%B %Y")
        st.info(f"📅 **Registrerer for:** {month_name}")
        
        # Get available activities
        activities = db.get_active_activities()
        
        if not activities:
            st.error("Ingen aktiviteter tilgjengelig")
            return
        
        # Get user's existing entries for this month
        user_entries = db.get_user_entries_for_competition(user['id'], competition['id'])
        user_entries_dict = {entry['activity_id']: entry for entry in user_entries}
        
        # Show current totals first
        if user_entries:
            st.subheader("📊 Dine totaler denne måneden")
            show_current_registrations(user, competition, user_entries, db)
            st.markdown("---")
        
        # Show activity registration forms
        st.subheader("➕ Legg til ny aktivitet")
        st.info("💡 **Tips:** Verdiene du legger inn blir **lagt til** dine eksisterende totaler for måneden")
        
        # Activity selector dropdown
        activities_dict = {activity['id']: activity for activity in activities}
        activity_options = [f"{activity['name']} ({activity['unit']})" for activity in activities]
        
        selected_activity_display = st.selectbox(
            "🏃 Velg aktivitet å registrere:",
            activity_options,
            help="Velg hvilken aktivitet du vil legge til data for"
        )
        
        # Find selected activity
        selected_activity = None
        for activity in activities:
            if f"{activity['name']} ({activity['unit']})" == selected_activity_display:
                selected_activity = activity
                break
        
        if selected_activity:
            activity_id = selected_activity['id']
            activity_name = selected_activity['name']
            activity_unit = selected_activity['unit']
            activity_description = selected_activity['description']
            
            # Show selected activity details
            with st.container():
                st.markdown(f"### {activity_name}")
                st.caption(activity_description)
                
                # Show scoring tiers
                scoring_tiers = selected_activity['scoring_tiers']['tiers']
                tier_text = " | ".join([
                    f"{tier['min']}-{tier.get('max', '∞')} {activity_unit} = {tier['points']}p"
                    for tier in scoring_tiers
                ])
                st.caption(f"🎯 **Poengskala:** {tier_text}")
                
                # Get current total if exists
                current_total = 0.0
                if activity_id in user_entries_dict:
                    current_total = float(user_entries_dict[activity_id]['value'])
                    current_points = db.calculate_points_for_activity(activity_id, current_total)
                    st.info(f"📈 **Nåværende total:** {current_total} {activity_unit} ({current_points} poeng)")
                
                # Registration form for selected activity
                with st.form("single_activity_form", clear_on_submit=True):
                    st.markdown(f"**Legg til {activity_name}:**")
                    
                    new_value = st.number_input(
                        f"Antall {activity_unit} å legge til",
                        min_value=0.0,
                        value=0.0,
                        step=1.0 if activity_unit == 'k steps' else 0.1,
                        key="single_activity_input",
                        help=f"Hvor mye {activity_name.lower()} vil du legge til?"
                    )
                    
                    # Submit button
                    submitted = st.form_submit_button(
                        f"➕ Legg til {activity_name}", 
                        type="primary", 
                        use_container_width=True
                    )
                
                if submitted and new_value > 0:
                    add_single_activity(user, competition, activity_id, new_value, current_total, db)
                elif submitted and new_value == 0:
                    st.warning("Skriv inn en verdi større enn 0")
        
        # Show alternative: Reset/Edit existing
        if user_entries:
            st.markdown("---")
            st.subheader("✏️ Rediger eksisterende verdier")
            
            with st.expander("🔧 Endre totaler direkte"):
                st.warning("⚠️ Dette vil **overskrive** dine eksisterende totaler")
                
                with st.form("edit_totals_form"):
                    edit_values = {}
                    
                    for activity in activities:
                        activity_id = activity['id']
                        if activity_id in user_entries_dict:
                            activity_name = activity['name']
                            activity_unit = activity['unit']
                            current_total = float(user_entries_dict[activity_id]['value'])
                            
                            edit_values[activity_id] = st.number_input(
                                f"Total {activity_name} ({activity_unit})",
                                min_value=0.0,
                                value=current_total,
                                step=1.0 if activity_unit == 'k steps' else 0.1,
                                key=f"edit_activity_{activity_id}"
                            )
                    
                    edit_submitted = st.form_submit_button("💾 Oppdater totaler", type="secondary")
                
                if edit_submitted:
                    update_activities(user, competition, edit_values, db)
        
    except Exception as e:
        st.error(f"Feil ved lasting av aktiviteter: {e}")


def add_single_activity(user, competition, activity_id, new_value, current_total, db):
    """Add single activity value and refresh page"""
    try:
        # Calculate new total
        new_total = current_total + new_value
        
        # Use our fixed upsert function
        entry = upsert_user_entry(
            user_id=user['id'],
            activity_id=activity_id,
            competition_id=competition['id'],
            value=new_total,
            db=db
        )
        
        activity_name = get_activity_name(activity_id, db)
        activity_unit = get_activity_unit(activity_id, db)
        
        st.success(f"✅ Lagt til {new_value} {activity_unit} til {activity_name}")
        st.success(f"🎯 Ny total: {new_total} {activity_unit} ({entry['points']} poeng)")
        st.balloons()
        
        # Auto refresh page to clear form and show updated data
        st.rerun()
        
    except Exception as e:
        st.error(f"Feil ved lagring: {e}")


def update_activities(user, competition, activity_values, db):
    """Update existing activity totals directly"""
    try:
        updated_count = 0
        
        for activity_id, new_total in activity_values.items():
            entry = upsert_user_entry(
                user_id=user['id'],
                activity_id=activity_id,
                competition_id=competition['id'],
                value=new_total,
                db=db
            )
            updated_count += 1
        
        if updated_count > 0:
            st.success(f"✅ Oppdatert {updated_count} aktiviteter!")
            st.rerun()
            
    except Exception as e:
        st.error(f"Feil ved oppdatering: {e}")


def upsert_user_entry(user_id: str, activity_id: str, competition_id: str, value: float, db):
    """Safely insert or update user entry to avoid duplicate key constraint"""
    try:
        # Calculate points
        points = db.calculate_points_for_activity(activity_id, value)
        
        # Try to update first
        supabase = get_supabase()
        
        # Check if entry exists
        existing = supabase.table('user_entries').select('id').eq('user_id', user_id).eq('activity_id', activity_id).eq('competition_id', competition_id).execute()
        
        if existing.data:
            # Update existing entry
            response = supabase.table('user_entries').update({
                'value': value,
                'points': points,
                'updated_at': datetime.now().isoformat()
            }).eq('user_id', user_id).eq('activity_id', activity_id).eq('competition_id', competition_id).execute()
        else:
            # Insert new entry
            response = supabase.table('user_entries').insert({
                'user_id': user_id,
                'activity_id': activity_id,
                'competition_id': competition_id,
                'value': value,
                'points': points
            }).execute()
        
        if response.data:
            return response.data[0]
        else:
            raise Exception("No data returned from upsert")
            
    except Exception as e:
        raise Exception(f"Feil ved lagring av registrering: {e}")


def show_current_registrations(user, competition, user_entries, db):
    """Show user's current activity registrations"""
    if user_entries:
        total_points = 0
        
        # Create a nice table view
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        
        with col1:
            st.write("**Aktivitet**")
        with col2:
            st.write("**Verdi**")
        with col3:
            st.write("**Poeng**")
        with col4:
            st.write("**Sist oppdatert**")
        
        st.markdown("---")
        
        for entry in user_entries:
            activity = entry.get('activities', {})
            activity_name = activity.get('name', 'Ukjent')
            activity_unit = activity.get('unit', '')
            
            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
            
            with col1:
                st.write(f"🏃 {activity_name}")
            with col2:
                st.write(f"{entry['value']} {activity_unit}")
            with col3:
                st.write(f"**{entry['points']}** poeng")
            with col4:
                updated_date = entry['updated_at'][:10] if entry.get('updated_at') else entry['created_at'][:10]
                st.write(updated_date)
            
            total_points += entry['points']
        
        st.markdown("---")
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        with col1:
            st.write("**🎯 TOTALT**")
        with col2:
            st.write("")
        with col3:
            st.write(f"**{total_points} poeng**")
        with col4:
            st.write("")
        
        # Show ranking hint
        try:
            leaderboard = db.get_leaderboard_for_competition(competition['id'])
            user_rank = None
            for i, entry in enumerate(leaderboard, 1):
                if entry['user_id'] == user['id']:
                    user_rank = i
                    break
            
            if user_rank:
                st.info(f"🏆 Du er på **plass {user_rank}** av {len(leaderboard)} deltakere")
            
        except Exception as e:
            st.warning("Kunne ikke hente ranking-info")
        
    else:
        st.info("Du har ikke registrert noen aktiviteter ennå denne måneden")
        st.markdown("👆 Bruk skjemaet over for å registrere dine aktiviteter!")


def show_activity_history(user):
    """Show activity history for previous months"""
    st.subheader("📈 Aktivitetshistorikk")
    
    try:
        db = get_db_helper()
        competitions = db.get_competitions_for_company(user['company_id'], limit=6)
        
        if len(competitions) <= 1:
            st.info("Ingen historiske data ennå")
            return
        
        # Skip current month (first in list)
        historical_competitions = competitions[1:]
        
        for competition in historical_competitions:
            month_date = datetime.strptime(competition['year_month'], '%Y-%m-%d').date()
            month_name = month_date.strftime("%B %Y")
            
            with st.expander(f"📅 {month_name}"):
                entries = db.get_user_entries_for_competition(user['id'], competition['id'])
                
                if entries:
                    total_points = sum(entry['points'] for entry in entries)
                    st.metric("Totale poeng", total_points)
                    
                    for entry in entries:
                        activity = entry.get('activities', {})
                        activity_name = activity.get('name', 'Ukjent')
                        activity_unit = activity.get('unit', '')
                        
                        st.write(f"• **{activity_name}:** {entry['value']} {activity_unit} ({entry['points']} poeng)")
                else:
                    st.write("Ingen aktiviteter registrert denne måneden")
                    
    except Exception as e:
        st.error(f"Kunne ikke laste historikk: {e}")


def get_activity_name(activity_id: str, db) -> str:
    """Get activity name by ID"""
    try:
        activity = db.get_activity_by_id(activity_id)
        return activity['name'] if activity else 'Ukjent aktivitet'
    except:
        return 'Ukjent aktivitet'


def get_activity_unit(activity_id: str, db) -> str:
    """Get activity unit by ID"""
    try:
        activity = db.get_activity_by_id(activity_id)
        return activity['unit'] if activity else ''
    except:
        return ''
