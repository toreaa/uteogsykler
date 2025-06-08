"""
Database helper functions for CRUD operations
"""

import json
import uuid
from datetime import datetime, date
from typing import Dict, List, Optional, Any, Union
from dateutil.relativedelta import relativedelta

from .supabase_client import get_supabase


class DatabaseError(Exception):
    """Custom exception for database operations"""
    pass


class DatabaseHelper:
    """Helper class for database operations"""
    
    def __init__(self):
        self.supabase = get_supabase()
    
    # ============= COMPANY OPERATIONS =============
    
    def create_company(self, name: str) -> Dict[str, Any]:
        """
        Opprett ny bedrift med auto-generert bedriftskode og standard aktiviteter
        
        Args:
            name: Bedriftsnavn
            
        Returns:
            Dict med bedriftsinformasjon
            
        Raises:
            DatabaseError: Hvis opprettelse feiler
        """
        try:
            # Generer bedriftskode
            response = self.supabase.rpc('generate_company_code').execute()
            
            if not response.data:
                raise DatabaseError("Kunne ikke generere bedriftskode")
            
            company_code = response.data
            
            # Opprett bedrift
            company_data = {
                'name': name,
                'company_code': company_code
            }
            
            response = self.supabase.table('companies').insert(company_data).execute()
            
            if not response.data:
                raise DatabaseError("Kunne ikke opprette bedrift")
            
            company = response.data[0]
            
            # Kopier standard aktiviteter til den nye bedriften
            self._copy_global_activities_to_company(company['id'])
            
            return company
            
        except Exception as e:
            raise DatabaseError(f"Feil ved opprettelse av bedrift: {e}")
    
    def _copy_global_activities_to_company(self, company_id: str) -> None:
        """
        Privat metode: Kopier globale standard aktiviteter til ny bedrift
        
        Args:
            company_id: ID for bedriften som skal få aktivitetene
        """
        try:
            # Hent globale aktiviteter (company_id = NULL)
            response = self.supabase.table('activities').select('*').is_('company_id', 'null').eq('is_active', True).execute()
            
            global_activities = response.data or []
            
            # Kopier hver aktivitet til bedriften
            for activity in global_activities:
                company_activity_data = {
                    'name': activity['name'],
                    'description': activity['description'],
                    'unit': activity['unit'],
                    'scoring_tiers': activity['scoring_tiers'],
                    'company_id': company_id,
                    'is_active': True
                }
                
                self.supabase.table('activities').insert(company_activity_data).execute()
                
        except Exception as e:
            raise DatabaseError(f"Feil ved kopiering av standard aktiviteter: {e}")
    
    def get_company_by_code(self, company_code: str) -> Optional[Dict[str, Any]]:
        """
        Hent bedrift basert på bedriftskode
        
        Args:
            company_code: Bedriftskode
            
        Returns:
            Bedriftsinformasjon eller None hvis ikke funnet
        """
        try:
            response = self.supabase.table('companies').select('*').eq('company_code', company_code.upper()).execute()
            
            if response.data:
                return response.data[0]
            return None
            
        except Exception as e:
            raise DatabaseError(f"Feil ved henting av bedrift: {e}")
    
    def get_company_by_id(self, company_id: str) -> Optional[Dict[str, Any]]:
        """Hent bedrift basert på ID"""
        try:
            response = self.supabase.table('companies').select('*').eq('id', company_id).execute()
            
            if response.data:
                return response.data[0]
            return None
            
        except Exception as e:
            raise DatabaseError(f"Feil ved henting av bedrift: {e}")
    
    def get_all_companies(self) -> List[Dict[str, Any]]:
        """Hent alle bedrifter (for system admin)"""
        try:
            response = self.supabase.table('companies').select('*').order('created_at', desc=True).execute()
            
            return response.data or []
            
        except Exception as e:
            raise DatabaseError(f"Feil ved henting av alle bedrifter: {e}")
    
    def update_company(self, company_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Oppdater bedrift (for system admin)"""
        try:
            response = self.supabase.table('companies').update(updates).eq('id', company_id).execute()
            
            if not response.data:
                raise DatabaseError("Kunne ikke oppdatere bedrift")
            
            return response.data[0]
            
        except Exception as e:
            raise DatabaseError(f"Feil ved oppdatering av bedrift: {e}")
    
    # ============= USER OPERATIONS =============
    
    def create_user(self, user_id: str, email: str, full_name: str, 
                   company_id: str, is_admin: bool = False) -> Dict[str, Any]:
        """
        Opprett ny bruker (koblet til Supabase Auth)
        
        Args:
            user_id: UUID fra Supabase Auth
            email: Brukerens e-post
            full_name: Fullt navn
            company_id: Bedrift-ID
            is_admin: Om brukeren skal være admin
            
        Returns:
            Brukerinformasjon
        """
        try:
            user_data = {
                'id': user_id,
                'email': email,
                'full_name': full_name,
                'company_id': company_id,
                'is_admin': is_admin,
                'user_role': 'company_admin' if is_admin else 'user'
            }
            
            response = self.supabase.table('users').insert(user_data).execute()
            
            if not response.data:
                raise DatabaseError("Kunne ikke opprette bruker")
            
            return response.data[0]
            
        except Exception as e:
            raise DatabaseError(f"Feil ved opprettelse av bruker: {e}")
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Hent bruker basert på ID"""
        try:
            response = self.supabase.table('users').select('*, companies(*)').eq('id', user_id).execute()
            
            if response.data:
                return response.data[0]
            return None
            
        except Exception as e:
            raise DatabaseError(f"Feil ved henting av bruker: {e}")
    
    def get_users_by_company(self, company_id: str) -> List[Dict[str, Any]]:
        """Hent alle brukere for en bedrift"""
        try:
            response = self.supabase.table('users').select('*').eq('company_id', company_id).execute()
            
            return response.data or []
            
        except Exception as e:
            raise DatabaseError(f"Feil ved henting av brukere: {e}")
    
    def update_user_admin_status(self, user_id: str, is_admin: bool) -> bool:
        """Oppdater admin-status for bruker"""
        try:
            user_role = 'company_admin' if is_admin else 'user'
            response = self.supabase.table('users').update({
                'is_admin': is_admin,
                'user_role': user_role
            }).eq('id', user_id).execute()
            
            return len(response.data) > 0
            
        except Exception as e:
            raise DatabaseError(f"Feil ved oppdatering av admin-status: {e}")
    
    # ============= ACTIVITY OPERATIONS (FIKSET) =============
    
    def get_active_activities(self, company_id: str = None) -> List[Dict[str, Any]]:
        """
        FIKSET: Hent alle aktive aktiviteter for en bedrift
        
        Args:
            company_id: Bedrift-ID - hvis oppgitt, hent kun aktiviteter for den bedriften
            
        Returns:
            Liste med aktiviteter
        """
        try:
            if company_id:
                # FIKSET: Hent kun bedriftsspesifikke aktiviteter (ikke globale + bedriftsspesifikke)
                response = self.supabase.table('activities').select('*').eq('company_id', company_id).eq('is_active', True).order('name').execute()
            else:
                # Hent globale aktiviteter (for kopiering til nye bedrifter)
                response = self.supabase.table('activities').select('*').is_('company_id', 'null').eq('is_active', True).order('name').execute()
            
            return response.data or []
            
        except Exception as e:
            raise DatabaseError(f"Feil ved henting av aktiviteter: {e}")
    
    def get_activity_by_id(self, activity_id: str) -> Optional[Dict[str, Any]]:
        """Hent aktivitet basert på ID"""
        try:
            response = self.supabase.table('activities').select('*').eq('id', activity_id).execute()
            
            if response.data:
                return response.data[0]
            return None
            
        except Exception as e:
            raise DatabaseError(f"Feil ved henting av aktivitet: {e}")
    
    def create_activity(self, name: str, description: str, unit: str, 
                       scoring_tiers: Dict[str, Any], company_id: str = None) -> Dict[str, Any]:
        """
        Opprett ny aktivitet
        
        Args:
            name: Aktivitetsnavn
            description: Beskrivelse
            unit: Måleenhet (km, k steps, etc.)
            scoring_tiers: Poengskala som JSON
            company_id: Bedrift-ID (None for globale aktiviteter)
            
        Returns:
            Opprettet aktivitet
        """
        try:
            activity_data = {
                'name': name,
                'description': description,
                'unit': unit,
                'scoring_tiers': scoring_tiers,
                'company_id': company_id,
                'is_active': True
            }
            
            response = self.supabase.table('activities').insert(activity_data).execute()
            
            if not response.data:
                raise DatabaseError("Kunne ikke opprette aktivitet")
            
            return response.data[0]
            
        except Exception as e:
            raise DatabaseError(f"Feil ved opprettelse av aktivitet: {e}")
    
    def update_activity(self, activity_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Oppdater aktivitet
        
        Args:
            activity_id: Aktivitet-ID
            updates: Felt som skal oppdateres
            
        Returns:
            Oppdatert aktivitet
        """
        try:
            response = self.supabase.table('activities').update(updates).eq('id', activity_id).execute()
            
            if not response.data:
                raise DatabaseError("Kunne ikke oppdatere aktivitet")
            
            return response.data[0]
            
        except Exception as e:
            raise DatabaseError(f"Feil ved oppdatering av aktivitet: {e}")
    
    def delete_activity(self, activity_id: str) -> bool:
        """
        Slett aktivitet (setter is_active = False)
        
        Args:
            activity_id: Aktivitet-ID
            
        Returns:
            True hvis vellykket
        """
        try:
            response = self.supabase.table('activities').update({'is_active': False}).eq('id', activity_id).execute()
            
            return len(response.data) > 0
            
        except Exception as e:
            raise DatabaseError(f"Feil ved sletting av aktivitet: {e}")
    
    def can_user_modify_activity(self, user_company_id: str, activity_id: str) -> bool:
        """
        Sjekk om bruker kan modifisere en aktivitet
        
        Args:
            user_company_id: Brukerens bedrift-ID
            activity_id: Aktivitet-ID
            
        Returns:
            True hvis brukeren kan modifisere aktiviteten
        """
        try:
            activity = self.get_activity_by_id(activity_id)
            
            if not activity:
                return False
            
            # Kan kun modifisere aktiviteter som tilhører egen bedrift
            return activity.get('company_id') == user_company_id
            
        except Exception as e:
            return False
    
    def calculate_points_for_activity(self, activity_id: str, value: float) -> int:
        """
        Beregn poeng basert på aktivitet og verdi
        
        Args:
            activity_id: Aktivitet-ID
            value: Verdi (km, steps, etc.)
            
        Returns:
            Beregnede poeng
        """
        try:
            activity = self.get_activity_by_id(activity_id)
            if not activity:
                raise DatabaseError("Aktivitet ikke funnet")
            
            scoring_tiers = activity['scoring_tiers']['tiers']
            
            # Finn riktig tier
            for tier in scoring_tiers:
                min_val = tier['min']
                max_val = tier.get('max')
                
                if max_val is None:  # Øverste tier (ingen max)
                    if value >= min_val:
                        return tier['points']
                else:
                    if min_val <= value < max_val:
                        return tier['points']
            
            # Hvis ingen tier passer, returner 0 poeng
            return 0
            
        except Exception as e:
            raise DatabaseError(f"Feil ved poengberegning: {e}")
    
    # ============= COMPETITION OPERATIONS =============
    
    def get_or_create_monthly_competition(self, company_id: str, year_month: date = None) -> Dict[str, Any]:
        """
        Hent eller opprett månedlig konkurranse
        
        Args:
            company_id: Bedrift-ID
            year_month: Måned (default: inneværende måned)
            
        Returns:
            Konkurranseinformasjon
        """
        try:
            if year_month is None:
                year_month = date.today().replace(day=1)
            
            # Prøv å hente eksisterende konkurranse
            response = self.supabase.table('monthly_competitions').select('*').eq('company_id', company_id).eq('year_month', year_month.isoformat()).execute()
            
            if response.data:
                return response.data[0]
            
            # Opprett ny konkurranse
            competition_data = {
                'company_id': company_id,
                'year_month': year_month.isoformat(),
                'is_active': True
            }
            
            response = self.supabase.table('monthly_competitions').insert(competition_data).execute()
            
            if not response.data:
                raise DatabaseError("Kunne ikke opprette konkurranse")
            
            return response.data[0]
            
        except Exception as e:
            raise DatabaseError(f"Feil ved håndtering av konkurranse: {e}")
    
    def get_competitions_for_company(self, company_id: str, limit: int = 12) -> List[Dict[str, Any]]:
        """Hent konkurranser for bedrift (nyeste først)"""
        try:
            response = self.supabase.table('monthly_competitions').select('*').eq('company_id', company_id).order('year_month', desc=True).limit(limit).execute()
            
            return response.data or []
            
        except Exception as e:
            raise DatabaseError(f"Feil ved henting av konkurranser: {e}")
    
    # ============= USER ENTRY OPERATIONS =============
    
    def create_or_update_user_entry(self, user_id: str, activity_id: str, 
                                  competition_id: str, value: float) -> Dict[str, Any]:
        """
        Opprett eller oppdater brukerregistrering
        
        Args:
            user_id: Bruker-ID
            activity_id: Aktivitet-ID
            competition_id: Konkurranse-ID
            value: Verdi
            
        Returns:
            Entry-informasjon
        """
        try:
            # Beregn poeng
            points = self.calculate_points_for_activity(activity_id, value)
            
            entry_data = {
                'user_id': user_id,
                'activity_id': activity_id,
                'competition_id': competition_id,
                'value': value,
                'points': points
            }
            
            # Prøv å oppdatere eksisterende entry
            response = self.supabase.table('user_entries').upsert(entry_data).execute()
            
            if not response.data:
                raise DatabaseError("Kunne ikke lagre registrering")
            
            return response.data[0]
            
        except Exception as e:
            raise DatabaseError(f"Feil ved lagring av registrering: {e}")
    
    def get_user_entries_for_competition(self, user_id: str, competition_id: str) -> List[Dict[str, Any]]:
        """Hent alle entries for en bruker i en konkurranse"""
        try:
            response = self.supabase.table('user_entries').select('*, activities(*)').eq('user_id', user_id).eq('competition_id', competition_id).execute()
            
            return response.data or []
            
        except Exception as e:
            raise DatabaseError(f"Feil ved henting av brukerregistreringer: {e}")
    
    def get_leaderboard_for_competition(self, competition_id: str) -> List[Dict[str, Any]]:
        """
        Hent leaderboard for en konkurranse
        
        Returns:
            Liste med brukere sortert etter total poeng (høyest først)
        """
        try:
            # SQL query for å beregne total poeng per bruker
            response = self.supabase.rpc('get_competition_leaderboard', {
                'competition_id_param': competition_id
            }).execute()
            
            # Fallback hvis RPC ikke fungerer - vi lager funksjon senere
            if not hasattr(response, 'data') or not response.data:
                # Manuell beregning
                entries_response = self.supabase.table('user_entries').select('*, users(full_name)').eq('competition_id', competition_id).execute()
                
                if not entries_response.data:
                    return []
                
                # Grupper etter bruker og summer poeng
                user_totals = {}
                for entry in entries_response.data:
                    user_id = entry['user_id']
                    if user_id not in user_totals:
                        user_totals[user_id] = {
                            'user_id': user_id,
                            'full_name': entry['users']['full_name'],
                            'total_points': 0,
                            'entries_count': 0
                        }
                    user_totals[user_id]['total_points'] += entry['points']
                    user_totals[user_id]['entries_count'] += 1
                
                # Sorter etter poeng
                leaderboard = sorted(user_totals.values(), key=lambda x: x['total_points'], reverse=True)
                
                # Legg til ranking
                for i, user in enumerate(leaderboard):
                    user['rank'] = i + 1
                
                return leaderboard
            
            return response.data or []
            
        except Exception as e:
            raise DatabaseError(f"Feil ved henting av leaderboard: {e}")
    
    # ============= SYSTEM ADMIN OPERATIONS =============
    
    def get_all_users(self) -> List[Dict[str, Any]]:
        """Hent alle brukere (for system admin)"""
        try:
            response = self.supabase.table('users').select('*, companies(name, company_code)').order('created_at', desc=True).execute()
            
            return response.data or []
            
        except Exception as e:
            raise DatabaseError(f"Feil ved henting av alle brukere: {e}")
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Hent systemstatistikk (for system admin)"""
        try:
            # Hent antall bedrifter
            companies_response = self.supabase.table('companies').select('id').execute()
            total_companies = len(companies_response.data or [])
            
            # Hent antall brukere
            users_response = self.supabase.table('users').select('id').execute()
            total_users = len(users_response.data or [])
            
            # Hent antall aktive konkurranser denne måneden
            current_month = date.today().replace(day=1)
            competitions_response = self.supabase.table('monthly_competitions').select('id').eq('year_month', current_month.isoformat()).execute()
            active_competitions = len(competitions_response.data or [])
            
            return {
                'total_companies': total_companies,
                'total_users': total_users,
                'active_competitions': active_competitions,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            raise DatabaseError(f"Feil ved henting av systemstatistikk: {e}")


# Global helper instance
_db_helper = None

def get_db_helper() -> DatabaseHelper:
    """Get global database helper instance"""
    global _db_helper
    
    if _db_helper is None:
        _db_helper = DatabaseHelper()
    
    return _db_helper


# Convenience functions for getting activity names/units (used in activities.py)
def get_activity_name(activity_id: str, db: DatabaseHelper) -> str:
    """Hent aktivitetsnavn basert på ID"""
    activity = db.get_activity_by_id(activity_id)
    return activity['name'] if activity else 'Ukjent aktivitet'


def get_activity_unit(activity_id: str, db: DatabaseHelper) -> str:
    """Hent aktivitetsenhet basert på ID"""
    activity = db.get_activity_by_id(activity_id)
    return activity['unit'] if activity else ''
