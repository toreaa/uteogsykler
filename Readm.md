Plan:
# Konkurranseapp - Utviklingsplan

## Fase 1: Prosjektoppsett og Database Design

### Step 1.1: Prosjektstruktur og Repository
**Hvor:** GitHub
**Hva:**
- Opprett nytt GitHub repository
- Sett opp grunnleggende mappestruktur:
  - `/src` - hovedkode
  - `/docs` - dokumentasjon  
  - `/config` - konfigurasjonsfiler
  - `requirements.txt` - Python dependencies
  - `README.md` - prosjektbeskrivelse
- Opprett `.gitignore` for Python-prosjekter
- Sett opp GitHub branch protection for main

### Step 1.2: Supabase Database Oppsett
**Hvor:** Supabase Dashboard
**Hva:**
- Opprett nytt Supabase-prosjekt
- Design og implementer database-tabeller:
  - `companies` (id, name, company_code, created_at)
  - `users` (id, email, full_name, company_id, is_admin, created_at)
  - `activities` (id, name, description, scoring_tiers, is_active)
  - `monthly_competitions` (id, company_id, year_month, is_active, created_at)
  - `user_entries` (id, user_id, activity_id, competition_id, value, points, created_at)
- Sett opp Row Level Security (RLS) policies
- Opprett indexes for performance
- Dokumenter database-skjema i `/docs/database-schema.md`

### Step 1.3: Miljøvariabler og Secrets
**Hvor:** GitHub Secrets + Streamlit Cloud
**Hva:**
- Sett opp Supabase API-nøkler som miljøvariabler
- Konfigurer secrets for deployment
- Opprett `.env.example` fil som template
- Dokumenter miljøoppsett i `/docs/environment-setup.md`

## Fase 2: Grunnleggende Applikasjon

### Step 2.1: Supabase Connection og Utils
**Hvor:** `/src/utils/`
**Hva:**
- Implementer `supabase_client.py` for database-tilkobling
- Lag `database_helpers.py` med CRUD-operasjoner
- Implementer error handling og logging
- Test database-tilkobling og grunnleggende operasjoner

### Step 2.2: Autentisering og Brukerbehandling  
**Hvor:** `/src/auth/`
**Hva:**
- Implementer `auth.py` med Supabase Auth
- Lag pålogging/registrering flow
- Sett opp session management i Streamlit
- Implementer admin vs vanlig bruker rolle-sjekk
- Test autentisering end-to-end

### Step 2.3: Bedriftsregistrering
**Hvor:** `/src/pages/`
**Hva:**
- Lag `company_registration.py` 
- Implementer skjema for bedriftsopprettelse
- Generer unik bedriftskode automatisk
- Sett første bruker som admin automatisk
- Test bedriftsregistrering flow

## Fase 3: Kjernefeatures

### Step 3.1: Brukerregistrering og Onboarding
**Hvor:** `/src/pages/`
**Hva:**
- Lag `user_registration.py`
- Implementer skjema med bedriftskode-validering
- Koble nye brukere til riktig bedrift
- Lag velkomstside for nye brukere
- Test brukerregistrering med eksisterende bedriftskoder

### Step 3.2: Aktivitetssystem
**Hvor:** `/src/activities/`
**Hva:**
- Implementer `activity_manager.py`
- Definer forhåndssatte aktiviteter med poengskalaer:
  - Løping (km): 0-50=1p, 50-100=2p, 100+=3p
  - Sykling (km): 0-100=1p, 100-200=2p, 200+=3p  
  - Skritt (tusen): 0-200=1p, 200-400=2p, 400+=3p
- Lag poengkalkulator-funksjon
- Implementer aktivitet-validering
- Test poengberegning for alle aktiviteter

### Step 3.3: Månedlige Konkurranser
**Hvor:** `/src/competitions/`
**Hva:**
- Implementer `competition_manager.py`
- Lag automatisk opprettelse av månedlige konkurranser
- Implementer logikk for inneværende måned vs historikk
- Sett opp konkurranseperioder (1. til siste dag i måned)
- Test konkurranseopprettelse og -lukking

## Fase 4: Brukergrensesnitt

### Step 4.1: Dashboard og Navigering
**Hvor:** `/src/main.py` og `/src/components/`
**Hva:**
- Lag hovednavigering i Streamlit
- Implementer sidebar med brukerinfo og meny
- Opprett dashboard med oversikt over:
  - Inneværende konkurranser
  - Brukerens poengstatus  
  - Siste registreringer
- Test navigering mellom sider

### Step 4.2: Aktivitetsregistrering
**Hvor:** `/src/pages/register_activity.py`
**Hva:**
- Lag brukervenlig skjema for aktivitetsregistrering
- Implementer dropdown for aktivitetstype
- Legg til input-validering (positive tall, rimelige verdier)
- Vis poengkalkulator i sanntid
- Implementer lagring til database
- Test registrering av ulike aktivitetstyper

### Step 4.3: Leaderboard
**Hvor:** `/src/pages/leaderboard.py`
**Hva:**
- Implementer månedlig leaderboard for bedriften
- Lag sortering etter totale poeng
- Vis brukerens posisjon og poeng
- Implementer historisk visning (tidligere måneder)
- Legg til filtrering per aktivitetstype
- Test leaderboard med testdata

## Fase 5: Admin-funksjonalitet

### Step 5.1: Admin Dashboard
**Hvor:** `/src/pages/admin/`
**Hva:**
- Lag `admin_dashboard.py` (kun for admin-brukere)
- Implementer oversikt over:
  - Antall aktive brukere
  - Pågående konkurranser
  - Aktivitetsstatistikk
- Legg til admin-meny i sidebar
- Test admin-tilgang og vanlig bruker-blokkering

### Step 5.2: Brukeradministrasjon
**Hvor:** `/src/pages/admin/user_management.py`
**Hva:**
- Implementer liste over alle bedriftens brukere
- Lag funksjonalitet for å gjøre andre brukere til admin
- Implementer sletting/deaktivering av brukere
- Legg til søk og filtrering
- Test admin-operasjoner på brukere

### Step 5.3: Konkurranseadministrasjon
**Hvor:** `/src/pages/admin/competition_management.py`
**Hva:**
- Implementer start/stopp av månedlige konkurranser
- Lag oversikt over historiske konkurranser
- Implementer mulighet til å nullstille/korrigere data
- Test konkurranseadministrasjon

## Fase 6: Testing og Deploy

### Step 6.1: Testing og Kvalitetssikring
**Hvor:** `/tests/` og lokalt
**Hva:**
- Opprett testdata for ulike scenarios
- Test alle brukerflows end-to-end
- Verifiser poengberegning og leaderboards
- Test admin-funksjonalitet
- Sjekk responsivitet på mobil/desktop
- Dokumenter kjente issues i `/docs/known-issues.md`

### Step 6.2: Deployment Setup
**Hvor:** Streamlit Cloud
**Hva:**
- Koble GitHub repository til Streamlit Cloud
- Konfigurer miljøvariabler i Streamlit Cloud
- Test deployment og live-funksjonalitet
- Sett opp automatisk deploy ved push til main
- Dokumenter deployment-prosess i `/docs/deployment.md`

### Step 6.3: Dokumentasjon og Brukerguide
**Hvor:** `/docs/`
**Hva:**
- Opprett `user-guide.md` for sluttbrukere
- Lag `admin-guide.md` for bedriftsadministratorer  
- Dokumenter API og database i `technical-docs.md`
- Opprett troubleshooting-guide
- Test dokumentasjonen med eksterne brukere

## Fase 7: MVP Launch Prep

### Step 7.1: Beta Testing
**Hvor:** Live environment
**Hva:**
- Inviter 1-2 testbedrifter for beta
- Samle feedback på brukeropplevelse
- Identifiser og fiks kritiske bugs
- Optimaliser performance basert på real bruk
- Dokumenter feedback i `/docs/beta-feedback.md`

### Step 7.2: Production Ready
**Hvor:** Alle komponenter
**Hva:**
- Implementer backup-rutiner for database
- Sett opp error monitoring og logging
- Lag support-kontaktinfo i appen
- Ferdigstill terms of service og privacy policy
- Forbered onboarding-materiale for nye bedrifter

---

**Estimert tidsramme:** 6-8 uker for MVP
**Kritiske milepæler:** 
- Uke 2: Database og auth fungerer
- Uke 4: Grunnleggende registrering og leaderboard
- Uke 6: Admin-panel og full testing
- Uke 8: Deploy og beta-testing
