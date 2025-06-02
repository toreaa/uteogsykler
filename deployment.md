# 🚀 Cloud-Native Deployment Guide

## Oversikt
Denne applikasjonen er designet for fullstendig cloud-native deployment uten lokal kjøring.

## 📋 Pre-requisites

### 1. GitHub Repository
- [x] Kode pushet til GitHub
- [x] `main` branch som default
- [x] Alle filer i korrekt mappestruktur

### 2. Supabase Database  
- [x] Supabase prosjekt opprettet
- [x] Database schema implementert (fra Step 1.2)
- [x] URL og anon key tilgjengelig

### 3. Streamlit Cloud Account
- [x] Konto opprettet på [share.streamlit.io](https://share.streamlit.io)
- [x] GitHub repository tilgang gitt

## 🔧 Deployment Steps

### Step 1: Forberede Repository
Sørg for at følgende filer er på plass i ditt GitHub repo:

```
├── requirements.txt          # Python dependencies
├── src/
│   ├── __init__.py
│   ├── config.py            # Cloud-native configuration
│   ├── test_app.py          # Test application  
│   └── utils/
│       ├── __init__.py
│       ├── supabase_client.py
│       ├── database_helpers.py
│       └── error_handler.py
└── .streamlit/
    └── secrets.toml         # Template (don't commit real values!)
```

### Step 2: Koble til Streamlit Cloud
1. Gå til [share.streamlit.io](https://share.streamlit.io)
2. Klikk **"New app"**
3. Velg **"From existing repo"**
4. Autoriser GitHub tilgang hvis nødvendig
5. Velg ditt repository
6. Konfigurer app:
   - **Branch:** `main`
   - **Main file path:** `src/test_app.py`
   - **App URL:** velg ønsket URL (kan endres senere)

### Step 3: Konfigurer Secrets
1. I Streamlit Cloud app → **"Settings"** → **"Secrets"**
2. Legg inn følgende TOML-konfigurasjon:

```toml
[supabase]
url = "https://your-actual-project-id.supabase.co"
anon_key = "your-actual-anon-key-from-supabase"

[app]
name = "Konkurranseapp"
version = "1.0.0"
debug_mode = true
secret_key = "your-random-secret-key-for-sessions"
```

### Step 4: Første Deployment
1. Klikk **"Deploy!"** i Streamlit Cloud
2. Vent på deployment (1-3 minutter)
3. App åpnes automatisk når klar

### Step 5: Test Database Connection
1. I deployed app, klikk **"Test Database Connection"**
2. Verifiser at connection test passerer ✅
3. Test **"Load Activities"** for å sjekke data access
4. Test **"Calculate Points"** for å verifisere business logic

## 🔄 Continuous Deployment

### Automatisk deployment:
- **Push til main branch** → Streamlit Cloud deployer automatisk
- **Deployment tid:** 1-3 minutter
- **Hot reload:** Endringer vises umiddelbart

### Development workflow:
1. Edit kode (GitHub web editor eller git clone)
2. Commit til main branch  
3. Streamlit deployer automatisk
4. Test i live app

## 📊 Monitoring og Debugging

### App Health Check:
- Gå til din Streamlit app URL
- Kjør database connection test
- Sjekk at alle komponenter laster korrekt

### Common Issues og løsninger:

**🔴 App ikke starter:**
- Sjekk Streamlit Cloud logs for error messages
- Verifiser at `requirements.txt` er korrekt
- Kontroller at main file path er `src/test_app.py`

**🔴 "Secret not found" error:**
- Verifiser secrets format i Streamlit Cloud settings
- Sjekk at section og key navn matcher koden
- Restart app etter secrets endringer

**🔴 Database connection fails:**
- Dobbeltsjekk Supabase URL (må inkludere https://)
- Verifiser anon key er komplett kopiert
- Test connection i Supabase dashboard

**🔴 Import errors:**
- Kontroller at alle filer er pushet til GitHub
- Sjekk mappestruktur og __init__.py filer
- Verifiser Python pakke versioner i requirements.txt

### Debug Mode:
Sett `debug_mode = true` i Streamlit secrets for utvidet debugging info.

## 🚀 Production Deployment

### Fra test til production:
1. **Test grundig** med `test_app.py`
2. **Bytt main file** til `src/main.py` (når ferdig implementert)
3. **Sett debug_mode = false** i secrets
4. **Konfigurer custom domain** (optional)

### Security checklist:
- [ ] Secrets ikke hardkodet i kode
- [ ] Debug mode deaktivert for production
- [ ] Supabase RLS policies aktivert
- [ ] Strong secret keys i bruk

## 🆘 Support

### Streamlit Cloud issues:
- Docs: [docs.streamlit.io](https://docs.streamlit.io)
- Community: [discuss.streamlit.io](https://discuss.streamlit.io)

### Supabase issues:
- Docs: [supabase.com/docs](https://supabase.com/docs)
- Discord: [discord.supabase.com](https://discord.supabase.com)

---

## ✅ Deployment Verification

Når deployment er vellykket skal du kunne:
- [x] Åpne Streamlit app uten errors
- [x] Se "Configuration is valid" ✅
- [x] Test database connection successfully ✅  
- [x] Load activities and see data ✅
- [x] Calculate points for test values ✅

**🎉 Gratulerer! Din cloud-native Konkurranseapp er live!**
