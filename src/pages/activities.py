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
    
    # Only show current month for now
    show_current_month_activities(user)


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
        
        # Get available activities - Pass company_id for å få bedriftsspesifikke aktiviteter
        activities = db.get_active_activities(company_id=user['company_id'])
        
        if not activities:
            st.error("Ingen aktiviteter tilgjengelig")
            if user.get('is_admin'):
                st.info("💡 Gå til 'Aktivitetsstyring' for å legge til aktiviteter for bedriften")
            else:
                st.info("💡 Be administrator om å legge til aktiviteter for bedriften")
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
        
        # Build simple dropdown options - one option per activity
        activity_options = []
        activities_dict = {}
        
        for activity in activities:
            # Create display name
            display_name = f"{activity['name']} ({activity['unit']})"
            if activity.get('company_id') == user['company_id']:
                display_name += " 🏢"
            
            activity_options.append(display_name)
            activities_dict[display_name] = activity
        
        # Show activity selector dropdown
        if len(activity_options) > 1:
            selected_activity_display = st.selectbox(
                "🏃 Velg aktivitet å registrere:",
                activity_options,
                index=0,
                help="Velg hvilken aktivitet du vil legge til data for"
            )
        else:
            # Only one activity - just show it
            selected_activity_display = activity_options[0]
            st.write(f"**🏃 Aktivitet:** {selected_activity_display}")
        
        # Get selected activity
        selected_activity = activities_dict[selected_activity_display]
        
        if selected_activity:
            activity_id = selected_activity['id']
            activity_name = selected_activity['name']
            activity_unit = selected_activity['unit']
            activity_description = selected_activity['description']
            is_company_specific = selected_activity.get('company_id') == user['company_id']
            
            # Show selected activity details
            with st.container():
                header = f"### {activity_name}"
                if is_company_specific:
                    header += " 🏢"
                st.markdown(header)
                
                if is_company_specific:
                    st.caption("🏢 Bedriftsspesifikk aktivitet")
                else:
                    st.caption("🌐 Standard aktivitet")
                
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
        
        # Only admin can edit existing values - removed from user interface
        
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
            is_company_specific = activity.get('company_id') == user['company_id']
            
            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
            
            with col1:
                display_name = f"🏃 {activity_name}"
                if is_company_specific:
                    display_name += " 🏢"
                st.write(display_name)
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


# Import functions that are used from database_helpers
from utils.database_helpers import get_activity_name, get_activity_unit
