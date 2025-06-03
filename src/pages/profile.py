"""
Profile page for Konkurranseapp
User profile information and settings
"""

import streamlit as st
import sys
import os

# Add src to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.database_helpers import get_db_helper


def show_profile_page(user):
    """Profile page"""
    st.title("👤 Min profil")
    
    # User information section
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📋 Brukerinformasjon")
        
        st.write(f"**Navn:** {user['full_name']}")
        st.write(f"**E-post:** {user['email']}")
        st.write(f"**Rolle:** {'👑 Administrator' if user['is_admin'] else '👤 Vanlig bruker'}")
        st.write(f"**Bruker-ID:** `{user['id']}`")
    
    with col2:
        # Profile avatar/status
        st.markdown("### 🎯 Status")
        if user['is_admin']:
            st.success("👑 Administrator")
            st.caption("Du kan administrere bedriften")
        else:
            st.info("👤 Bruker")
            st.caption("Du kan registrere aktiviteter")
    
    st.markdown("---")
    
    # Company information
    show_company_info(user)
    
    st.markdown("---")
    
    # Activity statistics
    show_activity_statistics(user)
    
    st.markdown("---")
    
    # Account settings
    show_account_settings(user)


def show_company_info(user):
    """Show company information"""
    st.subheader("🏢 Bedriftsinformasjon")
    
    try:
        db = get_db_helper()
        company = db.get_company_by_id(user['company_id'])
        
        if company:
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Bedriftsnavn:** {company['name']}")
                st.write(f"**Bedriftskode:** `{company['company_code']}`")
                st.write(f"**Registrert:** {company['created_at'][:10]}")
            
            with col2:
                # Show company stats
                users = db.get_users_by_company(user['company_id'])
                admin_count = sum(1 for u in users if u['is_admin'])
                
                st.metric("👥 Antall ansatte", len(users))
                st.metric("👑 Administratorer", admin_count)
            
            if user['is_admin']:
                st.info("💡 **Tip:** Del bedriftskoden med nye ansatte så de kan registrere seg")
                
        else:
            st.error("Kunne ikke hente bedriftsinformasjon")
            
    except Exception as e:
        st.error(f"Feil ved henting av bedriftsinformasjon: {e}")


def show_activity_statistics(user):
    """Show user's activity statistics"""
    st.subheader("📊 Dine aktivitetsstatistikker")
    
    try:
        db = get_db_helper()
        
        # Get all competitions for user's company
        competitions = db.get_competitions_for_company(user['company_id'], limit=12)
        
        if not competitions:
            st.info("Ingen konkurranser funnet ennå")
            return
        
        # Calculate overall stats
        total_points = 0
        total_activities = 0
        months_active = 0
        best_month_points = 0
        best_month_name = ""
        
        activity_breakdown = {}
        
        for comp in competitions:
            entries = db.get_user_entries_for_competition(user['id'], comp['id'])
            
            if entries:
                months_active += 1
                month_points = sum(entry['points'] for entry in entries)
                total_points += month_points
                total_activities += len(entries)
                
                if month_points > best_month_points:
                    best_month_points = month_points
                    comp_date = comp['year_month']
                    best_month_name = comp_date[:7]  # YYYY-MM
                
                # Track activity types
                for entry in entries:
                    activity = entry.get('activities', {})
                    activity_name = activity.get('name', 'Ukjent')
                    
                    if activity_name not in activity_breakdown:
                        activity_breakdown[activity_name] = {
                            'count': 0,
                            'total_value': 0,
                            'total_points': 0,
                            'unit': activity.get('unit', '')
                        }
                    
                    activity_breakdown[activity_name]['count'] += 1
                    activity_breakdown[activity_name]['total_value'] += entry['value']
                    activity_breakdown[activity_name]['total_points'] += entry['points']
        
        # Display overall stats
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("🎯 Totale poeng", total_points)
        
        with col2:
            st.metric("📅 Aktive måneder", months_active)
        
        with col3:
            st.metric("🏃 Aktivitetsregistreringer", total_activities)
        
        with col4:
            if best_month_name:
                st.metric("🏆 Beste måned", f"{best_month_points}p", delta=best_month_name)
            else:
                st.metric("🏆 Beste måned", "Ingen data")
        
        # Show activity breakdown
        if activity_breakdown:
            st.markdown("**📈 Aktivitetsfordeling:**")
            
            for activity_name, stats in activity_breakdown.items():
                with st.expander(f"{activity_name} - {stats['total_points']} poeng totalt"):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Måneder registrert", stats['count'])
                    with col2:
                        st.metric(f"Total {stats['unit']}", f"{stats['total_value']:.1f}")
                    with col3:
                        avg_points = stats['total_points'] / stats['count'] if stats['count'] > 0 else 0
                        st.metric("Snitt poeng/mnd", f"{avg_points:.1f}")
        
    except Exception as e:
        st.error(f"Kunne ikke laste aktivitetsstatistikk: {e}")


def show_account_settings(user):
    """Show account settings and options"""
    st.subheader("⚙️ Kontoinnstillinger")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**🔐 Sikkerhet:**")
        if st.button("🔄 Bytt passord", help="Funksjonen kommer snart"):
            st.info("Passord-endring kommer i en fremtidig versjon")
        
        if st.button("📧 Endre e-post", help="Funksjonen kommer snart"):
            st.info("E-post-endring kommer i en fremtidig versjon")
    
    with col2:
        st.markdown("**📱 Preferanser:**")
        
        # Theme preference (placeholder)
        theme_option = st.selectbox(
            "🎨 Tema",
            ["Auto", "Lys", "Mørk"],
            disabled=True,
            help="Tema-valg kommer snart"
        )
        
        # Notification preferences (placeholder)
        notifications = st.checkbox(
            "🔔 E-post varsler",
            disabled=True,
            help="Varslings-innstillinger kommer snart"
        )
    
    st.markdown("---")
    
    # Data export
    st.markdown("**📄 Data og eksport:**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📊 Last ned mine data", help="Eksporter dine aktivitetsdata"):
            export_user_data(user)
    
    with col2:
        if st.button("🗑️ Slett konto", help="Permanent sletting av konto", type="secondary"):
            show_delete_account_warning()


def export_user_data(user):
    """Export user's activity data"""
    try:
        db = get_db_helper()
        competitions = db.get_competitions_for_company(user['company_id'], limit=24)
        
        export_data = []
        
        for comp in competitions:
            entries = db.get_user_entries_for_competition(user['id'], comp['id'])
            
            for entry in entries:
                activity = entry.get('activities', {})
                export_data.append({
                    'Måned': comp['year_month'],
                    'Aktivitet': activity.get('name', 'Ukjent'),
                    'Verdi': entry['value'],
                    'Enhet': activity.get('unit', ''),
                    'Poeng': entry['points'],
                    'Registrert': entry['created_at'][:10]
                })
        
        if export_data:
            st.success(f"✅ Fant {len(export_data)} aktivitetsregistreringer")
            st.info("💡 Data-eksport funksjonalitet kommer snart")
            
            # Preview data
            st.markdown("**Forhåndsvisning:**")
            for item in export_data[:5]:  # Show first 5
                st.write(f"• {item['Måned']}: {item['Aktivitet']} - {item['Verdi']} {item['Enhet']} ({item['Poeng']}p)")
            
            if len(export_data) > 5:
                st.caption(f"... og {len(export_data) - 5} til")
        else:
            st.info("Ingen aktivitetsdata å eksportere")
            
    except Exception as e:
        st.error(f"Kunne ikke eksportere data: {e}")


def show_delete_account_warning():
    """Show account deletion warning"""
    st.warning("⚠️ **Advarsel:** Sletting av konto er permanent og kan ikke angres!")
    st.error("🚫 Konto-sletting er ikke implementert ennå. Kontakt en administrator hvis du virkelig ønsker å slette kontoen din.")
