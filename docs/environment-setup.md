# Environment Setup Guide

## Oversikt
Denne guiden beskriver hvordan miljøvariabler og secrets settes opp for Konkurranseapp.

## Lokal Utvikling

### 1. Kopier environment template
```bash
cp .env.example .env
```

### 2. Fyll inn verdier i .env
Rediger `.env` filen og legg inn:
- `SUPABASE_URL`: Din Supabase Project URL
- `SUPABASE_ANON_KEY`: Din Supabase anon public key

### 3. Installer python-dotenv (hvis ikke allerede gjort)
```bash
pip install python-dotenv
```

### 4. Last miljøvariabler i koden
```python
import os
from dotenv import load_dotenv

# Last .env fil
load_dotenv()

# Bruk miljøvariabler
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_ANON_KEY")
```

## GitHub Actions / CI/CD

### GitHub Repository Secrets
Følgende secrets må settes opp i GitHub repository:

| Secret Name | Beskrivelse | Eksempel |
|-------------|-------------|----------|
| `SUPABASE_URL` | Supabase Project URL | `https://abc123.supabase.co` |
| `SUPABASE_ANON_KEY` | Supabase anon public key | `eyJhbGciOiJIUzI1NiI...` |
| `SECRET_KEY` | App secret key for sessions | Random streng |

### Sett opp secrets:
1. Gå til repository → Settings → Secrets and variables → Actions
2. Klikk "New repository secret"
3. Legg inn navn og verdi for hver secret

## Streamlit Cloud Deployment

### 1. Koble repository til Streamlit Cloud
1. Gå til [share.streamlit.io](https://share.streamlit.io)
2. Klikk "New app"
3. Velg ditt GitHub repository
4. Sett main file path: `src/main.py` (når den er opprettet)

### 2. Legg til secrets i Streamlit Cloud
I Streamlit Cloud app settings → "Secrets":

```toml
[supabase]
url = "https://your-project-id.supabase.co"
anon_key = "your-actual-anon-key"

[app]
name = "Konkurranseapp"
version = "1.0.0"
debug_mode = false
secret_key = "your-actual-secret-key"
```

### 3. Tilgang til secrets i Streamlit
```python
import streamlit as st

# I Streamlit Cloud
supabase_url = st.secrets["supabase"]["url"]
supabase_key = st.secrets["supabase"]["anon_key"]
```

## Produksjon

### Anbefalte sikkerhetstiltak:
1. **Aldri** commit `.env` filer eller secrets til git
2. Bruk sterke, unike nøkler for produksjon
3. Roter secrets regelmessig
4. Bruk miljøspesifikke konfigurasjoner (.env.staging, .env.production)
5. Overvåk tilgang til secrets og API-nøkler

### Environment-spesifikke konfigurasjoner:
```bash
# Utvikling
.env.development

# Testing  
.env.staging

# Produksjon
.env.production
```

## Debugging

### Vanlige problemer:

**"Module not found" for environment variabler:**
- Sjekk at `.env` filen eksisterer
- Verifiser at `python-dotenv` er installert
- Sørg for at `load_dotenv()` kalles før miljøvariabler brukes

**Supabase connection feil:**
- Dobbeltsjekk SUPABASE_URL format (må inkludere https://)
- Verifiser at SUPABASE_ANON_KEY er korrekt kopiert
- Test connection med Supabase dashboard

**Streamlit secrets ikke funker:**
- Sjekk at secrets.toml har korrekt TOML-format
- Verifiser at secrets er satt opp i Streamlit Cloud dashboard
- Restart Streamlit app etter secrets-endringer

## Eksempel på config loader

```python
# src/config.py
import os
import streamlit as st
from dotenv import load_dotenv

class Config:
    def __init__(self):
        # Last .env for lokal utvikling
        load_dotenv()
        
        self.supabase_url = self._get_secret("SUPABASE_URL", "supabase", "url")
        self.supabase_anon_key = self._get_secret("SUPABASE_ANON_KEY", "supabase", "anon_key")
        self.secret_key = self._get_secret("SECRET_KEY", "app", "secret_key")
        self.debug_mode = self._get_secret("DEBUG_MODE", "app", "debug_mode", "false").lower() == "true"
    
    def _get_secret(self, env_name, streamlit_section=None, streamlit_key=None, default=None):
        """Hent secret fra miljøvariabel eller Streamlit secrets"""
        # Prøv miljøvariabel først
        value = os.getenv(env_name)
        
        if value is None and streamlit_section and streamlit_key:
            # Prøv Streamlit secrets
            try:
                value = st.secrets[streamlit_section][streamlit_key]
            except (KeyError, AttributeError):
                pass
        
        if value is None:
            if default is not None:
                return default
            raise ValueError(f"Missing required configuration: {env_name}")
        
        return value

# Bruk:
config = Config()
```

## Sikkerhet

### ALDRI commit:
- `.env` filer med ekte verdier
- API-nøkler i kode
- Passord eller tokens
- `.streamlit/secrets.toml` med ekte data

### Sjekkliste før commit:
- [ ] `.env` er i `.gitignore`
- [ ] Ingen hardkodede secrets i kode
- [ ] Template-filer inneholder kun eksempler
- [ ] GitHub secrets er satt opp korrekt
