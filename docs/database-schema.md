# Database Schema - Konkurranseapp

## Oversikt
Applikasjonen bruker Supabase (PostgreSQL) som database med Row Level Security (RLS) aktivert på alle tabeller.

## Tabeller

### companies
Inneholder informasjon om bedrifter som bruker systemet.

| Kolonne | Type | Beskrivelse |
|---------|------|-------------|
| id | UUID | Primary key, auto-generert |
| name | VARCHAR(255) | Bedriftsnavn |
| company_code | VARCHAR(10) | Unik 6-tegns kode for bedriften |
| created_at | TIMESTAMPTZ | Opprettelsestidspunkt |

**Constraints:**
- `company_code` må være unik
- Auto-genereres med `generate_company_code()` funksjonen

### users
Utvider Supabase auth.users med app-spesifikk data.

| Kolonne | Type | Beskrivelse |
|---------|------|-------------|
| id | UUID | Foreign key til auth.users(id) |
| email | VARCHAR(255) | Brukerens e-post |
| full_name | VARCHAR(255) | Fullt navn |
| company_id | UUID | Foreign key til companies(id) |
| is_admin | BOOLEAN | Om brukeren er admin for bedriften |
| created_at | TIMESTAMPTZ | Opprettelsestidspunkt |

**Relationships:**
- Kobles til `companies` via `company_id`
- Cascade delete når bedrift eller auth-bruker slettes

### activities
Forhåndsdefinerte aktivitetstyper med poengskalaer.

| Kolonne | Type | Beskrivelse |
|---------|------|-------------|
| id | UUID | Primary key, auto-generert |
| name | VARCHAR(100) | Aktivitetsnavn (f.eks. "Løping") |
| description | TEXT | Beskrivelse av aktiviteten |
| unit | VARCHAR(20) | Måleenhet (f.eks. "km", "k steps") |
| scoring_tiers | JSONB | Poengskala som JSON |
| is_active | BOOLEAN | Om aktiviteten er tilgjengelig |
| created_at | TIMESTAMPTZ | Opprettelsestidspunkt |

**Scoring Tiers Format:**
```json
{
  "tiers": [
    {"min": 0, "max": 50, "points": 1},
    {"min": 50, "max": 100, "points": 2},
    {"min": 100, "max": null, "points": 3}
  ]
}
```

**Forhåndsdefinerte aktiviteter:**
1. **Løping**: 0-50km=1p, 50-100km=2p, 100+km=3p
2. **Sykling**: 0-100km=1p, 100-200km=2p, 200+km=3p  
3. **Skritt**: 0-200k=1p, 200-400k=2p, 400k+=3p

### monthly_competitions
Representerer månedlige konkurranser per bedrift.

| Kolonne | Type | Beskrivelse |
|---------|------|-------------|
| id | UUID | Primary key, auto-generert |
| company_id | UUID | Foreign key til companies(id) |
| year_month | DATE | Måned i YYYY-MM-01 format |
| is_active | BOOLEAN | Om konkurranseperioden er aktiv |
| created_at | TIMESTAMPTZ | Opprettelsestidspunkt |

**Constraints:**
- Unique constraint på (company_id, year_month)
- Cascade delete når bedrift slettes

### user_entries
Brukerregistreringer av aktiviteter for spesifikke konkurranser.

| Kolonne | Type | Beskrivelse |
|---------|------|-------------|
| id | UUID | Primary key, auto-generert |
| user_id | UUID | Foreign key til users(id) |
| activity_id | UUID | Foreign key til activities(id) |
| competition_id | UUID | Foreign key til monthly_competitions(id) |
| value | DECIMAL(10,2) | Faktisk verdi (km, steps, etc.) |
| points | INTEGER | Beregnede poeng basert på verdi |
| created_at | TIMESTAMPTZ | Opprettelsestidspunkt |
| updated_at | TIMESTAMPTZ | Sist oppdatert |

**Constraints:**
- Unique constraint på (user_id, activity_id, competition_id)
- En registrering per bruker/aktivitet/måned
- Cascade delete når refererte objekter slettes

## Row Level Security (RLS) Policies

### companies
- **SELECT**: Brukere kan kun se sin egen bedrift
- **UPDATE**: Kun admin kan oppdatere sin bedrift

### users  
- **SELECT**: Brukere kan se kolleger i samme bedrift
- **UPDATE**: Admin kan oppdatere brukere i sin bedrift, brukere kan oppdatere seg selv

### activities
- **SELECT**: Alle kan se aktive aktiviteter

### monthly_competitions
- **SELECT**: Brukere kan se konkurranser for sin bedrift

### user_entries
- **SELECT**: Brukere kan se entries for sin bedrift
- **INSERT/UPDATE/DELETE**: Brukere kan kun administrere sine egne entries

## Indexes

Følgende indexes er opprettet for performance:
- `idx_users_company_id` på users(company_id)
- `idx_monthly_competitions_company_year` på monthly_competitions(company_id, year_month)
- `idx_user_entries_competition` på user_entries(competition_id)
- `idx_user_entries_user` på user_entries(user_id)

## Funksjoner

### generate_company_code()
Genererer unik 6-tegns alfanumerisk bedriftskode.
- Format: 2 bokstaver + 2 tall + 1 bokstav + 1 tall (f.eks. AB12C3)
- Sjekker automatiskt for duplikater
- Brukes ved bedriftsopprettelse

## Triggers

### update_user_entries_updated_at
Oppdaterer automatisk `updated_at` kolonne når `user_entries` modifiseres.
